from rest_framework import routers
from .api import (
    PedidoViewSet,
    DetallePedidoViewSet,
    HistorialPuntosViewSet,
    CotizacionViewSet,
    ItemCotizacionViewSet,
    MensajeCotizacionViewSet
    )

app_name = "transacciones"

router = routers.DefaultRouter()
router.register(r'pedidos',PedidoViewSet,basename='pedido')
router.register(r'detalles-pedidos',DetallePedidoViewSet,basename='detalle')
router.register(r'historiales-pedidos',HistorialPuntosViewSet,basename='Historial')
router.register(r'cotizaciones',CotizacionViewSet,basename='cotizacion')
router.register(r'item-cotizaciones',ItemCotizacionViewSet,basename='item')
router.register(r'mensaje-cotizacion',MensajeCotizacionViewSet,basename='mensaje')
urlpatterns = router.urls