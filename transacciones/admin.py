from django.contrib import admin
from .models import (Pedido,
                     DetallePedido, 
                     HistorialPuntos, 
                     Cotizacion
                     )
# Register your models here.)

admin.site.register(Pedido)
admin.site.register(DetallePedido)
admin.site.register(HistorialPuntos)
admin.site.register(Cotizacion)
