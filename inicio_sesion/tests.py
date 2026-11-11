from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from django.urls import resolve
from django.utils import timezone

from inicio_sesion.models import (
    Contacto,
    Cuenta,
    Nacimiento,
    SesionActivaNavegador,
    Usuario,
    VerificacionCodigo,
)
from inicio_sesion.validators import validar_contrasenia_segura

class RecuperarUsuarioTests(TestCase):
    def test_recuperar_usuario_without_credentials_redirects(self):
        usuario = Usuario.objects.create(
            nombres="Ana",
            apellidos="Pérez",
            genero="F",
            cedula_identidad="12345678",
            estado_civil="Soltera",
        )
        Contacto.objects.create(
            correo_electronico="test@example.com",
            id_usuario=usuario,
        )
        VerificacionCodigo.objects.create(
            cedula_identidad=usuario.cedula_identidad,
            token="token-123",
            codigo="123456",
            creado="2024-01-01T00:00:00Z",
            activo=0,
            descripcion="recuperacion",
        )

        session = self.client.session
        session["flujo_verificacion"] = True
        session["correo_verificado"] = True
        session["token_recuperacion"] = "token-123"
        session["CI_usuario"] = usuario.cedula_identidad
        session.save()

        response = self.client.get(reverse("recuperar_usuario"))

        self.assertRedirects(response, reverse("buscar_usuario"))


class AutenticacionCuentaTests(TestCase):
    def test_usuario_puede_iniciar_sesion_con_credenciales_validas(self):
        usuario = Usuario.objects.create(
            nombres="Ana",
            apellidos="Prueba",
            cedula_identidad="V-7654321",
        )
        Nacimiento.objects.create(
            pais="Venezuela",
            estado="Barinas",
            municipio="Barinas",
            parroquia="Barinas",
            direccion_nacimiento="Centro",
            fecha_nacimiento="2000-01-01",
            id_usuario=usuario,
        )
        cuenta = Cuenta.objects.create(
            id_usuario=usuario,
            usuario="ana_login_test",
            clave=make_password("ClaveSegura!2026"),
            tipo_cuenta="EST",
        )

        respuesta = self.client.post(
            reverse("inicio_sesion"),
            {
                "usuario": cuenta.usuario,
                "contrasenia": "ClaveSegura!2026",
            },
            HTTP_X_CASRCE_BROWSER_ID="browser-test-123",
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json()["estado"], "exito")
        self.assertEqual(respuesta.json()["url"], reverse("panel_usuario"))
        self.assertEqual(
            self.client.session["id_cuenta"],
            cuenta.id_cuenta,
        )
        self.assertTrue(
            SesionActivaNavegador.objects.filter(
                identificador_navegador="browser-test-123",
                cuenta=cuenta,
            ).exists()
        )


class PasswordPolicyTests(SimpleTestCase):
    def test_acepta_contrasenia_con_todos_los_requisitos(self):
        self.assertEqual(
            validar_contrasenia_segura("Barinas!2026"),
            "Barinas!2026",
        )

    def test_rechaza_contrasenias_que_omiten_un_requisito(self):
        for contrasenia in (
            "barinas!2026",
            "BARINAS!2026",
            "Barinas!abcdef",
            "Barinas2026",
            "A!1a",
        ):
            with self.subTest(contrasenia=contrasenia):
                with self.assertRaises(ValidationError):
                    validar_contrasenia_segura(contrasenia)


class RegistroContraseniaTests(TestCase):
    def test_registro_estudiantil_rechaza_contrasenia_debil_en_servidor(self):
        respuesta = self.client.post(
            reverse("registro_est"),
            {
                "nombres": "Ana",
                "apellidos": "Pérez",
                "nacionalidad": "V",
                "cedula_identidad": "12345678",
                "correo_electronico": "ana",
                "dominio": "@example.com",
                "prefijo": "+58",
                "telefono": "4121234567",
                "usuario": "ana_test",
                "password": "contrasena",
            },
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(
            respuesta.json()["title"],
            "Contraseña insegura",
        )


class SeguridadMapaPermisosTests(TestCase):
    def test_modulos_internos_tienen_roles_por_defecto(self):
        from permisos.mapa_permisos import DEFAULT_MODULE_ROLES
        self.assertTrue({
            "inicio_sesion", "gestion_institucional",
            "notas_academicas", "documentos", "bitacora"
        }.issubset(DEFAULT_MODULE_ROLES))

    def test_vistas_internas_requieren_sesion_en_inicio_y_documentos(self):
        rutas_internas = (
            ("datos_usr_admin", {}),
            ("documentos:emitir_reporte_academico", {"id_estudiante": 1}),
        )

        for nombre_url, argumentos in rutas_internas:
            with self.subTest(nombre_url=nombre_url):
                response = self.client.get(
                    reverse(nombre_url, kwargs=argumentos)
                )
                self.assertRedirects(
                    response,
                    reverse("inicio_sesion"),
                    fetch_redirect_response=False,
                )

    def test_bitacora_restringida_a_roles_administrativos(self):
        from permisos.mapa_permisos import URL_PERMISSIONS, ROLES_ADMINISTRATIVOS
        self.assertEqual(URL_PERMISSIONS["bitacora_acciones"], ROLES_ADMINISTRATIVOS)

    def test_rutas_de_autenticacion_son_publicas(self):
        from permisos.mapa_permisos import PUBLIC_URL_NAMES
        self.assertIn("inicio_sesion", PUBLIC_URL_NAMES)
        self.assertIn("panel_registro", PUBLIC_URL_NAMES)
        self.assertIn("verificar_codigo_correo_admin", PUBLIC_URL_NAMES)

    @override_settings(
        STORAGES={
            "default": {
                "BACKEND": "django.core.files.storage.FileSystemStorage",
            },
            "staticfiles": {
                "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
            },
        }
    )
    def test_visitante_puede_abrir_el_panel_de_registro(self):
        respuesta = self.client.get(reverse("panel_registro"))

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Crear una cuenta")
