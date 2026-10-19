from django.shortcuts import render
from django.http import JsonResponse
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from django.db.models import F, Exists, OuterRef, Q, Prefetch, Avg

from inicio_sesion.models import CoordinadorPNF, ControlEstudio, TrayectoAcademico, MateriaAsignada, CalendarioPeriodo, PeriodoAcademicoMateria, Usuario, Pnf, PNFNucleo, Estudiante, EstatusEstudiante, CalendarioAcademico, Nucleos, PeriodoAcademico, Materia, Docente, DocenteAsignadoMateria

from notas_academicas.models import PlanificacionAcademica, Reparacion, DetallePlanificacion, HistorialTrayectoEstudiante, HistorialDetalleNota, HistorialModificacionNotas, DetalleEvaluacion, PromedioFinal, Calificaciones, DetalleCalificacionesUnidad

# Remover cambios notas académicas

def pnfs_rem_not_acad(request):
    cedula = request.session.get("cedula_usuario")

    if not cedula:
        return JsonResponse({
            "estado": "fallo",
            "datos": [],
            "title": "Sesión",
            "descripcion": (
                "No se encontró la cédula del usuario en la sesión."
            ),
            "icon": "error"
        })

    # VALIDAR CALENDARIO ACADÉMICO
    fecha_actual = timezone.localdate()
    año_actual = fecha_actual.year

    calendarios_carga = (
        CalendarioPeriodo.objects
        .select_related(
            "periodo",
            "calendario"
        )
        .filter(
            calendario__tipo="CARGA_NOTAS",
            calendario__activo=True,
            calendario__fecha_inicio__year=año_actual
        )
        .order_by(
            "calendario__fecha_inicio"
        )
    )

    if not calendarios_carga.exists():
        return JsonResponse({
            "estado": "fallo",
            "datos": [],
            "title": "Calendario académico",
            "icon": "warning",
            "descripcion": (
                "No existe un calendario académico de carga "
                f"de notas registrado para el año {año_actual}."
            )
        })

    calendarios_periodos = (
        calendarios_carga
        .filter(
            calendario__fecha_inicio__lte=fecha_actual,
            calendario__fecha_final__gte=fecha_actual
        )
    )

    if not calendarios_periodos.exists():

        calendario_proximo = (
            calendarios_carga
            .filter(
                calendario__fecha_inicio__gt=fecha_actual
            )
            .order_by(
                "calendario__fecha_inicio"
            )
            .first()
        )

        if calendario_proximo:
            return JsonResponse({
                "estado": "fallo",
                "datos": [],
                "title": "Carga de notas no habilitada",
                "icon": "warning",
                "descripcion": (
                    "Actualmente no existe un período académico "
                    "habilitado para la carga de notas. "
                    "El próximo período disponible corresponde a "
                    f"{calendario_proximo.periodo.nombre} y "
                    "inicia el "
                    f"{calendario_proximo.calendario.fecha_inicio.strftime('%d/%m/%Y')}."
                )
            })

        calendario_anterior = (
            calendarios_carga
            .filter(
                calendario__fecha_final__lt=fecha_actual
            )
            .order_by(
                "-calendario__fecha_final"
            )
            .first()
        )

        if calendario_anterior:
            return JsonResponse({
                "estado": "fallo",
                "datos": [],
                "title": "Plazo de carga vencido",
                "icon": "warning",
                "descripcion": (
                    "El plazo de carga de notas del período "
                    f"{calendario_anterior.periodo.nombre} "
                    "finalizó el "
                    f"{calendario_anterior.calendario.fecha_final.strftime('%d/%m/%Y')}. "
                    "Actualmente no existe otro período académico "
                    "habilitado para la carga de notas."
                )
            })

        return JsonResponse({
            "estado": "fallo",
            "datos": [],
            "title": "Carga de notas no habilitada",
            "icon": "warning",
            "descripcion": (
                "Actualmente no existe un período académico "
                "habilitado para la carga de notas."
            )
        })

    # CONTROL DE ESTUDIO
    control_estudio = (
        ControlEstudio.objects
        .select_related(
            "usuario",
            "nucleo"
        )
        .filter(
            usuario__cedula_identidad=cedula,
            activo=True
        )
        .first()
    )

    pnfs = (
        Pnf.objects
        .filter(
            pnfnucleo__id_nucleo=control_estudio.nucleo_id
        )
        .distinct()
        .order_by("pnf")
    )

    if not pnfs.exists():
        return JsonResponse({
            "estado": "vacio",
            "datos": [],
            "title": "No hay P.N.F disponibles",
            "descripcion": (
                "No existen P.N.F disponibles para el "
                "núcleo asignado al perfil de Control de Estudio."
            ),
            "icon": "info"
        })

    datos = [
        {
            "id_pnf": pnf.id_pnf,
            "pnf": pnf.pnf,
            "codigo": pnf.codigo,
            "periodo_academico": pnf.periodo_academico
        }
        for pnf in pnfs
    ]

    return JsonResponse({
        "estado": "exito",
        "datos": datos,
        "nucleo": {
            "id_nucleo": control_estudio.nucleo_id,
            "municipio": control_estudio.nucleo.municipio
        }
    })

