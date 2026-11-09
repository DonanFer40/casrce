import json
from datetime import date, time

from django.test import RequestFactory, TestCase, override_settings
from django.contrib.sessions.backends.db import SessionStore
from django.urls import reverse

from inicio_sesion.models import (
    AulaAcademica,
    AulaEstudiante,
    CoordinadorPNF,
    Cuenta,
    DirectorGeneral,
    EstatusEstudiante,
    Estudiante,
    HorarioAcademico,
    Materia,
    MateriaAsignada,
    Nucleos,
    PeriodoAcademico,
    PeriodoAcademicoMateria,
    Pnf,
    SeccionAcademica,
    TrayectoAcademico,
    Usuario,
)
from gestion_institucional.views.seccion import (
    guardar_act_sec,
    obtener_siguiente_nombre_seccion,
    reg_sec,
)


class AsignacionAutomaticaSeccionesTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def crear_seccion(self, nombre):
        return SeccionAcademica.objects.create(
            nombre=nombre,
            turno="Diurno",
        )

    def crear_sesion(self, request):
        request.session = SessionStore()
        request.session["usuario_nombre"] = "Prueba"

    def test_asigna_la_primera_letra_libre_y_no_usa_el_valor_recibido(self):
        self.crear_seccion("A")
        self.crear_seccion("C")
        request = self.factory.post(
            "/reg_sec/",
            {"registro_seccion": "Z", "registro_turno": "Diurno"},
        )
        self.crear_sesion(request)

        response = reg_sec(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content)["seccion"], "B")
        self.assertTrue(
            SeccionAcademica.objects.filter(nombre="B").exists()
        )

    def test_modificar_asigna_primera_letra_libre_incluyendo_la_seleccionada(self):
        secciones = [self.crear_seccion(letra) for letra in "ABCD"]
        request = self.factory.post(
            "/guardar_act_sec/",
            {
                "seccion": str(secciones[0].pk),
                "actualizar_seccion": "A",
                "actualizar_turno": "Nocturno",
            },
        )
        self.crear_sesion(request)

        response = guardar_act_sec(request)
        secciones[0].refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(secciones[0].nombre, "E")
        self.assertEqual(secciones[0].turno, "Nocturno")

    def test_no_asigna_si_todas_las_letras_estan_ocupadas(self):
        for letra in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            self.crear_seccion(letra)

        self.assertIsNone(obtener_siguiente_nombre_seccion())


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
class HorarioAcademicoTests(TestCase):
    def setUp(self):
        self.nucleo = Nucleos.objects.create(
            municipio="Barinas",
            direccion="Sede central",
        )
        self.pnf = Pnf.objects.create(
            pnf="Informática",
            codigo="INF",
        )
        self.seccion = SeccionAcademica.objects.create(
            nombre="A",
            turno="Diurno",
        )
        self.aula = AulaAcademica.objects.create(
            nombre_aula="Aula 33",
            Nota="Aula de prueba",
            piso_edificio="1",
            tipo_aula="Regular",
            id_seccion=self.seccion,
            id_pnf=self.pnf,
            id_nucleo=self.nucleo,
        )
        self.trayecto = TrayectoAcademico.objects.create(nombre="Trayecto 4")
        self.periodo = PeriodoAcademico.objects.create(nombre="T4T3")
        self.materia = Materia.objects.create(
            nombre="Auditoría Informática",
            codigo="AI4",
            recuperacion="Sí",
            htea=2,
            htei=2,
            id_trayecto=self.trayecto,
            id_pnf=self.pnf,
        )
        self.asignacion = MateriaAsignada.objects.create(materia=self.materia)
        PeriodoAcademicoMateria.objects.create(
            materia=self.materia,
            periodo=self.periodo,
        )

    def crear_cuenta(self, nombres, rol):
        usuario = Usuario.objects.create(
            nombres=nombres,
            apellidos="Prueba",
            cedula_identidad=f"{nombres}001",
        )
        cuenta = Cuenta.objects.create(
            id_usuario=usuario,
            usuario=f"{nombres.lower()}_test",
            clave="no-se-usa",
            tipo_cuenta="EST" if rol == "Estudiante" else "ADMIN",
        )
        session = self.client.session
        session["id_cuenta"] = cuenta.pk
        session["usuario_nombre"] = f"{nombres} Prueba"
        session["registro_completado"] = True
        session["rol"] = [rol]
        session.save()
        return usuario

    def test_solo_coordinador_puede_abrir_gestion_y_ve_siete_franjas(self):
        usuario = self.crear_cuenta("Coordinador", "Coordinador PNF")
        CoordinadorPNF.objects.create(
            usuario=usuario,
            nucleo=self.nucleo,
            pnf=self.pnf,
        )

        respuesta = self.client.get(reverse("registrar_horario"))

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.content.count(b"data-franja="), 35)
        self.assertContains(respuesta, "8:00 - 8:45")
        self.assertContains(respuesta, "1:00 - 1:45")

    def test_estudiante_solo_ve_el_horario_de_su_matricula_vigente(self):
        usuario = self.crear_cuenta("Estudiante", "Estudiante")
        estudiante = Estudiante.objects.create(
            usuario=usuario,
            nucleo=self.nucleo,
            pnf=self.pnf,
        )
        estatus = EstatusEstudiante.objects.create(
            estatus="Activo",
            estado="Activo",
            ingreso="Regular",
            descripcion_ingreso="Nuevo ingreso",
            fecha_ingreso=date.today(),
            trayecto=self.trayecto,
            estudiante=estudiante,
        )
        AulaEstudiante.objects.create(
            aula=self.aula,
            estatus=estatus,
            fecha_inicio=date.today(),
            estado="Curso",
        )
        HorarioAcademico.objects.create(
            trayecto=self.trayecto,
            periodo=self.periodo,
            aula=self.aula,
            materia_asignada=self.asignacion,
            dia_semana="MIERCOLES",
            hora_inicio=time(8, 0),
            hora_final=time(8, 45),
            registrado_por=usuario,
        )

        respuesta = self.client.get(reverse("horario_estudiante"))

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Auditoría Informática")
        self.assertContains(respuesta, "Barinas")
        self.assertContains(respuesta, "Trayecto 4")

    def test_estudiante_accede_a_sus_reportes_personales(self):
        usuario = self.crear_cuenta("Estudiante", "Estudiante")
        Estudiante.objects.create(
            usuario=usuario,
            nucleo=self.nucleo,
            pnf=self.pnf,
        )

        respuesta = self.client.get(reverse("reportes_control_estudio"))

        self.assertEqual(respuesta.status_code, 200)
        self.assertTrue(respuesta.context["es_estudiante"])
        self.assertContains(respuesta, "Récord Académico")
        self.assertContains(respuesta, "Constancia de Estudios")


