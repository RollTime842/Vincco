from rest_framework import routers
from .api import DepartamentoViewSet
from .api import MunicipioViewSet
from .api import PerfilUsuarioViewSet

router = routers.DefaultRouter()
router.register('api/departamentos', DepartamentoViewSet, 'departamento')
router.register('api/municipios', MunicipioViewSet, 'municipio')
router.register('api/perfiles-usuario', PerfilUsuarioViewSet, 'perfil')
urlpatterns = router.urls