from django.shortcuts import render
from django.http import JsonResponse
from django.db import transaction
from decimal import Decimal, ROUND_DOWN, InvalidOperation
from django.utils import timezone
from django.db.models.functions import TruncDate
from datetime import timedelta
from datetime import datetime

from inicio_sesion.models import Usuario, CalendarioPeriodo, MateriaAsignada, ControlEstudio, PeriodoAcademicoMateria, Usuario, Pnf, PNFNucleo, Estudiante, EstatusEstudiante, CalendarioAcademico, Nucleos, PeriodoAcademico, Materia, Docente, DocenteAsignadoMateria

from notas_academicas.models import PlanificacionAcademica, DetallePlanificacion, HistorialTrayectoEstudiante, HistorialDetalleNota, HistorialModificacionNotas, DetalleEvaluacion, PromedioFinal, Calificaciones, DetalleCalificacionesUnidad

# Registrar Plan de Actividades

def perf_asig(request):
    cedula = request.session.get("cedula_usuario")

    tiene_docente = Docente.objects.filter(
        usuario__cedula_identidad=cedula,
        activo=True
    ).exists()

    tiene_control_estudio = ControlEstudio.objects.filter(
        usuario__cedula_identidad=cedula,
        activo=True
    ).exists()

    return JsonResponse({
        "estado": "exito",
        "docente": tiene_docente,
        "control_estudio": tiene_control_estudio
    })

def nucl_asig_doc(request):
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
                "descripcion": "El usuario no tiene núcleos asignados como Encargado de Control de Estudio."
            })

        return JsonResponse({
            "estado": "fallo",
            "icon": "info",
            "title": "Sin núcleos asignados",
            "descripcion": "El usuario no tiene núcleos asignados como Docente."
        })

    return JsonResponse({
        "estado": "exito",
        "datos": datos
    })

def pnfs_asig_doc(request):
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

    # CONTROL DE ESTUDIO
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

    # DOCENTE
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

    # SIN PNF
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

