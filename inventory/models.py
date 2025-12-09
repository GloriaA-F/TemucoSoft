from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from core.models import Company, User
from products.models import Product, Supplier


class Branch(models.Model):
    """
    Modelo para sucursales
    """
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='branches',
        verbose_name="Empresa"
    )
    name = models.CharField(max_length=200, verbose_name="Nombre")
    address = models.TextField(verbose_name="Dirección")
    phone = models.CharField(max_length=20, verbose_name="Teléfono")
    email = models.EmailField(blank=True, verbose_name="Email")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Sucursal"
        verbose_name_plural = "Sucursales"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} - {self.company.name}"


class Inventory(models.Model):
    """
    Modelo para control de inventario por sucursal
    """
    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        related_name='inventory_items',
        verbose_name="Sucursal"
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='inventory_records',
        verbose_name="Producto"
    )
    stock = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Stock Actual"
    )
    reorder_point = models.IntegerField(
        default=10,
        validators=[MinValueValidator(0)],
        verbose_name="Punto de Reorden"
    )
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Inventario"
        verbose_name_plural = "Inventarios"
        unique_together = [['branch', 'product']]
        ordering = ['branch', 'product']
    
    def __str__(self):
        return f"{self.product.name} en {self.branch.name}: {self.stock} unidades"
    
    def clean(self):
        if self.stock < 0:
            raise ValidationError({'stock': 'El stock no puede ser negativo'})
    
    @property
    def needs_reorder(self):
        """Indica si el producto necesita ser reordenado"""
        return self.stock <= self.reorder_point
    
    def adjust_stock(self, quantity, reason="Ajuste manual"):
        """
        Ajusta el stock y crea un registro de movimiento
        quantity positivo = entrada, negativo = salida
        """
        new_stock = self.stock + quantity
        if new_stock < 0:
            raise ValidationError(f"Stock insuficiente. Stock actual: {self.stock}")
        
        self.stock = new_stock
        self.save()
        
        # Crear movimiento
        InventoryMovement.objects.create(
            inventory=self,
            movement_type='ajuste',
            quantity=quantity,
            reason=reason,
            previous_stock=self.stock - quantity,
            new_stock=self.stock
        )


class InventoryMovement(models.Model):
    """
    Registro de movimientos de inventario
    """
    MOVEMENT_TYPES = [
        ('entrada', 'Entrada'),
        ('salida', 'Salida'),
        ('ajuste', 'Ajuste'),
        ('devolucion', 'Devolución'),
    ]
    
    inventory = models.ForeignKey(
        Inventory,
        on_delete=models.CASCADE,
        related_name='movements'
    )
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    quantity = models.IntegerField(verbose_name="Cantidad")
    previous_stock = models.IntegerField(verbose_name="Stock Anterior")
    new_stock = models.IntegerField(verbose_name="Stock Nuevo")
    reason = models.TextField(verbose_name="Motivo")
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Movimiento de Inventario"
        verbose_name_plural = "Movimientos de Inventario"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.movement_type} - {self.inventory.product.name}: {self.quantity}"


class Purchase(models.Model):
    """
    Modelo para órdenes de compra a proveedores
    """
    STATUS_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('recibida', 'Recibida'),
        ('cancelada', 'Cancelada'),
    ]
    
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='purchases'
    )
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT,
        related_name='purchases',
        verbose_name="Proveedor"
    )
    branch = models.ForeignKey(
        Branch,
        on_delete=models.PROTECT,
        related_name='purchases',
        verbose_name="Sucursal Destino"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='purchases',
        verbose_name="Usuario"
    )
    purchase_date = models.DateField(verbose_name="Fecha de Compra")
    total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Total"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pendiente'
    )
    notes = models.TextField(blank=True, verbose_name="Notas")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Compra"
        verbose_name_plural = "Compras"
        ordering = ['-purchase_date']
    
    def __str__(self):
        return f"Compra #{self.id} - {self.supplier.name} - {self.purchase_date}"
    
    def clean(self):
        if self.purchase_date and self.purchase_date > timezone.now().date():
            raise ValidationError({
                'purchase_date': 'La fecha de compra no puede ser futura'
            })
    
    def receive(self):
        """Marca la compra como recibida y actualiza inventario"""
        if self.status == 'recibida':
            raise ValidationError('Esta compra ya fue recibida')
        
        for item in self.items.all():
            # Obtener o crear registro de inventario
            inventory, created = Inventory.objects.get_or_create(
                branch=self.branch,
                product=item.product,
                defaults={'stock': 0, 'reorder_point': 10}
            )
            
            # Ajustar stock
            inventory.adjust_stock(
                item.quantity,
                f"Compra #{self.id} recibida"
            )
        
        self.status = 'recibida'
        self.save()


class PurchaseItem(models.Model):
    """
    Items individuales de una orden de compra
    """
    purchase = models.ForeignKey(
        Purchase,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='purchase_items'
    )
    quantity = models.IntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Cantidad"
    )
    unit_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Costo Unitario"
    )
    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Subtotal"
    )
    
    class Meta:
        verbose_name = "Item de Compra"
        verbose_name_plural = "Items de Compra"
    
    def __str__(self):
        return f"{self.product.name} x{self.quantity}"
    
    def save(self, *args, **kwargs):
        # Calcular subtotal automáticamente
        self.subtotal = self.quantity * self.unit_cost
        super().save(*args, **kwargs)
