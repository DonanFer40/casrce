from django.shortcuts import render
from datetime import timedelta

from django.http import JsonResponse
from django.utils import timezone

from inicio_sesion.models import CoordinadorPNF, PNFNucleo, ControlEstudio, CalendarioPeriodo, DocenteAsignadoMateria, Docente
from notas_academicas.models import PlanificacionAcademica

def pl_reg_coord_pnf(request):
    if request.method != "POST":
        return JsonResponse({
            "datos": []
        })

    id_pnf = request.POST.get("pnf_asignado", "").strip()
    perfil = request.POST.get("perfil", "").strip()
    cedula = request.session.get("cedula_usuario")
    print(perfil)

    if not cedula or not perfil:
        return JsonResponse({
            "datos": []
        })

    # COORDINADOR PNF
    if perfil == "COORDINADOR_PNF":

        coordinador = (
            CoordinadorPNF.objects
            .filter(
                usuario__cedula_identidad=cedula,
                activo=True
            )
            .select_related(
                "pnf",
                "nucleo"
            )
            .first()
        )

        if not coordinador:
            return JsonResponse({
                "datos": []
            })

        # El coordinador solo puede consultar
        # su PNF y su núcleo asignado.
        pnf_id = coordinador.pnf_id
        nucleo_id = coordinador.nucleo_id

    # CONTROL DE ESTUDIO
    elif perfil == "CONTROL_ESTUDIO":

        if not id_pnf:
            return JsonResponse({
                "datos": []
            })

        control = (
            ControlEstudio.objects
            .filter(
                usuario__cedula_identidad=cedula,
                activo=True
            )
            .select_related(
                "nucleo"
            )
            .first()
        )

        if not control:
            return JsonResponse({
                "datos": []
            })

        relacion_pnf = (
            PNFNucleo.objects
            .filter(
                id_pnf_id=id_pnf,
                id_nucleo_id=control.nucleo_id
            )
            .first()
        )

        if not relacion_pnf:
            return JsonResponse({
                "datos": []
            })

        pnf_id = relacion_pnf.id_pnf_id
        nucleo_id = control.nucleo_id

    else:
        return JsonResponse({
            "datos": []
        })

    # FECHA ACTUAL
    fecha_actual = timezone.localdate()
    anio_actual = fecha_actual.year

    # PLANIFICACIONES DEL PNF Y NÚCLEO
    planes = (
        PlanificacionAcademica.objects
        .filter(
            estado_aceptacion="ENVIADO",
            activo=True,
            pnf_id=pnf_id,
            nucleo_id=nucleo_id
        )
        .select_related(
            "pnf",
            "nucleo",
            "materia_asignacion__materia",
            "periodo_academico"
        )
        .prefetch_related(
            "detalles"
        )
        .order_by(
            "id_planificacion"
        )
    )

    datos = []

    for plan in planes:

        # CALENDARIO ACADÉMICO DEL PERÍODO
        calendario = (
            CalendarioPeriodo.objects
            .filter(
                periodo=plan.periodo_academico,
                calendario__tipo="PERIODO",
                calendario__activo=True,
                calendario__fecha_inicio__year=anio_actual
            )
            .select_related(
                "calendario"
            )
            .first()
        )

        if not calendario:
            continue

        fecha_inicio = calendario.calendario.fecha_inicio
        fecha_final = calendario.calendario.fecha_final

        # PLAZO DE LOS PRIMEROS 5 DÍAS
        fecha_limite = fecha_inicio + timedelta(days=4)

        # El período todavía no comienza
        if fecha_actual < fecha_inicio:
            continue

        # Ya pasaron los primeros 5 días
        if fecha_actual > fecha_limite:
            continue

        # El período académico ya finalizó
        if fecha_actual > fecha_final:
            continue

        datos.append({
            "id_plan": plan.id_planificacion,

            "pnf": plan.pnf.pnf,

            "nucleo": plan.nucleo.municipio,

            "materia": (
                plan.materia_asignacion.materia.nombre
            ),

            "periodo_academico": (
                plan.periodo_academico.nombre
            ),

            "cantidad_unidades": (
                plan.detalles.count()
            ),

            "fecha_creacion": (
                plan.fecha_creacion.strftime(
                    "%d/%m/%Y %H:%M"
                )
            ),

            "fecha_actualizacion": (
                plan.fecha_actualizacion.strftime(
                    "%d/%m/%Y %H:%M"
                )
            ),

            "estado_aceptacion": (
                plan.estado_aceptacion
            ),

            "estado_aceptacion_display": (
                plan.get_estado_aceptacion_display()
            ),
        })

    return JsonResponse({
        "estado": "exito",
        "datos": datos
    })