def doc_selec(request):
    nucleo_asignado = request.POST.get("nucleo_asignado")
    pnf_seleccionado = request.POST.get("pnf_seleccionado")
    cedula = request.session.get("cedula_usuario")

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
        .select_related("usuario")
        .distinct()
    )

    if not docentes.exists():
        return JsonResponse({
            "estado": "vacio",
            "datos": [],
            "title": "No hay docentes disponibles",
            "descripcion": (
                "No existen docentes activos con materias "
                "asignadas activamente para el núcleo y PNF seleccionado."
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
   
def mat_asig_doc(request):
    id_nucleo = request.POST.get("id_nucleo")
    id_pnf = request.POST.get("id_pnf")
    perfil = request.POST.get("perfil")
    ci_docente = request.POST.get("docente")
    cedula = request.session.get("cedula_usuario")

    if not cedula:
        return JsonResponse({
            "estado": "fallo",
            "icon": "warning",
            "title": "Sesión no válida",
            "descripcion": "No se encontró un usuario autenticado."
        })

    if not id_nucleo or not id_pnf:
        return JsonResponse({
            "estado": "fallo",
            "icon": "warning",
            "title": "Datos incompletos",
            "descripcion": (
                "No se recibió el núcleo o PNF seleccionado."
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
            .select_related(
                "usuario",
                "nucleo",
                "pnf"
            )
            .first()
        )

        if not docente:
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Docente no disponible",
                "descripcion": (
                    "El perfil de docente no está activo "
                    "para el núcleo y PNF seleccionado."
                )
            })

    elif perfil == "CONTROL_ESTUDIO":

        control = (
            ControlEstudio.objects
            .filter(
                usuario__cedula_identidad=cedula,
                nucleo_id=id_nucleo,
                activo=True
            )
            .first()
        )

        if not control:
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Perfil no disponible",
                "descripcion": (
                    "El perfil de Control de Estudio no está "
                    "activo para el núcleo seleccionado."
                )
            })

        if not ci_docente or ci_docente in (
            "null",
            "undefined",
            ""
        ):
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Docente no seleccionado",
                "descripcion": (
                    "Debe seleccionar un docente para "
                    "consultar sus materias asignadas."
                )
            })

        docente = (
            Docente.objects
            .filter(
                usuario__cedula_identidad=ci_docente,
                nucleo_id=id_nucleo,
                pnf_id=id_pnf,
                activo=True
            )
            .select_related(
                "usuario",
                "nucleo",
                "pnf"
            )
            .first()
        )

        if not docente:
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Docente no disponible",
                "descripcion": (
                    "El docente seleccionado no está activo "
                    "o no pertenece al núcleo y PNF seleccionado."
                )
            })

    else:

        return JsonResponse({
            "estado": "fallo",
            "icon": "warning",
            "title": "Perfil no válido",
            "descripcion": "El perfil seleccionado no es válido."
        })

    fecha_actual = timezone.localdate()

    calendarios_vigentes = list(
        CalendarioPeriodo.objects
        .filter(
            calendario__tipo="PERIODO",
            calendario__activo=True,
            calendario__fecha_inicio__lte=fecha_actual,
            calendario__fecha_final__gte=fecha_actual
        )
        .select_related(
            "periodo",
            "calendario"
        )
        .order_by(
            "calendario__fecha_inicio",
            "periodo_id"
        )
    )

    if not calendarios_vigentes:
        return JsonResponse({
            "estado": "fallo",
            "icon": "info",
            "title": "Período académico no disponible",
            "descripcion": (
                "No existe un período académico vigente "
                "para registrar la planificación."
            )
        })

    calendario_por_periodo = {
        cp.periodo_id: {
            "id_periodo": cp.periodo_id,
            "nombre": cp.periodo.nombre,
            "fecha_inicio": cp.calendario.fecha_inicio,
            "fecha_final": cp.calendario.fecha_final,
        }
        for cp in calendarios_vigentes
    }

    asignaciones = list(
        DocenteAsignadoMateria.objects
        .filter(
            docente=docente,
            activo=True,
            materia_asignada__activo=True,
            materia_asignada__materia__activa=True
        )
        .select_related(
            "materia_asignada__materia"
        )
        .prefetch_related(
            "materia_asignada__materia__periodos_academicos__periodo"
        )
    )

    if not asignaciones:
        return JsonResponse({
            "estado": "fallo",
            "icon": "info",
            "title": "Sin materias asignadas",
            "descripcion": (
                "El docente no tiene materias asignadas "
                "activas para el núcleo y PNF seleccionado."
            )
        })

    materias = []
    periodos_academicos = {}
    claves = set()

    for asignacion in asignaciones:

        materia_asignada = asignacion.materia_asignada
        materia = materia_asignada.materia

        for periodo_materia in (
            materia.periodos_academicos
            .select_related("periodo")
            .all()
        ):

            periodo_id = periodo_materia.periodo_id

            if periodo_id not in calendario_por_periodo:
                continue

            periodo_info = calendario_por_periodo[periodo_id]

            existe_planificacion = (
                PlanificacionAcademica.objects
                .filter(
                    materia_asignacion=materia_asignada,
                    periodo_academico_id=periodo_id,
                    fecha_creacion__year=fecha_actual.year,
                    activo=True,
                    estado_aceptacion__in=[
                        "ENVIADO",
                        "ACEPTADA"
                    ]
                )
                .exists()
            )

            if existe_planificacion:
                continue

            periodos_academicos[periodo_id] = periodo_info

            clave = (
                materia_asignada.id_materia_asignada,
                periodo_id
            )

            if clave in claves:
                continue

            claves.add(clave)

            materias.append({
                "id_materia_asignada":
                    materia_asignada.id_materia_asignada,

                "id_materia":
                    materia.id_materia,

                "nombre":
                    materia.nombre,

                "codigo":
                    materia.codigo,

                "rol":
                    asignacion.rol,

                "id_periodo":
                    periodo_id
            })

    if not materias:
        return JsonResponse({
            "estado": "fallo",
            "icon": "info",
            "title": "No hay materias disponibles",
            "descripcion": (
                "Las materias asignadas al docente no tienen "
                "un período académico vigente que requiera "
                "registrar planificación."
            ),
            "datos": [],
            "periodos_academicos": []
        })

    return JsonResponse({
        "estado": "exito",
        "datos": materias,
        "periodos_academicos": list(
            periodos_academicos.values()
        )
    })

