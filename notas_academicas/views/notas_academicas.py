from django.shortcuts import render
from django.http import JsonResponse
from django.db import transaction
from decimal import Decimal, ROUND_HALF_UP
from django.utils import timezone
from django.db.models import F
from django.db.models import Exists, OuterRef

from inicio_sesion.models import TrayectoAcademico, MateriaAsignada, CalendarioPeriodo, PeriodoAcademicoMateria, Usuario, Pnf, PNFNucleo, Estudiante, EstatusEstudiante, CalendarioAcademico, Nucleos, PeriodoAcademico, Materia, Docente, DocenteAsignadoMateria

from notas_academicas.models import PlanificacionAcademica, Reparacion, DetallePlanificacion, HistorialTrayectoEstudiante, HistorialDetalleNota, HistorialModificacionNotas, DetalleEvaluacion, PromedioFinal, Calificaciones, DetalleCalificacionesUnidad

# Registrar Notas Académicas
def mat_not_acad(request):
    if request.method != "POST":
        return JsonResponse({
            "estado": "fallo",
            "title": "Error",
            "icon": "error",
            "descripcion": "Método de solicitud no permitido."
        })

    nucleo = request.POST.get("id_nucleo")
    pnf = request.POST.get("id_pnf")
    cedula = request.session.get("cedula_usuario")

    if not all([nucleo, pnf, cedula]):
        return JsonResponse({
            "estado": "fallo",
            "title": "Error",
            "icon": "error",
            "descripcion": "Faltan datos para realizar la consulta."
        })

    fecha_actual = timezone.localdate()
    año_actual = fecha_actual.year

    # BUSCAR EL PERÍODO ACADÉMICO ACTUAL PARA CARGA DE NOTAS
    calendarios_periodos = (
        CalendarioPeriodo.objects
        .filter(
            calendario__tipo="CARGA_NOTAS",
            calendario__activo=True,
            calendario__fecha_inicio__lte=fecha_actual,
            calendario__fecha_final__gte=fecha_actual,
            calendario__fecha_inicio__year=año_actual,
        )
        .select_related("periodo", "calendario")
    )

    if not calendarios_periodos.exists():
        return JsonResponse({
            "estado": "exito",
            "materias": [],
            "periodo_actual": None,
            "mensaje": "Actualmente no existe un período habilitado para la carga de notas."
        })

    periodos_actuales = calendarios_periodos.values_list(
        "periodo_id",
        flat=True
    )

   

    # ============================================================
    # MATERIAS DEL DOCENTE
    # ============================================================

    materias_asignadas = (
        DocenteAsignadoMateria.objects
        .filter(
            docente__usuario__cedula_identidad=cedula,
            docente__nucleo_id=nucleo,
            docente__pnf_id=pnf,
            activo=True,
            materia_asignada__activo=True,
            materia_asignada__materia__periodos_academicos__periodo_id__in=periodos_actuales,
        )
        .select_related(
            "materia_asignada__materia",
            "materia_asignada__materia__id_trayecto",
        )
        .distinct()
    )
    # EXCLUIR MATERIAS YA REGISTRADAS EN ESTE PERÍODO
    materias_registradas = Calificaciones.objects.filter(
        materia_asignada=OuterRef("materia_asignada"),
        periodo_materia__periodo_id__in=periodos_actuales,
        fecha_promedio__year=año_actual,
    )

    materias_asignadas = (
        materias_asignadas
        .annotate(
            ya_registrada=Exists(materias_registradas)
        )
        .filter(
            ya_registrada=False
        )
    )

    materias = []

    for asignacion in materias_asignadas:

        materia_asignada = asignacion.materia_asignada
        materia = materia_asignada.materia

        materias.append({
            "id_materia_asignada": materia_asignada.id_materia_asignada,
            "id_materia": materia.id_materia,
            "nombre": materia.nombre,
            "id_trayecto": materia.id_trayecto.id_periodo_academico,
            "trayecto": materia.id_trayecto.nombre,
        })

    return JsonResponse({
        "estado": "exito",
        "materias": materias,
        "periodos_actuales": [
            {
                "id_periodo": cp.periodo.id_periodo_academico,
                "nombre": cp.periodo.nombre,
            }
            for cp in calendarios_periodos
        ]
    })

def per_not_acad(request):
    if request.method == "POST":
        nucleo = request.POST.get("id_nucleo")
        pnf = request.POST.get("id_pnf")
        materia_asignada = request.POST.get("id_materia_asignada")

        if not all([nucleo, pnf, materia_asignada]):
            return JsonResponse({
                "estado": "fallo",
                "title": "Error",
                "icon": "error",
                "descripcion": "Faltan datos para realizar la consulta."
            })

        try:
            materia_asignada_obj = (
                MateriaAsignada.objects
                .select_related("materia")
                .get(
                    id_materia_asignada=materia_asignada,
                    activo=True,
                    materia__id_pnf=pnf
                )
            )
        except MateriaAsignada.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "title": "Error",
                "icon": "error",
                "descripcion": "La materia asignada no se encuentra registrada."
            })

        hoy = timezone.localdate()

        periodos_habilitados = (
            CalendarioPeriodo.objects
            .filter(
                calendario__activo=True,
                calendario__tipo="CARGA_NOTAS",
                calendario__fecha_inicio__lte=hoy,
                calendario__fecha_final__gte=hoy
            )
            .values_list(
                "periodo__id_periodo_academico",
                flat=True
            )
        )

        periodos_materia = (
            PeriodoAcademicoMateria.objects
            .filter(
                materia=materia_asignada_obj.materia,
                periodo__id_periodo_academico__in=periodos_habilitados
            )
            .select_related("periodo")
            .order_by("periodo__nombre")
        )

        print(periodos_materia)

        if not periodos_materia.exists():
            return JsonResponse({
                "estado": "exito",
                "title": "Sin período habilitado",
                "icon": "info",
                "descripcion": "La materia no tiene un período de carga de notas habilitado actualmente.",
                "datos": []
            })

        datos = []

        for periodo_materia in periodos_materia:
            datos.append({
                "id_periodo_materia": periodo_materia.id,
                "id_periodo_academico": periodo_materia.periodo_id,
                "nombre": periodo_materia.periodo.nombre
            })

        return JsonResponse({
            "estado": "exito",
            "datos": datos
        })

def cant_det_pla(request):
    if request.method == "POST":
        nucleo = request.POST.get("id_nucleo")
        pnf = request.POST.get("id_pnf")
        materia_asignada = request.POST.get("id_materia_asignada")
        periodo_materia = request.POST.get("id_periodo_materia")

        try:
            materia_asignada_obj = (
                MateriaAsignada.objects
                .select_related("materia")
                .get(
                    id_materia_asignada=materia_asignada,
                    activo=True,
                    materia__id_pnf=pnf
                )
            )

            periodo_materia_obj = (
                PeriodoAcademicoMateria.objects
                .select_related("periodo")
                .get(
                    periodo=periodo_materia,
                    materia=materia_asignada_obj.materia
                )
            )

        except (
            MateriaAsignada.DoesNotExist,
            PeriodoAcademicoMateria.DoesNotExist
        ):
            return JsonResponse({
                "estado": "fallo",
                "title": "Error",
                "icon": "error",
                "descripcion": "La materia o el período académico no son válidos."
            })

        planificacion = (
            PlanificacionAcademica.objects
            .filter(
                pnf_id=pnf,
                nucleo_id=nucleo,
                materia_asignacion=materia_asignada_obj,
                periodo_academico=periodo_materia_obj.periodo,
                activo=True,
                estado_aceptacion="ACEPTADA"
            )
            .first()
        )

        if not planificacion:
            return JsonResponse({
                "estado": "exito",
                "cantidad_actividades": 0
            })

        cantidad_unidades = (
            DetallePlanificacion.objects
            .filter(
                plan_academico=planificacion
            )
            .count()
        )

        return JsonResponse({
            "estado": "exito",
            "cantidad_actividades": cantidad_unidades
        })
    
