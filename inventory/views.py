from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from .models import Branch, Inventory, InventoryMovement, Purchase, PurchaseItem
from .serializers import (
    BranchSerializer, InventorySerializer, InventoryAdjustSerializer,
    InventoryMovementSerializer, PurchaseSerializer, PurchaseCreateSerializer
)
from core.permissions import IsAdminCliente, CanManageInventory


class BranchViewSet(viewsets.ModelViewSet):
    """
    ViewSet para sucursales
    """
    queryset = Branch.objects.all()
    serializer_class = BranchSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'address']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAdminCliente]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'super_admin':
            return Branch.objects.all()
        elif user.company:
            return Branch.objects.filter(company=user.company, is_active=True)
        return Branch.objects.none()
    
    def perform_create(self, serializer):
        serializer.save(company=self.request.user.company)
    
    @action(detail=True, methods=['get'])
    def inventory(self, request, pk=None):
        """
        Obtener inventario de una sucursal específica
        """
        branch = self.get_object()
        inventory_items = Inventory.objects.filter(branch=branch).select_related('product')
        serializer = InventorySerializer(inventory_items, many=True)
        return Response(serializer.data)


class InventoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet para inventario
    """
    queryset = Inventory.objects.all()
    serializer_class = InventorySerializer
    permission_classes = [CanManageInventory]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['branch', 'product']
    ordering_fields = ['stock', 'last_updated']
    ordering = ['product__name']
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'super_admin':
            return Inventory.objects.all()
        elif user.company:
            return Inventory.objects.filter(
                branch__company=user.company
            ).select_related('product', 'branch')
        return Inventory.objects.none()
    
    @action(detail=False, methods=['post'], permission_classes=[CanManageInventory])
    def adjust(self, request):
        """
        Ajustar stock de inventario manualmente
        """
        serializer = InventoryAdjustSerializer(data=request.data)
        
        if serializer.is_valid():
            branch_id = serializer.validated_data['branch_id']
            product_id = serializer.validated_data['product_id']
            quantity = serializer.validated_data['quantity']
            reason = serializer.validated_data['reason']
            
            try:
                inventory = Inventory.objects.get(
                    branch_id=branch_id,
                    product_id=product_id
                )
                inventory.adjust_stock(quantity, reason)
                
                return Response({
                    'message': 'Inventario ajustado exitosamente',
                    'new_stock': inventory.stock
                })
            except Inventory.DoesNotExist:
                return Response(
                    {'error': 'Registro de inventario no encontrado'},
                    status=status.HTTP_404_NOT_FOUND
                )
            except Exception as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class InventoryMovementViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para ver movimientos de inventario (solo lectura)
    """
    queryset = InventoryMovement.objects.all()
    serializer_class = InventoryMovementSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['inventory__branch', 'inventory__product', 'movement_type']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'super_admin':
            return InventoryMovement.objects.all()
        elif user.company:
            return InventoryMovement.objects.filter(
                inventory__branch__company=user.company
            ).select_related('inventory__product', 'inventory__branch')
        return InventoryMovement.objects.none()


class PurchaseViewSet(viewsets.ModelViewSet):
    """
    ViewSet para compras a proveedores
    """
    queryset = Purchase.objects.all()
    permission_classes = [CanManageInventory]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['supplier', 'branch', 'status']
    ordering_fields = ['purchase_date', 'created_at']
    ordering = ['-purchase_date']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return PurchaseCreateSerializer
        return PurchaseSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'super_admin':
            return Purchase.objects.all()
        elif user.company:
            return Purchase.objects.filter(company=user.company).select_related(
                'supplier', 'branch', 'user'
            ).prefetch_related('items__product')
        return Purchase.objects.none()
    
    @action(detail=True, methods=['post'])
    def receive(self, request, pk=None):
        """
        Marcar compra como recibida y actualizar inventario
        """
        purchase = self.get_object()
        
        try:
            purchase.receive()
            return Response({
                'message': 'Compra recibida y stock actualizado',
                'status': purchase.status
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
