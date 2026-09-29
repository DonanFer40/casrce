from django.shortcuts import render
from django.http import JsonResponse
from django.db import transaction
from django.utils import timezone
from django.db.models import F, Exists, OuterRef, Q, Prefetch, Count 
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from inicio_sesion.models import Usuario, CoordinadorPNF, ControlEstudio, TrayectoAcademico, MateriaAsignada, CalendarioPeriodo, PeriodoAcademicoMateria, Usuario, Pnf, PNFNucleo, Estudiante, EstatusEstudiante, CalendarioAcademico, Nucleos, PeriodoAcademico, Materia, Docente, DocenteAsignadoMateria

from notas_academicas.models import PlanificacionAcademica, Reparacion, DetallePlanificacion, HistorialTrayectoEstudiante, HistorialDetalleNota, HistorialModificacionNotas, DetalleEvaluacion, PromedioFinal, Calificaciones, DetalleCalificacionesUnidad

# Registrar Notas Académicas
def nucl_reg_not(request):
    cedula = request.session.get("cedula_usuario")
    perfil = request.POST.get("perfil")

    if not cedula:
        return JsonResponse({
            "estado": "fallo",
            "icon": "warning",
            "title": "Sesión no válida",
            "descripcion": "No se encontró un usuario autenticado."
        })

    if perfil not in ("DOCENTE", "CONTROL_ESTUDIO"):
        return JsonResponse({
            "estado": "fallo",
            "icon": "warning",
            "title": "Perfil no válido",
            "descripcion": "El perfil seleccionado no es válido."
        })

    fecha_actual = timezone.localdate()

    calendario_carga_notas = CalendarioAcademico.objects.filter(
        tipo="CARGA_NOTAS",
        activo=True,
        fecha_inicio__lte=fecha_actual,
        fecha_final__gte=fecha_actual
    ).exists()

    if not calendario_carga_notas:
        return JsonResponse({
            "estado": "fallo",
            "icon": "warning",
            "title": "Registro de calificaciones no disponible",
            "descripcion": (
                "Actualmente no se encuentra vigente el período "
                "establecido en el calendario académico para la "
                "carga de notas."
            )
        })

    if perfil == "CONTROL_ESTUDIO":

        nucleos = Nucleos.objects.filter(
            materias_asignadas__usuario__cedula_identidad=cedula,
            materias_asignadas__activo=True
        ).distinct()

    else:

        nucleos = Nucleos.objects.filter(
            docente__usuario__cedula_identidad=cedula,
            docente__activo=True
        ).distinct()

    datos = [
        {
            "id_nucleo": nucleo.id_nucleo,
            "municipio": nucleo.municipio,
            "direccion": nucleo.direccion,
        }
        for nucleo in nucleos
    ]

    if not datos:
        if perfil == "CONTROL_ESTUDIO":
            return JsonResponse({
                "estado": "fallo",
                "icon": "info",
                "title": "Sin núcleos asignados",
                "descripcion": (
                    "El usuario no tiene núcleos asignados como "
                    "Encargado de Control de Estudio."
                )
            })

        return JsonResponse({
            "estado": "fallo",
            "icon": "info",
            "title": "Sin núcleos asignados",
            "descripcion": (
                "El usuario no tiene núcleos asignados como Docente."
            )
        })

    return JsonResponse({
        "estado": "exito",
        "datos": datos
    })

def pnf_reg_not(request):
    cedula = request.session.get("cedula_usuario")
    nucleo_asignado = request.POST.get("nucleo_asignado", "").strip()
    perfil = request.POST.get("perfil", "").strip()

    if not cedula or not nucleo_asignado or not perfil:
        return JsonResponse({
            "estado": "vacio",
            "datos": [],
            "title": "Datos incompletos",
            "descripcion": "No se recibieron todos los datos necesarios.",
            "icon": "info"
        })

    fecha_actual = timezone.localdate()

    calendario_carga_notas = CalendarioAcademico.objects.filter(
        tipo="CARGA_NOTAS",
        activo=True,
        fecha_inicio__lte=fecha_actual,
        fecha_final__gte=fecha_actual
    ).exists()

    if not calendario_carga_notas:
        return JsonResponse({
            "estado": "vacio",
            "datos": [],
            "title": "Registro de calificaciones no disponible",
            "descripcion": (
                "Actualmente no se encuentra vigente el período "
                "establecido en el calendario académico para la "
                "carga de notas."
            ),
            "icon": "warning"
        })

    if perfil == "CONTROL_ESTUDIO":

        control_estudio = (
            ControlEstudio.objects
            .filter(
                usuario__cedula_identidad=cedula,
                nucleo_id=nucleo_asignado,
                activo=True
            )
            .first()
        )

        if not control_estudio:
            return JsonResponse({
                "estado": "vacio",
                "datos": [],
                "title": "Control de Estudio no disponible",
                "descripcion": (
                    "No existe un perfil activo de Control de Estudio "
                    "asociado a este núcleo."
                ),
                "icon": "info"
            })

        pnfs = (
            Pnf.objects
            .filter(
                pnfnucleo__id_nucleo=control_estudio.nucleo_id
            )
            .distinct()
            .order_by("pnf")
        )

    elif perfil == "DOCENTE":

        docentes = (
            Docente.objects
            .filter(
                usuario__cedula_identidad=cedula,
                nucleo_id=nucleo_asignado,
                activo=True
            )
        )

        pnf_ids = (
            docentes
            .values_list(
                "pnf_id",
                flat=True
            )
            .distinct()
        )

        pnfs = (
            Pnf.objects
            .filter(
                id_pnf__in=pnf_ids,
                pnfnucleo__id_nucleo=nucleo_asignado
            )
            .distinct()
            .order_by("pnf")
        )

    else:
        return JsonResponse({
            "estado": "vacio",
            "datos": [],
            "title": "Perfil no válido",
            "descripcion": "El perfil seleccionado no es válido.",
            "icon": "info"
        })

    if not pnfs.exists():
        return JsonResponse({
            "estado": "vacio",
            "datos": [],
            "title": "No hay P.N.F disponibles",
            "descripcion": (
                "No existen P.N.F disponibles para el "
                "perfil y núcleo seleccionado."
            ),
            "icon": "info"
        })

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

def doc_reg_not(request):
    nucleo_asignado = request.POST.get("nucleo_asignado")
    pnf_seleccionado = request.POST.get("pnf_seleccionado")
    cedula = request.session.get("cedula_usuario")

    if not nucleo_asignado or not pnf_seleccionado:
        return JsonResponse({
            "estado": "fallo",
            "datos": [],
            "title": "Datos incompletos",
            "descripcion": (
                "Debe seleccionar el núcleo y el PNF "
                "para registrar calificaciones."
            ),
            "icon": "warning"
        })

    fecha_actual = timezone.localdate()
    año_actual = fecha_actual.year

    # VALIDAR CALENDARIO ACADÉMICO
    calendario_carga_notas = CalendarioAcademico.objects.filter(
        tipo="CARGA_NOTAS",
        activo=True,
        fecha_inicio__lte=fecha_actual,
        fecha_final__gte=fecha_actual
    ).exists()

    if not calendario_carga_notas:
        return JsonResponse({
            "estado": "fallo",
            "datos": [],
            "title": "Registro de calificaciones no disponible",
            "descripcion": (
                "Actualmente no se encuentra vigente el período "
                "establecido en el calendario académico para la "
                "carga de notas."
            ),
            "icon": "warning"
        })

    docentes = (
        Docente.objects
        .filter(
            nucleo_id=nucleo_asignado,
            pnf_id=pnf_seleccionado,
            activo=True,
            materias_asignadas__activo=True,
            materias_asignadas__materia_asignada__activo=True
        )
        .exclude(
            usuario__cedula_identidad=cedula
        )
        .annotate(
            total_materias=Count(
                "materias_asignadas__materia_asignada",
                filter=Q(
                    materias_asignadas__activo=True,
                    materias_asignadas__materia_asignada__activo=True,
                    materias_asignadas__materia_asignada__materia__activa=True,
                    materias_asignadas__materia_asignada__materia__id_pnf_id=pnf_seleccionado
                ),
                distinct=True
            ),
            materias_con_notas=Count(
                "materias_asignadas__materia_asignada",
                filter=Q(
                    materias_asignadas__activo=True,
                    materias_asignadas__materia_asignada__activo=True,
                    materias_asignadas__materia_asignada__materia__activa=True,
                    materias_asignadas__materia_asignada__materia__id_pnf_id=pnf_seleccionado,
                    materias_asignadas__materia_asignada__calificaciones_materia__fecha_registro__year=año_actual
                ),
                distinct=True
            )
        )
        .filter(
            total_materias__gt=0,
            materias_con_notas__lt=F("total_materias")
        )
        .select_related("usuario")
        .distinct()
    )
    if not docentes.exists():
        return JsonResponse({
            "estado": "fallo",
            "datos": [],
            "title": "No hay docentes pendientes",
            "descripcion": (
                "No existen docentes con materias activas pendientes "
                "de registrar calificaciones para el año actual."
            ),
            "icon": "info"
        })

    datos = [
        {
            "id_docente": docente.id_docente,
            "cedula": docente.usuario.cedula_identidad,
            "nombres": docente.usuario.nombres,
            "apellidos": docente.usuario.apellidos,
        }
        for docente in docentes
    ]

    return JsonResponse({
        "estado": "exito",
        "datos": datos
    })

