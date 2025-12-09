from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from core.models import validate_rut, Company


class Supplier(models.Model):
    """
    Modelo para proveedores
    """
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='suppliers',
        verbose_name="Empresa"
    )
    name = models.CharField(max_length=200, verbose_name="Nombre")
    rut = models.CharField(
        max_length=12,
        validators=[validate_rut],
        verbose_name="RUT"
    )
    contact_name = models.CharField(max_length=150, verbose_name="Nombre Contacto")
    contact_phone = models.CharField(max_length=20, verbose_name="Teléfono")
    contact_email = models.EmailField(verbose_name="Email")
    address = models.TextField(blank=True, verbose_name="Dirección")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Proveedor"
        verbose_name_plural = "Proveedores"
        ordering = ['name']
        unique_together = [['company', 'rut']]
    
    def __str__(self):
        return f"{self.name} ({self.rut})"


class Category(models.Model):
    """
    Modelo para categorías de productos
    """
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='categories'
    )
    name = models.CharField(max_length=100, verbose_name="Nombre")
    description = models.TextField(blank=True, verbose_name="Descripción")
    
    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ['name']
        unique_together = [['company', 'name']]
    
    def __str__(self):
        return self.name


class Product(models.Model):
    """
    Modelo para productos
    """
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name="Empresa"
    )
    sku = models.CharField(max_length=50, verbose_name="SKU")
    name = models.CharField(max_length=200, verbose_name="Nombre")
    description = models.TextField(blank=True, verbose_name="Descripción")
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products'
    )
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products',
        verbose_name="Proveedor"
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Precio de Venta"
    )
    cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Costo"
    )
    image = models.ImageField(
        upload_to='products/',
        blank=True,
        null=True,
        verbose_name="Imagen"
    )
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ['name']
        unique_together = [['company', 'sku']]
    
    def __str__(self):
        return f"{self.sku} - {self.name}"
    
    def clean(self):
        """Validación personalizada"""
        if self.price < 0:
            raise ValidationError({'price': 'El precio no puede ser negativo'})
        if self.cost < 0:
            raise ValidationError({'cost': 'El costo no puede ser negativo'})
        if self.price < self.cost:
            raise ValidationError('El precio de venta no debería ser menor al costo')
    
    @property
    def profit_margin(self):
        """Calcula el margen de ganancia"""
        if self.cost > 0:
            return ((self.price - self.cost) / self.cost) * 100
        return 0
