import json
from contextlib import nullcontext
from datetime import date
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.test import RequestFactory, SimpleTestCase

from gestion_institucional.views.calendario_academico import (
    calendario_datos,
    calendario_guardar,
    limites_fechas_calendario,
)
from gestion_institucional.views.gestion_personal import pre_reg_personal


class ValidacionPreRegistroPersonalTests(SimpleTestCase):
    def setUp(self):
        self.datos = {
            "nombres": "Ana",
            "apellidos": "Pérez",
            "nacionalidad": "V",
            "cedula_identidad": "1234567",
            "correo_electronico": "ana.perez",
            "dominio": "@gmail.com",
            "prefijo": "0414",
            "telefono": "1234567",
        }

    def enviar_datos(self, cambios):
        datos = {**self.datos, **cambios}
        request = RequestFactory().post("/pre_reg_personal/", data=datos)
        return pre_reg_personal(request)

    def test_rechaza_cedula_con_formato_no_valido_en_el_servidor(self):
        response = self.enviar_datos({"cedula_identidad": "12ABC"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            json.loads(response.content)["title"],
            "Cédula no válida",
        )

    def test_rechaza_dominio_no_permitido_en_el_servidor(self):
        response = self.enviar_datos({"dominio": "@ejemplo.invalid"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            json.loads(response.content)["title"],
            "Correo no válido",
        )

    def test_rechaza_telefono_con_formato_no_valido_en_el_servidor(self):
        response = self.enviar_datos({"telefono": "12345"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            json.loads(response.content)["title"],
            "Teléfono no válido",
        )


class ActualizacionCalendarioTests(SimpleTestCase):
    def test_limites_respetan_mes_periodo_y_anio_registrado(self):
        calendario = SimpleNamespace(
            fecha_inicio=date(2024, 9, 15),
            tipo="PERIODO",
        )

        limites = limites_fechas_calendario(calendario, "Tramo I")

        self.assertEqual(limites["fecha_inicio_min"], "2024-01-01")
        self.assertEqual(limites["fecha_inicio_max"], "2024-01-31")
        self.assertEqual(limites["fecha_final_min"], "2024-04-01")
        self.assertEqual(limites["fecha_final_max"], "2024-04-30")

    def test_regresa_sin_limites_para_periodo_sin_regla(self):
        calendario = SimpleNamespace(
            fecha_inicio=date(2024, 2, 1),
            tipo="PERIODO",
        )

        limites = limites_fechas_calendario(calendario, "Período desconocido")

        self.assertIsNone(limites)

    def test_consulta_calendario_sin_periodo_asociado(self):
        calendario = SimpleNamespace(
            id_calendario_academico=7,
            fecha_inicio=date(2026, 8, 1),
            fecha_final=date(2026, 8, 31),
            descripcion="Vacaciones",
            tipo="VACACIONES",
            get_tipo_display=lambda: "Vacaciones",
        )
        request = RequestFactory().post(
            "/calendario_datos/",
            data={"id_calendario": "7"},
        )

        with (
            patch(
                "gestion_institucional.views.calendario_academico.CalendarioAcademico.objects.get",
                return_value=calendario,
            ),
            patch(
                "gestion_institucional.views.calendario_academico.CalendarioPeriodo.objects.filter"
            ) as filtrar_relaciones,
        ):
            filtrar_relaciones.return_value.select_related.return_value.first.return_value = None
            response = calendario_datos(request)

        resultado = json.loads(response.content)
        self.assertEqual(resultado["estado"], "exito")
        self.assertIsNone(resultado["calendario"]["periodo"])
        self.assertEqual(resultado["calendario"]["fecha_inicio"], "2026-08-01")

    def test_rechaza_fecha_final_anterior_al_inicio(self):
        calendario = SimpleNamespace(
            id_calendario_academico=7,
            fecha_inicio=date(2026, 8, 1),
            fecha_final=date(2026, 8, 31),
            tipo="VACACIONES",
            save=lambda: None,
        )
        request = RequestFactory().post(
            "/calendario_guardar/",
            data={
                "id_calendario": "7",
                "descripcion": "Vacaciones modificadas",
                "fecha_inicio": "2026-08-10",
                "fecha_finalizado": "2026-08-09",
            },
        )

        with (
            patch(
                "gestion_institucional.views.calendario_academico.CalendarioAcademico.objects.get",
                return_value=calendario,
            ),
            patch(
                "gestion_institucional.views.calendario_academico.CalendarioPeriodo.objects.filter"
            ) as filtrar_relaciones,
        ):
            filtrar_relaciones.return_value.select_related.return_value.first.return_value = None
            response = calendario_guardar(request)

        resultado = json.loads(response.content)
        self.assertEqual(resultado["estado"], "falla")
        self.assertEqual(resultado["title"], "Rango de fechas no válido")

    def test_rechaza_mes_y_anio_fuera_de_regla_del_periodo(self):
        calendario = SimpleNamespace(
            id_calendario_academico=7,
            fecha_inicio=date(2026, 4, 1),
            fecha_final=date(2026, 4, 30),
            tipo="CARGA_NOTAS",
        )
        relacion = SimpleNamespace(
            periodo=SimpleNamespace(nombre="Tramo I"),
            periodo_id=3,
        )
        with (
            patch(
                "gestion_institucional.views.calendario_academico.CalendarioAcademico.objects.get",
                return_value=calendario,
            ),
            patch(
                "gestion_institucional.views.calendario_academico.CalendarioPeriodo.objects.filter"
            ) as filtrar_relaciones,
        ):
            filtrar_relaciones.return_value.select_related.return_value.first.return_value = relacion
            for fecha_inicio, fecha_final in (
                ("2026-11-10", "2026-11-11"),
                ("2027-04-10", "2027-04-11"),
            ):
                with self.subTest(fecha_inicio=fecha_inicio):
                    request = RequestFactory().post(
                        "/calendario_guardar/",
                        data={
                            "id_calendario": "7",
                            "descripcion": "Carga de notas",
                            "fecha_inicio": fecha_inicio,
                            "fecha_finalizado": fecha_final,
                        },
                    )
                    response = calendario_guardar(request)
                    resultado = json.loads(response.content)
                    self.assertEqual(resultado["estado"], "falla")
                    self.assertEqual(
                        resultado["title"],
                        "Fecha fuera del rango permitido",
                    )

    def test_actualiza_descripcion_del_calendario(self):
        calendario = SimpleNamespace(
            id_calendario_academico=7,
            fecha_inicio=date(2026, 8, 1),
            fecha_final=date(2026, 8, 31),
            tipo="VACACIONES",
            descripcion="Descripción anterior",
            save=Mock(),
        )
        request = RequestFactory().post(
            "/calendario_guardar/",
            data={
                "id_calendario": "7",
                "descripcion": "Vacaciones de agosto",
                "fecha_inicio": "2026-08-01",
                "fecha_finalizado": "2026-08-31",
            },
        )
        request.session = {}

        with (
            patch(
                "gestion_institucional.views.calendario_academico.CalendarioAcademico.objects.get",
                return_value=calendario,
            ),
            patch(
                "gestion_institucional.views.calendario_academico.CalendarioPeriodo.objects.filter"
            ) as filtrar_relaciones,
            patch(
                "gestion_institucional.views.calendario_academico.Bitacora.objects.create"
            ),
            patch(
                "gestion_institucional.views.calendario_academico.transaction.atomic",
                return_value=nullcontext(),
            ),
        ):
            filtrar_relaciones.return_value.select_related.return_value.first.return_value = None
            response = calendario_guardar(request)

        resultado = json.loads(response.content)
        self.assertEqual(resultado["estado"], "exito")
        self.assertEqual(calendario.descripcion, "Vacaciones de agosto")
        calendario.save.assert_called_once()

    def test_rechaza_descripcion_vacia_o_mayor_a_150_caracteres(self):
        for descripcion in ("   ", "x" * 151):
            with self.subTest(longitud=len(descripcion)):
                request = RequestFactory().post(
                    "/calendario_guardar/",
                    data={
                        "id_calendario": "7",
                        "descripcion": descripcion,
                        "fecha_inicio": "2026-08-01",
                        "fecha_finalizado": "2026-08-31",
                    },
                )
                response = calendario_guardar(request)

                resultado = json.loads(response.content)
                self.assertEqual(resultado["estado"], "falla")
                self.assertIn("Descripción", resultado["title"])
