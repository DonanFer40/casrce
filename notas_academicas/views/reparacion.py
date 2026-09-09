from django.shortcuts import render
from django.http import JsonResponse
from django.db import transaction
from django.db.models import Prefetch
from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP, InvalidOperation
from django.utils import timezone
from django.db.models import Exists, OuterRef, Q

import json
from datetime import date

from inicio_sesion.models import MateriaAsignada, CalendarioPeriodo, TrayectoAcademico, PeriodoAcademico, Usuario, Pnf, PNFNucleo, Estudiante, EstatusEstudiante, CalendarioAcademico, Nucleos, PeriodoAcademicoMateria, Materia, Docente, DocenteAsignadoMateria

from notas_academicas.models import ModificacionReparacion, DetalleModificacionReparacion, EvaluacionReparacion, DetalleEvaluacionReparacion, PlanificacionAcademica, DetallePlanificacion, HistorialTrayectoEstudiante, HistorialDetalleNota, HistorialModificacionNotas, DetalleEvaluacion, PromedioFinal, Reparacion, Calificaciones, DetalleCalificacionesUnidad

# Evaluaciones Reparación

# Registrar

def mat_rep_not(request):
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
            "descripcion": "Faltan datos requeridos para realizar la consulta."
        })

    fecha_actual = timezone.localdate()
    año_actual = fecha_actual.year

    # 1. Obtener los calendarios de carga de notas activos
    # Obtener periodo académico Reparación activo

    periodo_reparacion = PeriodoAcademico.objects.filter(
        nombre__iexact="Reparación"
    ).first()


    if not periodo_reparacion:
        return JsonResponse({
            "estado": "fallo",
            "title": "Error",
            "icon": "error",
            "descripcion": "No existe configurado el periodo académico Reparación."
        })


    calendarios_periodos = (
        CalendarioPeriodo.objects
        .filter(
            periodo=periodo_reparacion,
            calendario__tipo="PERIODO",
            calendario__activo=True,
            calendario__fecha_inicio__lte=fecha_actual,
            calendario__fecha_final__gte=fecha_actual,
            calendario__fecha_inicio__year=año_actual,
        )
        .select_related(
            "periodo",
            "calendario"
        )
    )

    if not calendarios_periodos.exists():
        return JsonResponse({
            "estado": "exito",
            "materias": [],
            "periodos_actuales": [],
            "mensaje": "Actualmente no existe un período de Reparación habilitado."
        })

    materias_asignadas = (
        DocenteAsignadoMateria.objects
        .filter(
            docente__usuario__cedula_identidad=cedula,
            docente__nucleo_id=nucleo,
            docente__pnf_id=pnf,
            activo=True,
            materia_asignada__activo=True,

            # Tiene estudiantes reprobados
            materia_asignada__promedios_finales__estado="REPROBADO",
            materia_asignada__promedios_finales__fecha_promedio__year=año_actual,
            materia_asignada__promedios_finales__promedio_final__gte=6.0,
            materia_asignada__promedios_finales__asistencia__gte=75.0,
        )
        .exclude(
            materia_asignada__evaluaciones_reparacion_materia__fecha_creacion__year=año_actual,
            materia_asignada__evaluaciones_reparacion_materia__activo=True
        )
        .exclude(
            Q(materia_asignada__materia__tipo_materia__iexact="Electiva") |
            Q(materia_asignada__materia__id_trayecto__nombre__iexact="Trayecto Inicial") |
            Q(materia_asignada__materia__nombre__icontains="proyecto socio tecnológico") |
            Q(materia_asignada__materia__nombre__icontains="proyecto sociotecnologico") |
            Q(materia_asignada__materia__nombre__icontains="proyecto sociointegrador")
        )
        .select_related(
            "materia_asignada",
            "materia_asignada__materia",
            "materia_asignada__materia__id_trayecto",
        )
        .distinct()
    )
    # 3. Construir la lista de respuesta
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

