from django.urls import path
from rest_framework import routers
from .api import DepartamentoViewSet, EstadoTOTPView, UsuarioViewSet
from .api import MunicipioViewSet
from .api import PerfilUsuarioViewSet
from .api import ActivarTOTPView, ConfirmarTOTPView, LoginPaso1View, VerificarTOTPView

app_name = 'usuarios'

router = routers.DefaultRouter()
router.register(r'departamentos', DepartamentoViewSet, basename='departamento')
router.register(r'municipios', MunicipioViewSet, basename='municipio')
router.register(r'perfil-usuario', PerfilUsuarioViewSet, basename='perfil')
router.register(r'usuarios', UsuarioViewSet, basename='usuario')

urlpatterns = router.urls + [
    path('totp/activar/', ActivarTOTPView.as_view(), name='totp-activar'),
    path('totp/confirmar/', ConfirmarTOTPView.as_view(), name='totp-confirmar'),
    path('login/paso1/', LoginPaso1View.as_view(), name='login-paso1'),
    path('login/verificar-totp/', VerificarTOTPView.as_view(), name='verificar-totp'),
    path('totp/estado/', EstadoTOTPView.as_view(), name='totp-estado'),
]