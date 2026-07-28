from rest_framework.permissions import BasePermission,SAFE_METHODS

class EsProveedorOEmprendedor(BasePermission):
    message = "Solo usuarios Proveedor o Emprendedor pueden registrar negocios."

    def has_permission(self, request, view):
        if view.action != 'create':
            return True

        return request.user.groups.filter(
            name__in=['Proveedor', 'Emprendedor']
        ).exists()


