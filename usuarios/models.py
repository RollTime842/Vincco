from django.db import models
from django.db.models import Q
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


# Create your models here.

class Departamento(models.Model):
    nombre = models.CharField(max_length=40)
    codigo = models.CharField(max_length=5, unique=True)  # Ej: "MGA"

    def __str__(self):
        return self.nombre

class Municipio(models.Model):
    nombre = models.CharField(max_length=60)
    departamento = models.ForeignKey(
        Departamento,
        on_delete=models.PROTECT,
        related_name='municipios'
    )

    class Meta:
        unique_together = ('nombre', 'departamento')

    def __str__(self):
        return f"{self.nombre}, {self.departamento}"
    
class Rol(models.Model):
    nombre = models.CharField(max_length=15, blank=True, null=False)

    def __str__(self):
        return f"{self.nombre}"


class GeneroChoices(models.TextChoices):
    FEMENINO = 'F', _('Femenino')
    MASCULINO = 'M', _('Masculino')
    NO_BINARIO = 'NB', _('No binario')
    OTRO = 'O', _('Otro')
    PREFIERO_NO_DECIRLO = 'PND', _('Prefiero no decirlo') 

class EstadoUsuarioChoices(models.TextChoices):
    EN_REVISION = 'REV', _('En revisión') 
    ACTIVO = 'ACT', _('Activo')
    INACTIVO = 'INA', _('Inactivo')
    SUSPENDIDO = 'SUS', _('Suspendido')

class PerfilUsuario(models.Model):
    usuario = models.OneToOneField(User,on_delete=models.PROTECT,related_name='perfil')
    telefono = models.CharField(max_length=15, blank=True, null=True)
    cedula = models.CharField(max_length=20, blank=True, null=True)
    municipio = models.ForeignKey(Municipio, on_delete=models.PROTECT)
    genero = models.CharField(
        max_length=3,
        choices=GeneroChoices.choices,
        default=GeneroChoices.PREFIERO_NO_DECIRLO,
        help_text="Identidad de género del usuario."
    )
    estado = models.CharField(
        max_length=3,
        choices=EstadoUsuarioChoices.choices,
        default=EstadoUsuarioChoices.EN_REVISION, 
        help_text="Estado de operatividad y visibilidad de la cuenta."
    )
    ultima_actividad = models.DateTimeField(auto_now=True)

    @property
    def ultima_vez_conectado(self):
        return self.usuario.last_login
    
    @property 
    def fecha_de_registro(self):
        return self.usuario.date_joined
    
    class Meta:
        verbose_name = "Perfil del usuario"
        verbose_name_plural = "Perfiles de usuarios"
        ordering = ['usuario'] # Para que siempre salgan en orden alfabético

    def __str__(self):
        # Extraemos el 'username' del objeto User, lo cual sí es un texto.
        return f"Perfil de {self.usuario.username}"