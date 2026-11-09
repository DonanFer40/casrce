import re

import pyotp
from cryptography.fernet import Fernet
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.conf import settings
from django.core import mail
from django.core.exceptions import ValidationError
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from inicio_sesion.models import (
    Contacto,
    ConfiguracionSeguridadAdmin,
    Discapacidad,
    Docente,
    DocenteAsignadoMateria,
    Estudiante,
    Materia,
    MateriaAsignada,
    Nucleos,
    PeriodoAcademico,
    Pnf,
    Residencia,
    TrayectoAcademico,
    Usuario,
    VerificacionCodigo,
)
from inicio_sesion.validators import validar_contrasenia_segura
from notas_academicas.models import (
    DetalleEvaluacion,
    DetallePlanificacion,
    PlanificacionAcademica,
)

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
            "notas_academicas", "bitacora"
        }.issubset(DEFAULT_MODULE_ROLES))

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

    def test_modulos_directivos_y_horarios_tienen_roles_exclusivos(self):
        from permisos.mapa_permisos import URL_PERMISSIONS

        self.assertEqual(URL_PERMISSIONS["reg_aula"], {"Director General"})
        self.assertEqual(
            URL_PERMISSIONS["registrar_horario"],
            {"Coordinador PNF"},
        )
        self.assertEqual(
            URL_PERMISSIONS["horario_estudiante"],
            {"Estudiante"},
        )


