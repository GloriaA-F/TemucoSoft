from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Sale, SaleItem, Order, OrderItem
from .serializers import (
    SaleSerializer, SaleCreateSerializer,
    OrderSerializer, OrderCreateSerializer, OrderProcessSerializer
)
from core.permissions import CanCreateSales, CanViewReports


class SaleViewSet(viewsets.ModelViewSet):
    """
    ViewSet para ventas POS
    """
    queryset = Sale.objects.all()
    permission_classes = [CanCreateSales]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['branch', 'payment_method']
    ordering_fields = ['created_at', 'total']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return SaleCreateSerializer
        return SaleSerializer
    
    def get_queryset(self):
        user = self.request.user
        queryset = Sale.objects.all()
        
        if user.role == 'super_admin':
            pass  # Ver todas
        elif user.company:
            queryset = queryset.filter(branch__company=user.company)
        else:
            queryset = Sale.objects.none()
        
        # Filtros de fecha
        date_from = self.request.query_params.get('date_from', None)
        date_to = self.request.query_params.get('date_to', None)
        
        if date_from:
            try:
                date_from = datetime.strptime(date_from, '%Y-%m-%d')
                queryset = queryset.filter(created_at__gte=date_from)
            except ValueError:
                pass
        
        if date_to:
            try:
                date_to = datetime.strptime(date_to, '%Y-%m-%d')
                date_to = date_to.replace(hour=23, minute=59, second=59)
                queryset = queryset.filter(created_at__lte=date_to)
            except ValueError:
                pass
        
        return queryset.select_related('branch', 'user').prefetch_related('items__product')


class OrderViewSet(viewsets.ModelViewSet):
    """
    ViewSet para órdenes de e-commerce
    """
    queryset = Order.objects.all()
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'processing_branch']
    ordering_fields = ['created_at', 'total']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return OrderCreateSerializer
        elif self.action == 'process':
            return OrderProcessSerializer
        return OrderSerializer
    
    def get_permissions(self):
        if self.action == 'create':
            permission_classes = [IsAuthenticatedOrReadOnly]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        user = self.request.user
        
        if not user.is_authenticated:
            return Order.objects.none()
        
        if user.role == 'super_admin':
            return Order.objects.all()
        elif user.role == 'cliente_final':
            # Clientes finales solo ven sus propias órdenes
            return Order.objects.filter(user=user)
        elif user.company:
            # Staff de la empresa ve todas las órdenes
            return Order.objects.all()
        
        return Order.objects.none()
    
    @action(detail=True, methods=['post'], permission_classes=[CanCreateSales])
    def process(self, request, pk=None):
        """
        Procesar una orden y descontar del inventario
        """
        order = self.get_object()
        serializer = OrderProcessSerializer(data=request.data)
        
        if serializer.is_valid():
            from inventory.models import Branch
            branch_id = serializer.validated_data['branch_id']
            
            try:
                branch = Branch.objects.get(id=branch_id)
                order.process_order(branch)
                
                return Response({
                    'message': 'Orden procesada exitosamente',
                    'status': order.status,
                    'branch': branch.name
                })
            except Branch.DoesNotExist:
                return Response(
                    {'error': 'Sucursal no encontrada'},
                    status=status.HTTP_404_NOT_FOUND
                )
            except Exception as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """
        Actualizar el estado de una orden
        """
        order = self.get_object()
        new_status = request.data.get('status')
        
        if new_status not in dict(Order.STATUS_CHOICES):
            return Response(
                {'error': 'Estado inválido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        order.status = new_status
        order.save()
        
        return Response({
            'message': 'Estado actualizado',
            'status': order.status
        })
