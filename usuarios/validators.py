# usuarios/validators.py
import os
import magic
from django.core.exceptions import ValidationError

EXTENSIONES_PERMITIDAS = ['.pdf', '.jpg', '.jpeg', '.png']
TIPOS_MIME_PERMITIDOS = {
    '.pdf': ['application/pdf'],
    '.jpg': ['image/jpeg'],
    '.jpeg': ['image/jpeg'],
    '.png': ['image/png'],
}
TAMANO_MAXIMO_MB = 5


def validar_documento_identidad(value):
    # 1. Validar extensión
    ext = os.path.splitext(value.name)[1].lower()
    if ext not in EXTENSIONES_PERMITIDAS:
        raise ValidationError(
            f"Extensión no permitida ({ext}). Usa: {', '.join(EXTENSIONES_PERMITIDAS)}"
        )

    # 2. Validar tamaño
    if value.size > TAMANO_MAXIMO_MB * 1024 * 1024:
        raise ValidationError(f"El archivo no puede superar {TAMANO_MAXIMO_MB}MB.")

    # 3. Validar contenido real (magic numbers), no solo el nombre
    tipo_real = magic.from_buffer(value.read(2048), mime=True)
    value.seek(0)  # regresa el puntero al inicio para que Django pueda guardarlo después

    tipos_esperados = TIPOS_MIME_PERMITIDOS.get(ext, [])
    if tipo_real not in tipos_esperados:
        raise ValidationError(
            f"El contenido del archivo no coincide con su extensión "
            f"(se esperaba {tipos_esperados}, se detectó {tipo_real})."
        )