def doc_rem_not_acad(request):
    if request.method != "POST":
        return JsonResponse({
            "estado": "fallo",
            "datos": [],
            "title": "Error",
            "descripcion": "Método de solicitud no permitido.",
            "icon": "error"
        })

    pnf_seleccionado = request.POST.get("pnf_seleccionado")
    cedula = request.session.get("cedula_usuario")

    if not cedula:
        return JsonResponse({
            "estado": "fallo",
            "datos": [],
            "title": "Sesión",
            "descripcion": "No se encontró la cédula del usuario en la sesión.",
            "icon": "error"
        })

    if not pnf_seleccionado:
        return JsonResponse({
            "estado": "fallo",
            "datos": [],
            "title": "P.N.F",
            "descripcion": "Debe seleccionar un P.N.F.",
            "icon": "warning"
        })

    control_estudio = (
        ControlEstudio.objects
        .select_related("nucleo")
        .filter(
            usuario__cedula_identidad=cedula,
            activo=True
        )
        .first()
    )

    if not control_estudio:
        return JsonResponse({
            "estado": "fallo",
            "datos": [],
            "title": "Control de Estudio",
            "descripcion": (
                "El usuario no posee un perfil activo de "
                "Control de Estudio."
            ),
            "icon": "error"
        })

    nucleo_id = control_estudio.nucleo_id

    if not PNFNucleo.objects.filter(
        id_nucleo=nucleo_id,
        id_pnf=pnf_seleccionado
    ).exists():
        return JsonResponse({
            "estado": "fallo",
            "datos": [],
            "title": "P.N.F no válido",
            "descripcion": (
                "El P.N.F seleccionado no está asociado "
                "al núcleo de Control de Estudio."
            ),
            "icon": "warning"
        })

    fecha_actual = timezone.localdate()
    año_actual = fecha_actual.year

    calendarios_carga = (
        CalendarioPeriodo.objects
        .select_related("periodo", "calendario")
        .filter(
            calendario__tipo="CARGA_NOTAS",
            calendario__activo=True,
            calendario__fecha_inicio__year=año_actual
        )
        .order_by("calendario__fecha_inicio")
    )

    if not calendarios_carga.exists():
        return JsonResponse({
            "estado": "fallo",
            "datos": [],
            "title": "Calendario académico",
            "icon": "warning",
            "descripcion": (
                "No existe un calendario académico de carga "
                f"de notas registrado para el año {año_actual}."
            )
        })

    calendarios_periodos = calendarios_carga.filter(
        calendario__fecha_inicio__lte=fecha_actual,
        calendario__fecha_final__gte=fecha_actual
    )

    if not calendarios_periodos.exists():
        calendario_proximo = (
            calendarios_carga
            .filter(calendario__fecha_inicio__gt=fecha_actual)
            .order_by("calendario__fecha_inicio")
            .first()
        )

        if calendario_proximo:
            return JsonResponse({
                "estado": "fallo",
                "datos": [],
                "title": "Carga de notas no habilitada",
                "icon": "warning",
                "descripcion": (
                    "Actualmente no existe un período académico "
                    "habilitado para la carga de notas. El próximo "
                    "período disponible corresponde a "
                    f"{calendario_proximo.periodo.nombre} y "
                    "inicia el "
                    f"{calendario_proximo.calendario.fecha_inicio.strftime('%d/%m/%Y')}."
                )
            })

        calendario_anterior = (
            calendarios_carga
            .filter(calendario__fecha_final__lt=fecha_actual)
            .order_by("-calendario__fecha_final")
            .first()
        )

        if calendario_anterior:
            return JsonResponse({
                "estado": "fallo",
                "datos": [],
                "title": "Plazo de carga vencido",
                "icon": "warning",
                "descripcion": (
                    "El plazo de carga de notas del período "
                    f"{calendario_anterior.periodo.nombre} finalizó el "
                    f"{calendario_anterior.calendario.fecha_final.strftime('%d/%m/%Y')}. "
                    "Actualmente no existe otro período académico "
                    "habilitado para la carga de notas."
                )
            })

        return JsonResponse({
            "estado": "fallo",
            "datos": [],
            "title": "Carga de notas no habilitada",
            "icon": "warning",
            "descripcion": (
                "Actualmente no existe un período académico "
                "habilitado para la carga de notas."
            )
        })

    # Modificaciones del año actual que todavía figuran como MODIFICACION.
    historiales = (
        HistorialModificacionNotas.objects
        .filter(
            docente_asignado__docente__nucleo_id=nucleo_id,
            docente_asignado__docente__pnf_id=pnf_seleccionado,
            fecha_modificacion__year=año_actual,
            detalles__revertido=False
        )
        .select_related(
            "docente_asignado__docente__usuario"
        )
        .distinct()
        .order_by("-fecha_modificacion", "-id_historial")
    )

    docentes = {}

    for historial in historiales:
        docente_asignado = historial.docente_asignado

        if not docente_asignado or not docente_asignado.docente:
            continue

        docente = docente_asignado.docente
        usuario_docente = docente.usuario

        if not usuario_docente:
            continue

        docentes[docente.id_docente] = {
            "id_docente": docente.id_docente,
            "cedula": usuario_docente.cedula_identidad,
            "nombres": usuario_docente.nombres,
            "apellidos": usuario_docente.apellidos
        }

    if not docentes:
        return JsonResponse({
            "estado": "vacio",
            "datos": [],
            "title": "Sin modificaciones pendientes",
            "descripcion": (
                "No existen docentes con notas individuales pendientes "
                f"de reversión durante el año {año_actual} "
                "para el P.N.F. seleccionado."
            ),
            "icon": "info"
        })

    datos = sorted(
        docentes.values(),
        key=lambda docente: (
            docente["apellidos"].lower(),
            docente["nombres"].lower()
        )
    )

    return JsonResponse({
        "estado": "exito",
        "datos": datos
    })


