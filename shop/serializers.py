from rest_framework import serializers
from .models import CartItem
from products.serializers import ProductListSerializer


class CartItemSerializer(serializers.ModelSerializer):
    """Serializer para items del carrito"""
    product_details = ProductListSerializer(source='product', read_only=True)
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    
    class Meta:
        model = CartItem
        fields = [
            'id', 'product', 'product_details', 'quantity',
            'subtotal', 'added_at', 'updated_at'
        ]
        read_only_fields = ['added_at', 'updated_at']


class CartItemAddSerializer(serializers.Serializer):
    """Serializer para agregar productos al carrito"""
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1, default=1)
    
    def validate_product_id(self, value):
        from products.models import Product
        try:
            Product.objects.get(id=value, is_active=True)
            return value
        except Product.DoesNotExist:
            raise serializers.ValidationError("Producto no encontrado o inactivo")


class CartItemUpdateSerializer(serializers.Serializer):
    """Serializer para actualizar cantidad en el carrito"""
    quantity = serializers.IntegerField(min_value=1)


class CartSummarySerializer(serializers.Serializer):
    """Serializer para resumen del carrito"""
    items = CartItemSerializer(many=True, read_only=True)
    total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    item_count = serializers.IntegerField(read_only=True)
