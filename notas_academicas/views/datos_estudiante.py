from django.shortcuts import render
from django.http import JsonResponse
from django.db import transaction
from django.utils import timezone
from django.db.models import F, Exists, OuterRef, Q, Prefetch, Count 

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from inicio_sesion.models import CoordinadorPNF, ControlEstudio, TrayectoAcademico, MateriaAsignada, CalendarioPeriodo, PeriodoAcademicoMateria, Usuario, Pnf, PNFNucleo, Estudiante, EstatusEstudiante, CalendarioAcademico, Nucleos, PeriodoAcademico, Materia, Docente, DocenteAsignadoMateria

from notas_academicas.models import PlanificacionAcademica, Reparacion, DetallePlanificacion, HistorialTrayectoEstudiante, HistorialDetalleNota, HistorialModificacionNotas, DetalleEvaluacion, PromedioFinal, Calificaciones, DetalleCalificacionesUnidad

# Visualizar Notas Académicas Estudiante

def nucl_est_asig(request):
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
        cedula_usuario = request.session.get("cedula_usuario")

        if not id_nucleo or not cedula_usuario:
            return JsonResponse({
                "estado": "fallo",
                "title": "Error",
                "icon": "error",
                "descripcion": "No se pudo identificar al estudiante o al núcleo."
            })

        pnfs = (
            Estudiante.objects
            .filter(
                usuario__cedula_identidad=cedula_usuario,
                nucleo_id=id_nucleo
            )
            .values(
                "pnf__id_pnf",
                "pnf__pnf",
                "pnf__codigo",
                "pnf__periodo_academico"
            )
            .distinct()
        )

        return JsonResponse({
            "pnfs": [
                {
                    "id_pnf": pnf["pnf__id_pnf"],
                    "pnf": pnf["pnf__pnf"],
                    "codigo": pnf["pnf__codigo"],
                    "periodo_academico": pnf["pnf__periodo_academico"]
                }
                for pnf in pnfs
            ]
        })

def tray_est_curs(request):
    if request.method == "POST":
        cedula = request.session.get("cedula_usuario")
        id_nucleo = request.POST.get("id_nucleo")
        id_pnf = request.POST.get("id_pnf")

        if not cedula:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Error",
                "descripcion": "No se encontró la cédula del estudiante."
            })

        if not id_nucleo or not id_pnf:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Error",
                "descripcion": "Debe indicar el núcleo y P.N.F."
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
                "descripcion": "El estudiante no está registrado en el núcleo y P.N.F seleccionado."
            })

        # OBTENER TRAYECTOS CON CALIFICACIONES DEL ESTUDIANTE
        trayectos = (
            Calificaciones.objects
            .filter(
                estudiante=estudiante,
                trayecto__isnull=False
            )
            .values(
                "trayecto__id_periodo_academico",
                "trayecto__nombre"
            )
            .distinct()
            .order_by(
                "trayecto__id_periodo_academico"
            )
        )

        return JsonResponse({
            "estado": "exito",
            "trayectos": [
                {
                    "id_trayecto": trayecto["trayecto__id_periodo_academico"],
                    "trayecto": trayecto["trayecto__nombre"]
                }
                for trayecto in trayectos
            ]
        })