def reg_eval_rep(request): 
    if request.method == "POST":
        id_nucleo = request.POST.get("nucleo_asignado")
        id_pnf = request.POST.get("pnf_asignado")
        id_materia_asignada = request.POST.get("materia_asignada")

        tipos_evaluacion = request.POST.getlist("tipo_evaluacion[]")
        porcentajes = request.POST.getlist("porcentaje[]")

        controles = [
            (id_nucleo, "Núcleo", "Seleccione uno de los nucleos"),
            (id_pnf, "P.N.F", "Seleccione uno de los P.N.F"),
            (id_materia_asignada, "materia Asignación", "Seleccione uno de las materias"),
        ]

        for value, field_name, error_message in controles:
            if not value:
                return JsonResponse({
                    "estado": "fallo",
                    "icon": "warning",
                    "title": field_name,
                    "descripcion": error_message
                })

        # Validar que existan evaluaciones
        if not tipos_evaluacion:
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Evaluación",
                "descripcion": "Debe registrar al menos un tipo de evaluación."
            })


        # Validar tipos de evaluación vacíos
        for i, tipo in enumerate(tipos_evaluacion):

            if not tipo or tipo.strip() == "":
                return JsonResponse({
                    "estado": "fallo",
                    "icon": "warning",
                    "title": "Tipo de evaluación",
                    "descripcion": f"Debe seleccionar el tipo de evaluación {i + 1}."
                })
            
        porcentajes_numericos = []
        for p in porcentajes:
            try:
                val = int(p)
                if val < 10:
                    return JsonResponse({
                        "estado": "fallo",
                        "title": "Error de Validación",
                        "icon": "warning",
                        "descripcion": "Cada evaluación debe tener un porcentaje mínimo de 10%."
                    })
                porcentajes_numericos.append(val)
            except (ValueError, TypeError):
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Error",
                    "icon": "error",
                    "descripcion": "Los porcentajes ingresados deben ser números válidos."
                })

        if sum(porcentajes_numericos) != 100:
            return JsonResponse({
                "estado": "fallo",
                "title": "Error de Validación",
                "icon": "warning",
                "descripcion": "La suma total de los porcentajes debe ser exactamente 100%."
            })

        fecha_actual = timezone.localdate()
        año_actual = fecha_actual.year

        registrados = EvaluacionReparacion.objects.filter(
            materia_asignacion_id=id_materia_asignada,
            fecha_creacion__year=año_actual
        ).exists()
        if registrados:
            return JsonResponse({
                "estado": "fallo",
                "title": "Materia Ya Registrada",
                "icon": "info",
                "descripcion": "Esta materia ya cuenta con evaluaciones de reparación registradas para el año en curso."
            })

        try:
            with transaction.atomic():
                evaluacion = EvaluacionReparacion.objects.create(
                    pnf_id=id_pnf,
                    nucleo_id=id_nucleo,
                    materia_asignacion_id=id_materia_asignada
                )

                for tipo, porcentaje in zip(tipos_evaluacion, porcentajes_numericos):
                    DetalleEvaluacionReparacion.objects.create(
                        evaluacion_reparacion=evaluacion,
                        tipo_evaluacion=tipo,
                        porcentaje=porcentaje
                    )
            return JsonResponse({
                "estado": "exito",
                "title": "¡Éxito!",
                "icon": "success",
                "descripcion": "Evaluación de reparación registrada exitosamente."
            })
        except Exception as e:
            return JsonResponse({
                "estado": "fallo",
                "title": "Error en el Servidor",
                "icon": "error",
                "descripcion": str(e)
            })  
         
    return render(request, "registrar_examen_reparacion.html")

# Visualizar

def dato_eval_rep(request):

    cedula = request.session.get("cedula_usuario")

    if not cedula:
        return JsonResponse({
            "estado": "fallo",
            "title": "Sesión no válida",
            "icon": "warning",
            "descripcion": "No se pudo identificar al docente."
        })

    try:
        docente = Docente.objects.get(
            usuario__cedula_identidad=cedula,
            activo=True
        )
    except Docente.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "title": "Docente no encontrado",
            "icon": "warning",
            "descripcion": "No existe un docente activo asociado a la sesión actual."
        })
    except Docente.MultipleObjectsReturned:
        return JsonResponse({
            "estado": "fallo",
            "title": "Error",
            "icon": "error",
            "descripcion": "Se encontraron múltiples registros de docente para la cédula indicada."
        })

    evaluaciones = (
        EvaluacionReparacion.objects
        .filter(
            activo=True,

            # La materia de la evaluación debe estar asignada
            # al docente que inició sesión
            materia_asignacion__docentes__docente=docente,

            # La asignación del docente debe estar activa
            materia_asignacion__docentes__activo=True
        )
        .select_related(
            "pnf",
            "nucleo",
            "materia_asignacion__materia"
        )
        .prefetch_related(
            "detalles"
        )
        .distinct()
    )

    lista_evaluaciones = []

    for evaluacion in evaluaciones:

        detalles = []

        for detalle in evaluacion.detalles.all():
            detalles.append({
                "id_detalle": detalle.id_detalle_reparacion,
                "tipo_evaluacion": detalle.tipo_evaluacion,
                "tipo_nombre": detalle.get_tipo_evaluacion_display(),
                "porcentaje": float(detalle.porcentaje)
            })

        lista_evaluaciones.append({
            "id_evaluacion": evaluacion.id_evaluacion,

            "pnf": (
                evaluacion.pnf.pnf
                if evaluacion.pnf else ""
            ),

            "nucleo": (
                evaluacion.nucleo.municipio
                if evaluacion.nucleo else ""
            ),

            "materia": (
                evaluacion.materia_asignacion.materia.nombre
                if evaluacion.materia_asignacion
                and evaluacion.materia_asignacion.materia
                else ""
            ),

            "fecha_creacion": (
                evaluacion.fecha_creacion.strftime("%Y-%m-%d")
            ),

            "activo": evaluacion.activo,

            "evaluaciones": detalles
        })

    return JsonResponse({
        "estado": "exito",
        "title": "Correcto",
        "icon": "success",
        "descripcion": "Datos cargados correctamente.",
        "registros": lista_evaluaciones
    })

def vis_eval_rep(request):
    return render(request, "visualizar_evaluaciones_reparar.html")

# Modificar

