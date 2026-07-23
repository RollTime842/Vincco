from django.contrib import admin
from .models import (UnidadMedida,
                     Producto,
                     GaleriaProducto,
                     Servicio,
                     GaleriaServicio,
                     Catalogo,)
# Register your models here.

admin.site.register(UnidadMedida)
admin.site.register(Producto)
admin.site.register(GaleriaProducto)
admin.site.register(Servicio)
admin.site.register(GaleriaServicio)
admin.site.register(Catalogo)