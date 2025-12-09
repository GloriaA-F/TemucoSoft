from rest_framework import permissions


class IsSuperAdmin(permissions.BasePermission):
    """
    Permiso solo para super_admin
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role == 'super_admin' and
            request.user.is_active
        )


class IsAdminCliente(permissions.BasePermission):
    """
    Permiso para admin_cliente (puede ver todo de su empresa)
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role in ['super_admin', 'admin_cliente'] and
            request.user.is_active
        )


class IsGerente(permissions.BasePermission):
    """
    Permiso para gerente (gestión de inventario y reportes)
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role in ['super_admin', 'admin_cliente', 'gerente'] and
            request.user.is_active
        )


class IsVendedor(permissions.BasePermission):
    """
    Permiso para vendedor (puede hacer ventas)
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role in ['super_admin', 'admin_cliente', 'gerente', 'vendedor'] and
            request.user.is_active
        )


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permiso para objetos: solo el dueño puede editar
    """
    def has_object_permission(self, request, view, obj):
        # Lectura permitida para cualquiera autenticado
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Escritura solo para el dueño
        return obj.user == request.user


class IsSameCompany(permissions.BasePermission):
    """
    Verifica que el usuario pertenezca a la misma empresa que el objeto
    """
    def has_object_permission(self, request, view, obj):
        # Super admin puede ver todo
        if request.user.role == 'super_admin':
            return True
        
        # Verificar que el objeto tenga company y sea la misma
        if hasattr(obj, 'company'):
            return obj.company == request.user.company
        
        return False


class CanManageProducts(permissions.BasePermission):
    """
    Permiso para gestionar productos (admin_cliente y gerente)
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Lectura: todos los roles autenticados
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_active
        
        # Escritura: solo admin_cliente y gerente
        return (
            request.user.role in ['super_admin', 'admin_cliente', 'gerente'] and
            request.user.is_active
        )


class CanManageInventory(permissions.BasePermission):
    """
    Permiso para gestionar inventario
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Lectura: vendedor también puede ver
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_active
        
        # Escritura: solo admin_cliente y gerente
        return (
            request.user.role in ['super_admin', 'admin_cliente', 'gerente'] and
            request.user.is_active
        )


class CanCreateSales(permissions.BasePermission):
    """
    Permiso para crear ventas (todos excepto cliente_final)
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role != 'cliente_final' and
            request.user.is_active
        )


class CanViewReports(permissions.BasePermission):
    """
    Permiso para ver reportes (admin_cliente y gerente)
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role in ['super_admin', 'admin_cliente', 'gerente'] and
            request.user.is_active
        )