def mat_est_vist(request):
    if request.method == "POST":
        cedula = request.session.get("cedula_usuario")
        id_nucleo = request.POST.get("id_nucleo")
        id_pnf = request.POST.get("id_pnf")
        id_trayecto = request.POST.get("id_trayecto")

        if not cedula or not id_nucleo or not id_pnf or not id_trayecto:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Datos incompletos",
                "descripcion": "No se pudo identificar el estudiante, núcleo, P.N.F o trayecto."
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
                "title": "Estudiante no encontrado",
                "descripcion": "El estudiante no está registrado en el núcleo y P.N.F seleccionados."
            })

        # BUSCAR MATERIAS CURSADAS EN EL TRAYECTO
        materias = (
            MateriaAsignada.objects
            .select_related(
                "materia",
                "materia__id_pnf",
                "materia__id_trayecto"
            )
            .filter(
                activo=True,
                materia__id_pnf_id=id_pnf,
                materia__id_trayecto_id=id_trayecto,
                calificaciones_materia__estudiante=estudiante
            )
            .values(
                "id_materia_asignada",
                "materia__id_materia",
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
                "id_materia": materia["materia__id_materia"],
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

def perid_acad_mat(request):
    if request.method == "POST":
        cedula = request.session.get("cedula_usuario")
        id_nucleo = request.POST.get("id_nucleo")
        id_pnf = request.POST.get("id_pnf")
        id_trayecto = request.POST.get("id_trayecto")
        id_materia = request.POST.get("id_materia")

        if not cedula:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Error",
                "descripcion": "No se encontró la cédula del estudiante"
            })

        valores = [
            id_nucleo,
            id_pnf,
            id_trayecto,
            id_materia
        ]

        if any(valor in [None, "", "undefined", "null"] for valor in valores):
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Datos incompletos",
                "descripcion": "Debe indicar el núcleo, P.N.F., trayecto y materia."
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
                "title": "Estudiante no encontrado",
                "descripcion": "El estudiante no está registrado en el núcleo y P.N.F seleccionados."
            })

        # OBTENER LOS PERÍODOS ACADÉMICOS
        periodos = (
            Calificaciones.objects
            .filter(
                estudiante=estudiante,
                materia_asignada__materia_id=id_materia,
                trayecto_id=id_trayecto,
                periodo_materia__isnull=False
            )
            .select_related(
                "periodo_materia",
                "periodo_materia__periodo"
            )
            .values(
                "periodo_materia__periodo__id_periodo_academico",
                "periodo_materia__periodo__nombre"
            )
            .distinct()
            .order_by(
                "periodo_materia__periodo__nombre"
            )
        )

        return JsonResponse({
            "estado": "exito",
            "periodos": [
                {
                    "id_periodo": periodo[
                        "periodo_materia__periodo__id_periodo_academico"
                    ],
                    "periodo": periodo[
                        "periodo_materia__periodo__nombre"
                    ]
                }
                for periodo in periodos
            ]
        })
    
def planif_acad_est(request):
    if request.method == "POST":
        cedula = request.session.get("cedula_usuario")
        id_nucleo = request.POST.get("id_nucleo")
        id_pnf = request.POST.get("id_pnf")
        id_materia = request.POST.get("id_materia")
        id_periodo = request.POST.get("id_periodo")
        id_trayecto = request.POST.get("id_trayecto")

        if not cedula or not id_nucleo or not id_pnf or not id_materia:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Error",
                "descripcion": "Debe indicar el núcleo, PNF y materia"
            })

        if not id_periodo or not id_trayecto:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Error",
                "descripcion": "Debe indicar el trayecto y período académico"
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

        # OBTENER PLANIFICACIONES PRESENTADAS POR EL ESTUDIANTE
        planes = (
            PlanificacionAcademica.objects
            .filter(
                pnf_id=id_pnf,
                nucleo_id=id_nucleo,
                materia_asignacion__materia_id=id_materia,
                periodo_academico_id=id_periodo,
                activo=True,
                estado_aceptacion="ACEPTADA",
                calificaciones_planificacion__estudiante=estudiante,
                calificaciones_planificacion__trayecto_id=id_trayecto
            )
            .prefetch_related(
                "detalles__evaluaciones"
            )
            .distinct()
            .order_by("fecha_creacion")
        )

        if not planes.exists():
            return JsonResponse({
                "estado": "no_exite",
                "icon": "error",
                "title": "Sin plan de evaluación",
                "descripcion": "El estudiante no tiene registros de calificaciones asociados a un plan de evaluación para esta materia, trayecto y período académico"
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
                        "porcentaje_evaluacion": evaluacion.porcentaje_evaluacion,
                        "fecha_evaluacion": evaluacion.fecha_evaluacion
                    })

                unidades.append({
                    "id_planificacion": plan.id_planificacion,
                    "id_detalle": detalle.id_detalle,
                    "titulo_unidad": detalle.titulo_unidad,
                    "ponderacion": detalle.ponderacion,
                    "contenido_unidad": detalle.contenido_unidad,
                    "evaluaciones": evaluaciones
                })

        return JsonResponse({
            "estado": "exito",
            "trayecto": id_trayecto,
            "id_periodo": id_periodo,
            "unidades": unidades
        })
    
