# -*- coding: utf-8 -*-
"""
Comando de carga sintética para CASRCE.

USO:
    python manage.py seed_carsce --dry-run
    python manage.py seed_carsce --confirmar

La simulación es el comportamiento predeterminado: ejecuta las operaciones
dentro de una transacción y luego revierte todos los cambios.

IMPORTANTE:
- No actualiza registros existentes.
- Solo crea registros faltantes.
- No crea documentos falsos, códigos de verificación ni credenciales TOTP.
- Las cuentas de personal usan tipo_cuenta="ADMIN" porque el modelo Cuenta
  actual solo contempla ADMIN y EST. Docente y CoordinadorPNF son perfiles
  académicos asociados a esas cuentas.
- No genera materias, planificaciones ni calificaciones. La relación
  DocenteAsignadoMateria está limitada por el modelo actual a un principal
  activo y un secundario por MateriaAsignada (globalmente, no por núcleo).
"""

from datetime import date, timedelta
import random

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.hashers import make_password
from django.db import transaction

from inicio_sesion.models import (
    Usuario,
    Cuenta,
    Residencia,
    Contacto,
    Nacimiento,
    Pnf,
    Nucleos,
    PNFNucleo,
    SeccionAcademica,
    AulaAcademica,
    TrayectoAcademico,
    PeriodoAcademico,
    CalendarioAcademico,
    CalendarioPeriodo,
    DatosPreofesion,
    Estudiante,
    EstatusEstudiante,
    AulaEstudiante,
    ExpedienteEstudiante,
    HistorialExpedienteEstudiante,
    InformacionSecundaria,
    ContactoAuxiliar,
    Docente,
    CoordinadorPNF,
    ControlEstudio,
    DirectorGeneral,
)

# ---------------------------------------------------------------------
# DATOS INSTITUCIONALES OFICIALES DEL PROYECTO
# ---------------------------------------------------------------------

NUCLEOS = [
    {"municipio": "Barinas", "direccion": "Dirección Barinas"},
    {"municipio": "Barinitas", "direccion": "Dirección Barinitas"},
    {"municipio": "Socopo", "direccion": "Dirección Socopó"},
    {"municipio": "Pedraza", "direccion": "Dirección Ciudad Bolivia"},
]

PNF = [
    {"pnf": "PNF en Sistema e Informática", "codigo": "CARRE001", "periodo_academico": "Trimestre"},
    {"pnf": "PNF en Electrónica", "codigo": "CARRE002", "periodo_academico": "Trimestre"},
    {"pnf": "PNF en Medicina Veterinaria", "codigo": "CARRE003", "periodo_academico": "Semestre"},
    {"pnf": "PNF en Nutrición y Dietética", "codigo": "CARRE004", "periodo_academico": "Trimestre"},
    {"pnf": "PNF en Electricidad", "codigo": "CARRE005", "periodo_academico": "Trimestre"},
    {"pnf": "PNF en Mecánica", "codigo": "CARRE006", "periodo_academico": "Trimestre"},
    {"pnf": "PNF en Agroalimentación", "codigo": "CARRE007", "periodo_academico": "Trimestre"},
    {"pnf": "PNF en Construcción Civil", "codigo": "CARRE008", "periodo_academico": "Trimestre"},
    {"pnf": "PNF en Ingeniería Industrial", "codigo": "CARRE009", "periodo_academico": "Trimestre"},
]

PNF_POR_NUCLEO = {
    "Barinas": ["CARRE001", "CARRE002", "CARRE003", "CARRE004"],
    "Barinitas": ["CARRE009", "CARRE005", "CARRE006", "CARRE007", "CARRE008", "CARRE001", "CARRE003"],
    "Socopo": ["CARRE008", "CARRE005", "CARRE007", "CARRE001", "CARRE003"],
    "Pedraza": ["CARRE007", "CARRE003"],
}

TRAYECTOS = [
    "Trayecto Inicial",
    "Trayecto I",
    "Trayecto II",
    "Trayecto III",
    "Trayecto IV",
    "Trayecto V",
]

PERIODOS = [
    "Inicial Trimestre",
    "Inicial Semestre",
    "Reparación",
    "Tramo I",
    "Tramo II",
    "Tramo III",
    "Semestre I",
    "Semestre II",
]

