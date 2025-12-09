from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import authenticate
from .models import User, Company, Subscription
from .serializers import (
    UserSerializer, UserCreateSerializer, UserMeSerializer,
    CompanySerializer, SubscriptionSerializer
)
from .permissions import IsSuperAdmin, IsAdminCliente


class CompanyViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de empresas (solo super_admin)
    """
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsSuperAdmin]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'super_admin':
            return Company.objects.all()
        elif user.company:
            return Company.objects.filter(id=user.company.id)
        return Company.objects.none()
    
    @action(detail=True, methods=['post'], permission_classes=[IsSuperAdmin])
    def subscribe(self, request, pk=None):
        """
        Endpoint para asignar/actualizar suscripción a una empresa
        """
        company = self.get_object()
        serializer = SubscriptionSerializer(data=request.data)
        
        if serializer.is_valid():
            # Verificar si ya tiene suscripción
            try:
                subscription = company.subscription
                # Actualizar
                for key, value in serializer.validated_data.items():
                    setattr(subscription, key, value)
                subscription.save()
            except Subscription.DoesNotExist:
                # Crear nueva
                serializer.save(company=company)
            
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SubscriptionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para ver suscripciones
    """
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'super_admin':
            return Subscription.objects.all()
        elif user.company:
            return Subscription.objects.filter(company=user.company)
        return Subscription.objects.none()


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de usuarios
    """
    queryset = User.objects.all()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer
    
    def get_permissions(self):
        if self.action == 'me':
            permission_classes = [IsAuthenticated]
        elif self.action == 'create':
            permission_classes = [IsAdminCliente]
        else:
            permission_classes = [IsAdminCliente]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'super_admin':
            return User.objects.all()
        elif user.role == 'admin_cliente' and user.company:
            return User.objects.filter(company=user.company)
        return User.objects.filter(id=user.id)
    
    def perform_create(self, serializer):
        """
        Al crear un usuario, asignar la empresa del usuario que crea
        """
        user = self.request.user
        if user.role == 'super_admin':
            # Super admin puede asignar cualquier empresa
            serializer.save()
        else:
            # Admin_cliente solo puede crear usuarios de su empresa
            serializer.save(company=user.company)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """
        Endpoint para obtener información del usuario autenticado
        """
        serializer = UserMeSerializer(request.user)
        return Response(serializer.data)
