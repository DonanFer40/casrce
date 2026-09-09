from django.shortcuts import render
from django.http import JsonResponse
from django.db import transaction
from django.db.models import Prefetch
from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP, InvalidOperation
from django.utils import timezone
from django.db.models import Exists, OuterRef
from datetime import timedelta
from datetime import datetime

from inicio_sesion.models import CalendarioPeriodo, MateriaAsignada, PeriodoAcademicoMateria, Usuario, Pnf, PNFNucleo, Estudiante, EstatusEstudiante, CalendarioAcademico, Nucleos, PeriodoAcademico, Materia, Docente, DocenteAsignadoMateria

from notas_academicas.models import PlanificacionAcademica, DetallePlanificacion, HistorialTrayectoEstudiante, HistorialDetalleNota, HistorialModificacionNotas, DetalleEvaluacion, PromedioFinal, Calificaciones, DetalleCalificacionesUnidad

# Registrar Plan de Actividades

def nucl_asig_doc(request):
    cedula = request.session.get("cedula_usuario")

    nucleos = Nucleos.objects.filter(docente__usuario__cedula_identidad=cedula).distinct()

    datos = [
        {
            "id_nucleo": nucleo.id_nucleo,
            "municipio": nucleo.municipio,
            "direccion": nucleo.direccion,
        }
        for nucleo in nucleos
    ]

    return JsonResponse({
        "estado": "exito",
        "datos": datos
    })

def pnfs_asig_doc(request):
    cedula = request.session.get("cedula_usuario")
    nucleo_asignado = request.POST.get("nucleo_asignado")

    docentes = Docente.objects.filter(usuario__cedula_identidad=cedula, nucleo_id=nucleo_asignado).values_list("pnf_id", flat=True).distinct()

    pnfs = Pnf.objects.filter(id_pnf__in=docentes, pnfnucleo__id_nucleo=nucleo_asignado).distinct()

    datos = [
        {
            "id_pnf": pnf.id_pnf,
            "pnf": pnf.pnf,
            "codigo": pnf.codigo,
            "periodo_academico": pnf.periodo_academico,
        }
        for pnf in pnfs
    ]

    return JsonResponse({
        "estado": "exito",
        "datos": datos
    })

def mat_asig_doc(request):
    id_nucleo = request.POST.get("id_nucleo")
    id_pnf = request.POST.get("id_pnf")
    cedula = request.session.get("cedula_usuario")

    docente = Docente.objects.get(
        usuario__cedula_identidad=cedula,
        nucleo_id=id_nucleo,
        pnf_id=id_pnf
    )

    asignaciones = (
        DocenteAsignadoMateria.objects
        .filter(
            docente=docente,
            activo=True,
            materia_asignada__activo=True
        )
        .select_related(
            "materia_asignada__materia"
        )
        .prefetch_related(
            "materia_asignada__materia__periodos_academicos__periodo",
            "materia_asignada__planificaciones_academicas__detalles"
        )
    )

    materias = []
    fecha_actual = timezone.localdate()

    for asignacion in asignaciones:

        materia_asignada = asignacion.materia_asignada
        materia = materia_asignada.materia

        planificaciones = materia_asignada.planificaciones_academicas.filter(
            activo=True,
            estado_aceptacion__in=["ENVIADO", "ACEPTADA"]
        )

        # PERÍODOS QUE REALMENTE TIENE ASIGNADOS ESTA MATERIA
        periodos_materia = materia.periodos_academicos.all()

        for periodo_materia in periodos_materia:
            periodo = periodo_materia.periodo

            if planificaciones.filter(periodo_academico=periodo).exists():
                continue

            calendario_periodo = (
                CalendarioPeriodo.objects
                .filter(
                    periodo=periodo,
                    calendario__tipo="PERIODO",
                    calendario__activo=True
                )
                .select_related("calendario")
                .first()
            )

            if not calendario_periodo:
                continue

            calendario = calendario_periodo.calendario

            # LOS PRIMEROS 5 DÍAS DEL PERÍODO
            fecha_inicio = calendario.fecha_inicio
            fecha_fin_5_dias = fecha_inicio + timedelta(days=4)

            # La materia solamente aparece durante estos 5 días
            if not (fecha_inicio <= fecha_actual <= fecha_fin_5_dias):
                continue

            # LA MATERIA SE PUEDE MOSTRAR NUEVAMENTE
            # AUNQUE YA EXISTA UNA PLANIFICACIÓN.
            materias.append({
                "id_materia_asignada": materia_asignada.id_materia_asignada,
                "id_materia": materia.id_materia,
                "nombre": materia.nombre,
                "codigo": materia.codigo,
                "periodo": periodo.nombre,
                "id_periodo": periodo.id_periodo_academico,
                "rol": asignacion.rol,
            })

    return JsonResponse({
        "estado": "exito",
        "datos": materias
    })

