import os
import unittest
from io import BytesIO
from tempfile import TemporaryDirectory
from datetime import date

from PIL import Image

from django.test import RequestFactory, TestCase, override_settings

from documentos.models import DocumentoInstitucional
from documentos.services.generador_qr import generar_qr_png
from documentos.views.reportes_estadisticos import (
    _datos_matricula,
    emitir_reporte_estadistico,
)
from inicio_sesion.models import (
    ControlEstudio,
    Cuenta,
    Estudiante,
    EstatusEstudiante,
    Nucleos,
    Pnf,
    TrayectoAcademico,
    Usuario,
)


class GeneradorQRTests(unittest.TestCase):
    def test_genera_png_valido(self):
        contenido = generar_qr_png("https://example.org/documento/abc")
        imagen = Image.open(BytesIO(contenido))
        self.assertEqual(imagen.format, "PNG")
        self.assertGreater(imagen.width, 0)

    def test_rechaza_contenido_vacio(self):
        with self.assertRaises(ValueError):
            generar_qr_png("")


class ReportesEstadisticosTests(TestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create(
            nombres="Control",
            apellidos="Prueba",
            genero="",
            cedula_identidad="V12345678",
            estado_civil="",
        )
        self.cuenta = Cuenta.objects.create(
            id_usuario=self.usuario,
            usuario="control-prueba",
            clave="no-se-usa",
            tipo_cuenta="ADMIN",
        )
        self.nucleo = Nucleos.objects.create(
            municipio="Barinas",
            direccion="Centro",
        )
        self.pnf = Pnf.objects.create(
            pnf="Informática",
            codigo="INF",
        )
        self.trayecto = TrayectoAcademico.objects.create(nombre="Trayecto I")
        ControlEstudio.objects.create(
            usuario=self.usuario,
            nucleo=self.nucleo,
            activo=True,
        )
        estudiante_usuario = Usuario.objects.create(
            nombres="Ana",
            apellidos="Pérez",
            genero="Femenino",
            cedula_identidad="V87654321",
            estado_civil="Soltera",
        )
        estudiante = Estudiante.objects.create(
            usuario=estudiante_usuario,
            nucleo=self.nucleo,
            pnf=self.pnf,
        )
        EstatusEstudiante.objects.create(
            estatus="Activo",
            estado="Activo",
            ingreso="Regular",
            descripcion_ingreso="Nuevo ingreso",
            fecha_ingreso=date(2026, 1, 15),
            trayecto=self.trayecto,
            estudiante=estudiante,
        )
        self.estudiante = estudiante

    def test_reporte_estadistico_se_registra_con_pdf_y_codigo_verificable(self):
        request = RequestFactory().post(
            "/documentos/reportes/estadisticos/emitir/",
            {"tipo": "matricula", "modo": "TOTAL"},
        )
        request.session = {"id_cuenta": self.cuenta.pk}

        with TemporaryDirectory() as media_root:
            with override_settings(
                MEDIA_ROOT=media_root,
                STORAGES={
                    "default": {
                        "BACKEND": "django.core.files.storage.FileSystemStorage",
                    },
                    "staticfiles": {
                        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
                    },
                },
            ):
                response = emitir_reporte_estadistico(request)
                self.assertEqual(response.status_code, 200)
                documento = DocumentoInstitucional.objects.get(
                    tipo_documento="REPORTE_MATRICULA",
                )
                self.assertTrue(os.path.exists(documento.archivo_pdf.path))

        self.assertTrue(documento.archivo_pdf)
        self.assertEqual(
            documento.datos_documento["generado_por_usuario_id"],
            self.usuario.pk,
        )

    def test_estadisticas_respetan_nucleo_y_cuentan_al_estudiante_una_vez(self):
        EstatusEstudiante.objects.create(
            estatus="Activo",
            estado="Activo",
            ingreso="Regular",
            descripcion_ingreso="Cambio de trayecto",
            fecha_ingreso=date(2026, 8, 15),
            trayecto=self.trayecto,
            estudiante=self.estudiante,
        )
        otro_nucleo = Nucleos.objects.create(
            municipio="Pedraza",
            direccion="Centro",
        )
        otro_usuario = Usuario.objects.create(
            nombres="Luis",
            apellidos="Gómez",
            genero="Masculino",
            cedula_identidad="V13572468",
            estado_civil="Soltero",
        )
        Estudiante.objects.create(
            usuario=otro_usuario,
            nucleo=otro_nucleo,
            pnf=self.pnf,
        )

        columnas, filas = _datos_matricula(self.usuario, "LISTADO")
        columnas_totales, filas_totales = _datos_matricula(self.usuario, "TOTAL")

        self.assertEqual(len(filas), 1)
        self.assertEqual(filas[0][1], "Pérez, Ana")
        self.assertEqual(filas_totales[0][-1], 1)
