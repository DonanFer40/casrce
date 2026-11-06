from django.test import TestCase
from django.urls import reverse

from inicio_sesion.models import (
    CoordinadorPNF,
    ControlEstudio,
    Estudiante,
    ExpedienteEstudiante,
    HistorialExpedienteEstudiante,
    Nucleos,
    Pnf,
    Usuario,
)


class ExpedientesEstudiantilesTests(TestCase):
    def setUp(self):
        self.nucleo = Nucleos.objects.create(
            municipio="Barinas",
            direccion="Sede Barinas",
        )
        self.otro_nucleo = Nucleos.objects.create(
            municipio="Barinitas",
            direccion="Sede Barinitas",
        )
        self.pnf_asignado = Pnf.objects.create(
            pnf="Sistemas e Informática",
            codigo="PNF-SI",
        )
        self.otro_pnf = Pnf.objects.create(
            pnf="Electricidad",
            codigo="PNF-EL",
        )
        self.funcionario = Usuario.objects.create(
            nombres="Coordinador",
            apellidos="Prueba",
            cedula_identidad="V-10000001",
        )
        self.estudiante_usuario = Usuario.objects.create(
            nombres="Estudiante",
            apellidos="Prueba",
            cedula_identidad="V-20000001",
        )
        self.estudiante = Estudiante.objects.create(
            usuario=self.estudiante_usuario,
            nucleo=self.nucleo,
            pnf=self.pnf_asignado,
        )
        self.expediente = ExpedienteEstudiante.objects.create(
            usuario=self.estudiante_usuario,
        )
        CoordinadorPNF.objects.create(
            usuario=self.funcionario,
            nucleo=self.nucleo,
            pnf=self.pnf_asignado,
            activo=True,
        )
        session = self.client.session
        session["cedula_usuario"] = self.funcionario.cedula_identidad
        session.save()

    def test_coordinator_can_open_expediente_in_assigned_pnf(self):
        response = self.client.get(
            reverse("detalle_expediente", args=[self.expediente.id_expediente])
        )
        self.assertEqual(response.status_code, 200)

    def test_coordinator_cannot_access_other_pnf_in_same_nucleus(self):
        otro_usuario = Usuario.objects.create(
            nombres="Otro",
            apellidos="Estudiante",
            cedula_identidad="V-20000002",
        )
        Estudiante.objects.create(
            usuario=otro_usuario,
            nucleo=self.nucleo,
            pnf=self.otro_pnf,
        )
        otro_expediente = ExpedienteEstudiante.objects.create(usuario=otro_usuario)
        response = self.client.get(
            reverse("detalle_expediente", args=[otro_expediente.id_expediente])
        )
        self.assertEqual(response.status_code, 404)

    def test_coordinator_can_approve_after_administrative_validation(self):
        url = reverse(
            "actualizar_estado_expediente",
            args=[self.expediente.id_expediente],
        )
        self.client.post(url, {"estado": "EN_REVISION"})
        self.client.post(url, {"estado": "VALIDADO_ADMINISTRATIVAMENTE"})
        self.client.post(url, {"estado": "INSCRIPCION_APROBADA"})

        self.expediente.refresh_from_db()
        self.assertEqual(self.expediente.estado, "INSCRIPCION_APROBADA")
        self.assertEqual(self.expediente.aprobado_por, self.funcionario)
        self.assertEqual(self.expediente.perfil_aprobacion, "COORDINADOR_PNF")
        self.assertEqual(
            HistorialExpedienteEstudiante.objects.filter(
                expediente=self.expediente
            ).count(),
            3,
        )

    def test_approval_cannot_skip_review_and_validation(self):
        response = self.client.post(
            reverse(
                "actualizar_estado_expediente",
                args=[self.expediente.id_expediente],
            ),
            {"estado": "INSCRIPCION_APROBADA"},
        )
        self.assertEqual(response.status_code, 302)
        self.expediente.refresh_from_db()
        self.assertEqual(self.expediente.estado, "PENDIENTE_REVISION")
    def test_control_estudio_can_approve_within_assigned_nucleus(self):
        control = Usuario.objects.create(
            nombres="Control",
            apellidos="Prueba",
            cedula_identidad="V-10000002",
        )
        ControlEstudio.objects.create(
            usuario=control,
            nucleo=self.nucleo,
            activo=True,
        )
        session = self.client.session
        session["cedula_usuario"] = control.cedula_identidad
        session.save()

        url = reverse(
            "actualizar_estado_expediente",
            args=[self.expediente.id_expediente],
        )
        self.client.post(url, {"estado": "EN_REVISION"})
        self.client.post(url, {"estado": "VALIDADO_ADMINISTRATIVAMENTE"})
        self.client.post(url, {"estado": "INSCRIPCION_APROBADA"})

        self.expediente.refresh_from_db()
        self.assertEqual(self.expediente.estado, "INSCRIPCION_APROBADA")
        self.assertEqual(self.expediente.aprobado_por, control)
        self.assertEqual(self.expediente.perfil_aprobacion, "CONTROL_ESTUDIO")

