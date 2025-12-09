from django.db import models
from django.core.validators import MinValueValidator
from core.models import User
from products.models import Product


class CartItem(models.Model):
    """
    Items del carrito de compras
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='cart_items',
        verbose_name="Usuario"
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='cart_items',
        verbose_name="Producto"
    )
    quantity = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name="Cantidad"
    )
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Item de Carrito"
        verbose_name_plural = "Items de Carrito"
        unique_together = [['user', 'product']]
        ordering = ['-added_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.product.name} x{self.quantity}"
    
    @property
    def subtotal(self):
        """Calcula el subtotal del item"""
        return self.quantity * self.product.price
    
    def increase_quantity(self, amount=1):
        """Incrementa la cantidad del item"""
        self.quantity += amount
        self.save()
    
    def decrease_quantity(self, amount=1):
        """Decrementa la cantidad del item"""
        if self.quantity - amount <= 0:
            self.delete()
        else:
            self.quantity -= amount
            self.save()


class Cart:
    """
    Clase helper para manejar el carrito de compras
    No es un modelo, sino una utilidad
    """
    def __init__(self, user):
        self.user = user
    
    def add_product(self, product, quantity=1):
        """Agrega un producto al carrito"""
        cart_item, created = CartItem.objects.get_or_create(
            user=self.user,
            product=product,
            defaults={'quantity': quantity}
        )
        
        if not created:
            cart_item.quantity += quantity
            cart_item.save()
        
        return cart_item
    
    def remove_product(self, product):
        """Elimina un producto del carrito"""
        CartItem.objects.filter(user=self.user, product=product).delete()
    
    def update_quantity(self, product, quantity):
        """Actualiza la cantidad de un producto"""
        if quantity <= 0:
            self.remove_product(product)
        else:
            cart_item = CartItem.objects.get(user=self.user, product=product)
            cart_item.quantity = quantity
            cart_item.save()
    
    def get_items(self):
        """Obtiene todos los items del carrito"""
        return CartItem.objects.filter(user=self.user).select_related('product')
    
    def get_total(self):
        """Calcula el total del carrito"""
        items = self.get_items()
        return sum(item.subtotal for item in items)
    
    def get_item_count(self):
        """Cuenta el número de items en el carrito"""
        return self.get_items().count()
    
    def clear(self):
        """Vacía el carrito"""
        CartItem.objects.filter(user=self.user).delete()