def tray_mat_asig(request):
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
    cedula_docente = request.POST.get("docente")
    perfil = request.POST.get("perfil")

    if not cedula:
        return JsonResponse({
            "estado": "fallo",
            "title": "Sesión",
            "icon": "warning",
            "descripcion": "No se pudo identificar al usuario de la sesión."
        })

    if perfil not in ["CONTROL_ESTUDIO", "DOCENTE"]:
        return JsonResponse({
            "estado": "fallo",
            "title": "Perfil",
            "icon": "warning",
            "descripcion": "El perfil indicado no permite consultar trayectos."
        })

    if perfil == "DOCENTE":

        try:
            docente = Docente.objects.get(
                usuario__cedula_identidad=cedula,
                activo=True,
                nucleo_id=nucleo,
                pnf_id=pnf
            )
        except Docente.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "title": "Docente",
                "icon": "warning",
                "descripcion": (
                    "No se encontró un registro activo de docente "
                    "para el núcleo y PNF seleccionados."
                )
            })

        id_docentes = [docente.id_docente]

    else:
        if not nucleo or not pnf:
            return JsonResponse({
                "estado": "fallo",
                "title": "Datos incompletos",
                "icon": "warning",
                "descripcion": (
                    "Debe indicar el núcleo y el PNF."
                )

            })
        try:
            ControlEstudio.objects.get(
                usuario__cedula_identidad=cedula,
                activo=True
            )
        except ControlEstudio.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "title": "Control de Estudio",
                "icon": "error",
                "descripcion": (
                    "El usuario no tiene un perfil activo de "
                    "Control de Estudio."
                )
            })

        id_docentes = list(
            Docente.objects.filter(
                usuario__cedula_identidad=cedula_docente,
                nucleo_id=nucleo,
                pnf_id=pnf,
                activo=True
            ).values_list(
                "id_docente",
                flat=True
            )
        )

        if not id_docentes:
            return JsonResponse({
                "estado": "fallo",
                "title": "Docente",
                "icon": "warning",
                "descripcion": (
                    "El docente no posee una asignación activa "
                    "para el núcleo y PNF seleccionados."
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

    trayectos = (
        TrayectoAcademico.objects
        .filter(
            materia__asignaciones__docentes__docente_id__in=id_docentes,
            materia__asignaciones__activo=True,
            materia__asignaciones__docentes__activo=True,
            materia__activa=True,
            materia__id_pnf_id=pnf,

            materia__periodos_academicos__periodo_id__in=(
                periodos_actuales
            )
        )
        .distinct()
        .order_by(
            "id_periodo_academico"
        )
    )

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
    trayecto = request.POST.get("trayecto")
    cedula_docente = request.POST.get("docente")
    perfil = request.POST.get("perfil")
    cedula = request.session.get("cedula_usuario")

    if not cedula:
        return JsonResponse({
            "estado": "fallo",
            "title": "Sesión",
            "icon": "warning",
            "descripcion": "No se pudo identificar al usuario de la sesión."
        })

    if perfil not in ["CONTROL_ESTUDIO", "DOCENTE"]:
        return JsonResponse({
            "estado": "fallo",
            "title": "Perfil",
            "icon": "warning",
            "descripcion": "El perfil indicado no permite consultar materias."
        })

    if not nucleo or not pnf or not trayecto:
        return JsonResponse({
            "estado": "fallo",
            "title": "Datos incompletos",
            "icon": "warning",
            "descripcion": (
                "Debe indicar el núcleo, PNF y trayecto académico."
            )
        })

    fecha_actual = timezone.localdate()
    año_actual = fecha_actual.year

    # CALENDARIOS DE CARGA DE NOTAS DEL AÑO
    calendarios_carga = (
        CalendarioPeriodo.objects
        .filter(
            calendario__tipo="CARGA_NOTAS",
            calendario__activo=True,
            calendario__fecha_inicio__year=año_actual,
        )
        .select_related(
            "periodo",
            "calendario"
        )
    )

    if not calendarios_carga.exists():
        return JsonResponse({
            "estado": "fallo",
            "title": "Calendario académico",
            "icon": "warning",
            "descripcion": (
                "No existe un calendario académico de carga de notas "
                f"registrado para el año {año_actual}."
            )
        })

    # CALENDARIOS ACTUALMENTE VIGENTES
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

            fecha_inicio = (
                calendario_proximo.calendario.fecha_inicio
            )

            return JsonResponse({
                "estado": "fallo",
                "title": "Carga de notas no habilitada",
                "icon": "warning",
                "descripcion": (
                    "Actualmente no existe un período académico "
                    "habilitado para la carga de notas. "
                    "El próximo período disponible corresponde a "
                    f"{calendario_proximo.periodo.nombre} y "
                    f"inicia el {fecha_inicio.strftime('%d/%m/%Y')}."
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

            fecha_final = (
                calendario_anterior.calendario.fecha_final
            )

            return JsonResponse({
                "estado": "fallo",
                "title": "Plazo de carga vencido",
                "icon": "warning",
                "descripcion": (
                    "El plazo de carga de notas del período "
                    f"{calendario_anterior.periodo.nombre} "
                    f"finalizó el {fecha_final.strftime('%d/%m/%Y')}. "
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

    # DETERMINAR LOS DOCENTES SEGÚN EL PERFIL
    if perfil == "DOCENTE":
        try:
            docente_obj = Docente.objects.get(
                usuario__cedula_identidad=cedula,
                nucleo_id=nucleo,
                pnf_id=pnf,
                activo=True
            )
        except Docente.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "title": "Docente",
                "icon": "warning",
                "descripcion": (
                    "No se encontró un registro activo de docente "
                    "para el núcleo y PNF seleccionados."
                )
            })

        id_docentes = [docente_obj.id_docente]

    else:

        if not cedula_docente:
            return JsonResponse({
                "estado": "fallo",
                "title": "Docente",
                "icon": "warning",
                "descripcion": "No se especificó el docente."
            })

        try:
            ControlEstudio.objects.get(
                usuario__cedula_identidad=cedula,
                activo=True
            )
        except ControlEstudio.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "title": "Control de Estudio",
                "icon": "error",
                "descripcion": (
                    "El usuario no tiene un perfil activo de "
                    "Control de Estudio."
                )
            })

        id_docentes = list(
            Docente.objects.filter(
                usuario__cedula_identidad=cedula_docente,
                nucleo_id=nucleo,
                pnf_id=pnf,
                activo=True
            ).values_list(
                "id_docente",
                flat=True
            )
        )

        if not id_docentes:
            return JsonResponse({
                "estado": "fallo",
                "title": "Docente",
                "icon": "warning",
                "descripcion": (
                    "El docente no posee un registro activo "
                    "para el núcleo y PNF seleccionados."
                )
            })

    # BUSCAR MATERIAS ASIGNADAS
    materias_asignadas = (
        DocenteAsignadoMateria.objects
        .filter(
            docente_id__in=id_docentes,
            docente__nucleo_id=nucleo,
            docente__pnf_id=pnf,
            activo=True,

            materia_asignada__activo=True,

            materia_asignada__materia__activa=True,
            materia_asignada__materia__id_pnf_id=pnf,
            materia_asignada__materia__id_trayecto_id=trayecto,

            materia_asignada__materia__periodos_academicos__periodo_id__in=(
                periodos_actuales
            ),
        )
        .select_related(
            "materia_asignada__materia",
            "materia_asignada__materia__id_trayecto",
        )
        .distinct()
    )

    # EXCLUIR MATERIAS YA REGISTRADAS EN ESTE PERÍODO
    materias_registradas = Calificaciones.objects.filter(
        materia_asignada=OuterRef(
            "materia_asignada"
        ),
        periodo_materia__periodo_id__in=periodos_actuales,
        fecha_promedio__year=año_actual,
    )

    materias_asignadas = (
        materias_asignadas
        .annotate(
            ya_registrada=Exists(
                materias_registradas
            )
        )
        .filter(
            ya_registrada=False
        )
    )

    # PREPARAR RESULTADO
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
            ),
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

        if not periodos_materia.exists():
            return JsonResponse({
                "estado": "exito",
                "title": "Sin período habilitado",
                "icon": "info",
                "descripcion": (
                    "La materia no tiene un período de carga de notas "
                    "habilitado actualmente."
                ),
                "datos": None
            })

        periodo_materia = periodos_materia.first()

        datos = {
            "id_periodo_materia": periodo_materia.id,
            "id_periodo_academico": periodo_materia.periodo_id,
            "nombre": periodo_materia.periodo.nombre
        }

        return JsonResponse({
            "estado": "exito",
            "datos": datos
        })

    return JsonResponse({
        "estado": "fallo",
        "title": "Método no permitido",
        "icon": "error",
        "descripcion": "La solicitud debe realizarse mediante POST."
    })

def cant_det_pla(request):
    if request.method != "POST":
        return JsonResponse({
            "estado": "fallo",
            "title": "Error",
            "icon": "error",
            "descripcion": "Método de solicitud no permitido."
        })

    nucleo = request.POST.get("id_nucleo")
    pnf = request.POST.get("id_pnf")
    materia_asignada = request.POST.get("id_materia_asignada")
    periodo_materia = request.POST.get("id_periodo_materia")
    trayecto = request.POST.get("trayecto")
    docente = request.POST.get("docente")
    perfil = request.POST.get("perfil")
    cedula = request.session.get("cedula_usuario")

    if not cedula:
        return JsonResponse({
            "estado": "fallo",
            "title": "Sesión",
            "icon": "warning",
            "descripcion": "No se pudo identificar al usuario de la sesión."
        })

    if perfil not in ["CONTROL_ESTUDIO", "DOCENTE"]:
        return JsonResponse({
            "estado": "fallo",
            "title": "Perfil",
            "icon": "warning",
            "descripcion": "El perfil indicado no permite realizar esta consulta."
        })

    if not all([
        nucleo,
        pnf,
        materia_asignada,
        periodo_materia
    ]):
        return JsonResponse({
            "estado": "fallo",
            "title": "Datos incompletos",
            "icon": "warning",
            "descripcion": "Faltan datos para realizar la consulta."
        })
    if perfil == "DOCENTE":
        try:
            Docente.objects.get(
                usuario__cedula_identidad=cedula,
                nucleo_id=nucleo,
                pnf_id=pnf,
                activo=True
            )
        except Docente.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "title": "Docente",
                "icon": "warning",
                "descripcion": (
                    "No se encontró un registro activo de docente "
                    "para el núcleo y PNF seleccionados."
                )
            })

    elif perfil == "CONTROL_ESTUDIO":

        if not docente:
            return JsonResponse({
                "estado": "fallo",
                "title": "Docente",
                "icon": "warning",
                "descripcion": "Debe seleccionar un docente."
            })

        try:
            ControlEstudio.objects.get(
                usuario__cedula_identidad=cedula,
                activo=True
            )
        except ControlEstudio.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "title": "Control de Estudio",
                "icon": "error",
                "descripcion": (
                    "El usuario no tiene un perfil activo de "
                    "Control de Estudio."
                )
            })

    # VALIDAR MATERIA ASIGNADA
    try:
        materia_asignada_obj = (
            MateriaAsignada.objects
            .select_related("materia")
            .get(
                id_materia_asignada=materia_asignada,
                activo=True,
                materia__id_pnf_id=pnf
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
            "descripcion": (
                "La materia o el período académico "
                "no son válidos."
            )
        })

    # BUSCAR PLANIFICACIÓN ACADÉMICA
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

    # CANTIDAD DE UNIDADES
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
    if request.method != "POST":
        return JsonResponse({
            "estado": "fallo",
            "title": "Error",
            "icon": "error",
            "descripcion": "Método de solicitud no permitido."
        })

    nucleo = request.POST.get("id_nucleo")
    pnf = request.POST.get("id_pnf")
    trayecto = request.POST.get("trayecto")
    perfil = request.POST.get("perfil")
    cedula = request.session.get("cedula_usuario")

    if not cedula:
        return JsonResponse({
            "estado": "fallo",
            "title": "Sesión",
            "icon": "warning",
            "descripcion": "No se pudo identificar al usuario de la sesión."
        })

    if perfil not in ["CONTROL_ESTUDIO", "DOCENTE"]:
        return JsonResponse({
            "estado": "fallo",
            "title": "Perfil",
            "icon": "warning",
            "descripcion": "El perfil indicado no permite realizar esta consulta."
        })

    if not all([nucleo, pnf, trayecto]):
        return JsonResponse({
            "estado": "fallo",
            "title": "Datos incompletos",
            "icon": "warning",
            "descripcion": "Faltan datos para realizar la consulta."
        })

    try:
        trayecto_obj = TrayectoAcademico.objects.get(
            id_periodo_academico=trayecto
        )
    except TrayectoAcademico.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "title": "Trayecto",
            "icon": "warning",
            "descripcion": "El trayecto académico no existe."
        })

    if perfil == "CONTROL_ESTUDIO":
        try:
            ControlEstudio.objects.get(
                usuario__cedula_identidad=cedula,
                activo=True
            )
        except ControlEstudio.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "title": "Control de Estudio",
                "icon": "error",
                "descripcion": (
                    "El usuario no tiene un perfil activo de "
                    "Control de Estudio."
                )
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

    datos = [
        {
            "id_estudiante": estudiante.id_estudiante,
            "nombre_completo": (
                estudiante.usuario.nombres
                + " "
                + estudiante.usuario.apellidos
            ),
            "cedula": estudiante.usuario.cedula_identidad
        }
        for estudiante in estudiantes
    ]

    return JsonResponse({
        "estado": "exito",
        "estudiantes": datos
    })
    
