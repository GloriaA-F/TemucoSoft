from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from .models import Product, Supplier, Category
from .serializers import (
    ProductSerializer, ProductListSerializer, ProductCreateSerializer,
    SupplierSerializer, CategorySerializer
)
from core.permissions import CanManageProducts


class CategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet para categorías
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [CanManageProducts]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name']
    ordering = ['name']
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'super_admin':
            return Category.objects.all()
        elif user.company:
            return Category.objects.filter(company=user.company)
        return Category.objects.none()
    
    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company)


class SupplierViewSet(viewsets.ModelViewSet):
    """
    ViewSet para proveedores
    """
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [CanManageProducts]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'rut', 'contact_name']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'super_admin':
            return Supplier.objects.all()
        elif user.company:
            return Supplier.objects.filter(company=user.company, is_active=True)
        return Supplier.objects.none()
    
    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company)


class ProductViewSet(viewsets.ModelViewSet):
    """
    ViewSet para productos
    """
    queryset = Product.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'supplier', 'is_active']
    search_fields = ['name', 'sku', 'description']
    ordering_fields = ['name', 'price', 'created_at']
    ordering = ['name']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ProductListSerializer
        elif self.action == 'create':
            return ProductCreateSerializer
        return ProductSerializer
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [IsAuthenticatedOrReadOnly]
        else:
            permission_classes = [CanManageProducts]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        user = self.request.user
        
        # Para usuarios no autenticados (e-commerce público)
        if not user.is_authenticated:
            return Product.objects.filter(is_active=True)
        
        if user.role == 'super_admin':
            return Product.objects.all()
        elif user.company:
            queryset = Product.objects.filter(company=user.company)
            # Si es solo lectura, mostrar solo activos
            if self.action in ['list', 'retrieve']:
                queryset = queryset.filter(is_active=True)
            return queryset
        return Product.objects.filter(is_active=True)
    
    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company)