def est_not_acad(request):
    if request.method == "POST":
        nucleo = request.POST.get("id_nucleo")
        pnf = request.POST.get("id_pnf")
        materia_asignacion = request.POST.get("id_materia_asignada")
        trayecto = request.POST.get("trayecto")
        periodo_materia = request.POST.get("id_periodo_materia")



        if not all([nucleo, pnf, materia_asignacion, trayecto, periodo_materia]):
            return JsonResponse({
                "estado": "fallo",
                "title": "Error",
                "icon": "error",
                "descripcion": "Faltan datos para realizar la consulta."
            })

        try:
            trayecto_obj = TrayectoAcademico.objects.get(
                nombre=trayecto
            )
        except TrayectoAcademico.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "title": "Error",
                "icon": "error",
                "descripcion": "El trayecto académico no existe."
            })

        estudiantes = (
            Estudiante.objects
            .filter(
                nucleo_id=nucleo,
                pnf_id=pnf,
                estatus__trayecto=trayecto_obj,
                estatus__estatus="Inscrito(a)",
                estatus__estado="Activo"
            )
            .select_related("usuario")
            .distinct()
        )

        datos = []

        for estudiante in estudiantes:
            datos.append({
                "id_estudiante": estudiante.id_estudiante,
                "nombre_completo": (
                    estudiante.usuario.nombres
                    + " "
                    + estudiante.usuario.apellidos
                ),
                "cedula": estudiante.usuario.cedula_identidad
            })

        return JsonResponse({
            "estado": "exito",
            "estudiantes": datos
        })
    