class GestionPNFTests(TestCase):
    def setUp(self):
        self.nucleo = Nucleos.objects.create(
            municipio="Barinas",
            direccion="Sede central",
        )
        usuario = Usuario.objects.create(
            nombres="Director",
            apellidos="Prueba",
            cedula_identidad="V-100",
        )
        cuenta = Cuenta.objects.create(
            id_usuario=usuario,
            usuario="director_test",
            clave="no-se-usa",
            tipo_cuenta="ADMIN",
        )
        DirectorGeneral.objects.create(usuario=usuario, nucleo=self.nucleo)
        session = self.client.session
        session["id_cuenta"] = cuenta.pk
        session["cedula_usuario"] = usuario.cedula_identidad
        session["usuario_nombre"] = "Director Prueba"
        session.save()

    def test_registro_rechaza_periodo_invalido(self):
        respuesta = self.client.post(
            reverse("reg_pnf"),
            {
                "nombrepnf": "Informática",
                "codigopnf": "INF",
                "periodoacademico": "Anual",
            },
        )

        self.assertEqual(respuesta.status_code, 400)
        self.assertFalse(Pnf.objects.filter(codigo="INF").exists())

    def test_registro_rechaza_nombre_duplicado_sin_importar_mayusculas(self):
        Pnf.objects.create(
            pnf="Programa de prueba",
            codigo="TEST-PNF-DUP",
            periodo_academico="Trimestre",
        )

        respuesta = self.client.post(
            reverse("reg_pnf"),
            {
                "nombrepnf": "PROGRAMA DE PRUEBA",
                "codigopnf": "TEST-PNF-DUP-2",
                "periodoacademico": "Semestre",
            },
        )

        self.assertEqual(respuesta.status_code, 409)
        self.assertEqual(
            Pnf.objects.filter(pnf__iexact="Programa de prueba").count(),
            1,
        )
