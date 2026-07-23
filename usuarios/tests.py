from django.test import TestCase

# Create your tests here.
# usuarios/tests/test_perfil_usuario.py
from django.contrib.auth.models import User, Group
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APITestCase

from usuarios.models import PerfilUsuario, EstadoVerificacionChoices

class PerfilUsuarioTestBase(APITestCase):
    BASE_URL = '/api/usuarios/perfil-usuario/'  
    

    def setUp(self):
        # Grupos base (normalmente vendrían de la migración, los creamos a mano en el test)
        self.grupo_admin, _ = Group.objects.get_or_create(name='Administrador')
        self.grupo_comun, _ = Group.objects.get_or_create(name='Usuario Comun')

        # Usuario común de prueba
        self.user = User.objects.create_user(username='juan', password='clave123')
        self.user.groups.add(self.grupo_comun)

        # Otro usuario común, para probar aislamiento entre usuarios
        self.otro_user = User.objects.create_user(username='maria', password='clave123')
        self.otro_user.groups.add(self.grupo_comun)

        # Usuario administrador
        self.admin = User.objects.create_user(username='admin', password='clave123')
        self.admin.groups.add(self.grupo_admin)

    def _documento_falso(self):
        return SimpleUploadedFile(
            'cedula.jpg', b'contenido-falso-de-archivo', content_type='image/jpeg'
        )