def datos_pl_reg_coord_pnf(request):
    if request.method == "POST":
        id_plan = request.POST.get("id_plan")

        if not id_plan:
            return JsonResponse({
                "datos": {}
            })

        plan = PlanificacionAcademica.objects.select_related(
            "pnf",
            "nucleo",
            "materia_asignacion__materia",
            "periodo_academico",
        ).prefetch_related(
            "detalles__evaluaciones"
        ).filter(
            id_planificacion=id_plan,
            activo=True
        ).first()

        if not plan:
            return JsonResponse({
                "datos": {}
            })

        docente_asignado = plan.materia_asignacion.docentes.filter(
            activo=True
        ).select_related(
            "docente__usuario"
        ).first()

        datos = {
            "id_plan": plan.id_planificacion,

            # Plan
            "pnf": plan.pnf.pnf,
            "nucleo": plan.nucleo.municipio,
            "materia": plan.materia_asignacion.materia.nombre,
            "periodo_academico": plan.periodo_academico.nombre,

            # Docente
            "docente": (
                f"{docente_asignado.docente.usuario.nombres} "
                f"{docente_asignado.docente.usuario.apellidos}"
                if docente_asignado
                else None
            ),

            "cedula_docente": (
                docente_asignado.docente.usuario.cedula_identidad
                if docente_asignado
                else None
            ),

            # Fechas
            "fecha_creacion": plan.fecha_creacion.strftime(
                "%d/%m/%Y %H:%M"
            ),
            "fecha_actualizacion": plan.fecha_actualizacion.strftime(
                "%d/%m/%Y %H:%M"
            ),

            # Estado
            "estado_aceptacion": plan.estado_aceptacion,
            "estado_aceptacion_display": plan.get_estado_aceptacion_display(),

            # Unidades
            "detalles": []
        }

        for detalle in plan.detalles.all():
            datos["detalles"].append({
                "id_detalle": detalle.id_detalle,
                "titulo_unidad": detalle.titulo_unidad,
                "ponderacion": str(detalle.ponderacion),
                "contenido_unidad": detalle.contenido_unidad,

                # Evaluaciones
                "evaluaciones": [
                    {
                        "id_evaluacion": evaluacion.id_evaluacion,
                        "metodo_evaluacion": evaluacion.metodo_evaluacion,
                        "porcentaje_evaluacion": str(
                            evaluacion.porcentaje_evaluacion
                        ),
                        "fecha_evaluacion": (
                            evaluacion.fecha_evaluacion.strftime("%Y-%m-%d")
                        ),
                    }
                    for evaluacion in detalle.evaluaciones.all()
                ]
            })

        return JsonResponse({
            "datos": datos
        })

def vis_pl_env(request):
    return render(
        request,
        'Roles/Coordinador_PNF/planificacion_academica/visualizar_planes_actividades.html'
    )

def camb_est_pl(request):
    if request.method == "POST":
        id_plan = request.POST.get("id_plan")
        estado = request.POST.get("estado")
        observacion = request.POST.get("observacion")

        try:
            plan = PlanificacionAcademica.objects.get(id_planificacion=id_plan)
        except PlanificacionAcademica.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Plan de Actividades",
                "descripcion": "No se encuentra registrado el plan de actividades."
            })

        try:
            plan.estado_aceptacion = estado
            plan.observacion = observacion
            plan.save()

            return JsonResponse({
                "estado": "exito",
                "icon": "success",
                "title": "Plan de Actividades",
                "descripcion": (
                    f"El plan ha sido marcado como {plan.get_estado_aceptacion_display().lower()}."
                )
            })

        except Exception:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Plan de Actividades",
                "descripcion": (
                    "Ocurrió un error al momento de actualizar "
                    "el estado del plan de actividades."
                )
            })

def rech_plan(request):
    return render(request, "Coordinador_PNF/planes_actividades/rechazado_planes_actividades.html")
