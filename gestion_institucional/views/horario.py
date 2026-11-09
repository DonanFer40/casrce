import logging

from django.db import IntegrityError, transaction
from django.db.models import Q
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from documentos.models import DocumentoInstitucional
from documentos.services.generador_pdf import crear_documento_institucional
from documentos.services.reportes_pdf import construir_reporte_horario
from inicio_sesion.models import (
    AulaAcademica,
    AulaEstudiante,
    CoordinadorPNF,
    Estudiante,
    HorarioAcademico,
    Materia,
    MateriaAsignada,
    PeriodoAcademico,
    PeriodoAcademicoMateria,
    TrayectoAcademico,
    Cuenta,
)
from inicio_sesion.horarios import DIAS_SEMANA, FRANJAS_HORARIAS


logger = logging.getLogger(__name__)


def _usuario_actual(request):
    id_cuenta = request.session.get("id_cuenta")
    if not id_cuenta:
        return None
    cuenta = Cuenta.objects.select_related("id_usuario").filter(
        id_cuenta=id_cuenta
    ).first()
    return cuenta.id_usuario if cuenta else None


def _coordinaciones(usuario):
    return list(CoordinadorPNF.objects.filter(
        usuario=usuario,
        activo=True,
        nucleo__isnull=False,
        pnf__isnull=False,
    ).values_list("nucleo_id", "pnf_id"))


def _aulas_coordinadas(usuario):
    coordinaciones = _coordinaciones(usuario)
    filtro = Q()
    for nucleo_id, pnf_id in coordinaciones:
        filtro |= Q(id_nucleo_id=nucleo_id, id_pnf_id=pnf_id)
    return AulaAcademica.objects.filter(filtro) if filtro else AulaAcademica.objects.none()


def _franjas_contexto():
    return [
        {
            "indice": indice,
            "inicio": inicio,
            "fin": fin,
            "etiqueta": (
                f"{inicio.strftime('%I:%M').lstrip('0')} - "
                f"{fin.strftime('%I:%M').lstrip('0')}"
            ),
        }
        for indice, (inicio, fin) in enumerate(FRANJAS_HORARIAS)
    ]


def _json_sin_permiso():
    return JsonResponse(
        {"success": False, "mensaje": "Solo Coordinación de PNF puede gestionar horarios."},
        status=403,
    )


@require_GET
def registrar_horario(request):
    usuario = _usuario_actual(request)
    if usuario is None:
        return redirect("inicio_sesion")
    if not _coordinaciones(usuario):
        return HttpResponseForbidden("No tienes permiso para registrar horarios.")
    return render(
        request,
        "Roles/Coordinador_PNF/horario/registrar_horario.html",
        {
            "franjas": _franjas_contexto(),
            "dias": DIAS_SEMANA,
        },
    )


