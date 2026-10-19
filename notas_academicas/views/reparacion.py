from django.shortcuts import render
from django.http import JsonResponse
from django.db import transaction
from django.db.models import F, Exists, OuterRef, Q, Prefetch, Count 
from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP, InvalidOperation
from django.utils import timezone
from django.db.models import Exists, OuterRef, Q

import json
from datetime import date, datetime

from inicio_sesion.models import MateriaAsignada, ControlEstudio, CalendarioPeriodo, TrayectoAcademico, PeriodoAcademico, Usuario, Pnf, PNFNucleo, Estudiante, EstatusEstudiante, CalendarioAcademico, Nucleos, PeriodoAcademicoMateria, Materia, Docente, DocenteAsignadoMateria

from notas_academicas.models import ModificacionReparacion, DetalleModificacionReparacion, EvaluacionReparacion, DetalleEvaluacionReparacion, PlanificacionAcademica, DetallePlanificacion, HistorialTrayectoEstudiante, HistorialDetalleNota, HistorialModificacionNotas, DetalleEvaluacion, PromedioFinal, Reparacion, Calificaciones, DetalleCalificacionesUnidad

# Evaluaciones Reparación

def nucl_not_rep(request):
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

    periodo_reparacion = CalendarioPeriodo.objects.filter(
        periodo__nombre="Reparación",
        calendario__tipo="PERIODO",
        calendario__activo=True,
        calendario__fecha_inicio__lte=fecha_actual,
        calendario__fecha_final__gte=fecha_actual
    ).exists()

    if not periodo_reparacion:
        return JsonResponse({
            "estado": "fallo",
            "icon": "warning",
            "title": "No se encuentra en el Periodo Académico",
            "descripcion": (
                "Actualmente no se encuentra vigente el período "
                "académico de Reparación para el registro o modificar."
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
            descripcion = (
                "El usuario no tiene núcleos asignados como "
                "Encargado de Control de Estudio."
            )
        else:
            descripcion = (
                "El usuario no tiene núcleos asignados como Docente."
            )

        return JsonResponse({
            "estado": "fallo",
            "icon": "info",
            "title": "Sin núcleos asignados",
            "descripcion": descripcion
        })

    return JsonResponse({
        "estado": "exito",
        "datos": datos
    })

def pnf_not_rep(request):
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
        control_estudio = ControlEstudio.objects.filter(
            usuario__cedula_identidad=cedula,
            nucleo_id=nucleo_asignado,
            activo=True
        ).first()

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

        pnfs = Pnf.objects.filter(
            pnfnucleo__id_nucleo=control_estudio.nucleo_id
        ).distinct().order_by("pnf")

    elif perfil == "DOCENTE":
        docentes = Docente.objects.filter(
            usuario__cedula_identidad=cedula,
            nucleo_id=nucleo_asignado,
            activo=True
        )

        pnf_ids = docentes.values_list(
            "pnf_id",
            flat=True
        ).distinct()

        pnfs = Pnf.objects.filter(
            id_pnf__in=pnf_ids,
            pnfnucleo__id_nucleo=nucleo_asignado
        ).distinct().order_by("pnf")

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

def doc_not_rep(request):
    nucleo_asignado = request.POST.get("nucleo_asignado", "").strip()
    pnf_seleccionado = request.POST.get("pnf_seleccionado", "").strip()
    cedula = request.session.get("cedula_usuario")

    if not cedula or not nucleo_asignado or not pnf_seleccionado:
        return JsonResponse({
            "estado": "fallo",
            "datos": [],
            "title": "Datos incompletos",
            "descripcion": (
                "Debe seleccionar el núcleo y el PNF "
                "para buscar docentes con materias arrastradas."
            ),
            "icon": "warning"
        })

    materias_reprobadas = PromedioFinal.objects.filter(
        materia_asignacion__activo=True,
        materia_asignacion__materia__activa=True,
        materia_asignacion__materia__id_pnf_id=pnf_seleccionado,
        estudiante__nucleo_id=nucleo_asignado,
        estudiante__pnf_id=pnf_seleccionado,
        estado__icontains="REPROBADO"
    )

    docentes = (
        Docente.objects.filter(
            nucleo_id=nucleo_asignado,
            pnf_id=pnf_seleccionado,
            activo=True,
            materias_asignadas__materia_asignada__in=(
                materias_reprobadas.values("materia_asignacion_id")
            ),
            materias_asignadas__activo=True,
            materias_asignadas__materia_asignada__activo=True
        )
        .exclude(
            usuario__cedula_identidad=cedula
        )
        .select_related("usuario")
        .distinct()
        .order_by("usuario__apellidos", "usuario__nombres")
    )

    if not docentes.exists():
        return JsonResponse({
            "estado": "fallo",
            "datos": [],
            "title": "No hay docentes con materias arrastradas",
            "descripcion": (
                "No existen docentes asignados a materias con "
                "estudiantes reprobados en el núcleo y PNF seleccionados."
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

# Registrar

def mat_rep_not(request):
    if request.method != "POST":
        return JsonResponse({
            "estado": "fallo",
            "title": "Método no permitido",
            "icon": "error",
            "descripcion": "La solicitud debe realizarse mediante POST."
        }, status=405)

    nucleo = request.POST.get("id_nucleo", "").strip()
    pnf = request.POST.get("id_pnf", "").strip()
    cedula_docente = request.POST.get("docente", "").strip()
    perfil = request.POST.get("perfil", "").strip()
    cedula = request.session.get("cedula_usuario")

    if not all([nucleo, pnf, cedula, perfil]):
        return JsonResponse({
            "estado": "fallo",
            "title": "Datos incompletos",
            "icon": "warning",
            "descripcion": "Faltan datos requeridos para realizar la consulta."
        })

    if perfil not in ("DOCENTE", "CONTROL_ESTUDIO"):
        return JsonResponse({
            "estado": "fallo",
            "title": "Perfil no válido",
            "icon": "warning",
            "descripcion": "El perfil seleccionado no es válido."
        })

    fecha_actual = timezone.localdate()
    año_actual = fecha_actual.year

    periodo_reparacion = PeriodoAcademico.objects.filter(
        nombre__iexact="Reparación"
    ).first()

    if not periodo_reparacion:
        return JsonResponse({
            "estado": "fallo",
            "title": "Período no configurado",
            "icon": "error",
            "descripcion": "No existe configurado el período académico Reparación."
        })

    calendarios_periodos = (
        CalendarioPeriodo.objects
        .filter(
            periodo=periodo_reparacion,
            calendario__tipo="PERIODO",
            calendario__activo=True,
            calendario__fecha_inicio__lte=fecha_actual,
            calendario__fecha_final__gte=fecha_actual,
            calendario__fecha_inicio__year=año_actual
        )
        .select_related("periodo", "calendario")
    )

    if not calendarios_periodos.exists():
        return JsonResponse({
            "estado": "exito",
            "materias": [],
            "periodos_actuales": [],
            "mensaje": "Actualmente no existe un período de Reparación habilitado."
        })

    # VALIDAR PERFIL Y OBTENER DOCENTE
    if perfil == "DOCENTE":
        docente_obj = Docente.objects.filter(
            usuario__cedula_identidad=cedula,
            nucleo_id=nucleo,
            pnf_id=pnf,
            activo=True
        ).first()

        if not docente_obj:
            return JsonResponse({
                "estado": "fallo",
                "title": "Docente no encontrado",
                "icon": "warning",
                "descripcion": (
                    "El docente no está asignado al núcleo y P.N.F. seleccionados."
                )
            })

    else:
        if not cedula_docente:
            return JsonResponse({
                "estado": "fallo",
                "title": "Docente no seleccionado",
                "icon": "warning",
                "descripcion": "Debe seleccionar un docente."
            })

        control_estudio = ControlEstudio.objects.filter(
            usuario__cedula_identidad=cedula,
            nucleo_id=nucleo,
            activo=True
        ).first()

        if not control_estudio:
            return JsonResponse({
                "estado": "fallo",
                "title": "Acceso denegado",
                "icon": "warning",
                "descripcion": (
                    "No tiene autorización de Control de Estudio "
                    "para el núcleo seleccionado."
                )
            })

        docente_obj = Docente.objects.filter(
            usuario__cedula_identidad=cedula_docente,
            nucleo_id=nucleo,
            pnf_id=pnf,
            activo=True
        ).first()

        if not docente_obj:
            return JsonResponse({
                "estado": "fallo",
                "title": "Docente no encontrado",
                "icon": "warning",
                "descripcion": (
                    "El docente seleccionado no está asignado "
                    "al núcleo y P.N.F. seleccionados."
                )
            })

    # OBTENER MATERIAS ASIGNADAS AL DOCENTE

    asignaciones_docentes = DocenteAsignadoMateria.objects.filter(
        docente=docente_obj,
        docente__nucleo_id=nucleo,
        docente__pnf_id=pnf,
        docente__activo=True,
        activo=True,
        materia_asignada__activo=True,
        materia_asignada__materia__activa=True,
        materia_asignada__materia__id_pnf_id=pnf
    )

    # BUSCAR PROMEDIOS FINALES REPROBADOS

    promedios_reprobados = PromedioFinal.objects.filter(
        materia_asignacion__activo=True,
        materia_asignacion__materia__activa=True,
        materia_asignacion__materia__id_pnf_id=pnf,
        estudiante__nucleo_id=nucleo,
        estudiante__pnf_id=pnf,
        estado="REPROBADO",
        promedio_final__gte=6.0,
        asistencia__gte=75.0
    )

    # OBTENER LAS ASIGNACIONES QUE TIENEN ESTUDIANTES REPROBADOS
    ids_materias_reprobadas = (
        promedios_reprobados
        .values_list("materia_asignacion_id", flat=True)
        .distinct()
    )

    materias_asignadas = (
        asignaciones_docentes
        .filter(
            materia_asignada_id__in=ids_materias_reprobadas
        )
        .exclude(
            materia_asignada__evaluaciones_reparacion_materia__pnf_id=pnf,
            materia_asignada__evaluaciones_reparacion_materia__nucleo_id=nucleo,
            materia_asignada__evaluaciones_reparacion_materia__fecha_creacion__year=año_actual,
            materia_asignada__evaluaciones_reparacion_materia__activo=True
        )
        .exclude(
            Q(materia_asignada__materia__tipo_materia__iexact="Electiva")
            | Q(
                materia_asignada__materia__id_trayecto__nombre__iexact="Trayecto Inicial"
            )
            | Q(
                materia_asignada__materia__nombre__icontains="proyecto socio tecnológico"
            )
            | Q(
                materia_asignada__materia__nombre__icontains="proyecto sociotecnologico"
            )
            | Q(
                materia_asignada__materia__nombre__icontains="proyecto sociointegrador"
            )
        )
        .select_related(
            "materia_asignada",
            "materia_asignada__materia",
            "materia_asignada__materia__id_trayecto"
        )
        .distinct()
        .order_by("materia_asignada__materia__nombre")
    )
    
    # PREPARAR RESPUESTA

    materias = []

    for asignacion in materias_asignadas:
        materia_asignada = asignacion.materia_asignada
        materia = materia_asignada.materia

        materias.append({
            "id_materia_asignada": materia_asignada.id_materia_asignada,
            "id_materia": materia.id_materia,
            "nombre": materia.nombre,
            "id_trayecto": materia.id_trayecto_id,
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
        ],
        "mensaje": (
            "Consulta realizada correctamente."
            if materias
            else "No se encontraron materias asignadas con estudiantes reprobados "
                 "que cumplan las condiciones para Reparación."
        )
    })

def reg_eval_rep(request):
    if request.method != "POST":
        return render(request, "Reparacion/registrar_examen_reparacion.html")

    id_nucleo = request.POST.get("nucleo_asignado", "").strip()
    id_pnf = request.POST.get("pnf_asignado", "").strip()
    id_materia_asignada = request.POST.get("materia_asignada", "").strip()
    docente = request.POST.get("seleccion_docente", "")
    perfil = request.POST.get("perfil", "").strip()
    cedula = request.session.get("cedula_usuario")

    tipos_evaluacion = request.POST.getlist("tipo_evaluacion[]")
    porcentajes = request.POST.getlist("porcentaje[]")

    if not cedula:
        return JsonResponse({
            "estado": "fallo",
            "title": "Sesión no válida",
            "icon": "warning",
            "descripcion": "No se encontró un usuario autenticado."
        })

    if perfil not in ("DOCENTE", "CONTROL_ESTUDIO"):
        return JsonResponse({
            "estado": "fallo",
            "title": "Perfil no válido",
            "icon": "warning",
            "descripcion": "El perfil seleccionado no es válido."
        })

    controles = [
        (id_nucleo, "Núcleo", "Seleccione un núcleo."),
        (id_pnf, "P.N.F", "Seleccione un P.N.F."),
        (id_materia_asignada, "Materia", "Seleccione una materia asignada.")
    ]

    for valor, titulo, mensaje in controles:
        if not valor:
            return JsonResponse({
                "estado": "fallo",
                "title": titulo,
                "icon": "warning",
                "descripcion": mensaje
            })

    if not tipos_evaluacion or len(tipos_evaluacion) != len(porcentajes):
        return JsonResponse({
            "estado": "fallo",
            "title": "Evaluaciones incompletas",
            "icon": "warning",
            "descripcion": (
                "Debe indicar el tipo y porcentaje de cada evaluación."
            )
        })

    porcentajes_numericos = []

    for i, (tipo, porcentaje) in enumerate(
        zip(tipos_evaluacion, porcentajes),
        start=1
    ):
        tipo = tipo.strip()

        if not tipo:
            return JsonResponse({
                "estado": "fallo",
                "title": "Tipo de evaluación",
                "icon": "warning",
                "descripcion": (
                    f"Debe seleccionar el tipo de evaluación {i}."
                )
            })

        try:
            valor = int(porcentaje)
        except (ValueError, TypeError):
            return JsonResponse({
                "estado": "fallo",
                "title": "Porcentaje inválido",
                "icon": "error",
                "descripcion": (
                    "Los porcentajes deben ser números enteros válidos."
                )
            })

        if valor < 10 or valor > 100:
            return JsonResponse({
                "estado": "fallo",
                "title": "Porcentaje inválido",
                "icon": "warning",
                "descripcion": (
                    "Cada evaluación debe tener un porcentaje "
                    "entre 10% y 100%."
                )
            })

        porcentajes_numericos.append(valor)

    if sum(porcentajes_numericos) != 100:
        return JsonResponse({
            "estado": "fallo",
            "title": "Porcentajes incorrectos",
            "icon": "warning",
            "descripcion": (
                "La suma de los porcentajes debe ser exactamente 100%."
            )
        })

    fecha_actual = timezone.localdate()
    año_actual = fecha_actual.year

    periodo_reparacion = PeriodoAcademico.objects.filter(
        nombre__iexact="Reparación"
    ).first()

    if not periodo_reparacion:
        return JsonResponse({
            "estado": "fallo",
            "title": "Período no configurado",
            "icon": "error",
            "descripcion": (
                "No existe configurado el período académico Reparación."
            )
        })

    calendario_vigente = CalendarioPeriodo.objects.filter(
        periodo=periodo_reparacion,
        calendario__tipo="PERIODO",
        calendario__activo=True,
        calendario__fecha_inicio__lte=fecha_actual,
        calendario__fecha_final__gte=fecha_actual,
        calendario__fecha_inicio__year=año_actual
    ).exists()

    if not calendario_vigente:
        return JsonResponse({
            "estado": "fallo",
            "title": "Período no disponible",
            "icon": "warning",
            "descripcion": (
                "No existe un período de Reparación vigente "
                "para registrar evaluaciones."
            )
        })

    materia_asignada = MateriaAsignada.objects.filter(
        id_materia_asignada=id_materia_asignada,
        activo=True,
        materia__activa=True,
        materia__id_pnf_id=id_pnf
    ).first()

    if not materia_asignada:
        return JsonResponse({
            "estado": "fallo",
            "title": "Materia no válida",
            "icon": "warning",
            "descripcion": (
                "La materia seleccionada no está activa o no "
                "pertenece al P.N.F. indicado."
            )
        })

    if perfil == "DOCENTE":
        asignaciones_docentes = DocenteAsignadoMateria.objects.filter(
            materia_asignada=materia_asignada,
            docente__usuario__cedula_identidad=cedula,
            docente__nucleo_id=id_nucleo,
            docente__pnf_id=id_pnf,
            docente__activo=True,
            materia_asignada__activo=True,
            activo=True
        )

    else:
        if not docente:
            return JsonResponse({
                "estado": "fallo",
                "title": "Docente no seleccionado",
                "icon": "warning",
                "descripcion": (
                    "Debe seleccionar el docente responsable de la materia."
                )
            })

        control_estudio = ControlEstudio.objects.filter(
            usuario__cedula_identidad=cedula,
            nucleo_id=id_nucleo,
            activo=True
        ).exists()

        if not control_estudio:
            return JsonResponse({
                "estado": "fallo",
                "title": "Acceso denegado",
                "icon": "warning",
                "descripcion": (
                    "No tiene un perfil activo de Control de Estudio "
                    "asociado al núcleo seleccionado."
                )
            })

        asignaciones_docentes = DocenteAsignadoMateria.objects.filter(
            materia_asignada=materia_asignada,
            docente__id_docente=docente,
            docente__nucleo_id=id_nucleo,
            docente__pnf_id=id_pnf,
            docente__activo=True,
            materia_asignada__activo=True,
            activo=True
        )

    if not asignaciones_docentes.exists():
        return JsonResponse({
            "estado": "fallo",
            "title": "Asignación no válida",
            "icon": "warning",
            "descripcion": (
                "El docente seleccionado no tiene una asignación activa "
                "para esta materia en el núcleo y P.N.F. indicados."
            )
        })

    estudiante_reprobado = PromedioFinal.objects.filter(
        materia_asignacion=materia_asignada,
        estudiante__nucleo_id=id_nucleo,
        estudiante__pnf_id=id_pnf,
        fecha_promedio__year=año_actual,
        estado="REPROBADO",
        promedio_final__gte=6,
        asistencia__gte=75
    ).exists()

    if not estudiante_reprobado:
        return JsonResponse({
            "estado": "fallo",
            "title": "Materia no elegible",
            "icon": "info",
            "descripcion": (
                "La materia no tiene estudiantes que cumplan "
                "las condiciones establecidas para Reparación."
            )
        })

    registrados = EvaluacionReparacion.objects.filter(
        materia_asignacion=materia_asignada,
        fecha_creacion__year=año_actual,
        activo=True
    ).exists()

    if registrados:
        return JsonResponse({
            "estado": "fallo",
            "title": "Evaluación ya registrada",
            "icon": "info",
            "descripcion": (
                "Esta materia ya tiene evaluaciones de Reparación "
                "registradas para el año actual."
            )
        })

    try:
        with transaction.atomic():
            evaluacion = EvaluacionReparacion.objects.create(
                pnf_id=id_pnf,
                nucleo_id=id_nucleo,
                materia_asignacion=materia_asignada
            )

            for tipo, porcentaje in zip(
                tipos_evaluacion,
                porcentajes_numericos
            ):
                DetalleEvaluacionReparacion.objects.create(
                    evaluacion_reparacion=evaluacion,
                    tipo_evaluacion=tipo.strip(),
                    porcentaje=porcentaje
                )

        return JsonResponse({
            "estado": "exito",
            "title": "¡Éxito!",
            "icon": "success",
            "descripcion": (
                "La evaluación de Reparación se registró exitosamente."
            )
        })

    except Exception:
        return JsonResponse({
            "estado": "fallo",
            "title": "Error en el servidor",
            "icon": "error",
            "descripcion": (
                "Ocurrió un error al registrar la evaluación "
                "de Reparación. Verifique los datos e intente nuevamente."
            )
        })

# Visualizar

def nucl_not_rep_vis(request):
    if request.method == "POST":
        cedula = request.session.get("cedula_usuario")
        perfil = request.POST.get("perfil", "").strip()

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
            nucleos_asignados = ControlEstudio.objects.filter(
                usuario__cedula_identidad=cedula,
                activo=True
            ).values_list("nucleo_id", flat=True)

            nucleos = Nucleos.objects.filter(
                id_nucleo__in=nucleos_asignados
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
                descripcion = (
                    "El usuario no tiene núcleos asignados como "
                    "Encargado de Control de Estudio."
                )
            else:
                descripcion = (
                    "El usuario no tiene núcleos asignados como Docente."
                )

            return JsonResponse({
                "estado": "fallo",
                "icon": "info",
                "title": "Sin núcleos asignados",
                "descripcion": descripcion
            })

        return JsonResponse({
            "estado": "exito",
            "datos": datos
        })

def pnf_not_rep_vis(request):
    if request.method == "POST":
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
            control_estudio = ControlEstudio.objects.filter(
                usuario__cedula_identidad=cedula,
                nucleo_id=nucleo_asignado,
                activo=True
            ).first()

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

            pnfs = Pnf.objects.filter(
                pnfnucleo__id_nucleo=control_estudio.nucleo_id
            ).distinct().order_by("pnf")

        elif perfil == "DOCENTE":
            docentes = Docente.objects.filter(
                usuario__cedula_identidad=cedula,
                nucleo_id=nucleo_asignado,
                activo=True
            )

            pnf_ids = docentes.values_list(
                "pnf_id",
                flat=True
            ).distinct()

            pnfs = Pnf.objects.filter(
                id_pnf__in=pnf_ids,
                pnfnucleo__id_nucleo=nucleo_asignado
            ).distinct().order_by("pnf")

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

def doc_not_rep_vis(request):
    if request.method == "POST":
        nucleo_asignado = request.POST.get(
            "nucleo_asignado", ""
        ).strip()

        pnf_seleccionado = request.POST.get(
            "pnf_seleccionado", ""
        ).strip()

        cedula = request.session.get("cedula_usuario")

        if not cedula or not nucleo_asignado or not pnf_seleccionado:
            return JsonResponse({
                "estado": "fallo",
                "datos": [],
                "title": "Datos incompletos",
                "descripcion": (
                    "Debe seleccionar el núcleo y el PNF "
                    "para buscar docentes con materias arrastradas."
                ),
                "icon": "warning"
            })

        materias_reprobadas = PromedioFinal.objects.filter(
            materia_asignacion__activo=True,
            materia_asignacion__materia__activa=True,
            materia_asignacion__materia__id_pnf_id=pnf_seleccionado,
            estudiante__nucleo_id=nucleo_asignado,
            estudiante__pnf_id=pnf_seleccionado,
            estado__icontains="REPROBADO"
        )

        docentes = (
            Docente.objects.filter(
                nucleo_id=nucleo_asignado,
                pnf_id=pnf_seleccionado,
                activo=True,
                materias_asignadas__materia_asignada__in=(
                    materias_reprobadas.values("materia_asignacion_id")
                ),
                materias_asignadas__activo=True,
                materias_asignadas__materia_asignada__activo=True
            )
            .exclude(
                usuario__cedula_identidad=cedula
            )
            .select_related("usuario")
            .distinct()
            .order_by(
                "usuario__apellidos",
                "usuario__nombres"
            )
        )

        if not docentes.exists():
            return JsonResponse({
                "estado": "fallo",
                "datos": [],
                "title": "No hay docentes con materias arrastradas",
                "descripcion": (
                    "No existen docentes asignados a materias con "
                    "estudiantes reprobados en el núcleo y PNF seleccionados."
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
        docente = Docente.objects.get(usuario__cedula_identidad=cedula, activo=True)
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
    return render(request, "Reparacion/visualizar_evaluaciones_reparar.html")

# Modificar

def mat_reg_eval(request):
    if request.method != "POST":
        return JsonResponse({
            "estado": "fallo",
            "title": "Error",
            "icon": "error",
            "descripcion": (
                "La solicitud debe realizarse mediante POST."
            )
        })

    pnf = request.POST.get("id_pnf", "").strip()
    nucleo = request.POST.get("id_nucleo", "").strip()
    cedula_docente = request.POST.get("docente", "").strip()
    perfil = request.POST.get("perfil", "").strip()
    cedula = request.session.get("cedula_usuario")

    if not all([pnf, nucleo, cedula, perfil]):
        return JsonResponse({
            "estado": "fallo",
            "title": "Datos incompletos",
            "icon": "warning",
            "descripcion": "Faltan datos requeridos."
        })

    if perfil not in ("DOCENTE", "CONTROL_ESTUDIO"):
        return JsonResponse({
            "estado": "fallo",
            "title": "Perfil no válido",
            "icon": "warning",
            "descripcion": "El perfil seleccionado no es válido."
        })

    fecha_actual = timezone.localdate()
    año_actual = fecha_actual.year

    # =====================================================
    # OBTENER PERÍODO ACADÉMICO REPARACIÓN
    # =====================================================

    periodo_reparacion = PeriodoAcademico.objects.filter(
        nombre__iexact="Reparación"
    ).first()

    if not periodo_reparacion:
        return JsonResponse({
            "estado": "exito",
            "materias": [],
            "periodos_actuales": [],
            "mensaje": (
                "No existe el período académico Reparación configurado."
            )
        })

    # =====================================================
    # VALIDAR CALENDARIO DE REPARACIÓN
    # =====================================================

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
            "mensaje": (
                "Actualmente no existe un período de Reparación habilitado."
            )
        })

    # =====================================================
    # PERFIL DOCENTE
    # Se identifica mediante la cédula de la sesión.
    # =====================================================

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
                "title": "Docente no encontrado",
                "icon": "warning",
                "descripcion": (
                    "El docente no está asignado al núcleo "
                    "y P.N.F. seleccionados."
                )
            })

    # =====================================================
    # PERFIL CONTROL DE ESTUDIO
    # La variable cedula_docente se utiliza exclusivamente
    # para buscar al docente seleccionado.
    # =====================================================

    else:
        if not cedula_docente:
            return JsonResponse({
                "estado": "fallo",
                "title": "Docente no seleccionado",
                "icon": "warning",
                "descripcion": "Debe seleccionar un docente."
            })

        control_estudio = (
            ControlEstudio.objects
            .filter(
                usuario__cedula_identidad=cedula,
                nucleo_id=nucleo,
                activo=True
            )
            .exists()
        )

        if not control_estudio:
            return JsonResponse({
                "estado": "fallo",
                "title": "Acceso denegado",
                "icon": "warning",
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
                "title": "Docente no encontrado",
                "icon": "warning",
                "descripcion": (
                    "El docente seleccionado no está asignado "
                    "al núcleo y P.N.F. seleccionados."
                )
            })

    # =====================================================
    # OBTENER MATERIAS ASIGNADAS AL DOCENTE
    # =====================================================

    materias_asignadas = (
        MateriaAsignada.objects
        .filter(
            activo=True,
            materia__activa=True,
            materia__id_pnf_id=pnf,
            docentes__docente=docente_obj,
            docentes__activo=True,
            evaluaciones_reparacion_materia__pnf_id=pnf,
            evaluaciones_reparacion_materia__nucleo_id=nucleo,
            evaluaciones_reparacion_materia__activo=True,
            evaluaciones_reparacion_materia__fecha_creacion__year=(
                año_actual
            )
        )
        .select_related(
            "materia",
            "materia__id_trayecto"
        )
        .distinct()
        .order_by("materia__nombre")
    )

    # =====================================================
    # PREPARAR LISTA DE MATERIAS CON EVALUACIONES
    # =====================================================

    lista_materias = []

    for materia_asignada in materias_asignadas:
        materia = materia_asignada.materia

        lista_materias.append({
            "id_materia_asignada": (
                materia_asignada.id_materia_asignada
            ),
            "id_materia": materia.id_materia,
            "nombre": materia.nombre,
            "id_trayecto": (
                materia.id_trayecto_id
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
    if request.method == "POST":
        pnf = request.POST.get("id_pnf", "").strip()
        nucleo = request.POST.get("id_nucleo", "").strip()
        materia_asignad = request.POST.get("id_materia_asignada", "").strip()
        cedula_docente = request.POST.get("docente", "").strip()
        perfil = request.POST.get("perfil", "").strip()
        cedula = request.session.get("cedula_usuario")

        if not all([pnf, nucleo, materia_asignad, cedula, perfil]):
            return JsonResponse({
                "estado": "fallo",
                "title": "Datos incompletos",
                "icon": "warning",
                "descripcion": (
                    "Faltan datos requeridos para consultar las evaluaciones."
                )
            })

        if perfil not in ("DOCENTE", "CONTROL_ESTUDIO"):
            return JsonResponse({
                "estado": "fallo",
                "title": "Perfil no válido",
                "icon": "warning",
                "descripcion": "El perfil seleccionado no es válido."
            })

        # PERFIL DOCENTE
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
                    "title": "Docente no encontrado",
                    "icon": "warning",
                    "descripcion": (
                        "El docente no está asignado al núcleo "
                        "y P.N.F. seleccionados."
                    )
                })

        # PERFIL CONTROL DE ESTUDIO
        else:
            if not cedula_docente:
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Docente no seleccionado",
                    "icon": "warning",
                    "descripcion": (
                        "Debe seleccionar el docente responsable "
                        "de la materia."
                    )
                })

            control_estudio = ControlEstudio.objects.filter(
                usuario__cedula_identidad=cedula,
                nucleo_id=nucleo,
                activo=True
            ).exists()

            if not control_estudio:
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Acceso denegado",
                    "icon": "warning",
                    "descripcion": (
                        "El usuario no tiene un perfil activo de "
                        "Control de Estudio en el núcleo seleccionado."
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
                    "title": "Docente no encontrado",
                    "icon": "warning",
                    "descripcion": (
                        "El docente seleccionado no está asignado "
                        "al núcleo y P.N.F. seleccionados."
                    )
                })

        # =====================================================
        # VALIDAR MATERIA Y ASIGNACIÓN DOCENTE
        # =====================================================

        materia_asignada = (
            MateriaAsignada.objects
            .filter(
                id_materia_asignada=materia_asignad,
                activo=True,
                materia__activa=True,
                materia__id_pnf_id=pnf,
                docentes__docente=docente_obj,
                docentes__activo=True
            )
            .first()
        )

        if not materia_asignada:
            return JsonResponse({
                "estado": "fallo",
                "title": "Materia no válida",
                "icon": "warning",
                "descripcion": (
                    "La materia no está asignada al docente seleccionado "
                    "en el núcleo y P.N.F. indicados."
                )
            })

        # =====================================================
        # CONSULTAR EVALUACIONES REGISTRADAS
        # =====================================================

        evaluaciones = (
            EvaluacionReparacion.objects
            .filter(
                pnf_id=pnf,
                nucleo_id=nucleo,
                materia_asignacion=materia_asignada,
                activo=True
            )
            .select_related(
                "materia_asignacion__materia"
            )
            .prefetch_related(
                "detalles"
            )
            .order_by("-fecha_creacion")
        )

        lista_evaluaciones = []

        for evaluacion in evaluaciones:
            detalles = [
                {
                    "id_detalle": detalle.id_detalle_reparacion,
                    "tipo_evaluacion": detalle.tipo_evaluacion,
                    "tipo_nombre": detalle.get_tipo_evaluacion_display(),
                    "porcentaje": float(detalle.porcentaje)
                }
                for detalle in evaluacion.detalles.all()
            ]

            lista_evaluaciones.append({
                "id_evaluacion": evaluacion.id_evaluacion,
                "id_materia_asignada": (
                    evaluacion.materia_asignacion.id_materia_asignada
                ),
                "materia": evaluacion.materia_asignacion.materia.nombre,
                "fecha_creacion": (
                    evaluacion.fecha_creacion.strftime("%Y-%m-%d")
                ),
                "detalles": detalles
            })

        if not lista_evaluaciones:
            return JsonResponse({
                "estado": "fallo",
                "title": "Aviso",
                "icon": "warning",
                "descripcion": (
                    "No existen evaluaciones registradas para "
                    "la materia seleccionada."
                )
            })

        return JsonResponse({
            "estado": "exito",
            "title": "Correcto",
            "icon": "success",
            "descripcion": (
                "Evaluaciones registradas correctamente."
            ),
            "evaluaciones": lista_evaluaciones
        })

@transaction.atomic
def mod_eval_rep(request):
    if request.method != "POST":
        return render(
            request,
            "Reparacion/modificar_evaluaciones_reparar.html"
        )

    fecha_actual = timezone.localdate()
    año_actual = fecha_actual.year

    periodo_reparacion = PeriodoAcademico.objects.filter(
        nombre__iexact="Reparación"
    ).first()

    if not periodo_reparacion:
        return JsonResponse({
            "estado": "fallo",
            "title": "Período no encontrado",
            "icon": "error",
            "descripcion": "No está configurado el período académico de Reparación."
        })

    def verificar_calendario():
        return CalendarioPeriodo.objects.filter(
            periodo=periodo_reparacion,
            calendario__tipo="PERIODO",
            calendario__activo=True,
            calendario__fecha_inicio__lte=fecha_actual,
            calendario__fecha_final__gte=fecha_actual,
            calendario__fecha_inicio__year=año_actual
        ).exists()

    if not verificar_calendario():
        return JsonResponse({
            "estado": "fallo",
            "title": "Período no vigente",
            "icon": "error",
            "descripcion": "El período académico de Reparación no está vigente para la fecha actual."
        })

    pnf = request.POST.get("pnf_asignado", "").strip()
    nucleo = request.POST.get("nucleo_asignado", "").strip()
    materia_asignado = request.POST.get("materia_asignada", "").strip()

    if not all([pnf, nucleo, materia_asignado]):
        return JsonResponse({
            "estado": "fallo",
            "title": "Datos incompletos",
            "icon": "error",
            "descripcion": "Debe seleccionar el PNF, el núcleo y la materia asignada."
        })

    if not PromedioFinal.objects.filter(
        materia_asignacion_id=materia_asignado,
        fecha_promedio__year=año_actual
    ).exists():
        return JsonResponse({
            "estado": "fallo",
            "title": "Promedio final no encontrado",
            "icon": "error",
            "descripcion": "La materia seleccionada no tiene registros de promedio final correspondientes al año en curso."
        })

    evaluacion = (
        EvaluacionReparacion.objects
        .filter(
            pnf_id=pnf,
            nucleo_id=nucleo,
            materia_asignacion_id=materia_asignado,
            fecha_creacion__year=año_actual,
            activo=True
        )
        .order_by("-fecha_creacion", "-id_evaluacion")
        .first()
    )

    if not evaluacion:
        return JsonResponse({
            "estado": "fallo",
            "title": "Evaluación no encontrada",
            "icon": "error",
            "descripcion": "No existe una evaluación activa de reparación para la materia seleccionada durante el año en curso."
        })

    tipos = request.POST.getlist("tipo_evaluacion[]")
    porcentajes = request.POST.getlist("porcentaje[]")

    if not tipos or len(tipos) != len(porcentajes):
        return JsonResponse({
            "estado": "fallo",
            "title": "Datos incompletos",
            "icon": "error",
            "descripcion": "Debe registrar el tipo y el porcentaje de cada evaluación."
        })

    if len(tipos) > 3:
        return JsonResponse({
            "estado": "fallo",
            "title": "Límite de evaluaciones",
            "icon": "error",
            "descripcion": "Solo se permiten hasta tres evaluaciones de reparación."
        })

    tipos_validos = {
        tipo[0]
        for tipo in DetalleEvaluacionReparacion.TIPOS_EVALUACION
    }

    if any(tipo not in tipos_validos for tipo in tipos):
        return JsonResponse({
            "estado": "fallo",
            "title": "Tipo de evaluación inválido",
            "icon": "error",
            "descripcion": "Uno o varios tipos de evaluación no son válidos."
        })

    if len(tipos) != len(set(tipos)):
        return JsonResponse({
            "estado": "fallo",
            "title": "Tipos duplicados",
            "icon": "error",
            "descripcion": "No puede registrar el mismo tipo de evaluación más de una vez."
        })

    porcentajes_convertidos = []

    try:
        for porcentaje in porcentajes:
            valor = Decimal(porcentaje)

            if not valor.is_finite() or valor <= 0 or valor > 100:
                raise InvalidOperation

            porcentajes_convertidos.append(valor)

    except (InvalidOperation, ValueError, TypeError):
        return JsonResponse({
            "estado": "fallo",
            "title": "Porcentaje inválido",
            "icon": "error",
            "descripcion": "Cada porcentaje debe ser un número mayor que cero y menor o igual a 100."
        })

    if sum(porcentajes_convertidos) != Decimal("100"):
        return JsonResponse({
            "estado": "fallo",
            "title": "Porcentajes incorrectos",
            "icon": "error",
            "descripcion": "La suma de los porcentajes de evaluación debe ser exactamente 100%."
        })

    try:
        evaluacion = (
            EvaluacionReparacion.objects
            .select_for_update()
            .filter(
                id_evaluacion=evaluacion.id_evaluacion,
                pnf_id=pnf,
                nucleo_id=nucleo,
                materia_asignacion_id=materia_asignado,
                fecha_creacion__year=año_actual,
                activo=True
            )
            .first()
        )

        if not evaluacion:
            return JsonResponse({
                "estado": "fallo",
                "title": "Evaluación no disponible",
                "icon": "error",
                "descripcion": "La evaluación ya no está activa o no corresponde al año en curso."
            })

        if not verificar_calendario():
            return JsonResponse({
                "estado": "fallo",
                "title": "Período no vigente",
                "icon": "error",
                "descripcion": "El período de Reparación dejó de estar vigente."
            })

        evaluacion.detalles.all().delete()

        DetalleEvaluacionReparacion.objects.bulk_create([
            DetalleEvaluacionReparacion(
                evaluacion_reparacion=evaluacion,
                tipo_evaluacion=tipo,
                porcentaje=porcentaje
            )
            for tipo, porcentaje in zip(
                tipos,
                porcentajes_convertidos
            )
        ])

        return JsonResponse({
            "estado": "exito",
            "title": "Evaluación modificada",
            "icon": "success",
            "descripcion": "La configuración de la evaluación de reparación del año en curso se modificó correctamente."
        })

    except Exception:
        import logging
        logging.getLogger(__name__).exception(
            "Error al modificar la evaluación de reparación."
        )

        return JsonResponse({
            "estado": "fallo",
            "title": "Error al modificar",
            "icon": "error",
            "descripcion": "Ocurrió un error al modificar la evaluación de reparación."
        })

# Calificaciones Reparación

def nucl_carg_not_rep(request):
    if request.method == "POST":
        cedula = request.session.get("cedula_usuario")
        perfil = request.POST.get("perfil", "").strip()

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
        año_actual = fecha_actual.year

        periodo_reparacion = PeriodoAcademico.objects.filter(
            nombre__iexact="Reparación"
        ).first()

        if not periodo_reparacion:
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Periodo académico no encontrado",
                "descripcion": (
                    "No se encontró el periodo académico de Reparación."
                )
            })

        carga_notas_vigente = CalendarioPeriodo.objects.filter(
            periodo=periodo_reparacion,
            calendario__tipo="CARGA_NOTAS",
            calendario__activo=True,
            calendario__fecha_inicio__lte=fecha_actual,
            calendario__fecha_final__gte=fecha_actual,
            calendario__fecha_inicio__year=año_actual
        ).exists()

        if not carga_notas_vigente:
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Fuera del periodo de carga de notas",
                "descripcion": (
                    "Actualmente no se encuentra vigente el calendario "
                    "de carga de notas de Reparación para registrar "
                    "o modificar calificaciones."
                )
            })

        if perfil == "CONTROL_ESTUDIO":
            nucleos_asignados = ControlEstudio.objects.filter(
                usuario__cedula_identidad=cedula,
                activo=True
            ).values_list("nucleo_id", flat=True)

            nucleos = Nucleos.objects.filter(
                id_nucleo__in=nucleos_asignados
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
                descripcion = (
                    "El usuario no tiene núcleos asignados como "
                    "Encargado de Control de Estudio."
                )
            else:
                descripcion = (
                    "El usuario no tiene núcleos asignados como Docente."
                )

            return JsonResponse({
                "estado": "fallo",
                "icon": "info",
                "title": "Sin núcleos asignados",
                "descripcion": descripcion
            })

        return JsonResponse({
            "estado": "exito",
            "datos": datos
        })

def pnf_carg_not_rep(request):
    if request.method == "POST":
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

        if perfil not in ("DOCENTE", "CONTROL_ESTUDIO"):
            return JsonResponse({
                "estado": "vacio",
                "datos": [],
                "title": "Perfil no válido",
                "descripcion": "El perfil seleccionado no es válido.",
                "icon": "info"
            })

        fecha_actual = timezone.localdate()
        año_actual = fecha_actual.year

        periodo_reparacion = PeriodoAcademico.objects.filter(
            nombre__iexact="Reparación"
        ).first()

        if not periodo_reparacion:
            return JsonResponse({
                "estado": "fallo",
                "datos": [],
                "title": "Periodo académico no encontrado",
                "descripcion": (
                    "No se encontró el periodo académico de Reparación."
                ),
                "icon": "warning"
            })

        carga_notas_vigente = CalendarioPeriodo.objects.filter(
            periodo=periodo_reparacion,
            calendario__tipo="CARGA_NOTAS",
            calendario__activo=True,
            calendario__fecha_inicio__lte=fecha_actual,
            calendario__fecha_final__gte=fecha_actual,
            calendario__fecha_inicio__year=año_actual
        ).exists()

        if not carga_notas_vigente:
            return JsonResponse({
                "estado": "fallo",
                "datos": [],
                "title": "Fuera del periodo de carga de notas",
                "descripcion": (
                    "Actualmente no se encuentra vigente el calendario "
                    "de carga de notas de Reparación para registrar "
                    "o modificar calificaciones."
                ),
                "icon": "warning"
            })

        if perfil == "CONTROL_ESTUDIO":
            control_estudio = ControlEstudio.objects.filter(
                usuario__cedula_identidad=cedula,
                nucleo_id=nucleo_asignado,
                activo=True
            ).first()

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

            pnfs = Pnf.objects.filter(
                pnfnucleo__id_nucleo=control_estudio.nucleo_id
            ).distinct().order_by("pnf")

        else:
            docentes = Docente.objects.filter(
                usuario__cedula_identidad=cedula,
                nucleo_id=nucleo_asignado,
                activo=True
            )

            pnf_ids = docentes.values_list(
                "pnf_id",
                flat=True
            ).distinct()

            pnfs = Pnf.objects.filter(
                id_pnf__in=pnf_ids,
                pnfnucleo__id_nucleo=nucleo_asignado
            ).distinct().order_by("pnf")

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

def doc_carg_not_rep(request):
    if request.method == "POST":
        nucleo_asignado = request.POST.get("nucleo_asignado", "").strip()
        pnf_seleccionado = request.POST.get("pnf_seleccionado", "").strip()
        cedula = request.session.get("cedula_usuario")

        if not cedula or not nucleo_asignado or not pnf_seleccionado:
            return JsonResponse({
                "estado": "fallo",
                "datos": [],
                "title": "Datos incompletos",
                "descripcion": (
                    "Debe seleccionar el núcleo y el PNF "
                    "para buscar docentes con materias arrastradas."
                ),
                "icon": "warning"
            })

        fecha_actual = timezone.localdate()
        año_actual = fecha_actual.year

        periodo_reparacion = PeriodoAcademico.objects.filter(
            nombre__iexact="Reparación"
        ).first()

        if not periodo_reparacion:
            return JsonResponse({
                "estado": "fallo",
                "datos": [],
                "title": "Periodo académico no encontrado",
                "descripcion": (
                    "No se encontró el periodo académico de Reparación."
                ),
                "icon": "warning"
            })

        carga_notas_vigente = CalendarioPeriodo.objects.filter(
            periodo=periodo_reparacion,
            calendario__tipo="CARGA_NOTAS",
            calendario__activo=True,
            calendario__fecha_inicio__lte=fecha_actual,
            calendario__fecha_final__gte=fecha_actual,
            calendario__fecha_inicio__year=año_actual
        ).exists()

        if not carga_notas_vigente:
            return JsonResponse({
                "estado": "fallo",
                "datos": [],
                "title": "Fuera del periodo de carga de notas",
                "descripcion": (
                    "Actualmente no se encuentra vigente el calendario "
                    "de carga de notas de Reparación para registrar "
                    "o modificar calificaciones."
                ),
                "icon": "warning"
            })

        materias_reprobadas = PromedioFinal.objects.filter(
            materia_asignacion__activo=True,
            materia_asignacion__materia__activa=True,
            materia_asignacion__materia__id_pnf_id=pnf_seleccionado,
            estudiante__nucleo_id=nucleo_asignado,
            estudiante__pnf_id=pnf_seleccionado,
            estado__icontains="REPROBADO"
        )

        docentes = (
            Docente.objects.filter(
                nucleo_id=nucleo_asignado,
                pnf_id=pnf_seleccionado,
                activo=True,
                materias_asignadas__materia_asignada__in=(
                    materias_reprobadas.values(
                        "materia_asignacion_id"
                    )
                ),
                materias_asignadas__activo=True,
                materias_asignadas__materia_asignada__activo=True
            )
            .exclude(
                usuario__cedula_identidad=cedula
            )
            .select_related("usuario")
            .distinct()
            .order_by(
                "usuario__apellidos",
                "usuario__nombres"
            )
        )

        if not docentes.exists():
            return JsonResponse({
                "estado": "fallo",
                "datos": [],
                "title": "No hay docentes con materias arrastradas",
                "descripcion": (
                    "No existen docentes asignados a materias con "
                    "estudiantes reprobados en el núcleo y PNF seleccionados."
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

# Registrar

def eval_mat_rep(request):
    if request.method == "POST":
        cedula = request.session.get("cedula_usuario")
        pnf = request.POST.get("id_pnf", "").strip()
        nucleo = request.POST.get("id_nucleo", "").strip()
        docente = request.POST.get("docente", "").strip()
        perfil = request.POST.get("perfil", "").strip()

        if not cedula:
            return JsonResponse({
                "estado": "fallo",
                "title": "Sesión no válida",
                "icon": "warning",
                "descripcion": "No se encontró un usuario autenticado.",
                "evaluaciones": []
            })

        if not all([pnf, nucleo, perfil]):
            return JsonResponse({
                "estado": "fallo",
                "title": "Datos incompletos",
                "icon": "warning",
                "descripcion": "Faltan datos requeridos.",
                "evaluaciones": []
            })

        if perfil not in ("DOCENTE", "CONTROL_ESTUDIO"):
            return JsonResponse({
                "estado": "fallo",
                "title": "Perfil no válido",
                "icon": "warning",
                "descripcion": "El perfil seleccionado no es válido.",
                "evaluaciones": []
            })

        fecha_actual = timezone.localdate()
        año_actual = fecha_actual.year

        periodo_reparacion = PeriodoAcademico.objects.filter(
            nombre__iexact="Reparación"
        ).first()

        if not periodo_reparacion:
            return JsonResponse({
                "estado": "fallo",
                "title": "Periodo académico no encontrado",
                "icon": "warning",
                "descripcion": (
                    "No se encontró el periodo académico de Reparación."
                ),
                "evaluaciones": []
            })

        calendarios = (
            CalendarioPeriodo.objects
            .filter(
                periodo=periodo_reparacion,
                calendario__tipo="CARGA_NOTAS",
                calendario__activo=True,
                calendario__fecha_inicio__lte=fecha_actual,
                calendario__fecha_final__gte=fecha_actual,
                calendario__fecha_inicio__year=año_actual
            )
            .select_related("periodo", "calendario")
        )

        if not calendarios.exists():
            return JsonResponse({
                "estado": "fallo",
                "title": "Periodo de carga de notas no disponible",
                "icon": "warning",
                "descripcion": (
                    "Actualmente no existe un calendario vigente de "
                    "carga de notas para Reparación."
                ),
                "evaluaciones": []
            })

        if perfil == "DOCENTE":
            cedula_docente = docente if docente else cedula

            docente_obj = Docente.objects.filter(
                usuario__cedula_identidad=cedula_docente,
                nucleo_id=nucleo,
                pnf_id=pnf,
                activo=True
            ).first()

            if not docente_obj:
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Docente no disponible",
                    "icon": "warning",
                    "descripcion": (
                        "No existe un docente activo asociado al núcleo "
                        "y PNF seleccionados."
                    ),
                    "evaluaciones": []
                })

            if cedula_docente != cedula:
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Acceso no autorizado",
                    "icon": "warning",
                    "descripcion": (
                        "El perfil Docente solo puede consultar sus propias "
                        "evaluaciones."
                    ),
                    "evaluaciones": []
                })

        else:
            control_estudio = ControlEstudio.objects.filter(
                usuario__cedula_identidad=cedula,
                nucleo_id=nucleo,
                activo=True
            ).first()

            if not control_estudio:
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Control de Estudio no disponible",
                    "icon": "warning",
                    "descripcion": (
                        "No existe un perfil activo de Control de Estudio "
                        "asociado al núcleo seleccionado."
                    ),
                    "evaluaciones": []
                })

            if not docente:
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Docente no seleccionado",
                    "icon": "info",
                    "descripcion": (
                        "Debe seleccionar un docente para consultar "
                        "sus evaluaciones de reparación."
                    ),
                    "evaluaciones": []
                })

            docente_obj = Docente.objects.filter(
                usuario__cedula_identidad=docente,
                nucleo_id=nucleo,
                pnf_id=pnf,
                activo=True
            ).first()

            if not docente_obj:
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Docente no disponible",
                    "icon": "warning",
                    "descripcion": (
                        "El docente seleccionado no está activo o no "
                        "pertenece al núcleo y PNF indicados."
                    ),
                    "evaluaciones": []
                })

        materias_docente = MateriaAsignada.objects.filter(
            activo=True,
            materia__activa=True,
            materia__id_pnf_id=pnf,
            docentes__docente=docente_obj,
            docentes__activo=True
        ).values_list("id_materia_asignada", flat=True)

        evaluaciones = (
            EvaluacionReparacion.objects
            .filter(
                pnf_id=pnf,
                nucleo_id=nucleo,
                materia_asignacion_id__in=materias_docente,
                activo=True,
                fecha_creacion__year=año_actual
            )
            .exclude(
                reparaciones__fecha_reparacion__year=año_actual
            )
            .select_related(
                "materia_asignacion",
                "materia_asignacion__materia",
                "materia_asignacion__materia__id_trayecto"
            )
            .prefetch_related("detalles")
            .distinct()
            .order_by("materia_asignacion__materia__nombre")
        )

        lista_evaluaciones = []

        for evaluacion in evaluaciones:
            materia_asignada = evaluacion.materia_asignacion

            if not materia_asignada:
                continue

            materia = materia_asignada.materia

            detalles = [
                {
                    "id_detalle": detalle.id_detalle_reparacion,
                    "tipo_evaluacion": detalle.tipo_evaluacion,
                    "tipo_nombre": detalle.get_tipo_evaluacion_display(),
                    "porcentaje": float(detalle.porcentaje)
                }
                for detalle in evaluacion.detalles.all()
            ]

            lista_evaluaciones.append({
                "id_evaluacion": evaluacion.id_evaluacion,
                "id_materia_asignada": (
                    materia_asignada.id_materia_asignada
                ),
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
                "fecha_creacion": (
                    evaluacion.fecha_creacion.strftime("%Y-%m-%d")
                ),
                "detalles": detalles
            })

        return JsonResponse({
            "estado": "exito",
            "title": "Correcto",
            "icon": "success",
            "descripcion": (
                "Evaluaciones de reparación cargadas correctamente."
            ),
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
            cedula = request.session.get("cedula_usuario")
            nucleo = request.POST.get("id_nucleo", "").strip()
            pnf = request.POST.get("id_pnf", "").strip()
            materia_asignacion = request.POST.get("id_materia_asignacion", "").strip()
            trayecto = request.POST.get("id_trayecto", "").strip()
            docente = request.POST.get("docente", "").strip()
            perfil = request.POST.get("perfil", "").strip()

            if not cedula:
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Sesión no válida",
                    "icon": "warning",
                    "descripcion": "No se encontró un usuario autenticado.",
                    "estudiantes": []
                })

            if perfil not in ("DOCENTE", "CONTROL_ESTUDIO"):
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Perfil no válido",
                    "icon": "warning",
                    "descripcion": "El perfil seleccionado no es válido.",
                    "estudiantes": []
                })

            if not all([nucleo, pnf, materia_asignacion, trayecto]):
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Datos incompletos",
                    "icon": "warning",
                    "descripcion": (
                        "Faltan datos requeridos para consultar los estudiantes."
                    ),
                    "estudiantes": []
                })

            # Validar periodo y calendario de carga de notas
            fecha_actual = timezone.localdate()
            año_actual = fecha_actual.year

            periodo_reparacion = PeriodoAcademico.objects.filter(
                nombre__iexact="Reparación"
            ).first()

            if not periodo_reparacion:
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Periodo académico no encontrado",
                    "icon": "warning",
                    "descripcion": (
                        "No existe el periodo académico Reparación."
                    ),
                    "estudiantes": []
                })

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
                .select_related("periodo", "calendario")
                .first()
            )

            if not calendario_reparacion:
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Carga de notas no disponible",
                    "icon": "warning",
                    "descripcion": (
                        "Actualmente no existe un calendario vigente "
                        "de carga de notas de Reparación."
                    ),
                    "estudiantes": []
                })

            # Validar el perfil y determinar el docente autorizado
            if perfil == "DOCENTE":
                docente_obj = Docente.objects.filter(
                    usuario__cedula_identidad=cedula,
                    nucleo_id=nucleo,
                    pnf_id=pnf,
                    activo=True
                ).first()

                if not docente_obj:
                    return JsonResponse({
                        "estado": "fallo",
                        "title": "Docente no autorizado",
                        "icon": "warning",
                        "descripcion": (
                            "No existe un perfil docente activo asociado "
                            "al núcleo y PNF seleccionados."
                        ),
                        "estudiantes": []
                    })

            else:
                control_estudio = ControlEstudio.objects.filter(
                    usuario__cedula_identidad=cedula,
                    nucleo_id=nucleo,
                    activo=True
                ).first()

                if not control_estudio:
                    return JsonResponse({
                        "estado": "fallo",
                        "title": "Control de Estudio no autorizado",
                        "icon": "warning",
                        "descripcion": (
                            "No existe un perfil activo de Control de Estudio "
                            "asociado al núcleo seleccionado."
                        ),
                        "estudiantes": []
                    })

                if not docente:
                    return JsonResponse({
                        "estado": "fallo",
                        "title": "Docente no seleccionado",
                        "icon": "info",
                        "descripcion": (
                            "Debe seleccionar un docente para consultar "
                            "los estudiantes con materias reprobadas."
                        ),
                        "estudiantes": []
                    })

                docente_obj = Docente.objects.filter(
                    usuario__cedula_identidad=docente,
                    nucleo_id=nucleo,
                    pnf_id=pnf,
                    activo=True
                ).first()

                if not docente_obj:
                    return JsonResponse({
                        "estado": "fallo",
                        "title": "Docente no disponible",
                        "icon": "warning",
                        "descripcion": (
                            "El docente seleccionado no está activo o no "
                            "pertenece al núcleo y PNF indicados."
                        ),
                        "estudiantes": []
                    })

            # Verificar que la materia esté asignada al docente autorizado
            materia_valida = MateriaAsignada.objects.filter(
                id_materia_asignada=materia_asignacion,
                activo=True,
                materia__activa=True,
                materia__id_pnf_id=pnf,
                docentes__docente=docente_obj,
                docentes__activo=True
            ).exists()

            if not materia_valida:
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Materia no autorizada",
                    "icon": "warning",
                    "descripcion": (
                        "La materia seleccionada no está asignada al docente "
                        "autorizado o no corresponde al PNF seleccionado."
                    ),
                    "estudiantes": []
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
                    promedio_final__gte=6.0,
                    asistencia__gte=75.0
                )
                .select_related(
                    "estudiante__usuario",
                    "trayecto"
                )
                .order_by(
                    "estudiante__usuario__apellidos",
                    "estudiante__usuario__nombres"
                )
                .distinct()
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
                    "promedio_final": float(reg.promedio_final),
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
                "title": "Consulta completada",
                "icon": "success",
                "descripcion": (
                    "Estudiantes con materias reprobadas consultados "
                    "correctamente."
                ),
                "estudiantes": estudiantes,
                "total": len(estudiantes),
                "periodo": {
                    "id_periodo": (
                        calendario_reparacion.periodo.id_periodo_academico
                    ),
                    "nombre": calendario_reparacion.periodo.nombre
                }
            })

        except Exception:
            return JsonResponse({
                "estado": "fallo",
                "title": "Error de servidor",
                "icon": "error",
                "descripcion": (
                    "Ocurrió un error inesperado al consultar "
                    "los estudiantes."
                ),
                "estudiantes": []
            })