def tray_rem_not(request):
    if request.method != "POST":
        return JsonResponse({
            "estado": "fallo",
            "title": "Error",
            "icon": "error",
            "descripcion": "Método de solicitud no permitido."
        })

    pnf_seleccionado = request.POST.get("pnf_seleccionado")
    docente_seleccionado = request.POST.get("docente_seleccionado")
    cedula = request.session.get("cedula_usuario")

    if not cedula:
        return JsonResponse({
            "estado": "fallo",
            "title": "Sesión",
            "icon": "warning",
            "descripcion": "No se pudo identificar al usuario de la sesión."
        })

    if not pnf_seleccionado:
        return JsonResponse({
            "estado": "fallo",
            "title": "P.N.F",
            "icon": "warning",
            "descripcion": "Debe seleccionar un P.N.F."
        })

    if not docente_seleccionado:
        return JsonResponse({
            "estado": "fallo",
            "title": "Docente",
            "icon": "warning",
            "descripcion": "Debe seleccionar un docente."
        })

    control_estudio = (
        ControlEstudio.objects
        .select_related("nucleo")
        .filter(
            usuario__cedula_identidad=cedula,
            activo=True
        )
        .first()
    )

    if not control_estudio:
        return JsonResponse({
            "estado": "fallo",
            "title": "Control de Estudio",
            "icon": "error",
            "descripcion": (
                "El usuario no posee un perfil activo de "
                "Control de Estudio."
            )
        })

    nucleo_asignado = control_estudio.nucleo_id

    if not PNFNucleo.objects.filter(
        id_nucleo=nucleo_asignado,
        id_pnf=pnf_seleccionado
    ).exists():
        return JsonResponse({
            "estado": "fallo",
            "title": "P.N.F no válido",
            "icon": "warning",
            "descripcion": (
                "El P.N.F seleccionado no está asociado "
                "al núcleo de Control de Estudio."
            )
        })

    docente = (
        Docente.objects
        .select_related("usuario")
        .filter(
            usuario__cedula_identidad=docente_seleccionado,
            nucleo_id=nucleo_asignado,
            pnf_id=pnf_seleccionado,
            activo=True
        )
        .first()
    )

    if not docente:
        return JsonResponse({
            "estado": "fallo",
            "title": "Docente",
            "icon": "warning",
            "descripcion": (
                "El docente seleccionado no posee una asignación "
                "activa para el núcleo y P.N.F seleccionados."
            )
        })

    fecha_actual = timezone.localdate()
    año_actual = fecha_actual.year

    calendarios_carga = (
        CalendarioPeriodo.objects
        .select_related("periodo", "calendario")
        .filter(
            calendario__tipo="CARGA_NOTAS",
            calendario__activo=True,
            calendario__fecha_inicio__year=año_actual
        )
        .order_by("calendario__fecha_inicio")
    )

    if not calendarios_carga.exists():
        return JsonResponse({
            "estado": "fallo",
            "title": "Calendario académico",
            "icon": "warning",
            "descripcion": (
                "No existe un calendario académico de carga "
                f"de notas registrado para el año {año_actual}."
            )
        })

    calendarios_periodos = calendarios_carga.filter(
        calendario__fecha_inicio__lte=fecha_actual,
        calendario__fecha_final__gte=fecha_actual
    )

    if not calendarios_periodos.exists():

        calendario_proximo = (
            calendarios_carga
            .filter(
                calendario__fecha_inicio__gt=fecha_actual
            )
            .order_by("calendario__fecha_inicio")
            .first()
        )

        if calendario_proximo:
            return JsonResponse({
                "estado": "fallo",
                "title": "Carga de notas no habilitada",
                "icon": "warning",
                "descripcion": (
                    "Actualmente no existe un período académico "
                    "habilitado para la carga de notas. El próximo "
                    "período disponible corresponde a "
                    f"{calendario_proximo.periodo.nombre} e inicia el "
                    f"{calendario_proximo.calendario.fecha_inicio.strftime('%d/%m/%Y')}."
                )
            })

        calendario_anterior = (
            calendarios_carga
            .filter(
                calendario__fecha_final__lt=fecha_actual
            )
            .order_by("-calendario__fecha_final")
            .first()
        )

        if calendario_anterior:
            return JsonResponse({
                "estado": "fallo",
                "title": "Plazo de carga vencido",
                "icon": "warning",
                "descripcion": (
                    "El plazo de carga de notas del período "
                    f"{calendario_anterior.periodo.nombre} finalizó el "
                    f"{calendario_anterior.calendario.fecha_final.strftime('%d/%m/%Y')}. "
                    "Actualmente no existe otro período académico "
                    "habilitado para la carga de notas."
                )
            })

        return JsonResponse({
            "estado": "fallo",
            "title": "Carga de notas no habilitada",
            "icon": "warning",
            "descripcion": (
                "Actualmente no existe un período académico "
                "habilitado para la carga de notas."
            )
        })
    
    periodos_actuales = list(
        calendarios_periodos.values_list("periodo_id", flat=True)
    )

    detalles_pendientes = (
        HistorialDetalleNota.objects
        .filter(
            revertido=False,
            historial__docente_asignado__docente=docente,
            historial__periodo_academico_id__in=periodos_actuales,
            historial__calificacion__estudiante__nucleo_id=nucleo_asignado,
            historial__calificacion__estudiante__pnf_id=pnf_seleccionado,
            historial__calificacion__materia_asignada__materia__id_pnf=pnf_seleccionado,
        )
        .filter(
            historial__calificacion__materia_asignada__materia__activa=True,
            historial__calificacion__materia_asignada__activo=True,
        )
        .select_related(
            "historial__trayecto",
            "historial__calificacion",
        )
    )

    ids_trayectos = (
        detalles_pendientes
        .filter(historial__trayecto__isnull=False)
        .values_list("historial__trayecto_id", flat=True)
        .distinct()
    )

    trayectos = (
        TrayectoAcademico.objects
        .filter(id_periodo_academico__in=ids_trayectos)
        .distinct()
        .order_by("id_periodo_academico")
    )

    if not trayectos.exists():
        return JsonResponse({
            "estado": "vacio",
            "trayectos": [],
            "title": "Sin cambios de carga de notas",
            "icon": "info",
            "descripcion": (
                "El docente seleccionado no tiene modificaciones "
                "de notas pendientes de reversión para el P.N.F "
                "y los períodos académicos actualmente habilitados."
            )
        })

    datos = [
        {
            "id_trayecto": trayecto.id_periodo_academico,
            "nombre": trayecto.nombre
        }
        for trayecto in trayectos
    ]

    return JsonResponse({
        "estado": "exito",
        "trayectos": datos
    })

