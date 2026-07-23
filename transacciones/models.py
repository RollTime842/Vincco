from django.db import models
from django.db.models import Q
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.exceptions import ValidationError
from usuarios.models import PerfilUsuario
from comercios.models import Sucursal
from inventario.models import Catalogo,Producto, Servicio

# Create your models here.
class EstadoPedidoChoices(models.TextChoices):
    PENDIENTE = 'PEN', 'Pendiente de confirmación'
    ACEPTADO = 'ACE', 'En preparación'
    EN_CAMINO = 'CAM', 'En camino / Delivery'
    ENTREGADO = 'ENT', 'Entregado y Finalizado'
    CANCELADO = 'CAN', 'Cancelado'

class Pedido(models.Model):
    usuario = models.ForeignKey(PerfilUsuario, on_delete=models.PROTECT, related_name='pedidos_realizados')
    sucursal = models.ForeignKey(Sucursal, on_delete=models.PROTECT, related_name='pedidos_recibidos')
    estado = models.CharField(
        max_length=3, 
        choices=EstadoPedidoChoices.choices, 
        default=EstadoPedidoChoices.PENDIENTE
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True) # Para saber cuándo cambió de estado
    total_estimado = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_puntos_obtenidos = models.PositiveIntegerField(default=0)
    notas = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        es_nuevo = self.pk is None 
        estado_anterior = None
        
        if not es_nuevo:
            estado_anterior = Pedido.objects.get(pk=self.pk).estado

        super().save(*args, **kwargs)

        if self.estado == EstadoPedidoChoices.ENTREGADO and estado_anterior != EstadoPedidoChoices.ENTREGADO:
            if self.total_puntos_obtenidos > 0:
                from .models import HistorialPuntos, TipoMovimientoPuntos 
                
                HistorialPuntos.objects.create(
                    usuario=self.usuario,
                    pedido=self, # Conectamos el recibo
                    tipo_movimiento=TipoMovimientoPuntos.COMPRA,
                    cantidad=self.total_puntos_obtenidos, # Copiamos la cantidad automáticamente
                    descripcion=f"Puntos ganados por la compra #{self.id} en {self.sucursal.nombre}"
                )

    def __str__(self):
        return f"Pedido #{self.id} - {self.sucursal.nombre} ({self.get_estado_display()})"

class DetallePedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='items')
    item_catalogo = models.ForeignKey(Catalogo, on_delete=models.SET_NULL, null=True)
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario_historico = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    puntos_unitarios_historicos = models.PositiveIntegerField(default=0, null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.item_catalogo:
            if not self.pk:
                item = self.item_catalogo.producto or self.item_catalogo.servicio
                self.precio_unitario_historico = item.precio if item else 0
        
        super().save(*args, **kwargs)

    def subtotal(self):
        precio = self.precio_unitario_historico or 0
        return self.cantidad * precio

    def subtotal_puntos(self):
        puntos = self.puntos_unitarios_historicos or 0
        return self.cantidad * puntos

    def __str__(self):
        return f"{self.cantidad}x {self.item_catalogo} en Pedido #{self.pedido.id}"
    
class TipoMovimientoPuntos(models.TextChoices):
    COMPRA = 'COM', 'Ganancia por compra en sucursal'
    BONO = 'BON', 'Bono (Bienvenida, Referido, etc.)'
    
    CANJE = 'CAN', 'Canjeo de recompensa'
    EXPIRACION = 'EXP', 'Expiración por inactividad'
    PENALIZACION = 'PEN', 'Penalización / Reembolso'

class HistorialPuntos(models.Model):
    usuario = models.ForeignKey(PerfilUsuario, on_delete=models.PROTECT, related_name='movimientos_puntos')
    pedido = models.ForeignKey(Pedido, on_delete=models.PROTECT, null=True, blank=True, related_name='puntos_generados')
    tipo_movimiento = models.CharField(
        max_length=3, 
        choices=TipoMovimientoPuntos.choices
    )
    
    cantidad = models.IntegerField(
        help_text="Usa números positivos para ganancias y negativos para gastos/canjes"
    )
    fecha_agregacion = models.DateTimeField(auto_now_add=True)
    descripcion = models.CharField(
        max_length=200, 
        help_text="Ej: Canje por 1 Libra de Frijoles en Pulpería Doña María"
    )

    def clean(self):
        if self.pedido:
            if self.pedido.usuario != self.usuario:
                raise ValidationError({
                    'pedido': "Alerta de Seguridad: No puedes interactuar con un pedido que pertenece a otro usuario."
                })

    def save(self, *args, **kwargs):
        
        if self.pedido and not self.pk:
            puntos_obtenidos = self.pedido.total_puntos_obtenidos 
            if self.tipo_movimiento == TipoMovimientoPuntos.CANJE:
                self.cantidad = -abs(puntos_obtenidos)
            else:
                self.cantidad = abs(puntos_obtenidos)
            if not self.descripcion:
                self.descripcion = f"Puntos automáticos por Pedido #{self.pedido.id}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.usuario.usuario} | {self.cantidad} pts | {self.get_tipo_movimiento_display()}"
    
class EstadoCotizacion(models.TextChoices):
    PENDIENTE = 'PEN', 'Pendiente de Respuesta'
    RESPONDIDA = 'RES', 'Respondida por Proveedor'
    ACEPTADA = 'ACE', 'Aceptada por Cliente'
    RECHAZADA = 'REC', 'Rechazada / Cancelada'
    EXPIRADA = 'EXP', 'Vencida por Fecha'

class Cotizacion(models.Model):
    solicitante = models.ForeignKey(PerfilUsuario, on_delete=models.PROTECT, related_name='cotizaciones_pedidas')
    proveedor = models.ForeignKey(Sucursal, on_delete=models.PROTECT, related_name='cotizaciones_recibidas')
    estado = models.CharField(
        max_length=3,
        choices=EstadoCotizacion.choices,
        default=EstadoCotizacion.PENDIENTE
    )
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    fecha_respuesta = models.DateTimeField(null=True, blank=True)
    valida_hasta = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Fecha límite antes de que el precio sufra volatilidad"
    )
    notas_comprador = models.TextField(blank=True, help_text="Ej: Necesito transporte al mercado central")
    notas_proveedor = models.TextField(blank=True, help_text="Ej: Precio especial por pago de contado")

    @property
    def esta_vencida(self):
        """Revisión automática de expiración"""
        if self.valida_hasta and timezone.now() > self.valida_hasta:
            return True
        return False

    def __str__(self):
        return f"Cotización #{self.id} | De: {self.solicitante.usuario} a {self.proveedor.nombre}"