def reg_rep_not(request):
    if request.method != "POST":
        return render(request, "Reparacion/registrar_reparacion.html")

    try:
        cedula = request.session.get("cedula_usuario")
        nucleo = request.POST.get("nucleo_asignado", "").strip()
        pnf = request.POST.get("pnf_asignado", "").strip()
        materia_id = request.POST.get("materia_asignada", "").strip()
        notas_json = request.POST.get("notas_reparacion", "")
        docente = request.POST.get("docente", "").strip()
        perfil = request.POST.get("perfil", "").strip()

        if not cedula:
            return JsonResponse({
                "estado": "fallo",
                "title": "Sesión no válida",
                "icon": "warning",
                "descripcion": "No se encontró un usuario autenticado."
            })

        if not all([nucleo, pnf, materia_id, perfil]):
            return JsonResponse({
                "estado": "fallo",
                "title": "Datos incompletos",
                "icon": "warning",
                "descripcion": (
                    "Debe indicar el núcleo, PNF, materia y perfil."
                )
            })

        if perfil not in ("DOCENTE", "CONTROL_ESTUDIO"):
            return JsonResponse({
                "estado": "fallo",
                "title": "Perfil no válido",
                "icon": "warning",
                "descripcion": "El perfil seleccionado no es válido."
            })

        if not notas_json:
            return JsonResponse({
                "estado": "fallo",
                "title": "Sin datos",
                "icon": "warning",
                "descripcion": "No se recibieron calificaciones."
            })

        try:
            lista_notas = json.loads(notas_json)
        except (json.JSONDecodeError, TypeError):
            return JsonResponse({
                "estado": "fallo",
                "title": "Datos inválidos",
                "icon": "warning",
                "descripcion": (
                    "Las calificaciones recibidas tienen un formato inválido."
                )
            })

        if not isinstance(lista_notas, list) or not lista_notas:
            return JsonResponse({
                "estado": "fallo",
                "title": "Sin calificaciones",
                "icon": "warning",
                "descripcion": (
                    "Debe proporcionar al menos una calificación válida."
                )
            })

        fecha_actual = timezone.localdate()
        año_actual = fecha_actual.year

        # Validar el periodo académico de Reparación
        periodo_reparacion = PeriodoAcademico.objects.filter(
            nombre__iexact="Reparación"
        ).first()

        if not periodo_reparacion:
            return JsonResponse({
                "estado": "fallo",
                "title": "Periodo académico no encontrado",
                "icon": "warning",
                "descripcion": (
                    "No se encontró el periodo académico de Reparación."
                )
            })

        # Validar el calendario de carga de notas
        carga_notas_vigente = CalendarioPeriodo.objects.filter(
            periodo=periodo_reparacion,
            calendario__tipo="CARGA_NOTAS",
            calendario__activo=True,
            calendario__fecha_inicio__lte=fecha_actual,
            calendario__fecha_final__gte=fecha_actual,
            calendario__fecha_inicio__year=año_actual
        ).exists()

        if not carga_notas_vigente:
            return JsonResponse({
                "estado": "fallo",
                "title": "Carga de notas no disponible",
                "icon": "warning",
                "descripcion": (
                    "Actualmente no se encuentra vigente el calendario "
                    "de carga de notas de Reparación."
                )
            })

        # Determinar el docente autorizado según el perfil
        if perfil == "DOCENTE":
            docente_obj = Docente.objects.filter(
                usuario__cedula_identidad=cedula,
                nucleo_id=nucleo,
                pnf_id=pnf,
                activo=True
            ).first()

            if not docente_obj:
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Docente no autorizado",
                    "icon": "warning",
                    "descripcion": (
                        "No existe un perfil docente activo asociado "
                        "al núcleo y PNF seleccionados."
                    )
                })

        else:
            control_estudio = ControlEstudio.objects.filter(
                usuario__cedula_identidad=cedula,
                nucleo_id=nucleo,
                activo=True
            ).first()

            if not control_estudio:
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Control de Estudio no autorizado",
                    "icon": "warning",
                    "descripcion": (
                        "No existe un perfil activo de Control de Estudio "
                        "asociado al núcleo seleccionado."
                    )
                })

            if not docente:
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Docente no seleccionado",
                    "icon": "warning",
                    "descripcion": (
                        "Debe seleccionar el docente responsable "
                        "de la materia."
                    )
                })

            docente_obj = Docente.objects.filter(
                usuario__cedula_identidad=docente,
                nucleo_id=nucleo,
                pnf_id=pnf,
                activo=True
            ).first()

            if not docente_obj:
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Docente no disponible",
                    "icon": "warning",
                    "descripcion": (
                        "El docente seleccionado no está activo o no "
                        "pertenece al núcleo y PNF indicados."
                    )
                })

        # Validar que la materia esté asignada al docente autorizado
        materia_asignada = MateriaAsignada.objects.filter(
            id_materia_asignada=materia_id,
            activo=True,
            materia__activa=True,
            materia__id_pnf_id=pnf,
            docentes__docente=docente_obj,
            docentes__activo=True
        ).distinct().first()

        if not materia_asignada:
            return JsonResponse({
                "estado": "fallo",
                "title": "Materia no autorizada",
                "icon": "warning",
                "descripcion": (
                    "La materia seleccionada no está asignada al docente "
                    "autorizado o no corresponde al PNF indicado."
                )
            })

        # Validar que exista la evaluación de Reparación
        evaluacion = (
            EvaluacionReparacion.objects
            .filter(
                pnf_id=pnf,
                nucleo_id=nucleo,
                materia_asignacion=materia_asignada,
                activo=True,
                fecha_creacion__year=año_actual
            )
            .first()
        )

        if not evaluacion:
            return JsonResponse({
                "estado": "fallo",
                "title": "Evaluación inexistente",
                "icon": "warning",
                "descripcion": (
                    "No existe una evaluación de Reparación activa "
                    "para esta materia en el año actual."
                )
            })

        # Validar todas las calificaciones antes de guardar
        notas_validadas = []
        estudiantes_procesados = set()

        for item in lista_notas:
            if not isinstance(item, dict):
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Datos inválidos",
                    "icon": "warning",
                    "descripcion": (
                        "Una de las calificaciones recibidas no es válida."
                    )
                })

            id_estudiante = item.get("id_estudiante")
            valor_nota = item.get("nota")

            if id_estudiante in (None, "") or valor_nota in (None, ""):
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Datos incompletos",
                    "icon": "warning",
                    "descripcion": (
                        "Cada registro debe incluir el estudiante "
                        "y su calificación."
                    )
                })

            try:
                id_estudiante = int(id_estudiante)
                nota = Decimal(str(valor_nota))
            except (ValueError, TypeError, InvalidOperation):
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Calificación inválida",
                    "icon": "warning",
                    "descripcion": (
                        "El identificador del estudiante o la nota "
                        "no tiene un formato válido."
                    )
                })

            if not nota.is_finite() or nota < 0 or nota > 20:
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Nota inválida",
                    "icon": "warning",
                    "descripcion": (
                        "Las calificaciones deben estar entre 0 y 20."
                    )
                })

            if id_estudiante in estudiantes_procesados:
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Estudiante duplicado",
                    "icon": "warning",
                    "descripcion": (
                        "La lista contiene más de una calificación "
                        "para el mismo estudiante."
                    )
                })

            estudiante = Estudiante.objects.filter(
                pk=id_estudiante,
                nucleo_id=nucleo,
                pnf_id=pnf
            ).first()

            if not estudiante:
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Estudiante no válido",
                    "icon": "warning",
                    "descripcion": (
                        "Uno de los estudiantes no pertenece al "
                        "núcleo y PNF seleccionados."
                    )
                })

            # Comprobar que el estudiante sea apto para Reparación
            promedio_valido = PromedioFinal.objects.filter(
                estudiante=estudiante,
                materia_asignacion=materia_asignada,
                estado="REPROBADO",
                fecha_promedio__year=año_actual,
                promedio_final__gte=6.0,
                asistencia__gte=75.0
            ).exists()

            if not promedio_valido:
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Estudiante no apto",
                    "icon": "warning",
                    "descripcion": (
                        "Uno de los estudiantes no cumple las condiciones "
                        "para presentar Reparación en esta materia."
                    )
                })

            estado = "APROBADO" if nota >= 12 else "REPROBADO"

            notas_validadas.append({
                "estudiante": estudiante,
                "nota": nota,
                "estado": estado
            })

            estudiantes_procesados.add(id_estudiante)

        # Guardar las calificaciones de forma atómica
        with transaction.atomic():
            evaluacion = (
                EvaluacionReparacion.objects
                .select_for_update()
                .get(
                    pk=evaluacion.pk,
                    activo=True
                )
            )

            for registro in notas_validadas:
                Reparacion.objects.update_or_create(
                    estudiante=registro["estudiante"],
                    evaluacion_reparacion=evaluacion,
                    defaults={
                        "fecha_reparacion": fecha_actual,
                        "calificacion": registro["nota"],
                        "estado": registro["estado"]
                    }
                )

        return JsonResponse({
            "estado": "exito",
            "title": "Correcto",
            "icon": "success",
            "descripcion": (
                "Las notas de Reparación se registraron correctamente."
            ),
            "total": len(notas_validadas)
        })

    except Exception:
        return JsonResponse({
            "estado": "fallo",
            "title": "Error del servidor",
            "icon": "error",
            "descripcion": (
                "Ocurrió un error inesperado al registrar "
                "las notas de Reparación."
            )
        })

