from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import CartItem, Cart
from .serializers import (
    CartItemSerializer, CartItemAddSerializer,
    CartItemUpdateSerializer, CartSummarySerializer
)
from products.models import Product
from sales.models import Order, OrderItem


class CartViewSet(viewsets.ViewSet):
    """
    ViewSet para gestión del carrito de compras
    """
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """
        Listar items del carrito del usuario
        """
        cart = Cart(request.user)
        items = cart.get_items()
        total = cart.get_total()
        
        serializer = CartItemSerializer(items, many=True)
        return Response({
            'items': serializer.data,
            'total': total,
            'item_count': cart.get_item_count()
        })
    
    @action(detail=False, methods=['post'])
    def add(self, request):
        """
        Agregar producto al carrito
        """
        serializer = CartItemAddSerializer(data=request.data)
        
        if serializer.is_valid():
            product_id = serializer.validated_data['product_id']
            quantity = serializer.validated_data['quantity']
            
            try:
                product = Product.objects.get(id=product_id, is_active=True)
                cart = Cart(request.user)
                cart_item = cart.add_product(product, quantity)
                
                item_serializer = CartItemSerializer(cart_item)
                return Response({
                    'message': 'Producto agregado al carrito',
                    'item': item_serializer.data,
                    'cart_total': cart.get_total()
                })
            except Product.DoesNotExist:
                return Response(
                    {'error': 'Producto no encontrado'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['patch'])
    def update_quantity(self, request, pk=None):
        """
        Actualizar cantidad de un item del carrito
        """
        serializer = CartItemUpdateSerializer(data=request.data)
        
        if serializer.is_valid():
            quantity = serializer.validated_data['quantity']
            
            try:
                cart_item = CartItem.objects.get(id=pk, user=request.user)
                cart = Cart(request.user)
                cart.update_quantity(cart_item.product, quantity)
                
                return Response({
                    'message': 'Cantidad actualizada',
                    'cart_total': cart.get_total()
                })
            except CartItem.DoesNotExist:
                return Response(
                    {'error': 'Item no encontrado'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['delete'])
    def remove(self, request, pk=None):
        """
        Eliminar un item del carrito
        """
        try:
            cart_item = CartItem.objects.get(id=pk, user=request.user)
            cart = Cart(request.user)
            cart.remove_product(cart_item.product)
            
            return Response({
                'message': 'Producto eliminado del carrito',
                'cart_total': cart.get_total()
            })
        except CartItem.DoesNotExist:
            return Response(
                {'error': 'Item no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['post'])
    def checkout(self, request):
        """
        Convertir el carrito en una orden
        """
        cart = Cart(request.user)
        items = cart.get_items()
        
        if not items.exists():
            return Response(
                {'error': 'El carrito está vacío'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Obtener datos del cliente
        customer_name = request.data.get('customer_name', request.user.get_full_name())
        customer_email = request.data.get('customer_email', request.user.email)
        customer_phone = request.data.get('customer_phone', '')
        shipping_address = request.data.get('shipping_address', '')
        
        if not customer_name or not customer_email or not shipping_address:
            return Response(
                {'error': 'Faltan datos del cliente (nombre, email, dirección)'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Calcular total
        total = cart.get_total()
        
        # Crear orden
        order = Order.objects.create(
            user=request.user,
            customer_name=customer_name,
            customer_email=customer_email,
            customer_phone=customer_phone,
            shipping_address=shipping_address,
            total=total,
            status='pendiente'
        )
        
        # Crear items de la orden
        for cart_item in items:
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                quantity=cart_item.quantity,
                price=cart_item.product.price,
                subtotal=cart_item.subtotal
            )
        
        # Vaciar el carrito
        cart.clear()
        
        return Response({
            'message': 'Orden creada exitosamente',
            'order_id': order.id,
            'total': order.total
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['delete'])
    def clear(self, request):
        """
        Vaciar el carrito
        """
        cart = Cart(request.user)
        cart.clear()
        
        return Response({'message': 'Carrito vaciado'})
