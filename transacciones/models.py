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
    # 1. ¿Quién pide y a dónde?
    usuario = models.ForeignKey(PerfilUsuario, on_delete=models.PROTECT, related_name='pedidos_realizados')
    sucursal = models.ForeignKey(Sucursal, on_delete=models.PROTECT, related_name='pedidos_recibidos')
    
    # 2. El Estado (Usando nuestra regla de TextChoices)
    estado = models.CharField(
        max_length=3, 
        choices=EstadoPedidoChoices.choices, 
        default=EstadoPedidoChoices.PENDIENTE
    )
    
    # 3. Fechas (Creación y actualización automática)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True) # Para saber cuándo cambió de estado
    
    # 4. Totales (Tu propuesta)
    total_estimado = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_puntos_obtenidos = models.PositiveIntegerField(default=0)
    
    # Extra recomendado: Notas del cliente (Ej: "Llamar al llegar")
    notas = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        # 1. Verificamos si este pedido ya existía en la base de datos
        es_nuevo = self.pk is None 
        estado_anterior = None
        
        if not es_nuevo:
            # Buscamos cómo estaba el pedido ANTES de guardarlo ahora
            estado_anterior = Pedido.objects.get(pk=self.pk).estado

        # 2. Guardamos el pedido en la base de datos normalmente
        super().save(*args, **kwargs)

        # 3. LA AUTOMATIZACIÓN DE PUNTOS
        # Si el pedido acaba de cambiar a 'ENTREGADO' (y no estaba entregado antes),
        # y además generó más de 0 puntos...
        if self.estado == EstadoPedidoChoices.ENTREGADO and estado_anterior != EstadoPedidoChoices.ENTREGADO:
            if self.total_puntos_obtenidos > 0:
                # ¡Creamos la fila en el Historial automáticamente!
                # Importamos el modelo aquí para evitar errores circulares
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
    
    # Permitimos null y blank porque el backend los rellenará automáticamente antes de persistir
    precio_unitario_historico = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    puntos_unitarios_historicos = models.PositiveIntegerField(default=0, null=True, blank=True)

    def save(self, *args, **kwargs):
        # 1. Validamos que exista un ítem del catálogo asociado
        if self.item_catalogo:
            # 2. Si es la primera vez que se guarda (no tiene ID aún), capturamos los valores
            if not self.pk:
                item = self.item_catalogo.producto or self.item_catalogo.servicio
                self.precio_unitario_historico = item.precio if item else 0
        
        # 3. Llamamos al método save original de Django para guardar los datos en la BD
        super().save(*args, **kwargs)

    def subtotal(self):
        # Aseguramos un fallback por si acaso no se han guardado (útil para instancias en memoria)
        precio = self.precio_unitario_historico or 0
        return self.cantidad * precio

    def subtotal_puntos(self):
        puntos = self.puntos_unitarios_historicos or 0
        return self.cantidad * puntos

    def __str__(self):
        return f"{self.cantidad}x {self.item_catalogo} en Pedido #{self.pedido.id}"
    
class TipoMovimientoPuntos(models.TextChoices):
    # Entradas de puntos (Positivos)
    COMPRA = 'COM', 'Ganancia por compra en sucursal'
    BONO = 'BON', 'Bono (Bienvenida, Referido, etc.)'
    
    # Salidas de puntos (Negativos)
    CANJE = 'CAN', 'Canjeo de recompensa'
    EXPIRACION = 'EXP', 'Expiración por inactividad'
    PENALIZACION = 'PEN', 'Penalización / Reembolso'

