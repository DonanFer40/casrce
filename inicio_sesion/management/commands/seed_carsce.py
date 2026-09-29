from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth.hashers import make_password
from django.utils import timezone

from inicio_sesion.models import (
    Usuario,
    Cuenta,
    Nucleos,
    Pnf,
    Contacto,
    Nacimiento,
    PNFNucleo,
    Residencia,
    SeccionAcademica,
    AulaAcademica,
    TrayectoAcademico,
    PeriodoAcademico,
    CalendarioAcademico,
    CalendarioPeriodo,
    Materia,
    PeriodoAcademicoMateria,
    DatosPreofesion,
    Estudiante,
    EstatusEstudiante,
    AulaEstudiante,
    DocumentosEstudiante,
    InformacionSecundaria,
    ContactoAuxiliar,
    Discapacidad,
    Docente,
    MateriaAsignada,
    DocenteAsignadoMateria,
    CoordinadorPNF,
    ControlEstudio,
    DirectorGeneral,
    Autoridades,
    Bitacora,
    VerificacionCodigo,
    HistorialAsignaciones,
)

from notas_academicas.models import (
    PlanificacionAcademica,
    DetallePlanificacion,
    DetalleEvaluacion,
    PromedioFinal,
    EvaluacionReparacion,
    DetalleEvaluacionReparacion,
    Reparacion,
    ModificacionReparacion,
    DetalleModificacionReparacion,
    Calificaciones,
    DetalleCalificacionesUnidad,
    HistorialModificacionNotas,
    HistorialDetalleNota,
    HistorialTrayectoEstudiante,
)