def mat_rem_not(request):
    if request.method != "POST":
        return JsonResponse({
            "estado": "fallo",
            "title": "Error",
            "icon": "error",
            "descripcion": "Método de solicitud no permitido."
        })

    pnf_seleccionado = request.POST.get("pnf_seleccionado")
    docente_seleccionado = request.POST.get("docente_seleccionado")
    trayecto_seleccionado = request.POST.get("trayecto_seleccionado")
    cedula = request.session.get("cedula_usuario")

    if not cedula:
        return JsonResponse({
            "estado": "fallo",
            "title": "Sesión",
            "icon": "warning",
            "descripcion": (
                "No se pudo identificar al usuario de la sesión."
            )
        })

    if not pnf_seleccionado:
        return JsonResponse({
            "estado": "fallo",
            "title": "P.N.F",
            "icon": "warning",
            "descripcion": "Debe seleccionar un P.N.F."
        })

    if not docente_seleccionado:
        return JsonResponse({
            "estado": "fallo",
            "title": "Docente",
            "icon": "warning",
            "descripcion": "Debe seleccionar un docente."
        })

    if not trayecto_seleccionado:
        return JsonResponse({
            "estado": "fallo",
            "title": "Trayecto",
            "icon": "warning",
            "descripcion": "Debe seleccionar un trayecto académico."
        })

    # CONTROL DE ESTUDIO
    control_estudio = (
        ControlEstudio.objects
        .select_related("nucleo")
        .filter(
            usuario__cedula_identidad=cedula,
            activo=True
        )
        .first()
    )

    if not control_estudio:
        return JsonResponse({
            "estado": "fallo",
            "title": "Control de Estudio no disponible",
            "icon": "error",
            "descripcion": (
                "El usuario no posee un perfil activo de "
                "Control de Estudio."
            )
        })

    nucleo_asignado = control_estudio.nucleo_id

    # VALIDAR PNF DEL NÚCLEO
    if not PNFNucleo.objects.filter(
        id_nucleo=nucleo_asignado,
        id_pnf=pnf_seleccionado
    ).exists():

        return JsonResponse({
            "estado": "fallo",
            "title": "P.N.F no válido",
            "icon": "warning",
            "descripcion": (
                "El P.N.F seleccionado no está asociado "
                "al núcleo de Control de Estudio."
            )
        })

    # VALIDAR TRAYECTO
    if not TrayectoAcademico.objects.filter(
        id_periodo_academico=trayecto_seleccionado
    ).exists():

        return JsonResponse({
            "estado": "fallo",
            "title": "Trayecto no válido",
            "icon": "warning",
            "descripcion": (
                "El trayecto académico seleccionado no es válido."
            )
        })

    # VALIDAR CALENDARIO ACADÉMICO
    fecha_actual = timezone.localdate()
    año_actual = fecha_actual.year

    calendarios_carga = (
        CalendarioPeriodo.objects
        .select_related(
            "periodo",
            "calendario"
        )
        .filter(
            calendario__tipo="CARGA_NOTAS",
            calendario__activo=True,
            calendario__fecha_inicio__year=año_actual
        )
        .order_by(
            "calendario__fecha_inicio"
        )
    )

    if not calendarios_carga.exists():
        return JsonResponse({
            "estado": "fallo",
            "title": "Calendario académico",
            "icon": "warning",
            "descripcion": (
                "No existe un calendario académico de carga "
                f"de notas registrado para el año {año_actual}."
            )
        })

    calendarios_periodos = (
        calendarios_carga
        .filter(
            calendario__fecha_inicio__lte=fecha_actual,
            calendario__fecha_final__gte=fecha_actual
        )
    )

    if not calendarios_periodos.exists():

        calendario_proximo = (
            calendarios_carga
            .filter(
                calendario__fecha_inicio__gt=fecha_actual
            )
            .order_by(
                "calendario__fecha_inicio"
            )
            .first()
        )

        if calendario_proximo:
            return JsonResponse({
                "estado": "fallo",
                "title": "Carga de notas no habilitada",
                "icon": "warning",
                "descripcion": (
                    "Actualmente no existe un período académico "
                    "habilitado para la carga de notas. "
                    "El próximo período disponible corresponde a "
                    f"{calendario_proximo.periodo.nombre} y "
                    f"inicia el "
                    f"{calendario_proximo.calendario.fecha_inicio.strftime('%d/%m/%Y')}."
                )
            })

        calendario_anterior = (
            calendarios_carga
            .filter(
                calendario__fecha_final__lt=fecha_actual
            )
            .order_by(
                "-calendario__fecha_final"
            )
            .first()
        )

        if calendario_anterior:
            return JsonResponse({
                "estado": "fallo",
                "title": "Plazo de carga vencido",
                "icon": "warning",
                "descripcion": (
                    "El plazo de carga de notas del período "
                    f"{calendario_anterior.periodo.nombre} "
                    f"finalizó el "
                    f"{calendario_anterior.calendario.fecha_final.strftime('%d/%m/%Y')}. "
                    "Actualmente no existe otro período académico "
                    "habilitado para la carga de notas."
                )
            })

        return JsonResponse({
            "estado": "fallo",
            "title": "Carga de notas no habilitada",
            "icon": "warning",
            "descripcion": (
                "Actualmente no existe un período académico "
                "habilitado para la carga de notas."
            )
        })

    periodos_actuales = calendarios_periodos.values_list(
        "periodo_id",
        flat=True
    )

    # DOCENTE SELECCIONADO
    docente_obj = (
        Docente.objects
        .filter(
            usuario__cedula_identidad=docente_seleccionado,
            nucleo_id=nucleo_asignado,
            pnf_id=pnf_seleccionado,
            activo=True
        )
        .first()
    )

    if not docente_obj:
        return JsonResponse({
            "estado": "fallo",
            "title": "Docente no encontrado",
            "icon": "warning",
            "descripcion": (
                "El docente seleccionado no posee un registro "
                "activo para el núcleo y P.N.F seleccionados."
            )
        })

    # MATERIAS DEL DOCENTE CON NOTAS PENDIENTES DE REVERSIÓN
    materias_asignadas = (
        DocenteAsignadoMateria.objects
        .filter(
            docente=docente_obj,
            activo=True,
            materia_asignada__activo=True,
            materia_asignada__materia__activa=True,
            materia_asignada__materia__id_pnf_id=pnf_seleccionado,
            materia_asignada__materia__id_trayecto_id=trayecto_seleccionado,

            historial_modificaciones_notas__isnull=False,

            historial_modificaciones_notas__periodo_academico_id__in=(
                periodos_actuales
            ),

            historial_modificaciones_notas__detalles__revertido=False
        )
        .select_related(
            "materia_asignada__materia",
            "materia_asignada__materia__id_trayecto"
        )
        .distinct()
        .order_by(
            "materia_asignada__materia__nombre"
        )
    )

    if not materias_asignadas.exists():
        return JsonResponse({
            "estado": "vacio",
            "datos": [],
            "title": "Sin notas pendientes de reversión",
            "descripcion": (
                "No existen materias con notas individuales pendientes "
                "de reversión para el docente, trayecto y períodos "
                "académicos habilitados seleccionados."
            ),
            "icon": "info"
        })

    materias = []

    for asignacion in materias_asignadas:
        materia_asignada = asignacion.materia_asignada
        materia = materia_asignada.materia

        materias.append({
            "id_materia_asignada": (
                materia_asignada.id_materia_asignada
            ),
            "id_materia": materia.id_materia,
            "nombre": materia.nombre,
            "codigo": materia.codigo,
            "tipo_materia": materia.tipo_materia,
            "id_trayecto": (
                materia.id_trayecto.id_periodo_academico
                if materia.id_trayecto
                else None
            ),
            "trayecto": (
                materia.id_trayecto.nombre
                if materia.id_trayecto
                else None
            )
        })

    return JsonResponse({
        "estado": "exito",
        "materias": materias
    })

