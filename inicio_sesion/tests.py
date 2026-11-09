from datetime import timedelta
from urllib.parse import parse_qs, urlsplit

from django.contrib.auth.hashers import make_password
from django.contrib.sessions.backends.db import SessionStore
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpResponse, HttpResponseNotFound
from django.test import RequestFactory, TestCase
from django.test import override_settings
from django.urls import reverse
from django.urls import resolve
from django.utils import timezone

from inicio_sesion.models import (
    Cuenta,
    Contacto,
    ControlIntentosInicioSesion,
    DirectorGeneral,
    Nucleos,
    SesionActivaNavegador,
    Usuario,
    VerificacionCodigo,
)
from middleware.seguridad_roles import SeguridadRolesMiddleware
from middleware.sesiones_por_pestana import SesionesPorPestanaMiddleware

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
        self.assertIn("verificar_codigo_correo_admin", PUBLIC_URL_NAMES)


class ValidacionCorreoTests(TestCase):
    def test_disponibilidad_compara_correo_sin_distinguir_mayusculas(self):
        usuario = Usuario.objects.create(
            nombres="Ana",
            apellidos="Pérez",
            genero="F",
            cedula_identidad="V-7654321",
            estado_civil="Soltera",
        )
        Contacto.objects.create(
            correo_electronico="Ana.Perez@gmail.com",
            telefono_personal="04141234567",
            id_usuario=usuario,
        )

        response = self.client.post(
            reverse("validar_email"),
            {"correo": "ana.perez", "dominio": "@gmail.com"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["existe"])


class AutenticacionSesionTests(TestCase):
    def iniciar_sesion(self, datos, **kwargs):
        kwargs.setdefault("HTTP_X_CASRCE_BROWSER_ID", "navegador-prueba")
        return self.client.post(
            reverse("inicio_sesion"),
            datos,
            **kwargs,
        )

    @override_settings(CASRCE_ADMIN_GATE_USERNAME="otro-usuario")
    def test_tres_intentos_fallidos_bloquean_la_cuenta_por_cinco_minutos(self):
        usuario = Usuario.objects.create(
            nombres="Ana",
            apellidos="Pérez",
            genero="F",
            cedula_identidad="V-4444444",
            estado_civil="Soltera",
        )
        cuenta = Cuenta.objects.create(
            id_usuario=usuario,
            usuario="intentos-test",
            clave=make_password("clave-correcta"),
            tipo_cuenta="ADMIN",
        )

        for numero_intento in range(1, 4):
            respuesta = self.iniciar_sesion(
                {
                    "usuario": cuenta.usuario,
                    "contrasenia": "clave-incorrecta",
                },
            )
            if numero_intento < 3:
                self.assertEqual(respuesta.status_code, 200)
                self.assertEqual(respuesta.json()["estado"], "fallo")
            else:
                self.assertEqual(respuesta.status_code, 429)
                self.assertEqual(respuesta.json()["estado"], "bloqueado")

        control = ControlIntentosInicioSesion.objects.get(cuenta=cuenta)
        self.assertEqual(control.intentos, 3)
        self.assertIsNotNone(control.bloqueado_hasta)
        self.assertAlmostEqual(
            (control.bloqueado_hasta - timezone.now()).total_seconds(),
            5 * 60,
            delta=2,
        )

        respuesta_bloqueada = self.iniciar_sesion(
            {
                "usuario": cuenta.usuario,
                "contrasenia": "clave-correcta",
            },
        )
        self.assertEqual(respuesta_bloqueada.status_code, 429)
        self.assertEqual(respuesta_bloqueada.json()["estado"], "bloqueado")

    @override_settings(CASRCE_ADMIN_GATE_USERNAME="otro-usuario")
    def test_inicio_sesion_reinicia_intentos_tras_expirar_bloqueo(self):
        usuario = Usuario.objects.create(
            nombres="Luis",
            apellidos="Gómez",
            genero="M",
            cedula_identidad="V-5555555",
            estado_civil="Soltero",
        )
        cuenta = Cuenta.objects.create(
            id_usuario=usuario,
            usuario="desbloqueo-test",
            clave=make_password("clave-correcta"),
            tipo_cuenta="ADMIN",
        )
        control = ControlIntentosInicioSesion.objects.create(
            cuenta=cuenta,
            intentos=3,
            bloqueado_hasta=timezone.now() - timedelta(seconds=1),
        )

        respuesta = self.iniciar_sesion(
            {
                "usuario": cuenta.usuario,
                "contrasenia": "clave-correcta",
            },
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json()["estado"], "exito")
        control.refresh_from_db()
        self.assertEqual(control.intentos, 0)
        self.assertIsNone(control.bloqueado_hasta)

    def test_pestanas_nuevas_reciben_identificadores_distintos(self):
        middleware = SesionesPorPestanaMiddleware(
            lambda request: HttpResponse("ok")
        )
        identificadores = []
        for _ in range(2):
            request = RequestFactory().get(
                reverse("inicio_sesion"),
                HTTP_ACCEPT="text/html",
            )
            SessionMiddleware(lambda current_request: None).process_request(
                request
            )
            respuesta = middleware(request)
            self.assertEqual(respuesta.status_code, 302)
            identificadores.append(
                respuesta["X-CASRCE-Tab-Session"]
            )
            self.assertIn(
                f"tab_session_id={identificadores[-1]}",
                respuesta["Location"],
            )
            self.assertIn("tab_session_bootstrap=", respuesta["Location"])

        self.assertNotEqual(*identificadores)

    def test_enlace_de_inicio_de_sesion_es_de_un_solo_uso(self):
        middleware = SesionesPorPestanaMiddleware(
            lambda request: HttpResponse("ok")
        )
        request = RequestFactory().get(
            reverse("inicio_sesion"),
            HTTP_ACCEPT="text/html",
        )
        SessionMiddleware(lambda current_request: None).process_request(request)
        inicial = middleware(request)
        parametros = parse_qs(urlsplit(inicial["Location"]).query)
        identificador = parametros["tab_session_id"][0]
        bootstrap = parametros["tab_session_bootstrap"][0]

        request_sesion = RequestFactory().get(
            f'{reverse("inicio_sesion")}?tab_session_id={identificador}'
            f"&tab_session_bootstrap={bootstrap}",
            HTTP_ACCEPT="text/html",
        )
        SessionMiddleware(lambda current_request: None).process_request(
            request_sesion
        )
        primera_visita = middleware(request_sesion)
        self.assertEqual(primera_visita.status_code, 200)
        self.assertEqual(
            primera_visita["X-CASRCE-Tab-Session"],
            identificador,
        )

        request_repetida = RequestFactory().get(
            f'{reverse("inicio_sesion")}?tab_session_id={identificador}'
            f"&tab_session_bootstrap={bootstrap}",
            HTTP_ACCEPT="text/html",
        )
        SessionMiddleware(lambda current_request: None).process_request(
            request_repetida
        )
        visita_repetida = middleware(request_repetida)
        self.assertEqual(visita_repetida.status_code, 302)
        self.assertNotEqual(
            visita_repetida["X-CASRCE-Tab-Session"],
            identificador,
        )

    @override_settings(CASRCE_ADMIN_GATE_USERNAME="otro-usuario")
    def test_pestanas_conservan_sesiones_independientes(self):
        cuentas = []
        for nombre, cedula in (
            ("tab-usuario-a", "V-1111111"),
            ("tab-usuario-b", "V-2222222"),
        ):
            usuario = Usuario.objects.create(
                nombres=nombre,
                apellidos="Prueba",
                genero="F",
                cedula_identidad=cedula,
                estado_civil="Soltera",
            )
            cuentas.append(Cuenta.objects.create(
                id_usuario=usuario,
                usuario=nombre,
                clave=make_password("clave-segura"),
                tipo_cuenta="ADMIN",
            ))

        identificadores_iniciales = ("a" * 32, "b" * 32)
        identificadores_sesion = []

        for cuenta, identificador in zip(cuentas, identificadores_iniciales):
            respuesta = self.iniciar_sesion(
                {
                    "usuario": cuenta.usuario,
                    "contrasenia": "clave-segura",
                },
                HTTP_X_CASRCE_TAB_SESSION=identificador,
            )

            if identificador == identificadores_iniciales[0]:
                self.assertEqual(respuesta.status_code, 200)
                self.assertEqual(respuesta.json()["estado"], "exito")
                identificador_sesion = respuesta["X-CASRCE-Tab-Session"]
                self.assertNotEqual(identificador_sesion, identificador)
                identificadores_sesion.append(identificador_sesion)
            else:
                self.assertEqual(respuesta.status_code, 409)
                self.assertEqual(
                    respuesta.json()["estado"],
                    "sesion_activa_otro_tab",
                )

        sesion = SessionStore(session_key=identificadores_sesion[0])
        self.assertEqual(sesion["id_cuenta"], cuentas[0].id_cuenta)
        self.assertEqual(SesionActivaNavegador.objects.count(), 1)

        segunda_sesion = self.iniciar_sesion(
            {
                "usuario": cuentas[1].usuario,
                "contrasenia": "clave-segura",
            },
            HTTP_X_CASRCE_TAB_SESSION="c" * 32,
            HTTP_X_CASRCE_BROWSER_ID="otro-navegador",
        )
        self.assertEqual(segunda_sesion.status_code, 200)
        self.assertEqual(segunda_sesion.json()["estado"], "exito")

    def test_vista_interna_marca_la_pestana_como_autenticada(self):
        usuario = Usuario.objects.create(
            nombres="Ana",
            apellidos="Pérez",
            genero="F",
            cedula_identidad="V-7654321",
            estado_civil="Soltera",
        )
        cuenta = Cuenta.objects.create(
            id_usuario=usuario,
            usuario="tab-test",
            clave=make_password("clave-segura"),
            tipo_cuenta="ADMIN",
        )
        nucleo = Nucleos.objects.create(
            municipio="Núcleo de prueba",
            direccion="Dirección de prueba",
        )
        DirectorGeneral.objects.create(
            usuario=usuario,
            nucleo=nucleo,
        )

        ruta = reverse("datos_usr_admin")
        request = RequestFactory().get(ruta)
        SessionMiddleware(lambda current_request: None).process_request(request)
        request.session["id_cuenta"] = cuenta.id_cuenta
        request.resolver_match = resolve(ruta)

        middleware = SeguridadRolesMiddleware(lambda current_request: None)
        resultado = middleware.process_view(
            request,
            request.resolver_match.func,
            request.resolver_match.args,
            request.resolver_match.kwargs,
        )

        self.assertIsNone(resultado)
        self.assertTrue(request.tab_auth_required)

    def test_usuario_autenticado_que_abre_login_vuelve_a_su_modulo(self):
        usuario = Usuario.objects.create(
            nombres="Ana",
            apellidos="Pérez",
            genero="F",
            cedula_identidad="V-7676767",
            estado_civil="Soltera",
        )
        cuenta = Cuenta.objects.create(
            id_usuario=usuario,
            usuario="volver-modulo",
            clave=make_password("clave-segura"),
            tipo_cuenta="ADMIN",
        )
        ruta_login = reverse("inicio_sesion")
        ruta_modulo = "/modulo-actual/"
        request = RequestFactory().get(ruta_login)
        SessionMiddleware(lambda current_request: None).process_request(request)
        request.session["id_cuenta"] = cuenta.id_cuenta
        request.session["casrce_ultima_url_autorizada"] = ruta_modulo
        request.resolver_match = resolve(ruta_login)

        middleware = SeguridadRolesMiddleware(lambda current_request: None)
        respuesta = middleware.process_view(
            request,
            request.resolver_match.func,
            request.resolver_match.args,
            request.resolver_match.kwargs,
        )

        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(respuesta["Location"], ruta_modulo)

    def test_acceso_a_modulo_sin_permiso_redirige_al_panel(self):
        usuario = Usuario.objects.create(
            nombres="Luis",
            apellidos="Gómez",
            genero="M",
            cedula_identidad="V-7878787",
            estado_civil="Soltero",
        )
        cuenta = Cuenta.objects.create(
            id_usuario=usuario,
            usuario="sin-rol",
            clave=make_password("clave-segura"),
            tipo_cuenta="ADMIN",
        )
        ruta = reverse("bitacora_acciones")
        request = RequestFactory().get(ruta)
        SessionMiddleware(lambda current_request: None).process_request(request)
        request.session["id_cuenta"] = cuenta.id_cuenta
        request.resolver_match = resolve(ruta)

        middleware = SeguridadRolesMiddleware(lambda current_request: None)
        respuesta = middleware.process_view(
            request,
            request.resolver_match.func,
            request.resolver_match.args,
            request.resolver_match.kwargs,
        )

        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(respuesta["Location"], reverse("panel_usuario"))

    def test_url_inexistente_con_sesion_conserva_respuesta_404(self):
        usuario = Usuario.objects.create(
            nombres="Ana",
            apellidos="Pérez",
            genero="F",
            cedula_identidad="V-7979797",
            estado_civil="Soltera",
        )
        cuenta = Cuenta.objects.create(
            id_usuario=usuario,
            usuario="url-inexistente",
            clave=make_password("clave-segura"),
            tipo_cuenta="ADMIN",
        )
        ruta_modulo = "/modulo-actual/"
        request = RequestFactory().get(
            "/modulo-inexistente/",
            HTTP_ACCEPT="text/html",
        )
        SessionMiddleware(lambda current_request: None).process_request(request)
        request.session["id_cuenta"] = cuenta.id_cuenta
        request.session["casrce_ultima_url_autorizada"] = ruta_modulo

        middleware = SeguridadRolesMiddleware(
            lambda current_request: HttpResponseNotFound()
        )
        respuesta = middleware(request)

        self.assertEqual(respuesta.status_code, 404)

    def test_pagina_404_personalizada(self):
        storages = {
            "default": {
                "BACKEND": "django.core.files.storage.FileSystemStorage",
            },
            "staticfiles": {
                "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
            },
        }
        with override_settings(STORAGES=storages):
            respuesta = self.client.get(
                "/pagina-que-no-existe/",
                HTTP_ACCEPT="text/html",
                follow=True,
            )

        self.assertEqual(respuesta.status_code, 404)
        self.assertContains(
            respuesta,
            "Página no encontrada",
            status_code=404,
        )

    def test_pagina_vpn_muestra_la_imagen_y_es_publica(self):
        storages = {
            "default": {
                "BACKEND": "django.core.files.storage.FileSystemStorage",
            },
            "staticfiles": {
                "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
            },
        }
        with override_settings(STORAGES=storages):
            respuesta = self.client.get("/acceso-vpn/")

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Imagenes/pagina_vpn.png")
        self.assertContains(respuesta, "Acceso mediante VPN no permitido")

    def test_url_inexistente_sin_sesion_muestra_404_en_vez_de_redirigir(self):
        request = RequestFactory().get(
            "/modulo-inexistente/",
            HTTP_ACCEPT="text/html",
        )
        SessionMiddleware(lambda current_request: None).process_request(request)
        middleware = SeguridadRolesMiddleware(
            lambda current_request: HttpResponseNotFound()
        )

        respuesta = middleware(request)

        self.assertEqual(respuesta.status_code, 404)

    @override_settings(CASRCE_ADMIN_GATE_USERNAME="otro-usuario")
    def test_autenticacion_rota_y_limpia_la_sesion_previa(self):
        usuario = Usuario.objects.create(
            nombres="Ana",
            apellidos="Pérez",
            genero="F",
            cedula_identidad="V-1234567",
            estado_civil="Soltera",
        )
        Cuenta.objects.create(
            id_usuario=usuario,
            usuario="sesion-test",
            clave=make_password("contraseña-segura"),
            tipo_cuenta="ADMIN",
        )

        session = self.client.session
        session["dato_de_otra_sesion"] = "no conservar"
        session.save()
        session_key_anterior = session.session_key

        response = self.iniciar_sesion(
            {
                "usuario": "sesion-test",
                "contrasenia": "contraseña-segura",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["estado"], "exito")
        self.assertTrue(response.json()["tab_auth_required"])

        session_posterior = self.client.session
        self.assertNotEqual(
            session_posterior.session_key,
            session_key_anterior,
        )
        self.assertNotIn("dato_de_otra_sesion", session_posterior)
        self.assertEqual(session_posterior["id_cuenta"], Cuenta.objects.get(
            usuario="sesion-test"
        ).id_cuenta)
        self.assertAlmostEqual(
            session_posterior.get_expiry_age(),
            60 * 60 * 8,
            delta=2,
        )

    @override_settings(CASRCE_ADMIN_GATE_USERNAME="otro-usuario")
    def test_sesion_activa_advierte_y_solo_se_reemplaza_con_confirmacion(self):
        usuario_actual = Usuario.objects.create(
            nombres="Ana",
            apellidos="Pérez",
            genero="F",
            cedula_identidad="V-7654321",
            estado_civil="Soltera",
        )
        cuenta_actual = Cuenta.objects.create(
            id_usuario=usuario_actual,
            usuario="sesion-actual",
            clave=make_password("clave-actual"),
            tipo_cuenta="ADMIN",
        )
        usuario_nuevo = Usuario.objects.create(
            nombres="Luis",
            apellidos="Gómez",
            genero="M",
            cedula_identidad="V-1234567",
            estado_civil="Soltero",
        )
        cuenta_nueva = Cuenta.objects.create(
            id_usuario=usuario_nuevo,
            usuario="sesion-nueva",
            clave=make_password("clave-nueva"),
            tipo_cuenta="ADMIN",
        )

        session = self.client.session
        session["id_cuenta"] = cuenta_actual.id_cuenta
        session["usuario_nombre"] = "Ana Pérez"
        session.save()

        datos_login = {
            "usuario": "sesion-nueva",
            "contrasenia": "clave-nueva",
        }
        advertencia = self.iniciar_sesion(
            datos_login,
        )

        self.assertEqual(advertencia.status_code, 200)
        self.assertEqual(advertencia.json()["estado"], "advertencia")
        self.assertEqual(
            self.client.session["id_cuenta"],
            cuenta_actual.id_cuenta,
        )

        respuesta = self.iniciar_sesion(
            {**datos_login, "confirmar_nueva_sesion": "1"},
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json()["estado"], "exito")
        self.assertEqual(
            self.client.session["id_cuenta"],
            cuenta_nueva.id_cuenta,
        )

    def test_logout_impide_reutilizar_sesion_y_marca_respuestas_no_cacheables(self):
        usuario = Usuario.objects.create(
            nombres="Ana",
            apellidos="Pérez",
            genero="F",
            cedula_identidad="V-7654321",
            estado_civil="Soltera",
        )
        cuenta = Cuenta.objects.create(
            id_usuario=usuario,
            usuario="logout-test",
            clave=make_password("contraseña-segura"),
            tipo_cuenta="ADMIN",
        )
        session = self.client.session
        session["id_cuenta"] = cuenta.id_cuenta
        session.save()

        login_response = self.iniciar_sesion(
            {
                "usuario": "logout-test",
                "contrasenia": "contraseña-segura",
                "confirmar_nueva_sesion": "1",
            },
        )
        self.assertEqual(login_response.status_code, 200)
        self.assertEqual(login_response.json()["estado"], "exito")
        self.assertIn("no-store", login_response["Cache-Control"])

        logout_response = self.client.get(
            reverse("cerrar_sesion"),
            HTTP_X_CASRCE_BROWSER_ID="navegador-prueba",
        )
        self.assertEqual(logout_response.status_code, 302)
        self.assertIn("no-store", logout_response["Cache-Control"])
        self.assertNotIn("id_cuenta", self.client.session)
        self.assertFalse(SesionActivaNavegador.objects.exists())

        panel_sin_sesion = self.client.get(reverse("panel_usuario"))
        self.assertRedirects(
            panel_sin_sesion,
            reverse("inicio_sesion"),
            fetch_redirect_response=False,
        )

        nuevo_login = self.iniciar_sesion(
            {
                "usuario": "logout-test",
                "contrasenia": "contraseña-segura",
            },
            HTTP_X_CASRCE_TAB_SESSION="d" * 32,
        )
        self.assertEqual(nuevo_login.status_code, 200)
        self.assertEqual(nuevo_login.json()["estado"], "exito")
