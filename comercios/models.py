from django.db import models
from django.db.models import Q
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class RubroPrincipal(models.Model):
    """
    Categoría macro del negocio. Ej: Ganadería, Agricultura, Comercio, Servicios.
    """
    nombre = models.CharField(
        max_length=100, 
        unique=True,
        help_text="Nombre general del rubro (Ej. Agricultura)"
    )
    descripcion = models.TextField(
        blank=True, 
        null=True,
        help_text="Breve explicación de qué abarca este rubro."
    )
    icono = models.CharField(
        max_length=50, 
        blank=True, 
        null=True, 
        help_text="Clase del ícono para el Frontend (Ej. 'fa-solid fa-tractor')"
    )
    
    activo = models.BooleanField(
        default=True,
        help_text="Desmarcar si este rubro ya no está disponible en la plataforma"
    )

    class Meta:
        verbose_name = "Rubro Principal"
        verbose_name_plural = "Rubros Principales"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class SubRubro(models.Model):
    """
    Categoría específica dentro del rubro. 
    Ej: Dentro de 'Agricultura' -> 'Venta de Semillas', 'Fertilizantes', 'Maquinaria'.
    """
    rubro_padre = models.ForeignKey(
        RubroPrincipal, 
        on_delete=models.CASCADE, # Si se borra el rubro padre, se borran sus subrubros
        related_name='subrubros'
    )
    nombre = models.CharField(max_length=100)
    
    class Meta:
        verbose_name = "Sub Rubro"
        verbose_name_plural = "Sub Rubros"
        unique_together = ('rubro_padre', 'nombre') 
        ordering = ['rubro_padre__nombre', 'nombre']

    def __str__(self):
        return f"{self.nombre}"
    
class RubroComercial(models.Model):
    rubro_principal = models.ForeignKey(RubroPrincipal,on_delete=models.PROTECT)
    sub_rubro = models.ForeignKey(SubRubro,on_delete=models.PROTECT)

    def __str__(self):
        return f"{self.rubro_principal} ==> {self.sub_rubro}."

    class Meta:
        verbose_name = "Rubro comercial"
        verbose_name_plural = "Rubros Comerciales"

class EstadoNegocioChoices(models.TextChoices):
    EN_REVISION = 'en_revision', 'En Revisión (Pendiente de validación)'
    ACTIVO = 'activo', 'Activo (Visible en el directorio)'
    INACTIVO = 'inactivo', 'Inactivo (Pausado por el dueño)'
    SUSPENDIDO = 'suspendido', 'Suspendido (Por infracciones o reportes)'

class PerfilNegocio(models.Model):
    usuario = models.ForeignKey(PerfilUsuario,on_delete=models.PROTECT)
    nombre = models.CharField(max_length=50,help_text='Nombre del negocio')
    rubro_comercial = models.ForeignKey(
        RubroComercial,
        on_delete=models.PROTECT,
        help_text="Selecciona la categoría específica del negocio.")
    razon_social = models.CharField(max_length=200, blank=True, null=True)
    ruc = models.CharField(max_length=50, blank=True, null=True)
    url_documento_legal = models.URLField(max_length=300, blank=True, null=True)
    estado = models.CharField(
        max_length=20,
        choices=EstadoNegocioChoices.choices,
        default=EstadoNegocioChoices.EN_REVISION
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre}---{self.usuario}"

    def clean(self):
    # Definimos la lista de roles que sí están permitidos
        roles_permitidos = ['PROVEEDOR', 'EMPRENDEDOR']
    
        if self.usuario.rol.nombre.upper() not in roles_permitidos:
            raise ValidationError("Solo se pueden seleccionar usuarios con rol de Proveedor o Emprendedor.")
        


class TipoContactoChoices(models.TextChoices):
    WHATSAPP = 'whatsapp','WhatsApp',
    TELEFONO = 'telefono','Telefono'
    

class TipoSucursalChoices(models.TextChoices):
    LOCAL_FISICO = 'FIS', 'Local Físico (Visitable)'
    VIRTUAL_DOMICILIO = 'VIR', 'Solo a Domicilio / Virtual / Freelancer'

class Sucursal(models.Model):
    negocio = models.ForeignKey(PerfilNegocio, on_delete=models.CASCADE, related_name='sucursales')
    tipo_presencia = models.CharField(
        max_length=3,
        choices=TipoSucursalChoices.choices,
        default=TipoSucursalChoices.LOCAL_FISICO
    )
    
    nombre = models.CharField(max_length=100, help_text="Ej: Sucursal Centro, o 'Servicios a Domicilio'")
    latitud = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitud = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    def clean(self):
        # Validamos si es un local físico
        if self.tipo_presencia == TipoSucursalChoices.LOCAL_FISICO:
            # Si falta la latitud O falta la longitud, disparamos el error
            if not self.latitud or not self.longitud:
                raise ValidationError({
                    'latitud': "Un local físico debe tener una latitud registrada.",
                    'longitud': "Un local físico debe tener una longitud registrada."
                })
    def __str__(self):
        return f"{self.nombre} - {self.get_tipo_presencia_display()}"
    
    class Meta:
        verbose_name = "Sucursal"
        verbose_name_plural = "Sucursales"

    
class ContactoSucursal(models.Model):
    sucursal = models.ForeignKey(Sucursal,on_delete=models.CASCADE)
    nombre = models.CharField(max_length=50,blank=True,help_text="Nombre del encargado del numero.")
    tipo_contacto = models.CharField(
        max_length=20,
        choices=TipoContactoChoices.choices,
        default=TipoContactoChoices.TELEFONO,
        help_text="Tipo de contacto."
    )
    telefono = models.CharField(max_length=12,blank=False)

    def __str__(self):
        return f"{self.sucursal}--{self.nombre}---{self.tipo_contacto}--{self.telefono}"