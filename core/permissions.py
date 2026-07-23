from rest_framework.permissions import BasePermission,SAFE_METHODS

class EsProveedorOEmprendedor(BasePermission):
    message = "Solo usuarios Proveedor o Emprendedor pueden registrar negocios."

    def has_permission(self, request, view):
        if view.action != 'create':
            return True

        return request.user.groups.filter(
            name__in=['Proveedor', 'Emprendedor']
        ).exists()



class EsAdminOSoloLectura(BasePermission):
    """
    Cualquier usuario autenticado puede leer (GET, HEAD, OPTIONS).
    Solo el grupo Administrador puede crear/editar/borrar.
    """
    message = "Solo un Administrador puede modificar este recurso."

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.groups.filter(
            name='Administrador'
        ).exists()