def reg_nota_acad(request):
    if request.method == "POST":
        nucleo_asignado = request.POST.get("nucleo_asignado")
        pnf_asignado = request.POST.get("pnf_asignado")
        materia_asignada = request.POST.get("materia_asignada")
        periodo_materia = request.POST.get("periodo_academico")
        trayecto_academico = request.POST.get("trayecto_academico")
        cantidad_evaluaciones = request.POST.get("cantidad_evaluaciones")

        calificaciones = {}
        asistencias = {}
        promedios = {}

        controles = [
            (
                nucleo_asignado,
                "Núcleo",
                "Debe seleccionar el núcleo."
            ),
            (
                pnf_asignado,
                "P.N.F",
                "Debe seleccionar el P.N.F."
            ),
            (
                materia_asignada,
                "Materia",
                "Debe seleccionar la materia."
            ),
            (
                periodo_materia,
                "Periodo académico",
                "Debe seleccionar el periodo académico."
            ),
            (
                trayecto_academico,
                "Trayecto Académico",
                "Debe seleccionar el trayecto académico."
            )
        ]

        for control, titulo, descripcion in controles:
            if not control:
                return JsonResponse({
                    "estado": "fallo",
                    "icon": "error",
                    "title": titulo,
                    "descripcion": descripcion
                })

        if not cantidad_evaluaciones:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Cantidad de evaluaciones",
                "descripcion": "Debe indicar la cantidad de evaluaciones."
            })

        try:
            cantidad_evaluaciones = int(cantidad_evaluaciones)
        except (TypeError, ValueError):
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Cantidad de evaluaciones",
                "descripcion": "La cantidad de evaluaciones no es válida."
            })

        if cantidad_evaluaciones < 1:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Cantidad de evaluaciones",
                "descripcion": (
                    "La cantidad de evaluaciones debe ser mayor que cero."
                )
            })

        ids_estudiantes = set()

        for nombre_campo, valor in request.POST.items():

            if nombre_campo.startswith("calificacion_"):
                partes = nombre_campo.split("_")

                if len(partes) != 3:
                    continue

                id_estudiante = partes[1]
                numero_unidad = partes[2]

                ids_estudiantes.add(id_estudiante)

                calificaciones.setdefault(
                    id_estudiante,
                    {}
                )

                calificaciones[id_estudiante][numero_unidad] = valor

            elif nombre_campo.startswith("asistencia_"):
                partes = nombre_campo.split("_")

                if len(partes) != 2:
                    continue

                id_estudiante = partes[1]

                ids_estudiantes.add(id_estudiante)
                asistencias[id_estudiante] = valor

            elif nombre_campo.startswith("promedio_"):
                partes = nombre_campo.split("_")

                if len(partes) != 2:
                    continue

                id_estudiante = partes[1]

                ids_estudiantes.add(id_estudiante)
                promedios[id_estudiante] = valor

        try:
            materia_asignacion = (
                MateriaAsignada.objects
                .select_related("materia")
                .get(
                    id_materia_asignada=materia_asignada,
                    activo=True,
                    materia__id_pnf=pnf_asignado
                )
            )
        except MateriaAsignada.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Materia",
                "descripcion": (
                    "La materia asignada no existe, "
                    "se encuentra inactiva o no pertenece al P.N.F seleccionado."
                )
            })

        try:
            periodo_materia = (
                PeriodoAcademicoMateria.objects
                .select_related("periodo", "materia")
                .get(
                    periodo=periodo_materia,
                    materia=materia_asignacion.materia
                )
            )
        except PeriodoAcademicoMateria.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Periodo académico",
                "descripcion": (
                    "El periodo académico seleccionado no está asociado "
                    "a la materia seleccionada."
                )
            })

        hoy = timezone.localdate()

        calendario_habilitado = (
            CalendarioPeriodo.objects
            .filter(
                calendario__activo=True,
                calendario__tipo="CARGA_NOTAS",
                calendario__fecha_inicio__lte=hoy,
                calendario__fecha_final__gte=hoy,
                periodo_id=periodo_materia.periodo_id
            )
            .exists()
        )

        if not calendario_habilitado:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Periodo no habilitado",
                "descripcion": (
                    "El periodo académico seleccionado "
                    "no se encuentra habilitado actualmente para la carga de notas."
                )
            })

        planificacion = (
            PlanificacionAcademica.objects
            .filter(
                materia_asignacion=materia_asignacion,
                pnf_id=pnf_asignado,
                nucleo_id=nucleo_asignado,
                periodo_academico_id=periodo_materia.periodo_id,
                activo=True,
                estado_aceptacion="ACEPTADA"
            )
            .first()
        )

        if not planificacion:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Plan académico",
                "descripcion": (
                    "No se encuentra registrado un plan de actividad "
                    "académica aceptado para la materia, núcleo, P.N.F "
                    "y periodo académico seleccionado."
                )
            })

        unidades = list(
            planificacion.detalles
            .all()
            .order_by("id_detalle")
        )

        if not unidades:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Unidades académicas",
                "descripcion": (
                    "El plan de actividad académica seleccionado "
                    "no tiene unidades registradas."
                )
            })

        cantidad_unidades = len(unidades)

        if cantidad_evaluaciones != cantidad_unidades:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Cantidad de evaluaciones",
                "descripcion": (
                    "La cantidad de evaluaciones recibida no coincide "
                    "con la cantidad de unidades registradas en el "
                    "plan de actividad académica."
                )
            })

        try:
            trayecto_obj = TrayectoAcademico.objects.get(
                nombre=trayecto_academico
            )
        except TrayectoAcademico.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Trayecto académico",
                "descripcion": (
                    "El trayecto académico seleccionado no existe."
                )
            })

        año_actual = hoy.year

        with transaction.atomic():

            for id_estudiante in ids_estudiantes:

                try:
                    estudiante = (
                        Estudiante.objects
                        .get(
                            id_estudiante=id_estudiante,
                            nucleo_id=nucleo_asignado,
                            pnf_id=pnf_asignado
                        )
                    )
                except Estudiante.DoesNotExist:
                    return JsonResponse({
                        "estado": "fallo",
                        "icon": "error",
                        "title": "Estudiante",
                        "descripcion": (
                            f"No se encontró el estudiante {id_estudiante} "
                            "en el núcleo y P.N.F seleccionados."
                        )
                    })

                ya_registrada = (
                    Calificaciones.objects
                    .filter(
                        estudiante=estudiante,
                        materia_asignada=materia_asignacion,
                        periodo_materia=periodo_materia,
                        fecha_promedio__year=año_actual
                    )
                    .exists()
                )

                if ya_registrada:
                    continue

                valor_promedio = promedios.get(
                    id_estudiante,
                    "0"
                )

                if valor_promedio == "":
                    valor_promedio = "0"

                try:
                    promedio = Decimal(
                        valor_promedio.replace(",", ".")
                    )
                except (ValueError, TypeError):
                    return JsonResponse({
                        "estado": "fallo",
                        "icon": "error",
                        "title": "Promedio inválido",
                        "descripcion": (
                            f"El promedio del estudiante "
                            f"{id_estudiante} no es válido."
                        )
                    })

                if promedio < Decimal("0") or promedio > Decimal("20"):
                    return JsonResponse({
                        "estado": "fallo",
                        "icon": "error",
                        "title": "Promedio inválido",
                        "descripcion": (
                            f"El promedio del estudiante "
                            f"{id_estudiante} debe estar entre 0 y 20."
                        )
                    })

                try:
                    asistencia = int(
                        asistencias.get(
                            id_estudiante,
                            0
                        )
                    )
                except (ValueError, TypeError):
                    return JsonResponse({
                        "estado": "fallo",
                        "icon": "error",
                        "title": "Asistencia inválida",
                        "descripcion": (
                            f"La asistencia del estudiante "
                            f"{id_estudiante} no es válida."
                        )
                    })

                if asistencia < 0 or asistencia > 100:
                    return JsonResponse({
                        "estado": "fallo",
                        "icon": "error",
                        "title": "Asistencia inválida",
                        "descripcion": (
                            f"La asistencia del estudiante "
                            f"{id_estudiante} debe estar entre 0 y 100."
                        )
                    })

                nombre_materia = (
                    materia_asignacion.materia.nombre
                    .strip()
                    .lower()
                )

                if asistencia >= 75:
                    if "proyecto socio tecnológico" in nombre_materia:
                        if promedio >= Decimal("16"):
                            condicion = "APROBADO"
                        else:
                            condicion = "REPROBADO"
                    else:
                        if promedio >= Decimal("12"):
                            condicion = "APROBADO"
                        else:
                            condicion = "REPARACIÓN"
                else:
                    condicion = "REPROBADO"

                calificacion = Calificaciones.objects.create(
                    planificacion_academica=planificacion,
                    periodo_materia=periodo_materia,
                    materia_asignada=materia_asignacion,
                    estudiante=estudiante,
                    promedio_tramo=promedio,
                    asistencia=asistencia,
                    condicion=condicion,
                    trayecto=trayecto_obj,
                    fecha_promedio=hoy
                )

                notas_estudiante = calificaciones.get(
                    id_estudiante,
                    {}
                )

                for numero_unidad, nota in notas_estudiante.items():

                    if nota == "":
                        continue

                    try:
                        numero_unidad = int(numero_unidad)
                    except (ValueError, TypeError):
                        return JsonResponse({
                            "estado": "fallo",
                            "icon": "error",
                            "title": "Unidad inválida",
                            "descripcion": (
                                f"La unidad recibida para el estudiante "
                                f"{id_estudiante} no es válida."
                            )
                        })

                    if numero_unidad < 1 or numero_unidad > cantidad_unidades:
                        return JsonResponse({
                            "estado": "fallo",
                            "icon": "error",
                            "title": "Unidad inválida",
                            "descripcion": (
                                f"La unidad {numero_unidad} "
                                "no existe en el plan académico."
                            )
                        })

                    try:
                        nota_unidad = Decimal(
                            nota.replace(",", ".")
                        )
                    except (ValueError, TypeError):
                        return JsonResponse({
                            "estado": "fallo",
                            "icon": "error",
                            "title": "Nota inválida",
                            "descripcion": (
                                f"La nota de la unidad {numero_unidad} "
                                f"del estudiante {id_estudiante} "
                                "no es válida."
                            )
                        })

                    if nota_unidad < Decimal("0") or nota_unidad > Decimal("20"):
                        return JsonResponse({
                            "estado": "fallo",
                            "icon": "error",
                            "title": "Nota inválida",
                            "descripcion": (
                                f"La nota de la unidad {numero_unidad} "
                                f"del estudiante {id_estudiante} "
                                "debe estar entre 0 y 20."
                            )
                        })

                    unidad = unidades[numero_unidad - 1]

                    DetalleCalificacionesUnidad.objects.create(
                        calificacion=calificacion,
                        unidad=unidad,
                        nota_unidad=nota_unidad
                    )

        return JsonResponse({
            "estado": "exito",
            "icon": "success",
            "title": "Éxito",
            "descripcion": (
                "Se registraron las notas académicas exitosamente."
            )
        })

    return render(
        request,
        "registrar_notas_academicas.html"
    )

# Visualizar Notas Académicas

def vis_not_acad(request):
    return render (request, "visualizar_notas_academicas.html")

def mat_reg_not(request):
    if request.method == "POST":
        cedula = request.session.get("cedula_usuario")
        id_nucleo = request.POST.get("id_nucleo")
        id_pnf = request.POST.get("id_pnf")

        if not all([cedula, id_nucleo, id_pnf]):
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Datos incompletos",
                "descripcion": "Faltan datos para realizar la consulta."
            })

        docente = (
            Docente.objects
            .filter(
                usuario__cedula_identidad=cedula,
                nucleo_id=id_nucleo,
                pnf_id=id_pnf,
                activo=True
            )
            .first()
        )

        if not docente:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Docente no encontrado",
                "descripcion": (
                    "El docente no está asignado al núcleo y "
                    "P.N.F seleccionados."
                )
            })

        materias = (
            MateriaAsignada.objects
            .filter(
                activo=True,
                docentes__docente=docente,
                docentes__activo=True,
                materia__id_pnf=id_pnf,
                calificaciones_materia__isnull=False
            )
            .values(
                "id_materia_asignada",
                "materia__nombre",
                "materia__codigo",
                trayecto_materia=F(
                    "materia__id_trayecto__nombre"
                )
            )
            .distinct()
            .order_by("materia__nombre")
        )

        materias_lista = [
            {
                "id_materia_asignada": materia["id_materia_asignada"],
                "nombre_materia": materia["materia__nombre"],
                "codigo_materia": materia["materia__codigo"],
                "trayecto_materia": materia["trayecto_materia"]
            }
            for materia in materias
        ]

        return JsonResponse({
            "estado": "exito",
            "materias": materias_lista
        })