def perd_acad_reg(request):

    id_asignacion = request.POST.get("id_asignacion")

    try:
        materia_asignada = (
            MateriaAsignada.objects
            .select_related("materia")
            .get(
                id_materia_asignada=id_asignacion,
                activo=True
            )
        )

    except MateriaAsignada.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "descripcion": "La materia asignada no existe."
        })


    fecha_actual = timezone.localdate()


    calendarios = (
        CalendarioPeriodo.objects
        .filter(
            periodo__materias__materia=materia_asignada.materia,
            calendario__tipo="PERIODO",
            calendario__activo=True,
            calendario__fecha_inicio__lte=fecha_actual,
            calendario__fecha_final__gte=fecha_actual
        )
        .select_related(
            "periodo",
            "calendario"
        )
        .distinct()
    )


    resultado = []

    for item in calendarios:
        resultado.append({
            "id_periodo": item.periodo.id_periodo_academico,
            "nombre": item.periodo.nombre
        })


    return JsonResponse({
        "estado": "exito",
        "periodos": resultado
    })

def cant_und_reg(request):
    id_asignacion = request.POST.get("id_asignacion")
    id_periodo_academico = request.POST.get("id_periodo_academico")

    if not id_asignacion or not id_periodo_academico:
        return JsonResponse({
            "estado": "fallo",
            "existe_plan": False,
            "cantidad": 0,
            "puede_enviar": False,
            "descripcion": "Debe indicar la materia y el período académico."
        })

    # ============================================================
    # AÑO ACTUAL
    # ============================================================
    anio_actual = timezone.localdate().year

    # ============================================================
    # VERIFICAR QUE EL PERÍODO PERTENEZCA AL AÑO ACTUAL
    # ============================================================
    periodo_actual = (
        CalendarioPeriodo.objects
        .filter(
            periodo_id=id_periodo_academico,
            calendario__tipo="PERIODO",
            calendario__activo=True,
            calendario__fecha_inicio__year=anio_actual
        )
        .select_related("periodo", "calendario")
        .first()
    )

    # ============================================================
    # EL PERÍODO NO PERTENECE AL AÑO ACTUAL
    # ============================================================
    if not periodo_actual:
        return JsonResponse({
            "estado": "exito",
            "existe_plan": False,
            "id_plan": None,
            "id_periodo_academico": id_periodo_academico,
            "periodo": None,
            "cantidad": 0,
            "estado_aceptacion": None,
            "puede_enviar": False
        })

    # ============================================================
    # BUSCAR PLANIFICACIÓN
    #
    # IMPORTANTE:
    # fecha_creacion__year=anio_actual evita recuperar
    # una planificación creada el año pasado.
    # ============================================================
    plan = (
        PlanificacionAcademica.objects
        .filter(
            materia_asignacion_id=id_asignacion,
            periodo_academico_id=id_periodo_academico,
            fecha_creacion__year=anio_actual,
            activo=True
        )
        .select_related("periodo_academico")
        .first()
    )

    # ============================================================
    # NO EXISTE PLANIFICACIÓN PARA EL AÑO ACTUAL
    # ============================================================
    if not plan:
        return JsonResponse({
            "estado": "exito",
            "existe_plan": False,
            "id_plan": None,
            "id_periodo_academico": id_periodo_academico,
            "periodo": periodo_actual.periodo.nombre,
            "cantidad": 0,
            "estado_aceptacion": None,
            "puede_enviar": False
        })

    # ============================================================
    # CANTIDAD DE UNIDADES
    # ============================================================
    cantidad = plan.detalles.count()

    # ============================================================
    # PUEDE ENVIAR
    # ============================================================
    puede_enviar = (
        4 <= cantidad <= 6
        and plan.estado_aceptacion in [
            "BORRADOR",
            "DENEGADA"
        ]
    )

    # ============================================================
    # RESPUESTA
    # ============================================================
    return JsonResponse({
        "estado": "exito",
        "existe_plan": True,
        "id_plan": plan.id_planificacion,
        "id_periodo_academico": plan.periodo_academico_id,
        "periodo": plan.periodo_academico.nombre,
        "cantidad": cantidad,
        "estado_aceptacion": plan.estado_aceptacion,
        "puede_enviar": puede_enviar
    })

