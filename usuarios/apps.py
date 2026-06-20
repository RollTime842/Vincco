from django.apps import AppConfig


class UsuariosConfig(AppConfig):
    name = 'usuarios'
    verbose_name = "Gestión de Usuarios"

    def ready(self):
        import usuarios.signals  # Importa las señales para que se registren correctamente
