from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Sum, Count, Avg
from datetime import datetime, timedelta
from .models import Sale
from inventory.models import Inventory
from core.permissions import CanViewReports


@api_view(['GET'])
@permission_classes([CanViewReports])
def stock_report(request):
    """
    Reporte de stock por sucursal
    """
    branch_id = request.query_params.get('branch', None)
    
    queryset = Inventory.objects.select_related('branch', 'product')
    
    # Filtrar por empresa del usuario
    if request.user.role != 'super_admin':
        queryset = queryset.filter(branch__company=request.user.company)
    
    # Filtrar por sucursal si se especifica
    if branch_id:
        queryset = queryset.filter(branch_id=branch_id)
    
    # Agrupar datos
    report_data = []
    for item in queryset:
        report_data.append({
            'branch': item.branch.name,
            'product_sku': item.product.sku,
            'product_name': item.product.name,
            'stock': item.stock,
            'reorder_point': item.reorder_point,
            'needs_reorder': item.needs_reorder,
            'product_price': float(item.product.price),
            'stock_value': float(item.stock * item.product.cost)
        })
    
    # Calcular totales
    total_items = len(report_data)
    total_value = sum(item['stock_value'] for item in report_data)
    items_need_reorder = sum(1 for item in report_data if item['needs_reorder'])
    
    return Response({
        'report': report_data,
        'summary': {
            'total_items': total_items,
            'total_stock_value': total_value,
            'items_need_reorder': items_need_reorder
        }
    })


@api_view(['GET'])
@permission_classes([CanViewReports])
def sales_report(request):
    """
    Reporte de ventas por periodo
    """
    date_from = request.query_params.get('date_from', None)
    date_to = request.query_params.get('date_to', None)
    branch_id = request.query_params.get('branch', None)
    
    # Fecha por defecto: último mes
    if not date_from:
        date_from = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not date_to:
        date_to = datetime.now().strftime('%Y-%m-%d')
    
    # Parsear fechas
    try:
        date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
        date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
        date_to_obj = date_to_obj.replace(hour=23, minute=59, second=59)
    except ValueError:
        return Response({'error': 'Formato de fecha inválido. Use YYYY-MM-DD'}, status=400)
    
    # Query base
    queryset = Sale.objects.filter(
        created_at__gte=date_from_obj,
        created_at__lte=date_to_obj
    ).select_related('branch', 'user')
    
    # Filtrar por empresa del usuario
    if request.user.role != 'super_admin':
        queryset = queryset.filter(branch__company=request.user.company)
    
    # Filtrar por sucursal si se especifica
    if branch_id:
        queryset = queryset.filter(branch_id=branch_id)
    
    # Calcular estadísticas
    total_sales = queryset.count()
    total_revenue = queryset.aggregate(Sum('total'))['total__sum'] or 0
    avg_ticket = queryset.aggregate(Avg('total'))['total__avg'] or 0
    
    # Ventas por sucursal
    sales_by_branch = queryset.values('branch__name').annotate(
        count=Count('id'),
        revenue=Sum('total')
    ).order_by('-revenue')
    
    # Ventas por método de pago
    sales_by_payment = queryset.values('payment_method').annotate(
        count=Count('id'),
        revenue=Sum('total')
    ).order_by('-revenue')
    
    # Ventas por vendedor
    sales_by_seller = queryset.values('user__username', 'user__first_name', 'user__last_name').annotate(
        count=Count('id'),
        revenue=Sum('total')
    ).order_by('-revenue')[:10]
    
    return Response({
        'period': {
            'from': date_from,
            'to': date_to
        },
        'summary': {
            'total_sales': total_sales,
            'total_revenue': float(total_revenue),
            'average_ticket': float(avg_ticket)
        },
        'by_branch': list(sales_by_branch),
        'by_payment_method': list(sales_by_payment),
        'top_sellers': list(sales_by_seller)
    })
