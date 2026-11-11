from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.backends.db import SessionStore
from django.test import RequestFactory, TestCase, override_settings

from inicio_sesion.models import SeccionAcademica
from gestion_institucional.views.seccion import reg_sec


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
class SeccionAutomaticaEnFormularioTests(TestCase):
    def test_formulario_muestra_desde_el_servidor_la_primera_letra_libre(self):
        SeccionAcademica.objects.create(nombre="A", turno="Diurno")
        request = RequestFactory().get("/reg_sec/")
        request.session = SessionStore()
        request.user = AnonymousUser()

        respuesta = reg_sec(request)

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'value="B"')
        self.assertContains(respuesta, "Se asignará automáticamente la sección B.")

    def test_formulario_informa_cuando_no_hay_letras_disponibles(self):
        for letra in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            SeccionAcademica.objects.create(nombre=letra, turno="Diurno")
        request = RequestFactory().get("/reg_sec/")
        request.session = SessionStore()
        request.user = AnonymousUser()

        respuesta = reg_sec(request)

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'value=""')
        self.assertContains(respuesta, "Las letras de la A a la Z están ocupadas.")
