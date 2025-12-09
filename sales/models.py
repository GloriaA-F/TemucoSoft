from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from core.models import User
from products.models import Product
from inventory.models import Branch, Inventory


class Sale(models.Model):
    """
    Modelo para ventas POS (punto de venta)
    """
    PAYMENT_METHODS = [
        ('efectivo', 'Efectivo'),
        ('tarjeta_debito', 'Tarjeta de Débito'),
        ('tarjeta_credito', 'Tarjeta de Crédito'),
        ('transferencia', 'Transferencia'),
    ]
    
    branch = models.ForeignKey(
        Branch,
        on_delete=models.PROTECT,
        related_name='sales',
        verbose_name="Sucursal"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='sales',
        verbose_name="Vendedor"
    )
    total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Total"
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHODS,
        verbose_name="Método de Pago"
    )
    notes = models.TextField(blank=True, verbose_name="Notas")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Venta"
        verbose_name_plural = "Ventas"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['branch', '-created_at']),
        ]
    
    def __str__(self):
        return f"Venta #{self.id} - {self.branch.name} - ${self.total}"
    
    def clean(self):
        """Validación: no permitir ventas con fecha futura"""
        if self.created_at and self.created_at > timezone.now():
            raise ValidationError({
                'created_at': 'La fecha de venta no puede ser futura'
            })
    
    def process_sale(self):
        """
        Procesa la venta descontando del inventario
        """
        for item in self.items.all():
            try:
                inventory = Inventory.objects.get(
                    branch=self.branch,
                    product=item.product
                )
                
                # Descontar del inventario
                inventory.adjust_stock(
                    -item.quantity,
                    f"Venta POS #{self.id}"
                )
            except Inventory.DoesNotExist:
                raise ValidationError(
                    f"Producto {item.product.name} no disponible en esta sucursal"
                )


class SaleItem(models.Model):
    """
    Items individuales de una venta
    """
    sale = models.ForeignKey(
        Sale,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='sale_items'
    )
    quantity = models.IntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Cantidad"
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Precio Unitario"
    )
    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Subtotal"
    )
    
    class Meta:
        verbose_name = "Item de Venta"
        verbose_name_plural = "Items de Venta"
    
    def __str__(self):
        return f"{self.product.name} x{self.quantity}"
    
    def save(self, *args, **kwargs):
        # Calcular subtotal automáticamente
        self.subtotal = self.quantity * self.price
        super().save(*args, **kwargs)


class Order(models.Model):
    """
    Modelo para órdenes de e-commerce
    """
    STATUS_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('procesando', 'Procesando'),
        ('enviado', 'Enviado'),
        ('entregado', 'Entregado'),
        ('cancelado', 'Cancelado'),
    ]
    
    # Cliente puede ser anónimo o registrado
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders'
    )
    customer_name = models.CharField(max_length=200, verbose_name="Nombre Cliente")
    customer_email = models.EmailField(verbose_name="Email Cliente")
    customer_phone = models.CharField(max_length=20, verbose_name="Teléfono Cliente")
    shipping_address = models.TextField(verbose_name="Dirección de Envío")
    
    total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Total"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pendiente',
        verbose_name="Estado"
    )
    
    # Sucursal que procesa el pedido
    processing_branch = models.ForeignKey(
        Branch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
        verbose_name="Sucursal que Procesa"
    )
    
    notes = models.TextField(blank=True, verbose_name="Notas")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Orden"
        verbose_name_plural = "Órdenes"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"Orden #{self.id} - {self.customer_name} - {self.get_status_display()}"
    
    def process_order(self, branch):
        """
        Procesa la orden y descuenta del inventario de una sucursal
        """
        if self.status != 'pendiente':
            raise ValidationError('Solo se pueden procesar órdenes pendientes')
        
        self.processing_branch = branch
        
        for item in self.items.all():
            try:
                inventory = Inventory.objects.get(
                    branch=branch,
                    product=item.product
                )
                
                # Verificar stock disponible
                if inventory.stock < item.quantity:
                    raise ValidationError(
                        f"Stock insuficiente de {item.product.name}. "
                        f"Disponible: {inventory.stock}, Requerido: {item.quantity}"
                    )
                
                # Descontar del inventario
                inventory.adjust_stock(
                    -item.quantity,
                    f"Orden e-commerce #{self.id}"
                )
            except Inventory.DoesNotExist:
                raise ValidationError(
                    f"Producto {item.product.name} no disponible en esta sucursal"
                )
        
        self.status = 'procesando'
        self.save()


class OrderItem(models.Model):
    """
    Items individuales de una orden
    """
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='order_items'
    )
    quantity = models.IntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Cantidad"
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Precio Unitario"
    )
    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Subtotal"
    )
    
    class Meta:
        verbose_name = "Item de Orden"
        verbose_name_plural = "Items de Orden"
    
    def __str__(self):
        return f"{self.product.name} x{self.quantity}"
    
    def save(self, *args, **kwargs):
        # Calcular subtotal automáticamente
        self.subtotal = self.quantity * self.price
        super().save(*args, **kwargs)