# Visualizar

def mat_vis_not(request):
    if request.method != "POST":
        return JsonResponse({
            "estado": "fallo",
            "title": "Método no permitido",
            "icon": "error",
            "descripcion": "La solicitud debe realizarse mediante POST."
        }, status=405)

    nucleo = request.POST.get("id_nucleo", "").strip()
    pnf = request.POST.get("id_pnf", "").strip()
    cedula = request.session.get("cedula_usuario")
    docente = request.POST.get("docente", "").strip()
    perfil = request.POST.get("perfil", "").strip()

    if not all([nucleo, pnf, cedula, perfil]):
        return JsonResponse({
            "estado": "fallo",
            "title": "Datos incompletos",
            "icon": "warning",
            "descripcion": "Faltan datos requeridos para realizar la consulta."
        })

    if perfil not in ("DOCENTE", "CONTROL_ESTUDIO"):
        return JsonResponse({
            "estado": "fallo",
            "title": "Perfil no válido",
            "icon": "warning",
            "descripcion": "El perfil seleccionado no es válido."
        })

    if perfil == "DOCENTE":
        docente_obj = Docente.objects.filter(
            usuario__cedula_identidad=cedula,
            nucleo_id=nucleo,
            pnf_id=pnf,
            activo=True
        ).first()

        if not docente_obj:
            return JsonResponse({
                "estado": "fallo",
                "title": "Docente no encontrado",
                "icon": "warning",
                "descripcion": (
                    "El docente autenticado no está asignado "
                    "al núcleo y P.N.F. seleccionados."
                )
            })

    else:
        if not docente:
            return JsonResponse({
                "estado": "fallo",
                "title": "Docente no seleccionado",
                "icon": "warning",
                "descripcion": "Debe seleccionar un docente."
            })

        control_estudio = ControlEstudio.objects.filter(
            usuario__cedula_identidad=cedula,
            nucleo_id=nucleo,
            activo=True
        ).first()

        if not control_estudio:
            return JsonResponse({
                "estado": "fallo",
                "title": "Acceso denegado",
                "icon": "warning",
                "descripcion": (
                    "No tiene un perfil activo de Control de Estudio "
                    "asignado al núcleo seleccionado."
                )
            })

        docente_obj = Docente.objects.filter(
            usuario__cedula_identidad=docente,
            nucleo_id=nucleo,
            pnf_id=pnf,
            activo=True
        ).first()

        if not docente_obj:
            return JsonResponse({
                "estado": "fallo",
                "title": "Docente no encontrado",
                "icon": "warning",
                "descripcion": (
                    "El docente seleccionado no está asignado "
                    "al núcleo y P.N.F. seleccionados."
                )
            })

    evaluaciones = (
        EvaluacionReparacion.objects
        .filter(
            pnf_id=pnf,
            nucleo_id=nucleo,
            activo=True,
            materia_asignacion__docentes__docente=docente_obj,
            materia_asignacion__docentes__activo=True,
            reparaciones__isnull=False
        )
        .select_related(
            "materia_asignacion",
            "materia_asignacion__materia",
            "materia_asignacion__materia__id_trayecto"
        )
        .order_by(
            "materia_asignacion__materia__nombre",
            "-fecha_creacion",
            "-id_evaluacion"
        )
        .distinct()
    )

    materias_por_id = {}

    for evaluacion in evaluaciones:
        materia_asignada = evaluacion.materia_asignacion

        if not materia_asignada or not materia_asignada.materia:
            continue

        materia = materia_asignada.materia
        id_materia = materia.id_materia

        if id_materia not in materias_por_id:
            materias_por_id[id_materia] = {
                "id_evaluacion": evaluacion.id_evaluacion,
                "id_materia_asignada": materia_asignada.id_materia_asignada,
                "id_materia": materia.id_materia,
                "nombre": materia.nombre,
                "id_trayecto": (
                    materia.id_trayecto_id
                    if materia.id_trayecto
                    else None
                ),
                "trayecto": (
                    materia.id_trayecto.nombre
                    if materia.id_trayecto
                    else ""
                )
            }

    materias = list(materias_por_id.values())

    return JsonResponse({
        "estado": "exito",
        "materias": materias,
        "total": len(materias),
        "mensaje": (
            "Materias consultadas correctamente."
            if materias
            else "No se encontraron evaluaciones de reparación "
                 "para el docente seleccionado."
        )
    })