def calif_est_reg(request):
    if request.method == "POST":
        cedula = request.session.get("cedula_usuario")
        id_nucleo = request.POST.get("id_nucleo")
        id_pnf = request.POST.get("id_pnf")
        id_materia = request.POST.get("id_materia")
        id_periodo = request.POST.get("id_periodo")
        id_trayecto = request.POST.get("id_trayecto")

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

        if not id_periodo or not id_trayecto:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Error",
                "descripcion": "Debe indicar el trayecto y período académico"
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

        # BUSCAR CALIFICACIONES DEL ESTUDIANTE
        # PARA EL TRAYECTO, PERÍODO Y MATERIA SELECCIONADOS
        calificaciones = (
            Calificaciones.objects
            .filter(
                estudiante=estudiante,
                materia_asignada__materia_id=id_materia,
                trayecto_id=id_trayecto,
                periodo_materia__periodo_id=id_periodo
            )
            .select_related(
                "planificacion_academica",
                "periodo_materia",
                "periodo_materia__periodo",
                "trayecto"
            )
            .prefetch_related(
                "detalles_unidad__unidad"
            )
            .order_by(
                "trayecto_id",
                "periodo_materia_id"
            )
        )

        # TODAVÍA NO TIENE CALIFICACIONES
        if not calificaciones.exists():
            return JsonResponse({
                "estado": "exito",
                "registradas": False,
                "evaluaciones": []
            })

        evaluaciones = []

        for calificacion in calificaciones:
            detalles = []

            for detalle in calificacion.detalles_unidad.all():
                detalles.append({
                    "id_detalle": detalle.id_detalle_calificaciones_unidad,
                    "id_unidad": detalle.unidad.id_detalle,
                    "titulo_unidad": detalle.unidad.titulo_unidad,
                    "nota_unidad": detalle.nota_unidad,
                    "fecha_calificacion": detalle.fecha_calificacion
                })

            evaluaciones.append({
                "id_calificaciones": calificacion.id_calificaciones,
                "id_planificacion": calificacion.planificacion_academica_id,
                "id_periodo_materia": calificacion.periodo_materia_id,
                "id_periodo": calificacion.periodo_materia.periodo_id,
                "periodo": calificacion.periodo_materia.periodo.nombre,
                "trayecto": calificacion.trayecto_id,
                "promedio_tramo": calificacion.promedio_tramo,
                "asistencia": calificacion.asistencia,
                "condicion": calificacion.condicion,
                "fecha_promedio": calificacion.fecha_promedio,
                "detalles": detalles
            })

        return JsonResponse({
            "estado": "exito",
            "registradas": True,
            "evaluaciones": evaluaciones
        })

def info_acad_est(request):
    return render(request, "Roles/Estudiante/Calificaciones_Estudiante/info_academica_estudiante.html")

# Materias a presentar o presentado

def tray_mat_est(request):
    if request.method == "POST":
        cedula = request.session.get("cedula_usuario")
        id_nucleo = request.POST.get("id_nucleo")
        id_pnf = request.POST.get("id_pnf")

        if not cedula:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Error",
                "descripcion": "No se encontró la cédula del estudiante"
            })

        if not id_nucleo or not id_pnf:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Datos incompletos",
                "descripcion": "Debe indicar el núcleo y P.N.F."
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
                "title": "Estudiante no encontrado",
                "descripcion": "El estudiante no está registrado en el núcleo y P.N.F seleccionados."
            })

        # OBTENER TRAYECTOS QUE EL ESTUDIANTE HA CURSADO
        trayectos = (
            Calificaciones.objects
            .filter(
                estudiante=estudiante,
                trayecto__isnull=False
            )
            .select_related("trayecto")
            .values(
                "trayecto_id",
                "trayecto__nombre"
            )
            .distinct()
            .order_by("trayecto_id")
        )

        return JsonResponse({
            "estado": "exito",
            "trayectos": [
                {
                    "id_trayecto": trayecto["trayecto_id"],
                    "trayecto": trayecto["trayecto__nombre"]
                }
                for trayecto in trayectos
            ]
        })

