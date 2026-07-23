from rest_framework import viewsets,permissions
from rest_framework.permissions import IsAuthenticated  
from django.contrib.auth.models import User

from .models import (
    Pedido,
    DetallePedido,
    HistorialPuntos,
    Cotizacion,
    ItemCotizacion,
    MensajeCotizacion,
)
from .serializers import (
    PedidoSerializer,
    DetallePedidoSerializer,
    HistorialPuntosSerializer,
    CotizacionSerializer,
    ItemCotizacionSerializer,
    MensajeCotizacionSerializer
)

class PedidoViewSet(viewsets.ModelViewSet):
    """API endpoint que permite ver o editar Pedidos."""
    queryset = Pedido.objects.all().order_by('id')
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PedidoSerializer

class DetallePedidoViewSet(viewsets.ModelViewSet):
    """API endpoint que permite ver o editar Detalles de Pedidos."""
    queryset = DetallePedido.objects.all().order_by('id')
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = DetallePedidoSerializer

class HistorialPuntosViewSet(viewsets.ModelViewSet):
    """API endpoint que permite ver o editar Historial de Puntos."""
    queryset = HistorialPuntos.objects.all().order_by('id')
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = HistorialPuntosSerializer

class CotizacionViewSet(viewsets.ModelViewSet):
    """API endpoint que permite ver o editar Cotizaciones."""
    queryset = Cotizacion.objects.all().order_by('id')
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CotizacionSerializer

class ItemCotizacionViewSet(viewsets.ModelViewSet):
    """API endpoint que permite ver o editar Items de Cotizaciones."""
    queryset = ItemCotizacion.objects.all().order_by('id')
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ItemCotizacionSerializer

class MensajeCotizacionViewSet(viewsets.ModelViewSet):
    """API endpoint que permite ver o editar Mensajes de Cotizaciones."""
    queryset = MensajeCotizacion.objects.all().order_by('id')
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MensajeCotizacionSerializer