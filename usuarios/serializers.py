from rest_framework import serializers
from django.contrib.auth.models import User,Group


from .models import (
    Departamento,
    Municipio,
    PerfilUsuario,
)


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['id', 'name']
        
class DepartamentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Departamento
        fields = '__all__'

class MunicipioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Municipio
        fields = '__all__'


class PerfilUsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerfilUsuario
        fields = [
            'id',
            'usuario',
            'telefono',
            'cedula',
            'municipio',
            'genero',
            'ultima_actividad',
            'estado_verificacion',
            'verificado_por',
            'fecha_revision',
            'motivo_rechazo',
        ]
        read_only_fields = [
            'usuario',
            'estado_verificacion',
            'verificado_por',
            'fecha_revision',
            'motivo_rechazo',
        ]

class UsuarioSerializer(serializers.ModelSerializer):
    groups = GroupSerializer(many=True, read_only=True)
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'groups'] 

class RegistroUsuarioSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password']

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)
    
class ActivarTOTPResponseSerializer(serializers.Serializer):
    qr_code = serializers.CharField()

class ConfirmarTOTPSerializer(serializers.Serializer):
    codigo = serializers.CharField(max_length=6)

class LoginPaso1Serializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

class VerificarTOTPSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    codigo = serializers.CharField(max_length=6)