def fech_cal_mat(request):

    id_periodo = request.POST.get("id_periodo")

    if not id_periodo:
        return JsonResponse({
            "estado": "fallo",
            "icon": "error",
            "title": "Período no indicado",
            "descripcion": "Debe indicar el período académico."
        })

    anio_actual = timezone.localdate().year

    calendario_periodo = (
        CalendarioPeriodo.objects
        .filter(
            periodo_id=id_periodo,
            calendario__tipo="PERIODO",
            calendario__activo=True,
            calendario__fecha_inicio__year=anio_actual,
            calendario__fecha_final__year=anio_actual,
        )
        .select_related("periodo", "calendario")
        .order_by("calendario__fecha_inicio")
        .first()
    )

    if not calendario_periodo:
        return JsonResponse({
            "estado": "fallo",
            "icon": "error",
            "title": "Período no encontrado",
            "descripcion": (
                f"No existe un calendario académico activo "
                f"para el período seleccionado en el año {anio_actual}."
            )
        })

    calendario = calendario_periodo.calendario

    return JsonResponse({
        "estado": "exito",
        "id_periodo": calendario_periodo.periodo.id_periodo_academico,
        "periodo": calendario_periodo.periodo.nombre,
        "fecha_inicio": calendario.fecha_inicio.strftime("%Y-%m-%d"),
        "fecha_final": calendario.fecha_final.strftime("%Y-%m-%d"),
    })

def fech_reg_mat(request):
    id_materia_asignada = request.POST.get("id_materia")
    id_periodo = request.POST.get("id_periodo")

    try:
        fechas = (
            DetalleEvaluacion.objects
            .filter(
                detalle_plan__plan_academico__materia_asignacion_id=
                    id_materia_asignada,

                detalle_plan__plan_academico__periodo_academico_id=
                    id_periodo,

                detalle_plan__plan_academico__activo=True
            )
            .values_list(
                "fecha_evaluacion",
                flat=True
            )
            .distinct()
            .order_by(
                "fecha_evaluacion"
            )
        )

        return JsonResponse({
            "estado": "exito",
            "fechas": [
                fecha.strftime("%Y-%m-%d")
                for fecha in fechas
            ]
        })

    except Exception as error:
        return JsonResponse({
            "estado": "fallo",
            "icon": "error",
            "title": "Error",
            "descripcion": str(error)
        })