class ItemCotizacion(models.Model):
    """Tabla intermedia para listar los productos solicitados"""
    cotizacion = models.ForeignKey(Cotizacion, on_delete=models.CASCADE, related_name='items')
    
    
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, null=True, blank=True)
    servicio = models.ForeignKey(Servicio, on_delete=models.PROTECT, null=True, blank=True)
    cantidad = models.PositiveIntegerField()
    precio_unitario_ofertado = models.DecimalField(
       
        max_digits=12,
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Precio final asignado por el proveedor"
    )

    def clean(self):
        if not self.producto and not self.servicio:
            raise ValidationError({'__all__': "El ítem de la cotización debe ser un Producto o un Servicio."})
        
        if self.producto and self.servicio:
            raise ValidationError({'__all__': "Un ítem no puede ser Producto y Servicio al mismo tiempo."})

    def __str__(self):
        if self.producto:
            return f"{self.cantidad}x Producto: {self.producto.nombre} (Cot #{self.cotizacion.id})"
        return f"{self.cantidad}x Servicio: {self.servicio.nombre} (Cot #{self.cotizacion.id})"
    
class MensajeCotizacion(models.Model):
    cotizacion = models.ForeignKey(
        Cotizacion, 
        on_delete=models.CASCADE, 
        related_name='mensajes'
    )
    remitente = models.ForeignKey(
        PerfilUsuario,
        on_delete=models.PROTECT, 
        related_name='mensajes_enviados'
    )
    texto = models.TextField(blank=True, null=True, help_text="Cuerpo del mensaje")
    archivo_adjunto = models.FileField(
        upload_to='cotizaciones/mensajes_adjuntos/', 
        blank=True, 
        null=True,
        help_text="Formatos permitidos: PDF, JPG, PNG, etc."
    )
    

    leido = models.BooleanField(default=False)
    fecha_envio = models.DateTimeField(auto_now_add=True) # Marca de tiempo inmutable

    class Meta:
        ordering = ['fecha_envio'] 
        verbose_name = "Mensaje de Cotización"
        verbose_name_plural = "Mensajes de Cotización"

    def __str__(self):
        return f"Mensaje de {self.remitente.usuario.username} - Cotización #{self.cotizacion.id}"

    def clean(self):
        if not self.texto and not self.archivo_adjunto:
            raise ValidationError("El mensaje debe contener texto o un archivo adjunto.")