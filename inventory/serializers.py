from rest_framework import serializers
from .models import Branch, Inventory, InventoryMovement, Purchase, PurchaseItem
from products.serializers import ProductListSerializer


class BranchSerializer(serializers.ModelSerializer):
    """Serializer para sucursales"""
    
    class Meta:
        model = Branch
        fields = [
            'id', 'name', 'address', 'phone', 'email',
            'is_active', 'created_at', 'company'
        ]
        read_only_fields = ['created_at', 'company']


class InventorySerializer(serializers.ModelSerializer):
    """Serializer para inventario"""
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    product_details = ProductListSerializer(source='product', read_only=True)
    needs_reorder = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Inventory
        fields = [
            'id', 'branch', 'branch_name', 'product', 'product_name',
            'product_sku', 'product_details', 'stock', 'reorder_point',
            'needs_reorder', 'last_updated'
        ]
        read_only_fields = ['last_updated']


class InventoryAdjustSerializer(serializers.Serializer):
    """Serializer para ajustes de inventario"""
    branch_id = serializers.IntegerField()
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField()
    reason = serializers.CharField(max_length=500)
    
    def validate_quantity(self, value):
        if value == 0:
            raise serializers.ValidationError("La cantidad no puede ser cero")
        return value


class InventoryMovementSerializer(serializers.ModelSerializer):
    """Serializer para movimientos de inventario"""
    product_name = serializers.CharField(source='inventory.product.name', read_only=True)
    branch_name = serializers.CharField(source='inventory.branch.name', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = InventoryMovement
        fields = [
            'id', 'inventory', 'product_name', 'branch_name',
            'movement_type', 'quantity', 'previous_stock', 'new_stock',
            'reason', 'created_by', 'created_by_username', 'created_at'
        ]
        read_only_fields = ['created_at']


class PurchaseItemSerializer(serializers.ModelSerializer):
    """Serializer para items de compra"""
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = PurchaseItem
        fields = [
            'id', 'product', 'product_name', 'quantity',
            'unit_cost', 'subtotal'
        ]
        read_only_fields = ['subtotal']


class PurchaseSerializer(serializers.ModelSerializer):
    """Serializer para compras"""
    items = PurchaseItemSerializer(many=True, read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Purchase
        fields = [
            'id', 'supplier', 'supplier_name', 'branch', 'branch_name',
            'user', 'user_username', 'purchase_date', 'total', 'status',
            'status_display', 'notes', 'items', 'created_at', 'company'
        ]
        read_only_fields = ['created_at', 'user', 'company']
    
    def validate_purchase_date(self, value):
        from django.utils import timezone
        if value > timezone.now().date():
            raise serializers.ValidationError(
                "La fecha de compra no puede ser futura"
            )
        return value


class PurchaseCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear compras con items"""
    items = PurchaseItemSerializer(many=True)
    
    class Meta:
        model = Purchase
        fields = [
            'supplier', 'branch', 'purchase_date', 'notes', 'items'
        ]
    
    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("Debe incluir al menos un item")
        return value
    
    def create(self, validated_data):
        items_data = validated_data.pop('items')
        
        # Calcular total
        total = sum(
            item['quantity'] * item['unit_cost']
            for item in items_data
        )
        
        # Crear compra
        purchase = Purchase.objects.create(
            **validated_data,
            total=total,
            user=self.context['request'].user,
            company=self.context['request'].user.company
        )
        
        # Crear items
        for item_data in items_data:
            PurchaseItem.objects.create(purchase=purchase, **item_data)
        
        return purchase