def reg_nota_acad(request):
    if request.method == "POST":
        nucleo_asignado = request.POST.get("nucleo_asignado")
        pnf_asignado = request.POST.get("pnf_asignado")
        docente = request.POST.get("seleccion_docente")
        trayecto_academico = request.POST.get("trayecto_academico")
        materia_asignada = request.POST.get("materia_asignada")
        periodo_materia = request.POST.get("periodo_academico")
        cantidad_evaluaciones = request.POST.get("cantidad_evaluaciones")
        perfil = request.POST.get("perfil")

        cedula = request.session.get("cedula_usuario")

        if not cedula:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Sesión",
                "descripcion": (
                    "No se pudo identificar al usuario "
                    "de la sesión actual."
                )
            })

        if not perfil:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Perfil",
                "descripcion": (
                    "No se recibió el perfil que realizará "
                    "el registro de las notas."
                )
            })

        if perfil not in ["DOCENTE", "CONTROL_ESTUDIO"]:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Perfil no válido",
                "descripcion": (
                    "El perfil seleccionado no está autorizado "
                    "para registrar notas académicas."
                )
            })

        controles = [
            (nucleo_asignado, "Núcleo", "Debe seleccionar el núcleo."),
            (pnf_asignado, "P.N.F", "Debe seleccionar el P.N.F."),
            (materia_asignada, "Materia", "Debe seleccionar la materia."),
            (periodo_materia, "Periodo académico", "Debe seleccionar el periodo académico."),
            (trayecto_academico, "Trayecto Académico", "Debe seleccionar el trayecto académico.")
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
                "descripcion": (
                    "Debe indicar la cantidad de evaluaciones."
                )
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
                    "La cantidad de evaluaciones "
                    "debe ser mayor que cero."
                )
            })

        # USUARIO QUE REALIZA EL REGISTRO
        try:
            usuario_registro = Usuario.objects.get(cedula_identidad=cedula)
        except Usuario.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Usuario",
                "descripcion": (
                    "No se encontró el usuario asociado "
                    "a la sesión actual."
                )
            })

        # VALIDACIÓN DEL PERFIL
        docente_obj = None

        if perfil == "DOCENTE":
            docente_obj = (
                Docente.objects
                .filter(
                    usuario__cedula_identidad=cedula,
                    nucleo_id=nucleo_asignado,
                    pnf_id=pnf_asignado,
                    activo=True
                )
                .select_related(
                    "usuario",
                    "nucleo",
                    "pnf"
                )
                .first()
            )

            if not docente_obj:
                return JsonResponse({
                    "estado": "fallo",
                    "icon": "error",
                    "title": "Docente",
                    "descripcion": (
                        "El usuario actual no tiene una "
                        "asignación activa como docente en "
                        "el núcleo y P.N.F seleccionados."
                    )
                })

        elif perfil == "CONTROL_ESTUDIO":
            if not docente:
                return JsonResponse({
                    "estado": "fallo",
                    "icon": "warning",
                    "title": "Docente",
                    "descripcion": (
                        "Debe seleccionar el docente "
                        "que registrará las notas."
                    )
                })

            control_estudio = (
                ControlEstudio.objects
                .filter(
                    usuario__cedula_identidad=cedula,
                    nucleo_id=nucleo_asignado,
                    activo=True
                )
                .first()
            )

            if not control_estudio:
                return JsonResponse({
                    "estado": "fallo",
                    "icon": "error",
                    "title": "Control de Estudio",
                    "descripcion": (
                        "El usuario actual no tiene una "
                        "asignación activa de Control de Estudio "
                        "en el núcleo seleccionado."
                    )
                })

            docente_obj = (
                Docente.objects
                .filter(
                    usuario__cedula_identidad=docente,
                    nucleo_id=nucleo_asignado,
                    pnf_id=pnf_asignado,
                    activo=True
                )
                .select_related(
                    "usuario",
                    "nucleo",
                    "pnf"
                )
                .first()
            )

            if not docente_obj:
                return JsonResponse({
                    "estado": "fallo",
                    "icon": "error",
                    "title": "Docente",
                    "descripcion": (
                        "El docente seleccionado no pertenece "
                        "al núcleo y P.N.F seleccionados o "
                        "se encuentra inactivo."
                    )
                })

        # OBTENER MATERIA ASIGNADA
        try:
            materia_asignada_obj = (
                MateriaAsignada.objects
                .select_related(
                    "materia"
                )
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
                    "se encuentra inactiva o no pertenece "
                    "al P.N.F seleccionado."
                )
            })

        # VALIDAR QUE EL DOCENTE TENGA LA MATERIA ASIGNADA
        asignacion_docente = (
            DocenteAsignadoMateria.objects
            .filter(
                docente=docente_obj,
                materia_asignada=materia_asignada_obj,
                activo=True
            )
            .first()
        )

        if not asignacion_docente:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Asignación docente",
                "descripcion": (
                    "El docente seleccionado no tiene "
                    "asignada la materia seleccionada."
                )
            })

        # OBTENER PERIODO ACADÉMICO
        try:
            periodo_materia_obj = (
                PeriodoAcademicoMateria.objects
                .select_related(
                    "periodo",
                    "materia"
                )
                .get(
                    periodo=periodo_materia,
                    materia=materia_asignada_obj.materia
                )
            )

        except PeriodoAcademicoMateria.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Periodo académico",
                "descripcion": (
                    "El periodo académico seleccionado "
                    "no está asociado a la materia seleccionada."
                )
            })

        # CALENDARIO DE CARGA DE NOTAS
        hoy = timezone.localdate()
        año_actual = hoy.year

        calendario_habilitado = (
            CalendarioPeriodo.objects
            .filter(
                calendario__activo=True,
                calendario__tipo="CARGA_NOTAS",
                calendario__fecha_inicio__lte=hoy,
                calendario__fecha_final__gte=hoy,
                periodo_id=periodo_materia_obj.periodo_id
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
                    "no se encuentra habilitado actualmente "
                    "para la carga de notas."
                )
            })

        # PLANIFICACIÓN ACADÉMICA
        planificacion = (
            PlanificacionAcademica.objects
            .filter(
                materia_asignacion=materia_asignada_obj,
                pnf_id=pnf_asignado,
                nucleo_id=nucleo_asignado,
                periodo_academico_id=periodo_materia_obj.periodo_id,
                activo=True,
                estado_aceptacion="ACEPTADA"
            )
            .first()
        )

        if not planificacion:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Planificación Académica",
                "descripcion": (
                    "No se encuentra registrado una Planificación Académica "
                    "aceptado para la materia, núcleo, P.N.F y periodo "
                    "académico seleccionado."
                )
            })

        # UNIDADES
        unidades = list(
            planificacion.detalles
            .all()
            .order_by(
                "id_detalle"
            )
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
                    "La cantidad de evaluaciones recibida "
                    "no coincide con la cantidad de unidades "
                    "registradas en el plan de actividad académica."
                )
            })

        # TRAYECTO
        try:
            trayecto_obj = (
                TrayectoAcademico.objects
                .get(
                    id_periodo_academico=trayecto_academico
                )
            )

        except TrayectoAcademico.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Trayecto académico",
                "descripcion": (
                    "El trayecto académico seleccionado "
                    "no existe."
                )
            })

        # RECIBIR CALIFICACIONES
        calificaciones = {}
        asistencias = {}
        promedios = {}

        ids_estudiantes = []

        for nombre_campo, valor in request.POST.items():

            if nombre_campo.startswith("calificacion_"):

                partes = nombre_campo.split("_")

                if len(partes) != 3:
                    continue

                id_estudiante = partes[1]
                numero_unidad = partes[2]

                if id_estudiante not in ids_estudiantes:
                    ids_estudiantes.append(id_estudiante)

                calificaciones.setdefault(
                    id_estudiante,
                    {}
                )

                calificaciones[
                    id_estudiante
                ][numero_unidad] = valor

            elif nombre_campo.startswith("asistencia_"):

                partes = nombre_campo.split("_")

                if len(partes) != 2:
                    continue

                id_estudiante = partes[1]

                if id_estudiante not in ids_estudiantes:
                    ids_estudiantes.append(id_estudiante)

                asistencias[
                    id_estudiante
                ] = valor

            elif nombre_campo.startswith("promedio_"):

                partes = nombre_campo.split("_")

                if len(partes) != 2:
                    continue

                id_estudiante = partes[1]

                if id_estudiante not in ids_estudiantes:
                    ids_estudiantes.append(id_estudiante)

                promedios[
                    id_estudiante
                ] = valor

        hay_datos_registrados = any(
            valor.strip()
            for datos in calificaciones.values()
            for valor in datos.values()
        ) or any(
            valor.strip()
            for valor in promedios.values()
        ) or any(
            valor.strip()
            for valor in asistencias.values()
        )

        if not hay_datos_registrados:
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Calificaciones",
                "descripcion": (
                    "No se ha registrado ninguna calificación. "
                    "Debe ingresar al menos una calificación "
                    "antes de continuar."
                )
            })

        estudiantes_a_registrar = []
        estudiantes_validos = {}

        for id_estudiante in ids_estudiantes:
            try:
                estudiante = (
                    Estudiante.objects
                    .select_related("usuario")
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
                        f"No se encontró el estudiante "
                        f"con identificación {id_estudiante} "
                        "en el núcleo y P.N.F seleccionados."
                    )
                })
            
            estudiantes_validos[id_estudiante] = estudiante
            
            ya_registrada = (
                Calificaciones.objects
                .filter(
                    estudiante=estudiante,
                    materia_asignada=materia_asignada_obj,
                    periodo_materia=periodo_materia_obj,
                    fecha_promedio__year=año_actual
                )
                .exists()
            )

            if not ya_registrada:
                estudiantes_a_registrar.append(id_estudiante)

        estudiantes_todas_cero = 0

        for id_estudiante in estudiantes_a_registrar:

            estudiante = estudiantes_validos[id_estudiante]

            notas_estudiante = calificaciones.get(
                id_estudiante,
                {}
            )

            todas_notas_cero = True

            for numero_unidad in range(1, cantidad_unidades + 1):

                nota = notas_estudiante.get(
                    str(numero_unidad),
                    ""
                )

                if nota == "":
                    return JsonResponse({
                        "estado": "fallo",
                        "icon": "error",
                        "title": "Nota faltante",
                        "descripcion": (
                            f"Debe registrar la nota de la unidad "
                            f"{numero_unidad} del estudiante "
                            f"{estudiante.usuario.nombres} "
                            f"{estudiante.usuario.apellidos}."
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
                            f"La nota de la unidad "
                            f"{numero_unidad} del estudiante "
                            f"{estudiante.usuario.nombres} "
                            f"{estudiante.usuario.apellidos} "
                            "no es válida."
                        )
                    })

                if (
                    nota_unidad < Decimal("0")
                    or nota_unidad > Decimal("20")
                ):
                    return JsonResponse({
                        "estado": "fallo",
                        "icon": "error",
                        "title": "Nota inválida",
                        "descripcion": (
                            f"La nota de la unidad "
                            f"{numero_unidad} del estudiante "
                            f"{estudiante.usuario.nombres} "
                            f"{estudiante.usuario.apellidos} "
                            "debe estar entre 0 y 20."
                        )
                    })

                if nota_unidad != Decimal("0"):
                    todas_notas_cero = False

            if todas_notas_cero:
                estudiantes_todas_cero += 1
                
            # VALIDAR ASISTENCIA
            asistencia = asistencias.get(
                id_estudiante,
                ""
            )

            if asistencia == "":
                return JsonResponse({
                    "estado": "fallo",
                    "icon": "error",
                    "title": "Asistencia faltante",
                    "descripcion": (
                        f"No se recibió la asistencia del estudiante "
                        f"{estudiante.usuario.nombres} "
                        f"{estudiante.usuario.apellidos}."
                    )
                })

            try:
                asistencia_decimal = Decimal(asistencia)

            except (ValueError, TypeError):
                return JsonResponse({
                    "estado": "fallo",
                    "icon": "error",
                    "title": "Asistencia inválida",
                    "descripcion": (
                        f"La asistencia del estudiante "
                        f"{estudiante.usuario.nombres} "
                        f"{estudiante.usuario.apellidos} "
                        "no es válida."
                    )
                })

            if (
                asistencia_decimal < Decimal("0")
                or asistencia_decimal > Decimal("100")
            ):
                return JsonResponse({
                    "estado": "fallo",
                    "icon": "error",
                    "title": "Asistencia inválida",
                    "descripcion": (
                        f"La asistencia del estudiante "
                        f"{estudiante.usuario.nombres} "
                        f"{estudiante.usuario.apellidos} "
                        "debe estar entre 0 y 100."
                    )
                })
        if estudiantes_todas_cero == len(estudiantes_a_registrar):
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Calificaciones inválidas",
                "descripcion": (
                    "No se puede registrar la carga de notas porque "
                    "todos los estudiantes tienen las calificaciones "
                    "de todas las unidades en cero."
                )
            })

        fecha_registro = timezone.now()

        try:
            with transaction.atomic():

                for id_estudiante in estudiantes_a_registrar:

                    estudiante = (
                        Estudiante.objects
                        .select_related("usuario")
                        .get(
                            id_estudiante=id_estudiante,
                            nucleo_id=nucleo_asignado,
                            pnf_id=pnf_asignado
                        )
                    )

                    # VALIDAR SI YA EXISTE
                    ya_registrada = (
                        Calificaciones.objects
                        .filter(
                            estudiante=estudiante,
                            materia_asignada=materia_asignada_obj,
                            periodo_materia=periodo_materia_obj,
                            fecha_promedio__year=año_actual
                        )
                        .exists()
                    )

                    if ya_registrada:
                        continue

                    # PROMEDIO
                    valor_promedio = promedios.get(
                        id_estudiante,
                        ""
                    )

                    if valor_promedio == "":
                        return JsonResponse({
                            "estado": "fallo",
                            "icon": "error",
                            "title": "Promedio faltante",
                            "descripcion": (
                                f"No se recibió el promedio del estudiante "
                                f"{estudiante.usuario.nombres} "
                                f"{estudiante.usuario.apellidos}."
                            )
                        })

                    promedio = Decimal(
                        valor_promedio.replace(",", ".")
                    )

                    # ASISTENCIA
                    asistencia = int(
                        asistencias.get(
                            id_estudiante,
                            0
                        )
                    )

                    # CONDICIÓN
                    nombre_materia = (
                        materia_asignada_obj.materia.nombre
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

                    print(usuario_registro)
                    print(perfil)

                    # CALIFICACIÓN
                    calificacion = (
                        Calificaciones.objects.create(
                            planificacion_academica=planificacion,
                            periodo_materia=periodo_materia_obj,
                            materia_asignada=materia_asignada_obj,
                            estudiante=estudiante,
                            promedio_tramo=promedio,
                            asistencia=asistencia,
                            condicion=condicion,
                            trayecto=trayecto_obj,
                            fecha_promedio=hoy,

                            registrado_por=usuario_registro,
                            fecha_registro=fecha_registro,
                            perfil_registro=perfil
                        )
                    )

                    # NOTAS POR UNIDAD
                    notas_estudiante = calificaciones.get(
                        id_estudiante,
                        {}
                    )

                    for numero_unidad in range(
                        1,
                        cantidad_unidades + 1
                    ):

                        nota = notas_estudiante[
                            str(numero_unidad)
                        ]

                        nota_unidad = Decimal(
                            nota.replace(",", ".")
                        )

                        unidad = unidades[
                            numero_unidad - 1
                        ]

                        DetalleCalificacionesUnidad.objects.create(
                            calificacion=calificacion,
                            unidad=unidad,
                            nota_unidad=nota_unidad,
                            registrado_por=usuario_registro,
                            fecha_registro=fecha_registro,
                            perfil_registro=perfil
                        )

            return JsonResponse({
                "estado": "exito",
                "icon": "success",
                "title": "Éxito",
                "descripcion": (
                    "Se registraron las notas académicas "
                    "exitosamente."
                )
            })

        except Exception as e:
            print(e)
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Error",
                "descripcion": (
                    "Ocurrió un error al registrar las "
                    "calificaciones académicas."
                )
            })
         
    return render(request, "Notas_Academicas/registrar_notas_academicas.html")

# Visualizar Notas Académicas

def vis_not_acad(request):
    return render (request, "Notas_Academicas/visualizar_notas_academicas.html")

def vis_nucl_not(request):
    cedula = request.session.get("cedula_usuario")
    perfil = request.POST.get("perfil")

    if not cedula:
        return JsonResponse({
            "estado": "fallo",
            "icon": "warning",
            "title": "Sesión no válida",
            "descripcion": "No se encontró un usuario autenticado."
        })

    if perfil not in ("DOCENTE", "CONTROL_ESTUDIO"):
        return JsonResponse({
            "estado": "fallo",
            "icon": "warning",
            "title": "Perfil no válido",
            "descripcion": "El perfil seleccionado no es válido."
        })

    if perfil == "DOCENTE":

        nucleos = Nucleos.objects.filter(
            docente__usuario__cedula_identidad=cedula,
            docente__activo=True,
            docente__materias_asignadas__activo=True,
            docente__materias_asignadas__materia_asignada__activo=True,
            docente__materias_asignadas__materia_asignada__calificaciones_materia__isnull=False
        ).distinct()

    else:

        nucleos = Nucleos.objects.filter(
            docente__materias_asignadas__materia_asignada__activo=True,
            docente__materias_asignadas__activo=True,
            docente__materias_asignadas__materia_asignada__calificaciones_materia__isnull=False
        ).distinct()

    datos = [
        {
            "id_nucleo": nucleo.id_nucleo,
            "municipio": nucleo.municipio,
            "direccion": nucleo.direccion,
        }
        for nucleo in nucleos
    ]

    if not datos:
        if perfil == "CONTROL_ESTUDIO":
            return JsonResponse({
                "estado": "vacio",
                "icon": "info",
                "title": "No hay calificaciones registradas",
                "descripcion": (
                    "No existen calificaciones registradas en los "
                    "núcleos asociados al usuario."
                ),
                "datos": []
            })

        return JsonResponse({
            "estado": "vacio",
            "icon": "info",
            "title": "No hay calificaciones registradas",
            "descripcion": (
                "No existen calificaciones registradas para las "
                "materias activas del docente."
            ),
            "datos": []
        })

    return JsonResponse({
        "estado": "exito",
        "datos": datos
    })

def vis_pnf_not(request):
    cedula = request.session.get("cedula_usuario")
    nucleo_asignado = request.POST.get("nucleo_asignado", "").strip()
    perfil = request.POST.get("perfil", "").strip()

    if not cedula or not nucleo_asignado or not perfil:
        return JsonResponse({
            "estado": "vacio",
            "datos": [],
            "title": "Datos incompletos",
            "descripcion": "No se recibieron todos los datos necesarios.",
            "icon": "info"
        })

    if perfil == "CONTROL_ESTUDIO":

        control_estudio = (
            ControlEstudio.objects
            .filter(
                usuario__cedula_identidad=cedula,
                nucleo_id=nucleo_asignado,
                activo=True
            )
            .first()
        )

        if not control_estudio:
            return JsonResponse({
                "estado": "vacio",
                "datos": [],
                "title": "Control de Estudio no disponible",
                "descripcion": (
                    "No existe un perfil activo de Control de Estudio "
                    "asociado a este núcleo."
                ),
                "icon": "info"
            })

        pnfs = (
            Pnf.objects
            .filter(
                pnfnucleo__id_nucleo=nucleo_asignado,
                materia__activa=True,
                materia__asignaciones__activo=True,
                materia__asignaciones__docentes__activo=True,
                materia__asignaciones__calificaciones_materia__isnull=False
            )
            .distinct()
            .order_by("pnf")
        )

    elif perfil == "DOCENTE":

        docente = (
            Docente.objects
            .filter(
                usuario__cedula_identidad=cedula,
                nucleo_id=nucleo_asignado,
                activo=True
            )
            .first()
        )

        if not docente:
            return JsonResponse({
                "estado": "vacio",
                "datos": [],
                "title": "Docente no disponible",
                "descripcion": (
                    "No existe un registro activo de docente "
                    "para el núcleo seleccionado."
                ),
                "icon": "info"
            })

        pnfs = (
            Pnf.objects
            .filter(
                id_pnf=docente.pnf_id,
                pnfnucleo__id_nucleo=nucleo_asignado,
                materia__activa=True,
                materia__asignaciones__activo=True,
                materia__asignaciones__docentes__docente=docente,
                materia__asignaciones__docentes__activo=True,
                materia__asignaciones__calificaciones_materia__isnull=False
            )
            .distinct()
            .order_by("pnf")
        )

    else:
        return JsonResponse({
            "estado": "vacio",
            "datos": [],
            "title": "Perfil no válido",
            "descripcion": "El perfil seleccionado no es válido.",
            "icon": "info"
        })

    if not pnfs.exists():
        return JsonResponse({
            "estado": "vacio",
            "datos": [],
            "title": "No hay P.N.F con calificaciones",
            "descripcion": (
                "No existen P.N.F con materias activas, asignaciones "
                "activas y calificaciones registradas."
            ),
            "icon": "info"
        })

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

def vis_doc_not(request):
    nucleo_asignado = request.POST.get("nucleo_asignado")
    pnf_seleccionado = request.POST.get("pnf_seleccionado")
    cedula = request.session.get("cedula_usuario")

    calificaciones_docente = Calificaciones.objects.filter(
        materia_asignada__docentes__docente=OuterRef("pk"),
        materia_asignada__docentes__activo=True,
        materia_asignada__activo=True,
    )

    docentes = (
        Docente.objects
        .filter(
            nucleo_id=nucleo_asignado,
            pnf_id=pnf_seleccionado,
            activo=True,
        )
        .exclude(
            usuario__cedula_identidad=cedula
        )
        .annotate(
            tiene_calificaciones=Exists(calificaciones_docente)
        )
        .filter(
            tiene_calificaciones=True
        )
        .select_related("usuario")
    )

    if not docentes.exists():
        return JsonResponse({
            "estado": "fallo",
            "datos": [],
            "title": "No hay docentes con calificaciones",
            "descripcion": (
                "No existen docentes activos con materias activas "
                "y calificaciones registradas para el núcleo y PNF seleccionado."
            ),
            "icon": "info"
        })

    datos = [
        {
            "id_docente": docente.id_docente,
            "cedula": docente.usuario.cedula_identidad,
            "nombres": docente.usuario.nombres,
            "apellidos": docente.usuario.apellidos,
        }
        for docente in docentes
    ]

    return JsonResponse({
        "estado": "exito",
        "datos": datos
    })