def perd_reg_not(request):
    if request.method == "POST":
        cedula = request.session.get("cedula_usuario")
        nucleo = request.POST.get("id_nucleo")
        pnf = request.POST.get("id_pnf")
        materia_asignada = request.POST.get("id_materia_asignada")

        if not all([cedula, nucleo, pnf, materia_asignada]):
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Datos incompletos",
                "descripcion": "Faltan datos para realizar la consulta."
            })

        try:
            materia_asignada_obj = (
                MateriaAsignada.objects
                .select_related("materia")
                .get(
                    id_materia_asignada=materia_asignada,
                    activo=True,
                    materia__id_pnf=pnf
                )
            )
        except MateriaAsignada.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Materia",
                "descripcion": "La materia asignada no es válida."
            })

        periodos = (
            PeriodoAcademicoMateria.objects
            .filter(
                materia=materia_asignada_obj.materia,
                calificaciones_periodo__materia_asignada=materia_asignada_obj,
                calificaciones_periodo__estudiante__nucleo_id=nucleo,
                calificaciones_periodo__estudiante__pnf_id=pnf,
                calificaciones_periodo__materia_asignada__docentes__docente__usuario__cedula_identidad=cedula,
                calificaciones_periodo__materia_asignada__docentes__activo=True
            )
            .select_related("periodo")
            .values(
                "id",
                "periodo__id_periodo_academico",
                "periodo__nombre"
            )
            .distinct()
            .order_by("periodo__nombre")
        )

        if not periodos:
            return JsonResponse({
                "estado": "exito",
                "periodos": []
            })

        return JsonResponse({
            "estado": "exito",
            "periodos": [
                {
                    "id_periodo_materia": periodo["id"],
                    "id_periodo_academico": periodo["periodo__id_periodo_academico"],
                    "nombre_periodo": periodo["periodo__nombre"]
                }
                for periodo in periodos
            ]
        })

def fech_reg_not(request):
    if request.method == "POST":
        cedula = request.session.get("cedula_usuario")
        nucleo = request.POST.get("id_nucleo")
        pnf = request.POST.get("id_pnf")
        materia_asignada = request.POST.get("id_materia_asignada")
        id_periodo_materia = request.POST.get("id_periodo_academico")

        if not all([
            cedula,
            nucleo,
            pnf,
            materia_asignada,
            id_periodo_materia
        ]):
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Datos incompletos",
                "descripcion": (
                    "Debe seleccionar el núcleo, P.N.F, materia "
                    "y período académico."
                )
            })

        try:
            materia_asignacion = (
                MateriaAsignada.objects
                .select_related("materia")
                .get(
                    id_materia_asignada=materia_asignada,
                    materia__id_pnf=pnf,
                    activo=True
                )
            )
        except MateriaAsignada.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Materia no encontrada",
                "descripcion": (
                    "La materia seleccionada no existe, "
                    "se encuentra inactiva o no pertenece al P.N.F seleccionado."
                )
            })

        try:
            periodo_materia = (
                PeriodoAcademicoMateria.objects
                .select_related("periodo")
                .get(
                    periodo=id_periodo_materia,
                    materia=materia_asignacion.materia
                )
            )
        except PeriodoAcademicoMateria.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Periodo académico",
                "descripcion": (
                    "El período académico seleccionado no está "
                    "asociado a la materia seleccionada."
                )
            })

        fechas = (
            Calificaciones.objects
            .filter(
                periodo_materia=periodo_materia,
                materia_asignada=materia_asignacion,
                estudiante__nucleo_id=nucleo,
                estudiante__pnf_id=pnf,
                materia_asignada__docentes__docente__usuario__cedula_identidad=cedula,
                materia_asignada__docentes__activo=True,
                fecha_promedio__isnull=False
            )
            .values_list(
                "fecha_promedio",
                flat=True
            )
            .distinct()
            .order_by("-fecha_promedio")
        )

        return JsonResponse({
            "estado": "exito",
            "fechas": [
                fecha.strftime("%Y-%m-%d")
                for fecha in fechas
            ]
        })

def calf_reg_not(request):
    if request.method == "POST":
        nucleo = request.POST.get("id_nucleo")
        pnf = request.POST.get("id_pnf")
        materia_asignada = request.POST.get("id_materia_asignada")
        id_periodo_materia = request.POST.get("id_periodo_materia")
        fecha_calificacion = request.POST.get("fecha_calificacion")

        if not all([
            nucleo,
            pnf,
            materia_asignada,
            id_periodo_materia
        ]):
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Datos incompletos",
                "descripcion": (
                    "Faltan datos para realizar la consulta."
                )
            })

        try:
            materia_asignacion = (
                MateriaAsignada.objects
                .select_related("materia")
                .get(
                    id_materia_asignada=materia_asignada,
                    materia__id_pnf=pnf,
                    activo=True
                )
            )
        except MateriaAsignada.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Materia no encontrada",
                "descripcion": (
                    "La materia seleccionada no existe, "
                    "se encuentra inactiva o no pertenece al P.N.F seleccionado."
                )
            })

        try:
            periodo_materia = (
                PeriodoAcademicoMateria.objects
                .select_related("periodo", "materia")
                .get(
                    periodo=id_periodo_materia,
                    materia=materia_asignacion.materia
                )
            )
        except PeriodoAcademicoMateria.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Periodo académico",
                "descripcion": (
                    "La materia seleccionada no está asociada "
                    "al período académico seleccionado."
                )
            })

        calificaciones = (
            Calificaciones.objects
            .select_related(
                "estudiante",
                "estudiante__usuario",
                "estudiante__nucleo",
                "estudiante__pnf",
                "materia_asignada",
                "materia_asignada__materia",
                "periodo_materia",
                "periodo_materia__periodo",
                "trayecto"
            )
            .prefetch_related(
                "detalles_unidad",
                "detalles_unidad__unidad"
            )
            .filter(
                periodo_materia=periodo_materia,
                materia_asignada=materia_asignacion,
                estudiante__nucleo_id=nucleo,
                estudiante__pnf_id=pnf,
                materia_asignada__docentes__docente__usuario__cedula_identidad=(
                    request.session.get("cedula_usuario")
                ),
                materia_asignada__docentes__activo=True
            )
            .order_by(
                "estudiante__usuario__apellidos",
                "estudiante__usuario__nombres"
            )
            .distinct()
        )

        if fecha_calificacion:
            calificaciones = calificaciones.filter(
                detalles_unidad__fecha_calificacion=fecha_calificacion
            ).distinct()

        datos = []

        for calificacion in calificaciones:
            estudiante = calificacion.estudiante
            usuario = estudiante.usuario

            unidades = []

            for detalle in calificacion.detalles_unidad.all():

                if (
                    fecha_calificacion
                    and detalle.fecha_calificacion
                    and detalle.fecha_calificacion.strftime("%Y-%m-%d")
                    != fecha_calificacion
                ):
                    continue

                unidades.append({
                    "id_detalle": detalle.id_detalle_calificaciones_unidad,
                    "id_unidad": detalle.unidad_id,
                    "nombre_unidad": detalle.unidad.titulo_unidad,
                    "nota_unidad": str(detalle.nota_unidad),
                    "fecha_calificacion": (
                        detalle.fecha_calificacion.strftime("%Y-%m-%d")
                        if detalle.fecha_calificacion
                        else None
                    )
                })

            datos.append({
                "id_calificaciones": calificacion.id_calificaciones,
                "id_estudiante": estudiante.id_estudiante,
                "nombre_estudiante": (
                    f"{usuario.nombres} {usuario.apellidos}"
                ),
                "cedula_identidad": usuario.cedula_identidad,
                "promedio": str(calificacion.promedio_tramo),
                "asistencia": calificacion.asistencia,
                "condicion": calificacion.condicion,
                "trayecto": (
                    calificacion.trayecto.nombre
                    if calificacion.trayecto
                    else None
                ),
                "unidades": unidades
            })

        return JsonResponse({
            "estado": "exito",
            "calificaciones": datos
        })

