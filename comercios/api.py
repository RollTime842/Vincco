from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated  
from rest_framework.exceptions import PermissionDenied   
from core.permissions import EsAdminOSoloLectura, EsProveedorOEmprendedor

from .models import (
    RubroPrincipal,
    SubRubro,
    PerfilNegocio,
    Sucursal,
    ContactoSucursal,
)

from .serializers import (
    RubroPrincipalSerializer,
    SubRubroSerializer,
    PerfilNegocioSerializer,
    SucursalSerializer,
    ContactoSucursalSerializer,
)

class RubroPrincipalViewSet(viewsets.ModelViewSet):
    queryset = RubroPrincipal.objects.all().order_by('nombre')
    permission_classes = [IsAuthenticated, EsAdminOSoloLectura]
    serializer_class = RubroPrincipalSerializer

class SubRubroViewSet(viewsets.ModelViewSet):
    queryset = SubRubro.objects.all().order_by('nombre')
    permission_classes = [IsAuthenticated, EsAdminOSoloLectura]
    serializer_class = SubRubroSerializer


class PerfilNegocioViewSet(viewsets.ModelViewSet):
    serializer_class = PerfilNegocioSerializer
    permission_classes = [IsAuthenticated, EsProveedorOEmprendedor]

    def get_queryset(self):
        if self.request.user.groups.filter(name='Administrador').exists():
            return PerfilNegocio.objects.all()
        return PerfilNegocio.objects.filter(perfil_usuario__usuario=self.request.user)

    def perform_create(self, serializer):
        perfil_usuario = self.request.user.perfil
        serializer.save(perfil_usuario=perfil_usuario)

    def perform_update(self, serializer):
        instancia = self.get_object()
        es_admin = self.request.user.groups.filter(name='Administrador').exists()
        es_dueño = instancia.perfil_usuario.usuario == self.request.user

        if not es_admin and not es_dueño:
            raise PermissionDenied("No puedes editar el negocio de otro usuario.")

        if not es_admin:
            serializer.validated_data.pop('estado', None)
            serializer.validated_data.pop('perfil_usuario', None)

        serializer.save()

    def perform_destroy(self, instance):
        es_admin = self.request.user.groups.filter(name='Administrador').exists()
        es_dueño = instance.perfil_usuario.usuario == self.request.user

        if not es_admin and not es_dueño:
            raise PermissionDenied("No puedes eliminar el negocio de otro usuario.")

        instance.delete()

class SucursalViewSet(viewsets.ModelViewSet):
    queryset = Sucursal.objects.all().order_by('nombre')
    permission_classes = [IsAuthenticated, EsAdminOSoloLectura]
    serializer_class = SucursalSerializer

class ContactoSucursalViewSet(viewsets.ModelViewSet):
    queryset = ContactoSucursal.objects.all().order_by('nombre')
    permission_classes = [IsAuthenticated, EsAdminOSoloLectura]
    serializer_class = ContactoSucursalSerializer