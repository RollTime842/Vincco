from django.db import models
from django.db.models import Q
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from usuarios.models import PerfilUsuario
from comercios.models import PerfilNegocio, SubRubro, Sucursal
# Create your models here.

class EstadoProductoChoices(models.TextChoices):
    BORRADOR = 'borrador', 'Borrador (No publicado)'
    ACTIVO = 'activo', 'Activo (Visible en el directorio)'
    EN_REVISION = 'en_revision', 'En Revisión (Control de calidad por admin)'
    DISPONIBLE = 'disponible', 'Disponible (Activo y visible)'
    OCULTO = 'oculto', 'Oculto (Retirado por infracción)'


class EstadoServicioChoices(models.TextChoices):
    BORRADOR = 'borrador', 'Borrador (No publicado)'
    PAUSADO = 'pausado', 'Pausado (El freelancer/proveedor no está aceptando trabajos)'
    OCULTO = 'oculto', 'Oculto (Retirado por infracción)'
    EN_REVISION = 'en_revision', 'En Revisión (Control de calidad por admin)'

class UnidadMedida(models.Model):
    """
    Catálogo de unidades físicas o de tiempo para productos y servicios.
    """
    nombre = models.CharField(
        max_length=50, 
        unique=True,
        help_text="Ej: Quintal, Libra, Litro, Hora, Unidad, Proyecto"
    )
    abreviatura = models.CharField(
        max_length=10,
        help_text="Ej: qq, lb, L, hr, ud"
    )
    es_fraccionable = models.BooleanField(
        default=False,
        help_text="¿Se puede vender en decimales? (Ej. 1.5 libras = True, 1 Martillo = False)"
    )

    class Meta:
        verbose_name = "Unidad de Medida"
        verbose_name_plural = "Unidades de Medida"
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} ({self.abreviatura})"
    


class Producto(models.Model):
    negocio = models.ForeignKey(
        PerfilNegocio, 
        on_delete=models.CASCADE, # Si se borra la ferretería, se borran sus clavos y martillos
        related_name='productos'
    )
    nombre = models.CharField(max_length=200, help_text="Ej: Consultoría Contable")
    descripcion = models.TextField(help_text="Detalles del servicio.")
    precio = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    unidad_medida = models.ForeignKey(UnidadMedida,on_delete=models.PROTECT)
    stock_disponible = models.PositiveIntegerField()
    foto_portada = models.URLField(blank=True, null=True, help_text="Foto principal para la lista")
    estado = models.CharField(
        max_length=20,
        choices=EstadoProductoChoices.choices,
        default=EstadoProductoChoices.BORRADOR,
        help_text="Estado actual de disponibilidad en el directorio."
    )
    fecha_publicacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ['-estado', 'nombre'] 

    def __str__(self):
        return f"{self.nombre} - {self.get_estado_display()}"

class GaleriaProducto(models.Model):
    producto = models.ForeignKey(Producto, related_name='imagenes_extra', on_delete=models.CASCADE)
    url_imagen = models.URLField()
    descripcion = models.CharField(max_length=50, blank=True, help_text="Ej: Vista lateral, Empaque")
    fecha_subida = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Imagen extra de {self.producto.nombre}"

class Servicio(models.Model):
    negocio = models.ForeignKey(
        PerfilNegocio, 
        on_delete=models.CASCADE, # Si se borra la ferretería, se borran sus clavos y martillos
        related_name='servicios'
    )
    foto_portada = models.URLField(blank=True, null=True, help_text="Foto principal para la lista")
    nombre = models.CharField(max_length=80,blank=True,null=False)
    descripcion = models.CharField(max_length=200,blank=True,null=False,help_text="Descripcion del servicio")
    precio = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    fecha_publicacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre}"

class GaleriaServicio(models.Model):
    servicio = models.ForeignKey(Servicio, related_name='imagenes_extra', on_delete=models.CASCADE)
    url_imagen = models.URLField()
    descripcion = models.CharField(max_length=50, blank=True, help_text="Ej: Vista lateral, Empaque")
    fecha_subida = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.servicio}"

class EstadoCatalogoChoices(models.TextChoices):
    ACTIVO = 'activo', 'Activo'
    INACTIVO = 'inactivo', 'Inactivo'
    OCULTO = 'oculto', 'Oculto'

class Catalogo(models.Model):
    sucursal = models.ForeignKey(Sucursal, on_delete=models.CASCADE, related_name='ofertas_catalogo')
    
    # 2. Los Arcos Exclusivos (Tus productos / servicios)
    producto = models.ForeignKey(Producto, 
                                on_delete=models.SET_NULL,
                                null=True, 
                                blank=True)
    servicio = models.ForeignKey(Servicio, 
                                on_delete=models.SET_NULL, 
                                null=True, 
                                blank=True)
    
    # 3. El motor de la gamificación
    puntos_recompensa = models.PositiveIntegerField(
        default=0,
        help_text="Puntos que gana el usuario al comprar esto"
    )

    # 4. (Recomendado) El estado que discutimos en el paso anterior
    estado = models.CharField(
        max_length=20,
        choices=EstadoCatalogoChoices.choices,
        default=EstadoCatalogoChoices.ACTIVO
    )

    # --- VALIDACIÓN ---
    def clean(self):
        # Regla 1: Validar el Arco Exclusivo 
        if not self.producto and not self.servicio:
            raise ValidationError({'__all__': "El ítem debe ser un Producto o un Servicio."})
        
        if self.producto and self.servicio:
            raise ValidationError({'__all__': "Un ítem no puede ser Producto y Servicio a la vez."})

        # Regla 2: COHERENCIA DE PROPIEDAD 
        # Verificamos que el producto que intentan agregar a la sucursal
        # realmente pertenezca al Negocio (PerfilNegocio) dueño de esa sucursal.
        
        if self.producto:
            if self.producto.negocio != self.sucursal.negocio:
                raise ValidationError({
                    'producto': f"¡Alerta de Seguridad! El producto '{self.producto.nombre}' pertenece a otro negocio y no puede ser vendido en esta sucursal."
                })

        if self.servicio:
            if self.servicio.negocio != self.sucursal.negocio:
                raise ValidationError({
                    'servicio': f"¡Alerta de Seguridad! El servicio '{self.servicio.nombre}' pertenece a otro negocio y no puede ser ofrecido en esta sucursal."
                })

    def save(self, *args, **kwargs):
        self.full_clean()  # Valida campos + clean() + unique
        super().save(*args, **kwargs)

    def __str__(self):
        # 1. Operador ternario: evaluamos el tipo en una sola línea
        tipo = "Producto" if self.producto else "Servicio"
        
        # 2. Usamos get_estado_display() y limpiamos un poco los separadores
        return f"{self.sucursal} | {tipo} | Puntos: {self.puntos_recompensa} | {self.get_estado_display()}"        
    
    class Meta:
        verbose_name = "Catálogo"
        verbose_name_plural = "Catálogos"
        # Evita duplicados: misma sucursal no puede tener el mismo producto dos veces
        constraints = [
            models.UniqueConstraint(
                fields=['sucursal', 'producto'],
                condition=Q(producto__isnull=False),
                name='unique_producto_por_sucursal'
            ),
            models.UniqueConstraint(
                fields=['sucursal', 'servicio'],
                condition=Q(servicio__isnull=False),
                name='unique_servicio_por_sucursal'
            ),
        ]