def tray_not_reg(request):
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
    cedula_docente = request.POST.get("docente")
    perfil = request.POST.get("perfil")

    if not cedula:
        return JsonResponse({
            "estado": "fallo",
            "title": "Sesión",
            "icon": "warning",
            "descripcion": "No se pudo identificar al usuario de la sesión."
        })

    if perfil not in ["CONTROL_ESTUDIO", "DOCENTE"]:
        return JsonResponse({
            "estado": "fallo",
            "title": "Perfil",
            "icon": "warning",
            "descripcion": "El perfil indicado no permite consultar trayectos."
        })

    if not nucleo or not pnf:
        return JsonResponse({
            "estado": "fallo",
            "title": "Datos incompletos",
            "icon": "warning",
            "descripcion": "Debe indicar el núcleo y el PNF."
        })

    if perfil == "DOCENTE":

        try:
            docente = Docente.objects.get(
                usuario__cedula_identidad=cedula,
                activo=True,
                nucleo_id=nucleo,
                pnf_id=pnf
            )
        except Docente.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "title": "Docente",
                "icon": "warning",
                "descripcion": (
                    "No se encontró un registro activo de docente "
                    "para el núcleo y PNF seleccionados."
                )
            })

        id_docentes = [docente.id_docente]

    else:

        try:
            ControlEstudio.objects.get(
                usuario__cedula_identidad=cedula,
                activo=True
            )
        except ControlEstudio.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "title": "Control de Estudio",
                "icon": "error",
                "descripcion": (
                    "El usuario no tiene un perfil activo de "
                    "Control de Estudio."
                )
            })

        id_docentes = list(
            Docente.objects.filter(
                usuario__cedula_identidad=cedula_docente,
                nucleo_id=nucleo,
                pnf_id=pnf,
                activo=True
            ).values_list(
                "id_docente",
                flat=True
            )
        )

        if not id_docentes:
            return JsonResponse({
                "estado": "fallo",
                "title": "Docente",
                "icon": "warning",
                "descripcion": (
                    "El docente no posee una asignación activa "
                    "para el núcleo y PNF seleccionados."
                )
            })

    trayectos = (
        TrayectoAcademico.objects
        .filter(
            calificaciones__materia_asignada__docentes__docente_id__in=id_docentes,
            calificaciones__materia_asignada__docentes__activo=True,
            calificaciones__materia_asignada__activo=True,
            calificaciones__materia_asignada__materia__activa=True,
            calificaciones__materia_asignada__materia__id_pnf_id=pnf,
            calificaciones__trayecto__isnull=False
        )
        .distinct()
        .order_by("id_periodo_academico")
    )

    if not trayectos.exists():
        return JsonResponse({
            "estado": "vacio",
            "trayectos": [],
            "title": "No hay calificaciones registradas",
            "icon": "info",
            "descripcion": (
                "No existen calificaciones registradas para el docente "
                "y los datos académicos seleccionados."
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

def mat_reg_not(request):
    if request.method == "POST":
        cedula = request.session.get("cedula_usuario")
        id_nucleo = request.POST.get("id_nucleo")
        id_pnf = request.POST.get("id_pnf")
        trayecto = request.POST.get("trayecto")
        cedula_docente = request.POST.get("docente")
        perfil = request.POST.get("perfil")

        if not all([
            cedula,
            id_nucleo,
            id_pnf,
            trayecto,
            perfil
        ]):
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Datos incompletos",
                "descripcion": (
                    "Faltan datos para realizar la consulta."
                )
            })

        # DOCENTE
        if perfil == "DOCENTE":

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
                        "El docente no está asignado al núcleo "
                        "y P.N.F seleccionados."
                    )
                })

        # =====================================================
        # CONTROL DE ESTUDIO
        # =====================================================

        elif perfil == "CONTROL_ESTUDIO":

            if not cedula_docente:
                return JsonResponse({
                    "estado": "fallo",
                    "icon": "warning",
                    "title": "Docente",
                    "descripcion": (
                        "Debe seleccionar el docente."
                    )
                })

            control_estudio = (
                ControlEstudio.objects
                .filter(
                    usuario__cedula_identidad=cedula,
                    nucleo_id=id_nucleo,
                    activo=True
                )
                .first()
            )

            if not control_estudio:
                return JsonResponse({
                    "estado": "fallo",
                    "icon": "error",
                    "title": "Control de Estudio",
                    "descripcion": (
                        "El usuario no está asignado como encargado "
                        "de Control de Estudio en el núcleo seleccionado."
                    )
                })

            docente = (
                Docente.objects
                .filter(
                    usuario__cedula_identidad=cedula_docente,
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
                        "El docente seleccionado no está asignado "
                        "al núcleo y P.N.F seleccionados."
                    )
                })

        else:

            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Perfil no válido",
                "descripcion": (
                    "El perfil seleccionado no es válido."
                )
            })

        # =====================================================
        # MATERIAS CON CALIFICACIONES REGISTRADAS
        # =====================================================

        materias = (
            MateriaAsignada.objects
            .filter(
                activo=True,

                docentes__docente=docente,
                docentes__activo=True,

                materia__id_pnf=id_pnf,
                materia__id_trayecto_id=trayecto,

                calificaciones_materia__isnull=False,

                calificaciones_materia__estudiante__nucleo_id=(
                    id_nucleo
                ),

                calificaciones_materia__estudiante__pnf_id=(
                    id_pnf
                )
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
            .order_by(
                "materia__nombre"
            )
        )

        materias_lista = [
            {
                "id_materia_asignada": materia[
                    "id_materia_asignada"
                ],
                "nombre_materia": materia[
                    "materia__nombre"
                ],
                "codigo_materia": materia[
                    "materia__codigo"
                ],
                "trayecto_materia": materia[
                    "trayecto_materia"
                ]
            }
            for materia in materias
        ]

        return JsonResponse({
            "estado": "exito",
            "materias": materias_lista
        })

    return JsonResponse({
        "estado": "fallo",
        "icon": "error",
        "title": "Solicitud no válida",
        "descripcion": (
            "La solicitud debe realizarse mediante POST."
        )
    })

def perd_reg_not(request):
    if request.method != "POST":
        return JsonResponse({
            "estado": "fallo",
            "icon": "error",
            "title": "Solicitud no válida",
            "descripcion": (
                "La solicitud debe realizarse mediante POST."
            ),
            "periodos": []
        })

    cedula = request.session.get(
        "cedula_usuario"
    )

    nucleo = request.POST.get(
        "id_nucleo"
    )

    pnf = request.POST.get(
        "id_pnf"
    )

    materia_asignada = request.POST.get(
        "id_materia_asignada"
    )

    trayecto = request.POST.get(
        "trayecto"
    )

    id_docente = request.POST.get(
        "docente"
    )

    perfil = request.POST.get(
        "perfil"
    )

    if not all([
        cedula,
        nucleo,
        pnf,
        materia_asignada,
        perfil
    ]):
        return JsonResponse({
            "estado": "fallo",
            "icon": "error",
            "title": "Datos incompletos",
            "descripcion": (
                "Faltan datos para realizar la consulta."
            ),
            "periodos": []
        })

    docente_obj = None

    # =========================================================
    # DOCENTE
    # =========================================================

    if perfil == "DOCENTE":

        docente_obj = (
            Docente.objects
            .filter(
                usuario__cedula_identidad=cedula,
                nucleo_id=nucleo,
                pnf_id=pnf,
                activo=True
            )
            .first()
        )

        if not docente_obj:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Docente no encontrado",
                "descripcion": (
                    "El docente no está asignado al "
                    "núcleo y P.N.F seleccionados."
                ),
                "periodos": []
            })

    # =========================================================
    # CONTROL DE ESTUDIO
    # =========================================================

    elif perfil == "CONTROL_ESTUDIO":

        if not id_docente:
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Docente",
                "descripcion": (
                    "Debe seleccionar el docente."
                ),
                "periodos": []
            })

        control_estudio = (
            ControlEstudio.objects
            .filter(
                usuario__cedula_identidad=cedula,
                nucleo_id=nucleo,
                activo=True
            )
            .first()
        )

        if not control_estudio:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Control de Estudio",
                "descripcion": (
                    "El usuario no está asignado como encargado "
                    "de Control de Estudio en el núcleo seleccionado."
                ),
                "periodos": []
            })

        docente_obj = (
            Docente.objects
            .filter(
                usuario__cedula_identidad=id_docente,
                nucleo_id=nucleo,
                pnf_id=pnf,
                activo=True
            )
            .first()
        )

        if not docente_obj:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Docente no encontrado",
                "descripcion": (
                    "El docente seleccionado no está asignado "
                    "al núcleo y P.N.F seleccionados."
                ),
                "periodos": []
            })

    else:

        return JsonResponse({
            "estado": "fallo",
            "icon": "error",
            "title": "Perfil no válido",
            "descripcion": (
                "El perfil seleccionado no es válido."
            ),
            "periodos": []
        })

    # =========================================================
    # MATERIA
    # =========================================================

    try:

        materia_asignada_obj = (
            MateriaAsignada.objects
            .select_related(
                "materia",
                "materia__id_trayecto"
            )
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
            "descripcion": (
                "La materia asignada no es válida."
            ),
            "periodos": []
        })

    # =========================================================
    # VALIDAR TRAYECTO
    # =========================================================

    if trayecto:

        if str(
            materia_asignada_obj.materia.id_trayecto_id
        ) != str(trayecto):

            return JsonResponse({
                "estado": "exito",
                "periodos": []
            })

    # =========================================================
    # PERÍODOS
    # =========================================================

    filtros_calificacion = {
        "materia_asignada": materia_asignada_obj,
        "estudiante__nucleo_id": nucleo,
        "estudiante__pnf_id": pnf,
        "materia_asignada__docentes__docente": docente_obj,
        "materia_asignada__docentes__activo": True
    }

    if trayecto:

        filtros_calificacion[
            "estudiante__estatus__trayecto_id"
        ] = trayecto

    periodos = (
        PeriodoAcademicoMateria.objects
        .filter(
            materia=materia_asignada_obj.materia,
            calificaciones_periodo__isnull=False,
            calificaciones_periodo__materia_asignada=(
                materia_asignada_obj
            ),
            calificaciones_periodo__estudiante__nucleo_id=nucleo,
            calificaciones_periodo__estudiante__pnf_id=pnf,
            calificaciones_periodo__materia_asignada__docentes__docente=(
                docente_obj
            ),
            calificaciones_periodo__materia_asignada__docentes__activo=True
        )
        .select_related(
            "periodo"
        )
        .values(
            "id",
            "periodo__id_periodo_academico",
            "periodo__nombre"
        )
        .distinct()
        .order_by(
            "periodo__nombre"
        )
    )

    datos_periodos = [
        {
            "id_periodo_materia": periodo["id"],
            "id_periodo_academico": (
                periodo["periodo__id_periodo_academico"]
            ),
            "nombre_periodo": (
                periodo["periodo__nombre"]
            )
        }
        for periodo in periodos
    ]

    return JsonResponse({
        "estado": "exito",
        "periodos": datos_periodos
    })

def fech_reg_not(request):
    if request.method == "POST":
        cedula = request.session.get("cedula_usuario")
        nucleo = request.POST.get("id_nucleo")
        pnf = request.POST.get("id_pnf")
        materia_asignada = request.POST.get("id_materia_asignada")
        id_periodo_materia = request.POST.get("id_periodo_academico")
        trayecto = request.POST.get("trayecto")
        cedula_docente = request.POST.get("docente")
        perfil = request.POST.get("perfil")

        if not all([
            cedula,
            nucleo,
            pnf,
            materia_asignada,
            id_periodo_materia,
            trayecto,
            perfil
        ]):
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Datos incompletos",
                "descripcion": (
                    "Debe seleccionar el núcleo, P.N.F, "
                    "trayecto, materia y período académico."
                )
            })

        if perfil == "DOCENTE":

            docente = (
                Docente.objects
                .filter(
                    usuario__cedula_identidad=cedula,
                    nucleo_id=nucleo,
                    pnf_id=pnf,
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
                        "El docente de la sesión no está asignado "
                        "al núcleo y P.N.F seleccionados."
                    )
                })

        elif perfil == "CONTROL_ESTUDIO":

            if not cedula_docente:
                return JsonResponse({
                    "estado": "fallo",
                    "icon": "warning",
                    "title": "Docente",
                    "descripcion": (
                        "Debe seleccionar el docente que registró "
                        "las notas académicas."
                    )
                })

            control_estudio = (
                ControlEstudio.objects
                .filter(
                    usuario__cedula_identidad=cedula,
                    nucleo_id=nucleo,
                    activo=True
                )
                .first()
            )

            if not control_estudio:
                return JsonResponse({
                    "estado": "fallo",
                    "icon": "error",
                    "title": "Control de Estudio",
                    "descripcion": (
                        "El usuario no está asignado como encargado "
                        "de Control de Estudio en el núcleo seleccionado."
                    )
                })

            docente = (
                Docente.objects
                .filter(
                    usuario__cedula_identidad=cedula_docente,
                    nucleo_id=nucleo,
                    pnf_id=pnf,
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
                        "El docente seleccionado no está asignado "
                        "al núcleo y P.N.F seleccionados."
                    )
                })

        else:

            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Perfil no válido",
                "descripcion": (
                    "El perfil seleccionado no es válido."
                )
            })

        try:
            materia_asignacion = (
                MateriaAsignada.objects
                .select_related(
                    "materia",
                    "materia__id_trayecto"
                )
                .get(
                    id_materia_asignada=materia_asignada,
                    materia__id_pnf=pnf,
                    materia__id_trayecto_id=trayecto,
                    activo=True,
                    docentes__docente=docente,
                    docentes__activo=True
                )
            )

        except MateriaAsignada.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Materia no encontrada",
                "descripcion": (
                    "La materia seleccionada no pertenece al "
                    "núcleo, P.N.F, trayecto o docente indicado."
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
                trayecto__id_periodo_academico=trayecto,
                fecha_promedio__isnull=False
            )
            .values_list(
                "fecha_promedio",
                flat=True
            )
            .distinct()
            .order_by(
                "-fecha_promedio"
            )
        )

        fechas_lista = [
            fecha.strftime("%Y-%m-%d")
            for fecha in fechas
        ]

        return JsonResponse({
            "estado": "exito",
            "fechas": fechas_lista
        })

    return JsonResponse({
        "estado": "fallo",
        "icon": "error",
        "title": "Solicitud no válida",
        "descripcion": (
            "La solicitud debe realizarse mediante POST."
        )
    })