def perid_rem_not(request):
    if request.method != "POST":
        return JsonResponse({
            "estado": "fallo",
            "title": "Error",
            "icon": "error",
            "descripcion": "Método de solicitud no permitido."
        })

    pnf_seleccionado = request.POST.get("pnf_seleccionado")
    docente_seleccionado = request.POST.get("docente_seleccionado")
    trayecto_seleccionado = request.POST.get("trayecto_seleccionado")
    materia_seleccionado = request.POST.get("materia_seleccionado")
    cedula = request.session.get("cedula_usuario")

    if not cedula:
        return JsonResponse({
            "estado": "fallo",
            "title": "Sesión",
            "icon": "warning",
            "descripcion": (
                "No se pudo identificar al usuario de la sesión."
            )
        })

    if not all([
        pnf_seleccionado,
        docente_seleccionado,
        trayecto_seleccionado,
        materia_seleccionado
    ]):
        return JsonResponse({
            "estado": "fallo",
            "title": "Datos incompletos",
            "icon": "warning",
            "descripcion": (
                "Debe seleccionar el P.N.F, docente, trayecto "
                "y materia."
            )
        })

    control_estudio = (
        ControlEstudio.objects
        .filter(
            usuario__cedula_identidad=cedula,
            activo=True
        )
        .first()
    )

    if not control_estudio:
        return JsonResponse({
            "estado": "fallo",
            "title": "Control de Estudio",
            "icon": "error",
            "descripcion": (
                "El usuario no posee un perfil activo de "
                "Control de Estudio."
            )
        })

    nucleo = control_estudio.nucleo_id

    if not PNFNucleo.objects.filter(
        id_nucleo=nucleo,
        id_pnf=pnf_seleccionado
    ).exists():
        return JsonResponse({
            "estado": "fallo",
            "title": "P.N.F no válido",
            "icon": "warning",
            "descripcion": (
                "El P.N.F seleccionado no está asociado "
                "al núcleo de Control de Estudio."
            )
        })

    docente = (
        Docente.objects
        .filter(
            usuario__cedula_identidad=docente_seleccionado,
            nucleo_id=nucleo,
            pnf_id=pnf_seleccionado,
            activo=True
        )
        .first()
    )

    if not docente:
        return JsonResponse({
            "estado": "fallo",
            "title": "Docente",
            "icon": "warning",
            "descripcion": (
                "El docente seleccionado no posee una asignación "
                "activa para el núcleo y P.N.F."
            )
        })

    materia_asignada = (
        MateriaAsignada.objects
        .filter(
            id_materia_asignada=materia_seleccionado,
            activo=True,
            materia__activa=True,
            materia__id_pnf=pnf_seleccionado,
            materia__id_trayecto_id=trayecto_seleccionado,
            docentes__docente=docente,
            docentes__activo=True
        )
        .select_related(
            "materia",
            "materia__id_trayecto"
        )
        .distinct()
        .first()
    )

    if not materia_asignada:
        return JsonResponse({
            "estado": "fallo",
            "title": "Materia",
            "icon": "warning",
            "descripcion": (
                "La materia seleccionada no posee una asignación "
                "activa para el docente, núcleo, P.N.F y trayecto."
            )
        })

    periodo = (
        HistorialModificacionNotas.objects
        .filter(
            docente_asignado__materia_asignada=materia_asignada,
            docente_asignado__docente=docente,
            periodo_academico__isnull=False,
            trayecto_id=trayecto_seleccionado,
            detalles__revertido=False
        )
        .select_related("periodo_academico")
        .distinct()
        .order_by(
            "-fecha_modificacion",
            "-id_historial"
        )
        .first()
    )

    if not periodo:
        return JsonResponse({
            "estado": "vacio",
            "datos": [],
            "title": "Sin modificaciones pendientes",
            "icon": "info",
            "descripcion": (
                "La materia seleccionada no tiene modificaciones "
                "de notas pendientes de reversión para el docente "
                "y trayecto seleccionados."
            )
        })

    return JsonResponse({
        "estado": "exito",
        "datos": {
            "id_periodo_academico": periodo.periodo_academico_id,
            "nombre": periodo.periodo_academico.nombre
        }
    })

def cant_est_rem(request):
    if request.method != "POST":
        return JsonResponse({
            "estado": "fallo",
            "title": "Error",
            "icon": "error",
            "descripcion": "Método de solicitud no permitido."
        })

    pnf_seleccionado = request.POST.get("pnf_seleccionado")
    docente_seleccionado = request.POST.get("docente_seleccionado")
    trayecto_seleccionado = request.POST.get("trayecto_seleccionado")
    materia_seleccionado = request.POST.get("materia_seleccionado")
    periodo_academico_seleccionado = request.POST.get(
        "periodo_academico_seleccionado"
    )

    cedula = request.session.get("cedula_usuario")

    if not cedula:
        return JsonResponse({
            "estado": "fallo",
            "title": "Sesión",
            "icon": "warning",
            "descripcion": (
                "No se pudo identificar al usuario de la sesión."
            )
        })

    if not all([
        pnf_seleccionado,
        docente_seleccionado,
        trayecto_seleccionado,
        materia_seleccionado,
        periodo_academico_seleccionado
    ]):
        return JsonResponse({
            "estado": "fallo",
            "title": "Datos incompletos",
            "icon": "warning",
            "descripcion": (
                "Faltan datos para obtener la cantidad "
                "de modificaciones."
            )
        })

    control_estudio = (
        ControlEstudio.objects
        .filter(
            usuario__cedula_identidad=cedula,
            activo=True
        )
        .select_related("nucleo")
        .first()
    )

    if not control_estudio:
        return JsonResponse({
            "estado": "fallo",
            "title": "Control de Estudio",
            "icon": "error",
            "descripcion": (
                "El usuario no posee un perfil activo de "
                "Control de Estudio."
            )
        })

    nucleo = control_estudio.nucleo_id

    if not PNFNucleo.objects.filter(
        id_nucleo=nucleo,
        id_pnf=pnf_seleccionado
    ).exists():
        return JsonResponse({
            "estado": "fallo",
            "title": "P.N.F no válido",
            "icon": "warning",
            "descripcion": (
                "El P.N.F seleccionado no está asociado "
                "al núcleo de Control de Estudio."
            )
        })

    docente = (
        Docente.objects
        .filter(
            usuario__cedula_identidad=docente_seleccionado,
            nucleo_id=nucleo,
            pnf_id=pnf_seleccionado,
            activo=True
        )
        .first()
    )

    if not docente:
        return JsonResponse({
            "estado": "fallo",
            "title": "Docente",
            "icon": "warning",
            "descripcion": (
                "El docente seleccionado no posee un registro "
                "activo para el núcleo y P.N.F seleccionados."
            )
        })

    docente_asignado = (
        DocenteAsignadoMateria.objects
        .filter(
            docente=docente,
            materia_asignada_id=materia_seleccionado,
            activo=True,
            materia_asignada__activo=True,
            materia_asignada__materia__activa=True,
            materia_asignada__materia__id_pnf=pnf_seleccionado,
            materia_asignada__materia__id_trayecto_id=(
                trayecto_seleccionado
            )
        )
        .select_related("materia_asignada__materia")
        .first()
    )

    if not docente_asignado:
        return JsonResponse({
            "estado": "vacio",
            "cantidad_estudiantes": 0,
            "cantidad_modificaciones": 0,
            "title": "Materia asignada",
            "descripcion": (
                "El docente no posee una asignación activa "
                "para la materia y trayecto seleccionados."
            ),
            "icon": "info"
        })

    periodo_materia = (
        PeriodoAcademicoMateria.objects
        .filter(
            materia=docente_asignado.materia_asignada.materia,
            periodo_id=periodo_academico_seleccionado
        )
        .select_related("periodo")
        .first()
    )

    if not periodo_materia:
        return JsonResponse({
            "estado": "vacio",
            "cantidad_estudiantes": 0,
            "cantidad_modificaciones": 0,
            "title": "Período académico",
            "descripcion": (
                "El período académico seleccionado no está "
                "asociado a la materia."
            ),
            "icon": "info"
        })

    detalles_pendientes = (
        HistorialDetalleNota.objects
        .filter(
            historial__docente_asignado=docente_asignado,
            historial__periodo_academico=periodo_materia.periodo,
            historial__trayecto_id=trayecto_seleccionado,
            historial__calificacion__materia_asignada_id=(
                materia_seleccionado
            ),
            historial__calificacion__estudiante__nucleo_id=nucleo,
            historial__calificacion__estudiante__pnf_id=pnf_seleccionado,
            revertido=False
        )
    )

    cantidad_modificaciones = detalles_pendientes.count()

    cantidad_estudiantes = (
        detalles_pendientes
        .values("estudiante_id")
        .distinct()
        .count()
    )

    if cantidad_modificaciones == 0:
        return JsonResponse({
            "estado": "vacio",
            "cantidad_estudiantes": 0,
            "cantidad_modificaciones": 0,
            "title": "Sin modificaciones pendientes",
            "icon": "info",
            "descripcion": (
                "No existen modificaciones de notas pendientes "
                "de reversión para la materia, trayecto y período "
                "seleccionados."
            )
        })

    return JsonResponse({
        "estado": "exito",
        "cantidad_estudiantes": cantidad_estudiantes,
        "cantidad_modificaciones": cantidad_modificaciones
    })