class HistorialPuntos(models.Model):
    # 1. ¿De quién son los puntos?
    usuario = models.ForeignKey(PerfilUsuario, on_delete=models.PROTECT, related_name='movimientos_puntos')
    
    # 2. El Recibo (Tu propuesta). Usamos null=True porque a veces ganas puntos sin comprar (ej. Bono de bienvenida)
    pedido = models.ForeignKey(Pedido, on_delete=models.PROTECT, null=True, blank=True, related_name='puntos_generados')
    
    # 3. El Tipo de movimiento (Tu propuesta)
    tipo_movimiento = models.CharField(
        max_length=3, 
        choices=TipoMovimientoPuntos.choices
    )
    
    # 4. EL CAMPO CLAVE: La Cantidad (¡Debe permitir negativos!)
    cantidad = models.IntegerField(
        help_text="Usa números positivos para ganancias y negativos para gastos/canjes"
    )
    
    # 5. La Fecha (Tu propuesta, automática e inmodificable)
    fecha_agregacion = models.DateTimeField(auto_now_add=True)
    
    # Extra recomendado: Un pequeño texto para el historial del usuario
    descripcion = models.CharField(
        max_length=200, 
        help_text="Ej: Canje por 1 Libra de Frijoles en Pulpería Doña María"
    )

    def clean(self):
        # Validamos la propiedad cruzada (Aislación de Datos)
        if self.pedido:
            # Si el dueño del pedido NO es el mismo usuario que está recibiendo los puntos...
            if self.pedido.usuario != self.usuario:
                raise ValidationError({
                    'pedido': "Alerta de Seguridad: No puedes interactuar con un pedido que pertenece a otro usuario."
                })

    def save(self, *args, **kwargs):
        # 1. Verificamos si este movimiento está enlazado a un pedido y es la primera vez que se guarda
        if self.pedido and not self.pk:
            
            # 2. Extraer el total de puntos del pedido. 
            # Si en Pedido es un método, usarías: self.pedido.total_puntos()
            puntos_obtenidos = self.pedido.total_puntos_obtenidos 
            
            # 3. Validamos si es un ingreso o un gasto basado en el tipo de movimiento
            # Supongamos que en tu TipoMovimientoPuntos tienes 'GAN' (Ganancia) y 'CAN' (Canje)
            if self.tipo_movimiento == TipoMovimientoPuntos.CANJE:
                # Si el usuario usó puntos para pagar el pedido, la cantidad debe ser negativa
                self.cantidad = -abs(puntos_obtenidos)
            else:
                # Si es una compra normal, gana puntos (positivo)
                self.cantidad = abs(puntos_obtenidos)

            # 4. (Opcional pero muy pro) Autocompletar la descripción si la dejaron vacía
            if not self.descripcion:
                self.descripcion = f"Puntos automáticos por Pedido #{self.pedido.id}"
                
        # 5. Llamamos al save original de Django para guardar en la base de datos
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
    # 1. ¿Quién pide y quién provee?
    solicitante = models.ForeignKey(PerfilUsuario, on_delete=models.PROTECT, related_name='cotizaciones_pedidas')
    proveedor = models.ForeignKey(Sucursal, on_delete=models.PROTECT, related_name='cotizaciones_recibidas')
    
    # 2. El Estado del flujo (Tu propuesta)
    estado = models.CharField(
        max_length=3,
        choices=EstadoCotizacion.choices,
        default=EstadoCotizacion.PENDIENTE
    )
    
    # 3. Fechas de control (Tu propuesta)
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    fecha_respuesta = models.DateTimeField(null=True, blank=True)
    valida_hasta = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Fecha límite antes de que el precio sufra volatilidad"
    )
    
    # Notas extras para dar contexto a la negociación
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
    
    # Cantidad que requiere el emprendedor
    cantidad = models.PositiveIntegerField()
    
    # PRECIO OFERTADO
    precio_unitario_ofertado = models.DecimalField(
       
        max_digits=12, # 12 dígitos soportan hasta 9,999,999,999.99 (suficiente y más óptimo que 30)
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Precio final asignado por el proveedor"
    )

    def clean(self):
        # Regla 1: Validar el Arco Exclusivo a nivel de aplicación
        if not self.producto and not self.servicio:
            raise ValidationError({'__all__': "El ítem de la cotización debe ser un Producto o un Servicio."})
        
        if self.producto and self.servicio:
            raise ValidationError({'__all__': "Un ítem no puede ser Producto y Servicio al mismo tiempo."})

    def __str__(self):
        if self.producto:
            return f"{self.cantidad}x Producto: {self.producto.nombre} (Cot #{self.cotizacion.id})"
        return f"{self.cantidad}x Servicio: {self.servicio.nombre} (Cot #{self.cotizacion.id})"
    
class MensajeCotizacion(models.Model):
    # 1. El Contexto de la Negociación
    cotizacion = models.ForeignKey(
        Cotizacion, 
        on_delete=models.CASCADE, 
        related_name='mensajes'
    )
    
    # 2. El Autor del Mensaje
    remitente = models.ForeignKey(
        PerfilUsuario, # O el nombre exacto de tu modelo de perfil/usuario
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