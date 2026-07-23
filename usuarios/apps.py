from django.apps import AppConfig


class UsuariosConfig(AppConfig):
    name = 'usuarios'
    verbose_name = "Gestión de Usuarios"

    def ready(self):
        import usuarios.signals  
