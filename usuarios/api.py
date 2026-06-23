from .models import (
    Departamento,
    Municipio,
    PerfilUsuario,
)
from rest_framework import viewsets,permissions
from .serializers import (
    DepartamentoSerializer,
    MunicipioSerializer,
    PerfilUsuarioSerializer,
)



class DepartamentoViewSet(viewsets.ModelViewSet):
    """API endpoint que permite ver o editar Departamentos."""
    queryset = Departamento.objects.all().order_by('id')
    permission_classes = [permissions.AllowAny]
    serializer_class = DepartamentoSerializer

class MunicipioViewSet(viewsets.ModelViewSet):
    """API endpoint que permite ver o editar Municipios."""
    queryset = Municipio.objects.all().order_by('id')
    permission_classes = [permissions.AllowAny]
    serializer_class = MunicipioSerializer


class PerfilUsuarioViewSet(viewsets.ModelViewSet):
    """
    API endpoint que permite ver o editar Perfiles de Usuario.
    """
    queryset = PerfilUsuario.objects.all().order_by('usuario__username')
    permission_classes = [permissions.AllowAny]
    serializer_class = PerfilUsuarioSerializer