def vis_cant_planif(request):
    if request.method != "POST":
        return JsonResponse({
            "estado": "fallo",
            "title": "Error",
            "icon": "error",
            "descripcion": "Método de solicitud no permitido."
        })

    nucleo = request.POST.get("id_nucleo")
    pnf = request.POST.get("id_pnf")
    materia_asignada = request.POST.get("id_materia_asignada")
    periodo_materia = request.POST.get("id_periodo_materia")
    trayecto = request.POST.get("trayecto")
    docente = request.POST.get("docente")
    perfil = request.POST.get("perfil")
    cedula = request.session.get("cedula_usuario")
    fecha_calificacion = request.POST.get("fecha_calificacion")

    if not cedula:
        return JsonResponse({
            "estado": "fallo",
            "title": "Sesión",
            "icon": "warning",
            "descripcion": "No se pudo identificar al usuario de la sesión."
        })

    if perfil not in ["CONTROL_ESTUDIO", "DOCENTE"]:
        return JsonResponse({
            "estado": "fallo",
            "title": "Perfil",
            "icon": "warning",
            "descripcion": (
                "El perfil indicado no permite realizar esta consulta."
            )
        })

    if not all([
        nucleo,
        pnf,
        materia_asignada,
        periodo_materia,
        trayecto,
        fecha_calificacion
    ]):
        return JsonResponse({
            "estado": "fallo",
            "title": "Datos incompletos",
            "icon": "warning",
            "descripcion": "Faltan datos para realizar la consulta."
        })

    # AÑO EN CURSO
    anio_actual = timezone.localdate().year

    # VALIDAR FECHA
    try:
        fecha_calificacion = datetime.strptime(
            fecha_calificacion,
            "%Y-%m-%d"
        ).date()

    except (ValueError, TypeError):
        return JsonResponse({
            "estado": "fallo",
            "title": "Fecha",
            "icon": "warning",
            "descripcion": "La fecha de calificación no es válida."
        })

    # ==========================================================
    # VALIDAR PERFIL DOCENTE
    # ==========================================================

    if perfil == "DOCENTE":

        try:
            docente_obj = (
                Docente.objects
                .get(
                    usuario__cedula_identidad=cedula,
                    nucleo_id=nucleo,
                    pnf_id=pnf,
                    activo=True
                )
            )

        except Docente.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "title": "Docente",
                "icon": "warning",
                "descripcion": (
                    "No se encontró un registro activo de docente "
                    "para el núcleo y PNF seleccionados."
                )
            })

    # ==========================================================
    # VALIDAR PERFIL CONTROL DE ESTUDIO
    # ==========================================================

    elif perfil == "CONTROL_ESTUDIO":

        if not docente:
            return JsonResponse({
                "estado": "fallo",
                "title": "Docente",
                "icon": "warning",
                "descripcion": "Debe seleccionar un docente."
            })

        try:
            ControlEstudio.objects.get(
                usuario__cedula_identidad=cedula,
                nucleo_id=nucleo,
                activo=True
            )

        except ControlEstudio.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "title": "Control de Estudio",
                "icon": "error",
                "descripcion": (
                    "El usuario no tiene un perfil activo de "
                    "Control de Estudio."
                )
            })

        try:
            docente_obj = (
                Docente.objects
                .get(
                    usuario__cedula_identidad=docente,
                    nucleo_id=nucleo,
                    pnf_id=pnf,
                    activo=True
                )
            )

        except Docente.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "title": "Docente",
                "icon": "warning",
                "descripcion": (
                    "El docente seleccionado no está asignado "
                    "al núcleo y PNF seleccionados."
                )
            })

    # ==========================================================
    # VALIDAR MATERIA ASIGNADA
    # ==========================================================

    try:
        materia_asignada_obj = (
            MateriaAsignada.objects
            .select_related("materia")
            .get(
                id_materia_asignada=materia_asignada,
                activo=True,
                materia__id_pnf_id=pnf
            )
        )

    except MateriaAsignada.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "title": "Materia",
            "icon": "error",
            "descripcion": (
                "La materia asignada no es válida, "
                "se encuentra inactiva o no pertenece "
                "al PNF seleccionado."
            )
        })

    # ==========================================================
    # VALIDAR PERÍODO ACADÉMICO
    # ==========================================================

    try:
        periodo_materia_obj = (
            PeriodoAcademicoMateria.objects
            .select_related("periodo")
            .get(
                periodo_id=periodo_materia,
                materia=materia_asignada_obj.materia
            )
        )

    except PeriodoAcademicoMateria.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "title": "Período académico",
            "icon": "error",
            "descripcion": (
                "La materia seleccionada no está asociada "
                "al período académico seleccionado."
            )
        })

    # ==========================================================
    # BUSCAR PLANIFICACIÓN DEL AÑO EN CURSO
    # ==========================================================

    planificacion = (
        PlanificacionAcademica.objects
        .filter(
            pnf_id=pnf,
            nucleo_id=nucleo,
            materia_asignacion=materia_asignada_obj,
            periodo_academico=periodo_materia_obj.periodo,
            fecha_creacion__year=anio_actual,
            activo=True,
            estado_aceptacion="ACEPTADA"
        )
        .order_by("-id_planificacion")
        .first()
    )

    if not planificacion:
        return JsonResponse({
            "estado": "exito",
            "cantidad_actividades": 0
        })

    # ==========================================================
    # CALIFICACIONES DEL AÑO EN CURSO
    # ==========================================================

    calificaciones = (
        Calificaciones.objects
        .filter(
            planificacion_academica=planificacion,
            periodo_materia=periodo_materia_obj,
            materia_asignada=materia_asignada_obj,
            trayecto_id=trayecto,
            estudiante__nucleo_id=nucleo,
            estudiante__pnf_id=pnf,
            estudiante__anio=anio_actual,
            detalles_unidad__registrado_por=docente_obj.usuario
        )
        .distinct()
    )

    # ==========================================================
    # CALIFICACIONES CON DETALLE EN LA FECHA SOLICITADA
    # ==========================================================

    calificaciones_fecha = (
        calificaciones
        .filter(
            detalles_unidad__fecha_calificacion=fecha_calificacion
        )
        .distinct()
    )

    if not calificaciones_fecha.exists():
        return JsonResponse({
            "estado": "exito",
            "cantidad_actividades": 0
        })

    # ==========================================================
    # CONTAR UNIDADES REGISTRADAS EN ESA FECHA
    # ==========================================================

    cantidad_unidades = (
        DetalleCalificacionesUnidad.objects
        .filter(
            calificacion__in=calificaciones_fecha,
            fecha_calificacion=fecha_calificacion,
            registrado_por=docente_obj
        )
        .values("unidad_id")
        .distinct()
        .count()
    )

    return JsonResponse({
        "estado": "exito",
        "cantidad_actividades": cantidad_unidades
    })

def calf_reg_not(request):
    if request.method == "POST":
        cedula = request.session.get("cedula_usuario")

        nucleo = request.POST.get("id_nucleo")
        pnf = request.POST.get("id_pnf")
        materia_asignada = request.POST.get("id_materia_asignada")
        id_periodo_materia = request.POST.get("id_periodo_materia")
        fecha_calificacion = request.POST.get("fecha_calificacion")
        trayecto = request.POST.get("trayecto")
        cedula_docente = request.POST.get("docente")
        perfil = request.POST.get("perfil")
       

        if not all([
            cedula,
            nucleo,
            pnf,
            materia_asignada,
            id_periodo_materia,
            trayecto,
            perfil
        ]):
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Datos incompletos",
                "descripcion": (
                    "Faltan datos para realizar la consulta."
                )
            })

        # VALIDACIÓN DEL PERFIL
        if perfil == "DOCENTE":
            docente = (
                Docente.objects
                .filter(
                    usuario__cedula_identidad=cedula,
                    nucleo_id=nucleo,
                    pnf_id=pnf,
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
                        "El docente de la sesión no está asignado "
                        "al núcleo y P.N.F seleccionados."
                    )
                })

        elif perfil == "CONTROL_ESTUDIO":
            if not cedula_docente:
                return JsonResponse({
                    "estado": "fallo",
                    "icon": "warning",
                    "title": "Docente",
                    "descripcion": (
                        "Debe seleccionar el docente cuyas "
                        "calificaciones desea consultar."
                    )
                })

            control_estudio = (
                ControlEstudio.objects
                .filter(
                    usuario__cedula_identidad=cedula,
                    nucleo_id=nucleo,
                    activo=True
                )
                .first()
            )

            if not control_estudio:
                return JsonResponse({
                    "estado": "fallo",
                    "icon": "error",
                    "title": "Control de Estudio",
                    "descripcion": (
                        "El usuario no está asignado como encargado "
                        "de Control de Estudio en el núcleo seleccionado."
                    )
                })

            docente = (
                Docente.objects
                .filter(
                    usuario__cedula_identidad=cedula_docente,
                    nucleo_id=nucleo,
                    pnf_id=pnf,
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
                        "El docente seleccionado no está asignado "
                        "al núcleo y P.N.F seleccionados."
                    )
                })

        else:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Perfil no válido",
                "descripcion": (
                    "El perfil seleccionado no es válido."
                )
            })

        # VALIDAR MATERIA ASIGNADA
        try:
            materia_asignacion = (
                MateriaAsignada.objects
                .select_related(
                    "materia",
                    "materia__id_trayecto"
                )
                .get(
                    id_materia_asignada=materia_asignada,
                    materia__id_pnf=pnf,
                    materia__id_trayecto_id=trayecto,
                    activo=True,
                    docentes__docente=docente,
                    docentes__activo=True
                )
            )

        except MateriaAsignada.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Materia no encontrada",
                "descripcion": (
                    "La materia seleccionada no existe, "
                    "se encuentra inactiva, no pertenece al "
                    "P.N.F, trayecto o docente seleccionado."
                )
            })

        periodo_academico = PeriodoAcademico.objects.get(id_periodo_academico=id_periodo_materia)

        # VALIDAR PERIODO ACADÉMICO
        try:
            periodo_materia = (
                PeriodoAcademicoMateria.objects
                .select_related(
                    "periodo",
                    "materia"
                )
                .get(
                    periodo=periodo_academico,
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

        # CONSULTAR CALIFICACIONES
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

                trayecto__id_periodo_academico=trayecto,

                materia_asignada__docentes__docente=docente,
                materia_asignada__docentes__activo=True
            )
            .order_by(
                "estudiante__usuario__apellidos",
                "estudiante__usuario__nombres"
            )
            .distinct()
        )

        # FILTRAR POR FECHA
        if fecha_calificacion:
            calificaciones = calificaciones.filter(
                detalles_unidad__fecha_calificacion=fecha_calificacion
            ).distinct()

        # CONSTRUIR RESPUESTA
        datos = []
        for calificacion in calificaciones:
            estudiante = calificacion.estudiante
            usuario = estudiante.usuario
        
            unidades = []
            for detalle in calificacion.detalles_unidad.all():

                unidades.append({
                    "id_detalle": (
                        detalle.id_detalle_calificaciones_unidad
                    ),
                    "id_unidad": detalle.unidad_id,
                    "nombre_unidad": (
                        detalle.unidad.titulo_unidad
                    ),
                    "nota_unidad": str(
                        detalle.nota_unidad
                    ),
                    "fecha_calificacion": (
                        detalle.fecha_calificacion.strftime(
                            "%Y-%m-%d"
                        )
                        if detalle.fecha_calificacion
                        else None
                    ),

                    "congelada": detalle.congelada,

                    "fecha_congelacion": (
                        detalle.fecha_congelacion.strftime(
                            "%Y-%m-%d %H:%M:%S"
                        )
                        if detalle.fecha_congelacion
                        else None
                    )
                })

            datos.append({
                "id_calificaciones": (
                    calificacion.id_calificaciones
                ),
                "id_estudiante": (
                    estudiante.id_estudiante
                ),
                "nombre_estudiante": (
                    f"{usuario.nombres} {usuario.apellidos}"
                ),
                "cedula_identidad": (
                    usuario.cedula_identidad
                ),
                "promedio": (
                    str(calificacion.promedio_tramo)
                    if calificacion.promedio_tramo is not None
                    else None
                ),
                "asistencia": (
                    calificacion.asistencia
                ),
                "condicion": (
                    calificacion.condicion
                ),
                "trayecto": (
                    calificacion.trayecto.nombre
                    if calificacion.trayecto
                    else None
                ),
                "congelada": (
                    calificacion.congelada
                ),
                "fecha_congelacion": (
                    calificacion.fecha_congelacion.strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                    if calificacion.fecha_congelacion
                    else None
                ),
                "unidades": unidades
            })

        if not datos:
            return JsonResponse({
                "estado": "vacio",
                "icon": "info",
                "title": "Sin calificaciones",
                "descripcion": (
                    "No existen calificaciones registradas "
                    "para la materia, período académico, "
                    "trayecto y docente seleccionados."
                ),
                "calificaciones": []
            })

        return JsonResponse({
            "estado": "exito",
            "calificaciones": datos
        })

    return JsonResponse({
        "estado": "fallo",
        "icon": "error",
        "title": "Solicitud no válida",
        "descripcion": (
            "La solicitud debe realizarse mediante POST."
        )
    })

# Modificar Notas Académicas

def nucl_mod_not(request):
    cedula = request.session.get("cedula_usuario")
    perfil = request.POST.get("perfil")

    if not cedula:
        return JsonResponse({
            "estado": "fallo",
            "icon": "warning",
            "title": "Sesión no válida",
            "descripcion": "No se encontró un usuario autenticado."
        })

    if perfil not in ("DOCENTE", "CONTROL_ESTUDIO"):
        return JsonResponse({
            "estado": "fallo",
            "icon": "warning",
            "title": "Perfil no válido",
            "descripcion": "El perfil seleccionado no es válido."
        })

    fecha_actual = timezone.localdate()

    calendario_carga_notas = CalendarioAcademico.objects.filter(
        tipo="CARGA_NOTAS",
        activo=True,
        fecha_inicio__lte=fecha_actual,
        fecha_final__gte=fecha_actual
    ).exists()

    if not calendario_carga_notas:
        return JsonResponse({
            "estado": "vacio",
            "icon": "warning",
            "title": "Modificación de calificaciones no disponible",
            "descripcion": (
                "Actualmente no se encuentra vigente el período "
                "establecido en el calendario académico para la "
                "carga y modificación de notas."
            ),
            "datos": []
        })

    if perfil == "DOCENTE":

        nucleos = (
            Nucleos.objects
            .filter(
                docente__usuario__cedula_identidad=cedula,
                docente__activo=True,
                docente__materias_asignadas__activo=True,
                docente__materias_asignadas__materia_asignada__activo=True,
                docente__materias_asignadas__materia_asignada__materia__activa=True,
                docente__materias_asignadas__materia_asignada__calificaciones_materia__isnull=False
            )
            .distinct()
        )

    else:

        nucleos = (
            Nucleos.objects
            .filter(
                docente__activo=True,
                docente__materias_asignadas__activo=True,
                docente__materias_asignadas__materia_asignada__activo=True,
                docente__materias_asignadas__materia_asignada__materia__activa=True,
                docente__materias_asignadas__materia_asignada__calificaciones_materia__isnull=False
            )
            .distinct()
        )

    datos = [
        {
            "id_nucleo": nucleo.id_nucleo,
            "municipio": nucleo.municipio,
            "direccion": nucleo.direccion,
        }
        for nucleo in nucleos
    ]

    if not datos:
        return JsonResponse({
            "estado": "vacio",
            "icon": "info",
            "title": "No hay calificaciones registradas",
            "descripcion": (
                "No existen calificaciones registradas para "
                "materias activas y asignaciones activas."
            ),
            "datos": []
        })

    return JsonResponse({
        "estado": "exito",
        "datos": datos
    })

