from rest_framework import serializers


from .models import (
    Pedido,
    DetallePedido,
    HistorialPuntos,
    Cotizacion,
    ItemCotizacion,
    MensajeCotizacion,
)

class PedidoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pedido
        fields = '__all__'

class DetallePedidoSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetallePedido
        fields = '__all__'

class HistorialPuntosSerializer(serializers.ModelSerializer):
    class Meta:
        model = HistorialPuntos
        fields = '__all__'

class CotizacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cotizacion
        fields = '__all__'

class ItemCotizacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemCotizacion
        fields = '__all__'

class MensajeCotizacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MensajeCotizacion
        fields = '__all__'