# Modificar Notas Académicas

def mod_mat_not(request):
    if request.method == "POST":
        cedula = request.session.get("cedula_usuario")
        pnf = request.POST.get("id_pnf")

        if not cedula or not pnf:
            return JsonResponse({
                "estado": "fallo",
                "title": "Error",
                "icon": "error",
                "descripcion": "Faltan datos para realizar la consulta."
            })

        hoy = timezone.localdate()

        materias = (
            Calificaciones.objects
            .filter(
                materia_asignada__isnull=False,
                materia_asignada__materia__id_pnf=pnf,
                materia_asignada__docentes__docente__usuario__cedula_identidad=cedula,
                materia_asignada__docentes__activo=True,
                periodo_materia__periodo__calendarios__calendario__activo=True,
                periodo_materia__periodo__calendarios__calendario__tipo="CARGA_NOTAS",
                periodo_materia__periodo__calendarios__calendario__fecha_inicio__lte=hoy,
                periodo_materia__periodo__calendarios__calendario__fecha_final__gte=hoy
            )
            .select_related(
                "materia_asignada__materia",
                "materia_asignada__materia__id_trayecto",
                "periodo_materia",
                "periodo_materia__periodo"
            )
            .values(
                "materia_asignada_id",
                "materia_asignada__materia__nombre",
                "materia_asignada__materia__id_trayecto__nombre",
                "periodo_materia_id",
                "periodo_materia__periodo__id_periodo_academico",
                "periodo_materia__periodo__nombre"
            )
            .distinct()
            .order_by(
                "materia_asignada__materia__nombre"
            )
        )

        return JsonResponse({
            "estado": "exito",
            "materias": [
                {
                    "id_materia_asignada": materia["materia_asignada_id"],
                    "nombre_materia": materia["materia_asignada__materia__nombre"],
                    "trayecto_materia": materia["materia_asignada__materia__id_trayecto__nombre"],
                    "id_periodo_materia": materia["periodo_materia_id"],
                    "id_periodo_academico": materia["periodo_materia__periodo__id_periodo_academico"],
                    "nombre_periodo": materia["periodo_materia__periodo__nombre"]
                }
                for materia in materias
            ]
        })

def mod_per_not(request):
    if request.method == "POST":
        cedula = request.session.get("cedula_usuario")
        pnf = request.POST.get("id_pnf")
        materia_asignada = request.POST.get("id_materia_asignada")

        if not all([cedula, pnf, materia_asignada]):
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Error",
                "descripcion": "Faltan datos para realizar la consulta."
            })

        calificacion = (
            Calificaciones.objects
            .filter(
                materia_asignada_id=materia_asignada,
                materia_asignada__materia__id_pnf=pnf,
                materia_asignada__docentes__docente__usuario__cedula_identidad=cedula,
                materia_asignada__docentes__activo=True,
                periodo_materia__isnull=False
            )
            .select_related(
                "periodo_materia",
                "periodo_materia__periodo"
            )
            .order_by("-id_calificaciones")
            .first()
        )

        if not calificacion:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Periodo Académico",
                "descripcion": (
                    "No existen notas registradas para la materia seleccionada."
                )
            })

        periodo_materia = calificacion.periodo_materia
        periodo = periodo_materia.periodo

        return JsonResponse({
            "estado": "exito",
            "id_periodo_materia": periodo.id_periodo_academico,
            "id_periodo_academico": periodo.id_periodo_academico,
            "nombre_periodo": periodo.nombre
        })

def mod_calf_not(request):
    if request.method == "POST":
        cedula = request.session.get("cedula_usuario")
        pnf = request.POST.get("id_pnf")
        materia_asignada = request.POST.get("id_materia_asignada")
        id_periodo_materia = request.POST.get("id_periodo_materia")

        if not all([cedula, pnf, materia_asignada, id_periodo_materia]):
            return JsonResponse({
                "estado": "error",
                "mensaje": "Faltan datos requeridos."
            })

        try:
            materia_asignada_obj = (
                MateriaAsignada.objects
                .select_related("materia")
                .get(
                    id_materia_asignada=materia_asignada,
                    activo=True,
                    materia__id_pnf=pnf,
                    docentes__docente__usuario__cedula_identidad=cedula,
                    docentes__activo=True
                )
            )
        except MateriaAsignada.DoesNotExist:
            return JsonResponse({
                "estado": "error",
                "mensaje": "La materia asignada no es válida."
            })

        try:
            periodo_materia = (
                PeriodoAcademicoMateria.objects
                .select_related("periodo", "materia")
                .get(
                    periodo=id_periodo_materia,
                    materia=materia_asignada_obj.materia
                )
            )
        except PeriodoAcademicoMateria.DoesNotExist:
            return JsonResponse({
                "estado": "error",
                "mensaje": (
                    "El período académico seleccionado no está "
                    "asociado a la materia seleccionada."
                )
            })

        calificaciones = (
            Calificaciones.objects
            .filter(
                materia_asignada=materia_asignada_obj,
                periodo_materia=periodo_materia,
                estudiante__nucleo_id=request.POST.get("id_nucleo"),
                estudiante__pnf_id=pnf,
                materia_asignada__docentes__docente__usuario__cedula_identidad=cedula,
                materia_asignada__docentes__activo=True
            )
            .select_related(
                "estudiante__usuario",
                "periodo_materia__periodo",
                "materia_asignada__materia",
                "trayecto"
            )
            .prefetch_related(
                "detalles_unidad__unidad"
            )
            .order_by(
                "estudiante__usuario__apellidos",
                "estudiante__usuario__nombres",
                "estudiante__usuario__cedula_identidad"
            )
        )

        if not calificaciones.exists():
            return JsonResponse({
                "estado": "error",
                "mensaje": (
                    "No existen calificaciones registradas "
                    "para este período."
                )
            })

        primera_calificacion = calificaciones.first()

        periodo = periodo_materia.periodo
        materia = materia_asignada_obj.materia

        datos = []

        for calificacion in calificaciones:
            estudiante = calificacion.estudiante
            usuario = estudiante.usuario

            datos.append({
                "id_calificaciones": calificacion.id_calificaciones,
                "id_estudiante": estudiante.id_estudiante,
                "nombre_estudiante": (
                    f"{usuario.nombres} {usuario.apellidos}"
                ),
                "cedula_identidad": usuario.cedula_identidad,
                "promedio": (
                    str(calificacion.promedio_tramo)
                    if calificacion.promedio_tramo is not None
                    else None
                ),
                "asistencia": calificacion.asistencia,
                "condicion": calificacion.condicion,
                "trayecto": (
                    calificacion.trayecto.nombre
                    if calificacion.trayecto
                    else None
                ),
                "unidades": [
                    {
                        "id_unidad": detalle.unidad_id,
                        "numero_unidad": indice + 1,
                        "nombre_unidad": detalle.unidad.titulo_unidad,
                        "nota_unidad": (
                            str(detalle.nota_unidad)
                            if detalle.nota_unidad is not None
                            else None
                        ),
                        "fecha_calificacion": (
                            detalle.fecha_calificacion.strftime("%Y-%m-%d")
                            if detalle.fecha_calificacion
                            else None
                        )
                    }
                    for indice, detalle in enumerate(
                        calificacion.detalles_unidad.all()
                    )
                ]
            })

        return JsonResponse({
            "estado": "exito",

            "periodo": {
                "id_periodo_materia": periodo_materia.id,
                "id_periodo_academico": periodo.id_periodo_academico,
                "nombre": periodo.nombre
            },

            "materia": {
                "id_materia_asignada": materia_asignada_obj.id_materia_asignada,
                "id_materia": materia.id_materia,
                "nombre": materia.nombre,
                "trayecto": (
                    materia.id_trayecto.nombre
                    if materia.id_trayecto
                    else None
                )
            },

            "fecha_calificacion": (
                primera_calificacion.fecha_promedio.strftime("%Y-%m-%d")
                if primera_calificacion.fecha_promedio
                else None
            ),

            "calificaciones": datos
        })

