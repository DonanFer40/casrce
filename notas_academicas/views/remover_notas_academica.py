from django.shortcuts import render
from django.http import JsonResponse
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from django.db.models import F, Exists, OuterRef, Q, Prefetch

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
            "descripcion": (
                "No se encontró la cédula del usuario en la sesión."
            ),
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
            "datos": [],
            "title": "Control de Estudio",
            "descripcion": (
                "El usuario no posee un perfil activo de "
                "Control de Estudio."
            ),
            "icon": "error"
        })

    nucleo_id = control_estudio.nucleo_id

    # VALIDAR PNF DEL NÚCLEO
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

    # DOCENTES CON MODIFICACIONES REGISTRADAS
    historiales = (
        HistorialModificacionNotas.objects
        .filter(
            docente_asignado__docente__nucleo_id=nucleo_id,
            docente_asignado__docente__pnf_id=pnf_seleccionado,
            docente_asignado__docente__activo=True,
            tipo_modificacion="MODIFICACION"
        )
        .select_related(
            "docente_asignado__docente__usuario"
        )
    )

    # NO EXISTEN MODIFICACIONES
    if not historiales.exists():
        return JsonResponse({
            "estado": "vacio",
            "datos": [],
            "title": "Sin modificaciones",
            "descripcion": (
                "No existen docentes con modificaciones "
                "de notas registradas para el P.N.F seleccionado."
            ),
            "icon": "info"
        })
    
    # OBTENER DOCENTES SIN DUPLICADOS
    docentes = {}
    for historial in historiales:
        docente_asignado = historial.docente_asignado

        if not docente_asignado:
            continue

        docente = docente_asignado.docente

        if not docente:
            continue

        docentes[docente.id_docente] = {
            "id_docente": docente.id_docente,
            "cedula": docente.usuario.cedula_identidad,
            "nombres": docente.usuario.nombres,
            "apellidos": docente.usuario.apellidos
        }

    if not docentes:
        return JsonResponse({
            "estado": "vacio",
            "datos": [],
            "title": "Sin modificaciones",
            "descripcion": (
                "No existen docentes con modificaciones "
                "de notas registradas para el P.N.F seleccionado."
            ),
            "icon": "info"
        })

    datos = list(docentes.values())

    datos.sort(
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
            "descripcion": (
                "No se pudo identificar al usuario de la sesión."
            )
        })

    if not pnf_seleccionado:
        return JsonResponse({
            "estado": "fallo",
            "title": "P.N.F",
            "icon": "warning",
            "descripcion": (
                "Debe seleccionar un P.N.F."
            )
        })

    if not docente_seleccionado:
        return JsonResponse({
            "estado": "fallo",
            "title": "Docente",
            "icon": "warning",
            "descripcion": (
                "Debe seleccionar un docente."
            )
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
            "title": "Control de Estudio",
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

    # DOCENTE
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

    # PERÍODOS ACTUALMENTE HABILITADOS
    periodos_actuales = calendarios_periodos.values_list(
        "periodo_id",
        flat=True
    )

    trayectos = (
        TrayectoAcademico.objects
        .filter(
            materia__id_pnf=pnf_seleccionado,
            materia__activa=True,

            materia__asignaciones__activo=True,

            materia__asignaciones__docentes__docente=docente,
            materia__asignaciones__docentes__activo=True,

            materia__asignaciones__docentes__historial_modificaciones_notas__tipo_modificacion=(
                "MODIFICACION"
            ),

            materia__periodos_academicos__periodo_id__in=periodos_actuales
        )
        .distinct()
        .order_by(
            "id_periodo_academico"
        )
    )

    if not trayectos.exists():
        return JsonResponse({
            "estado": "vacio",
            "trayectos": [],
            "title": "Sin cambios de carga de notas",
            "icon": "info",
            "descripcion": (
                "El docente seleccionado no tiene cambios de "
                "carga de notas registrados para el P.N.F "
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

    # MATERIAS DEL DOCENTE CON CAMBIOS DE NOTAS
    materias_asignadas = (
        DocenteAsignadoMateria.objects
        .filter(
            docente=docente_obj,
            activo=True,

            materia_asignada__activo=True,

            materia_asignada__materia__activa=True,
            materia_asignada__materia__id_pnf_id=pnf_seleccionado,
            materia_asignada__materia__id_trayecto_id=trayecto_seleccionado,

            # El historial pertenece directamente a
            # DocenteAsignadoMateria.
            historial_modificaciones_notas__isnull=False,

            # Solo historiales pertenecientes a períodos
            # actualmente habilitados.
            historial_modificaciones_notas__periodo_academico_id__in=(
                periodos_actuales
            ),

            # Solo modificaciones que todavía no han sido revertidas.
            historial_modificaciones_notas__tipo_modificacion="MODIFICACION"
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
            "title": "Sin cambios de carga de notas",
            "descripcion": (
                "El P.N.F seleccionado no tiene cambios de carga "
                "de notas registrados para el docente y trayecto "
                "seleccionados."
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

    # CONTROL DE ESTUDIO
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

    # VALIDAR PNF DEL NÚCLEO
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

    # VALIDAR DOCENTE
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

    # VALIDAR MATERIA ASIGNADA
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
            periodo_academico__isnull=False
        )
        .select_related("periodo_academico")
        .order_by("-fecha_modificacion")
        .first()
    )

    if not periodo:
        return JsonResponse({
            "estado": "vacio",
            "datos": [],
            "title": "Sin modificaciones de notas",
            "icon": "info",
            "descripcion": (
                "La materia seleccionada no tiene cambios de "
                "calificaciones registrados para este docente."
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
            "descripcion": (
                "Método de solicitud no permitido."
            )
        })

    pnf_seleccionado = request.POST.get("pnf_seleccionado")
    docente_seleccionado = request.POST.get("docente_seleccionado")
    trayecto_seleccionado = request.POST.get("trayecto_seleccionado")
    materia_seleccionado = request.POST.get("materia_seleccionado")
    periodo_academico_seleccionado = request.POST.get("periodo_academico_seleccionado")

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
                "de estudiantes."
            )
        })

    # CONTROL DE ESTUDIO
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

    # VALIDAR PNF DEL NÚCLEO
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

    # VALIDAR DOCENTE
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

    # VALIDAR MATERIA ASIGNADA
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
        .first()
    )

    if not docente_asignado:
        return JsonResponse({
            "estado": "fallo",
            "title": "Materia asignada",
            "icon": "warning",
            "descripcion": (
                "El docente no posee una asignación activa "
                "para la materia y trayecto seleccionados."
            )
        })

    # VALIDAR PERÍODO ACADÉMICO
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
            "estado": "fallo",
            "title": "Período académico",
            "icon": "warning",
            "descripcion": (
                "El período académico seleccionado no está "
                "asociado a la materia."
            )
        })

    # CONTAR ESTUDIANTES CON MODIFICACIONES
    cantidad_estudiantes = (
        HistorialDetalleNota.objects
        .filter(
            historial__docente_asignado=docente_asignado,
            historial__periodo_academico=(
                periodo_materia.periodo
            ),
            historial__trayecto_id=trayecto_seleccionado,
            historial__tipo_modificacion="MODIFICACION",
            estudiante__nucleo_id=nucleo,
            estudiante__pnf_id=pnf_seleccionado
        )
        .values(
            "estudiante_id"
        )
        .distinct()
        .count()
    )
    print(cantidad_estudiantes)

    if cantidad_estudiantes == 0:
        return JsonResponse({
            "estado": "vacio",
            "cantidad_estudiantes": 0,
            "title": "Sin cambios de carga de nota",
            "icon": "info",
            "descripcion": (
                "No existen estudiantes con modificaciones "
                "de notas para la materia, trayecto y período "
                "seleccionados."
            )
        })

    return JsonResponse({
        "estado": "exito",
        "cantidad_estudiantes": cantidad_estudiantes
    })

def rem_calif_mod(request):
    if request.method != "POST":
        return JsonResponse({
            "estado": "fallo",
            "title": "Error",
            "icon": "error",
            "descripcion": (
                "Método de solicitud no permitido."
            )
        })

    pnf_seleccionado = request.POST.get("pnf_seleccionado")
    docente_seleccionado = request.POST.get("docente_seleccionado")
    trayecto_seleccionado = request.POST.get("trayecto_seleccionado")
    materia_seleccionado = request.POST.get("materia_seleccionado")
    periodo_academico_seleccionado = request.POST.get("periodo_academico_seleccionado")

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
                "Faltan datos para consultar las modificaciones "
                "de notas registradas."
            )
        })

    # CONTROL DE ESTUDIO
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

    nucleo_id = control_estudio.nucleo_id

    # VALIDAR PNF DEL NÚCLEO
    if not PNFNucleo.objects.filter(
        id_nucleo=nucleo_id,
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

    # DOCENTE
    docente = (
        Docente.objects
        .filter(
            usuario__cedula_identidad=docente_seleccionado,
            nucleo_id=nucleo_id,
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

    # ASIGNACIÓN DEL DOCENTE A LA MATERIA
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
        .select_related(
            "materia_asignada__materia"
        )
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

    # PERÍODO ACADÉMICO
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

    # HISTORIALES DE MODIFICACIÓN
    #
    # IMPORTANTE:
    # Solo se muestran modificaciones que todavía pueden
    # ser revertidas. Una vez revertido el historial,
    # tipo_modificacion pasa a REVERSION y deja de aparecer.
    historiales = (
        HistorialModificacionNotas.objects
        .filter(
            docente_asignado=docente_asignado,
            periodo_academico=periodo_materia.periodo,
            trayecto_id=trayecto_seleccionado,
            tipo_modificacion="MODIFICACION"
        )
        .select_related(
            "docente_asignado",
            "docente_asignado__docente",
            "docente_asignado__materia_asignada",
            "docente_asignado__materia_asignada__materia",
            "periodo_academico",
            "trayecto",
            "calificacion",
            "calificacion__estudiante",
            "calificacion__estudiante__usuario",
            "usuario_modifica"
        )
        .prefetch_related(
            "detalles__estudiante",
            "detalles__detalle_calificacion_unidad",
            "detalles__detalle_calificacion_unidad__unidad"
        )
        .order_by(
            "-fecha_modificacion",
            "-id_historial"
        )
    )

    if not historiales.exists():
        return JsonResponse({
            "estado": "vacio",
            "datos": [],
            "title": "Sin cambios de carga de nota",
            "descripcion": (
                "No existen modificaciones de notas pendientes "
                "de reversión para los criterios seleccionados."
            ),
            "icon": "info"
        })

    estudiantes = {}

    for historial in historiales:

        calificacion = historial.calificacion

        if not calificacion:
            continue

        estudiante = calificacion.estudiante

        if not estudiante:
            continue

        usuario_estudiante = estudiante.usuario

        if not usuario_estudiante:
            continue

        id_estudiante = estudiante.id_estudiante

        if id_estudiante not in estudiantes:

            estudiantes[id_estudiante] = {
                # HISTORIAL
                "id_historial": historial.id_historial,
                "perfil_modificacion": (
                    historial.perfil_modificacion
                ),
                "fecha_modificacion": (
                    historial.fecha_modificacion.strftime(
                        "%d/%m/%Y %H:%M"
                    )
                    if historial.fecha_modificacion
                    else None
                ),
                "motivo": historial.motivo,
                "tipo_modificacion": (
                    historial.tipo_modificacion
                ),

                # DOCENTE ASIGNADO
                "id_docente_asignado": (
                    historial.docente_asignado_id
                ),

                # PERÍODO
                "id_periodo_academico": (
                    historial.periodo_academico_id
                ),
                "periodo_academico": (
                    historial.periodo_academico.nombre
                    if historial.periodo_academico
                    else None
                ),

                # TRAYECTO
                "id_trayecto": historial.trayecto_id,
                "trayecto": (
                    historial.trayecto.nombre
                    if historial.trayecto
                    else None
                ),

                # USUARIO QUE MODIFICÓ
                "id_usuario_modifica": (
                    historial.usuario_modifica_id
                ),
                "usuario_modifica": (
                    f"{historial.usuario_modifica.nombres} "
                    f"{historial.usuario_modifica.apellidos}"
                    if historial.usuario_modifica
                    else None
                ),
                "cedula_usuario_modifica": (
                    historial.usuario_modifica.cedula_identidad
                    if historial.usuario_modifica
                    else None
                ),

                # ESTUDIANTE
                "id_estudiante": id_estudiante,
                "nombre_completo": (
                    f"{usuario_estudiante.nombres} "
                    f"{usuario_estudiante.apellidos}"
                ),
                "cedula": (
                    usuario_estudiante.cedula_identidad
                ),

                # CALIFICACIÓN
                "id_calificaciones": (
                    calificacion.id_calificaciones
                ),
                "promedio_tramo": (
                    float(calificacion.promedio_tramo)
                    if calificacion.promedio_tramo is not None
                    else None
                ),
                "asistencia": (
                    float(calificacion.asistencia)
                    if calificacion.asistencia is not None
                    else None
                ),
                "condicion": calificacion.condicion,

                # DETALLES
                "detalles": []
            }

        estudiante_data = estudiantes[id_estudiante]

        for detalle_historial in historial.detalles.all():

            unidad = (
                detalle_historial.detalle_calificacion_unidad
            )

            estudiante_data["detalles"].append({
                # HISTORIAL DETALLE
                "id_detalle": (
                    detalle_historial.id_detalle
                ),
                "id_historial": (
                    detalle_historial.historial_id
                ),

                # ESTUDIANTE
                "id_estudiante": (
                    detalle_historial.estudiante_id
                ),

                # DETALLE DE UNIDAD
                "id_detalle_calificaciones_unidad": (
                    unidad.id_detalle_calificaciones_unidad
                    if unidad
                    else None
                ),

                # UNIDAD
                "id_unidad": (
                    unidad.unidad_id
                    if unidad
                    else None
                ),
                "nombre_unidad": (
                    unidad.unidad.titulo_unidad
                    if unidad and unidad.unidad
                    else None
                ),

                # NOTA ANTERIOR
                "nota_anterior": (
                    float(detalle_historial.nota_anterior)
                    if detalle_historial.nota_anterior is not None
                    else None
                ),

                # NOTA NUEVA
                "nota_nueva": (
                    float(detalle_historial.nota_nueva)
                    if detalle_historial.nota_nueva is not None
                    else None
                ),

                # ASISTENCIA ANTERIOR
                "asistencia_anterior": (
                    float(
                        detalle_historial.asistencia_anterior
                    )
                    if (
                        detalle_historial.asistencia_anterior
                        is not None
                    )
                    else None
                ),

                # ASISTENCIA NUEVA
                "asistencia_nueva": (
                    float(
                        detalle_historial.asistencia_nueva
                    )
                    if (
                        detalle_historial.asistencia_nueva
                        is not None
                    )
                    else None
                ),

                # PROMEDIO ANTERIOR
                "promedio_anterior": (
                    float(
                        detalle_historial.promedio_anterior
                    )
                    if (
                        detalle_historial.promedio_anterior
                        is not None
                    )
                    else None
                ),

                # PROMEDIO NUEVO
                "promedio_nuevo": (
                    float(
                        detalle_historial.promedio_nuevo
                    )
                    if (
                        detalle_historial.promedio_nuevo
                        is not None
                    )
                    else None
                )
            })

    if not estudiantes:
        return JsonResponse({
            "estado": "vacio",
            "datos": [],
            "title": "Sin estudiantes",
            "descripcion": (
                "No existen estudiantes asociados a "
                "las modificaciones de notas pendientes "
                "de reversión."
            ),
            "icon": "info"
        })

    datos = list(
        estudiantes.values()
    )

    datos.sort(
        key=lambda estudiante: (
            estudiante["nombre_completo"].lower()
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
            "descripcion": (
                "Método de solicitud no permitido."
            )
        })

    id_historial = request.POST.get("id_historial")
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

    if not id_historial:
        return JsonResponse({
            "estado": "fallo",
            "title": "Modificación",
            "icon": "warning",
            "descripcion": (
                "Debe seleccionar una modificación "
                "para realizar la reversión."
            )
        })

    # USUARIO
    usuario = (
        Usuario.objects
        .filter(
            cedula_identidad=cedula
        )
        .first()
    )

    if not usuario:
        return JsonResponse({
            "estado": "fallo",
            "title": "Usuario",
            "icon": "error",
            "descripcion": (
                "No se encontró el usuario asociado "
                "a la sesión."
            )
        })

    # CONTROL DE ESTUDIO
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
                "El usuario no posee un perfil activo "
                "de Control de Estudio."
            )
        })

    # VALIDAR ID DEL HISTORIAL
    try:
        id_historial = int(id_historial)
    except (TypeError, ValueError):
        return JsonResponse({
            "estado": "fallo",
            "title": "Modificación",
            "icon": "warning",
            "descripcion": (
                "El identificador de la modificación "
                "no es válido."
            )
        })

    # HISTORIAL DE MODIFICACIÓN
    try:
        historial = (
            HistorialModificacionNotas.objects
            .select_for_update()
            .get(
                id_historial=id_historial
            )
        )

    except HistorialModificacionNotas.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "title": "Modificación no encontrada",
            "icon": "warning",
            "descripcion": (
                "La modificación seleccionada no existe."
            )
        })

    # VALIDAR ESTADO DEL HISTORIAL
    if historial.tipo_modificacion == "REVERSION":
        return JsonResponse({
            "estado": "fallo",
            "title": "Modificación ya revertida",
            "icon": "warning",
            "descripcion": (
                "La modificación seleccionada ya fue "
                "revertida y no puede volver a revertirse."
            )
        })

    if historial.tipo_modificacion != "MODIFICACION":
        return JsonResponse({
            "estado": "fallo",
            "title": "Estado no válido",
            "icon": "warning",
            "descripcion": (
                "La modificación seleccionada posee "
                "un estado no válido para realizar la reversión."
            )
        })

    # CALIFICACIÓN RELACIONADA CON EL HISTORIAL
    if not historial.calificacion_id:
        return JsonResponse({
            "estado": "fallo",
            "title": "Calificación no encontrada",
            "icon": "warning",
            "descripcion": (
                "La modificación seleccionada no tiene "
                "una calificación asociada."
            )
        })

    # BLOQUEAR LA CALIFICACIÓN
    try:
        calificacion = (
            Calificaciones.objects
            .select_for_update()
            .get(
                id_calificaciones=historial.calificacion_id
            )
        )

    except Calificaciones.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "title": "Calificación no encontrada",
            "icon": "warning",
            "descripcion": (
                "La calificación asociada a la modificación "
                "ya no existe."
            )
        })

    # DETALLES DEL HISTORIAL
    detalles = list(
        HistorialDetalleNota.objects
        .select_for_update()
        .filter(
            historial=historial
        )
    )

    if not detalles:
        return JsonResponse({
            "estado": "fallo",
            "title": "Sin respaldo",
            "icon": "warning",
            "descripcion": (
                "La modificación seleccionada no posee "
                "un respaldo para realizar la reversión."
            )
        })

    # VALIDAR CALIFICACIÓN CONGELADA
    if calificacion.congelada:
        return JsonResponse({
            "estado": "fallo",
            "title": "Calificación congelada",
            "icon": "warning",
            "descripcion": (
                "La calificación relacionada con la "
                "modificación se encuentra congelada "
                "y no puede ser revertida."
            )
        })

    # BLOQUEAR Y VALIDAR UNIDADES
    detalles_unidad = []

    for detalle in detalles:
        if not detalle.detalle_calificacion_unidad_id:
            continue

        try:
            detalle_calificacion = (
                DetalleCalificacionesUnidad.objects
                .select_for_update()
                .get(
                    id_detalle_calificaciones_unidad=(
                        detalle.detalle_calificacion_unidad_id
                    )
                )
            )

        except DetalleCalificacionesUnidad.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "title": "Unidad no encontrada",
                "icon": "warning",
                "descripcion": (
                    "Una de las unidades relacionadas con "
                    "la modificación ya no existe."
                )
            })

        if detalle_calificacion.congelada:
            return JsonResponse({
                "estado": "fallo",
                "title": "Unidad congelada",
                "icon": "warning",
                "descripcion": (
                    "Una de las unidades relacionadas con "
                    "la modificación se encuentra congelada "
                    "y no puede ser revertida."
                )
            })

        detalles_unidad.append(
            (
                detalle,
                detalle_calificacion
            )
        )

    # VARIABLES DE CONTROL
    nota_modificada = False
    asistencia_modificada = False
    promedio_modificado = False

    # RESTAURAR NOTAS DE LAS UNIDADES
    for detalle, detalle_calificacion in detalles_unidad:

        if detalle.nota_anterior != detalle.nota_nueva:

            detalle_calificacion.nota_unidad = (
                detalle.nota_anterior
            )

            detalle_calificacion.modificado_por = usuario
            detalle_calificacion.fecha_modificacion = (
                timezone.now()
            )
            detalle_calificacion.perfil_modificacion = (
                "CONTROL_ESTUDIO"
            )

            detalle_calificacion.save(
                update_fields=[
                    "nota_unidad",
                    "modificado_por",
                    "fecha_modificacion",
                    "perfil_modificacion"
                ]
            )

            nota_modificada = True

    # RESTAURAR ASISTENCIA Y PROMEDIO
    for detalle in detalles:

        if (
            detalle.asistencia_anterior
            != detalle.asistencia_nueva
        ):
            calificacion.asistencia = (
                detalle.asistencia_anterior
            )

            asistencia_modificada = True

        if (
            detalle.promedio_anterior
            != detalle.promedio_nuevo
        ):
            calificacion.promedio_tramo = (
                detalle.promedio_anterior
            )

            promedio_modificado = True

    # VALIDAR QUE HUBO ALGUNA MODIFICACIÓN
    if not (
        nota_modificada
        or asistencia_modificada
        or promedio_modificado
    ):
        return JsonResponse({
            "estado": "fallo",
            "title": "Sin cambios para revertir",
            "icon": "warning",
            "descripcion": (
                "No se encontraron notas, asistencia "
                "o promedio modificados en el historial."
            )
        })

    # VALIDAR MATERIA
    if not calificacion.materia_asignada_id:
        return JsonResponse({
            "estado": "fallo",
            "title": "Materia no encontrada",
            "icon": "warning",
            "descripcion": (
                "La calificación no tiene una materia "
                "asignada relacionada."
            )
        })

    # OBTENER NOMBRE DE LA MATERIA
    nombre_materia = (
        MateriaAsignada.objects
        .filter(
            id_materia_asignada=(
                calificacion.materia_asignada_id
            )
        )
        .values_list(
            "materia__nombre",
            flat=True
        )
        .first()
    )

    if not nombre_materia:
        return JsonResponse({
            "estado": "fallo",
            "title": "Materia no encontrada",
            "icon": "warning",
            "descripcion": (
                "No se pudo identificar la materia "
                "asociada a la calificación."
            )
        })

    # NORMALIZAR NOMBRE
    nombre_materia = (
        nombre_materia
        .strip()
        .lower()
    )

    # DETERMINAR SI ES PROYECTO
    es_proyecto = (
        "proyecto socio tecnológico"
        in nombre_materia
    )

    nota_aprobacion = (
        Decimal("16")
        if es_proyecto
        else Decimal("12")
    )

    # ACTUALIZAR CONDICIÓN
    asistencia = (
        calificacion.asistencia
        if calificacion.asistencia is not None
        else 0
    )

    if asistencia < 75:

        calificacion.condicion = "REPROBADO"

    elif (
        calificacion.promedio_tramo is not None
        and calificacion.promedio_tramo >= nota_aprobacion
    ):

        calificacion.condicion = "APROBADO"

    elif es_proyecto:

        calificacion.condicion = "REPROBADO"

    else:

        calificacion.condicion = "REPARACIÓN"

    # AUDITORÍA DE CALIFICACIÓN
    calificacion.modificado_por = usuario
    calificacion.fecha_modificacion = timezone.now()
    calificacion.perfil_modificacion = (
        "CONTROL_ESTUDIO"
    )

    calificacion.save(
        update_fields=[
            "asistencia",
            "promedio_tramo",
            "condicion",
            "modificado_por",
            "fecha_modificacion",
            "perfil_modificacion"
        ]
    )

    # CAMBIAR HISTORIAL A REVERSION
    historial.tipo_modificacion = "REVERSION"
    historial.usuario_modifica = usuario
    historial.perfil_modificacion = (
        "CONTROL_ESTUDIO"
    )
    historial.fecha_modificacion = timezone.now()
    historial.motivo = (
        f"Reversión de la modificación "
        f"del Historial {historial.id_historial}."
    )

    historial.save(
        update_fields=[
            "tipo_modificacion",
            "usuario_modifica",
            "perfil_modificacion",
            "fecha_modificacion",
            "motivo"
        ]
    )

    return JsonResponse({
        "estado": "exito",
        "title": "Reversión realizada",
        "icon": "success",
        "descripcion": (
            "La modificación fue revertida correctamente "
            "y se restauraron los valores anteriores."
        ),
        "id_historial": historial.id_historial
    })

def rem_not_acad(request):
    return render(request, "Roles/Control_Estudio/Remover_Cambios_Notas/remover_notas_academica.html") 