def pnf_mod_not(request):
    cedula = request.session.get("cedula_usuario")
    nucleo_asignado = request.POST.get("nucleo_asignado").strip()
    perfil = request.POST.get("perfil", "").strip()

    if not cedula or not nucleo_asignado or not perfil:
        return JsonResponse({
            "estado": "vacio",
            "datos": [],
            "title": "Datos incompletos",
            "descripcion": "No se recibieron todos los datos necesarios.",
            "icon": "info"
        })

    fecha_actual = timezone.localdate()

    calendario_carga_notas = CalendarioAcademico.objects.filter(
        tipo="CARGA_NOTAS",
        activo=True,
        fecha_inicio__lte=fecha_actual,
        fecha_final__gte=fecha_actual
    ).exists()

    if not calendario_carga_notas:
        return JsonResponse({
            "estado": "vacio",
            "datos": [],
            "title": "Modificación de calificaciones no disponible",
            "descripcion": (
                "Actualmente no se encuentra vigente el período "
                "establecido en el calendario académico para la "
                "carga y modificación de notas."
            ),
            "icon": "warning"
        })

    if perfil == "CONTROL_ESTUDIO":

        control_estudio = (
            ControlEstudio.objects
            .filter(
                usuario__cedula_identidad=cedula,
                nucleo_id=nucleo_asignado,
                activo=True
            )
            .first()
        )

        if not control_estudio:
            return JsonResponse({
                "estado": "vacio",
                "datos": [],
                "title": "Control de Estudio no disponible",
                "descripcion": (
                    "No existe un perfil activo de Control de Estudio "
                    "asociado a este núcleo."
                ),
                "icon": "info"
            })

        pnfs = (
            Pnf.objects
            .filter(
                pnfnucleo__id_nucleo=nucleo_asignado,
                materia__activa=True,
                materia__asignaciones__activo=True,
                materia__asignaciones__docentes__activo=True,
                materia__asignaciones__calificaciones_materia__isnull=False
            )
            .distinct()
            .order_by("pnf")
        )

    elif perfil == "DOCENTE":

        docente = (
            Docente.objects
            .filter(
                usuario__cedula_identidad=cedula,
                nucleo_id=nucleo_asignado,
                activo=True
            )
            .first()
        )

        if not docente:
            return JsonResponse({
                "estado": "vacio",
                "datos": [],
                "title": "Docente no disponible",
                "descripcion": (
                    "No existe un registro activo de docente "
                    "para el núcleo seleccionado."
                ),
                "icon": "info"
            })

        pnfs = (
            Pnf.objects
            .filter(
                id_pnf=docente.pnf_id,
                pnfnucleo__id_nucleo=nucleo_asignado,
                materia__activa=True,
                materia__asignaciones__activo=True,
                materia__asignaciones__docentes__docente=docente,
                materia__asignaciones__docentes__activo=True,
                materia__asignaciones__calificaciones_materia__isnull=False
            )
            .distinct()
            .order_by("pnf")
        )

    else:
        return JsonResponse({
            "estado": "vacio",
            "datos": [],
            "title": "Perfil no válido",
            "descripcion": "El perfil seleccionado no es válido.",
            "icon": "info"
        })

    if not pnfs.exists():
        return JsonResponse({
            "estado": "vacio",
            "datos": [],
            "title": "No hay P.N.F con calificaciones",
            "descripcion": (
                "No existen P.N.F con materias activas, asignaciones "
                "activas y calificaciones registradas."
            ),
            "icon": "info"
        })

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

def doc_mod_not(request):
    nucleo_asignado = request.POST.get("nucleo_asignado")
    pnf_seleccionado = request.POST.get("pnf_seleccionado")
    cedula = request.session.get("cedula_usuario")

    if not nucleo_asignado or not pnf_seleccionado:
        return JsonResponse({
            "estado": "fallo",
            "datos": [],
            "title": "Datos incompletos",
            "descripcion": (
                "Debe seleccionar el núcleo y el PNF "
                "para modificar calificaciones."
            ),
            "icon": "warning"
        })

    fecha_actual = timezone.localdate()

    calendario_carga_notas = CalendarioAcademico.objects.filter(
        tipo="CARGA_NOTAS",
        activo=True,
        fecha_inicio__lte=fecha_actual,
        fecha_final__gte=fecha_actual
    ).exists()

    if not calendario_carga_notas:
        return JsonResponse({
            "estado": "fallo",
            "datos": [],
            "title": "Modificación de calificaciones no disponible",
            "descripcion": (
                "Actualmente no se encuentra vigente el período "
                "establecido en el calendario académico para la "
                "carga de notas."
            ),
            "icon": "warning"
        })

    calificaciones_docente = Calificaciones.objects.filter(
        materia_asignada__docentes__docente=OuterRef("pk"),
        materia_asignada__docentes__activo=True,
        materia_asignada__activo=True,
        materia_asignada__materia__activa=True
    )

    docentes = (
        Docente.objects
        .filter(
            nucleo_id=nucleo_asignado,
            pnf_id=pnf_seleccionado,
            activo=True,
            materias_asignadas__activo=True,
            materias_asignadas__materia_asignada__activo=True,
            materias_asignadas__materia_asignada__materia__activa=True
        )
        .exclude(
            usuario__cedula_identidad=cedula
        )
        .annotate(
            tiene_calificaciones=Exists(calificaciones_docente)
        )
        .filter(
            tiene_calificaciones=True
        )
        .select_related("usuario")
        .distinct()
    )

    if not docentes.exists():
        return JsonResponse({
            "estado": "fallo",
            "datos": [],
            "title": "No hay docentes con calificaciones",
            "descripcion": (
                "No existen otros docentes activos con materias activas "
                "y calificaciones registradas para el núcleo y PNF "
                "seleccionado."
            ),
            "icon": "info"
        })

    datos = [
        {
            "id_docente": docente.id_docente,
            "cedula": docente.usuario.cedula_identidad,
            "nombres": docente.usuario.nombres,
            "apellidos": docente.usuario.apellidos,
        }
        for docente in docentes
    ]

    return JsonResponse({
        "estado": "exito",
        "datos": datos
    })

def tray_mod_not(request):
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
    cedula_docente = request.POST.get("docente")
    perfil = request.POST.get("perfil")

    if not cedula:
        return JsonResponse({
            "estado": "fallo",
            "title": "Sesión",
            "icon": "warning",
            "descripcion": "No se pudo identificar al usuario de la sesión."
        })

    if perfil not in ["CONTROL_ESTUDIO", "DOCENTE"]:
        return JsonResponse({
            "estado": "fallo",
            "title": "Perfil",
            "icon": "warning",
            "descripcion": "El perfil indicado no permite consultar trayectos."
        })

    if not nucleo or not pnf:
        return JsonResponse({
            "estado": "fallo",
            "title": "Datos incompletos",
            "icon": "warning",
            "descripcion": "Debe indicar el núcleo y el PNF."
        })

    # OBTENER DOCENTE(S)
    if perfil == "DOCENTE":

        try:
            docente = Docente.objects.get(
                usuario__cedula_identidad=cedula,
                activo=True,
                nucleo_id=nucleo,
                pnf_id=pnf
            )
        except Docente.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "title": "Docente",
                "icon": "warning",
                "descripcion": (
                    "No se encontró un registro activo de docente "
                    "para el núcleo y PNF seleccionados."
                )
            })

        id_docentes = [docente.id_docente]

    else:

        try:
            ControlEstudio.objects.get(
                usuario__cedula_identidad=cedula,
                activo=True
            )
        except ControlEstudio.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "title": "Control de Estudio",
                "icon": "error",
                "descripcion": (
                    "El usuario no tiene un perfil activo de "
                    "Control de Estudio."
                )
            })

        id_docentes = list(
            Docente.objects.filter(
                usuario__cedula_identidad=cedula_docente,
                nucleo_id=nucleo,
                pnf_id=pnf,
                activo=True
            ).values_list(
                "id_docente",
                flat=True
            )
        )

        if not id_docentes:
            return JsonResponse({
                "estado": "fallo",
                "title": "Docente",
                "icon": "warning",
                "descripcion": (
                    "El docente no posee una asignación activa "
                    "para el núcleo y PNF seleccionados."
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
                "title": "Modificación de notas no habilitada",
                "icon": "warning",
                "descripcion": (
                    "Actualmente no existe un período académico "
                    "habilitado para la modificación de notas. "
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
                "title": "Plazo de modificación vencido",
                "icon": "warning",
                "descripcion": (
                    "El plazo de carga de notas del período "
                    f"{calendario_anterior.periodo.nombre} "
                    f"finalizó el "
                    f"{calendario_anterior.calendario.fecha_final.strftime('%d/%m/%Y')}. "
                    "Actualmente no existe otro período académico "
                    "habilitado para modificar notas."
                )
            })

        return JsonResponse({
            "estado": "fallo",
            "title": "Modificación de notas no habilitada",
            "icon": "warning",
            "descripcion": (
                "Actualmente no existe un período académico "
                "habilitado para modificar notas."
            )
        })

    # PERÍODOS ACADÉMICOS ACTUALMENTE VIGENTES
    periodos_actuales = calendarios_periodos.values_list(
        "periodo_id",
        flat=True
    )

    # TRAYECTOS CON NOTAS REGISTRADAS
    trayectos = (
        TrayectoAcademico.objects
        .filter(
            materia__id_pnf_id=pnf,
            materia__activa=True,

            materia__asignaciones__activo=True,

            materia__asignaciones__docentes__docente_id__in=id_docentes,
            materia__asignaciones__docentes__activo=True,

            materia__periodos_academicos__periodo_id__in=periodos_actuales,

            materia__asignaciones__calificaciones_materia__isnull=False
        )
        .distinct()
        .order_by(
            "id_periodo_academico"
        )
    )

    if not trayectos.exists():
        return JsonResponse({
            "estado": "vacio",
            "title": "No hay notas registradas",
            "icon": "info",
            "descripcion": (
                "El docente no tiene calificaciones registradas "
                "en materias activas correspondientes a los "
                "períodos académicos actualmente habilitados."
            ),
            "trayectos": []
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

def mod_mat_not(request):
    if request.method == "POST":
        cedula = request.session.get("cedula_usuario")
        id_nucleo = request.POST.get("id_nucleo")
        id_pnf = request.POST.get("id_pnf")
        trayecto = request.POST.get("trayecto")
        cedula_docente = request.POST.get("docente")
        perfil = request.POST.get("perfil")

        if not all([
            cedula,
            id_nucleo,
            id_pnf,
            trayecto,
            perfil
        ]):
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Datos incompletos",
                "descripcion": (
                    "Faltan datos para realizar la consulta."
                )
            })

        if perfil == "DOCENTE":

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

            cedula_docente = cedula

        elif perfil == "CONTROL_ESTUDIO":

            if not cedula_docente:
                return JsonResponse({
                    "estado": "fallo",
                    "icon": "warning",
                    "title": "Docente",
                    "descripcion": (
                        "Debe seleccionar el docente cuyas "
                        "calificaciones desea modificar."
                    )
                })

            control_estudio = (
                ControlEstudio.objects
                .filter(
                    usuario__cedula_identidad=cedula,
                    nucleo_id=id_nucleo,
                    activo=True
                )
                .first()
            )

            if not control_estudio:
                return JsonResponse({
                    "estado": "fallo",
                    "icon": "error",
                    "title": "Control de Estudio",
                    "descripcion": (
                        "El usuario no está asignado como encargado "
                        "de Control de Estudio en el núcleo seleccionado."
                    )
                })

            docente = (
                Docente.objects
                .filter(
                    usuario__cedula_identidad=cedula_docente,
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
                        "El docente seleccionado no está asignado "
                        "al núcleo y P.N.F seleccionados."
                    )
                })

        hoy = timezone.localdate()

        materias = (
            Calificaciones.objects
            .filter(
                materia_asignada__isnull=False,
                materia_asignada__activo=True,
                materia_asignada__materia__id_pnf=id_pnf,
                materia_asignada__materia__id_trayecto_id=trayecto,
                materia_asignada__docentes__docente=docente,
                materia_asignada__docentes__activo=True,
                estudiante__nucleo_id=id_nucleo,
                estudiante__pnf_id=id_pnf
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
                "materia_asignada__materia__codigo",
                "materia_asignada__materia__id_trayecto__nombre",
                "periodo_materia_id",
                "periodo_materia__periodo__id_periodo_academico",
                "periodo_materia__periodo__nombre"
            )
            .distinct()
            .order_by(
                "materia_asignada__materia__nombre",
                "periodo_materia__periodo__nombre"
            )
        )

        if not materias:
            return JsonResponse({
                "estado": "fallo",
                "icon": "info",
                "title": "Sin materias",
                "descripcion": (
                    "No existen materias con calificaciones "
                    "asignadas al docente en el núcleo, P.N.F "
                    "y trayecto seleccionados."
                )
            })

        materias_lista = []

        for materia in materias:

            periodo_id = materia[
                "periodo_materia__periodo__id_periodo_academico"
            ]

            calendario = (
                CalendarioPeriodo.objects
                .select_related("calendario")
                .filter(
                    periodo_id=periodo_id,
                    calendario__activo=True,
                    calendario__tipo="CARGA_NOTAS"
                )
                .order_by(
                    "-calendario__fecha_final"
                )
                .first()
            )

            if not calendario:
                continue

            fecha_inicio = calendario.calendario.fecha_inicio
            fecha_final = calendario.calendario.fecha_final

            if fecha_inicio <= hoy <= fecha_final:
                materias_lista.append({
                    "id_materia_asignada": materia[
                        "materia_asignada_id"
                    ],
                    "nombre_materia": materia[
                        "materia_asignada__materia__nombre"
                    ],
                    "codigo_materia": materia[
                        "materia_asignada__materia__codigo"
                    ],
                    "trayecto_materia": materia[
                        "materia_asignada__materia__id_trayecto__nombre"
                    ],
                    "id_periodo_materia": materia[
                        "periodo_materia_id"
                    ],
                    "id_periodo_academico": materia[
                        "periodo_materia__periodo__id_periodo_academico"
                    ],
                    "nombre_periodo": materia[
                        "periodo_materia__periodo__nombre"
                    ]
                })

        if not materias_lista:
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Calendario académico",
                "descripcion": (
                    "En la fecha actual no existe un período "
                    "académico habilitado para la carga y "
                    "modificación de calificaciones según "
                    "el calendario académico."
                )
            })

        return JsonResponse({
            "estado": "exito",
            "materias": materias_lista
        })