@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }
)
class ConfiguracionUsuarioTests(TestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create(
            nombres="Ana",
            apellidos="Pérez",
            genero="Femenino",
            cedula_identidad="V12345678",
            estado_civil="Soltera",
        )
        Contacto.objects.create(
            id_usuario=self.usuario,
            correo_electronico="ana.configuracion@example.com",
            telefono_personal="04120000000",
        )

    def test_configuracion_requiere_sesion(self):
        response = self.client.get(reverse("configuracion_usuario"))
        self.assertRedirects(response, reverse("inicio_sesion"))

    def test_configuracion_actualiza_datos_personales_y_residencia(self):
        session = self.client.session
        session["cedula_usuario"] = self.usuario.cedula_identidad
        session.save()

        response = self.client.post(
            reverse("actualizar_registro_usuario"),
            {
                "nombres": "Ana María",
                "apellidos": "Pérez",
                "genero": "Femenino",
                "estado_civil": "Soltera",
                "telefono_personal": "04125551234",
                "telefono_suplete": "",
                "condicion_residencia": "Residente",
                "municipio": "Barinas",
                "parroquia": "Barinas",
                "direccion_residencia": "Sector Centro",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.nombres, "Ana María")
        self.assertEqual(
            self.usuario.residencia.direccion_residencia,
            "Sector Centro",
        )
        self.assertEqual(self.usuario.contacto.telefono_personal, "04125551234")

    def test_configuracion_rechaza_residencia_incompleta(self):
        session = self.client.session
        session["cedula_usuario"] = self.usuario.cedula_identidad
        session.save()

        response = self.client.post(
            reverse("actualizar_registro_usuario"),
            {
                "nombres": "Ana",
                "apellidos": "Pérez",
                "genero": "Femenino",
                "estado_civil": "Soltera",
                "condicion_residencia": "Residente",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Residencia.objects.filter(id_usuario=self.usuario).exists())
        self.assertContains(response, "Completa todos los datos de residencia.")

    def test_pantalla_de_configuracion_enlaza_el_formulario_de_edicion(self):
        session = self.client.session
        session["cedula_usuario"] = self.usuario.cedula_identidad
        session["rol"] = ["Estudiante"]
        session.save()

        response = self.client.get(reverse("configuracion_usuario"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "Sesion/actualizar/configuracion_usuarios.html",
        )
        self.assertContains(response, reverse("actualizar_registro_usuario"))

    def test_estudiante_puede_actualizar_datos_de_discapacidad(self):
        Estudiante.objects.create(usuario=self.usuario)
        session = self.client.session
        session["cedula_usuario"] = self.usuario.cedula_identidad
        session.save()

        response = self.client.post(
            reverse("actualizar_registro_usuario"),
            {
                "nombres": "Ana",
                "apellidos": "Pérez",
                "genero": "Femenino",
                "estado_civil": "Soltera",
                "carnet_discapacidad": "C-123",
                "registro_medico": "12345",
                "tipos_discapacidad": "Visual",
                "grado_discapacidad": "Leve",
                "causa_discapacidad": "Congenita",
            },
        )

        self.assertEqual(response.status_code, 200)
        discapacidad = Discapacidad.objects.get(id_usuario=self.usuario)
        self.assertEqual(discapacidad.tipo_discapacidad, "Visual")
        self.assertContains(response, "Datos de discapacidad")


@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }
)
class PlanificacionDocenteForoTests(TestCase):
    def test_planificacion_docente_muestra_estado_vacio(self):
        response = self.client.get(reverse("Planificacion_Docente"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Todavía no hay planificaciones aprobadas para mostrar.",
        )

    def test_planificaciones_ordenadas_por_nucleo_y_detalle_publicado(self):
        pnf = Pnf.objects.create(pnf="Informática", codigo="INF")
        trayecto = TrayectoAcademico.objects.create(nombre="Trayecto I")
        periodo = PeriodoAcademico.objects.create(nombre="2026-I")

        nucleos_entrada = ["Pedraza", "Socopo", "Barinitas", "Barinas"]
        for indice, nombre_nucleo in enumerate(nucleos_entrada):
            nucleo = Nucleos.objects.create(
                municipio=nombre_nucleo,
                direccion=f"Dirección {nombre_nucleo}",
            )
            usuario = Usuario.objects.create(
                nombres=f"Docente{indice}",
                apellidos="Prueba",
                cedula_identidad=f"CI-{indice}",
            )
            docente = Docente.objects.create(
                usuario=usuario,
                nucleo=nucleo,
                pnf=pnf,
            )
            materia = Materia.objects.create(
                nombre=f"Materia {nombre_nucleo}",
                codigo=f"M{indice}",
                recuperacion="Evaluación",
                htea=2,
                htei=2,
                id_trayecto=trayecto,
                id_pnf=pnf,
            )
            asignacion = MateriaAsignada.objects.create(materia=materia)
            DocenteAsignadoMateria.objects.create(
                materia_asignada=asignacion,
                docente=docente,
                rol="PRINCIPAL",
            )
            plan = PlanificacionAcademica.objects.create(
                pnf=pnf,
                nucleo=nucleo,
                materia_asignacion=asignacion,
                periodo_academico=periodo,
                estado_aceptacion="ACEPTADA",
            )
            if nombre_nucleo == "Barinas":
                unidad = DetallePlanificacion.objects.create(
                    plan_academico=plan,
                    titulo_unidad="Introducción",
                    ponderacion=100,
                    contenido_unidad="Contenidos de prueba",
                )
                DetalleEvaluacion.objects.create(
                    detalle_plan=unidad,
                    metodo_evaluacion="Taller",
                    porcentaje_evaluacion=100,
                    fecha_evaluacion="2026-11-08",
                )

        response = self.client.get(reverse("Planificacion_Docente"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [plan.nucleo.municipio for plan in response.context["planes"]],
            ["Barinas", "Barinitas", "Socopo", "Pedraza"],
        )
        self.assertContains(response, "Contenidos de prueba")
        self.assertContains(response, "Taller")


@override_settings(
    CASRCE_ADMIN_USERNAME="casrce-root",
    CASRCE_ADMIN_GATE_USERNAME="casrce-gate",
    CASRCE_ADMIN_GATE_PASSWORD_HASH=make_password("GatePassword!234"),
    CASRCE_ADMIN_FERNET_KEY=Fernet.generate_key().decode(),
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    DEFAULT_FROM_EMAIL="casrce@example.com",
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    },
)
class AccesoSuperusuarioTests(TestCase):
    def setUp(self):
        self.superusuario = get_user_model().objects.create_superuser(
            username="casrce-root",
            email="admin@example.com",
            password="RealPassword!234",
        )
        self.secreto_totp = pyotp.random_base32()
        secreto_cifrado = Fernet(
            settings.CASRCE_ADMIN_FERNET_KEY.encode()
        ).encrypt(self.secreto_totp.encode()).decode()
        ConfiguracionSeguridadAdmin.objects.create(
            usuario=self.superusuario,
            secreto_totp_cifrado=secreto_cifrado,
            totp_activo=True,
        )

    def test_acceso_admin_verifica_correo_totp_y_login_django(self):
        respuesta_inicio = self.client.post(
            reverse("inicio_sesion"),
            {
                "usuario": "casrce-gate",
                "contrasenia": "GatePassword!234",
            },
        )
        self.assertEqual(respuesta_inicio.status_code, 200)
        self.assertEqual(
            respuesta_inicio.json()["url"],
            reverse("acceso_admin"),
        )
        self.assertEqual(len(mail.outbox), 1)

        respuesta_acceso = self.client.get(reverse("acceso_admin"))
        self.assertEqual(respuesta_acceso.status_code, 200)
        self.assertTemplateUsed(respuesta_acceso, "Security/acceso_admin.html")

        codigo_correo = re.search(r"\b\d{6}\b", mail.outbox[0].body).group()
        respuesta_correo = self.client.post(
            reverse("verificar_codigo_correo_admin"),
            {"codigo": codigo_correo},
        )
        self.assertTrue(respuesta_correo.json()["success"])

        respuesta_totp = self.client.post(
            reverse("verificar_totp_admin"),
            {"codigo": pyotp.TOTP(self.secreto_totp).now()},
        )
        self.assertTrue(respuesta_totp.json()["success"])
        self.assertEqual(
            respuesta_totp.json()["siguiente"],
            f'{reverse("admin:login")}?next=/admin/',
        )

        respuesta_login_admin = self.client.get(
            respuesta_totp.json()["siguiente"],
        )
        self.assertEqual(respuesta_login_admin.status_code, 200)

        respuesta_admin = self.client.post(
            reverse("admin:login"),
            {
                "username": "casrce-root",
                "password": "RealPassword!234",
                "next": "/admin/",
            },
            follow=True,
        )
        self.assertEqual(
            respuesta_admin.status_code,
            200,
            respuesta_admin.redirect_chain,
        )
        self.assertTrue(respuesta_admin.wsgi_request.user.is_superuser)

    def test_primer_acceso_redirige_al_registro_de_google_authenticator(self):
        ConfiguracionSeguridadAdmin.objects.filter(
            usuario=self.superusuario
        ).delete()
        self.client.force_login(self.superusuario)

        respuesta = self.client.get("/admin/")

        self.assertRedirects(
            respuesta,
            "/seguridad-admin/configurar-totp/",
            fetch_redirect_response=False,
        )