def mat_reg_eval(request):
    if request.method != "POST":
        return JsonResponse({
            "estado": "fallo",
            "title": "Error",
            "icon": "error",
            "descripcion": "Método de solicitud no permitido."
        }, status=405)

    pnf = request.POST.get("id_pnf")
    nucleo = request.POST.get("id_nucleo")

    if not all([pnf, nucleo]):
        return JsonResponse({
            "estado": "fallo",
            "title": "Error",
            "icon": "error",
            "descripcion": "Faltan datos requeridos."
        })


    fecha_actual = timezone.localdate()
    año_actual = fecha_actual.year


    # Obtener período académico Reparación
    periodo_reparacion = PeriodoAcademico.objects.filter(
        nombre__iexact="Reparación"
    ).first()


    if not periodo_reparacion:
        return JsonResponse({
            "estado": "exito",
            "materias": [],
            "periodos_actuales": [],
            "mensaje": "No existe el período académico Reparación."
        })


    # Validar calendario del período Reparación
    calendarios_reparacion = (
        CalendarioPeriodo.objects
        .filter(
            periodo=periodo_reparacion,
            calendario__tipo="PERIODO",
            calendario__activo=True,
            calendario__fecha_inicio__lte=fecha_actual,
            calendario__fecha_final__gte=fecha_actual,
            calendario__fecha_inicio__year=año_actual
        )
        .select_related(
            "periodo",
            "calendario"
        )
    )


    if not calendarios_reparacion.exists():
        return JsonResponse({
            "estado": "exito",
            "materias": [],
            "periodos_actuales": [],
            "mensaje": "Actualmente no existe un período de reparación habilitado."
        })


    # Evaluaciones registradas para modificación
    evaluaciones = (
        EvaluacionReparacion.objects
        .filter(
            pnf_id=pnf,
            nucleo_id=nucleo,
            activo=True
        )
        .select_related(
            "materia_asignacion__materia",
            "materia_asignacion__materia__id_trayecto"
        )
        .distinct()
    )


    lista_materias = []


    for evaluacion in evaluaciones:

        materia_asignada = evaluacion.materia_asignacion

        if materia_asignada:

            materia = materia_asignada.materia


            lista_materias.append({

                "id_materia_asignada": materia_asignada.id_materia_asignada,

                "id_materia": materia.id_materia,

                "nombre": materia.nombre,

                "id_trayecto": (
                    materia.id_trayecto.id_periodo_academico
                    if materia.id_trayecto else None
                ),

                "trayecto": (
                    materia.id_trayecto.nombre
                    if materia.id_trayecto else ""
                )

            })


    return JsonResponse({

        "estado": "exito",

        "materias": lista_materias,

        "periodos_actuales": [

            {
                "id_periodo": cp.periodo.id_periodo_academico,
                "nombre": cp.periodo.nombre
            }

            for cp in calendarios_reparacion

        ]

    })

def eval_reg_rep(request):
    if request.method != "POST":
        return JsonResponse({
            "estado": "fallo",
            "title": "Error",
            "icon": "error",
            "descripcion": "Método de solicitud no permitido."
        })

    pnf = request.POST.get("id_pnf")
    nucleo = request.POST.get("id_nucleo")
    materia_asignad = request.POST.get("id_materia_asignada")

    evaluaciones = EvaluacionReparacion.objects.filter(
        pnf_id=pnf,
        nucleo_id=nucleo,
        materia_asignacion_id=materia_asignad,
        activo=True
    ).select_related(
        "materia_asignacion__materia"
    ).prefetch_related(
        "detalles"
    )

    lista_evaluaciones = []
    for evaluacion in evaluaciones:
        detalles = []
        for detalle in evaluacion.detalles.all():
            detalles.append({
                "id_detalle": detalle.id_detalle_reparacion,
                "tipo_evaluacion": detalle.tipo_evaluacion,
                "tipo_nombre": detalle.get_tipo_evaluacion_display(),
                "porcentaje": float(detalle.porcentaje)
            })

        lista_evaluaciones.append({
            "id_evaluacion": evaluacion.id_evaluacion,
            "id_materia_asignada": evaluacion.materia_asignacion.id_materia_asignada,
            "materia": evaluacion.materia_asignacion.materia.nombre,
            "fecha_creacion": evaluacion.fecha_creacion.strftime("%Y-%m-%d"),
            "detalles": detalles
        })

    if not lista_evaluaciones:
        return JsonResponse({
            "estado": "fallo",
            "title": "Aviso",
            "icon": "warning",
            "descripcion": "No existen evaluaciones registradas para la materia seleccionada."
        })

    return JsonResponse({
        "estado": "exito",
        "title": "Correcto",
        "icon": "success",
        "descripcion": "Evaluaciones registradas correctamente.",
        "evaluaciones": lista_evaluaciones
    })

def mod_eval_rep(request):
    if request.method == "POST":
        pnf = request.POST.get("pnf_asignado")
        nucleo = request.POST.get("nucleo_asignado")
        materia_asignado = request.POST.get("materia_asignada")

        try:
            evaluacion = EvaluacionReparacion.objects.get(
                pnf_id=pnf,
                nucleo_id=nucleo,
                materia_asignacion_id=materia_asignado,
                activo=True
            )
        except EvaluacionReparacion.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "title": "Error",
                "icon": "error",
                "descripcion": "No existe una evaluación de reparación registrada."
            })

        # No permitir cambios si ya existen notas
        if evaluacion.reparaciones.filter(calificaciones__isnull=False).exists():
            return JsonResponse({
                "estado": "fallo",
                "title": "No permitido",
                "icon": "warning",
                "descripcion": "No se puede modificar la evaluación porque ya existen calificaciones registradas."
            })

        tipos = request.POST.getlist("tipo_evaluacion[]")
        porcentajes = request.POST.getlist("porcentaje[]")

        if not tipos:
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Evaluación",
                "descripcion": "Debe registrar al menos un tipo de evaluación."
            })


        # Validar tipos de evaluación vacíos
        for i, tipo in enumerate(tipos):
            if not tipo or tipo.strip() == "":
                return JsonResponse({
                    "estado": "fallo",
                    "icon": "warning",
                    "title": "Tipo de evaluación",
                    "descripcion": f"La evaluación número {i + 1} no tiene un tipo de evaluación seleccionado. Por favor, seleccione una opción (Examen, Informe, Proyecto, Práctica u otra) para poder registrar la reparación."
                })

        if len(tipos) != len(porcentajes):
            return JsonResponse({
                "estado": "fallo",
                "title": "Error",
                "icon": "error",
                "descripcion": "Los datos de evaluación no coinciden."
            })

        # Validar máximo 3 controles
        if len(tipos) > 3:
            return JsonResponse({
                "estado": "fallo",
                "title": "Error",
                "icon": "warning",
                "descripcion": "Solo se permiten máximo tres evaluaciones."
            })

        # Validar suma porcentaje
        suma = sum(
            float(p)
            for p in porcentajes
        )

        if suma != 100:
            return JsonResponse({
                "estado": "fallo",
                "title": "Error",
                "icon": "warning",
                "descripcion": "La suma de los porcentajes debe ser 100%."
            })

        # Recrear detalles
        evaluacion.detalles.all().delete()

        for tipo, porcentaje in zip(tipos, porcentajes):

            DetalleEvaluacionReparacion.objects.create(
                evaluacion_reparacion=evaluacion,
                tipo_evaluacion=tipo,
                porcentaje=porcentaje
            )
        return JsonResponse({
            "estado": "exito",
            "title": "Correcto",
            "icon": "success",
            "descripcion": "Evaluación de reparación modificada correctamente."
        })

    return render(request, "modificar_evaluaciones_reparar.html")

