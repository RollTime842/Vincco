from rest_framework import routers
from .api import (
    UnidadMedidaViewSet,
    ProductoViewSet,
    GaleriaProductoViewSet,
    ServicioViewSet,
    GaleriaServicioViewSet,
    CatalogoViewSet
)

app_name = "inventario"


router = routers.DefaultRouter()
router.register(r'Unidades-medidas',UnidadMedidaViewSet,basename='unidad')
router.register(r'productos',ProductoViewSet,basename='producto')
router.register(r'galeria-productdos',GaleriaProductoViewSet,basename='galeria_producto')
router.register(r'servicios',ServicioViewSet,basename='servicio')
router.register(r'galeria-servicios',GaleriaServicioViewSet,basename='galeria_servicio')
router.register(r'catalogos',CatalogoViewSet,basename='catalogo')
urlpatterns = router.urls