def fech_reg_rep(request):
    if request.method == "POST":
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
            "title": "Método no permitido",
            "icon": "error",
            "descripcion": "La solicitud debe realizarse mediante POST."
        }, status=405)

    nucleo = request.POST.get("id_nucleo", "").strip()
    pnf = request.POST.get("id_pnf", "").strip()
    materia_asignacion = request.POST.get("id_materia_asignacion", "").strip()
    trayecto = request.POST.get("id_trayecto", "").strip()
    fecha_reparacion = request.POST.get("fecha_reparacion", "").strip()
    cedula = request.session.get("cedula_usuario")
    docente = request.POST.get("docente", "").strip()
    perfil = request.POST.get("perfil", "").strip()

    if not all([
        nucleo,
        pnf,
        materia_asignacion,
        trayecto,
        fecha_reparacion,
        cedula,
        perfil
    ]):
        return JsonResponse({
            "estado": "fallo",
            "title": "Datos incompletos",
            "icon": "warning",
            "descripcion": (
                "Debe proporcionar el núcleo, P.N.F., materia, trayecto, "
                "fecha de reparación y perfil."
            )
        })

    if perfil not in ("DOCENTE", "CONTROL_ESTUDIO"):
        return JsonResponse({
            "estado": "fallo",
            "title": "Perfil no válido",
            "icon": "warning",
            "descripcion": "El perfil seleccionado no es válido."
        })

    try:
        # VALIDAR FECHA
        fecha_reparacion = datetime.strptime(
            fecha_reparacion, "%Y-%m-%d"
        ).date()

        # VALIDAR PERFIL Y OBTENER DOCENTE
        if perfil == "DOCENTE":
            docente_obj = Docente.objects.filter(
                usuario__cedula_identidad=cedula,
                nucleo_id=nucleo,
                pnf_id=pnf,
                activo=True
            ).first()

            if not docente_obj:
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Docente no encontrado",
                    "icon": "warning",
                    "descripcion": (
                        "El docente autenticado no está asignado "
                        "al núcleo y P.N.F. seleccionados."
                    )
                })

        else:
            if not docente:
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Docente no seleccionado",
                    "icon": "warning",
                    "descripcion": "Debe seleccionar un docente."
                })

            control_estudio = ControlEstudio.objects.filter(
                usuario__cedula_identidad=cedula,
                nucleo_id=nucleo,
                activo=True
            ).first()

            if not control_estudio:
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Acceso denegado",
                    "icon": "warning",
                    "descripcion": (
                        "No tiene un perfil activo de Control de Estudio "
                        "asignado al núcleo seleccionado."
                    )
                })

            docente_obj = Docente.objects.filter(
                usuario__cedula_identidad=docente,
                nucleo_id=nucleo,
                pnf_id=pnf,
                activo=True
            ).first()

            if not docente_obj:
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Docente no encontrado",
                    "icon": "warning",
                    "descripcion": (
                        "El docente seleccionado no está asignado "
                        "al núcleo y P.N.F. seleccionados."
                    )
                })

        # VALIDAR ASIGNACIÓN DE LA MATERIA AL DOCENTE
        materia_valida = DocenteAsignadoMateria.objects.filter(
            docente=docente_obj,
            docente__nucleo_id=nucleo,
            docente__pnf_id=pnf,
            docente__activo=True,
            activo=True,
            materia_asignada_id=materia_asignacion,
            materia_asignada__activo=True,
            materia_asignada__materia__activa=True,
            materia_asignada__materia__id_pnf_id=pnf,
            materia_asignada__materia__id_trayecto_id=trayecto
        ).exists()

        if not materia_valida:
            return JsonResponse({
                "estado": "fallo",
                "title": "Materia no válida",
                "icon": "warning",
                "descripcion": (
                    "La materia no está asignada al docente "
                    "o no corresponde al núcleo, P.N.F. y trayecto seleccionados."
                )
            })

        # CONSULTAR CALIFICACIONES DE REPARACIÓN
        reparaciones = (
            Reparacion.objects
            .filter(
                evaluacion_reparacion__materia_asignacion_id=materia_asignacion,
                evaluacion_reparacion__pnf_id=pnf,
                evaluacion_reparacion__nucleo_id=nucleo,
                evaluacion_reparacion__activo=True,
                evaluacion_reparacion__materia_asignacion__materia__id_trayecto_id=trayecto,
                evaluacion_reparacion__materia_asignacion__docentes__docente=docente_obj,
                evaluacion_reparacion__materia_asignacion__docentes__activo=True,
                estudiante__nucleo_id=nucleo,
                estudiante__pnf_id=pnf,
                fecha_reparacion=fecha_reparacion
            )
            .select_related(
                "estudiante__usuario",
                "evaluacion_reparacion__materia_asignacion__materia"
            )
            .distinct()
            .order_by(
                "estudiante__usuario__apellidos",
                "estudiante__usuario__nombres"
            )
        )

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
            "estudiantes": estudiantes,
            "total": len(estudiantes),
            "descripcion": (
                "Consulta realizada correctamente."
                if estudiantes
                else (
                    "No se encontraron calificaciones de reparación "
                    "para la fecha seleccionada."
                )
            )
        })

    except ValueError:
        return JsonResponse({
            "estado": "fallo",
            "title": "Fecha no válida",
            "icon": "warning",
            "descripcion": "La fecha debe tener el formato AAAA-MM-DD."
        })

    except Exception:
        return JsonResponse({
            "estado": "fallo",
            "title": "Error de consulta",
            "icon": "error",
            "descripcion": (
                "Ocurrió un error al consultar las calificaciones de reparación."
            )
        })
        