# Calificaciones Reparación

# Registrar

def eval_mat_rep(request):
    if request.method == "POST":
        pnf = request.POST.get("id_pnf")
        nucleo = request.POST.get("id_nucleo")

        if not all([pnf, nucleo]):
            return JsonResponse({
                "estado": "fallo",
                "title": "Error",
                "icon": "warning",
                "descripcion": "Faltan datos requeridos."
            })


        fecha_actual = timezone.localdate()
        año_actual = fecha_actual.year

        # Validar calendario académico CARGA_NOTAS
        calendarios = (
            CalendarioPeriodo.objects
            .filter(
                calendario__tipo="CARGA_NOTAS",
                calendario__activo=True,
                calendario__fecha_inicio__lte=fecha_actual,
                calendario__fecha_final__gte=fecha_actual,
                calendario__fecha_inicio__year=año_actual,
                periodo__nombre__iexact="Reparación"
            )
            .select_related(
                "periodo",
                "calendario"
            )
        )

        if not calendarios.exists():
            return JsonResponse({
                "estado": "fallo",
                "title": "Período no disponible",
                "icon": "warning",
                "descripcion": (
                    "Actualmente no existe un calendario de carga de notas "
                    "habilitado para reparación."
                ),
                "evaluaciones": []
            })

        # Obtener evaluaciones registradas del año actual
        evaluaciones = (
            EvaluacionReparacion.objects
            .filter(
                pnf_id=pnf,
                nucleo_id=nucleo,
                activo=True,
                fecha_creacion__year=año_actual
            )
            .exclude(
                reparaciones__fecha_reparacion__year=año_actual
            )
        )
        lista_evaluaciones = []
        for evaluacion in evaluaciones:
            materia_asignada = evaluacion.materia_asignacion

            if not materia_asignada:
                continue


            materia = materia_asignada.materia

            detalles = []
            for detalle in evaluacion.detalles.all():
                detalles.append({
                    "id_detalle": detalle.id_detalle_reparacion,
                    "tipo_evaluacion": detalle.tipo_evaluacion,
                    "tipo_nombre": detalle.get_tipo_evaluacion_display(),
                    "porcentaje": float(detalle.porcentaje)
                })

            lista_evaluaciones.append({
                "id_evaluacion": evaluacion.id_evaluacion,
                "id_materia_asignada": materia_asignada.id_materia_asignada,
                "id_materia": materia.id_materia,
                "materia": materia.nombre,
                "id_trayecto": (
                    materia.id_trayecto.id_periodo_academico
                    if materia.id_trayecto else None
                ),
                "trayecto": (
                    materia.id_trayecto.nombre
                    if materia.id_trayecto else ""
                ),
                "fecha_creacion": evaluacion.fecha_creacion.strftime("%Y-%m-%d"),
                "detalles": detalles
            })

        return JsonResponse({
            "estado": "exito",
            "title": "Correcto",
            "icon": "success",
            "descripcion": "Evaluaciones de reparación cargadas correctamente.",
            "evaluaciones": lista_evaluaciones,
            "periodos_actuales": [
                {
                    "id_periodo": cp.periodo.id_periodo_academico,
                    "nombre": cp.periodo.nombre
                }
                for cp in calendarios
            ]
        })

