from rest_framework import viewsets,permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated  
from core.permissions import EsAdminOSoloLectura

from .models import (
    UnidadMedida,
    Producto,
    GaleriaProducto,
    Servicio,
    GaleriaServicio,
    Catalogo
)

from .serializers import (
    UnidadMedidaSerializer,
    ProductoSerializer,
    GaleriaProductoSerializer,
    ServicioSerializer,
    GaleriaServicioSerializer,
    CatalogoSerializer
)

class UnidadMedidaViewSet(viewsets.ModelViewSet):
    queryset = UnidadMedida.objects.all().order_by('id')
    permission_classes = [IsAuthenticated, EsAdminOSoloLectura]
    serializer_class = UnidadMedidaSerializer

class ProductoViewSet(viewsets.ModelViewSet):
    serializer_class = ProductoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.groups.filter(name='Administrador').exists():
            return Producto.objects.all().order_by('id')
        return Producto.objects.filter(
            negocio__perfil_usuario__usuario=self.request.user
        ).order_by('id')

    def perform_create(self, serializer):
        negocio = serializer.validated_data.get('negocio')
        es_admin = self.request.user.groups.filter(name='Administrador').exists()
        es_dueño = negocio.perfil_usuario.usuario == self.request.user

        if not es_admin and not es_dueño:
            raise PermissionDenied("No puedes crear productos para un negocio que no es tuyo.")
        serializer.save()

    def perform_update(self, serializer):
        instancia = self.get_object()
        es_admin = self.request.user.groups.filter(name='Administrador').exists()
        es_dueño = instancia.negocio.perfil_usuario.usuario == self.request.user

        if not es_admin and not es_dueño:
            raise PermissionDenied("No puedes editar productos de un negocio que no es tuyo.")
        serializer.save()

    def perform_destroy(self, instance):
        es_admin = self.request.user.groups.filter(name='Administrador').exists()
        es_dueño = instance.negocio.perfil_usuario.usuario == self.request.user

        if not es_admin and not es_dueño:
            raise PermissionDenied("No puedes eliminar productos de un negocio que no es tuyo.")
        instance.delete()

class GaleriaProductoViewSet(viewsets.ModelViewSet):
    serializer_class = GaleriaProductoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.groups.filter(name='Administrador').exists():
            return GaleriaProducto.objects.all().order_by('id')
        return GaleriaProducto.objects.filter(
            producto__negocio__perfil_usuario__usuario=self.request.user
        ).order_by('id')

    def perform_create(self, serializer):
        producto = serializer.validated_data.get('producto')
        es_admin = self.request.user.groups.filter(name='Administrador').exists()
        es_dueño = producto.negocio.perfil_usuario.usuario == self.request.user

        if not es_admin and not es_dueño:
            raise PermissionDenied("No puedes agregar imágenes a un producto que no es tuyo.")
        serializer.save()

    def perform_update(self, serializer):
        instancia = self.get_object()
        es_admin = self.request.user.groups.filter(name='Administrador').exists()
        es_dueño = instancia.producto.negocio.perfil_usuario.usuario == self.request.user

        if not es_admin and not es_dueño:
            raise PermissionDenied("No puedes editar imágenes de un producto que no es tuyo.")
        serializer.save()

    def perform_destroy(self, instance):
        es_admin = self.request.user.groups.filter(name='Administrador').exists()
        es_dueño = instance.producto.negocio.perfil_usuario.usuario == self.request.user

        if not es_admin and not es_dueño:
            raise PermissionDenied("No puedes eliminar imágenes de un producto que no es tuyo.")
        instance.delete()

