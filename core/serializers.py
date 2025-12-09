from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User, Company, Subscription


class CompanySerializer(serializers.ModelSerializer):
    """Serializer para empresas"""
    
    class Meta:
        model = Company
        fields = [
            'id', 'name', 'rut', 'contact_email', 'contact_phone',
            'address', 'is_active', 'created_at'
        ]
        read_only_fields = ['created_at']


class SubscriptionSerializer(serializers.ModelSerializer):
    """Serializer para suscripciones"""
    company_name = serializers.CharField(source='company.name', read_only=True)
    plan_display = serializers.CharField(source='get_plan_name_display', read_only=True)
    
    class Meta:
        model = Subscription
        fields = [
            'id', 'company', 'company_name', 'plan_name', 'plan_display',
            'start_date', 'end_date', 'active', 'max_branches', 'max_users'
        ]
    
    def validate(self, data):
        if data.get('end_date') and data.get('start_date'):
            if data['end_date'] <= data['start_date']:
                raise serializers.ValidationError(
                    "La fecha de término debe ser posterior a la fecha de inicio"
                )
        return data


class UserSerializer(serializers.ModelSerializer):
    """Serializer para usuarios"""
    company_name = serializers.CharField(source='company.name', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    password = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'rut', 'role', 'role_display', 'company', 'company_name',
            'is_active', 'created_at', 'password'
        ]
        read_only_fields = ['created_at']
        extra_kwargs = {
            'password': {'write_only': True}
        }
    
    def validate_password(self, value):
        if value:
            validate_password(value)
        return value
    
    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = User.objects.create(**validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user
    
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if password:
            instance.set_password(password)
        
        instance.save()
        return instance


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer específico para creación de usuarios"""
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name',
            'rut', 'role', 'company', 'password', 'password2'
        ]
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Las contraseñas no coinciden"})
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserMeSerializer(serializers.ModelSerializer):
    """Serializer para información del usuario autenticado"""
    company_name = serializers.CharField(source='company.name', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'rut', 'role', 'role_display', 'company', 'company_name',
            'is_active', 'created_at'
        ]
        read_only_fields = fields
