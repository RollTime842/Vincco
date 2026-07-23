from rest_framework import serializers

from .models import (
    RubroPrincipal,
    SubRubro,
    PerfilNegocio,
    Sucursal,
    ContactoSucursal,
)

class RubroPrincipalSerializer(serializers.ModelSerializer):
    class Meta:
        model = RubroPrincipal
        fields = '__all__'


class SubRubroSerializer(serializers.ModelSerializer):
    rubro_principal = serializers.ReadOnlyField(source='rubro_padre.nombre')

    class Meta:
        model = SubRubro
        fields = '__all__'


class PerfilNegocioSerializer(serializers.ModelSerializer):
    sub_rubro = SubRubroSerializer(read_only=True)
    sub_rubro_id = serializers.PrimaryKeyRelatedField(
        queryset=SubRubro.objects.all(),
        source='sub_rubro',
        write_only=True
    )

    class Meta:
        model = PerfilNegocio
        fields = '__all__'


class SucursalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sucursal
        fields = '__all__'

class ContactoSucursalSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactoSucursal
        fields = '__all__'