class ServicioViewSet(viewsets.ModelViewSet):
    serializer_class = ServicioSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.groups.filter(name='Administrador').exists():
            return Servicio.objects.all().order_by('id')
        return Servicio.objects.filter(
            negocio__perfil_usuario__usuario=self.request.user
        ).order_by('id')

    def perform_create(self, serializer):
        negocio = serializer.validated_data.get('negocio')
        es_admin = self.request.user.groups.filter(name='Administrador').exists()
        es_dueño = negocio.perfil_usuario.usuario == self.request.user

        if not es_admin and not es_dueño:
            raise PermissionDenied("No puedes crear servicios para un negocio que no es tuyo.")
        serializer.save()

    def perform_update(self, serializer):
        instancia = self.get_object()
        es_admin = self.request.user.groups.filter(name='Administrador').exists()
        es_dueño = instancia.negocio.perfil_usuario.usuario == self.request.user

        if not es_admin and not es_dueño:
            raise PermissionDenied("No puedes editar servicios de un negocio que no es tuyo.")
        serializer.save()

    def perform_destroy(self, instance):
        es_admin = self.request.user.groups.filter(name='Administrador').exists()
        es_dueño = instance.negocio.perfil_usuario.usuario == self.request.user

        if not es_admin and not es_dueño:
            raise PermissionDenied("No puedes eliminar servicios de un negocio que no es tuyo.")
        instance.delete()

class GaleriaServicioViewSet(viewsets.ModelViewSet):
    serializer_class = GaleriaServicioSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.groups.filter(name='Administrador').exists():
            return GaleriaServicio.objects.all().order_by('id')
        return GaleriaServicio.objects.filter(
            servicio__negocio__perfil_usuario__usuario=self.request.user
        ).order_by('id')

    def perform_create(self, serializer):
        servicio = serializer.validated_data.get('servicio')
        es_admin = self.request.user.groups.filter(name='Administrador').exists()
        es_dueño = servicio.negocio.perfil_usuario.usuario == self.request.user

        if not es_admin and not es_dueño:
            raise PermissionDenied("No puedes agregar imágenes a un servicio que no es tuyo.")
        serializer.save()

    def perform_update(self, serializer):
        instancia = self.get_object()
        es_admin = self.request.user.groups.filter(name='Administrador').exists()
        es_dueño = instancia.servicio.negocio.perfil_usuario.usuario == self.request.user

        if not es_admin and not es_dueño:
            raise PermissionDenied("No puedes editar imágenes de un servicio que no es tuyo.")
        serializer.save()

    def perform_destroy(self, instance):
        es_admin = self.request.user.groups.filter(name='Administrador').exists()
        es_dueño = instance.servicio.negocio.perfil_usuario.usuario == self.request.user

        if not es_admin and not es_dueño:
            raise PermissionDenied("No puedes eliminar imágenes de un servicio que no es tuyo.")
        instance.delete()

class CatalogoViewSet(viewsets.ModelViewSet):
    serializer_class = CatalogoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.groups.filter(name='Administrador').exists():
            return Catalogo.objects.all().order_by('id')
        return Catalogo.objects.filter(
            sucursal__negocio__perfil_usuario__usuario=self.request.user
        ).order_by('id')

    def perform_create(self, serializer):
        sucursal = serializer.validated_data.get('sucursal')
        es_admin = self.request.user.groups.filter(name='Administrador').exists()
        es_dueño = sucursal.negocio.perfil_usuario.usuario == self.request.user

        if not es_admin and not es_dueño:
            raise PermissionDenied("No puedes agregar ítems al catálogo de una sucursal que no es tuya.")
        serializer.save()

    def perform_update(self, serializer):
        instancia = self.get_object()
        es_admin = self.request.user.groups.filter(name='Administrador').exists()
        es_dueño = instancia.sucursal.negocio.perfil_usuario.usuario == self.request.user

        if not es_admin and not es_dueño:
            raise PermissionDenied("No puedes editar el catálogo de una sucursal que no es tuya.")
        serializer.save()

    def perform_destroy(self, instance):
        es_admin = self.request.user.groups.filter(name='Administrador').exists()
        es_dueño = instance.sucursal.negocio.perfil_usuario.usuario == self.request.user

        if not es_admin and not es_dueño:
            raise PermissionDenied("No puedes eliminar del catálogo de una sucursal que no es tuya.")
        instance.delete()