@transaction.atomic
def reg_pl_act(request):

    if request.method != "POST":
        return render(request, "registrar_planificacion.html")

    nulcleo_asignado = request.POST.get("nucleo_asignado")
    pnfs_asignado = request.POST.get("pnfs_asignado")
    materia_asignacion = request.POST.get("asignacion_materia")
    periodo_academico = request.POST.get("periodo_academico")

    titulo_unidad = request.POST.get("titulo_unidad", "").strip()
    contenido_unidad = request.POST.get("contenido_unidad", "").strip()

    def error(title, descripcion, icon="warning"):
        return JsonResponse({
            "estado": "fallo",
            "icon": icon,
            "title": title,
            "descripcion": descripcion
        })

    # ==========================================================
    # DATOS OBLIGATORIOS
    # ==========================================================

    for valor, titulo, mensaje in [
        (
            materia_asignacion,
            "Materia Asignada",
            "Por favor, selecciona una materia."
        ),
        (
            periodo_academico,
            "Periodo Académico",
            "Por favor, selecciona un período académico."
        ),
        (
            titulo_unidad,
            "Título de la Unidad",
            "Por favor, ingresa el título de la unidad."
        ),
        (
            contenido_unidad,
            "Contenido de la Unidad",
            "Por favor, ingresa el contenido de la unidad."
        )
    ]:
        if not valor:
            return error(titulo, mensaje)

    # ==========================================================
    # EVALUACIONES
    # ==========================================================

    try:
        cantidad_evaluaciones = int(
            request.POST.get("cantidad_evaluaciones", 0)
        )
    except (TypeError, ValueError):
        cantidad_evaluaciones = 0

    if cantidad_evaluaciones <= 0:
        return error(
            "Cantidad de Evaluaciones",
            "Debe registrar al menos una evaluación."
        )

    evaluaciones = []
    total_porcentaje = Decimal("0.00")

    for i in range(1, cantidad_evaluaciones + 1):

        metodo = request.POST.get(
            f"metodo_evaluacion_{i}",
            ""
        ).strip()

        fecha = request.POST.get(
            f"fecha_evaluacion_{i}",
            ""
        ).strip()

        porcentaje = request.POST.get(
            f"porcentaje_evaluacion_{i}",
            ""
        ).strip()

        if not metodo:
            return error(
                "Método de Evaluación",
                f"El método de evaluación {i} no puede estar vacío."
            )

        if not fecha:
            return error(
                "Fecha de Evaluación",
                f"La fecha de evaluación {i} no puede estar vacía."
            )

        try:
            fecha_obj = datetime.strptime(
                fecha,
                "%Y-%m-%d"
            ).date()
        except ValueError:
            return error(
                "Fecha de Evaluación",
                f"La fecha de evaluación {i} no tiene un formato válido."
            )

        if not porcentaje:
            return error(
                "Porcentaje de Evaluación",
                f"Debe ingresar el porcentaje de la evaluación {i}."
            )

        try:
            porcentaje_decimal = Decimal(porcentaje)
        except (InvalidOperation, ValueError):
            return error(
                "Porcentaje de Evaluación",
                f"El porcentaje de la evaluación {i} no es válido."
            )

        if porcentaje_decimal <= 0:
            return error(
                "Porcentaje de Evaluación",
                f"La evaluación {i} debe tener un porcentaje mayor que 0%."
            )

        if porcentaje_decimal > 25:
            return error(
                "Porcentaje de Evaluación",
                f"El porcentaje de la evaluación {i} no puede superar el 25%."
            )

        total_porcentaje += porcentaje_decimal

        evaluaciones.append({
            "metodo_evaluacion": metodo,
            "fecha_evaluacion": fecha_obj,
            "porcentaje_evaluacion": porcentaje_decimal
        })

    if total_porcentaje != Decimal("25.00"):
        return error(
            "Porcentaje de Evaluaciones",
            f"La suma debe ser exactamente 25%. "
            f"Actualmente suma {total_porcentaje}%."
        )

    # ==========================================================
    # SESIÓN
    # ==========================================================

    cedula = request.session.get("cedula_usuario")

    if not cedula:
        return error(
            "Sesión no válida",
            "No se encontró el usuario autenticado en la sesión."
        )

    # ==========================================================
    # DOCENTE
    # ==========================================================

    try:
        docente = (
            Docente.objects
            .select_related(
                "usuario",
                "nucleo",
                "pnf"
            )
            .get(
                usuario__cedula_identidad=cedula,
                nucleo_id=nulcleo_asignado,
                pnf_id=pnfs_asignado
            )
        )
    except Docente.DoesNotExist:
        return error(
            "Docente no encontrado",
            "El docente no está asociado al núcleo y PNF seleccionados."
        )

    # ==========================================================
    # PERÍODO
    # ==========================================================

    try:
        periodo = PeriodoAcademico.objects.get(
            pk=periodo_academico
        )
    except PeriodoAcademico.DoesNotExist:
        return error(
            "Período Académico",
            "El período académico no se encuentra registrado.",
            "error"
        )

    # ==========================================================
    # AÑO ACTUAL Y CALENDARIO
    # ==========================================================

    fecha_actual = timezone.localdate()
    anio_actual = fecha_actual.year

    calendario = (
        CalendarioPeriodo.objects
        .filter(
            periodo=periodo,
            calendario__tipo="PERIODO",
            calendario__activo=True,
            calendario__fecha_inicio__year=anio_actual
        )
        .select_related("calendario")
        .first()
    )

    if not calendario:
        return error(
            "Calendario Académico",
            f"El período {periodo.nombre} no tiene calendario "
            f"registrado para el año {anio_actual}."
        )

    fecha_inicio = calendario.calendario.fecha_inicio
    fecha_final = calendario.calendario.fecha_final

    # ==========================================================
    # FECHAS DE EVALUACIÓN
    # ==========================================================

    for i, evaluacion in enumerate(evaluaciones, 1):

        fecha_eval = evaluacion["fecha_evaluacion"]

        if fecha_eval < fecha_inicio or fecha_eval > fecha_final:
            return error(
                "Fecha de Evaluación",
                f"La fecha de la evaluación {i} debe estar "
                f"dentro del período académico."
            )

    # ==========================================================
    # PRIMEROS 5 DÍAS
    # ==========================================================

    if fecha_actual < fecha_inicio:
        return error(
            "Período no iniciado",
            f"El período {periodo.nombre} inicia el "
            f"{fecha_inicio.strftime('%d/%m/%Y')}."
        )

    if fecha_actual > fecha_inicio + timedelta(days=4):
        return error(
            "Registro cerrado",
            f"El registro de {periodo.nombre} solo está disponible "
            f"durante los primeros 5 días del período."
        )

    # ==========================================================
    # MATERIA
    # ==========================================================

    try:
        asignacion = (
            MateriaAsignada.objects
            .select_for_update()
            .select_related(
                "materia",
                "materia__id_pnf"
            )
            .get(
                pk=materia_asignacion,
                activo=True
            )
        )
    except MateriaAsignada.DoesNotExist:
        return error(
            "Materia Asignada",
            "La materia no se encuentra registrada o está inactiva.",
            "error"
        )

    if asignacion.materia.id_pnf_id != docente.pnf_id:
        return error(
            "Materia no válida",
            "La materia seleccionada no pertenece al PNF del docente."
        )
    # ==========================================================
    # PLANIFICACIÓN
    # ==========================================================

    PERIODOS_INICIALES = {
        "Inicial Trimestre",
        "Inicial Semestre"
    }

    if periodo.nombre in PERIODOS_INICIALES:

        planificacion = (
            PlanificacionAcademica.objects
            .select_for_update()
            .filter(
                pnf=docente.pnf,
                nucleo=docente.nucleo,
                materia_asignacion=asignacion,
                periodo_academico__nombre__in=PERIODOS_INICIALES,
                fecha_creacion__year=anio_actual,
                activo=True
            )
            .first()
        )

    else:

        planificacion = (
            PlanificacionAcademica.objects
            .select_for_update()
            .filter(
                pnf=docente.pnf,
                nucleo=docente.nucleo,
                materia_asignacion=asignacion,
                periodo_academico=periodo,
                fecha_creacion__year=anio_actual,
                activo=True
            )
            .first()
        )

        if planificacion:

            if planificacion.estado_aceptacion == "ACEPTADA":
                return error(
                    "Planificación aceptada",
                    "La planificación ya fue aceptada y no puede modificarse."
                )

            if planificacion.estado_aceptacion == "ENVIADO":
                return error(
                    "Planificación enviada",
                    "La planificación ya fue enviada al Coordinador."
                )

            if planificacion.estado_aceptacion not in {
                "BORRADOR",
                "DENEGADA"
            }:
                return error(
                    "Planificación no disponible",
                    "La planificación no puede modificarse."
                )
    # ==========================================================
    # CREAR PLANIFICACIÓN
    # ==========================================================

    if not planificacion:

        planificacion = PlanificacionAcademica.objects.create(
            pnf=docente.pnf,
            nucleo=docente.nucleo,
            materia_asignacion=asignacion,
            periodo_academico=periodo,
            activo=True,
            estado_aceptacion="BORRADOR"
        )

    elif planificacion.estado_aceptacion == "DENEGADA":

        planificacion.estado_aceptacion = "BORRADOR"

        planificacion.save(
            update_fields=["estado_aceptacion"]
        )

    # ==========================================================
    # MÁXIMO 6 UNIDADES
    # ==========================================================

    cantidad = (
        DetallePlanificacion.objects
        .filter(
            plan_academico__pnf=docente.pnf,
            plan_academico__nucleo=docente.nucleo,
            plan_academico__materia_asignacion=asignacion,
            plan_academico__periodo_academico=periodo,
            plan_academico__fecha_creacion__year=anio_actual,
            plan_academico__activo=True
        )
        .count()
    )

    if cantidad >= 6:
        return error(
            "Límite de unidades",
            f"La materia '{asignacion.materia.nombre}' "
            f"ya tiene registradas 6 unidades para el año {anio_actual}."
        )

    # ==========================================================
    # CREAR UNIDAD
    # ==========================================================

    detalle = DetallePlanificacion.objects.create(
        plan_academico=planificacion,
        titulo_unidad=titulo_unidad,
        contenido_unidad=contenido_unidad,
        ponderacion=Decimal("0.00")
    )

    # ==========================================================
    # ACTUALIZAR PONDERACIONES
    # ==========================================================

    unidades = list(
        planificacion.detalles.order_by("pk")
    )

    cantidad = len(unidades)

    base = (
        Decimal("100.00") / Decimal(cantidad)
    ).quantize(
        Decimal("0.01"),
        rounding=ROUND_DOWN
    )

    diferencia = (
        Decimal("100.00") -
        (base * cantidad)
    )

    for i, unidad in enumerate(unidades):

        unidad.ponderacion = (
            base + diferencia
            if i == cantidad - 1
            else base
        )

        unidad.save(
            update_fields=["ponderacion"]
        )

    # ==========================================================
    # EVALUACIONES
    # ==========================================================

    for evaluacion in evaluaciones:

        DetalleEvaluacion.objects.create(
            detalle_plan=detalle,
            metodo_evaluacion=evaluacion["metodo_evaluacion"],
            porcentaje_evaluacion=evaluacion["porcentaje_evaluacion"],
            fecha_evaluacion=evaluacion["fecha_evaluacion"]
        )

    # ==========================================================
    # RESPUESTA
    # ==========================================================

    return JsonResponse({
        "estado": "exito",
        "icon": "success",
        "title": "Planificación registrada",
        "descripcion": (
            f"Se registró correctamente la unidad de "
            f"'{asignacion.materia.nombre}'."
        )
    })

