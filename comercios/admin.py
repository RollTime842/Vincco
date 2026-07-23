from django.contrib import admin
from .models  import (
    RubroPrincipal,
    SubRubro,
    PerfilNegocio,
    Sucursal,
    ContactoSucursal,
)
# Register your models here.
admin.site.register(RubroPrincipal)
admin.site.register(SubRubro)
admin.site.register(PerfilNegocio)
admin.site.register(Sucursal)
admin.site.register(ContactoSucursal)