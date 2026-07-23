from django.contrib.auth.models import Group,User
from django.dispatch import receiver
from django.db.models.signals import post_save


@receiver(post_save, sender=User)
def asignar_grupo_usuario(sender, instance, created, **kwargs):
    if created:
        grupo_usuario, _ = Group.objects.get_or_create(name='Usuario Comun')
        instance.groups.add(grupo_usuario)