def est_rep_not(request):
    if request.method == "POST":
        try:
            nucleo = request.POST.get("id_nucleo")
            pnf = request.POST.get("id_pnf")
            materia_asignacion = request.POST.get("id_materia_asignacion")
            trayecto = request.POST.get("id_trayecto")

            if not all([nucleo, pnf, materia_asignacion, trayecto]):
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Datos incompletos",
                    "icon": "warning",
                    "descripcion": "Faltan datos requeridos para consultar los estudiantes.",
                    "estudiantes": []
                })

            fecha_actual = timezone.localdate()
            año_actual = fecha_actual.year

            # Buscar periodo Reparación
            try:
                periodo_reparacion = PeriodoAcademico.objects.get(nombre__iexact="Reparación")
            except PeriodoAcademico.DoesNotExist:
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Error",
                    "icon": "error",
                    "descripcion": "No existe el período académico Reparación."
                })

            # Validar calendario académico activo
            calendario_reparacion = (
                CalendarioPeriodo.objects
                .filter(
                    periodo=periodo_reparacion,
                    calendario__tipo="CARGA_NOTAS",
                    calendario__activo=True,
                    calendario__fecha_inicio__lte=fecha_actual,
                    calendario__fecha_final__gte=fecha_actual,
                    calendario__fecha_inicio__year=año_actual
                )
                .select_related(
                    "periodo",
                    "calendario"
                )
                .first()
            )

            if not calendario_reparacion:
                return JsonResponse({
                    "estado": "exito",
                    "estudiantes": [],
                    "total": 0,
                    "mensaje": "Actualmente no existe un calendario de carga de notas de Reparación activo."
                })
                

            # Buscar estudiantes reprobados aptos para reparación
            reprobados = (
                PromedioFinal.objects
                .filter(
                    materia_asignacion_id=materia_asignacion,
                    trayecto_id=trayecto,

                    estudiante__nucleo_id=nucleo,
                    estudiante__pnf_id=pnf,

                    estado="REPROBADO",

                    fecha_promedio__year=año_actual,

                    # Condiciones para tener derecho a reparación
                    promedio_final__gte=6.0,
                    asistencia__gte=75.0,
                )
                .select_related(
                    "estudiante__usuario",
                    "trayecto"
                )
                .order_by(
                    "estudiante__usuario__apellidos",
                    "estudiante__usuario__nombres"
                )
            )

            estudiantes = []
            for reg in reprobados:
                usuario = reg.estudiante.usuario
                estudiantes.append({
                    "id_estudiante": reg.estudiante.id_estudiante,
                    "cedula": usuario.cedula_identidad,
                    "nombre_completo": (
                        f"{usuario.nombres} {usuario.apellidos}"
                    ),
                    "promedio_final": float(
                        reg.promedio_final
                    ),
                    "asistencia": (
                        float(reg.asistencia)
                        if reg.asistencia is not None
                        else 0.0
                    ),
                    "id_promedio_final": reg.id_promedio_final,
                    "id_trayecto": (
                        reg.trayecto.id_periodo_academico
                        if reg.trayecto else None
                    ),
                    "trayecto_nombre": (
                        reg.trayecto.nombre
                        if reg.trayecto else ""
                    )
                })

            return JsonResponse({
                "estado": "exito",
                "estudiantes": estudiantes,
                "total": len(estudiantes),
                "periodo": {
                    "id_periodo": calendario_reparacion.periodo.id_periodo_academico,
                    "nombre": calendario_reparacion.periodo.nombre
                }
            })

        except Exception as e:
            return JsonResponse({
                "estado": "fallo",
                "title": "Error de servidor",
                "icon": "error",
                "descripcion": f"Ocurrió un error inesperado: {str(e)}"
            })

def reg_rep_not(request):
    if request.method == "POST":
        try:
            nucleo = request.POST.get("nucleo_asignado")
            pnf = request.POST.get("pnf_asignado")
            materia_id = request.POST.get("materia_asignada")
            notas_json = request.POST.get("notas_reparacion")

            if not notas_json:
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Sin datos",
                    "icon": "warning",
                    "descripcion": "No se recibieron calificaciones."
                })

            lista_notas = json.loads(notas_json)
            fecha_actual = timezone.localdate()

            with transaction.atomic():
                evaluacion = (
                    EvaluacionReparacion.objects
                    .filter(
                        pnf_id=pnf,
                        nucleo_id=nucleo,
                        materia_asignacion_id=materia_id,
                        activo=True
                    )
                    .first()
                )

                if not evaluacion:
                    return JsonResponse({
                        "estado": "fallo",
                        "title": "Evaluación inexistente",
                        "icon": "warning",
                        "descripcion": "No existe una evaluación de reparación registrada para esta materia."
                    })

                for item in lista_notas:
                    estudiante = Estudiante.objects.get(pk=item["id_estudiante"])

                    nota = Decimal(item["nota"]);

                    if nota < 0 or nota > 20:
                        return JsonResponse({
                            "estado": "fallo",
                            "title": "Nota inválida",
                            "icon": "warning",
                            "descripcion": "La nota debe estar entre 0 y 20."
                        })


                    estado = (
                        "APROBADO"
                        if nota >= 12
                        else "REPROBADO"
                    )


                    Reparacion.objects.update_or_create(
                        estudiante=estudiante,
                        evaluacion_reparacion=evaluacion,
                        defaults={
                            "fecha_reparacion": fecha_actual,
                            "calificacion": nota,
                            "estado": estado
                        }
                    )

            return JsonResponse({
                "estado": "exito",
                "title": "Correcto",
                "icon": "success",
                "descripcion": "Notas de reparación registradas correctamente."

            })

        except Exception as e:
            return JsonResponse({
                "estado": "fallo",
                "title": "Error del servidor",
                "icon": "error",
                "descripcion": str(e)
            })
        
    return render(request, "registrar_reparacion.html")

# Visualizar

def mat_vis_not(request):

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
            "icon": "warning",
            "descripcion": "Faltan datos requeridos para realizar la consulta."
        })


    # Materias que tienen evaluación de reparación
    # y estudiantes con notas registradas
    evaluaciones = (
        EvaluacionReparacion.objects
        .filter(
            pnf_id=pnf,
            nucleo_id=nucleo,
            activo=True,

            # Solo materias con notas registradas
            reparaciones__calificacion__gt=0,

            # Docente asignado a la materia
            materia_asignacion__docentes__docente__usuario__cedula_identidad=cedula,

            # Docente activo
            materia_asignacion__docentes__activo=True
        )
        .select_related(
            "materia_asignacion",
            "materia_asignacion__materia",
            "materia_asignacion__materia__id_trayecto"
        )
        .distinct()
    )



    materias = []


    for evaluacion in evaluaciones:

        materia_asignada = evaluacion.materia_asignacion

        if not materia_asignada:
            continue


        materia = materia_asignada.materia


        materias.append({

            "id_evaluacion": evaluacion.id_evaluacion,

            "id_materia_asignada": materia_asignada.id_materia_asignada,

            "id_materia": materia.id_materia,

            "nombre": materia.nombre,

            "id_trayecto": (
                materia.id_trayecto.id_periodo_academico
                if materia.id_trayecto
                else None
            ),

            "trayecto": (
                materia.id_trayecto.nombre
                if materia.id_trayecto
                else ""
            )

        })


    return JsonResponse({
        "estado": "exito",
        "materias": materias,
        "total": len(materias)
    })

