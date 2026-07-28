from django.contrib.auth.models import Group,User
from django.dispatch import receiver
from django.db.models.signals import post_save


@receiver(post_save, sender=User)
def asignar_grupo_por_defecto(sender, instance, created, **kwargs):
    if not created:
        return


    if instance.is_superuser or instance.is_staff:
        administrador = Group.objects.get(name='Administrador')
        instance.groups.add(administrador)
        return

    grupo_comun = Group.objects.get(name='Usuario Comun')
    instance.groups.add(grupo_comun)