def rem_calif_mod(request):
    if request.method != "POST":
        return JsonResponse({
            "estado": "fallo",
            "title": "Error",
            "icon": "error",
            "descripcion": "Método de solicitud no permitido."
        })

    pnf_seleccionado = request.POST.get("pnf_seleccionado")
    docente_seleccionado = request.POST.get("docente_seleccionado")
    trayecto_seleccionado = request.POST.get("trayecto_seleccionado")
    materia_seleccionado = request.POST.get("materia_seleccionado")
    periodo_academico_seleccionado = request.POST.get(
        "periodo_academico_seleccionado"
    )

    cedula = request.session.get("cedula_usuario")

    if not cedula:
        return JsonResponse({
            "estado": "fallo",
            "title": "Sesión",
            "icon": "warning",
            "descripcion": "No se pudo identificar al usuario de la sesión."
        })

    if not all([
        pnf_seleccionado,
        docente_seleccionado,
        trayecto_seleccionado,
        materia_seleccionado,
        periodo_academico_seleccionado
    ]):
        return JsonResponse({
            "estado": "fallo",
            "title": "Datos incompletos",
            "icon": "warning",
            "descripcion": (
                "Faltan datos para consultar las modificaciones "
                "de notas registradas."
            )
        })

    control_estudio = ControlEstudio.objects.filter(
        usuario__cedula_identidad=cedula,
        activo=True
    ).first()

    if not control_estudio:
        return JsonResponse({
            "estado": "fallo",
            "title": "Control de Estudio",
            "icon": "error",
            "descripcion": (
                "El usuario no posee un perfil activo de "
                "Control de Estudio."
            )
        })

    nucleo_id = control_estudio.nucleo_id

    if not PNFNucleo.objects.filter(
        id_nucleo=nucleo_id,
        id_pnf=pnf_seleccionado
    ).exists():
        return JsonResponse({
            "estado": "fallo",
            "title": "P.N.F no válido",
            "icon": "warning",
            "descripcion": (
                "El P.N.F seleccionado no está asociado al núcleo "
                "de Control de Estudio."
            )
        })

    docente = Docente.objects.filter(
        usuario__cedula_identidad=docente_seleccionado,
        nucleo_id=nucleo_id,
        pnf_id=pnf_seleccionado,
        activo=True
    ).first()

    if not docente:
        return JsonResponse({
            "estado": "fallo",
            "title": "Docente",
            "icon": "warning",
            "descripcion": (
                "El docente seleccionado no posee un registro activo "
                "para el núcleo y P.N.F seleccionados."
            )
        })

    docente_asignado = (
        DocenteAsignadoMateria.objects
        .filter(
            docente=docente,
            materia_asignada_id=materia_seleccionado,
            activo=True,
            materia_asignada__activo=True,
            materia_asignada__materia__activa=True,
            materia_asignada__materia__id_pnf=pnf_seleccionado,
            materia_asignada__materia__id_trayecto_id=(
                trayecto_seleccionado
            )
        )
        .select_related("materia_asignada__materia")
        .first()
    )

    if not docente_asignado:
        return JsonResponse({
            "estado": "vacio",
            "datos": [],
            "title": "Sin asignación",
            "descripcion": (
                "El docente no posee una asignación activa "
                "para la materia seleccionada."
            ),
            "icon": "info"
        })

    periodo_materia = (
        PeriodoAcademicoMateria.objects
        .filter(
            materia=docente_asignado.materia_asignada.materia,
            periodo_id=periodo_academico_seleccionado
        )
        .select_related("periodo")
        .first()
    )

    if not periodo_materia:
        return JsonResponse({
            "estado": "vacio",
            "datos": [],
            "title": "Período académico",
            "descripcion": (
                "La materia seleccionada no está asociada "
                "al período académico indicado."
            ),
            "icon": "info"
        })

    historiales = (
        HistorialModificacionNotas.objects
        .filter(
            docente_asignado=docente_asignado,
            periodo_academico=periodo_materia.periodo,
            trayecto_id=trayecto_seleccionado,
            detalles__revertido=False
        )
        .select_related(
            "docente_asignado",
            "docente_asignado__docente",
            "docente_asignado__materia_asignada",
            "docente_asignado__materia_asignada__materia",
            "periodo_academico",
            "trayecto",
            "calificacion",
            "usuario_modifica"
        )
        .prefetch_related(
            "detalles__estudiante",
            "detalles__estudiante__usuario",
            "detalles__detalle_calificacion_unidad",
            "detalles__detalle_calificacion_unidad__unidad"
        )
        .distinct()
        .order_by("-fecha_modificacion", "-id_historial")
    )

    datos = []

    for historial in historiales:
        calificacion = historial.calificacion

        for detalle_historial in historial.detalles.filter(
            revertido=False
        ):
            estudiante = detalle_historial.estudiante

            if not estudiante or not estudiante.usuario:
                continue

            usuario_estudiante = estudiante.usuario
            unidad = detalle_historial.detalle_calificacion_unidad

            datos.append({
                "id_historial": historial.id_historial,
                "perfil_modificacion": historial.perfil_modificacion,
                "fecha_modificacion": (
                    historial.fecha_modificacion.strftime(
                        "%d/%m/%Y %H:%M"
                    )
                    if historial.fecha_modificacion else None
                ),
                "motivo": historial.motivo,

                "id_docente_asignado": historial.docente_asignado_id,
                "id_periodo_academico": historial.periodo_academico_id,
                "periodo_academico": (
                    historial.periodo_academico.nombre
                    if historial.periodo_academico else None
                ),

                "id_trayecto": historial.trayecto_id,
                "trayecto": (
                    historial.trayecto.nombre
                    if historial.trayecto else None
                ),

                "id_usuario_modifica": historial.usuario_modifica_id,
                "usuario_modifica": (
                    f"{historial.usuario_modifica.nombres} "
                    f"{historial.usuario_modifica.apellidos}"
                    if historial.usuario_modifica else None
                ),
                "cedula_usuario_modifica": (
                    historial.usuario_modifica.cedula_identidad
                    if historial.usuario_modifica else None
                ),

                "id_estudiante": estudiante.id_estudiante,
                "nombre_completo": (
                    f"{usuario_estudiante.nombres} "
                    f"{usuario_estudiante.apellidos}"
                ),
                "cedula": usuario_estudiante.cedula_identidad,

                "id_calificaciones": (
                    calificacion.id_calificaciones
                    if calificacion else None
                ),
                "promedio_tramo": (
                    float(calificacion.promedio_tramo)
                    if calificacion
                    and calificacion.promedio_tramo is not None
                    else None
                ),
                "asistencia": (
                    float(calificacion.asistencia)
                    if calificacion
                    and calificacion.asistencia is not None
                    else None
                ),
                "condicion": (
                    calificacion.condicion if calificacion else None
                ),

                "id_detalle": detalle_historial.id_detalle,
                "id_historial_detalle": detalle_historial.id_detalle,

                "id_detalle_calificaciones_unidad": (
                    unidad.id_detalle_calificaciones_unidad
                    if unidad else None
                ),
                "id_unidad": unidad.unidad_id if unidad else None,
                "nombre_unidad": (
                    unidad.unidad.titulo_unidad
                    if unidad and unidad.unidad else None
                ),

                "nota_anterior": (
                    float(detalle_historial.nota_anterior)
                    if detalle_historial.nota_anterior is not None
                    else None
                ),
                "nota_nueva": (
                    float(detalle_historial.nota_nueva)
                    if detalle_historial.nota_nueva is not None
                    else None
                ),

                "asistencia_anterior": (
                    float(detalle_historial.asistencia_anterior)
                    if detalle_historial.asistencia_anterior is not None
                    else None
                ),
                "asistencia_nueva": (
                    float(detalle_historial.asistencia_nueva)
                    if detalle_historial.asistencia_nueva is not None
                    else None
                ),

                "promedio_anterior": (
                    float(detalle_historial.promedio_anterior)
                    if detalle_historial.promedio_anterior is not None
                    else None
                ),
                "promedio_nuevo": (
                    float(detalle_historial.promedio_nuevo)
                    if detalle_historial.promedio_nuevo is not None
                    else None
                )
            })

    if not datos:
        return JsonResponse({
            "estado": "vacio",
            "datos": [],
            "title": "Sin modificaciones pendientes",
            "descripcion": (
                "No existen modificaciones de notas pendientes "
                "de reversión para los criterios seleccionados."
            ),
            "icon": "info"
        })

    datos.sort(
        key=lambda registro: (
            registro["nombre_completo"].lower(),
            registro["fecha_modificacion"] or "",
            registro["id_historial"],
            registro["id_detalle"]
        )
    )

    return JsonResponse({
        "estado": "exito",
        "datos": datos
    })

