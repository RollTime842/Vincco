from django.contrib.auth.models import Group
from django.dispatch import receiver
from django.db.models.signals import post_save

from .models import PerfilUsuario

@receiver(post_save, sender=PerfilUsuario)
def asignar_grupo_usuario(sender, instance, created, **kwargs):
    if created:
        try:
            grupo_usuario = Group.objects.get(name='Usuario')
        except Group.DoesNotExist:
            grupo_usuario = Group.objects.create(name='Usuario')
        instance.usuario.groups.add(grupo_usuario)