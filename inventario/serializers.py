from rest_framework import serializers

from .models import (
    UnidadMedida,
    Producto,
    GaleriaProducto,
    Servicio,
    GaleriaServicio,
    Catalogo
)

class UnidadMedidaSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnidadMedida
        fields = '__all__'


class ProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Producto
        fields = '__all__'

class GaleriaProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = GaleriaProducto
        fields = '__all__'

class ServicioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Servicio
        fields = '__all__'

class GaleriaServicioSerializer(serializers.ModelSerializer):
    class Meta:
        model = GaleriaServicio
        fields = '__all__'

class CatalogoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Catalogo
        fields = '__all__'

