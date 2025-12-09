from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SaleViewSet, OrderViewSet
from .reports import stock_report, sales_report

router = DefaultRouter()
router.register(r'sales', SaleViewSet, basename='sale')
router.register(r'orders', OrderViewSet, basename='order')

urlpatterns = [
    path('', include(router.urls)),
    path('reports/stock/', stock_report, name='stock-report'),
    path('reports/sales/', sales_report, name='sales-report'),
]