@require_GET
def horario_estudiante(request):
    usuario = _usuario_actual(request)
    if usuario is None:
        return redirect("inicio_sesion")
    if not Estudiante.objects.filter(usuario=usuario).exists():
        return HttpResponseForbidden("Este horario solo está disponible para estudiantes.")

    fecha = timezone.localdate()
    matriculas = AulaEstudiante.objects.filter(
        estatus__estudiante__usuario=usuario,
        estado="Curso",
        fecha_inicio__lte=fecha,
    ).filter(
        Q(fecha_final__isnull=True) | Q(fecha_final__gte=fecha)
    ).select_related(
        "aula__id_nucleo",
        "aula__id_pnf",
        "aula__id_seccion",
        "estatus__trayecto",
    )
    if not matriculas.exists():
        return render(
            request,
            "Roles/Estudiante/horario_academico.html",
            {"horarios": [], "sin_matricula": True},
        )

    filtro = Q()
    for matricula in matriculas:
        filtro |= Q(
            aula_id=matricula.aula_id,
            trayecto_id=matricula.estatus.trayecto_id,
        )

    registros = HorarioAcademico.objects.filter(filtro).select_related(
        "aula__id_nucleo",
        "aula__id_pnf",
        "aula__id_seccion",
        "trayecto",
        "periodo",
        "materia_asignada__materia",
    ).prefetch_related(
        "materia_asignada__docentes__docente__usuario",
    )
    por_aula_periodo = {}
    for horario in registros:
        llave = (
            horario.aula_id,
            horario.trayecto_id,
            horario.periodo_id,
        )
        if llave not in por_aula_periodo:
            por_aula_periodo[llave] = {
                "aula": horario.aula,
                "trayecto": horario.trayecto,
                "periodo": horario.periodo,
                "celdas": {},
            }
        docentes = [
            f"{asignacion.docente.usuario.nombres} {asignacion.docente.usuario.apellidos}"
            for asignacion in horario.materia_asignada.docentes.all()
            if asignacion.activo and asignacion.docente.activo
        ]
        por_aula_periodo[llave]["celdas"][
            (horario.hora_inicio, horario.dia_semana)
        ] = {
            "materia": horario.materia_asignada.materia.nombre,
            "docentes": docentes,
        }

    horarios = []
    for grupo in por_aula_periodo.values():
        grupo["filas"] = [
            {
                "etiqueta": (
                    f"{inicio.strftime('%I:%M').lstrip('0')} - "
                    f"{fin.strftime('%I:%M').lstrip('0')}"
                ),
                "celdas": [
                    grupo["celdas"].get((inicio, dia), None)
                    for dia, _ in DIAS_SEMANA
                ],
            }
            for inicio, fin in FRANJAS_HORARIAS
        ]
        horarios.append(grupo)

    return render(
        request,
        "Roles/Estudiante/horario_academico.html",
        {
            "horarios": horarios,
            "dias": DIAS_SEMANA,
            "sin_matricula": False,
        },
    )


@require_GET
def trayectos_horario(request):
    usuario = _usuario_actual(request)
    if usuario is None:
        return JsonResponse({"success": False}, status=401)
    if not _coordinaciones(usuario):
        return _json_sin_permiso()
    pnf_ids = _aulas_coordinadas(usuario).values_list("id_pnf_id", flat=True)
    ids_trayecto = Materia.objects.filter(
        id_pnf_id__in=pnf_ids,
        asignaciones__activo=True,
    ).values_list("id_trayecto_id", flat=True).distinct()
    trayectos = list(
        TrayectoAcademico.objects.filter(
            id_periodo_academico__in=ids_trayecto
        ).values("id_periodo_academico", "nombre")
    )
    return JsonResponse({"trayectos": trayectos})


@require_GET
def aulas_horario(request):
    usuario = _usuario_actual(request)
    if usuario is None:
        return JsonResponse({"success": False}, status=401)
    if not _coordinaciones(usuario):
        return _json_sin_permiso()
    aulas = _aulas_coordinadas(usuario).select_related(
        "id_nucleo",
        "id_pnf",
        "id_seccion",
    ).order_by("id_nucleo__municipio", "id_pnf__pnf", "id_seccion__nombre")
    return JsonResponse({
        "aulas": [
            {
                "id_aula": aula.pk,
                "nombre_aula": (
                    f"{aula.nombre_aula} · {aula.id_nucleo.municipio} · "
                    f"{aula.id_pnf.pnf} · Sección {aula.id_seccion.nombre}"
                ),
                "id_seccion": aula.id_seccion_id,
            }
            for aula in aulas
        ]
    })


@require_POST
def periodos_horario(request):
    usuario = _usuario_actual(request)
    if usuario is None:
        return JsonResponse({"success": False}, status=401)
    if not _coordinaciones(usuario):
        return _json_sin_permiso()
    trayecto_id = request.POST.get("trayecto")
    aula = get_object_or_404(
        _aulas_coordinadas(usuario),
        pk=request.POST.get("aula"),
    )
    periodos = PeriodoAcademico.objects.filter(
        materias__materia__id_trayecto_id=trayecto_id,
        materias__materia__id_pnf_id=aula.id_pnf_id,
        materias__materia__activa=True,
        materias__materia__asignaciones__activo=True,
    ).distinct().order_by("nombre")
    return JsonResponse({
        "periodos_academicos": [
            {"id": periodo.pk, "nombre": periodo.nombre}
            for periodo in periodos
        ]
    })