def fech_reg_rep(request):
    if request.method != "POST":
        return JsonResponse({
            "estado": "fallo",
            "title": "Error",
            "icon": "error",
            "descripcion": "Método de solicitud no permitido."
        })

    materia_asignacion = request.POST.get("id_materia_asignacion")

    if not materia_asignacion:
        return JsonResponse({
            "estado": "fallo",
            "title": "Error",
            "icon": "error",
            "descripcion": "Debe seleccionar una materia válida."
        })

    try:

        fechas_unicas = (
            Reparacion.objects
            .filter(
                evaluacion_reparacion__materia_asignacion_id=materia_asignacion,
                calificacion__isnull=False
            )
            .dates(
                "fecha_reparacion",
                "day",
                order="DESC"
            )
        )


        if not fechas_unicas:
            return JsonResponse({
                "estado": "exito",
                "fechas": [],
                "descripcion": "No hay registros de reparación para esta materia."
            })


        fechas_formateadas = [
            {
                "fecha_iso": fecha.strftime("%Y-%m-%d"),
                "fecha_mostrar": fecha.strftime("%d/%m/%Y"),
                "año": fecha.year
            }
            for fecha in fechas_unicas
        ]


        return JsonResponse({
            "estado": "exito",
            "fechas": fechas_formateadas
        })


    except Exception as e:
        return JsonResponse({
            "estado": "fallo",
            "title": "Error de Consulta",
            "icon": "error",
            "descripcion": str(e)
        })
    
def reg_est_rep(request):
    if request.method != "POST":
        return JsonResponse({
            "estado": "fallo",
            "title": "Error",
            "icon": "error",
            "descripcion": "Método de solicitud no permitido."
        })


    nucleo = request.POST.get("id_nucleo")
    pnf = request.POST.get("id_pnf")
    materia_asignacion = request.POST.get("id_materia_asignacion")
    trayecto = request.POST.get("id_trayecto")
    fecha_reparacion = request.POST.get("fecha_reparacion")


    if not all([
        nucleo,
        pnf,
        materia_asignacion,
        trayecto,
        fecha_reparacion
    ]):
        return JsonResponse({
            "estado": "fallo",
            "title": "Error",
            "icon": "error",
            "descripcion": "Faltan datos requeridos (incluida la fecha) para consultar los estudiantes."
        })


    try:

        reparaciones = (
            Reparacion.objects
            .filter(
                evaluacion_reparacion__materia_asignacion_id=materia_asignacion,

                evaluacion_reparacion__materia_asignacion__materia__id_trayecto_id=trayecto,

                estudiante__nucleo_id=nucleo,

                estudiante__pnf_id=pnf,

                fecha_reparacion=fecha_reparacion
            )
            .select_related(
                "estudiante__usuario",
                "evaluacion_reparacion__materia_asignacion__materia"
            )
            .order_by(
                "estudiante__usuario__apellidos",
                "estudiante__usuario__nombres"
            )
        )


        if not reparaciones.exists():

            return JsonResponse({
                "estado": "exito",
                "estudiantes": [],
                "descripcion": "No se encontraron calificaciones de reparación en la fecha seleccionada."
            })


        estudiantes = []


        for rep in reparaciones:

            estudiante = rep.estudiante
            usuario = estudiante.usuario


            estudiantes.append({

                "id_reparacion": rep.id_reparacion,

                "id_estudiante": estudiante.id_estudiante,

                "cedula": usuario.cedula_identidad,

                "nombre_completo": (
                    f"{usuario.nombres} {usuario.apellidos}"
                ).strip(),

                "calificacion": (
                    float(rep.calificacion)
                    if rep.calificacion is not None
                    else 0
                ),

                "fecha_reparacion": (
                    rep.fecha_reparacion.strftime("%d/%m/%Y")
                    if rep.fecha_reparacion
                    else ""
                ),

                "estado_reparacion": rep.estado

            })


        return JsonResponse({
            "estado": "exito",
            "estudiantes": estudiantes
        })


    except Exception as e:

        return JsonResponse({
            "estado": "fallo",
            "title": "Error de Consulta",
            "icon": "error",
            "descripcion": str(e)
        })
    
def vis_rep_not(request):
    return render(request, "visualizar_reparacion.html")

# Modificar Reparaciones Registradas