def mod_per_not(request):
    if request.method == "POST":
        cedula = request.session.get("cedula_usuario")
        pnf = request.POST.get("id_pnf")
        materia_asignada = request.POST.get("id_materia_asignada")
        nucleo = request.POST.get("id_nucleo")
        trayecto = request.POST.get("trayecto")
        cedula_docente = request.POST.get("docente")
        perfil = request.POST.get("perfil")

        if not all([
            cedula,
            pnf,
            materia_asignada,
            nucleo,
            trayecto,
            perfil
        ]):
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Datos incompletos",
                "descripcion": (
                    "Faltan datos para realizar la consulta."
                )
            })

        if perfil == "DOCENTE":

            docente_obj = (
                Docente.objects
                .filter(
                    usuario__cedula_identidad=cedula,
                    nucleo_id=nucleo,
                    pnf_id=pnf,
                    activo=True
                )
                .first()
            )

            if not docente_obj:
                return JsonResponse({
                    "estado": "fallo",
                    "icon": "error",
                    "title": "Docente no encontrado",
                    "descripcion": (
                        "El docente no está asignado al núcleo y "
                        "P.N.F seleccionados."
                    )
                })

            cedula_docente = cedula

        elif perfil == "CONTROL_ESTUDIO":

            if not cedula_docente:
                return JsonResponse({
                    "estado": "fallo",
                    "icon": "warning",
                    "title": "Docente",
                    "descripcion": (
                        "Debe seleccionar el docente cuyas "
                        "calificaciones desea modificar."
                    )
                })

            control_estudio = (
                ControlEstudio.objects
                .filter(
                    usuario__cedula_identidad=cedula,
                    nucleo_id=nucleo,
                    activo=True
                )
                .first()
            )

            if not control_estudio:
                return JsonResponse({
                    "estado": "fallo",
                    "icon": "error",
                    "title": "Control de Estudio",
                    "descripcion": (
                        "El usuario no está asignado como encargado "
                        "de Control de Estudio en el núcleo seleccionado."
                    )
                })

            docente_obj = (
                Docente.objects
                .filter(
                    usuario__cedula_identidad=cedula_docente,
                    nucleo_id=nucleo,
                    pnf_id=pnf,
                    activo=True
                )
                .first()
            )

            if not docente_obj:
                return JsonResponse({
                    "estado": "fallo",
                    "icon": "error",
                    "title": "Docente no encontrado",
                    "descripcion": (
                        "El docente seleccionado no está asignado "
                        "al núcleo y P.N.F seleccionados."
                    )
                })

        else:

            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Perfil no válido",
                "descripcion": (
                    "El perfil seleccionado no es válido."
                )
            })

        calificacion = (
            Calificaciones.objects
            .filter(
                materia_asignada_id=materia_asignada,
                materia_asignada__activo=True,
                materia_asignada__materia__id_pnf=pnf,
                materia_asignada__materia__id_trayecto_id=trayecto,
                materia_asignada__docentes__docente=docente_obj,
                materia_asignada__docentes__activo=True,
                estudiante__nucleo_id=nucleo,
                estudiante__pnf_id=pnf,
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
                "icon": "info",
                "title": "Periodo Académico",
                "descripcion": (
                    "No existen calificaciones registradas para "
                    "la materia seleccionada."
                )
            })

        periodo_materia = calificacion.periodo_materia
        periodo = periodo_materia.periodo

        return JsonResponse({
            "estado": "exito",
            "id_periodo_materia": periodo_materia.id,
            "id_periodo_academico": periodo.id_periodo_academico,
            "nombre_periodo": periodo.nombre
        })

    return JsonResponse({
        "estado": "fallo",
        "icon": "error",
        "title": "Solicitud no válida",
        "descripcion": (
            "La solicitud debe realizarse mediante POST."
        )
    })

def mod_cant_pla(request):
    if request.method != "POST":
        return JsonResponse({
            "estado": "fallo",
            "title": "Error",
            "icon": "error",
            "descripcion": "Método de solicitud no permitido."
        })

    nucleo = request.POST.get("id_nucleo")
    pnf = request.POST.get("id_pnf")
    materia_asignada = request.POST.get("id_materia_asignada")
    periodo_materia = request.POST.get("id_periodo_materia")
    trayecto = request.POST.get("trayecto")
    docente = request.POST.get("docente")
    perfil = request.POST.get("perfil")
    cedula = request.session.get("cedula_usuario")

    ano_actual = timezone.localdate().year

    # ==========================================================
    # VALIDAR SESIÓN
    # ==========================================================

    if not cedula:
        return JsonResponse({
            "estado": "fallo",
            "title": "Sesión",
            "icon": "warning",
            "descripcion": (
                "No se pudo identificar al usuario de la sesión."
            )
        })

    # ==========================================================
    # VALIDAR PERFIL
    # ==========================================================

    if perfil not in ["CONTROL_ESTUDIO", "DOCENTE"]:
        return JsonResponse({
            "estado": "fallo",
            "title": "Perfil",
            "icon": "warning",
            "descripcion": (
                "El perfil indicado no permite realizar esta consulta."
            )
        })

    # ==========================================================
    # VALIDAR DATOS
    # ==========================================================

    if not all([
        nucleo,
        pnf,
        materia_asignada,
        periodo_materia,
        trayecto
    ]):
        return JsonResponse({
            "estado": "fallo",
            "title": "Datos incompletos",
            "icon": "warning",
            "descripcion": (
                "Faltan datos para realizar la consulta."
            )
        })

    # ==========================================================
    # VALIDAR DOCENTE
    # ==========================================================

    if perfil == "DOCENTE":

        try:
            docente_obj = (
                Docente.objects
                .get(
                    usuario__cedula_identidad=cedula,
                    nucleo_id=nucleo,
                    pnf_id=pnf,
                    activo=True
                )
            )

        except Docente.DoesNotExist:

            return JsonResponse({
                "estado": "fallo",
                "title": "Docente",
                "icon": "warning",
                "descripcion": (
                    "No se encontró un registro activo de docente "
                    "para el núcleo y PNF seleccionados."
                )
            })

    # ==========================================================
    # VALIDAR CONTROL DE ESTUDIO
    # ==========================================================

    elif perfil == "CONTROL_ESTUDIO":

        if not docente:
            return JsonResponse({
                "estado": "fallo",
                "title": "Docente",
                "icon": "warning",
                "descripcion": "Debe seleccionar un docente."
            })

        try:
            ControlEstudio.objects.get(
                usuario__cedula_identidad=cedula,
                nucleo_id=nucleo,
                activo=True
            )

        except ControlEstudio.DoesNotExist:

            return JsonResponse({
                "estado": "fallo",
                "title": "Control de Estudio",
                "icon": "error",
                "descripcion": (
                    "El usuario no tiene un perfil activo de "
                    "Control de Estudio."
                )
            })

        try:
            docente_obj = (
                Docente.objects
                .get(
                    usuario__cedula_identidad=docente,
                    nucleo_id=nucleo,
                    pnf_id=pnf,
                    activo=True
                )
            )

        except Docente.DoesNotExist:

            return JsonResponse({
                "estado": "fallo",
                "title": "Docente",
                "icon": "warning",
                "descripcion": (
                    "El docente seleccionado no pertenece "
                    "al núcleo y PNF seleccionados."
                )
            })

    # ==========================================================
    # VALIDAR MATERIA ASIGNADA
    # ==========================================================

    try:

        materia_asignada_obj = (
            MateriaAsignada.objects
            .select_related(
                "materia",
                "materia__id_trayecto"
            )
            .get(
                id_materia_asignada=materia_asignada,
                activo=True,
                materia__id_pnf_id=pnf,
                materia__id_trayecto_id=trayecto
            )
        )

    except MateriaAsignada.DoesNotExist:

        return JsonResponse({
            "estado": "fallo",
            "title": "Materia",
            "icon": "error",
            "descripcion": (
                "La materia asignada no es válida."
            )
        })

    # ==========================================================
    # VALIDAR PERÍODO ACADÉMICO
    # ==========================================================

    try:

        periodo_materia_obj = (
            PeriodoAcademicoMateria.objects
            .select_related("periodo")
            .get(
                periodo_id=periodo_materia,
                materia=materia_asignada_obj.materia
            )
        )

    except PeriodoAcademicoMateria.DoesNotExist:

        return JsonResponse({
            "estado": "fallo",
            "title": "Período académico",
            "icon": "error",
            "descripcion": (
                "La materia no está asociada al período "
                "académico seleccionado."
            )
        })

    periodo = periodo_materia_obj.periodo

    # ==========================================================
    # VALIDAR QUE EL PERÍODO TENGA CALENDARIO DEL AÑO ACTUAL
    # ==========================================================

    calendario_periodo = (
        CalendarioPeriodo.objects
        .select_related("calendario")
        .filter(
            periodo=periodo,
            calendario__activo=True,
            calendario__fecha_inicio__year=ano_actual
        )
        .order_by(
            "calendario__fecha_inicio"
        )
    )

    if not calendario_periodo.exists():

        return JsonResponse({
            "estado": "exito",
            "cantidad_actividades": 0,
            "ano": ano_actual
        })

    # ==========================================================
    # BUSCAR PLANIFICACIÓN DEL AÑO EN CURSO
    # ==========================================================

    planificacion = (
        PlanificacionAcademica.objects
        .filter(
            pnf_id=pnf,
            nucleo_id=nucleo,
            materia_asignacion=materia_asignada_obj,
            periodo_academico=periodo,
            fecha_creacion__year=ano_actual,
            activo=True,
            estado_aceptacion="ACEPTADA"
        )
        .first()
    )

    # ==========================================================
    # SIN PLANIFICACIÓN
    # ==========================================================

    if not planificacion:

        return JsonResponse({
            "estado": "exito",
            "cantidad_actividades": 0,
            "ano": ano_actual
        })

    # ==========================================================
    # CANTIDAD DE UNIDADES
    # ==========================================================

    cantidad_unidades = (
        DetallePlanificacion.objects
        .filter(
            plan_academico=planificacion
        )
        .count()
    )

    # ==========================================================
    # RESPUESTA
    # ==========================================================

    return JsonResponse({
        "estado": "exito",
        "cantidad_actividades": cantidad_unidades,
        "ano": ano_actual
    })

