from django.db import models
from django.db.models import Q
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.contrib.auth.models import User
from .validators import validar_documento_identidad
import pyotp


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

class EstadoVerificacionChoices(models.TextChoices):
    PENDIENTE = 'pendiente', 'Pendiente de revisión'
    VERIFICADO = 'verificado', 'Verificado'
    RECHAZADO = 'rechazado', 'Rechazado'
    
class PerfilUsuario(models.Model):
    usuario = models.OneToOneField(User,on_delete=models.PROTECT,related_name='perfil')
    telefono = models.CharField(max_length=15, blank=True, null=True)
    cedula = models.CharField(max_length=20, blank=True, null=True)
    documento_identidad = models.FileField(
        upload_to='verificaciones/',
        null=True,
        blank=True,
        validators=[validar_documento_identidad],
        help_text="Opcional al crear el perfil. Obligatorio antes de que un Administrador pueda aprobar."
    )
    municipio = models.ForeignKey(Municipio, on_delete=models.PROTECT,null=True,blank=True)
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
    estado_verificacion = models.CharField(
        max_length=20,
        choices=EstadoVerificacionChoices.choices,
        default=EstadoVerificacionChoices.PENDIENTE,
        db_index=True,
    )
    verificado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='usuarios_verificados',
        help_text="Administrador que revisó este perfil"
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_revision = models.DateTimeField(null=True, blank=True)
    motivo_rechazo = models.CharField(max_length=255, blank=True, default='')
    ultima_actividad = models.DateTimeField(auto_now=True)

    @property
    def ultima_vez_conectado(self):
        return self.usuario.last_login
    
    @property 
    def fecha_de_registro(self):
        return self.usuario.date_joined
    
    @property
    def esta_verificado(self):
        return self.estado_verificacion == EstadoVerificacionChoices.VERIFICADO
    
    class Meta:
        verbose_name = "Perfil del usuario"
        verbose_name_plural = "Perfiles de usuarios"
        ordering = ['usuario'] 

    def __str__(self):
        return f"Perfil de {self.usuario.username} ({self.estado_verificacion})"

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    
class DispositivoTOTP(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='totp')
    secreto = models.CharField(max_length=32)
    confirmado = models.BooleanField(default=False)

    def get_totp(self):
        return pyotp.TOTP(self.secreto)

    def verificar_codigo(self, codigo):
        return self.get_totp().verify(codigo, valid_window=1)

    def __str__(self):
        return f"TOTP de {self.usuario.username} ({'confirmado' if self.confirmado else 'pendiente'})"