# Visualizar Plan de Actividades

def vis_plan_est(request):
    return render(request, "visualizar_plan_academico.html")

def pl_reg(request):
    if request.method == "POST":
        nucleo = request.POST.get("nucleo")
        pnf = request.POST.get("pnf")

        docente = Docente.objects.get(
            usuario__cedula_identidad=request.session.get("cedula_usuario"),
            nucleo_id=nucleo,
            pnf_id=pnf
        )

        # Materias que pertenecen a este docente
        materias_docente = DocenteAsignadoMateria.objects.filter(
            docente=docente,
            activo=True
        ).values_list(
            "materia_asignada_id",
            flat=True
        )

        # Planes únicamente de las materias asignadas a este docente
        planes = PlanificacionAcademica.objects.filter(
            materia_asignacion_id__in=materias_docente,
            nucleo=docente.nucleo,
            pnf=docente.pnf,
            activo=True
        ).select_related(
            "materia_asignacion__materia"
        )

        datos = []
        for plan in planes:
            datos.append({
                "id_plan": plan.id_planificacion,
                "materia": plan.materia_asignacion.materia.nombre,
                "observacion": plan.observacion,
                "estado_aceptacion": plan.estado_aceptacion,
                "estado_aceptacion_display": plan.get_estado_aceptacion_display(),
                "cantidad_unidades": plan.detalles.count(),
            })

        return JsonResponse({"datos": datos})
  