@transaction.atomic
def mod_not_acad(request):
    if request.method != "POST":
        return render(request, "modificar_notas_academicas.html")

    def respuesta(icon, title, descripcion, estado="fallo"):
        return JsonResponse({
            "estado": estado,
            "icon": icon,
            "title": title,
            "descripcion": descripcion
        })

    nucleo = request.POST.get("nucleo_asignado")
    pnf = request.POST.get("pnf_asignado")
    materia_id = request.POST.get("materia_asignada")
    id_periodo_materia = request.POST.get("id_periodo_materia")
    trayecto = request.POST.get("trayecto_academico")
    motivo = request.POST.get(
        "motivo",
        "Modificación de notas académicas."
    ).strip()

    cedula = request.session.get("cedula_usuario")

    if not cedula:
        return respuesta(
            "error",
            "Sesión",
            "No se encontró la cédula del usuario en la sesión."
        )

    usuario = Usuario.objects.filter(
        cedula_identidad=cedula
    ).first()

    if not usuario:
        return respuesta(
            "error",
            "Usuario",
            "No se encontró el usuario asociado a la cédula de la sesión."
        )

    datos = {
        "nucleo": (
            "Núcleo",
            "Debe seleccionar el núcleo."
        ),
        "pnf": (
            "P.N.F",
            "Debe seleccionar el P.N.F."
        ),
        "materia_id": (
            "Materia",
            "Debe seleccionar la materia."
        ),
        "id_periodo_materia": (
            "Período Académico",
            "Debe seleccionar el período académico."
        ),
        "trayecto": (
            "Trayecto",
            "Debe seleccionar el trayecto."
        )
    }

    valores = {
        "nucleo": nucleo,
        "pnf": pnf,
        "materia_id": materia_id,
        "id_periodo_materia": id_periodo_materia,
        "trayecto": trayecto
    }

    for campo, valor in valores.items():
        if not valor:
            titulo, descripcion = datos[campo]
            return respuesta(
                "error",
                titulo,
                descripcion
            )

    calificaciones = {}
    asistencias = {}

    for nombre, valor in request.POST.items():
        if nombre.startswith("calificacion_"):
            partes = nombre.split("_")

            if len(partes) != 3:
                continue

            estudiante_id = partes[1]
            unidad = partes[2]
            valor = valor.strip()

            if not valor:
                return respuesta(
                    "warning",
                    "Campo vacío",
                    f"La calificación de la unidad {unidad} "
                    f"del estudiante {estudiante_id} está vacía."
                )

            calificaciones.setdefault(
                estudiante_id,
                {}
            )[unidad] = valor

        elif nombre.startswith("asistencia_"):
            partes = nombre.split("_")

            if len(partes) != 2:
                continue

            estudiante_id = partes[1]
            valor = valor.strip()

            if not valor:
                return respuesta(
                    "warning",
                    "Campo vacío",
                    f"La asistencia del estudiante "
                    f"{estudiante_id} está vacía."
                )

            asistencias[estudiante_id] = valor

    if not calificaciones:
        return respuesta(
            "warning",
            "Sin calificaciones",
            "No se encontraron calificaciones para actualizar."
        )

    try:
        materia_asignacion = (
            MateriaAsignada.objects
            .select_related("materia")
            .get(
                id_materia_asignada=materia_id,
                materia__id_pnf=pnf,
                activo=True,
                docentes__docente__usuario__cedula_identidad=cedula,
                docentes__activo=True
            )
        )
    except MateriaAsignada.DoesNotExist:
        return respuesta(
            "error",
            "Materia",
            "No se encontró la materia asignada o no está asociada al docente."
        )

    try:
        periodo_materia = (
            PeriodoAcademicoMateria.objects
            .select_related(
                "periodo",
                "materia"
            )
            .get(
                periodo=id_periodo_materia,
                materia=materia_asignacion.materia
            )
        )
    except PeriodoAcademicoMateria.DoesNotExist:
        return respuesta(
            "error",
            "Período",
            (
                "No existe un período académico asociado "
                "a la materia seleccionada."
            )
        )

    try:
        trayecto_obj = TrayectoAcademico.objects.get(
            nombre=trayecto
        )
    except TrayectoAcademico.DoesNotExist:
        return respuesta(
            "error",
            "Trayecto",
            "El trayecto académico seleccionado no existe."
        )

    plan = (
        PlanificacionAcademica.objects
        .filter(
            materia_asignacion=materia_asignacion,
            pnf_id=pnf,
            nucleo_id=nucleo,
            periodo_academico=periodo_materia.periodo,
            activo=True,
            estado_aceptacion="ACEPTADA"
        )
        .first()
    )

    if not plan:
        return respuesta(
            "error",
            "Plan académico",
            (
                "No se encuentra un plan de actividad académica "
                "aceptado para la materia y período seleccionado."
            )
        )

    unidades = list(
        plan.detalles.all().order_by("id_detalle")
    )

    if not unidades:
        return respuesta(
            "warning",
            "Unidades académicas",
            (
                "El plan de actividad académica "
                "no tiene unidades registradas."
            )
        )

    nombre_materia = (
        materia_asignacion.materia.nombre
        .strip()
        .lower()
    )

    es_proyecto = (
        "proyecto socio tecnológico" in nombre_materia
    )

    nota_aprobacion = (
        Decimal("16")
        if es_proyecto
        else Decimal("12")
    )

    docente_asignado = (
        DocenteAsignadoMateria.objects
        .filter(
            materia_asignada=materia_asignacion,
            activo=True
        )
        .first()
    )

    if not docente_asignado:
        return respuesta(
            "error",
            "Docente",
            (
                "No existe un docente asignado activo "
                "para la materia seleccionada."
            )
        )

    cambios_historial = []

    for estudiante_id, notas in calificaciones.items():

        estudiante = (
            Estudiante.objects
            .filter(
                id_estudiante=estudiante_id,
                nucleo_id=nucleo,
                pnf_id=pnf
            )
            .first()
        )

        if not estudiante:
            return respuesta(
                "error",
                "Estudiante",
                f"No se encontró el estudiante {estudiante_id}."
            )

        try:
            calificacion = (
                Calificaciones.objects
                .get(
                    periodo_materia=periodo_materia,
                    materia_asignada=materia_asignacion,
                    estudiante=estudiante,
                    trayecto=trayecto_obj
                )
            )
        except Calificaciones.DoesNotExist:
            return respuesta(
                "error",
                "Calificación no encontrada",
                (
                    f"No existe una calificación para "
                    f"el estudiante {estudiante_id}."
                )
            )
        except Calificaciones.MultipleObjectsReturned:
            return respuesta(
                "error",
                "Registros duplicados",
                (
                    f"Existen múltiples calificaciones "
                    f"para el estudiante {estudiante_id}."
                )
            )

        asistencia_anterior = calificacion.asistencia
        promedio_anterior = calificacion.promedio_tramo
        cambios_unidades = []

        try:
            asistencia = int(
                asistencias.get(
                    estudiante_id,
                    asistencia_anterior
                )
            )
        except (ValueError, TypeError):
            return respuesta(
                "error",
                "Asistencia inválida",
                (
                    f"La asistencia del estudiante "
                    f"{estudiante_id} no es válida."
                )
            )

        if not 0 <= asistencia <= 100:
            return respuesta(
                "error",
                "Asistencia inválida",
                (
                    f"La asistencia del estudiante "
                    f"{estudiante_id} debe estar entre 0 y 100."
                )
            )

        for numero_unidad, nota in notas.items():

            try:
                numero_unidad = int(numero_unidad)
                nota_unidad = Decimal(
                    str(nota).replace(",", ".")
                )
            except (ValueError, TypeError):
                return respuesta(
                    "error",
                    "Nota inválida",
                    (
                        f"La nota de la unidad {numero_unidad} "
                        f"del estudiante {estudiante_id} no es válida."
                    )
                )

            if not 1 <= numero_unidad <= len(unidades):
                return respuesta(
                    "error",
                    "Unidad inválida",
                    (
                        f"La unidad {numero_unidad} "
                        f"no existe en el plan académico."
                    )
                )

            if nota_unidad < 0 or nota_unidad > 20:
                return respuesta(
                    "error",
                    "Nota inválida",
                    (
                        f"La nota de la unidad {numero_unidad} "
                        f"del estudiante {estudiante_id} "
                        f"debe estar entre 0 y 20."
                    )
                )

            unidad = unidades[numero_unidad - 1]

            try:
                detalle = (
                    DetalleCalificacionesUnidad.objects
                    .get(
                        calificacion=calificacion,
                        unidad=unidad
                    )
                )
            except DetalleCalificacionesUnidad.DoesNotExist:
                return respuesta(
                    "error",
                    "Detalle no encontrado",
                    (
                        f"No existe el detalle de la unidad "
                        f"{numero_unidad} para el estudiante "
                        f"{estudiante_id}."
                    )
                )

            nota_anterior = detalle.nota_unidad

            if nota_anterior != nota_unidad:
                cambios_unidades.append({
                    "numero_unidad": numero_unidad,
                    "nota_anterior": nota_anterior,
                    "nota_nueva": nota_unidad
                })

                detalle.nota_unidad = nota_unidad

                detalle.save(
                    update_fields=["nota_unidad"]
                )

        notas_validas = list(
            DetalleCalificacionesUnidad.objects
            .filter(
                calificacion=calificacion,
                nota_unidad__isnull=False
            )
            .values_list(
                "nota_unidad",
                flat=True
            )
        )

        if not notas_validas:
            return respuesta(
                "warning",
                "Sin notas",
                (
                    f"No existen notas registradas "
                    f"para el estudiante {estudiante_id}."
                )
            )

        promedio = (
            sum(
                notas_validas,
                Decimal("0")
            ) / Decimal(len(notas_validas))
        ).quantize(
            Decimal("1"),
            rounding=ROUND_HALF_UP
        )

        if asistencia < 75:
            condicion = "REPROBADO"
        elif promedio >= nota_aprobacion:
            condicion = "APROBADO"
        elif es_proyecto:
            condicion = "REPROBADO"
        else:
            condicion = "REPARACIÓN"

        cambio_asistencia = (
            asistencia_anterior != asistencia
        )

        cambio_promedio = (
            promedio_anterior != promedio
        )

        hubo_cambio = (
            cambio_asistencia
            or cambio_promedio
            or cambios_unidades
        )

        if hubo_cambio:
            calificacion.asistencia = asistencia
            calificacion.promedio_tramo = promedio
            calificacion.condicion = condicion

            calificacion.save(
                update_fields=[
                    "asistencia",
                    "promedio_tramo",
                    "condicion"
                ]
            )

            cambios_historial.append({
                "estudiante": estudiante,
                "cambios_unidades": cambios_unidades,
                "asistencia_anterior": asistencia_anterior,
                "asistencia_nueva": asistencia,
                "promedio_anterior": promedio_anterior,
                "promedio_nuevo": promedio
            })

    if cambios_historial:
        historial = HistorialModificacionNotas.objects.create(
            docente_asignado=docente_asignado,
            periodo_academico_id=periodo_materia.periodo_id,
            trayecto=trayecto_obj,
            usuario_modifica=usuario,
            motivo=motivo or "Modificación de notas académicas."
        )

        detalles_historial = []

        for cambio in cambios_historial:

            for unidad in cambio["cambios_unidades"]:

                detalles_historial.append(
                    HistorialDetalleNota(
                        historial=historial,
                        estudiante=cambio["estudiante"],
                        numero_unidad=unidad["numero_unidad"],
                        nota_anterior=unidad["nota_anterior"],
                        nota_nueva=unidad["nota_nueva"],
                        asistencia_anterior=None,
                        asistencia_nueva=None,
                        promedio_anterior=cambio["promedio_anterior"],
                        promedio_nuevo=cambio["promedio_nuevo"]
                    )
                )

            if (
                not cambio["cambios_unidades"]
                and cambio["asistencia_anterior"] != cambio["asistencia_nueva"]
            ):
                detalles_historial.append(
                    HistorialDetalleNota(
                        historial=historial,
                        estudiante=cambio["estudiante"],
                        numero_unidad=None,
                        nota_anterior=None,
                        nota_nueva=None,
                        asistencia_anterior=cambio["asistencia_anterior"],
                        asistencia_nueva=cambio["asistencia_nueva"],
                        promedio_anterior=cambio["promedio_anterior"],
                        promedio_nuevo=cambio["promedio_nuevo"]
                    )
                )

        if detalles_historial:
            HistorialDetalleNota.objects.bulk_create(
                detalles_historial
            )

    return respuesta(
        "success",
        "Éxito",
        (
            "Se actualizaron las notas y se generó "
            "el respaldo de la modificación."
            if cambios_historial
            else
            "No se detectaron cambios en las notas."
        ),
        "exito"
    )