NOMBRES = [
    "Alejandro", "Andrea", "Andrés", "Ángel", "Camila", "Carlos",
    "Daniel", "Daniela", "David", "Diego", "Elena", "Fernando",
    "Gabriela", "Isabel", "Javier", "José", "Laura", "Luis",
    "María", "Mariana", "Miguel", "Natalia", "Pedro", "Rafael",
    "Samuel", "Valentina", "Victoria", "William", "Yuliana", "Zuleima",
]
APELLIDOS = [
    "Acosta", "Aguilar", "Aguirre", "Alvarado", "Álvarez", "Arias",
    "Barrios", "Blanco", "Bravo", "Cabrera", "Castillo", "Contreras",
    "Díaz", "Domínguez", "Escalona", "Fernández", "Flores", "García",
    "Gómez", "González", "Gutiérrez", "Hernández", "Jiménez", "López",
    "Martínez", "Mendoza", "Morales", "Pérez", "Ramírez", "Rivas",
    "Rodríguez", "Rojas", "Sánchez", "Suárez", "Torres", "Vargas",
]

PARROQUIAS = [
    "Barinas", "Alto Barinas", "El Carmen", "Corazón de Jesús",
    "Barinitas", "Altamira", "Socopó", "Ciudad Bolivia",
]

PASSWORD_PRUEBA = "CASRCE-Prueba-2026!"

class SimulacionRevertida(Exception):
    """Señal interna para revertir la transacción de simulación."""