@transaction.atomic
def rem_camb_not(request):
    if request.method != "POST":
        return JsonResponse({
            "estado": "fallo",
            "title": "Error",
            "icon": "error",
            "descripcion": "Método de solicitud no permitido."
        })

    id_historial = request.POST.get("id_historial")
    id_detalle = request.POST.get("id_detalle")
    cedula = request.session.get("cedula_usuario")

    if not cedula:
        return JsonResponse({
            "estado": "fallo",
            "title": "Sesión",
            "icon": "warning",
            "descripcion": "No se pudo identificar al usuario de la sesión."
        })

    try:
        id_historial = int(id_historial)
        id_detalle = int(id_detalle)
    except (TypeError, ValueError):
        return JsonResponse({
            "estado": "fallo",
            "title": "Identificador inválido",
            "icon": "warning",
            "descripcion": "Los identificadores no son válidos."
        })

    usuario = Usuario.objects.filter(
        cedula_identidad=cedula
    ).first()

    if not usuario:
        return JsonResponse({
            "estado": "fallo",
            "title": "Usuario",
            "icon": "error",
            "descripcion": "No se encontró el usuario de la sesión."
        })

    control_estudio = ControlEstudio.objects.filter(
        usuario=usuario,
        activo=True
    ).first()

    if not control_estudio:
        return JsonResponse({
            "estado": "fallo",
            "title": "Control de Estudio",
            "icon": "error",
            "descripcion": (
                "El usuario no posee un perfil activo de Control de Estudio."
            )
        })

    try:
        historial = (
            HistorialModificacionNotas.objects
            .select_for_update()
            .get(id_historial=id_historial)
        )
    except HistorialModificacionNotas.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "title": "Modificación no encontrada",
            "icon": "warning",
            "descripcion": "La modificación seleccionada no existe."
        })

    try:
        detalle = (
            HistorialDetalleNota.objects
            .select_for_update()
            .get(
                id_detalle=id_detalle,
                historial=historial
            )
        )
    except HistorialDetalleNota.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "title": "Detalle no encontrado",
            "icon": "warning",
            "descripcion": (
                "El detalle seleccionado no pertenece al historial indicado."
            )
        })

    if detalle.revertido:
        return JsonResponse({
            "estado": "fallo",
            "title": "Detalle ya revertido",
            "icon": "warning",
            "descripcion": (
                "Esta nota ya fue revertida y no puede revertirse nuevamente."
            )
        })

    if detalle.nota_anterior is None:
        return JsonResponse({
            "estado": "fallo",
            "title": "Nota anterior no disponible",
            "icon": "warning",
            "descripcion": (
                "El historial no contiene la nota anterior que debe restaurarse."
            )
        })

    if not historial.calificacion_id:
        return JsonResponse({
            "estado": "fallo",
            "title": "Calificación no encontrada",
            "icon": "warning",
            "descripcion": (
                "El historial no tiene una calificación asociada."
            )
        })

    try:
        calificacion = (
            Calificaciones.objects
            .select_for_update()
            .get(id_calificaciones=historial.calificacion_id)
        )
    except Calificaciones.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "title": "Calificación no encontrada",
            "icon": "warning",
            "descripcion": "La calificación asociada ya no existe."
        })

    if not detalle.detalle_calificacion_unidad_id:
        return JsonResponse({
            "estado": "fallo",
            "title": "Nota no disponible",
            "icon": "warning",
            "descripcion": (
                "El detalle no está asociado a una nota de unidad."
            )
        })

    try:
        unidad = (
            DetalleCalificacionesUnidad.objects
            .select_for_update()
            .get(
                id_detalle_calificaciones_unidad=(
                    detalle.detalle_calificacion_unidad_id
                ),
                calificacion=calificacion
            )
        )
    except DetalleCalificacionesUnidad.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "title": "Unidad no encontrada",
            "icon": "warning",
            "descripcion": (
                "La unidad relacionada con la nota no existe "
                "o no pertenece a la calificación indicada."
            )
        })

    if unidad.nota_unidad != detalle.nota_nueva:
        return JsonResponse({
            "estado": "fallo",
            "title": "Nota modificada posteriormente",
            "icon": "warning",
            "descripcion": (
                "La nota actual no coincide con la registrada en el historial. "
                "No se realizó ningún cambio."
            )
        })

    if not calificacion.materia_asignada_id:
        return JsonResponse({
            "estado": "fallo",
            "title": "Materia no encontrada",
            "icon": "warning",
            "descripcion": (
                "La calificación no tiene una materia asignada."
            )
        })

    nombre_materia = (
        MateriaAsignada.objects
        .filter(
            id_materia_asignada=calificacion.materia_asignada_id
        )
        .values_list("materia__nombre", flat=True)
        .first()
    )

    if not nombre_materia:
        return JsonResponse({
            "estado": "fallo",
            "title": "Materia no encontrada",
            "icon": "warning",
            "descripcion": (
                "No se pudo identificar la materia asociada."
            )
        })

    nombre_materia = nombre_materia.strip().casefold()

    es_proyecto = "proyecto socio tecnológico" in nombre_materia
    nota_aprobacion = Decimal("16") if es_proyecto else Decimal("12")

    notas_unidad = list(
        DetalleCalificacionesUnidad.objects
        .filter(calificacion=calificacion)
        .exclude(
            id_detalle_calificaciones_unidad=(
                detalle.detalle_calificacion_unidad_id
            )
        )
        .values_list("nota_unidad", flat=True)
    )

    notas_unidad.append(detalle.nota_anterior)

    notas_validas = [
        nota for nota in notas_unidad
        if nota is not None
    ]

    if not notas_validas:
        return JsonResponse({
            "estado": "fallo",
            "title": "Promedio no disponible",
            "icon": "warning",
            "descripcion": (
                "No existen notas válidas para calcular el promedio."
            )
        })

    promedio_recalculado = (
        sum(notas_validas, Decimal("0")) / len(notas_validas)
    ).quantize(Decimal("0.01"))

    asistencia = (
        calificacion.asistencia
        if calificacion.asistencia is not None
        else Decimal("0")
    )

    if asistencia < Decimal("75"):
        condicion = "REPROBADO"
    elif promedio_recalculado >= nota_aprobacion:
        condicion = "APROBADO"
    elif es_proyecto:
        condicion = "REPROBADO"
    else:
        condicion = "REPARACIÓN"

    ahora = timezone.now()

    nota_restaurada = detalle.nota_anterior

    unidad.nota_unidad = nota_restaurada
    unidad.modificado_por = usuario
    unidad.fecha_modificacion = ahora
    unidad.perfil_modificacion = "CONTROL_ESTUDIO"

    unidad.save(update_fields=[
        "nota_unidad",
        "modificado_por",
        "fecha_modificacion",
        "perfil_modificacion"
    ])

    calificacion.promedio_tramo = promedio_recalculado
    calificacion.condicion = condicion
    calificacion.modificado_por = usuario
    calificacion.fecha_modificacion = ahora
    calificacion.perfil_modificacion = "CONTROL_ESTUDIO"

    calificacion.save(update_fields=[
        "promedio_tramo",
        "condicion",
        "modificado_por",
        "fecha_modificacion",
        "perfil_modificacion"
    ])

    detalle.revertido = True

    detalle.save(update_fields=["revertido"])

    return JsonResponse({
        "estado": "exito",
        "title": "Reversión realizada",
        "icon": "success",
        "descripcion": (
            "La nota individual fue restaurada correctamente. "
            "El detalle quedó marcado como revertido y ya no debe "
            "mostrarse en el listado. Se actualizaron el promedio "
            "y la condición de la calificación."
        ),
        "id_historial": historial.id_historial,
        "id_detalle": detalle.id_detalle,
        "nota_restaurada": str(nota_restaurada),
        "promedio_recalculado": str(calificacion.promedio_tramo),
        "condicion": calificacion.condicion
    })

def rem_not_acad(request):
    return render(request, "Roles/Control_Estudio/Remover_Cambios_Notas/remover_notas_academica.html") 