def mat_present_est(request):
    if request.method != "POST":
        return JsonResponse({
            "estado": "fallo",
            "icon": "error",
            "title": "Método no permitido",
            "descripcion": "La solicitud debe realizarse mediante POST."
        })

    cedula = request.session.get("cedula_usuario")
    id_nucleo = request.POST.get("id_nucleo")
    id_pnf = request.POST.get("id_pnf")
    id_trayecto = request.POST.get("id_trayecto")

    if not cedula:
        return JsonResponse({
            "estado": "fallo",
            "icon": "error",
            "title": "Error",
            "descripcion": "No se encontró la cédula del estudiante."
        })

    filtros_estudiante = {
        "usuario__cedula_identidad": cedula
    }

    if id_nucleo and id_nucleo != "undefined":
        filtros_estudiante["nucleo_id"] = id_nucleo

    if id_pnf and id_pnf != "undefined":
        filtros_estudiante["pnf_id"] = id_pnf

    estudiante = (
        Estudiante.objects
        .filter(**filtros_estudiante)
        .first()
    )

    if not estudiante:
        return JsonResponse({
            "estado": "fallo",
            "icon": "error",
            "title": "Estudiante no encontrado",
            "descripcion": "No se encontró el estudiante con los datos seleccionados."
        })

    estatus = (
        EstatusEstudiante.objects
        .select_related("trayecto")
        .filter(estudiante=estudiante)
        .first()
    )

    if not estatus:
        return JsonResponse({
            "estado": "fallo",
            "icon": "error",
            "title": "Trayecto no encontrado",
            "descripcion": "El estudiante no tiene un trayecto académico registrado."
        })

    if id_trayecto and id_trayecto != "undefined":
        trayecto_id = id_trayecto
    else:
        trayecto_id = estatus.trayecto_id

    materias = (
        Materia.objects
        .select_related(
            "id_trayecto",
            "id_pnf"
        )
        .filter(
            id_pnf_id=estudiante.pnf_id,
            id_trayecto_id=trayecto_id,
            activa=True
        )
        .order_by("nombre")
    )

    trayectos = {}

    for materia in materias:

        id_trayecto_materia = materia.id_trayecto_id

        if id_trayecto_materia not in trayectos:
            trayectos[id_trayecto_materia] = {
                "id_trayecto": id_trayecto_materia,
                "trayecto": materia.id_trayecto.nombre,
                "materias": []
            }

        trayectos[id_trayecto_materia]["materias"].append({
            "id_materia": materia.id_materia,
            "nombre_materia": materia.nombre,
            "codigo_materia": materia.codigo,
            "tipo_materia": materia.tipo_materia,

            "htea": materia.htea,
            "htei": materia.htei,
            "thte": materia.thte,
            "uc": materia.uc
        })

    return JsonResponse({
        "estado": "exito",
        "trayecto_actual": {
            "id_trayecto": estatus.trayecto_id,
            "trayecto": estatus.trayecto.nombre
        },
        "trayectos": list(trayectos.values())
    })
    
def mat_vis_est(request):
    return render(request, "Roles/Estudiante/Calificaciones_Estudiante/materias_presentar.html")

# Planificación Académicas presentadas o a presentar

def tray_est_planif(request):
    if request.method == "POST":
        cedula = request.session.get("cedula_usuario")
        id_nucleo = request.POST.get("id_nucleo")
        id_pnf = request.POST.get("id_pnf")

        if not cedula:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Error",
                "descripcion": "No se encontró la cédula del estudiante."
            })

        if not id_nucleo or not id_pnf:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Datos incompletos",
                "descripcion": "Debe indicar el núcleo y P.N.F."
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
                "title": "Estudiante no encontrado",
                "descripcion": (
                    "El estudiante no está registrado en el núcleo "
                    "y P.N.F seleccionado."
                )
            })

        # OBTENER TRAYECTOS QUE TIENEN PLANIFICACIONES
        # PARA LAS MATERIAS DEL ESTUDIANTE
        trayectos = (
            PlanificacionAcademica.objects
            .filter(
                nucleo_id=id_nucleo,
                pnf_id=id_pnf,
                activo=True,
                materia_asignacion__materia__id_trayecto__isnull=False
            )
            .values(
                "materia_asignacion__materia__id_trayecto",
                "materia_asignacion__materia__id_trayecto__nombre"
            )
            .distinct()
            .order_by(
                "materia_asignacion__materia__id_trayecto"
            )
        )

        return JsonResponse({
            "estado": "exito",
            "trayectos": [
                {
                    "id_trayecto": trayecto[
                        "materia_asignacion__materia__id_trayecto"
                    ],
                    "trayecto": trayecto[
                        "materia_asignacion__materia__id_trayecto__nombre"
                    ]
                }
                for trayecto in trayectos
            ]
        })