def datos_pl_reg(request):
    if request.method == "POST":
        id_plan = request.POST.get("id_plan")

        plan = PlanificacionAcademica.objects.select_related(
            "pnf",
            "nucleo",
            "materia_asignacion__materia",
            "periodo_academico",
        ).prefetch_related(
            "detalles__evaluaciones"
        ).get(
            id_planificacion=id_plan,
            activo=True
        )

        calendario_periodo = CalendarioPeriodo.objects.select_related(
            "calendario"
        ).get(
            periodo=plan.periodo_academico,
            calendario__tipo="PERIODO",
            calendario__activo=True
        )

        datos = {
            "id_plan": plan.id_planificacion,

            # Plan
            "pnf": plan.pnf.pnf,
            "nucleo": plan.nucleo.municipio,
            "materia": plan.materia_asignacion.materia.nombre,
            "periodo_academico": plan.periodo_academico.nombre,

            # FECHAS DEL PERÍODO
            "fecha_inicio": calendario_periodo.calendario.fecha_inicio.strftime("%Y-%m-%d"),
            "fecha_final": calendario_periodo.calendario.fecha_final.strftime("%Y-%m-%d"),

            "fecha_creacion": plan.fecha_creacion.strftime("%d/%m/%Y %H:%M"),
            "fecha_actualizacion": plan.fecha_actualizacion.strftime("%d/%m/%Y %H:%M"),

            "estado_aceptacion": plan.estado_aceptacion,
            "estado_aceptacion_display": plan.get_estado_aceptacion_display(),

            "detalles": []
        }

        for detalle in plan.detalles.all():

            datos["detalles"].append({
                "id_detalle": detalle.id_detalle,
                "titulo_unidad": detalle.titulo_unidad,
                "ponderacion": str(detalle.ponderacion),
                "contenido_unidad": detalle.contenido_unidad,

                "evaluaciones": [
                    {
                        "id_evaluacion": evaluacion.id_evaluacion,
                        "metodo_evaluacion": evaluacion.metodo_evaluacion,
                        "porcentaje_evaluacion": str(
                            evaluacion.porcentaje_evaluacion
                        ),
                        "fecha_evaluacion": evaluacion.fecha_evaluacion.strftime(
                            "%Y-%m-%d"
                        ),
                    }
                    for evaluacion in detalle.evaluaciones.all()
                ]
            })

        return JsonResponse({"datos": datos})
    
