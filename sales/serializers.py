from rest_framework import serializers
from django.utils import timezone
from .models import Sale, SaleItem, Order, OrderItem


class SaleItemSerializer(serializers.ModelSerializer):
    """Serializer para items de venta"""
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = SaleItem
        fields = [
            'id', 'product', 'product_name', 'quantity',
            'price', 'subtotal'
        ]
        read_only_fields = ['subtotal']


class SaleSerializer(serializers.ModelSerializer):
    """Serializer para ventas"""
    items = SaleItemSerializer(many=True, read_only=True)
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    payment_method_display = serializers.CharField(
        source='get_payment_method_display', 
        read_only=True
    )
    
    class Meta:
        model = Sale
        fields = [
            'id', 'branch', 'branch_name', 'user', 'user_username',
            'total', 'payment_method', 'payment_method_display',
            'notes', 'items', 'created_at'
        ]
        read_only_fields = ['created_at', 'user']
    
    def validate_created_at(self, value):
        if value > timezone.now():
            raise serializers.ValidationError(
                "La fecha de venta no puede ser futura"
            )
        return value


class SaleCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear ventas con items"""
    items = SaleItemSerializer(many=True)
    
    class Meta:
        model = Sale
        fields = ['branch', 'payment_method', 'notes', 'items']
    
    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("Debe incluir al menos un item")
        return value
    
    def create(self, validated_data):
        from django.db import transaction
        from inventory.models import Inventory
        
        items_data = validated_data.pop('items')
        
        # Calcular total
        total = sum(
            item['quantity'] * item['price']
            for item in items_data
        )
        
        with transaction.atomic():
            # Crear venta
            sale = Sale.objects.create(
                **validated_data,
                total=total,
                user=self.context['request'].user
            )
            
            # Crear items y descontar inventario
            for item_data in items_data:
                SaleItem.objects.create(sale=sale, **item_data)
                
                # Descontar del inventario
                try:
                    inventory = Inventory.objects.get(
                        branch=sale.branch,
                        product=item_data['product']
                    )
                    inventory.adjust_stock(
                        -item_data['quantity'],
                        f"Venta POS #{sale.id}"
                    )
                except Inventory.DoesNotExist:
                    raise serializers.ValidationError(
                        f"Producto {item_data['product'].name} no disponible en esta sucursal"
                    )
        
        return sale


class OrderItemSerializer(serializers.ModelSerializer):
    """Serializer para items de orden"""
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = OrderItem
        fields = [
            'id', 'product', 'product_name', 'quantity',
            'price', 'subtotal'
        ]
        read_only_fields = ['subtotal']


class OrderSerializer(serializers.ModelSerializer):
    """Serializer para órdenes"""
    items = OrderItemSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    processing_branch_name = serializers.CharField(
        source='processing_branch.name', 
        read_only=True
    )
    
    class Meta:
        model = Order
        fields = [
            'id', 'user', 'customer_name', 'customer_email', 'customer_phone',
            'shipping_address', 'total', 'status', 'status_display',
            'processing_branch', 'processing_branch_name', 'notes',
            'items', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'user']


class OrderCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear órdenes desde el carrito o directamente"""
    items = OrderItemSerializer(many=True)
    
    class Meta:
        model = Order
        fields = [
            'customer_name', 'customer_email', 'customer_phone',
            'shipping_address', 'notes', 'items'
        ]
    
    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("Debe incluir al menos un item")
        return value
    
    def create(self, validated_data):
        items_data = validated_data.pop('items')
        
        # Calcular total
        total = sum(
            item['quantity'] * item['price']
            for item in items_data
        )
        
        # Crear orden
        order = Order.objects.create(
            **validated_data,
            total=total,
            user=self.context['request'].user if self.context['request'].user.is_authenticated else None
        )
        
        # Crear items
        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)
        
        return order


class OrderProcessSerializer(serializers.Serializer):
    """Serializer para procesar una orden"""
    branch_id = serializers.IntegerField()
    
    def validate_branch_id(self, value):
        from inventory.models import Branch
        try:
            branch = Branch.objects.get(id=value)
            if not branch.is_active:
                raise serializers.ValidationError("La sucursal no está activa")
            return value
        except Branch.DoesNotExist:
            raise serializers.ValidationError("Sucursal no encontrada")