@require_POST
def materias_horario(request):
    usuario = _usuario_actual(request)
    if usuario is None:
        return JsonResponse({"success": False}, status=401)
    if not _coordinaciones(usuario):
        return _json_sin_permiso()
    aula = get_object_or_404(
        _aulas_coordinadas(usuario),
        pk=request.POST.get("aula"),
    )
    periodo_id = request.POST.get("periodo_academico")
    asignaciones = MateriaAsignada.objects.filter(
        activo=True,
        materia__activa=True,
        materia__id_trayecto_id=request.POST.get("trayecto"),
        materia__id_pnf_id=aula.id_pnf_id,
        materia__periodos_academicos__periodo_id=periodo_id,
    ).select_related("materia").order_by("materia__nombre").distinct()
    return JsonResponse({
        "materias": [
            {
                "id_materia_asignada": asignacion.pk,
                "materia": {"nombre": asignacion.materia.nombre},
            }
            for asignacion in asignaciones
        ]
    })


@require_GET
def horario_existente(request):
    usuario = _usuario_actual(request)
    if usuario is None:
        return JsonResponse({"success": False}, status=401)
    if not _coordinaciones(usuario):
        return _json_sin_permiso()
    aula = get_object_or_404(
        _aulas_coordinadas(usuario),
        pk=request.GET.get("aula"),
    )
    trayecto = get_object_or_404(
        TrayectoAcademico,
        pk=request.GET.get("trayecto"),
    )
    periodo = get_object_or_404(
        PeriodoAcademico,
        pk=request.GET.get("periodo"),
    )
    if not PeriodoAcademicoMateria.objects.filter(
        periodo=periodo,
        materia__id_trayecto=trayecto,
        materia__id_pnf=aula.id_pnf,
    ).exists():
        return JsonResponse(
            {"success": False, "mensaje": "El período no corresponde al trayecto y PNF."},
            status=400,
        )
    horarios = HorarioAcademico.objects.filter(
        aula=aula,
        periodo=periodo,
        trayecto=trayecto,
    ).values_list("hora_inicio", "dia_semana", "materia_asignada_id")
    return JsonResponse({
        "success": True,
        "horarios": [
            {
                "franja": next(
                    (
                        indice
                        for indice, (inicio, fin) in enumerate(FRANJAS_HORARIAS)
                        if inicio == hora_inicio
                    ),
                    None,
                ),
                "dia": next(
                    indice for indice, (codigo, _) in enumerate(DIAS_SEMANA)
                    if codigo == dia
                ),
                "materia": materia_id,
            }
            for hora_inicio, dia, materia_id in horarios
            if any(inicio == hora_inicio for inicio, _ in FRANJAS_HORARIAS)
        ],
    })


def _crear_documento_horario(request, usuario, aula, periodo, trayecto):
    horarios = list(
        HorarioAcademico.objects.filter(
            aula=aula,
            periodo=periodo,
            trayecto=trayecto,
        ).select_related("materia_asignada__materia", "aula").prefetch_related(
            "materia_asignada__docentes__docente__usuario",
        )
    )
    DocumentoInstitucional.objects.filter(
        tipo_documento="HORARIO_ACADEMICO",
        datos_documento__aula_id=aula.pk,
        datos_documento__periodo_id=periodo.pk,
        datos_documento__trayecto_id=trayecto.pk,
        estado="VIGENTE",
    ).update(
        estado="ANULADO",
        fecha_anulacion=timezone.now(),
        motivo_anulacion="Reemplazado por un horario actualizado.",
    )
    return crear_documento_institucional(
        request=request,
        tipo_documento="HORARIO_ACADEMICO",
        titulo=f"Horario académico - {aula.id_nucleo.municipio}",
        contenido=construir_reporte_horario(
            horarios,
            f"Horario académico · {aula.id_nucleo.municipio} · "
            f"{aula.id_pnf.pnf} · Sección {aula.id_seccion.nombre}",
        ),
        emitido_por=usuario,
        datos_documento={
            "aula_id": aula.pk,
            "nucleo_id": aula.id_nucleo_id,
            "pnf_id": aula.id_pnf_id,
            "periodo_id": periodo.pk,
            "trayecto_id": trayecto.pk,
        },
    )