class Command(BaseCommand):
    help = "Genera cuentas y registros sintéticos de prueba para CASRCE."

    def add_arguments(self, parser):
        parser.add_argument(
            "--confirmar",
            action="store_true",
            help="Confirma y guarda la carga. Sin esta opción solo simula.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Ejecuta una simulación y revierte todos los cambios (predeterminado).",
        )

    def handle(self, *args, **options):
        confirmar = options["confirmar"]
        if confirmar and options["dry_run"]:
            raise CommandError("No combines --confirmar con --dry-run.")

        self.rng = random.Random(20261108)
        self.contadores = {}
        self.password_hash = make_password(PASSWORD_PRUEBA)

        modo = "CARGA REAL" if confirmar else "SIMULACIÓN (sin guardar)"
        self.stdout.write("\n" + "=" * 68)
        self.stdout.write(self.style.MIGRATE_HEADING(f"CASRCE — {modo}"))
        self.stdout.write("=" * 68)

        try:
            with transaction.atomic():
                self.crear_catalogos()
                estructura = self.obtener_estructura()
                personal = self.crear_personal(estructura)
                self.crear_estudiantes(estructura, personal)

                self.stdout.write("\nRESUMEN DE OPERACIONES:")
                for nombre, cantidad in sorted(self.contadores.items()):
                    self.stdout.write(f"  {nombre}: {cantidad}")

                if not confirmar:
                    raise SimulacionRevertida()

        except SimulacionRevertida:
            self.stdout.write(self.style.WARNING(
                "\nSimulación terminada: la transacción fue revertida. "
                "La base de datos no conserva ningún registro de esta ejecución."
            ))
            self.stdout.write(
                "Si el resumen es correcto, ejecuta nuevamente con --confirmar."
            )
            return

        self.stdout.write(self.style.SUCCESS(
            "\nCarga confirmada correctamente. Los registros existentes no fueron modificados."
        ))
        self.stdout.write(
            f"Contraseña temporal común de las cuentas sintéticas: {PASSWORD_PRUEBA}"
        )
        self.stdout.write(self.style.WARNING(
            "Estas son cuentas de prueba. Cámbialas o elimínalas antes de habilitar "
            "el uso institucional real."
        ))

    # -----------------------------------------------------------------
    # UTILIDADES
    # -----------------------------------------------------------------

    def sumar(self, etiqueta, creado):
        if creado:
            self.contadores[etiqueta] = self.contadores.get(etiqueta, 0) + 1

    def obtener_o_crear(self, modelo, etiqueta, criterios, defaults=None):
        objeto, creado = modelo.objects.get_or_create(
            **criterios,
            defaults=defaults or {},
        )
        self.sumar(etiqueta, creado)
        return objeto

    def crear_usuario_cuenta(self, username, cedula, nombres, apellidos, tipo_cuenta):
        usuario = Usuario.objects.filter(cedula_identidad=cedula).first()
        if usuario is None:
            usuario = Usuario.objects.create(
                nombres=nombres,
                apellidos=apellidos,
                genero=self.rng.choice(["Femenino", "Masculino"]),
                cedula_identidad=cedula,
                estado_civil=self.rng.choice(["Soltero", "Casado"]),
            )
            self.sumar("Usuarios", True)
        else:
            self.sumar("Usuarios existentes", False)

        cuenta = Cuenta.objects.filter(usuario=username).first()
        if cuenta is None:
            Cuenta.objects.create(
                id_usuario=usuario,
                usuario=username,
                clave=self.password_hash,
                tipo_cuenta=tipo_cuenta,
            )
            self.sumar("Cuentas", True)
        elif cuenta.id_usuario_id != usuario.id_usuario:
            raise CommandError(
                f"El usuario de acceso '{username}' ya pertenece a otra persona. "
                "Se detuvo la carga para no alterar datos."
            )
        else:
            self.sumar("Cuentas existentes", False)

        self.crear_datos_personales(usuario, username)
        return usuario

    def crear_datos_personales(self, usuario, username):
        indice = sum(ord(c) for c in username) % len(PARROQUIAS)
        municipio = self.rng.choice(["Barinas", "Barinitas", "Socopo", "Pedraza"])

        self.obtener_o_crear(
            Residencia,
            "Residencias",
            {"id_usuario": usuario},
            {
                "condicion_residencia": "Familiar",
                "municipio": municipio,
                "parroquia": PARROQUIAS[indice],
                "direccion_residencia": f"Dirección sintética de prueba, sector {indice + 1}",
            },
        )

        correo = f"{username}@casrce.test"
        self.obtener_o_crear(
            Contacto,
            "Contactos",
            {"id_usuario": usuario},
            {
                "telefono_suplete": None,
                "telefono_personal": f"+584120{(sum(ord(c) for c in username) % 900000) + 100000:06d}",
                "correo_electronico": correo,
                "correo_alternativo": None,
            },
        )

        fecha_nacimiento = date(
            self.rng.randint(1980, 2007),
            self.rng.randint(1, 12),
            self.rng.randint(1, 28),
        )
        self.obtener_o_crear(
            Nacimiento,
            "Nacimientos",
            {"id_usuario": usuario},
            {
                "pais": "Venezuela",
                "estado": "Barinas",
                "municipio": municipio,
                "parroquia": PARROQUIAS[indice],
                "direccion_nacimiento": "Centro asistencial (dato sintético)",
                "fecha_nacimiento": fecha_nacimiento,
            },
        )

    def crear_catalogos(self):
        self.stdout.write("\n1. Verificando catálogos institucionales...")

        for datos in NUCLEOS:
            self.obtener_o_crear(
                Nucleos,
                "Núcleos",
                {"municipio": datos["municipio"]},
                {"direccion": datos["direccion"]},
            )

        for datos in PNF:
            self.obtener_o_crear(
                Pnf,
                "PNF",
                {"codigo": datos["codigo"]},
                {
                    "pnf": datos["pnf"],
                    "periodo_academico": datos["periodo_academico"],
                },
            )

        for nombre in TRAYECTOS:
            self.obtener_o_crear(
                TrayectoAcademico,
                "Trayectos",
                {"nombre": nombre},
            )

        for nombre in PERIODOS:
            self.obtener_o_crear(
                PeriodoAcademico,
                "Períodos académicos",
                {"nombre": nombre},
            )

        nucleos = {n.municipio: n for n in Nucleos.objects.all()}
        pnfs = {p.codigo: p for p in Pnf.objects.all()}

        for municipio, codigos in PNF_POR_NUCLEO.items():
            nucleo = nucleos.get(municipio)
            if nucleo is None:
                raise CommandError(f"No existe el núcleo institucional: {municipio}")

            for codigo in codigos:
                pnf = pnfs.get(codigo)
                if pnf is None:
                    raise CommandError(f"No existe el PNF institucional: {codigo}")

                self.obtener_o_crear(
                    PNFNucleo,
                    "Relaciones PNF-núcleo",
                    {"id_nucleo": nucleo, "id_pnf": pnf},
                )

        # Un calendario sintético, vinculado a los períodos ya existentes.
        calendario = self.obtener_o_crear(
            CalendarioAcademico,
            "Calendarios",
            {"descripcion": "Calendario sintético de pruebas CASRCE 2026"},
            {
                "fecha_inicio": date(2026, 9, 1),
                "fecha_final": date(2026, 12, 15),
                "activo": True,
                "tipo": "PERIODO",
            },
        )

        periodos = {p.nombre: p for p in PeriodoAcademico.objects.all()}
        for nombre in ("Inicial Trimestre", "Inicial Semestre", "Tramo I", "Semestre I"):
            periodo = periodos.get(nombre)
            if periodo:
                self.obtener_o_crear(
                    CalendarioPeriodo,
                    "Vínculos calendario-período",
                    {"calendario": calendario, "periodo": periodo},
                )

    def obtener_estructura(self):
        nucleos = {n.municipio: n for n in Nucleos.objects.all()}
        pnfs = {p.codigo: p for p in Pnf.objects.all()}
        trayectos = {t.nombre: t for t in TrayectoAcademico.objects.all()}
        combinaciones = []

        for municipio, codigos in PNF_POR_NUCLEO.items():
            nucleo = nucleos[municipio]
            for codigo in codigos:
                combinaciones.append({
                    "nucleo": nucleo,
                    "pnf": pnfs[codigo],
                    "codigo": codigo,
                })

        if len(combinaciones) != 18:
            raise CommandError(
                f"Se esperaban 18 combinaciones PNF-núcleo y se encontraron {len(combinaciones)}."
            )

        return {
            "nucleos": nucleos,
            "pnfs": pnfs,
            "trayectos": trayectos,
            "combinaciones": combinaciones,
        }

    # -----------------------------------------------------------------
    # PERSONAL: 4 DG + 4 CONTROL + 18 COORDINADORES + 36 DOCENTES
    # -----------------------------------------------------------------

    def nombre_sintetico(self, numero):
        nombre = NOMBRES[numero % len(NOMBRES)]
        apellido1 = APELLIDOS[(numero * 3) % len(APELLIDOS)]
        apellido2 = APELLIDOS[(numero * 7 + 5) % len(APELLIDOS)]
        return nombre, f"{apellido1} {apellido2}"

    def crear_personal(self, estructura):
        self.stdout.write("\n2. Creando personal institucional y perfiles académicos...")

        resultado = {
            "directores": {},
            "controles": {},
            "coordinadores": {},
            "docentes": {},
        }
        contador = 1

        for municipio, nucleo in estructura["nucleos"].items():
            nombres, apellidos = self.nombre_sintetico(contador)
            usuario = self.crear_usuario_cuenta(
                f"dg_{municipio.lower()}",
                f"V-{22000000 + contador}",
                nombres,
                apellidos,
                "ADMIN",
            )
            self.obtener_o_crear(
                DirectorGeneral,
                "Directores Generales",
                {"usuario": usuario, "nucleo": nucleo},
            )
            resultado["directores"][municipio] = usuario
            contador += 1

        for municipio, nucleo in estructura["nucleos"].items():
            nombres, apellidos = self.nombre_sintetico(contador)
            usuario = self.crear_usuario_cuenta(
                f"control_{municipio.lower()}",
                f"V-{22000000 + contador}",
                nombres,
                apellidos,
                "ADMIN",
            )
            self.obtener_o_crear(
                ControlEstudio,
                "Perfiles Control de Estudio",
                {"usuario": usuario, "nucleo": nucleo},
            )
            resultado["controles"][municipio] = usuario
            contador += 1

        for indice, combo in enumerate(estructura["combinaciones"], start=1):
            nucleo = combo["nucleo"]
            pnf = combo["pnf"]
            username = f"coord_{combo['codigo'].lower()}_{nucleo.municipio.lower()}"
            nombres, apellidos = self.nombre_sintetico(contador)
            usuario = self.crear_usuario_cuenta(
                username,
                f"V-{22000000 + contador}",
                nombres,
                apellidos,
                "ADMIN",
            )
            self.obtener_o_crear(
                CoordinadorPNF,
                "Coordinadores PNF",
                {"usuario": usuario, "nucleo": nucleo, "pnf": pnf},
                {"activo": True},
            )
            resultado["coordinadores"][(nucleo.municipio, pnf.codigo)] = usuario
            contador += 1

        for combo in estructura["combinaciones"]:
            nucleo = combo["nucleo"]
            pnf = combo["pnf"]
            clave = (nucleo.municipio, pnf.codigo)
            resultado["docentes"][clave] = []

            for numero_docente in (1, 2):
                username = (
                    f"doc_{combo['codigo'].lower()}_"
                    f"{nucleo.municipio.lower()}_{numero_docente}"
                )
                nombres, apellidos = self.nombre_sintetico(contador)
                usuario = self.crear_usuario_cuenta(
                    username,
                    f"V-{22000000 + contador}",
                    nombres,
                    apellidos,
                    "ADMIN",
                )
                docente = self.obtener_o_crear(
                    Docente,
                    "Perfiles Docente",
                    {"usuario": usuario, "nucleo": nucleo, "pnf": pnf},
                    {"activo": True},
                )
                resultado["docentes"][clave].append(docente)
                contador += 1

        # Datos profesionales sintéticos para el personal.
        perfiles = list(resultado["directores"].values())
        perfiles += list(resultado["controles"].values())
        perfiles += list(resultado["coordinadores"].values())
        for docentes in resultado["docentes"].values():
            perfiles.extend([d.usuario for d in docentes])

        for usuario in perfiles:
            self.obtener_o_crear(
                DatosPreofesion,
                "Datos profesionales",
                {"id_usuario": usuario},
                {
                    "profesion_pregrado": "Profesional (dato sintético)",
                    "universidad_egreso_pregrado": "Institución de prueba",
                    "pais_profesion_pregrado": "Venezuela",
                },
            )

        return resultado

    # -----------------------------------------------------------------
    # ESTUDIANTES: 36 POR CADA UNA DE LAS 18 COMBINACIONES = 648
    # -----------------------------------------------------------------

    def crear_estudiantes(self, estructura, personal):
        self.stdout.write("\n3. Creando 648 estudiantes y sus registros asociados...")

        trayecto_inicial = estructura["trayectos"]["Trayecto Inicial"]
        numero_estudiante = 0
        extranjeros_restantes = 65
        grupos_restantes = len(estructura["combinaciones"])

        for combo_indice, combo in enumerate(estructura["combinaciones"]):
            nucleo = combo["nucleo"]
            pnf = combo["pnf"]
            clave_combo = (nucleo.municipio, pnf.codigo)

            control = personal["controles"][nucleo.municipio]
            coordinador = personal["coordinadores"][clave_combo]

            codigo_seccion = f"S{combo_indice + 1:02d}"
            seccion = self.obtener_o_crear(
                SeccionAcademica,
                "Secciones académicas",
                {"nombre": codigo_seccion, "turno": "Mañana"},
            )
            aula = self.obtener_o_crear(
                AulaAcademica,
                "Aulas académicas",
                {
                    "nombre_aula": f"Aula de prueba {nucleo.municipio} {pnf.codigo}",
                    "id_seccion": seccion,
                    "id_pnf": pnf,
                    "id_nucleo": nucleo,
                },
                {
                    "Nota": "Aula creada exclusivamente para pruebas sintéticas de CASRCE.",
                    "piso_edificio": "Planta baja",
                    "tipo_aula": "Aula de clases",
                },
            )

            # 65 extranjeros distribuidos como 4 en 11 combinaciones y 3 en 7.
            extranjeros_grupo = 4 if combo_indice < 11 else 3
            grupos_restantes -= 1

            for posicion in range(1, 37):
                numero_estudiante += 1
                es_extranjero = posicion <= extranjeros_grupo
                prefijo = "E-" if es_extranjero else "V-"
                cedula = f"{prefijo}{23000000 + numero_estudiante}"

                nombres, apellidos = self.nombre_sintetico(100 + numero_estudiante)
                username = f"estudiante{numero_estudiante:04d}"

                usuario = self.crear_usuario_cuenta(
                    username,
                    cedula,
                    nombres,
                    apellidos,
                    "EST",
                )

                estudiante = self.obtener_o_crear(
                    Estudiante,
                    "Perfiles Estudiante",
                    {"usuario": usuario, "nucleo": nucleo, "pnf": pnf},
                )

                fecha_ingreso = date(2026, 9, 1)
                estatus = self.obtener_o_crear(
                    EstatusEstudiante,
                    "Estatus de estudiantes",
                    {"estudiante": estudiante, "trayecto": trayecto_inicial},
                    {
                        "estatus": "ACTIVO",
                        "estado": "INSCRITO",
                        "ingreso": "REGULAR",
                        "descripcion_ingreso": "PRUEBA SINTETICA",
                        "fecha_ingreso": fecha_ingreso,
                        "registrado_por": control,
                        "perfil_registro": "CONTROL_ESTUDIO",
                    },
                )

                self.obtener_o_crear(
                    AulaEstudiante,
                    "Asignaciones de aula",
                    {"aula": aula, "estatus": estatus},
                    {
                        "fecha_inicio": fecha_ingreso,
                        "fecha_final": None,
                        "estado": "Curso",
                    },
                )

                self.obtener_o_crear(
                    InformacionSecundaria,
                    "Datos de secundaria",
                    {"codigo_sni_opsu": f"OPSU-PRUEBA-{numero_estudiante:05d}"},
                    {
                        "tipo_institucion": "Pública",
                        "nombre_institucion": f"Institución educativa de prueba {combo_indice + 1}",
                        "fecha_grado": date(2025, 7, 15),
                        "id_usuario": usuario,
                    },
                )

                self.obtener_o_crear(
                    ContactoAuxiliar,
                    "Contactos auxiliares",
                    {
                        "id_usuario": usuario,
                        "cedula_identidad": f"V-{24000000 + numero_estudiante}",
                    },
                    {
                        "nombres": "Contacto",
                        "apellidos": f"Auxiliar de prueba {numero_estudiante:04d}",
                        "telefono": f"+584120{(numero_estudiante % 900000) + 100000:06d}",
                        "parentesco": "Familiar",
                    },
                )

                estados = [
                    "PENDIENTE_REVISION",
                    "EN_REVISION",
                    "CON_OBSERVACIONES",
                    "VALIDADO_ADMINISTRATIVAMENTE",
                    "INSCRIPCION_APROBADA",
                ]
                estado = estados[(numero_estudiante - 1) % len(estados)]
                defaults_expediente = {
                    "estado": estado,
                    "nota_gemini": "",
                    "resultados_gemini": {},
                    "observacion_actual": (
                        "Registro sintético para pruebas. No representa una evaluación real."
                        if estado == "CON_OBSERVACIONES" else ""
                    ),
                }
                if estado == "INSCRIPCION_APROBADA":
                    defaults_expediente.update({
                        "aprobado_por": coordinador,
                        "fecha_aprobacion": date(2026, 9, 2),
                        "perfil_aprobacion": "COORDINADOR_PNF",
                    })

                expediente = self.obtener_o_crear(
                    ExpedienteEstudiante,
                    "Expedientes estudiantiles",
                    {"usuario": usuario},
                    defaults_expediente,
                )

                # Se crea un único evento inicial por expediente; no se inventa
                # una evaluación de Gemini ni se adjuntan archivos inexistentes.
                if not expediente.historial.exists():
                    HistorialExpedienteEstudiante.objects.create(
                        expediente=expediente,
                        estado_anterior="",
                        estado_nuevo=expediente.estado,
                        accion="CREACION",
                        observacion="Registro sintético generado para pruebas de CASRCE.",
                        realizado_por=(
                            coordinador
                            if expediente.estado == "INSCRIPCION_APROBADA"
                            else control
                        ),
                        perfil=(
                            "COORDINADOR_PNF"
                            if expediente.estado == "INSCRIPCION_APROBADA"
                            else "CONTROL_ESTUDIO"
                        ),
                    )
                    self.sumar("Historiales de expedientes", True)

        if numero_estudiante != 648:
            raise CommandError(
                f"Se esperaban 648 estudiantes y se procesaron {numero_estudiante}."
            )

        self.stdout.write(
            f"  Estudiantes procesados: {numero_estudiante} "
            "(583 venezolanos y 65 extranjeros por prefijo de cédula)."
        )
