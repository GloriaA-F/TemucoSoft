from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BranchViewSet, InventoryViewSet, InventoryMovementViewSet, PurchaseViewSet

router = DefaultRouter()
router.register(r'branches', BranchViewSet, basename='branch')
router.register(r'inventory', InventoryViewSet, basename='inventory')
router.register(r'inventory-movements', InventoryMovementViewSet, basename='inventory-movement')
router.register(r'purchases', PurchaseViewSet, basename='purchase')

urlpatterns = [
    path('', include(router.urls)),
]
