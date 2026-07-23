from rest_framework import routers
from .api import (
    RubroPrincipalViewSet,
    SubRubroViewSet,
    PerfilNegocioViewSet,
    SucursalViewSet,
    ContactoSucursalViewSet
)

app_name = "comercios"

router = routers.DefaultRouter()
router.register(r'rubros-principales', RubroPrincipalViewSet, basename='rubro_principal')
router.register(r'sub-rubros', SubRubroViewSet, basename='sub_rubro')
router.register(r'perfiles-negocios', PerfilNegocioViewSet, basename='perfil_negocio')
router.register(r'sucursales', SucursalViewSet, basename='sucursal')
router.register(r'contactos-sucursales', ContactoSucursalViewSet, basename='contacto_sucursal')
urlpatterns = router.urls