def mod_mat_rep_reg(request):

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
            "descripcion": "Faltan datos requeridos para realizar la consulta."
        })


    fecha_actual = timezone.localdate()
    año_actual = fecha_actual.year


    # Validar calendario CARGA_NOTAS Reparación
    calendarios_periodos = (
        CalendarioPeriodo.objects
        .filter(
            calendario__tipo="CARGA_NOTAS",
            calendario__activo=True,
            calendario__fecha_inicio__lte=fecha_actual,
            calendario__fecha_final__gte=fecha_actual,
            calendario__fecha_inicio__year=año_actual,
            periodo__nombre__iexact="Reparación"
        )
        .select_related(
            "periodo",
            "calendario"
        )
    )


    if not calendarios_periodos.exists():

        return JsonResponse({
            "estado": "exito",
            "materias": [],
            "periodos_actuales": [],
            "mensaje": "Actualmente no existe un calendario de carga de notas habilitado para reparación."
        })



    # Materias que ya tienen notas de reparación registradas
    materias_reparacion = (
        Reparacion.objects
        .filter(
            calificacion__isnull=False,
            evaluacion_reparacion__activo=True
        )
        .values_list(
            "evaluacion_reparacion__materia_asignacion_id",
            flat=True
        )
        .distinct()
    )



    if not materias_reparacion.exists():

        return JsonResponse({
            "estado": "exito",
            "materias": [],
            "periodos_actuales": [
                {
                    "id_periodo": cp.periodo.id_periodo_academico,
                    "nombre": cp.periodo.nombre
                }
                for cp in calendarios_periodos
            ],
            "mensaje": "No existen materias con notas de reparación registradas para modificar."
        })



    # Materias del docente con reparación registrada
    materias_asignadas = (
        DocenteAsignadoMateria.objects
        .filter(
            docente__usuario__cedula_identidad=cedula,
            docente__nucleo_id=nucleo,
            docente__pnf_id=pnf,

            activo=True,

            materia_asignada__activo=True,

            materia_asignada_id__in=materias_reparacion
        )
        .exclude(
            materia_asignada__materia__tipo_materia__iexact="Electiva"
        )
        .exclude(
            materia_asignada__materia__id_trayecto__nombre__iexact="Trayecto Inicial"
        )
        .select_related(
            "materia_asignada__materia",
            "materia_asignada__materia__id_trayecto"
        )
        .distinct()
    )



    materias = []


    for asignacion in materias_asignadas:

        materia_asignada = asignacion.materia_asignada
        materia = materia_asignada.materia


        materias.append({

            "id_materia_asignada": materia_asignada.id_materia_asignada,

            "id_materia": materia.id_materia,

            "nombre": materia.nombre,

            "id_trayecto": (
                materia.id_trayecto.id_periodo_academico
                if materia.id_trayecto
                else None
            ),

            "trayecto": (
                materia.id_trayecto.nombre
                if materia.id_trayecto
                else ""
            )

        })



    return JsonResponse({

        "estado": "exito",

        "materias": materias,

        "periodos_actuales": [
            {
                "id_periodo": cp.periodo.id_periodo_academico,
                "nombre": cp.periodo.nombre
            }
            for cp in calendarios_periodos
        ]

    })

def mod_not_rep_reg(request):

    if request.method != "POST":
        return JsonResponse({
            "estado": "fallo",
            "title": "Error",
            "icon": "error",
            "descripcion": "Método de solicitud no permitido."
        })


    nucleo = request.POST.get("id_nucleo")
    pnf = request.POST.get("id_pnf")
    materia_asignacion = request.POST.get("id_materia_asignacion")
    trayecto = request.POST.get("id_trayecto")
    cedula = request.session.get("cedula_usuario")


    if not all([
        nucleo,
        pnf,
        cedula,
        materia_asignacion,
        trayecto
    ]):
        return JsonResponse({
            "estado": "fallo",
            "title": "Error",
            "icon": "error",
            "descripcion": "Faltan datos requeridos para consultar los estudiantes en reparación."
        })


    try:

        reparaciones = (
            Reparacion.objects
            .filter(

                # Materia por evaluación de reparación
                evaluacion_reparacion__materia_asignacion_id=materia_asignacion,

                # Trayecto por materia
                evaluacion_reparacion__materia_asignacion__materia__id_trayecto_id=trayecto,

                # Ubicación académica del estudiante
                estudiante__nucleo_id=nucleo,
                estudiante__pnf_id=pnf

            )
            .select_related(
                "estudiante__usuario",
                "evaluacion_reparacion__materia_asignacion__materia",
                "evaluacion_reparacion__materia_asignacion__materia__id_trayecto"
            )
            .order_by(
                "estudiante__usuario__apellidos",
                "estudiante__usuario__nombres"
            )
        )


        if not reparaciones.exists():

            return JsonResponse({
                "estado": "exito",
                "estudiantes": [],
                "descripcion": "No se encontraron estudiantes registrados en reparación para esta materia."
            })


        estudiantes = []


        for rep in reparaciones:

            estudiante = rep.estudiante
            usuario = estudiante.usuario

            materia = (
                rep.evaluacion_reparacion
                .materia_asignacion
                .materia
            )


            estudiantes.append({

                "id_reparacion": rep.id_reparacion,

                "id_estudiante": estudiante.id_estudiante,

                "cedula": usuario.cedula_identidad,

                "nombre_completo": (
                    f"{usuario.nombres} {usuario.apellidos}"
                ).strip(),

                "calificacion": (
                    float(rep.calificacion)
                    if rep.calificacion is not None
                    else 0
                ),

                "estado_reparacion": rep.estado,

                "fecha_reparacion": (
                    rep.fecha_reparacion.strftime("%Y-%m-%d")
                    if rep.fecha_reparacion
                    else ""
                ),

                "trayecto_nombre": (
                    materia.id_trayecto.nombre
                    if materia.id_trayecto
                    else ""
                )

            })


        return JsonResponse({

            "estado": "exito",

            "estudiantes": estudiantes,

            "total": len(estudiantes)

        })


    except Exception as e:

        return JsonResponse({

            "estado": "fallo",

            "title": "Error de Servidor",

            "icon": "error",

            "descripcion": (
                f"Ocurrió un error al consultar los registros: {str(e)}"
            )

        }, status=500)