def env_pla(request):
    if request.method == "POST":
        id_plan = request.POST.get("id_plan")

        try:
            with transaction.atomic():
                plan_actividad = PlanificacionAcademica.objects.get(id_planificacion=id_plan)
                plan_actividad.estado_aceptacion = "ENVIADO"
                plan_actividad.save()

                return JsonResponse({
                    "estado": "exito",
                    "icon": "success",
                    "title": "Éxito",
                    "descripcion": "Se registró exitosamente el envío del plan de actividades."
                })

        except Exception as e:
            print("ERROR:", e)

            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Error",
                "descripcion": "Ocurrió un error al momento de enviar el plan de actividades."
            })

def act_pl_reg(request):
    if request.method == "POST":
        id_plan = request.POST.get("id_plan")

        print(id_plan)

        try:
            plan = PlanificacionAcademica.objects.get(id_planificacion=id_plan)
        except PlanificacionAcademica.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Error",
                "descripcion": "No se encuentra registrado el Plan de Actividades Académicas."
            })

        try:
            with transaction.atomic():

                # UNIDADES A ELIMINAR
                detalles_eliminar = request.POST.getlist(
                    "eliminar_detalle[]"
                )

                if detalles_eliminar:
                    DetallePlanificacion.objects.filter(
                        id_detalle__in=detalles_eliminar,
                        plan_academico=plan
                    ).delete()

                # EVALUACIONES A ELIMINAR
                evaluaciones_eliminar = request.POST.getlist(
                    "eliminar_evaluacion[]"
                )

                if evaluaciones_eliminar:
                    DetalleEvaluacion.objects.filter(
                        id_evaluacion__in=evaluaciones_eliminar,
                        detalle_plan__plan_academico=plan
                    ).delete()


                # RECORRER UNIDADES
                for clave, valor in request.POST.items():
                    if not clave.startswith("id_detalle_"):
                        continue

                    i = clave.replace("id_detalle_", "")
                    id_detalle = valor

                    titulo_unidad = request.POST.get(f"titulo_unidad_{i}")
                    contenido_unidad = request.POST.get(f"contenido_unidad_{i}")

                    if not titulo_unidad or not titulo_unidad.strip():
                        return JsonResponse({
                            "estado": "fallo",
                            "icon": "error",
                            "title": "Título de unidad requerido",
                            "descripcion": "Debe registrar el título de la unidad."
                        })

                    if not contenido_unidad or not contenido_unidad.strip():
                        return JsonResponse({
                            "estado": "fallo",
                            "icon": "error",
                            "title": "Contenido de unidad requerido",
                            "descripcion": "Debe registrar el contenido correspondiente a la unidad."
                        })
                    
                    try:
                        detalle = DetallePlanificacion.objects.get(
                            id_detalle=id_detalle,
                            plan_academico=plan
                        )
                    except DetallePlanificacion.DoesNotExist:
                        return JsonResponse({
                            "estado": "fallo",
                            "icon": "error",
                            "title": "Unidad no encontrada",
                            "descripcion": "La unidad de actividad académica que intenta modificar no se encuentra registrada en este plan."
                        })

                    detalle.titulo_unidad = titulo_unidad.strip()
                    detalle.contenido_unidad = contenido_unidad.strip()
                    detalle.save(
                        update_fields=[
                            "titulo_unidad",
                            "contenido_unidad"
                        ]
                    )
                    prefijo = f"metodo_evaluacion_{i}_"

                    # Obtener los índices de las evaluaciones de esta unidad
                    indices_evaluaciones = set()

                    for clave in request.POST.keys():
                        if clave.startswith(prefijo):
                            j = clave.replace(prefijo, "")
                            indices_evaluaciones.add(j)

                    # VALIDAR Y PROCESAR EVALUACIONES
                    for j in sorted(indices_evaluaciones, key=lambda x: int(x)):
                        id_evaluacion = request.POST.get(f"id_evaluacion_{i}_{j}")
                        metodo_evaluacion = request.POST.get(f"metodo_evaluacion_{i}_{j}", "")
                        porcentaje_evaluacion = request.POST.get(f"porcentaje_evaluacion_{i}_{j}", "")
                        fecha_evaluacion = request.POST.get(f"fecha_evaluacion_{i}_{j}", "")

                        # MÉTODO
                        if not metodo_evaluacion or not metodo_evaluacion.strip():
                            return JsonResponse({
                                "estado": "fallo",
                                "icon": "error",
                                "title": "Evaluación incompleta",
                                "descripcion": f"Debe registrar el método de la evaluación {int(j) + 1} de la unidad {int(i) + 1}."
                            })

                        # PORCENTAJE
                        if (not porcentaje_evaluacion or not porcentaje_evaluacion.strip()):
                            return JsonResponse({
                                "estado": "fallo",
                                "icon": "error",
                                "title": "Evaluación incompleta",
                                "descripcion": f"Debe registrar el porcentaje de la evaluación {int(j) + 1} de la unidad {int(i) + 1}."
                            })

                        try:
                            porcentaje = Decimal(porcentaje_evaluacion)
                        except (InvalidOperation, ValueError):
                            return JsonResponse({
                                "estado": "fallo",
                                "icon": "error",
                                "title": "Porcentaje inválido",
                                "descripcion": f"El porcentaje de la evaluación {int(j) + 1} no es válido."
                            })

                        # PORCENTAJE MAYOR A 0
                        if porcentaje <= 0:
                            return JsonResponse({
                                "estado": "fallo",
                                "icon": "error",
                                "title": "Porcentaje inválido",
                                "descripcion": f"La evaluación {int(j) + 1} no puede tener un porcentaje de 0%."
                            })

                        # PORCENTAJE MÁXIMO
                        if porcentaje > 100:
                            return JsonResponse({
                                "estado": "fallo",
                                "icon": "error",
                                "title": "Porcentaje inválido",
                                "descripcion": f"El porcentaje de la evaluación {int(j) + 1} no puede superar el 100%."
                            })

                        # FECHA
                        if not fecha_evaluacion or not fecha_evaluacion.strip():
                            return JsonResponse({
                                "estado": "fallo",
                                "icon": "error",
                                "title": "Evaluación incompleta",
                                "descripcion": f"Debe registrar la fecha de la evaluación {int(j) + 1} de la unidad {int(i) + 1}."
                            })

                        # ACTUALIZAR EVALUACIÓN EXISTENTE
                        if id_evaluacion:
                            if id_evaluacion in evaluaciones_eliminar:
                                continue

                            try:
                                evaluacion = (
                                    DetalleEvaluacion.objects.get(
                                        id_evaluacion=id_evaluacion,
                                        detalle_plan=detalle
                                    )
                                )
                            except DetalleEvaluacion.DoesNotExist:
                                return JsonResponse({
                                    "estado": "fallo",
                                    "icon": "error",
                                    "title": "Evaluación no encontrada",
                                    "descripcion":
                                        "No se encuentra registrada la evaluación."
                                })


                            evaluacion.metodo_evaluacion = (metodo_evaluacion.strip())
                            evaluacion.porcentaje_evaluacion = porcentaje

                            fecha = datetime.strptime(fecha_evaluacion, "%Y-%m-%d").date()

                            evaluacion.fecha_evaluacion = fecha
                            evaluacion.save(
                                update_fields=[
                                    "metodo_evaluacion",
                                    "porcentaje_evaluacion",
                                    "fecha_evaluacion"
                                ]
                            )

                        # CREAR EVALUACIÓN NUEVA
                        else:
                            DetalleEvaluacion.objects.create(
                                detalle_plan=detalle,
                                metodo_evaluacion=metodo_evaluacion.strip(),
                                porcentaje_evaluacion=porcentaje,
                                fecha_evaluacion=fecha_evaluacion
                            )
                plan.save()
            return JsonResponse({
                "estado": "exito",
                "icon": "success",
                "title": "Actualizado",
                "descripcion": "El Plan de Actividades Académicas fue actualizado correctamente."
            })

        except Exception as error:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Error",
                "descripcion": "Ocurrió un error al actualizar el Plan de Actividades Académicas."
            })
        