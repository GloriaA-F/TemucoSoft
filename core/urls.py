from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CompanyViewSet, SubscriptionViewSet, UserViewSet

router = DefaultRouter()
router.register(r'companies', CompanyViewSet, basename='company')
router.register(r'subscriptions', SubscriptionViewSet, basename='subscription')
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    path('', include(router.urls)),
]