def vis_rep_not(request):
    return render(request, "Reparacion/visualizar_reparacion.html")

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
    docente = request.POST.get("docente")
    perfil = request.POST.get("perfil")
    cedula = request.session.get("cedula_usuario")

    if not nucleo:
        return JsonResponse({
            "estado": "fallo",
            "title": "Dato faltante",
            "icon": "warning",
            "descripcion": "Debe seleccionar un núcleo."
        })

    if not pnf:
        return JsonResponse({
            "estado": "fallo",
            "title": "Dato faltante",
            "icon": "warning",
            "descripcion": "Debe seleccionar un PNF."
        })

    if not perfil:
        return JsonResponse({
            "estado": "fallo",
            "title": "Dato faltante",
            "icon": "warning",
            "descripcion": "Debe seleccionar un perfil."
        })
    
    if perfil not in ["DOCENTE", "CONTROL_ESTUDIO"]:
        return JsonResponse({
            "estado": "fallo",
            "title": "Error",
            "icon": "error",
            "descripcion": "El perfil seleccionado no tiene permisos para realizar esta consulta."
        })

    # Validar el docente según el perfil
    if perfil == "DOCENTE":
        docente_obj = Docente.objects.filter(
            usuario__cedula_identidad=cedula,
            nucleo_id=nucleo,
            pnf_id=pnf,
            activo=True
        ).first()

    else:
        if not docente:
            return JsonResponse({
                "estado": "fallo",
                "title": "Error",
                "icon": "error",
                "descripcion": "Debe seleccionar un docente."
            })

        control_estudio = ControlEstudio.objects.filter(
            usuario__cedula_identidad=cedula,
            nucleo_id=nucleo,
            activo=True
        ).exists()

        if not control_estudio:
            return JsonResponse({
                "estado": "fallo",
                "title": "Error",
                "icon": "error",
                "descripcion": "No tiene permisos para consultar docentes de este núcleo."
            })

        docente_obj = Docente.objects.filter(
            usuario__cedula_identidad=docente,
            nucleo_id=nucleo,
            pnf_id=pnf,
            activo=True
        ).first()

    if not docente_obj:
        return JsonResponse({
            "estado": "fallo",
            "title": "Error",
            "icon": "error",
            "descripcion": "No se encontró un docente activo asociado al núcleo y PNF seleccionados."
        })

    fecha_actual = timezone.localdate()
    año_actual = fecha_actual.year

    # Validar calendario de carga de notas de Reparación
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
        .select_related("periodo", "calendario")
    )

    if not calendarios_periodos.exists():
        return JsonResponse({
            "estado": "exito",
            "materias": [],
            "periodos_actuales": [],
            "mensaje": "Actualmente no existe un calendario de carga de notas habilitado para reparación."
        })

    # Materias que tienen calificaciones de reparación registradas
    materias_reparacion = (
        Reparacion.objects
        .filter(
            calificacion__isnull=False,
            evaluacion_reparacion__activo=True,
            evaluacion_reparacion__pnf_id=pnf,
            evaluacion_reparacion__nucleo_id=nucleo
        )
        .values_list(
            "evaluacion_reparacion__materia_asignacion_id",
            flat=True
        )
        .distinct()
    )

    periodos_actuales = [
        {
            "id_periodo": cp.periodo.id_periodo_academico,
            "nombre": cp.periodo.nombre
        }
        for cp in calendarios_periodos
    ]

    if not materias_reparacion.exists():
        return JsonResponse({
            "estado": "exito",
            "materias": [],
            "periodos_actuales": periodos_actuales,
            "mensaje": "No existen materias con notas de reparación registradas para modificar."
        })

    # Materias asignadas al docente seleccionado
    materias_asignadas = (
        DocenteAsignadoMateria.objects
        .filter(
            docente=docente_obj,
            docente__nucleo_id=nucleo,
            docente__pnf_id=pnf,
            docente__activo=True,
            activo=True,
            materia_asignada__activo=True,
            materia_asignada_id__in=materias_reparacion,
            materia_asignada__materia__activa=True,
            materia_asignada__materia__id_pnf_id=pnf
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
        "periodos_actuales": periodos_actuales,
        "mensaje": (
            "Materias disponibles para modificar."
            if materias
            else "No existen materias con notas de reparación registradas para el docente seleccionado."
        )
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
    docente = request.POST.get("docente")
    perfil = request.POST.get("perfil")
    cedula = request.session.get("cedula_usuario")

    if not nucleo:
        return JsonResponse({
            "estado": "fallo",
            "title": "Dato faltante",
            "icon": "warning",
            "descripcion": "Debe seleccionar un núcleo."
        })

    if not pnf:
        return JsonResponse({
            "estado": "fallo",
            "title": "Dato faltante",
            "icon": "warning",
            "descripcion": "Debe seleccionar un PNF."
        })

    if not materia_asignacion:
        return JsonResponse({
            "estado": "fallo",
            "title": "Dato faltante",
            "icon": "warning",
            "descripcion": "Debe seleccionar una materia asignada."
        })

    if not trayecto:
        return JsonResponse({
            "estado": "fallo",
            "title": "Dato faltante",
            "icon": "warning",
            "descripcion": "Debe seleccionar un trayecto académico."
        })

    if not perfil:
        return JsonResponse({
            "estado": "fallo",
            "title": "Dato faltante",
            "icon": "warning",
            "descripcion": "Debe seleccionar un perfil."
        })

    if not cedula:
        return JsonResponse({
            "estado": "fallo",
            "title": "Sesión inválida",
            "icon": "warning",
            "descripcion": "No se pudo identificar al usuario autenticado."
        })

    if perfil not in ["DOCENTE", "CONTROL_ESTUDIO"]:
        return JsonResponse({
            "estado": "fallo",
            "title": "Error",
            "icon": "error",
            "descripcion": (
                "El perfil seleccionado no tiene permisos "
                "para realizar esta consulta."
            )
        })

    try:
        if perfil == "DOCENTE":
            docente_obj = Docente.objects.filter(
                usuario__cedula_identidad=cedula,
                nucleo_id=nucleo,
                pnf_id=pnf,
                activo=True
            ).first()

        else:
            if not docente:
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Error",
                    "icon": "error",
                    "descripcion": "Debe seleccionar un docente."
                })

            control_estudio = ControlEstudio.objects.filter(
                usuario__cedula_identidad=cedula,
                nucleo_id=nucleo,
                activo=True
            ).exists()

            if not control_estudio:
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Error",
                    "icon": "error",
                    "descripcion": (
                        "No tiene permisos para consultar docentes "
                        "de este núcleo."
                    )
                })

            docente_obj = Docente.objects.filter(
                usuario__cedula_identidad=docente,
                nucleo_id=nucleo,
                pnf_id=pnf,
                activo=True
            ).first()

        if not docente_obj:
            return JsonResponse({
                "estado": "fallo",
                "title": "Error",
                "icon": "error",
                "descripcion": (
                    "No se encontró un docente activo asociado "
                    "al núcleo y PNF seleccionados."
                )
            })

        asignacion_valida = DocenteAsignadoMateria.objects.filter(
            docente=docente_obj,
            docente__nucleo_id=nucleo,
            docente__pnf_id=pnf,
            docente__activo=True,
            activo=True,
            materia_asignada_id=materia_asignacion,
            materia_asignada__activo=True,
            materia_asignada__materia__activa=True,
            materia_asignada__materia__id_pnf_id=pnf,
            materia_asignada__materia__id_trayecto_id=trayecto
        ).exists()

        if not asignacion_valida:
            return JsonResponse({
                "estado": "fallo",
                "title": "Error",
                "icon": "error",
                "descripcion": (
                    "El docente seleccionado no tiene asignada "
                    "esta materia en el trayecto indicado."
                )
            })

        # Obtener el año actual automáticamente.
        anio_actual = timezone.localdate().year

        # Consultar únicamente las reparaciones cuyas evaluaciones
        # fueron creadas durante el año en curso.
        reparaciones = (
            Reparacion.objects
            .filter(
                evaluacion_reparacion__materia_asignacion_id=materia_asignacion,
                evaluacion_reparacion__materia_asignacion__materia__id_trayecto_id=trayecto,
                evaluacion_reparacion__activo=True,
                evaluacion_reparacion__fecha_creacion__year=anio_actual,
                estudiante__nucleo_id=nucleo,
                estudiante__pnf_id=pnf,
                evaluacion_reparacion__materia_asignacion__docentes__docente=docente_obj,
                evaluacion_reparacion__materia_asignacion__docentes__activo=True
            )
            .select_related(
                "estudiante__usuario",
                "evaluacion_reparacion__materia_asignacion__materia",
                "evaluacion_reparacion__materia_asignacion__materia__id_trayecto"
            )
            .distinct()
            .order_by(
                "estudiante__usuario__apellidos",
                "estudiante__usuario__nombres"
            )
        )

        estudiantes = []

        for rep in reparaciones:
            estudiante = rep.estudiante
            usuario = estudiante.usuario
            materia = rep.evaluacion_reparacion.materia_asignacion.materia

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
            "total": len(estudiantes),
            "descripcion": (
                f"Estudiantes encontrados correctamente para el año {anio_actual}."
                if estudiantes
                else (
                    f"No se encontraron estudiantes registrados en reparación "
                    f"para esta materia durante el año {anio_actual}."
                )
            )
        })

    except Exception:
        return JsonResponse({
            "estado": "fallo",
            "title": "Error de Servidor",
            "icon": "error",
            "descripcion": (
                "Ocurrió un error al consultar los registros de reparación."
            )
        })

