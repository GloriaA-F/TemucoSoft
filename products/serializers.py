from rest_framework import serializers
from .models import Product, Supplier, Category


class CategorySerializer(serializers.ModelSerializer):
    """Serializer para categorías"""
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'company']
        read_only_fields = ['company']


class SupplierSerializer(serializers.ModelSerializer):
    """Serializer para proveedores"""
    
    class Meta:
        model = Supplier
        fields = [
            'id', 'name', 'rut', 'contact_name', 'contact_phone',
            'contact_email', 'address', 'is_active', 'created_at', 'company'
        ]
        read_only_fields = ['created_at', 'company']


class ProductListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listados de productos"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'sku', 'name', 'price', 'category', 'category_name',
            'supplier_name', 'is_active', 'image'
        ]


class ProductSerializer(serializers.ModelSerializer):
    """Serializer completo para productos"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    profit_margin = serializers.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        read_only=True
    )
    
    class Meta:
        model = Product
        fields = [
            'id', 'sku', 'name', 'description', 'category', 'category_name',
            'supplier', 'supplier_name', 'price', 'cost', 'profit_margin',
            'image', 'is_active', 'created_at', 'updated_at', 'company'
        ]
        read_only_fields = ['created_at', 'updated_at', 'company', 'profit_margin']
    
    def validate(self, data):
        """Validación personalizada"""
        price = data.get('price', 0)
        cost = data.get('cost', 0)
        
        # Si es actualización, obtener valores actuales si no se proporcionan
        if self.instance:
            price = price or self.instance.price
            cost = cost or self.instance.cost
        
        if price < 0:
            raise serializers.ValidationError({
                'price': 'El precio no puede ser negativo'
            })
        
        if cost < 0:
            raise serializers.ValidationError({
                'cost': 'El costo no puede ser negativo'
            })
        
        if price < cost:
            raise serializers.ValidationError(
                'El precio de venta no debería ser menor al costo'
            )
        
        return data


class ProductCreateSerializer(serializers.ModelSerializer):
    """Serializer para creación de productos"""
    
    class Meta:
        model = Product
        fields = [
            'sku', 'name', 'description', 'category', 'supplier',
            'price', 'cost', 'image'
        ]
    
    def validate(self, data):
        if data['price'] < data['cost']:
            raise serializers.ValidationError(
                'El precio de venta no debería ser menor al costo'
            )
        return data
