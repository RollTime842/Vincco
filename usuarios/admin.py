from django.contrib import admin
from .models import PerfilUsuario,Municipio,Departamento

# Register your models here.

class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'telefono', 'cedula', 'municipio', 'genero', 'estado', 'ultima_actividad')
    list_filter = ('estado', 'genero', 'municipio__departamento')
    search_fields = ('usuario__username', 'usuario__email', 'telefono', 'cedula')
    ordering = ('usuario',)

    def user_group(self, obj):
        return ", ".join([group.name for group in obj.usuario.groups.all()])

    user_group.short_description = 'Grupo'

admin.site.register(PerfilUsuario, PerfilUsuarioAdmin)
admin.site.register(Municipio)
admin.site.register(Departamento)


