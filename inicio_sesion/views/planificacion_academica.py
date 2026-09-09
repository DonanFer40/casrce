from django.shortcuts import render
from datetime import timedelta

from django.http import JsonResponse
from django.utils import timezone

from inicio_sesion.models import CoordinadorPNF
from notas_academicas.models import PlanificacionAcademica

def pnf_asig_coord(request):
    coordinadores = CoordinadorPNF.objects.filter(usuario__cedula_identidad=request.session.get("cedula_usuario")
    ).select_related("pnf")

    pnfs = []
    for coordinador in coordinadores:
        pnfs.append({
            "id_pnf": coordinador.pnf.id_pnf,
            "pnf": coordinador.pnf.pnf,
        })

    return JsonResponse({ "pnfs": pnfs })

def pl_reg_coord_pnf(request):
    if request.method == "POST":
        id_pnf = request.POST.get("pnf_asignado")

        if not id_pnf:
            return JsonResponse({
                "datos": []
            })

        cedula = request.session.get("cedula_usuario")

        coordinador = CoordinadorPNF.objects.filter(
            usuario__cedula_identidad=cedula,
            pnf_id=id_pnf
        ).select_related(
            "pnf",
            "nucleo"
        ).first()

        if not coordinador:
            return JsonResponse({
                "datos": []
            })

        fecha_actual = timezone.localdate()

        planes = PlanificacionAcademica.objects.filter(
            pnf=coordinador.pnf,
            nucleo=coordinador.nucleo,
            estado_aceptacion="ENVIADO",
            periodo_academico__calendarios__calendario__activo=True,
            periodo_academico__calendarios__calendario__tipo="PERIODO",
            periodo_academico__calendarios__calendario__fecha_inicio__lte=fecha_actual,
            periodo_academico__calendarios__calendario__fecha_inicio__gte=fecha_actual - timedelta(days=3)
        ).select_related(
            "pnf",
            "nucleo",
            "materia_asignacion__materia",
            "periodo_academico"
        ).prefetch_related(
            "detalles"
        ).distinct().order_by("-fecha_creacion")

        datos = []

        for plan in planes:
            datos.append({
                "id_plan": plan.id_planificacion,
                "pnf": plan.pnf.pnf,
                "nucleo": plan.nucleo.municipio,
                "materia": plan.materia_asignacion.materia.nombre,
                "periodo_academico": plan.periodo_academico.nombre,
                "cantidad_unidades": plan.detalles.count(),
                "fecha_creacion": plan.fecha_creacion.strftime("%d/%m/%Y %H:%M"),
                "fecha_actualizacion": plan.fecha_actualizacion.strftime("%d/%m/%Y %H:%M"),
            })

        return JsonResponse({
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
    return render(request, "Coordinador_PNF/planificacion_academica/visualizar_planes_actvidades.html")

def camb_est_pl(request):
    if request.method == "POST":

        id_plan = request.POST.get("id_plan")
        estado = request.POST.get("estado")
        observacion = request.POST.get("observacion")

        try:
            plan = PlanificacionAcademica.objects.get(
                id_planificacion=id_plan
            )

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