def mat_est_planif(request):
    if request.method == "POST":
        cedula = request.session.get("cedula_usuario")
        id_nucleo = request.POST.get("id_nucleo")
        id_pnf = request.POST.get("id_pnf")
        id_trayecto = request.POST.get("id_trayecto")

        if not cedula:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Error",
                "descripcion": "No se encontró la cédula del estudiante."
            })

        if not id_nucleo or not id_pnf or not id_trayecto:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Datos incompletos",
                "descripcion": "Debe indicar el núcleo, P.N.F. y trayecto."
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
                "title": "Estudiante no encontrado",
                "descripcion": (
                    "El estudiante no está registrado en el núcleo "
                    "y P.N.F seleccionado."
                )
            })

        # OBTENER MATERIAS CON PLANIFICACIÓN
        materias = (
            PlanificacionAcademica.objects
            .filter(
                nucleo_id=id_nucleo,
                pnf_id=id_pnf,
                activo=True,
                estado_aceptacion="ACEPTADA",
                materia_asignacion__materia__id_trayecto_id=id_trayecto
            )
            .select_related(
                "materia_asignacion__materia",
                "materia_asignacion__materia__id_trayecto"
            )
            .values(
                "materia_asignacion__materia_id",
                "materia_asignacion__materia__nombre",
                "materia_asignacion__materia__codigo",
                "materia_asignacion__materia__tipo_materia",
                "materia_asignacion__materia__htea",
                "materia_asignacion__materia__htei",
                "materia_asignacion__materia__id_trayecto",
                "materia_asignacion__materia__id_trayecto__nombre"
            )
            .distinct()
            .order_by(
                "materia_asignacion__materia__nombre"
            )
        )

        materias_lista = []

        for materia in materias:
            htea = materia["materia_asignacion__materia__htea"]
            htei = materia["materia_asignacion__materia__htei"]

            thte = htea + htei
            uc = thte // 25

            materias_lista.append({
                "id_materia": materia[
                    "materia_asignacion__materia_id"
                ],
                "nombre_materia": materia[
                    "materia_asignacion__materia__nombre"
                ],
                "codigo_materia": materia[
                    "materia_asignacion__materia__codigo"
                ],
                "tipo_materia": materia[
                    "materia_asignacion__materia__tipo_materia"
                ],
                "htea": htea,
                "htei": htei,
                "thte": thte,
                "uc": uc,
                "id_trayecto": materia[
                    "materia_asignacion__materia__id_trayecto"
                ],
                "trayecto": materia[
                    "materia_asignacion__materia__id_trayecto__nombre"
                ]
            })

        return JsonResponse({
            "estado": "exito",
            "materias": materias_lista
        })

def per_aca_planif(request):
    if request.method == "POST":
        cedula = request.session.get("cedula_usuario")
        id_nucleo = request.POST.get("id_nucleo")
        id_pnf = request.POST.get("id_pnf")
        id_trayecto = request.POST.get("id_trayecto")
        id_materia = request.POST.get("id_materia")

        if not cedula:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Error",
                "descripcion": "No se encontró la cédula del estudiante."
            })

        if not all([
            id_nucleo,
            id_pnf,
            id_trayecto,
            id_materia
        ]):
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Datos incompletos",
                "descripcion": (
                    "Debe indicar el núcleo, P.N.F., trayecto y materia."
                )
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
                "title": "Estudiante no encontrado",
                "descripcion": (
                    "El estudiante no está registrado en el núcleo "
                    "y P.N.F seleccionado."
                )
            })

        # OBTENER PERÍODOS ACADÉMICOS
        periodos = (
            PlanificacionAcademica.objects
            .filter(
                nucleo_id=id_nucleo,
                pnf_id=id_pnf,
                activo=True,
                estado_aceptacion="ACEPTADA",
                materia_asignacion__materia_id=id_materia,
                materia_asignacion__materia__id_trayecto_id=id_trayecto
            )
            .select_related(
                "periodo_academico"
            )
            .values(
                "periodo_academico_id",
                "periodo_academico__nombre"
            )
            .distinct()
            .order_by(
                "periodo_academico__nombre"
            )
        )

        return JsonResponse({
            "estado": "exito",
            "periodos": [
                {
                    "id_periodo": periodo["periodo_academico_id"],
                    "periodo": periodo["periodo_academico__nombre"]
                }
                for periodo in periodos
            ]
        })