def mod_rep_reg(request):
    if request.method != "POST":
        return render(request, "Reparacion/modificar_reparacion.html")

    nucleo = request.POST.get("nucleo_asignado")
    pnf = request.POST.get("pnf_asignado")
    materia_asignacion = request.POST.get("materia_asignada")
    trayecto = request.POST.get("id_trayecto")
    docente = request.POST.get("seleccion_docente")
    perfil = request.POST.get("perfil")
    cedula = request.session.get("cedula_usuario")

    notas_raw = request.POST.get("notas")
    motivo = (
        request.POST.get(
            "motivo",
            "Modificación de nota de reparación"
        ).strip()
        or "Modificación de nota de reparación"
    )

    if not nucleo:
        return JsonResponse({
            "estado": "fallo",
            "title": "Dato faltante",
            "icon": "warning",
            "descripcion": "Debe seleccionar un núcleo."
        })

    if not pnf:
        return JsonResponse({
            "estado": "fallo",
            "title": "Dato faltante",
            "icon": "warning",
            "descripcion": "Debe seleccionar un PNF."
        })

    if not materia_asignacion:
        return JsonResponse({
            "estado": "fallo",
            "title": "Dato faltante",
            "icon": "warning",
            "descripcion": "Debe seleccionar una materia asignada."
        })

    if not trayecto:
        return JsonResponse({
            "estado": "fallo",
            "title": "Dato faltante",
            "icon": "warning",
            "descripcion": "Debe seleccionar un trayecto académico."
        })

    if not perfil:
        return JsonResponse({
            "estado": "fallo",
            "title": "Dato faltante",
            "icon": "warning",
            "descripcion": "Debe seleccionar un perfil."
        })

    if not cedula:
        return JsonResponse({
            "estado": "fallo",
            "title": "Sesión inválida",
            "icon": "warning",
            "descripcion": "No se pudo identificar al usuario autenticado."
        })

    if perfil not in ["DOCENTE", "CONTROL_ESTUDIO"]:
        return JsonResponse({
            "estado": "fallo",
            "title": "Acceso denegado",
            "icon": "error",
            "descripcion": "El perfil seleccionado no tiene permisos para modificar notas."
        })

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

        # Validar docente según el perfil
        if perfil == "DOCENTE":
            docente_obj = Docente.objects.filter(
                usuario__cedula_identidad=cedula,
                nucleo_id=nucleo,
                pnf_id=pnf,
                activo=True
            ).first()

        else:
            if not docente:
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Atención",
                    "icon": "warning",
                    "descripcion": "Debe seleccionar un docente."
                })

            tiene_permiso = ControlEstudio.objects.filter(
                usuario__cedula_identidad=cedula,
                nucleo_id=nucleo,
                activo=True
            ).exists()

            if not tiene_permiso:
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Acceso denegado",
                    "icon": "error",
                    "descripcion": "No tiene permisos para modificar notas en este núcleo."
                })

            docente_obj = Docente.objects.filter(
                usuario__cedula_identidad=docente,
                nucleo_id=nucleo,
                pnf_id=pnf,
                activo=True
            ).first()

        if not docente_obj:
            return JsonResponse({
                "estado": "fallo",
                "title": "Docente no válido",
                "icon": "error",
                "descripcion": "No se encontró un docente activo para el núcleo y PNF seleccionados."
            })

        # Validar asignación de la materia
        asignacion_valida = DocenteAsignadoMateria.objects.filter(
            docente=docente_obj,
            docente__nucleo_id=nucleo,
            docente__pnf_id=pnf,
            docente__activo=True,
            activo=True,
            materia_asignada_id=materia_asignacion,
            materia_asignada__activo=True,
            materia_asignada__materia__activa=True,
            materia_asignada__materia__id_pnf_id=pnf,
            materia_asignada__materia__id_trayecto_id=trayecto
        ).exists()

        if not asignacion_valida:
            return JsonResponse({
                "estado": "fallo",
                "title": "Materia no autorizada",
                "icon": "error",
                "descripcion": "El docente seleccionado no tiene asignada esta materia en el trayecto indicado."
            })

        # Validar estructura de las notas recibidas
        ids_reparaciones = []

        for item in lista_notas:
            if not isinstance(item, dict) or not item.get("id_reparacion"):
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Datos incompletos",
                    "icon": "warning",
                    "descripcion": "Cada nota debe incluir un identificador de reparación válido."
                })

            ids_reparaciones.append(item["id_reparacion"])

        if len(ids_reparaciones) != len(set(map(str, ids_reparaciones))):
            return JsonResponse({
                "estado": "fallo",
                "title": "Registros duplicados",
                "icon": "warning",
                "descripcion": "La solicitud contiene reparaciones duplicadas."
            })

        with transaction.atomic():
            # Consultar y bloquear las reparaciones autorizadas
            reparaciones = list(
                Reparacion.objects
                .select_for_update()
                .filter(
                    id_reparacion__in=ids_reparaciones,
                    evaluacion_reparacion__materia_asignacion_id=materia_asignacion,
                    evaluacion_reparacion__materia_asignacion__materia__id_trayecto_id=trayecto,
                    evaluacion_reparacion__materia_asignacion__materia__id_pnf_id=pnf,
                    evaluacion_reparacion__materia_asignacion__docentes__docente=docente_obj,
                    evaluacion_reparacion__materia_asignacion__docentes__activo=True,
                    evaluacion_reparacion__materia_asignacion__activo=True,
                    evaluacion_reparacion__materia_asignacion__materia__activa=True,
                    evaluacion_reparacion__activo=True,
                    estudiante__nucleo_id=nucleo,
                    estudiante__pnf_id=pnf
                )
            )

            reparaciones_por_id = {
                str(rep.id_reparacion): rep
                for rep in reparaciones
            }

            if len(reparaciones_por_id) != len(set(map(str, ids_reparaciones))):
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Registros no autorizados",
                    "icon": "error",
                    "descripcion": "Una o más reparaciones no pertenecen a la materia seleccionada o no están autorizadas para este docente."
                })

            # Validar las notas antes de guardar cualquier cambio
            notas_validadas = []

            for item in lista_notas:
                id_reparacion = str(item["id_reparacion"])

                try:
                    nueva_calificacion = Decimal(
                        str(item.get("calificacion", ""))
                    )
                except (InvalidOperation, TypeError, ValueError):
                    raise ValueError(
                        "Una de las calificaciones no tiene un valor válido."
                    )

                if not nueva_calificacion.is_finite():
                    raise ValueError(
                        "Las calificaciones deben ser números válidos."
                    )

                if not Decimal("0") <= nueva_calificacion <= Decimal("20"):
                    raise ValueError(
                        f"La nota {nueva_calificacion} está fuera del rango permitido (0-20)."
                    )

                notas_validadas.append((
                    reparaciones_por_id[id_reparacion],
                    nueva_calificacion
                ))

            # Identificar cambios reales
            cambios = []

            for reparacion, nueva_calificacion in notas_validadas:
                nota_anterior = reparacion.calificacion
                nota_anterior_decimal = (
                    nota_anterior
                    if nota_anterior is not None
                    else Decimal("0")
                )

                estado_anterior = reparacion.estado
                estado_nuevo = (
                    "APROBADO"
                    if nueva_calificacion >= Decimal("12")
                    else "REPROBADO"
                )

                if (
                    nota_anterior_decimal != nueva_calificacion
                    or estado_anterior != estado_nuevo
                ):
                    cambios.append({
                        "reparacion": reparacion,
                        "nota_anterior": nota_anterior_decimal,
                        "nota_nueva": nueva_calificacion,
                        "estado_anterior": estado_anterior,
                        "estado_nuevo": estado_nuevo
                    })

            if not cambios:
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Sin cambios",
                    "icon": "info",
                    "descripcion": "No se detectaron modificaciones en las notas."
                })

            # Crear historial y actualizar reparaciones
            evaluacion = cambios[0]["reparacion"].evaluacion_reparacion

            modificacion = ModificacionReparacion.objects.create(
                evaluacion_reparacion=evaluacion,
                motivo=motivo
            )

            fecha_actual = timezone.localdate()

            for cambio in cambios:
                reparacion = cambio["reparacion"]

                DetalleModificacionReparacion.objects.create(
                    modificacion=modificacion,
                    reparacion=reparacion,
                    nota_anterior=cambio["nota_anterior"],
                    nota_nueva=cambio["nota_nueva"],
                    estado_anterior=cambio["estado_anterior"],
                    estado_nuevo=cambio["estado_nuevo"]
                )

                reparacion.calificacion = cambio["nota_nueva"]
                reparacion.estado = cambio["estado_nuevo"]
                reparacion.fecha_reparacion = fecha_actual

                reparacion.save(update_fields=[
                    "calificacion",
                    "estado",
                    "fecha_reparacion"
                ])

        return JsonResponse({
            "estado": "exito",
            "title": "Modificación exitosa",
            "icon": "success",
            "descripcion": "Las notas fueron actualizadas y el historial se guardó correctamente.",
            "total_modificadas": len(cambios)
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
            "descripcion": f"Ocurrió un error al modificar las notas de reparación {e}."
        })