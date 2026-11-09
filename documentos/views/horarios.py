import logging

from django.http import JsonResponse
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from documentos.services.generador_pdf import crear_documento_institucional
from documentos.services.reportes_pdf import construir_reporte_horario
from inicio_sesion.models import (
    AulaEstudiante,
    DocenteAsignadoMateria,
    Estudiante,
    HorarioAcademico,
)
from .verificar_documentos import obtener_usuario_sesion, obtener_roles_sesion


logger = logging.getLogger(__name__)


@require_POST
def emitir_horario_personal(request):
    usuario = obtener_usuario_sesion(request)
    if usuario is None:
        return JsonResponse(
            {"estado": "fallo", "mensaje": "La sesión ha expirado."},
            status=401,
        )

    roles = obtener_roles_sesion(request)
    hoy = timezone.localdate()
    horarios = HorarioAcademico.objects.none()
    perfil = None

    if "Estudiante" in roles:
        estudiante_ids = Estudiante.objects.filter(
            usuario=usuario,
        ).values_list("pk", flat=True)
        aulas_ids = AulaEstudiante.objects.filter(
            estatus__estudiante_id__in=estudiante_ids,
            estado="Curso",
            fecha_inicio__lte=hoy,
        ).filter(
            Q(fecha_final__isnull=True) | Q(fecha_final__gte=hoy)
        ).values_list("aula_id", flat=True)
        horarios = HorarioAcademico.objects.filter(aula_id__in=aulas_ids)
        perfil = "Estudiante"
    elif "Docente" in roles:
        asignaciones_ids = DocenteAsignadoMateria.objects.filter(
            docente__usuario=usuario,
            docente__activo=True,
            activo=True,
        ).values_list("materia_asignada_id", flat=True)
        horarios = HorarioAcademico.objects.filter(
            materia_asignada_id__in=asignaciones_ids
        )
        perfil = "Docente"
    else:
        return JsonResponse(
            {"estado": "fallo", "mensaje": "Este reporte está disponible para estudiantes y docentes."},
            status=403,
        )

    horarios = list(
        horarios.select_related(
            "materia_asignada__materia",
            "aula__id_nucleo",
            "aula__id_pnf",
            "aula__id_seccion",
            "periodo",
            "trayecto",
        ).order_by(
            "aula__id_nucleo__municipio",
            "aula__id_pnf__pnf",
            "aula__id_seccion__nombre",
            "hora_inicio",
        ).distinct()
    )
    if not horarios:
        return JsonResponse(
            {"estado": "fallo", "mensaje": "No hay un horario vigente asociado a tu cuenta."},
            status=404,
        )

    try:
        documento = crear_documento_institucional(
            request=request,
            tipo_documento="HORARIO_ACADEMICO",
            titulo=f"Horario académico personal · {perfil}",
            contenido=construir_reporte_horario(
                horarios,
                f"Horario académico personal · {perfil}",
            ),
            emitido_por=usuario,
            datos_documento={
                "usuario_id": usuario.pk,
                "perfil": perfil,
            },
        )
    except Exception:
        logger.exception("No se pudo emitir el horario personal.")
        return JsonResponse(
            {"estado": "fallo", "mensaje": "No fue posible generar el horario."},
            status=500,
        )

    return JsonResponse({
        "estado": "exito",
        "mensaje": "El horario quedó registrado y contiene un QR de verificación.",
        "codigo_documento": documento.codigo_documento,
        "url_descarga": reverse(
            "documentos:descargar_documento",
            kwargs={"identificador": documento.identificador},
        ),
    })