def planif_est_vis(request):
    if request.method == "POST":
        cedula = request.session.get("cedula_usuario")
        id_nucleo = request.POST.get("id_nucleo")
        id_pnf = request.POST.get("id_pnf")
        id_trayecto = request.POST.get("id_trayecto")
        id_materia = request.POST.get("id_materia")
        id_periodo = request.POST.get("id_periodo")

        if not cedula:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Error",
                "descripcion": "No se encontró la cédula del estudiante."
            })

        if not all([
            id_nucleo,
            id_pnf,
            id_trayecto,
            id_materia,
            id_periodo
        ]):
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Datos incompletos",
                "descripcion": (
                    "Debe indicar el núcleo, P.N.F., trayecto, "
                    "materia y período académico."
                )
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
                "title": "Estudiante no encontrado",
                "descripcion": (
                    "El estudiante no está registrado en el núcleo "
                    "y P.N.F seleccionado."
                )
            })

        # BUSCAR PLANIFICACIÓN ACADÉMICA
        planificaciones = (
            PlanificacionAcademica.objects
            .filter(
                nucleo_id=id_nucleo,
                pnf_id=id_pnf,
                materia_asignacion__materia_id=id_materia,
                materia_asignacion__materia__id_trayecto_id=id_trayecto,
                periodo_academico_id=id_periodo,
                activo=True,
                estado_aceptacion="ACEPTADA"
            )
            .select_related(
                "periodo_academico",
                "materia_asignacion__materia",
                "materia_asignacion__materia__id_trayecto"
            )
            .prefetch_related(
                "detalles__evaluaciones"
            )
            .order_by(
                "fecha_creacion"
            )
        )

        if not planificaciones.exists():
            return JsonResponse({
                "estado": "no_existe",
                "icon": "info",
                "title": "Sin planificación académica",
                "descripcion": (
                    "No existe una planificación académica aceptada "
                    "para la materia, trayecto y período académico seleccionados."
                ),
                "planificaciones": []
            })

        resultado = []

        for plan in planificaciones:
            detalles = []

            for detalle in plan.detalles.all():
                evaluaciones = []

                for evaluacion in detalle.evaluaciones.all():
                    evaluaciones.append({
                        "id_evaluacion": evaluacion.id_evaluacion,
                        "metodo_evaluacion": evaluacion.metodo_evaluacion,
                        "porcentaje_evaluacion": (
                            evaluacion.porcentaje_evaluacion
                        ),
                        "fecha_evaluacion": evaluacion.fecha_evaluacion
                    })

                detalles.append({
                    "id_detalle": detalle.id_detalle,
                    "titulo_unidad": detalle.titulo_unidad,
                    "ponderacion": detalle.ponderacion,
                    "contenido_unidad": detalle.contenido_unidad,
                    "evaluaciones": evaluaciones
                })

            resultado.append({
                "id_planificacion": plan.id_planificacion,
                "id_materia": (
                    plan.materia_asignacion.materia_id
                ),
                "materia": (
                    plan.materia_asignacion.materia.nombre
                ),
                "codigo_materia": (
                    plan.materia_asignacion.materia.codigo
                ),
                "id_trayecto": (
                    plan.materia_asignacion.materia.id_trayecto_id
                ),
                "trayecto": (
                    plan.materia_asignacion.materia.id_trayecto.nombre
                ),
                "id_periodo": plan.periodo_academico_id,
                "periodo": plan.periodo_academico.nombre,
                "observacion": plan.observacion,
                "fecha_creacion": plan.fecha_creacion,
                "fecha_actualizacion": plan.fecha_actualizacion,
                "detalles": detalles
            })

        return JsonResponse({
            "estado": "exito",
            "planificaciones": resultado
        })

def planif_est_reg(request):
    return render(request, "Roles/Estudiante/Calificaciones_Estudiante/planificaciones_academicas.html")