class CrearPerfilTests(PerfilUsuarioTestBase):

    def test_usuario_puede_crear_su_propio_perfil(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.BASE_URL, {
            'telefono': '88881234',
            'cedula': '001-123456-0000A',
            'genero': 'M',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        perfil = PerfilUsuario.objects.get(usuario=self.user)
        self.assertEqual(perfil.estado_verificacion, EstadoVerificacionChoices.PENDIENTE)

    def test_no_puede_crear_dos_perfiles(self):
        PerfilUsuario.objects.create(usuario=self.user, cedula='001-123456-0000A')
        self.client.force_authenticate(self.user)

        response = self.client.post(self.BASE_URL, {'cedula': '001-999999-0000B'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_no_puede_crear_perfil_a_nombre_de_otro_usuario(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.BASE_URL, {
            'usuario': self.otro_user.id,  # intento de inyectar otro usuario
            'cedula': '001-123456-0000A',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # A pesar de mandar otro id, el perfil se creó a nombre de quien hizo la petición
        perfil = PerfilUsuario.objects.get(cedula='001-123456-0000A')
        self.assertEqual(perfil.usuario, self.user)

    def test_no_autenticado_no_puede_crear_perfil(self):
        response = self.client.post(self.BASE_URL, {'cedula': '001-123456-0000A'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AislamientoEntreUsuariosTests(PerfilUsuarioTestBase):

    def setUp(self):
        super().setUp()
        self.perfil_juan = PerfilUsuario.objects.create(
            usuario=self.user, cedula='001-111111-0000A'
        )
        self.perfil_maria = PerfilUsuario.objects.create(
            usuario=self.otro_user, cedula='001-222222-0000B'
        )

    def test_usuario_solo_ve_su_propio_perfil_en_listado(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.BASE_URL)
        ids_devueltos = [p['id'] for p in response.data['results']] \
            if 'results' in response.data else [p['id'] for p in response.data]
        self.assertIn(self.perfil_juan.id, ids_devueltos)
        self.assertNotIn(self.perfil_maria.id, ids_devueltos)

    def test_usuario_no_puede_acceder_al_perfil_de_otro(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(f'{self.BASE_URL}{self.perfil_maria.id}/')
        # No debe ni siquiera saber que existe -> 404, no 403
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_admin_ve_todos_los_perfiles(self):
        self.client.force_authenticate(self.admin)
        response = self.client.get(self.BASE_URL)
        cantidad = response.data['count'] if 'count' in response.data else len(response.data)
        self.assertEqual(cantidad, 2)


class EscalacionDePrivilegiosTests(PerfilUsuarioTestBase):

    def setUp(self):
        super().setUp()
        self.perfil = PerfilUsuario.objects.create(
            usuario=self.user, cedula='001-111111-0000A'
        )

    def test_usuario_no_puede_auto_verificarse(self):
        self.client.force_authenticate(self.user)
        response = self.client.patch(f'{self.BASE_URL}{self.perfil.id}/', {
            'estado_verificacion': EstadoVerificacionChoices.VERIFICADO,
        })
        self.perfil.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # el request pasa...
        self.assertEqual(
            self.perfil.estado_verificacion, EstadoVerificacionChoices.PENDIENTE
        )  # ...pero el campo peligroso se ignoró

    def test_usuario_no_puede_asignarse_como_verificador(self):
        self.client.force_authenticate(self.user)
        self.client.patch(f'{self.BASE_URL}{self.perfil.id}/', {
            'verificado_por': self.user.id,
        })
        self.perfil.refresh_from_db()
        self.assertIsNone(self.perfil.verificado_por)

    def test_usuario_puede_editar_telefono_libremente(self):
        self.client.force_authenticate(self.user)
        response = self.client.patch(f'{self.BASE_URL}{self.perfil.id}/', {
            'telefono': '77778888',
        })
        self.perfil.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.perfil.telefono, '77778888')

    def test_cedula_bloqueada_despues_de_verificado(self):
        self.perfil.estado_verificacion = EstadoVerificacionChoices.VERIFICADO
        self.perfil.save()

        self.client.force_authenticate(self.user)
        self.client.patch(f'{self.BASE_URL}{self.perfil.id}/', {
            'cedula': '001-999999-9999Z',
        })
        self.perfil.refresh_from_db()
        self.assertEqual(self.perfil.cedula, '001-111111-0000A')  # no cambió

    def test_cedula_editable_antes_de_verificado(self):
        self.client.force_authenticate(self.user)
        response = self.client.patch(f'{self.BASE_URL}{self.perfil.id}/', {
            'cedula': '001-999999-9999Z',
        })
        self.perfil.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.perfil.cedula, '001-999999-9999Z')


class AprobarRechazarTests(PerfilUsuarioTestBase):

    def setUp(self):
        super().setUp()
        self.perfil = PerfilUsuario.objects.create(
            usuario=self.user, cedula='001-111111-0000A'
        )

    def test_usuario_comun_no_puede_aprobar(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(f'{self.BASE_URL}{self.perfil.id}/aprobar/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_no_puede_aprobar_sin_documento(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post(f'{self.BASE_URL}{self.perfil.id}/aprobar/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.perfil.refresh_from_db()
        self.assertEqual(
            self.perfil.estado_verificacion, EstadoVerificacionChoices.PENDIENTE
        )

    def test_admin_puede_aprobar_con_documento(self):
        self.perfil.documento_identidad = self._documento_falso()
        self.perfil.save()

        self.client.force_authenticate(self.admin)
        response = self.client.post(f'{self.BASE_URL}{self.perfil.id}/aprobar/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.perfil.refresh_from_db()
        self.assertEqual(
            self.perfil.estado_verificacion, EstadoVerificacionChoices.VERIFICADO
        )
        self.assertEqual(self.perfil.verificado_por, self.admin)

    def test_no_puede_aprobar_dos_veces(self):
        self.perfil.documento_identidad = self._documento_falso()
        self.perfil.estado_verificacion = EstadoVerificacionChoices.VERIFICADO
        self.perfil.save()

        self.client.force_authenticate(self.admin)
        response = self.client.post(f'{self.BASE_URL}{self.perfil.id}/aprobar/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_puede_rechazar_con_motivo(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post(f'{self.BASE_URL}{self.perfil.id}/rechazar/', {
            'motivo': 'Documento ilegible',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.perfil.refresh_from_db()
        self.assertEqual(
            self.perfil.estado_verificacion, EstadoVerificacionChoices.RECHAZADO
        )
        self.assertEqual(self.perfil.motivo_rechazo, 'Documento ilegible')

    def test_no_puede_rechazar_uno_ya_procesado(self):
        self.perfil.estado_verificacion = EstadoVerificacionChoices.RECHAZADO
        self.perfil.save()

        self.client.force_authenticate(self.admin)
        response = self.client.post(f'{self.BASE_URL}{self.perfil.id}/rechazar/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)