def mod_calf_not(request):
    if request.method != "POST":
        return JsonResponse({
            "estado": "fallo",
            "icon": "error",
            "title": "Solicitud no válida",
            "descripcion": (
                "La solicitud debe realizarse mediante POST."
            )
        })

    cedula = request.session.get("cedula_usuario")
    pnf = request.POST.get("id_pnf")
    materia_asignada = request.POST.get("id_materia_asignada")
    id_periodo_materia = request.POST.get("id_periodo_materia")
    nucleo = request.POST.get("id_nucleo")
    trayecto = request.POST.get("trayecto")
    cedula_docente = request.POST.get("docente")
    perfil = request.POST.get("perfil")

    if not all([
        cedula,
        pnf,
        materia_asignada,
        id_periodo_materia,
        nucleo,
        trayecto,
        perfil
    ]):
        return JsonResponse({
            "estado": "fallo",
            "icon": "warning",
            "title": "Datos incompletos",
            "descripcion": (
                "Faltan datos para realizar la consulta."
            )
        })

    # ==========================================================
    # VALIDAR PERFIL
    # ==========================================================

    if perfil == "DOCENTE":

        docente_obj = (
            Docente.objects
            .filter(
                usuario__cedula_identidad=cedula,
                nucleo_id=nucleo,
                pnf_id=pnf,
                activo=True
            )
            .first()
        )

        if not docente_obj:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Docente no encontrado",
                "descripcion": (
                    "El docente no está asignado al núcleo y "
                    "P.N.F seleccionados."
                )
            })

        cedula_docente = cedula

    elif perfil == "CONTROL_ESTUDIO":

        if not cedula_docente:
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Docente",
                "descripcion": (
                    "Debe seleccionar el docente que registró "
                    "las calificaciones."
                )
            })

        control_estudio = (
            ControlEstudio.objects
            .filter(
                usuario__cedula_identidad=cedula,
                nucleo_id=nucleo,
                activo=True
            )
            .first()
        )

        if not control_estudio:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Control de Estudio",
                "descripcion": (
                    "El usuario no está asignado como encargado "
                    "de Control de Estudio en el núcleo seleccionado."
                )
            })

        docente_obj = (
            Docente.objects
            .filter(
                usuario__cedula_identidad=cedula_docente,
                nucleo_id=nucleo,
                pnf_id=pnf,
                activo=True
            )
            .first()
        )

        if not docente_obj:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Docente no encontrado",
                "descripcion": (
                    "El docente seleccionado no está asignado "
                    "al núcleo y P.N.F seleccionados."
                )
            })

    else:

        return JsonResponse({
            "estado": "fallo",
            "icon": "error",
            "title": "Perfil no válido",
            "descripcion": (
                "El perfil seleccionado no es válido."
            )
        })

    # ==========================================================
    # MATERIA ASIGNADA
    # ==========================================================

    try:

        materia_asignada_obj = (
            MateriaAsignada.objects
            .select_related(
                "materia",
                "materia__id_trayecto"
            )
            .get(
                id_materia_asignada=materia_asignada,
                activo=True,
                materia__id_pnf=pnf,
                materia__id_trayecto_id=trayecto,
                docentes__docente=docente_obj,
                docentes__activo=True
            )
        )

    except MateriaAsignada.DoesNotExist:

        return JsonResponse({
            "estado": "fallo",
            "icon": "error",
            "title": "Materia no encontrada",
            "descripcion": (
                "La materia asignada no es válida, "
                "no pertenece al trayecto seleccionado "
                "o no está asignada al docente seleccionado."
            )
        })

    # ==========================================================
    # PERÍODO ACADÉMICO DE LA MATERIA
    # ==========================================================

    try:

        periodo_materia = (
            PeriodoAcademicoMateria.objects
            .select_related(
                "periodo",
                "materia"
            )
            .get(
                periodo__id_periodo_academico=id_periodo_materia,
                materia=materia_asignada_obj.materia
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

    # ==========================================================
    # AÑO ACADÉMICO ACTUAL
    # ==========================================================

    ano_actual = timezone.localdate().year

    # ==========================================================
    # CALIFICACIONES DEL AÑO EN CURSO
    # ==========================================================

    calificaciones = (
        Calificaciones.objects
            .filter(
                fecha_promedio__year=ano_actual,
                estudiante__nucleo_id=nucleo,
                estudiante__pnf_id=pnf,
                materia_asignada_id=materia_asignada_obj.id_materia_asignada,
                periodo_materia_id=periodo_materia.id,
                materia_asignada__docentes__docente=docente_obj,
                materia_asignada__docentes__activo=True,
                materia_asignada__materia__id_pnf=pnf,
                materia_asignada__materia__id_trayecto_id=trayecto
            )
            .select_related(
            "estudiante__usuario",
            "periodo_materia__periodo",
            "materia_asignada__materia",
            "trayecto"
        )
        .prefetch_related(
            Prefetch(
                "detalles_unidad",
                queryset=(
                    DetalleCalificacionesUnidad.objects
                    .select_related("unidad")
                    .order_by("unidad__id_detalle")
                )
            )
        )
        .order_by(
            "estudiante__usuario__apellidos",
            "estudiante__usuario__nombres",
            "estudiante__usuario__cedula_identidad"
        )
        .distinct()
    )

    if not calificaciones.exists():
        return JsonResponse({
            "estado": "fallo",
            "icon": "info",
            "title": "Sin calificaciones",
            "descripcion": (
                "No existen calificaciones registradas "
                f"para el año {ano_actual} en la materia, "
                "PNF, trayecto y período académico seleccionados."
            )
        })

    # ==========================================================
    # INFORMACIÓN GENERAL
    # ==========================================================

    primera_calificacion = calificaciones.first()

    periodo = periodo_materia.periodo
    materia = materia_asignada_obj.materia

    datos = []

    # ==========================================================
    # CONSTRUIR CALIFICACIONES
    # ==========================================================

    for calificacion in calificaciones:

        estudiante = calificacion.estudiante
        usuario = estudiante.usuario

        datos.append({
            "id_calificaciones": (
                calificacion.id_calificaciones
            ),

            "id_estudiante": (
                estudiante.id_estudiante
            ),

            "nombre_estudiante": (
                f"{usuario.nombres} {usuario.apellidos}"
            ),

            "cedula_identidad": (
                usuario.cedula_identidad
            ),

            "promedio": (
                int(calificacion.promedio_tramo)
                if calificacion.promedio_tramo is not None
                else None
            ),

            "asistencia": (
                calificacion.asistencia
            ),

            "condicion": (
                calificacion.condicion
            ),

            "trayecto": (
                calificacion.trayecto.nombre
                if calificacion.trayecto
                else None
            ),

            "congelada": (
                calificacion.congelada
            ),

            "fecha_congelacion": (
                calificacion.fecha_congelacion.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                if calificacion.fecha_congelacion
                else None
            ),

            "unidades": [
                {
                    "id_detalle": (
                        detalle.id_detalle_calificaciones_unidad
                    ),

                    "id_unidad": (
                        detalle.unidad_id
                    ),

                    "numero_unidad": (
                        indice + 1
                    ),

                    "nombre_unidad": (
                        detalle.unidad.titulo_unidad
                    ),

                    "nota_unidad": (
                        int(detalle.nota_unidad)
                        if detalle.nota_unidad is not None
                        else None
                    ),

                    "fecha_calificacion": (
                        detalle.fecha_calificacion.strftime(
                            "%Y-%m-%d"
                        )
                        if detalle.fecha_calificacion
                        else None
                    ),

                    "congelada": (
                        detalle.congelada
                    ),

                    "fecha_congelacion": (
                        detalle.fecha_congelacion.strftime(
                            "%Y-%m-%d %H:%M:%S"
                        )
                        if detalle.fecha_congelacion
                        else None
                    )
                }
                for indice, detalle in enumerate(
                    calificacion.detalles_unidad.all()
                )
            ]
        })

    # ==========================================================
    # RESPUESTA
    # ==========================================================

    return JsonResponse({
        "estado": "exito",

        "ano": ano_actual,

        "periodo": {
            "id_periodo_materia": (
                periodo_materia.id
            ),
            "id_periodo_academico": (
                periodo.id_periodo_academico
            ),
            "nombre": periodo.nombre
        },

        "materia": {
            "id_materia_asignada": (
                materia_asignada_obj.id_materia_asignada
            ),
            "id_materia": (
                materia.id_materia
            ),
            "nombre": materia.nombre,
            "trayecto": (
                materia.id_trayecto.nombre
                if materia.id_trayecto
                else None
            )
        },

        "fecha_calificacion": (
            primera_calificacion.fecha_promedio.strftime(
                "%Y-%m-%d"
            )
            if primera_calificacion.fecha_promedio
            else None
        ),

        "calificaciones": datos
    })

@transaction.atomic
def mod_not_acad(request):
    if request.method != "POST":
        return render(request, "Notas_Academicas/modificar_notas_academicas.html")

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
    motivo = request.POST.get("motivo", "Modificación de notas académicas.").strip()

    cedula_docente = request.POST.get("seleccion_docente")
    perfil = request.POST.get("perfil")

    cedula = request.session.get("cedula_usuario")

    if not cedula:
        return respuesta(
            "error",
            "Sesión",
            "No se encontró la cédula del usuario en la sesión."
        )

    usuario = (
        Usuario.objects
        .filter(
            cedula_identidad=cedula
        )
        .first()
    )

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
                "warning",
                titulo,
                descripcion
            )

    if not perfil:
        return respuesta(
            "warning",
            "Perfil",
            "Debe seleccionar el perfil con el que realizará la modificación."
        )

    if perfil == "DOCENTE":

        docente_obj = (
            Docente.objects
            .filter(
                usuario__cedula_identidad=cedula,
                nucleo_id=nucleo,
                pnf_id=pnf,
                activo=True
            )
            .first()
        )

        if not docente_obj:
            return respuesta(
                "error",
                "Docente no encontrado",
                (
                    "El docente no está asignado al núcleo y "
                    "P.N.F seleccionados."
                )
            )

        cedula_docente = cedula

    elif perfil == "CONTROL_ESTUDIO":

        if not cedula_docente:
            return respuesta(
                "warning",
                "Docente",
                (
                    "Debe seleccionar el docente cuyas "
                    "calificaciones desea modificar."
                )
            )

        control_estudio = (
            ControlEstudio.objects
            .filter(
                usuario__cedula_identidad=cedula,
                nucleo_id=nucleo,
                activo=True
            )
            .first()
        )

        if not control_estudio:
            return respuesta(
                "error",
                "Control de Estudio",
                (
                    "El usuario no está asignado como encargado "
                    "de Control de Estudio en el núcleo seleccionado."
                )
            )

        docente_obj = (
            Docente.objects
            .filter(
                usuario__cedula_identidad=cedula_docente,
                nucleo_id=nucleo,
                pnf_id=pnf,
                activo=True
            )
            .first()
        )

        if not docente_obj:
            return respuesta(
                "error",
                "Docente no encontrado",
                (
                    "El docente seleccionado no está asignado "
                    "al núcleo y P.N.F seleccionados."
                )
            )

    else:

        return respuesta(
            "error",
            "Perfil no válido",
            "El perfil seleccionado no es válido."
        )

    try:
        materia_asignacion = (
            MateriaAsignada.objects
            .select_related(
                "materia",
                "materia__id_trayecto"
            )
            .get(
                id_materia_asignada=materia_id,
                materia__id_pnf=pnf,
                materia__id_trayecto_id=trayecto,
                activo=True,
                docentes__docente=docente_obj,
                docentes__activo=True
            )
        )

    except MateriaAsignada.DoesNotExist:
        return respuesta(
            "error",
            "Materia",
            (
                "No se encontró la materia asignada, "
                "no pertenece al trayecto seleccionado "
                "o no está asociada al docente seleccionado."
            )
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
            "Período Académico",
            (
                "No existe un período académico asociado "
                "a la materia seleccionada."
            )
        )

    hoy = timezone.localdate()
    ano_actual = hoy.year

    calendario_carga = (
        CalendarioPeriodo.objects
        .select_related(
            "calendario",
            "periodo"
        )
        .filter(
            periodo_id=periodo_materia.periodo_id,
            calendario__tipo="CARGA_NOTAS",
            calendario__activo=True,
            calendario__fecha_inicio__year=ano_actual
        )
        .order_by(
            "-calendario__fecha_final"
        )
        .first()
    )

    fecha_inicio_carga = calendario_carga.calendario.fecha_inicio
    fecha_final_carga = calendario_carga.calendario.fecha_final

    if hoy < fecha_inicio_carga:
        return respuesta(
            "warning",
            "Carga de notas no habilitada",
            (
                "El período académico seleccionado todavía no "
                "se encuentra habilitado para la modificación "
                "de calificaciones. El plazo inicia el "
                f"{fecha_inicio_carga.strftime('%d/%m/%Y')}."
            )
        )

    if hoy > fecha_final_carga:
        return respuesta(
            "warning",
            "Plazo vencido",
            (
                "El plazo establecido en el calendario académico "
                "para la modificación de calificaciones finalizó el "
                f"{fecha_final_carga.strftime('%d/%m/%Y')}. "
                "Las calificaciones de este período ya no pueden "
                "ser modificadas."
            )
        )

    ano_actual = timezone.localdate().year

    if calendario_carga.calendario.fecha_inicio.year != ano_actual:
        return respuesta(
            "warning",
            "Período académico",
            (
                f"El período académico seleccionado no corresponde "
                f"al año académico en curso ({ano_actual})."
            )
        )

    try:
        trayecto_obj = (
            TrayectoAcademico.objects
            .get(
                id_periodo_academico=trayecto
            )
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
        plan.detalles.all()
        .order_by("id_detalle")
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

    calificaciones = {}
    asistencias = {}
    estudiantes_orden = []

    for nombre, valor in request.POST.items():

        if nombre.startswith("calificacion_"):

            partes = nombre.split("_")

            if len(partes) != 3:
                continue

            estudiante_id = partes[1]
            numero_unidad = partes[2]

            if estudiante_id not in estudiantes_orden:
                estudiantes_orden.append(estudiante_id)

            calificaciones.setdefault(
                estudiante_id,
                {}
            )[numero_unidad] = valor.strip()

        elif nombre.startswith("asistencia_"):

            partes = nombre.split("_")

            if len(partes) != 2:
                continue

            estudiante_id = partes[1]

            if estudiante_id not in estudiantes_orden:
                estudiantes_orden.append(estudiante_id)

            asistencias[estudiante_id] = valor.strip()


    # IMPEDIR QUE TODOS LOS CONTROLES ESTÉN VACÍOS
    hay_datos = any(
        valor
        for notas in calificaciones.values()
        for valor in notas.values()
    ) or any(
        valor
        for valor in asistencias.values()
    )

    if not hay_datos:
        return respuesta(
            "warning",
            "Campos vacíos",
            "Debe registrar al menos una calificación o una asistencia."
        )


    # VALIDAR ESTUDIANTE POR ESTUDIANTE
    for estudiante_id in estudiantes_orden:

        notas_estudiante = calificaciones.get(
            estudiante_id,
            {}
        )

        # VALIDAR LAS UNIDADES
        for numero_unidad in range(1, len(unidades) + 1):

            valor = notas_estudiante.get(
                str(numero_unidad),
                ""
            )

            if not valor:
                return respuesta(
                    "warning",
                    "Nota faltante",
                    (
                        f"Debe registrar la nota de la unidad "
                        f"{numero_unidad} del estudiante "
                        f"{estudiante_id}."
                    )
                )

        # VALIDAR ASISTENCIA
        valor_asistencia = asistencias.get(
            estudiante_id,
            ""
        )

        if not valor_asistencia:
            return respuesta(
                "warning",
                "Asistencia faltante",
                (
                    f"Debe registrar la asistencia "
                    f"del estudiante {estudiante_id}."
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
                (
                    f"No se encontró el estudiante "
                    f"{estudiante_id}."
                )
            )


        calificaciones_existentes = (
            Calificaciones.objects
            .select_for_update()
            .filter(
                periodo_materia=periodo_materia,
                materia_asignada=materia_asignacion,
                estudiante=estudiante,
                trayecto=trayecto_obj,
                fecha_registro__year=ano_actual
            )
        )

        cantidad_calificaciones = calificaciones_existentes.count()

        if cantidad_calificaciones == 0:
            return respuesta(
                "error",
                "Calificación no encontrada",
                (
                    f"No existe una calificación para "
                    f"el estudiante {estudiante_id}."
                )
            )

        if cantidad_calificaciones > 1:
            return respuesta(
                "error",
                "Registros duplicados",
                (
                    f"El estudiante {estudiante_id} tiene "
                    f"{cantidad_calificaciones} registros principales "
                    "de calificación para la misma materia, período "
                    "y trayecto. Debe existir un solo registro."
                )
            )

        calificacion = calificaciones_existentes.first()        
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

            except (ValueError, TypeError, InvalidOperation):
                return respuesta(
                    "error",
                    "Nota inválida",
                    (
                        f"La nota de la unidad "
                        f"{numero_unidad} del estudiante "
                        f"{estudiante_id} no es válida."
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
                        f"La nota de la unidad "
                        f"{numero_unidad} del estudiante "
                        f"{estudiante_id} debe estar entre 0 y 20."
                    )
                )

            unidad = unidades[numero_unidad - 1]

            try:
                detalle = (
                    DetalleCalificacionesUnidad.objects
                    .select_for_update()
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

            if detalle.congelada and nota_anterior != nota_unidad:
                return respuesta(
                    "warning",
                    "Unidad congelada",
                    (
                        f"La unidad {numero_unidad} del estudiante "
                        f"{estudiante_id} se encuentra congelada "
                        "y no puede ser modificada."
                    )
                )

            if nota_anterior != nota_unidad:

                cambios_unidades.append({
                    "detalle": detalle,
                    "nota_anterior": nota_anterior,
                    "nota_nueva": nota_unidad
                })


                detalle.nota_unidad = nota_unidad
                detalle.modificado_por = usuario
                detalle.fecha_modificacion = timezone.now()
                detalle.perfil_modificacion = perfil
                detalle.save(
                    update_fields=[
                        "nota_unidad",
                        "modificado_por",
                        "fecha_modificacion",
                        "perfil_modificacion"
                    ]
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
            or bool(cambios_unidades)
        )

        if hubo_cambio:

            calificacion.asistencia = asistencia
            calificacion.promedio_tramo = promedio
            calificacion.condicion = condicion
            calificacion.modificado_por = usuario
            calificacion.fecha_modificacion = timezone.now()
            calificacion.perfil_modificacion = perfil
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

            cambios_historial.append({
                "estudiante": estudiante,
                "calificacion": calificacion,
                "cambios_unidades": cambios_unidades,
                "asistencia_anterior": asistencia_anterior,
                "asistencia_nueva": asistencia,
                "promedio_anterior": promedio_anterior,
                "promedio_nuevo": promedio
            })

    if cambios_historial:

        for cambio in cambios_historial:

            calificacion = cambio["calificacion"]

            historial = (
                HistorialModificacionNotas.objects.create(
                    docente_asignado=docente_asignado,
                    periodo_academico=periodo_materia.periodo,
                    trayecto=trayecto_obj,
                    calificacion=calificacion,
                    usuario_modifica=usuario,
                    perfil_modificacion=perfil,
                    fecha_modificacion=timezone.now(),
                    motivo=(
                        motivo
                        or "Modificación de notas académicas."
                    ),
                    tipo_modificacion="MODIFICACION"
                )
            )

            detalles_historial = []

            asistencia_cambio = (
                cambio["asistencia_anterior"]
                != cambio["asistencia_nueva"]
            )

            for unidad in cambio["cambios_unidades"]:

                detalles_historial.append(
                    HistorialDetalleNota(
                        historial=historial,
                        estudiante=cambio["estudiante"],
                        detalle_calificacion_unidad=unidad["detalle"],
                        nota_anterior=unidad["nota_anterior"],
                        nota_nueva=unidad["nota_nueva"],
                        asistencia_anterior=(
                            cambio["asistencia_anterior"]
                            if asistencia_cambio
                            else None
                        ),
                        asistencia_nueva=(
                            cambio["asistencia_nueva"]
                            if asistencia_cambio
                            else None
                        ),
                        promedio_anterior=(
                            cambio["promedio_anterior"]
                        ),
                        promedio_nuevo=(
                            cambio["promedio_nuevo"]
                        )
                    )
                )

            if (
                asistencia_cambio
                and not cambio["cambios_unidades"]
            ):
                detalles_historial.append(
                    HistorialDetalleNota(
                        historial=historial,
                        estudiante=cambio["estudiante"],
                        detalle_calificacion_unidad=None,
                        nota_anterior=None,
                        nota_nueva=None,
                        asistencia_anterior=(
                            cambio["asistencia_anterior"]
                        ),
                        asistencia_nueva=(
                            cambio["asistencia_nueva"]
                        ),
                        promedio_anterior=(
                            cambio["promedio_anterior"]
                        ),
                        promedio_nuevo=(
                            cambio["promedio_nuevo"]
                        )
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