def datos_unid_reg(request):
    id_asignacion = request.POST.get("id_asignacion")
    id_periodo_academico = request.POST.get("id_periodo_academico")

    if not id_asignacion or not id_periodo_academico:
        return JsonResponse({
            "estado": "fallo",
            "existe_plan": False,
            "cantidad": 0,
            "evaluaciones": [],
            "puede_enviar": False,
            "descripcion": "Debe indicar la materia y el período académico."
        })

    # AÑO ACTUAL
    anio_actual = timezone.localdate().year

    # VERIFICAR QUE EL PERÍODO PERTENEZCA AL AÑO ACTUAL
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

    # EL PERÍODO NO PERTENECE AL AÑO ACTUAL
    if not periodo_actual:
        return JsonResponse({
            "estado": "exito",
            "existe_plan": False,
            "id_plan": None,
            "id_periodo_academico": id_periodo_academico,
            "periodo": None,
            "cantidad": 0,
            "estado_aceptacion": None,
            "evaluaciones": [],
            "puede_enviar": False
        })

    plan = (
        PlanificacionAcademica.objects
        .filter(
            materia_asignacion_id=id_asignacion,
            periodo_academico_id=id_periodo_academico,
            fecha_creacion__year=anio_actual,
            activo=True
        )
        .select_related("periodo_academico")
        .prefetch_related(
            "detalles__evaluaciones"
        )
        .first()
    )

    if not plan:
        return JsonResponse({
            "estado": "exito",
            "existe_plan": False,
            "id_plan": None,
            "id_periodo_academico": id_periodo_academico,
            "periodo": periodo_actual.periodo.nombre,
            "cantidad": 0,
            "estado_aceptacion": None,
            "evaluaciones": [],
            "puede_enviar": False
        })

    cantidad = plan.detalles.count()

    puede_enviar = (
        4 <= cantidad <= 6
        and plan.estado_aceptacion in [
            "BORRADOR",
            "DENEGADA"
        ]
    )

    evaluaciones = []

    for detalle in plan.detalles.all():

        for evaluacion in detalle.evaluaciones.all():

            evaluaciones.append({
                "id_detalle": detalle.id_detalle,
                "titulo_unidad": detalle.titulo_unidad,
                "id_evaluacion": evaluacion.id_evaluacion,
                "metodo_evaluacion": evaluacion.metodo_evaluacion,
                "porcentaje_evaluacion": float(
                    evaluacion.porcentaje_evaluacion
                ),
                "fecha_evaluacion": evaluacion.fecha_evaluacion.strftime(
                    "%Y-%m-%d"
                )
            })

    return JsonResponse({
        "estado": "exito",
        "existe_plan": True,
        "id_plan": plan.id_planificacion,
        "id_periodo_academico": plan.periodo_academico_id,
        "periodo": plan.periodo_academico.nombre,
        "cantidad": cantidad,
        "estado_aceptacion": plan.estado_aceptacion,
        "evaluaciones": evaluaciones,
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
                detalle_plan__plan_academico__materia_asignacion_id=id_materia_asignada,
                detalle_plan__plan_academico__periodo_academico_id=id_periodo,
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
        return render(request, "Planificacion_Academica/registrar_planificacion.html")
    
    nucleo_asignado = request.POST.get("nucleo_asignado")
    pnf_asignado = request.POST.get("pnfs_asignado")
    docente_seleccionado = request.POST.get("seleccion_docente")
    materia_asignacion = request.POST.get("asignacion_materia")
    id_periodo = request.POST.get("id_periodo")

    titulo_unidad = request.POST.get("titulo_unidad", "").strip()
    contenido_unidad = request.POST.get("contenido_unidad", "").strip()

    def error(title, descripcion, icon="warning"):
        return JsonResponse({
            "estado": "fallo",
            "icon": icon,
            "title": title,
            "descripcion": descripcion
        })

    # DATOS OBLIGATORIOS
    datos_obligatorios = [
        (nucleo_asignado, "Núcleo", "Por favor, selecciona un núcleo."),
        (pnf_asignado, "P.N.F.", "Por favor, selecciona un P.N.F."),
        (materia_asignacion, "Materia Asignada", "Por favor, selecciona una materia."),
        (id_periodo, "Período Académico", "Por favor, selecciona un período académico."),
        (titulo_unidad, "Título de la Unidad", "Por favor, ingresa el título de la unidad."),
        (contenido_unidad, "Contenido de la Unidad", "Por favor, ingresa el contenido de la unidad.")
    ]
    for valor, titulo, mensaje in datos_obligatorios:
        if not valor:
            return error(titulo, mensaje)

    # SESIÓN
    cedula = request.session.get("cedula_usuario")

    if not cedula:
        return error(
            "Sesión no válida",
            "No se encontró el usuario autenticado en la sesión."
        )

    # PERÍODO ACADÉMICO
    try:
        periodo = PeriodoAcademico.objects.get(pk=id_periodo)
    except PeriodoAcademico.DoesNotExist:
        return error(
            "Período Académico",
            "El período académico seleccionado no se encuentra registrado.",
            "error"
        )

    # DOCENTE
    try:
        # SI SE SELECCIONÓ UN DOCENTE DESDE EL SELECT
        if docente_seleccionado:
            docente = (
                Docente.objects
                .select_related(
                    "usuario",
                    "nucleo",
                    "pnf"
                )
                .get(
                    usuario__cedula_identidad=docente_seleccionado,
                    nucleo_id=nucleo_asignado,
                    pnf_id=pnf_asignado,
                    activo=True
                )
            )
        # SI NO SE SELECCIONÓ DOCENTE
        # SE UTILIZA EL DOCENTE DE LA SESIÓN
        else:
            docente = (
                Docente.objects
                .select_related(
                    "usuario",
                    "nucleo",
                    "pnf"
                )
                .get(
                    usuario__cedula_identidad=cedula,
                    nucleo_id=nucleo_asignado,
                    pnf_id=pnf_asignado,
                    activo=True
                )
            )

    except Docente.DoesNotExist:
        return error(
            "Docente no encontrado",
            "El docente seleccionado no está asociado "
            "al núcleo y PNF indicados o se encuentra inactivo.",
            "error"
        )

    # AÑO ACTUAL
    fecha_actual = timezone.localdate()
    anio_actual = fecha_actual.year

    # CALENDARIO DEL PERÍODO
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
        return error("Calendario Académico",
            (
                f"El período '{periodo.nombre}' "
                f"no tiene un calendario registrado "
                f"para el año {anio_actual}."
            )
        )

    fecha_inicio = calendario.calendario.fecha_inicio
    fecha_final = calendario.calendario.fecha_final

    # VALIDAR QUE EL PERÍODO ESTÉ ACTIVO
    if fecha_actual < fecha_inicio:
        return error("Período no iniciado",
            (
                f"El período '{periodo.nombre}' inicia el "
                f"{fecha_inicio.strftime('%d/%m/%Y')}."
            )
        )

    if fecha_actual > fecha_inicio + timedelta(days=4):
        return error("Registro cerrado",
            (
                f"El registro de '{periodo.nombre}' "
                f"solo está disponible durante los primeros "
                f"5 días del período."
            )
        )

    # MATERIA ASIGNADA
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
        return error("Materia Asignada",
            "La materia no se encuentra registrada o está inactiva.",
            "error"
        )

    # VALIDAR PNF DE LA MATERIA
    if asignacion.materia.id_pnf_id != docente.pnf_id:
        return error(
            "Materia no válida",
            "La materia seleccionada no pertenece al PNF del docente."
        )

    # VALIDAR NÚCLEO
    if docente.nucleo_id != int(nucleo_asignado):
        return error(
            "Núcleo no válido",
            "El docente no está asociado al núcleo seleccionado."
        )

    # VALIDAR PNF
    if docente.pnf_id != int(pnf_asignado):
        return error(
            "P.N.F. no válido",
            "El docente no está asociado al P.N.F. seleccionado."
        )

    # VALIDAR MATERIA - PERÍODO
    materia_periodo = (
        PeriodoAcademicoMateria.objects
        .filter(
            materia=asignacion.materia,
            periodo=periodo
        )
        .exists()
    )

    if not materia_periodo:
        return error(
            "Período no válido",
            (
                f"La materia '{asignacion.materia.nombre}' "
                f"no está asociada al período '{periodo.nombre}'."
            )
        )

    # FECHA DE LAS EVALUACIONES
    try:
        cantidad_evaluaciones = int(
            request.POST.get(
                "cantidad_evaluaciones",
                0
            )
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

    # VALIDAR EVALUACIONES
    for i in range(1, cantidad_evaluaciones + 1):
        metodo = request.POST.get(f"metodo_evaluacion_{i}", "").strip()
        fecha = request.POST.get(f"fecha_evaluacion_{i}", "").strip()
        porcentaje = request.POST.get(f"porcentaje_evaluacion_{i}", "").strip()

        if not metodo:
            return error("Método de Evaluación",
                (
                    f"El método de evaluación {i} "
                    f"no puede estar vacío."
                )
            )

        if not fecha:
            return error("Fecha de Evaluación",
                (
                    f"La fecha de evaluación {i} "
                    f"no puede estar vacía."
                )
            )

        try:
            fecha_obj = datetime.strptime(fecha, "%Y-%m-%d").date()
        except ValueError:
            return error("Fecha de Evaluación",
                (
                    f"La fecha de evaluación {i} "
                    f"no tiene un formato válido."
                )
            )

        if (fecha_obj < fecha_inicio or fecha_obj > fecha_final):
            return error("Fecha de Evaluación",
                (
                    f"La fecha de la evaluación {i} "
                    f"debe estar dentro del período académico."
                )
            )

        if not porcentaje:
            return error("Porcentaje de Evaluación",
                (
                    f"Debe ingresar el porcentaje "
                    f"de la evaluación {i}."
                )
            )

        try:
            porcentaje_decimal = Decimal(porcentaje)
        except (InvalidOperation, ValueError):
            return error(
                "Porcentaje de Evaluación",
                (
                    f"El porcentaje de la evaluación {i} "
                    f"no es válido."
                )
            )

        if porcentaje_decimal <= 0:
            return error(
                "Porcentaje de Evaluación",
                (
                    f"La evaluación {i} debe tener "
                    f"un porcentaje mayor que 0%."
                )
            )

        if porcentaje_decimal > 25:
            return error(
                "Porcentaje de Evaluación",
                (
                    f"El porcentaje de la evaluación {i} "
                    f"no puede superar el 25%."
                )
            )

        total_porcentaje += porcentaje_decimal

        evaluaciones.append({
            "metodo_evaluacion": metodo,
            "fecha_evaluacion": fecha_obj,
            "porcentaje_evaluacion": porcentaje_decimal
        })

    # TOTAL DE EVALUACIONES
    if total_porcentaje != Decimal("25.00"):
        return error("Porcentaje de Evaluaciones",
            (
                "La suma de los porcentajes debe ser "
                f"exactamente 25%. Actualmente suma "
                f"{total_porcentaje}%."
            )
        )

    # PLANIFICACIÓN
    PERIODOS_INICIALES = {
        "Inicial Trimestre",
        "Inicial Semestre"
    }

    # FILTRO BASE
    filtros_planificacion = {
        "pnf": docente.pnf,
        "nucleo": docente.nucleo,
        "materia_asignacion": asignacion,
        "fecha_creacion__year": anio_actual,
        "activo": True
    }

    # PERÍODOS INICIALES
    if periodo.nombre in PERIODOS_INICIALES:

        filtros_planificacion[
            "periodo_academico__nombre__in"
        ] = PERIODOS_INICIALES

    # PERÍODOS NORMALES
    else:
        filtros_planificacion[
            "periodo_academico"
        ] = periodo

    planificacion = (
        PlanificacionAcademica.objects
        .select_for_update()
        .filter(**filtros_planificacion)
        .first()
    )

    # VALIDAR ESTADO
    if planificacion:
        if planificacion.estado_aceptacion == "ACEPTADA":
            return error(
                "Planificación aceptada",
                (
                    "La planificación ya fue aceptada "
                    "y no puede modificarse."
                )
            )

        if planificacion.estado_aceptacion == "ENVIADO":
            return error(
                "Planificación enviada",
                (
                    "La planificación ya fue enviada "
                    "al Coordinador."
                )
            )

        if planificacion.estado_aceptacion not in {"BORRADOR", "DENEGADA"}:
            return error(
                "Planificación no disponible",
                "La planificación no puede modificarse."
            )

    # CREAR PLANIFICACIÓN
    if not planificacion:
        planificacion = (
            PlanificacionAcademica.objects.create(
                pnf=docente.pnf,
                nucleo=docente.nucleo,
                materia_asignacion=asignacion,
                periodo_academico=periodo,
                activo=True,
                estado_aceptacion="BORRADOR"
            )
        )

    elif planificacion.estado_aceptacion == "DENEGADA":
        planificacion.estado_aceptacion = "BORRADOR"
        planificacion.save(
            update_fields=[
                "estado_aceptacion"
            ]
        )

    # CONTAR UNIDADES
    filtros_unidades = {
        "plan_academico__pnf": docente.pnf,
        "plan_academico__nucleo": docente.nucleo,
        "plan_academico__materia_asignacion": asignacion,
        "plan_academico__fecha_creacion__year": anio_actual,
        "plan_academico__activo": True
    }

    if periodo.nombre in PERIODOS_INICIALES:
        filtros_unidades[
            "plan_academico__periodo_academico__nombre__in"
        ] = PERIODOS_INICIALES

    else:
        filtros_unidades[
            "plan_academico__periodo_academico"
        ] = periodo


    cantidad = (
        DetallePlanificacion.objects
        .filter(**filtros_unidades)
        .count()
    )

    # MÁXIMO 6 UNIDADES
    if cantidad >= 6:
        return error(
            "Límite de unidades",
            (
                f"La materia '{asignacion.materia.nombre}' "
                f"ya tiene registradas 6 unidades "
                f"para el año {anio_actual}."
            )
        )

    usuario = Usuario.objects.get(cedula_identidad=cedula)

    # CREAR UNIDAD
    detalle = (
        DetallePlanificacion.objects.create(
            plan_academico=planificacion,
            titulo_unidad=titulo_unidad,
            contenido_unidad=contenido_unidad,
            ponderacion=Decimal("0.00"),
            registrado_por=usuario,
            fecha_registro=timezone.now()
        )
    )

    # ACTUALIZAR PONDERACIONES
    unidades = list(
        planificacion.detalles.order_by("pk")
    )

    cantidad = len(unidades)

    base = (
        Decimal("100.00") /
        Decimal(cantidad)
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
            update_fields=[
                "ponderacion"
            ]
        )

    # CREAR EVALUACIONES
    for evaluacion in evaluaciones:
        DetalleEvaluacion.objects.create(
            detalle_plan=detalle,
            metodo_evaluacion=evaluacion[
                "metodo_evaluacion"
            ],
            porcentaje_evaluacion=evaluacion[
                "porcentaje_evaluacion"
            ],
            fecha_evaluacion=evaluacion[
                "fecha_evaluacion"
            ]
        )

    return JsonResponse({
        "estado": "exito",
        "icon": "success",
        "title": "Planificación registrada",
        "descripcion": (
            f"Se registró correctamente la unidad "
            f"de '{asignacion.materia.nombre}'."
        )
    })

# Visualizar Plan de Actividades

def vis_plan_est(request):
    return render(request, "Planificacion_Academica/visualizar_plan_academico.html")

def todos_pnfs_asig_doc(request):
    cedula = request.session.get("cedula_usuario")
    nucleo = request.POST.get("nucleo_asignado", "").strip()
    perfil = request.POST.get("perfil", "").strip()

    if not cedula:
        return JsonResponse({
            "estado": "error",
            "datos": [],
            "descripcion": "No se encontró el usuario en la sesión."
        })

    if perfil == "DOCENTE":

        pnfs = Pnf.objects.filter(
            id_pnf__in=Docente.objects.filter(
                usuario__cedula_identidad=cedula,
                activo=True,
                materias_asignadas__activo=True,
                materias_asignadas__materia_asignada__activo=True
            ).values_list(
                "pnf_id",
                flat=True
            )
        ).values(
            "id_pnf",
            "pnf"
        ).distinct().order_by(
            "pnf"
        )

    elif perfil == "CONTROL_ESTUDIO":

        if not nucleo:
            return JsonResponse({
                "estado": "exito",
                "datos": []
            })

        control_estudio = ControlEstudio.objects.filter(
            usuario__cedula_identidad=cedula,
            nucleo_id=nucleo,
            activo=True
        ).first()

        if not control_estudio:
            return JsonResponse({
                "estado": "error",
                "datos": [],
                "descripcion": "No se encontró un encargado de Control de Estudio activo para este núcleo."
            })

        pnfs = Pnf.objects.filter(
            id_pnf__in=Docente.objects.filter(
                nucleo_id=control_estudio.nucleo_id,
                activo=True
            ).values_list(
                "pnf_id",
                flat=True
            )
        ).values(
            "id_pnf",
            "pnf"
        ).distinct().order_by(
            "pnf"
        )

    else:

        return JsonResponse({
            "estado": "error",
            "datos": [],
            "descripcion": "Perfil no válido."
        })

    return JsonResponse({
        "estado": "exito",
        "datos": list(pnfs)
    })

def doc_reg(request):
    pnf = request.POST.get("id_pnf", "").strip()
    cedula = request.session.get("cedula_usuario")

    if not cedula:
        return JsonResponse({
            "estado": "fallo",
            "title": "Sesión no válida",
            "descripcion": "No se encontró el usuario en la sesión.",
            "icon": "warning"
        })

    control_estudio = ControlEstudio.objects.filter(
        usuario__cedula_identidad=cedula,
        activo=True
    ).first()

    if not control_estudio:
        return JsonResponse({
            "estado": "fallo",
            "title": "Acceso no autorizado",
            "descripcion": "No se encontró un encargado de Control de Estudio activo.",
            "icon": "warning"
        })

    docentes = Docente.objects.filter(
        nucleo=control_estudio.nucleo,
        activo=True,
        materias_asignadas__activo=True,
        materias_asignadas__materia_asignada__activo=True
    ).select_related(
        "usuario",
        "pnf"
    ).distinct()

    if pnf:
        docentes = docentes.filter(
            pnf_id=pnf
        )

    docentes = docentes.order_by(
        "usuario__apellidos",
        "usuario__nombres"
    )

    datos = [
        {
            "id_docente": docente.id_docente,
            "cedula": docente.usuario.cedula_identidad,
            "nombres": docente.usuario.nombres,
            "apellidos": docente.usuario.apellidos,
            "id_pnf": docente.pnf.id_pnf,
            "pnf": docente.pnf.pnf,
        }
        for docente in docentes
    ]

    return JsonResponse({
        "estado": "exito",
        "docentes": datos
    })

def pl_reg(request):
    nucleo = request.POST.get("nucleo", "").strip()
    pnf = request.POST.get("pnf", "").strip()
    docente = request.POST.get("docente", "").strip()

    perfil = request.POST.get("perfil", "").strip()
    cedula = request.session.get("cedula_usuario")

    if not cedula:
        return JsonResponse({
            "estado": "fallo",
            "datos": [],
            "descripcion": "No se encontró el usuario en la sesión."
        })

    if not perfil:
        return JsonResponse({
            "estado": "fallo",
            "datos": [],
            "descripcion": "No se recibió el perfil."
        })

    # CONTROL DE ESTUDIO
    if perfil == "CONTROL_ESTUDIO":
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
                "datos": [],
                "descripcion": (
                    "No se encontró un encargado de "
                    "Control de Estudio activo."
                )
            })

        docentes = Docente.objects.filter(
            nucleo_id=control_estudio.nucleo_id,
            activo=True
        )

        if docente:
            docentes = docentes.filter(
                usuario__cedula_identidad=docente
            )

        if pnf:
            docentes = docentes.filter(
                pnf_id=pnf
            )

        nucleo_id = control_estudio.nucleo_id

    # DOCENTE
    elif perfil == "DOCENTE":
        docentes = Docente.objects.filter(
            usuario__cedula_identidad=cedula,
            activo=True
        )

        if not docentes.exists():
            return JsonResponse({
                "estado": "fallo",
                "datos": [],
                "descripcion": (
                    "No se encontró un Docente activo "
                    "asociado al usuario."
                )
            })

        if pnf:
            docentes = docentes.filter(
                pnf_id=pnf
            )

        nucleo_id = None

    else:
        return JsonResponse({
            "estado": "fallo",
            "datos": [],
            "descripcion": (
                "El perfil recibido no tiene permiso "
                "para consultar las planificaciones."
            )
        })

    # ASIGNACIONES ACTIVAS
    materias_docente = (
        DocenteAsignadoMateria.objects
        .filter(
            docente__in=docentes,
            activo=True,
            materia_asignada__activo=True
        )
        .values_list(
            "materia_asignada_id",
            flat=True
        )
        .distinct()
    )

    # PLANIFICACIONES
    planes = (
        PlanificacionAcademica.objects
        .filter(
            activo=True,
            materia_asignacion_id__in=materias_docente
        )
        .select_related(
            "materia_asignacion__materia",
            "nucleo",
            "pnf"
        )
        .prefetch_related(
            "detalles"
        )
        .order_by(
            "-fecha_creacion",
            "-id_planificacion"
        )
    )

    if nucleo_id:
        planes = planes.filter(
            nucleo_id=nucleo_id
        )

    if pnf:
        planes = planes.filter(
            pnf_id=pnf
        )

    datos = [
        {
            "id_plan": plan.id_planificacion,
            "materia": plan.materia_asignacion.materia.nombre,
            "nucleo": plan.nucleo.municipio,
            "pnf": plan.pnf.pnf,
            "observacion": plan.observacion,
            "estado_aceptacion": plan.estado_aceptacion,
            "estado_aceptacion_display": (
                plan.get_estado_aceptacion_display()
            ),
            "fecha_registro": (
                plan.fecha_creacion.strftime("%d/%m/%Y %H:%M:%S")
                if plan.fecha_creacion
                else None
            ),
            "cantidad_unidades": len(plan.detalles.all()),
        }
        for plan in planes
    ]

    return JsonResponse({
        "estado": "exito",
        "datos": datos
    })

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

        try:
            plan = PlanificacionAcademica.objects.get(id_planificacion=id_plan)
        except PlanificacionAcademica.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Error",
                "descripcion": "No se encuentra registrado el Plan de Actividades Académicas."
            })

        cedula = request.session.get("cedula_usuario")

        if not cedula:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Sesión no válida",
                "descripcion": "No se encontró el usuario autenticado."
            })

        try:
            usuario = Usuario.objects.get(cedula_identidad=cedula)
        except Usuario.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Usuario no encontrado",
                "descripcion": (
                    "El usuario de la sesión no se encuentra "
                    "registrado."
                )
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
                    detalle.modificado_por = usuario
                    detalle.fecha_modificado = timezone.now()
                    detalle.save(
                        update_fields=[
                            "titulo_unidad",
                            "contenido_unidad",
                            "modificado_por",
                            "fecha_modificado"
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
        