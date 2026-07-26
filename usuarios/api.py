from rest_framework.permissions import SAFE_METHODS, BasePermission
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
import pyotp, qrcode, io, base64
from django.contrib.auth import authenticate


from core.permissions import EsAdminOSoloLectura
from .models import EstadoVerificacionChoices
from .models import DispositivoTOTP


from .models import (
    Departamento,
    Municipio,
    PerfilUsuario,
)
from rest_framework import request, viewsets,permissions
from rest_framework.permissions import IsAuthenticated  
from django.contrib.auth.models import User
from .serializers import (
    DepartamentoSerializer,
    MunicipioSerializer,
    PerfilUsuarioSerializer,
    RegistroUsuarioSerializer,
    UsuarioSerializer,
)



class EsAdministradorOSoloLectura(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return request.user.is_authenticated
        return request.user.groups.filter(name='Administrador').exists()
        
class DepartamentoViewSet(viewsets.ModelViewSet):
    """API endpoint que permite ver o editar Departamentos."""
    queryset = Departamento.objects.all().order_by('id')
    permission_classes = [permissions.IsAuthenticated,EsAdministradorOSoloLectura]
    serializer_class = DepartamentoSerializer

class MunicipioViewSet(viewsets.ModelViewSet):
    """API endpoint que permite ver o editar Municipios."""
    queryset = Municipio.objects.all().order_by('id')
    permission_classes = [IsAuthenticated, EsAdminOSoloLectura]
    serializer_class = MunicipioSerializer


CAMPOS_BLOQUEADOS_POST_VERIFICACION = ['cedula']


class PerfilUsuarioViewSet(viewsets.ModelViewSet):
    serializer_class = PerfilUsuarioSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    http_method_names = ['get', 'post', 'patch', 'head', 'options']

    def get_queryset(self):
        if self.request.user.groups.filter(name='Administrador').exists():
            return PerfilUsuario.objects.all()
        return PerfilUsuario.objects.filter(usuario=self.request.user)

    def perform_create(self, serializer):
        if PerfilUsuario.objects.filter(usuario=self.request.user).exists():
            raise ValidationError("Ya tienes un perfil creado.")

        serializer.save(
            usuario=self.request.user,
            estado_verificacion=EstadoVerificacionChoices.PENDIENTE,
        )

    def perform_update(self, serializer):
        user = self.request.user
        es_admin = user.groups.filter(name='Administrador').exists()
        instancia = self.get_object()

        if not es_admin:
            # Campos que nunca puede tocar un usuario común
            for campo in ['estado_verificacion', 'verificado_por', 'fecha_revision', 'usuario']:
                serializer.validated_data.pop(campo, None)

            # Cédula bloqueada una vez verificado (protege la validez de la aprobación)
            if instancia.estado_verificacion == EstadoVerificacionChoices.VERIFICADO:
                for campo in CAMPOS_BLOQUEADOS_POST_VERIFICACION:
                    serializer.validated_data.pop(campo, None)

        serializer.save()

    @action(detail=True, methods=['post'])
    def aprobar(self, request, pk=None):
        if not request.user.groups.filter(name='Administrador').exists():
            raise PermissionDenied("Solo un Administrador puede aprobar verificaciones.")

        perfil = self.get_object()

        if perfil.estado_verificacion == EstadoVerificacionChoices.VERIFICADO:
            raise ValidationError("Este perfil ya está verificado.")

        if not perfil.documento_identidad:
            raise ValidationError(
                "No se puede aprobar: el usuario aún no ha subido su documento de identidad."
            )

        perfil.estado_verificacion = EstadoVerificacionChoices.VERIFICADO
        perfil.verificado_por = request.user
        perfil.fecha_revision = timezone.now()
        perfil.motivo_rechazo = ''
        perfil.save()

        return Response({'detail': 'Perfil verificado correctamente.'})

    @action(detail=True, methods=['post'])
    def rechazar(self, request, pk=None):
        if not request.user.groups.filter(name='Administrador').exists():
            raise PermissionDenied("Solo un Administrador puede rechazar verificaciones.")

        perfil = self.get_object()

        if perfil.estado_verificacion != EstadoVerificacionChoices.PENDIENTE:
            raise ValidationError("Esta solicitud ya fue procesada.")

        perfil.estado_verificacion = EstadoVerificacionChoices.RECHAZADO
        perfil.verificado_por = request.user
        perfil.fecha_revision = timezone.now()
        perfil.motivo_rechazo = request.data.get('motivo', '')
        perfil.save()

        return Response({'detail': 'Perfil rechazado.'})

class UsuarioViewSet(viewsets.ModelViewSet):
    serializer_class = UsuarioSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'create':
            return RegistroUsuarioSerializer
        return UsuarioSerializer

    def perform_update(self, serializer):
        user = self.request.user
        es_admin = user.groups.filter(name='Administrador').exists()
        if not es_admin:
            for campo in ['estado_verificacion', 'verificado_por', 'fecha_revision', 'usuario',
                          'is_staff', 'is_superuser', 'is_active', 'groups']:
                serializer.validated_data.pop(campo, None)
        serializer.save()

    def get_queryset(self):
        if self.request.user.groups.filter(name='Administrador').exists():
            return User.objects.all().order_by('first_name')
        return User.objects.filter(pk=self.request.user.pk)

    def perform_destroy(self, instance):
        user = self.request.user
        es_admin = user.groups.filter(name='Administrador').exists()
        if not es_admin and instance.pk != user.pk:
            raise PermissionDenied("No puedes eliminar la cuenta de otro usuario.")
        instance.delete()

class ActivarTOTPView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        secreto = pyotp.random_base32()
        DispositivoTOTP.objects.update_or_create(
            usuario=request.user,
            defaults={'secreto': secreto, 'confirmado': False}
        )

        totp = pyotp.TOTP(secreto)
        uri = totp.provisioning_uri(name=request.user.username, issuer_name="Vincco")

        img = qrcode.make(uri)
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        qr_base64 = base64.b64encode(buffer.getvalue()).decode()

        return Response({'qr_code': f"data:image/png;base64,{qr_base64}"})


class ConfirmarTOTPView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        codigo = request.data.get('codigo')
        try:
            dispositivo = DispositivoTOTP.objects.get(usuario=request.user)
        except DispositivoTOTP.DoesNotExist:
            return Response({'detail': 'Primero activa el TOTP'}, status=400)

        if dispositivo.verificar_codigo(codigo):
            dispositivo.confirmado = True
            dispositivo.save()
            return Response({'detail': 'TOTP activado correctamente'})

        return Response({'detail': 'Código incorrecto'}, status=400)



class EstadoTOTPView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        activado = DispositivoTOTP.objects.filter(
            usuario=request.user, confirmado=True
        ).exists()
        return Response({'activado': activado})

# usuarios/api.py
class LoginConCookieView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)

        if not user:
            return Response({'detail': 'Credenciales inválidas'}, status=401)

        tiene_2fa = DispositivoTOTP.objects.filter(usuario=user, confirmado=True).exists()

        if tiene_2fa:
            return Response({'requiere_2fa': True, 'user_id': user.id})

        refresh = RefreshToken.for_user(user)
        response = Response({
            'requiere_2fa': False,
            'requiere_configurar_2fa': True,
            'access': str(refresh.access_token),
        })
        response.set_cookie(
            key='refresh_token', value=str(refresh),
            httponly=True, secure=False, samesite='Lax',
            max_age=7 * 24 * 60 * 60, path='/api/',
        )
        return response


class VerificarTOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        user_id = request.data.get('user_id')
        codigo = request.data.get('codigo')

        try:
            dispositivo = DispositivoTOTP.objects.get(usuario_id=user_id, confirmado=True)
        except DispositivoTOTP.DoesNotExist:
            return Response({'detail': '2FA no configurado'}, status=400)

        if not dispositivo.verificar_codigo(codigo):
            return Response({'detail': 'Código inválido'}, status=400)

        user = User.objects.get(pk=user_id)
        refresh = RefreshToken.for_user(user)

        response = Response({'access': str(refresh.access_token)})
        response.set_cookie(
            key='refresh_token', value=str(refresh),
            httponly=True, secure=False, samesite='Lax',
            max_age=7 * 24 * 60 * 60, path='/api/',
        )
        return response

class RefreshConCookieView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.COOKIES.get('refresh_token')
        if not refresh_token:
            return Response({'detail': 'No hay sesión activa.'}, status=401)
        try:
            refresh = RefreshToken(refresh_token)
            return Response({'access': str(refresh.access_token)})
        except Exception:
            return Response({'detail': 'Sesión inválida o expirada.'}, status=401)


class LogoutConCookieView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.COOKIES.get('refresh_token')
        if refresh_token:
            try:
                RefreshToken(refresh_token).blacklist()
            except Exception:
                pass

        response = Response({'detail': 'Sesión cerrada.'})
        response.delete_cookie('refresh_token', path='/api/')
        return response