class Command(BaseCommand):

    help = "Carga datos completos de prueba para CARSCE."

    def handle(self, *args, **options):

        self.stdout.write(
            self.style.WARNING(
                "\n============================================\n"
                "       CARGANDO DATOS DE PRUEBA CARSCE\n"
                "============================================\n"
            )
        )

        with transaction.atomic():

            # Estructura académica
            self.crear_calendarios()
            self.crear_materias()
            self.crear_secciones()
            self.crear_aulas()

            # Usuarios y roles
            self.crear_usuarios_base()
            self.crear_roles()
            self.crear_docentes_adicionales()

            # Estudiantes
            self.crear_estudiantes()
            self.crear_datos_personales()
            self.crear_inscripciones()

            # Docencia
            self.crear_materias_asignadas()
            self.crear_docentes_asignados()

            # Gestión académica
            self.crear_planificaciones()
            self.crear_calificaciones()
            self.crear_promedios()

            # Casos especiales
            self.crear_reparaciones()
            self.crear_historiales()

            # Sistema
            self.crear_autoridades()
            self.crear_bitacora()
            self.crear_verificaciones()

        self.stdout.write(
            self.style.SUCCESS(
                "\n============================================\n"
                "        SEED CARSCE COMPLETADO\n"
                "============================================\n"
            )
        )

    # ============================================================
    # CALENDARIO
    # ============================================================

    def crear_calendarios(self):

        calendario, _ = CalendarioAcademico.objects.get_or_create(
            descripcion="Calendario Académico 2026-I",
            defaults={
                "fecha_inicio": date(2026, 1, 15),
                "fecha_final": date(2026, 7, 31),
                "activo": True,
                "tipo": "PERIODO",
            },
        )

        periodo = PeriodoAcademico.objects.filter(
            nombre="Semestre I"
        ).first()

        if periodo:

            CalendarioPeriodo.objects.get_or_create(
                periodo=periodo,
                calendario=calendario,
            )

        self.stdout.write("✓ Calendario académico")

    # ============================================================
    # MATERIAS
    # ============================================================

    def crear_materias(self):

        trayecto = TrayectoAcademico.objects.filter(
            nombre="Trayecto I"
        ).first()

        if not trayecto:
            trayecto = TrayectoAcademico.objects.first()

        periodo = PeriodoAcademico.objects.filter(
            nombre="Semestre I"
        ).first()

        if not periodo:
            periodo = PeriodoAcademico.objects.first()

        materias_por_codigo = {

            "CARRE001": [
                "Programación",
                "Base de Datos",
                "Sistemas Operativos",
                "Redes de Computadoras",
                "Ingeniería de Software",
                "Matemática I",
            ],

            "CARRE002": [
                "Circuitos Eléctricos",
                "Electrónica Analógica",
                "Electrónica Digital",
                "Instrumentación",
                "Microcontroladores",
                "Matemática I",
            ],

            "CARRE003": [
                "Anatomía Animal",
                "Fisiología Animal",
                "Bioquímica",
                "Microbiología",
                "Zoología",
                "Matemática I",
            ],

            "CARRE004": [
                "Circuitos Eléctricos",
                "Máquinas Eléctricas",
                "Instalaciones Eléctricas",
                "Electrotecnia",
                "Sistemas de Potencia",
                "Matemática I",
            ],

            "CARRE005": [
                "Mecánica I",
                "Dibujo Técnico",
                "Resistencia de Materiales",
                "Termodinámica",
                "Materiales Industriales",
                "Matemática I",
            ],

            "CARRE006": [
                "Agroecología",
                "Producción Vegetal",
                "Producción Animal",
                "Suelos",
                "Riego y Drenaje",
                "Matemática I",
            ],

            "CARRE007": [
                "Dibujo Técnico",
                "Topografía",
                "Materiales de Construcción",
                "Resistencia de Materiales",
                "Construcción I",
                "Matemática I",
            ],

            "CARRE008": [
                "Procesos Industriales",
                "Control de Calidad",
                "Seguridad Industrial",
                "Gestión de Procesos",
                "Mantenimiento Industrial",
                "Matemática I",
            ],

            "CARRE009": [
                "Fundamentos de Ingeniería",
                "Procesos Industriales",
                "Gestión de Calidad",
                "Seguridad Industrial",
                "Mantenimiento Industrial",
                "Matemática I",
            ],
        }

        for pnf in Pnf.objects.all():

            nombres = materias_por_codigo.get(
                pnf.codigo,
                [
                    "Unidad Curricular I",
                    "Unidad Curricular II",
                    "Unidad Curricular III",
                    "Unidad Curricular IV",
                    "Unidad Curricular V",
                ],
            )

            for numero, nombre in enumerate(
                nombres,
                start=1,
            ):

                materia, _ = Materia.objects.update_or_create(
                    codigo=f"{pnf.codigo}-{numero:02d}",
                    defaults={
                        "nombre": nombre,
                        "recuperacion": "Sí",
                        "htea": 3.0,
                        "htei": 2.0,
                        "activa": True,
                        "tipo_materia": "Curso",
                        "id_trayecto": trayecto,
                        "id_pnf": pnf,
                        "fecha_registro": timezone.now(),
                        "perfil_registro": "SEED",
                    },
                )

                PeriodoAcademicoMateria.objects.get_or_create(
                    materia=materia,
                    periodo=periodo,
                )

        self.stdout.write("✓ Materias")

    # ============================================================
    # SECCIONES
    # ============================================================

    def crear_secciones(self):

        for nombre, turno in [
            ("A", "Diurno"),
            ("B", "Diurno"),
            ("C", "Nocturno"),
        ]:

            SeccionAcademica.objects.get_or_create(
                nombre=nombre,
                turno=turno,
            )

        self.stdout.write("✓ Secciones")

    # ============================================================
    # AULAS
    # ============================================================

    def crear_aulas(self):

        secciones = list(
            SeccionAcademica.objects.all()
        )

        if not secciones:
            return

        seccion = secciones[0]

        relaciones = PNFNucleo.objects.select_related(
            "id_nucleo",
            "id_pnf",
        )

        for relacion in relaciones:

            nucleo = relacion.id_nucleo
            pnf = relacion.id_pnf

            AulaAcademica.objects.get_or_create(
                nombre_aula=(
                    f"Aula {pnf.codigo} - "
                    f"{nucleo.municipio}"
                ),
                id_nucleo=nucleo,
                id_pnf=pnf,
                defaults={
                    "Nota": "Aula académica de prueba",
                    "piso_edificio": "Planta baja",
                    "tipo_aula": "Aula convencional",
                    "id_seccion": seccion,
                },
            )

        self.stdout.write("✓ Aulas")

    # ============================================================
    # USUARIOS ADMINISTRATIVOS
    # ============================================================

    def crear_usuarios_base(self):

        usuarios = [
            (
                "Carlos",
                "Rodríguez",
                "10000001",
                "director.general",
            ),
            (
                "María",
                "González",
                "10000002",
                "control.estudio",
            ),
            (
                "Luis",
                "Hernández",
                "10000003",
                "coordinador.pnf",
            ),
            (
                "Ana",
                "Martínez",
                "10000004",
                "docente.sistemas",
            ),
        ]

        for nombres, apellidos, cedula, username in usuarios:

            usuario, _ = Usuario.objects.update_or_create(
                cedula_identidad=cedula,
                defaults={
                    "nombres": nombres,
                    "apellidos": apellidos,
                    "genero": "No especificado",
                    "estado_civil": "Soltero(a)",
                },
            )

            Cuenta.objects.update_or_create(
                usuario=username,
                defaults={
                    "id_usuario": usuario,
                    "clave": make_password("12345678"),
                    "tipo_cuenta": "ADMIN",
                },
            )

        self.stdout.write("✓ Usuarios administrativos")

    # ============================================================
    # ROLES
    # ============================================================

    def crear_roles(self):

        barinas = Nucleos.objects.filter(
            municipio="Barinas"
        ).first()

        if not barinas:
            return

        pnf = Pnf.objects.first()

        director = Usuario.objects.get(
            cedula_identidad="10000001"
        )

        control = Usuario.objects.get(
            cedula_identidad="10000002"
        )

        coordinador = Usuario.objects.get(
            cedula_identidad="10000003"
        )

        docente = Usuario.objects.get(
            cedula_identidad="10000004"
        )

        DirectorGeneral.objects.get_or_create(
            usuario=director,
            nucleo=barinas,
        )

        ControlEstudio.objects.get_or_create(
            usuario=control,
            nucleo=barinas,
        )

        if pnf:

            CoordinadorPNF.objects.get_or_create(
                usuario=coordinador,
                nucleo=barinas,
                pnf=pnf,
                defaults={
                    "activo": True,
                },
            )

            Docente.objects.get_or_create(
                usuario=docente,
                nucleo=barinas,
                pnf=pnf,
                defaults={
                    "activo": True,
                },
            )

        self.stdout.write("✓ Roles")

    # ============================================================
    # DOCENTES ADICIONALES
    # ============================================================

    def crear_docentes_adicionales(self):

        barinas = Nucleos.objects.filter(
            municipio="Barinas"
        ).first()

        if not barinas:
            return

        docentes = [
            (
                "Pedro",
                "Mendoza",
                "30000001",
                "docente.electronica",
                "CARRE002",
            ),
            (
                "Laura",
                "Rojas",
                "30000002",
                "docente.veterinaria",
                "CARRE003",
            ),
            (
                "Miguel",
                "Díaz",
                "30000003",
                "docente.electricidad",
                "CARRE004",
            ),
            (
                "Sofía",
                "Torres",
                "30000004",
                "docente.mecanica",
                "CARRE005",
            ),
            (
                "Roberto",
                "Silva",
                "30000005",
                "docente.agro",
                "CARRE006",
            ),
            (
                "Elena",
                "Vargas",
                "30000006",
                "docente.industrial",
                "CARRE008",
            ),
        ]

        for nombres, apellidos, cedula, username, codigo in docentes:

            pnf = Pnf.objects.filter(
                codigo=codigo
            ).first()

            if not pnf:
                continue

            # Solo crear el docente si ese PNF existe
            # en el núcleo de Barinas.
            if not PNFNucleo.objects.filter(
                id_nucleo=barinas,
                id_pnf=pnf,
            ).exists():
                continue

            usuario, _ = Usuario.objects.update_or_create(
                cedula_identidad=cedula,
                defaults={
                    "nombres": nombres,
                    "apellidos": apellidos,
                    "genero": "No especificado",
                    "estado_civil": "Soltero(a)",
                },
            )

            Cuenta.objects.update_or_create(
                usuario=username,
                defaults={
                    "id_usuario": usuario,
                    "clave": make_password("12345678"),
                    "tipo_cuenta": "ADMIN",
                },
            )

            Docente.objects.get_or_create(
                usuario=usuario,
                nucleo=barinas,
                pnf=pnf,
                defaults={
                    "activo": True,
                },
            )

        self.stdout.write("✓ Docentes adicionales")

    # ============================================================
    # ESTUDIANTES
    # ============================================================

    def crear_estudiantes(self):

        nombres = [
            "Juan",
            "María",
            "Pedro",
            "Ana",
            "Luis",
            "Carla",
            "José",
            "Daniela",
            "Miguel",
            "Sofía",
        ]

        apellidos = [
            "Pérez",
            "González",
            "Rodríguez",
            "Hernández",
            "Martínez",
            "Díaz",
            "Rojas",
            "Mendoza",
            "Torres",
            "Silva",
        ]

        relaciones = list(
            PNFNucleo.objects.select_related(
                "id_nucleo",
                "id_pnf",
            )
        )

        contador = 1

        for relacion in relaciones:

            nucleo = relacion.id_nucleo
            pnf = relacion.id_pnf

            # Dos estudiantes por combinación PNF/Núcleo.
            for posicion in range(2):

                cedula = str(
                    20000000 + contador
                )

                nombre = nombres[
                    (contador - 1) % len(nombres)
                ]

                apellido = apellidos[
                    (contador - 1) % len(apellidos)
                ]

                usuario, _ = Usuario.objects.update_or_create(
                    cedula_identidad=cedula,
                    defaults={
                        "nombres": nombre,
                        "apellidos": apellido,
                        "genero": "No especificado",
                        "estado_civil": "Soltero(a)",
                    },
                )

                Cuenta.objects.update_or_create(
                    usuario=f"estudiante{contador:03d}",
                    defaults={
                        "id_usuario": usuario,
                        "clave": make_password("12345678"),
                        "tipo_cuenta": "EST",
                    },
                )

                Estudiante.objects.get_or_create(
                    usuario=usuario,
                    nucleo=nucleo,
                    pnf=pnf,
                )

                contador += 1

        self.stdout.write(
            f"✓ Estudiantes: {contador - 1}"
        )

    # ============================================================
    # DATOS PERSONALES
    # ============================================================

    def crear_datos_personales(self):

        estudiantes = list(
            Estudiante.objects.select_related(
                "usuario",
                "nucleo",
            )
        )

        for indice, estudiante in enumerate(
            estudiantes,
            start=1,
        ):

            usuario = estudiante.usuario

            Contacto.objects.get_or_create(
                id_usuario=usuario,
                defaults={
                    "telefono_personal":
                        f"0414{indice:07d}",
                    "telefono_suplete": "",
                    "correo_electronico":
                        f"estudiante{indice}@carsce.test",
                },
            )

            Nacimiento.objects.get_or_create(
                id_usuario=usuario,
                defaults={
                    "pais": "Venezuela",
                    "estado": "Barinas",
                    "municipio": estudiante.nucleo.municipio,
                    "parroquia": estudiante.nucleo.municipio,
                    "direccion_nacimiento":
                        "Dirección de nacimiento de prueba",
                    "fecha_nacimiento": date(
                        2000 + (indice % 6),
                        1 + (indice % 12),
                        1 + (indice % 25),
                    ),
                },
            )

            Residencia.objects.get_or_create(
                id_usuario=usuario,
                defaults={
                    "condicion_residencia": "Propia",
                    "municipio":
                        estudiante.nucleo.municipio,
                    "parroquia":
                        estudiante.nucleo.municipio,
                    "direccion_residencia":
                        "Dirección residencial de prueba",
                },
            )

            InformacionSecundaria.objects.get_or_create(
                id_usuario=usuario,
                defaults={
                    "tipo_institucion": "Liceo Público",
                    "nombre_institucion":
                        "Institución Educativa de Prueba",
                    "fecha_grado": date(2019, 7, 15),
                    "codigo_sni_opsu":
                        f"OPSUSEED{indice:05d}",
                },
            )

        self.stdout.write("✓ Datos personales")

    # ============================================================
    # INSCRIPCIONES
    # ============================================================

    def crear_inscripciones(self):

        trayecto = TrayectoAcademico.objects.filter(
            nombre="Trayecto I"
        ).first()

        if not trayecto:
            trayecto = TrayectoAcademico.objects.first()

        estudiantes = Estudiante.objects.select_related(
            "nucleo",
            "pnf",
        )

        for estudiante in estudiantes:

            estatus, _ = EstatusEstudiante.objects.get_or_create(
                estudiante=estudiante,
                trayecto=trayecto,
                defaults={
                    "estatus": "Activo",
                    "estado": "Activo",
                    "ingreso": "Regular",
                    "descripcion_ingreso":
                        "Ingreso regular",
                    "fecha_ingreso": date(2026, 1, 15),
                    "perfil_registro": "SEED",
                    "fecha_registro": timezone.now(),
                },
            )

            aula = AulaAcademica.objects.filter(
                id_nucleo=estudiante.nucleo,
                id_pnf=estudiante.pnf,
            ).first()

            if aula:

                AulaEstudiante.objects.get_or_create(
                    aula=aula,
                    estatus=estatus,
                    defaults={
                        "fecha_inicio": date(2026, 1, 15),
                        "estado": "Curso",
                    },
                )

        self.stdout.write("✓ Inscripciones")

    # ============================================================
    # MATERIAS ASIGNADAS
    # ============================================================

    def crear_materias_asignadas(self):

        docentes = Docente.objects.select_related(
            "usuario",
            "pnf",
            "nucleo",
        )

        for docente in docentes:

            materias = Materia.objects.filter(
                id_pnf=docente.pnf,
                activa=True,
            )[:3]

            for materia in materias:

                MateriaAsignada.objects.get_or_create(
                    materia=materia,
                    defaults={
                        "activo": True,
                        "registrado_por":
                            docente.usuario,
                        "fecha_registro":
                            timezone.now(),
                        "perfil_registro":
                            "SEED",
                    },
                )

        self.stdout.write("✓ Materias asignadas")

    # ============================================================
    # DOCENTES ASIGNADOS
    # ============================================================

    def crear_docentes_asignados(self):

        docentes = Docente.objects.select_related(
            "usuario",
            "pnf",
        )

        for docente in docentes:

            asignaciones = MateriaAsignada.objects.filter(
                materia__id_pnf=docente.pnf,
                activo=True,
            )[:3]

            for asignacion in asignaciones:

                DocenteAsignadoMateria.objects.get_or_create(
                    materia_asignada=asignacion,
                    defaults={
                        "docente": docente,
                        "rol": "PRINCIPAL",
                        "activo": True,
                        "registrado_por":
                            docente.usuario,
                        "fecha_registro":
                            timezone.now(),
                        "perfil_registro":
                            "SEED",
                    },
                )

        self.stdout.write("✓ Docentes asignados")

    # ============================================================
    # PLANIFICACIONES
    # ============================================================

    def crear_planificaciones(self):

        periodo = PeriodoAcademico.objects.filter(
            nombre="Semestre I"
        ).first()

        if not periodo:
            periodo = PeriodoAcademico.objects.first()

        for asignacion in MateriaAsignada.objects.select_related(
            "materia",
            "materia__id_pnf",
        ):

            pnf = asignacion.materia.id_pnf

            nucleo = Nucleos.objects.filter(
                aulas__id_pnf=pnf
            ).first()

            if not nucleo:
                continue

            plan, _ = PlanificacionAcademica.objects.get_or_create(
                pnf=pnf,
                nucleo=nucleo,
                materia_asignacion=asignacion,
                periodo_academico=periodo,
                defaults={
                    "activo": True,
                    "estado_aceptacion": "ACEPTADA",
                    "observacion":
                        "Planificación académica de prueba.",
                },
            )

            if plan.detalles.exists():
                continue

            for numero in range(1, 4):

                ponderacion = (
                    33.33
                    if numero < 3
                    else 33.34
                )

                detalle = DetallePlanificacion.objects.create(
                    plan_academico=plan,
                    titulo_unidad=f"Unidad {numero}",
                    ponderacion=ponderacion,
                    contenido_unidad=(
                        f"Contenido académico de prueba "
                        f"correspondiente a la unidad {numero}."
                    ),
                    fecha_registro=timezone.now(),
                )

                DetalleEvaluacion.objects.create(
                    detalle_plan=detalle,
                    metodo_evaluacion="Evaluación escrita",
                    porcentaje_evaluacion=100,
                    fecha_evaluacion=date(
                        2026,
                        numero + 1,
                        10,
                    ),
                )

        self.stdout.write("✓ Planificaciones")

    # ============================================================
    # CALIFICACIONES
    # ============================================================

    def crear_calificaciones(self):

        docente = Usuario.objects.filter(
            cedula_identidad="10000004"
        ).first()

        estudiantes = Estudiante.objects.select_related(
            "pnf",
        )

        for estudiante in estudiantes:

            asignaciones = MateriaAsignada.objects.filter(
                materia__id_pnf=estudiante.pnf,
                activo=True,
            )[:3]

            for indice, asignacion in enumerate(
                asignaciones
            ):

                plan = PlanificacionAcademica.objects.filter(
                    pnf=estudiante.pnf,
                    materia_asignacion=asignacion,
                ).first()

                periodo_materia = (
                    PeriodoAcademicoMateria.objects.filter(
                        materia=asignacion.materia
                    ).first()
                )

                if not plan or not periodo_materia:
                    continue

                promedio = 12 + (
                    (
                        estudiante.id_estudiante
                        + indice
                    ) % 9
                )

                condicion = (
                    "Aprobado"
                    if promedio >= 10
                    else "Reprobado"
                )

                calificacion, _ = Calificaciones.objects.get_or_create(
                    estudiante=estudiante,
                    materia_asignada=asignacion,
                    trayecto=asignacion.materia.id_trayecto,
                    defaults={
                        "planificacion_academica":
                            plan,
                        "periodo_materia":
                            periodo_materia,
                        "promedio_tramo":
                            promedio,
                        "asistencia":
                            85 + (
                                estudiante.id_estudiante
                                % 16
                            ),
                        "condicion":
                            condicion,
                        "fecha_promedio":
                            date(2026, 7, 15),
                        "registrado_por":
                            docente,
                        "fecha_registro":
                            timezone.now(),
                        "perfil_registro":
                            "SEED",
                        "congelada":
                            False,
                    },
                )

                for detalle in plan.detalles.all():

                    DetalleCalificacionesUnidad.objects.get_or_create(
                        calificacion=calificacion,
                        unidad=detalle,
                        defaults={
                            "nota_unidad":
                                promedio,
                            "fecha_registro":
                                timezone.now(),
                            "perfil_registro":
                                "SEED",
                        },
                    )

        self.stdout.write("✓ Calificaciones")

    # ============================================================
    # PROMEDIOS
    # ============================================================

    def crear_promedios(self):

        for calificacion in Calificaciones.objects.select_related(
            "estudiante",
            "materia_asignada",
            "trayecto",
        ):

            if not calificacion.estudiante:
                continue

            PromedioFinal.objects.get_or_create(
                estudiante=calificacion.estudiante,
                materia_asignacion=
                    calificacion.materia_asignada,
                trayecto=calificacion.trayecto,
                defaults={
                    "promedio_final":
                        calificacion.promedio_tramo or 0,
                    "asistencia":
                        calificacion.asistencia,
                    "estado":
                        calificacion.condicion or "Pendiente",
                    "fecha_promedio":
                        calificacion.fecha_promedio
                        or date.today(),
                    "motivo":
                        "Promedio generado por "
                        "datos de prueba.",
                },
            )

        self.stdout.write("✓ Promedios finales")

    # ============================================================
    # REPARACIONES
    # ============================================================

    def crear_reparaciones(self):

        nucleo = Nucleos.objects.filter(
            municipio="Barinas"
        ).first()

        for asignacion in MateriaAsignada.objects.all()[:5]:

            evaluacion, _ = EvaluacionReparacion.objects.get_or_create(
                materia_asignacion=asignacion,
                defaults={
                    "pnf":
                        asignacion.materia.id_pnf,
                    "nucleo":
                        nucleo,
                    "activo":
                        True,
                },
            )

            if not evaluacion.detalles.exists():

                DetalleEvaluacionReparacion.objects.create(
                    evaluacion_reparacion=evaluacion,
                    porcentaje=100,
                    tipo_evaluacion="EXAMEN",
                )

            estudiante = Estudiante.objects.filter(
                pnf=asignacion.materia.id_pnf
            ).first()

            if estudiante:

                Reparacion.objects.get_or_create(
                    estudiante=estudiante,
                    evaluacion_reparacion=evaluacion,
                    defaults={
                        "fecha_reparacion":
                            date(2026, 8, 10),
                        "calificacion":
                            14,
                        "estado":
                            "APROBADO",
                    },
                )

        self.stdout.write("✓ Reparaciones")

    # ============================================================
    # HISTORIALES
    # ============================================================

    def crear_historiales(self):

        usuario = Usuario.objects.filter(
            cedula_identidad="10000002"
        ).first()

        nucleo = Nucleos.objects.filter(
            municipio="Barinas"
        ).first()

        pnf = Pnf.objects.first()

        if usuario and nucleo and pnf:

            HistorialAsignaciones.objects.get_or_create(
                usuario=usuario,
                tipo_perfil="CONTROL_ESTUDIO",
                nucleo=nucleo,
                pnf=pnf,
                accion="ASIGNACION",
            )

        trayectos = list(
            TrayectoAcademico.objects.all()
        )

        if len(trayectos) >= 2:

            estudiantes = Estudiante.objects.filter(
                pnf=pnf
            )[:3]

            for estudiante in estudiantes:

                HistorialTrayectoEstudiante.objects.get_or_create(
                    estudiante=estudiante,
                    anio=2026,
                    trayecto_anterior=trayectos[0],
                    trayecto_nuevo=trayectos[1],
                    defaults={
                        "cantidad_materias": 3,
                        "materias_reprobadas": 0,
                        "materias_mala_asistencia": 0,
                        "estado": "Aprobado",
                        "puede_pasar": True,
                        "motivo":
                            "Cumplimiento de condiciones "
                            "académicas.",
                    },
                )

        self.stdout.write("✓ Historiales")

    # ============================================================
    # AUTORIDADES
    # ============================================================

    def crear_autoridades(self):

        autoridades = [
            (
                "Carlos",
                "Rodríguez",
                "40000001",
                "Director General",
                "RES-2026-001",
            ),
            (
                "María",
                "González",
                "40000002",
                "Control de Estudio",
                "RES-2026-002",
            ),
            (
                "Luis",
                "Hernández",
                "40000003",
                "Coordinador de PNF",
                "RES-2026-003",
            ),
        ]

        for (
            nombres,
            apellidos,
            cedula,
            cargo,
            resolucion,
        ) in autoridades:

            Autoridades.objects.update_or_create(
                cedula_identidad=cedula,
                defaults={
                    "nombres": nombres,
                    "apellidos": apellidos,
                    "genero": "No especificado",
                    "cargo": cargo,
                    "resolucion": resolucion,
                },
            )

        self.stdout.write("✓ Autoridades")

    # ============================================================
    # BITÁCORA
    # ============================================================

    def crear_bitacora(self):

        acciones = [
            "Inicio de sesión",
            "Registro de estudiante",
            "Registro de inscripción",
            "Registro de calificación",
            "Generación de reporte académico",
        ]

        for indice, accion in enumerate(
            acciones,
            start=1,
        ):

            Bitacora.objects.get_or_create(
                nombre_usuario="seed_carsce",
                accion=accion,
                defaults={
                    "fecha_hora":
                        timezone.now()
                        - timedelta(days=indice),
                },
            )

        self.stdout.write("✓ Bitácora")

    # ============================================================
    # VERIFICACIONES
    # ============================================================

    def crear_verificaciones(self):

        for indice in range(1, 6):

            VerificacionCodigo.objects.get_or_create(
                cedula_identidad=
                    f"2000000{indice}",
                codigo=f"{100000 + indice}",
                defaults={
                    "token":
                        f"TOKEN-SEED-{indice:04d}",
                    "creado":
                        timezone.now(),
                    "intentos":
                        0,
                    "activo":
                        1,
                    "descripcion":
                        "Código de verificación de prueba",
                    "fecha_expiracion":
                        timezone.now()
                        + timedelta(minutes=15),
                },
            )

        self.stdout.write("✓ Verificaciones")