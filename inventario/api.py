from rest_framework import viewsets,permissions
from rest_framework.permissions import IsAuthenticated  

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
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UnidadMedidaSerializer

class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.all().order_by('id')
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProductoSerializer

class GaleriaProductoViewSet(viewsets.ModelViewSet):
    queryset = GaleriaProducto.objects.all().order_by('id')
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = GaleriaProductoSerializer

class ServicioViewSet(viewsets.ModelViewSet):
    queryset = Servicio.objects.all().order_by('id')
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ServicioSerializer

class GaleriaServicioViewSet(viewsets.ModelViewSet):
    queryset = GaleriaServicio.objects.all().order_by('id')
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = GaleriaServicioSerializer

class CatalogoViewSet(viewsets.ModelViewSet):
    queryset = Catalogo.objects.all().order_by('id')
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CatalogoSerializer