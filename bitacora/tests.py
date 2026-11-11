from django.contrib.sessions.backends.db import SessionStore
from django.test import RequestFactory, TestCase, override_settings

from bitacora.models import RegistroAccion
from bitacora.views import bitacora_acciones


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
class FiltrosBitacoraTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        RegistroAccion.objects.create(
            nombre_usuario="Ana",
            categoria="ACADEMICO",
            modulo="Horario",
            accion="Registro de horario",
            descripcion="Se guardó un horario académico.",
            resultado="EXITOSO",
        )
        RegistroAccion.objects.create(
            nombre_usuario="Luis",
            categoria="SEGURIDAD",
            modulo="Autenticación",
            accion="Inicio de sesión",
            descripcion="Inicio de sesión rechazado.",
            resultado="FALLIDO",
        )

    def crear_request(self, path, query=None, **meta):
        request = self.factory.get(path, query or {}, **meta)
        request.session = SessionStore()
        request.session["id_cuenta"] = 1
        request.session["rol"] = ["Director General"]
        return request

    def test_filtro_ajax_retorna_solo_coincidencias_como_fragmento(self):
        request = self.crear_request(
            "/bitacora/",
            {"categoria": "ACADEMICO"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        respuesta = bitacora_acciones(request)

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Registro de horario")
        self.assertNotContains(respuesta, "Inicio de sesión")
        self.assertNotContains(respuesta, "Bitácora de Acciones")

    def test_solicitud_normal_sigue_renderizando_la_pagina_completa(self):
        request = self.crear_request("/bitacora/")

        respuesta = bitacora_acciones(request)

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Bitácora de Acciones")
        self.assertContains(respuesta, "filtros-bitacora")
