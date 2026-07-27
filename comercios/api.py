from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.views import APIView
from rest_framework.response import Response
from core.permissions import EsAdminOSoloLectura, EsProveedorOEmprendedor
from usuarios.models import PerfilUsuario
from .models import EstadoNegocioChoices,TipoSucursalChoices

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

from .utils import haversine

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
        try:
            perfil_usuario = self.request.user.perfil
        except PerfilUsuario.DoesNotExist:
            raise ValidationError(
                "Debes completar tu perfil de usuario antes de registrar un negocio."
            )

        pendientes = PerfilNegocio.objects.filter(
            perfil_usuario=perfil_usuario,
            estado=EstadoNegocioChoices.EN_REVISION
        ).count()

        if pendientes >= 3:
            raise ValidationError(
                "Ya tienes 3 negocios pendientes de revisión. "
                "Espera a que un Administrador apruebe o rechace alguno antes de registrar otro."
            )

        serializer.save(perfil_usuario=perfil_usuario)

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def directorio(self, request):
        negocios = (
            PerfilNegocio.objects
            .activos()
            .por_sub_rubro(request.query_params.get('sub_rubro'))
            .buscar(request.query_params.get('q'))
        )
        serializer = self.get_serializer(negocios, many=True)
        return Response(serializer.data)

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


class MisNegociosPendientesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            perfil_usuario = request.user.perfil
        except PerfilUsuario.DoesNotExist:
            return Response({'pendientes': 0, 'limite': 3})

        pendientes = PerfilNegocio.objects.filter(
            perfil_usuario=perfil_usuario,
            estado=EstadoNegocioChoices.EN_REVISION
        ).count()

        return Response({'pendientes': pendientes, 'limite': 3})


class SucursalViewSet(viewsets.ModelViewSet):
    serializer_class = SucursalSerializer
    permission_classes = [IsAuthenticated]  # sin EsAdminOSoloLectura

    def get_queryset(self):
        if self.request.user.groups.filter(name='Administrador').exists():
            return Sucursal.objects.all()
        return Sucursal.objects.filter(negocio__perfil_usuario__usuario=self.request.user)

    def perform_create(self, serializer):
        negocio = serializer.validated_data.get('negocio')
        es_admin = self.request.user.groups.filter(name='Administrador').exists()
        es_dueño = negocio.perfil_usuario.usuario == self.request.user

        if not es_admin and not es_dueño:
            raise PermissionDenied("No puedes crear sucursales para un negocio que no es tuyo.")

        serializer.save()

    def perform_update(self, serializer):
        instancia = self.get_object()
        es_admin = self.request.user.groups.filter(name='Administrador').exists()
        es_dueño = instancia.negocio.perfil_usuario.usuario == self.request.user

        if not es_admin and not es_dueño:
            raise PermissionDenied("No puedes editar la sucursal de un negocio que no es tuyo.")

        serializer.save()

    def perform_destroy(self, instance):
        es_admin = self.request.user.groups.filter(name='Administrador').exists()
        es_dueño = instance.negocio.perfil_usuario.usuario == self.request.user

        if not es_admin and not es_dueño:
            raise PermissionDenied("No puedes eliminar la sucursal de un negocio que no es tuyo.")

        instance.delete()


class ContactoSucursalViewSet(viewsets.ModelViewSet):
    queryset = ContactoSucursal.objects.all().order_by('nombre')
    permission_classes = [IsAuthenticated, EsAdminOSoloLectura]
    serializer_class = ContactoSucursalSerializer

class SucursalesCercanasView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            lat_usuario = float(request.query_params.get('lat'))
            lng_usuario = float(request.query_params.get('lng'))
        except (TypeError, ValueError):
            return Response(
                {'detail': 'Debes enviar los parámetros lat y lng como números.'},
                status=400
            )

        sucursales = Sucursal.objects.filter(
            tipo_presencia=TipoSucursalChoices.LOCAL_FISICO,
            latitud__isnull=False,
            longitud__isnull=False,
            negocio__estado=EstadoNegocioChoices.ACTIVO,
        ).select_related('negocio')

        # Filtro opcional por sub_rubro
        sub_rubro_id = request.query_params.get('sub_rubro')
        if sub_rubro_id:
            sucursales = sucursales.filter(negocio__sub_rubro_id=sub_rubro_id)

        resultados = []
        for sucursal in sucursales:
            distancia = haversine(
                lat_usuario, lng_usuario,
                float(sucursal.latitud), float(sucursal.longitud)
            )
            resultados.append({
                'sucursal_id': sucursal.id,
                'sucursal_nombre': sucursal.nombre,
                'negocio_id': sucursal.negocio.id,
                'negocio_nombre': sucursal.negocio.nombre,
                'latitud': sucursal.latitud,
                'longitud': sucursal.longitud,
                'distancia_km': round(distancia, 2),
            })

        resultados.sort(key=lambda r: r['distancia_km'])

        limite = int(request.query_params.get('limite', 20))
        return Response(resultados[:limite])