@require_POST
def guardar_horario(request):
    usuario = _usuario_actual(request)
    if usuario is None:
        return JsonResponse({
            "estado": "fallo",
            "descripcion": "La sesión expiró. Inicia sesión nuevamente.",
        }, status=401)

    if not _coordinaciones(usuario):
        return JsonResponse(
            {"estado": "fallo", "descripcion": "Solo Coordinación de PNF puede gestionar horarios."},
            status=403,
        )

    aula = get_object_or_404(
        _aulas_coordinadas(usuario),
        pk=request.POST.get("aula"),
    )
    trayecto = get_object_or_404(
        TrayectoAcademico,
        pk=request.POST.get("trayecto"),
    )
    periodo = get_object_or_404(
        PeriodoAcademico,
        pk=request.POST.get("periodo_academico"),
    )
    if not PeriodoAcademicoMateria.objects.filter(
        periodo=periodo,
        materia__id_trayecto=trayecto,
        materia__id_pnf=aula.id_pnf,
    ).exists():
        return JsonResponse({
            "estado": "fallo",
            "descripcion": "El período no corresponde al PNF y trayecto seleccionados.",
        }, status=400)

    filas = []
    for indice, (inicio, fin) in enumerate(FRANJAS_HORARIAS):
        materias = [
            request.POST.get(f"materia_{indice}_{dia}", "")
            for dia in range(5)
        ]
        for dia, materia_id in enumerate(materias):
            if not materia_id:
                continue
            asignacion = MateriaAsignada.objects.filter(
                pk=materia_id,
                activo=True,
                materia__activa=True,
                materia__id_trayecto=trayecto,
                materia__id_pnf=aula.id_pnf,
                materia__periodos_academicos__periodo=periodo,
            ).first()
            if asignacion is None:
                return JsonResponse({
                    "estado": "fallo",
                    "descripcion": "Una materia seleccionada no corresponde al aula.",
                }, status=400)
            filas.append({
                "trayecto": trayecto,
                "periodo": periodo,
                "aula": aula,
                "materia_asignada": asignacion,
                "dia_semana": DIAS_SEMANA[dia][0],
                "hora_inicio": inicio,
                "hora_final": fin,
                "registrado_por": usuario,
            })

    if not filas:
        return JsonResponse({
            "estado": "fallo",
            "descripcion": "Selecciona al menos una materia para el horario.",
        }, status=400)

    try:
        with transaction.atomic():
            HorarioAcademico.objects.filter(
                aula=aula,
                periodo=periodo,
                trayecto=trayecto,
            ).delete()
            for fila in filas:
                HorarioAcademico.objects.create(**fila)
            documento = _crear_documento_horario(
                request,
                usuario,
                aula,
                periodo,
                trayecto,
            )
    except IntegrityError:
        logger.exception("Conflicto al guardar el horario del aula %s.", aula.pk)
        return JsonResponse({
            "estado": "fallo",
            "descripcion": "El horario se cruza con otra clase del mismo período.",
        }, status=409)
    except Exception:
        logger.exception("No se pudo registrar el horario académico.")
        return JsonResponse({
            "estado": "fallo",
            "descripcion": "No se pudo generar y registrar el horario.",
        }, status=500)

    return JsonResponse({
        "estado": "exito",
        "title": "Horario registrado",
        "icon": "success",
        "descripcion": "El horario quedó guardado y su PDF incluye un QR de verificación.",
        "url_descarga": reverse(
            "documentos:descargar_documento",
            kwargs={"identificador": documento.identificador},
        ),
    })
