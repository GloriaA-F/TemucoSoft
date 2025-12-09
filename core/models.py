from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.core.exceptions import ValidationError
import re


def validate_rut(value):
    """
    Validador para RUT chileno.
    Formato aceptado: 12345678-9 o 12.345.678-9 o 12345678-K
    """
    # Limpiar el RUT
    rut = value.replace(".", "").replace("-", "").upper()
    
    if len(rut) < 2:
        raise ValidationError("RUT debe tener al menos 2 caracteres")
    
    # Separar número y dígito verificador
    num = rut[:-1]
    dv = rut[-1]
    
    # Validar que el número sea numérico
    if not num.isdigit():
        raise ValidationError("El cuerpo del RUT debe ser numérico")
    
    # Calcular dígito verificador
    reversed_digits = map(int, reversed(num))
    factors = [2, 3, 4, 5, 6, 7] * 3  # Ciclo 2-7
    s = sum(d * f for d, f in zip(reversed_digits, factors))
    verification = 11 - (s % 11)
    
    if verification == 11:
        expected_dv = '0'
    elif verification == 10:
        expected_dv = 'K'
    else:
        expected_dv = str(verification)
    
    if dv != expected_dv:
        raise ValidationError(f"RUT inválido. DV esperado: {expected_dv}")
    
    return value


class Company(models.Model):
    """
    Modelo para empresas cliente (tenants) de TemucoSoft
    """
    name = models.CharField(max_length=200, verbose_name="Nombre de Empresa")
    rut = models.CharField(
        max_length=12, 
        unique=True, 
        validators=[validate_rut],
        verbose_name="RUT Empresa"
    )
    contact_email = models.EmailField(verbose_name="Email de Contacto")
    contact_phone = models.CharField(max_length=20, verbose_name="Teléfono", blank=True)
    address = models.TextField(verbose_name="Dirección", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Empresa"
        verbose_name_plural = "Empresas"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.rut})"


class Subscription(models.Model):
    """
    Modelo para suscripciones de empresas
    """
    PLAN_CHOICES = [
        ('basico', 'Básico'),
        ('estandar', 'Estándar'),
        ('premium', 'Premium'),
    ]
    
    company = models.OneToOneField(
        Company, 
        on_delete=models.CASCADE, 
        related_name='subscription'
    )
    plan_name = models.CharField(
        max_length=20, 
        choices=PLAN_CHOICES, 
        default='basico'
    )
    start_date = models.DateField(verbose_name="Fecha de Inicio")
    end_date = models.DateField(verbose_name="Fecha de Término")
    active = models.BooleanField(default=True)
    max_branches = models.IntegerField(default=1, verbose_name="Máximo de Sucursales")
    max_users = models.IntegerField(default=5, verbose_name="Máximo de Usuarios")
    
    class Meta:
        verbose_name = "Suscripción"
        verbose_name_plural = "Suscripciones"
    
    def clean(self):
        if self.end_date and self.start_date and self.end_date <= self.start_date:
            raise ValidationError("La fecha de término debe ser posterior a la fecha de inicio")
    
    def __str__(self):
        return f"{self.company.name} - Plan {self.get_plan_name_display()}"


class UserManager(BaseUserManager):
    """
    Manager personalizado para el modelo User
    """
    def create_user(self, username, email, password=None, **extra_fields):
        if not email:
            raise ValueError('El usuario debe tener un email')
        if not username:
            raise ValueError('El usuario debe tener un username')
        
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'super_admin')
        extra_fields.setdefault('is_active', True)
        
        return self.create_user(username, email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Modelo de usuario personalizado con roles y validación de RUT
    """
    ROLE_CHOICES = [
        ('super_admin', 'Super Administrador'),
        ('admin_cliente', 'Administrador Cliente'),
        ('gerente', 'Gerente'),
        ('vendedor', 'Vendedor'),
        ('cliente_final', 'Cliente Final'),
    ]
    
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    rut = models.CharField(
        max_length=12, 
        unique=True, 
        validators=[validate_rut],
        verbose_name="RUT"
    )
    role = models.CharField(
        max_length=20, 
        choices=ROLE_CHOICES, 
        default='vendedor'
    )
    company = models.ForeignKey(
        Company, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='users'
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'rut']
    
    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.username} - {self.get_role_display()}"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    def has_permission(self, permission):
        """
        Verifica si el usuario tiene un permiso específico según su rol
        """
        role_permissions = {
            'super_admin': ['all'],
            'admin_cliente': ['manage_products', 'manage_inventory', 'manage_suppliers', 
                             'manage_branches', 'view_reports', 'manage_users'],
            'gerente': ['manage_products', 'manage_inventory', 'manage_suppliers', 'view_reports'],
            'vendedor': ['create_sales', 'view_products'],
            'cliente_final': ['create_orders', 'view_products'],
        }
        
        user_perms = role_permissions.get(self.role, [])
        return 'all' in user_perms or permission in user_perms