# Visualizar Notas Académicas Estudiante

def nucleos_est_asig(request):
    cedula = request.session.get("cedula_usuario")

    nucleos = (
        Estudiante.objects
        .filter(
            usuario__cedula_identidad=cedula
        )
        .values(
            "nucleo__id_nucleo",
            "nucleo__municipio",
            "nucleo__direccion"
        )
        .distinct()
    )

    return JsonResponse({
        "nucleos": [
            {
                "id_nucleo": nucleo["nucleo__id_nucleo"],
                "municipio": nucleo["nucleo__municipio"],
                "direccion": nucleo["nucleo__direccion"],
            }
            for nucleo in nucleos
        ]
    })

def pnfs_est_asig(request):
    if request.method == "POST":
        id_nucleo = request.POST.get("id_nucleo")

        pnfs = (
            PNFNucleo.objects
            .filter(
                id_nucleo_id=id_nucleo
            )
            .values(
                "id_pnf__id_pnf",
                "id_pnf__pnf",
                "id_pnf__codigo",
                "id_pnf__periodo_academico"
            )
            .distinct()
        )

        return JsonResponse({
            "pnfs": [
                {
                    "id_pnf": pnf["id_pnf__id_pnf"],
                    "pnf": pnf["id_pnf__pnf"],
                    "codigo": pnf["id_pnf__codigo"],
                    "periodo_academico": pnf["id_pnf__periodo_academico"]
                }
                for pnf in pnfs
            ]
        })