def mod_rep_reg(request):

    if request.method == "GET":
        return render(request, "modificar_reparacion.html")

    if request.method != "POST":
        return JsonResponse({
            "estado": "fallo",
            "title": "Método no permitido",
            "icon": "error",
            "descripcion": "Método de solicitud no permitido."
        }, status=405)

    notas_raw = request.POST.get("notas")

    motivo = request.POST.get(
        "motivo",
        "Modificación de nota de reparación"
    ).strip()

    if not notas_raw:
        return JsonResponse({
            "estado": "fallo",
            "title": "Atención",
            "icon": "warning",
            "descripcion": "No se recibieron calificaciones para actualizar."
        })

    try:
        lista_notas = json.loads(notas_raw)

    except json.JSONDecodeError:
        return JsonResponse({
            "estado": "fallo",
            "title": "Error de formato",
            "icon": "error",
            "descripcion": "La estructura de datos enviada no es válida."
        })

    if not isinstance(lista_notas, list) or not lista_notas:
        return JsonResponse({
            "estado": "fallo",
            "title": "Atención",
            "icon": "warning",
            "descripcion": "No existen notas para modificar."
        })

    try:

        with transaction.atomic():

            # ---------------------------------------------------------
            # Obtener la primera reparación para conocer la evaluación
            # ---------------------------------------------------------

            primera_id = lista_notas[0].get("id_reparacion")

            if not primera_id:
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Datos incompletos",
                    "icon": "warning",
                    "descripcion": "No se indicó el registro de reparación."
                })

            primera_reparacion = (
                Reparacion.objects
                .select_related("evaluacion_reparacion")
                .get(pk=primera_id)
            )

            if not primera_reparacion.evaluacion_reparacion:
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Error",
                    "icon": "error",
                    "descripcion": (
                        "La reparación seleccionada no tiene una "
                        "evaluación de reparación asociada."
                    )
                })

            # ---------------------------------------------------------
            # Crear cabecera del historial
            # ---------------------------------------------------------

            modificacion = ModificacionReparacion.objects.create(
                evaluacion_reparacion=(
                    primera_reparacion.evaluacion_reparacion
                ),
                motivo=(
                    motivo
                    if motivo
                    else "Modificación de nota de reparación"
                )
            )

            cambios_realizados = 0

            # ---------------------------------------------------------
            # Procesar cada nota
            # ---------------------------------------------------------

            for item in lista_notas:

                id_reparacion = item.get("id_reparacion")

                if not id_reparacion:
                    continue

                try:
                    nueva_calificacion = Decimal(
                        str(item.get("calificacion", 0))
                    )
                except (InvalidOperation, TypeError, ValueError):
                    raise ValueError(
                        "Una de las calificaciones no tiene un valor válido."
                    )

                # -----------------------------------------------------
                # Validar rango
                # -----------------------------------------------------

                if (
                    nueva_calificacion < Decimal("0")
                    or nueva_calificacion > Decimal("20")
                ):
                    raise ValueError(
                        f"La nota {nueva_calificacion} "
                        "está fuera del rango permitido (0-20)."
                    )

                # -----------------------------------------------------
                # Obtener reparación
                # -----------------------------------------------------

                reparacion = (
                    Reparacion.objects
                    .select_related("estudiante")
                    .get(pk=id_reparacion)
                )

                nota_anterior = reparacion.calificacion
                estado_anterior = reparacion.estado

                # Si la nota anterior es NULL, tratarla como 0
                nota_anterior_decimal = (
                    nota_anterior
                    if nota_anterior is not None
                    else Decimal("0")
                )

                # -----------------------------------------------------
                # Determinar nuevo estado
                # -----------------------------------------------------

                estado_nuevo = (
                    "APROBADO"
                    if nueva_calificacion >= Decimal("12")
                    else "REPROBADO"
                )

                # -----------------------------------------------------
                # Verificar si realmente existe modificación
                # -----------------------------------------------------

                if (
                    nota_anterior_decimal != nueva_calificacion
                    or estado_anterior != estado_nuevo
                ):

                    # -------------------------------------------------
                    # Guardar historial del cambio
                    # -------------------------------------------------

                    DetalleModificacionReparacion.objects.create(
                        modificacion=modificacion,
                        reparacion=reparacion,
                        nota_anterior=nota_anterior_decimal,
                        nota_nueva=nueva_calificacion,
                        estado_anterior=estado_anterior,
                        estado_nuevo=estado_nuevo
                    )

                    # -------------------------------------------------
                    # Actualizar reparación
                    # -------------------------------------------------

                    reparacion.calificacion = nueva_calificacion
                    reparacion.estado = estado_nuevo
                    reparacion.fecha_reparacion = timezone.localdate()

                    reparacion.save(
                        update_fields=[
                            "calificacion",
                            "estado",
                            "fecha_reparacion"
                        ]
                    )

                    cambios_realizados += 1

            # ---------------------------------------------------------
            # Si no hubo ningún cambio
            # ---------------------------------------------------------

            if cambios_realizados == 0:

                modificacion.delete()

                return JsonResponse({
                    "estado": "fallo",
                    "title": "Sin cambios",
                    "icon": "info",
                    "descripcion": (
                        "No se detectaron modificaciones en las notas."
                    )
                })

        # -------------------------------------------------------------
        # Respuesta exitosa
        # -------------------------------------------------------------

        return JsonResponse({
            "estado": "exito",
            "title": "Modificación exitosa",
            "icon": "success",
            "descripcion": (
                "Las notas fueron actualizadas y el historial "
                "fue guardado correctamente."
            )
        })

    except Reparacion.DoesNotExist:

        return JsonResponse({
            "estado": "fallo",
            "title": "Error",
            "icon": "error",
            "descripcion": (
                "No se encontró uno de los registros de reparación."
            )
        })

    except ValueError as e:

        return JsonResponse({
            "estado": "fallo",
            "title": "Calificación inválida",
            "icon": "warning",
            "descripcion": str(e)
        })

    except Exception as e:

        return JsonResponse({
            "estado": "fallo",
            "title": "Error del servidor",
            "icon": "error",
            "descripcion": str(e)
        }, status=500)
        