def mate_tray_est(request):
    if request.method == "POST":
        cedula = request.session.get("cedula_usuario")
        id_nucleo = request.POST.get("id_nucleo")
        id_pnf = request.POST.get("id_pnf")

        docente = (
            Docente.objects
            .select_related("usuario", "nucleo", "pnf")
            .filter(
                usuario__cedula_identidad=cedula,
                nucleo_id=id_nucleo,
                pnf_id=id_pnf,
                activo=True
            )
            .first()
        )

        if not docente:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Docente no encontrado",
                "descripcion": "El docente no está asignado al núcleo y P.N.F seleccionados."
            })

        materias = (
            MateriaAsignada.objects
            .select_related(
                "materia",
                "materia__id_pnf",
                "materia__id_trayecto"
            )
            .filter(
                activo=True,
                docentes__docente=docente,
                docentes__activo=True,
                materia__id_pnf_id=id_pnf,
                calificaciones__isnull=False
            )
            .values(
                "id_materia_asignada",
                "materia__nombre",
                "materia__codigo",
                "materia__id_trayecto"
            )
            .distinct()
            .order_by("materia__nombre")
        )

        materias_lista = [
            {
                "id_materia_asignada": materia["id_materia_asignada"],
                "nombre_materia": materia["materia__nombre"],
                "codigo_materia": materia["materia__codigo"],
                "trayecto_materia": materia["materia__id_trayecto"]
            }
            for materia in materias
        ]

        return JsonResponse({
            "estado": "exito",
            "materias": materias_lista
        })

def plan_act_est(request):
    if request.method == "POST":
        cedula = request.session.get("cedula_usuario")
        id_nucleo = request.POST.get("id_nucleo")
        id_pnf = request.POST.get("id_pnf")
        id_materia = request.POST.get("id_materia")

        if not id_nucleo or not id_pnf or not id_materia:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Error",
                "descripcion": "Debe indicar el núcleo, PNF y materia"
            })

        # BUSCAR ESTUDIANTE
        estudiante = (
            Estudiante.objects
            .filter(
                usuario__cedula_identidad=cedula,
                nucleo_id=id_nucleo,
                pnf_id=id_pnf
            )
            .first()
        )

        if not estudiante:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Error",
                "descripcion": "El estudiante no está registrado en el núcleo y P.N.F seleccionado"
            })

        # VERIFICAR ESTATUS DEL ESTUDIANTE
        estatus_estudiante = (
            EstatusEstudiante.objects
            .filter(estudiante=estudiante)
            .order_by("-fecha_ingreso")
            .first()
        )

        if not estatus_estudiante:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Error",
                "descripcion": "El estudiante no fue aceptado por el P.N.F"
            })

        if (estatus_estudiante.estado != "Activo" or estatus_estudiante.estatus != "Inscrito(a)"):
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Error",
                "descripcion": "El estudiante no se encuentra activo o inscrito en el P.N.F"
            })

        # BUSCAR PLAN DE ACTIVIDADES
        planes = (
            PlanificacionAcademica.objects
            .filter(
                pnf_id=id_pnf,
                nucleo_id=id_nucleo,
                materia_asignacion__materia_id=id_materia,
                activo=True,
                estado_aceptacion="ACEPTADA"
            )
            .prefetch_related(
                "detalles__evaluaciones"
            )
            .order_by("fecha_creacion")
        )

        if not planes.exists():
            return JsonResponse({
                "estado": "no_exite",
                "icon": "error",
                "title": "Sin plan de evaluación",
                "descripcion": "No existe un plan de evaluación aceptado para esta materia"
            })

        # CONSTRUIR LAS UNIDADES
        unidades = []
        for plan in planes:
            for detalle in plan.detalles.all():
                evaluaciones = []
                for evaluacion in detalle.evaluaciones.all():
                    evaluaciones.append({
                        "id_evaluacion": evaluacion.id_evaluacion,
                        "metodo_evaluacion": evaluacion.metodo_evaluacion,
                        "fecha_evaluacion": evaluacion.fecha_evaluacion
                    })

                unidades.append({
                    "id_detalle": detalle.id_detalle,
                    "titulo_unidad": detalle.titulo_unidad,
                    "ponderacion": detalle.ponderacion,
                    "contenido_unidad": detalle.contenido_unidad,
                    "evaluaciones": evaluaciones
                })

        return JsonResponse({
            "estado": "exito",
            "trayecto": estatus_estudiante.trayecto,
            "unidades": unidades
        })

def eval_reg_est(request):
    if request.method == "POST":
        cedula = request.session.get("cedula_usuario")
        id_nucleo = request.POST.get("id_nucleo")
        id_pnf = request.POST.get("id_pnf")
        id_materia = request.POST.get("id_materia")

        if not cedula:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Error",
                "descripcion": "No se encontró la cédula del estudiante"
            })

        if not id_nucleo or not id_pnf or not id_materia:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Error",
                "descripcion": "Debe indicar el núcleo, PNF y materia"
            })

        # BUSCAR ESTUDIANTE
        estudiante = (
            Estudiante.objects
            .filter(
                usuario__cedula_identidad=cedula,
                nucleo_id=id_nucleo,
                pnf_id=id_pnf
            )
            .first()
        )
        if not estudiante:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Error",
                "descripcion": "El estudiante no está registrado en el núcleo y P.N.F seleccionado"
            })

        # BUSCAR CALIFICACIONES
        calificacion = (
            Calificaciones.objects
            .filter(
                estudiante=estudiante,
                materia_asignada__materia_id=id_materia,
            )
            .prefetch_related(
                "detalles_unidad__unidad"
            )
            .first()
        )

        # TODAVÍA NO TIENE CALIFICACIONES
        if not calificacion:
            return JsonResponse({
                "estado": "exito",
                "registradas": False,
                "evaluaciones": []
            })

        # OBTENER DETALLES DE LAS UNIDADES
        detalles = calificacion.detalles_unidad.all()

        evaluaciones = []
        for detalle in detalles:
            evaluaciones.append({
                "id_detalle": detalle.id_detalle_calificaciones_unidad,
                "id_unidad": detalle.unidad.id_detalle,
                "titulo_unidad": detalle.unidad.titulo_unidad,
                "nota_unidad": detalle.nota_unidad,
                "fecha_calificacion": detalle.fecha_calificacion
            })

        return JsonResponse({
            "estado": "exito",
            "registradas": True,
            "promedio_tramo": calificacion.promedio_tramo,
            "asistencia": calificacion.asistencia,
            "condicion": calificacion.condicion,
            "trayecto": calificacion.trayecto,
            "evaluaciones": evaluaciones
        })

def info_acad_est(request):
    return render(request, "info_academica_estudiante.html")
