import logging

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_POST

from inicio_sesion.models import Estudiante
from documentos.services.constancias import construir_constancia_estudios
from documentos.services.generador_pdf import crear_documento_institucional
from .verificar_documentos import obtener_usuario_sesion, puede_emitir_reporte

logger = logging.getLogger(__name__)

@require_POST
def emitir_constancia_estudios(request, id_estudiante):
    usuario = obtener_usuario_sesion(request)
    if not usuario:
        return JsonResponse({"estado": "fallo", "mensaje": "La sesión ha expirado."}, status=401)

    estudiante = get_object_or_404(
        Estudiante.objects.select_related("usuario", "nucleo", "pnf"),
        id_estudiante=id_estudiante,
    )
    if not puede_emitir_reporte(request, usuario, estudiante):
        return JsonResponse({"estado": "fallo", "mensaje": "No tienes autorización para emitir esta constancia."}, status=403)

    try:
        documento = crear_documento_institucional(
            request=request,
            tipo_documento="CONSTANCIA_ESTUDIOS",
            titulo="Constancia de estudios",
            contenido=construir_constancia_estudios(estudiante),
            emitido_por=usuario,
            datos_documento={
                "estudiante_id": estudiante.pk,
                "nucleo_id": estudiante.nucleo_id,
                "pnf_id": estudiante.pnf_id,
            },
        )
        return JsonResponse({
            "estado": "exito",
            "mensaje": "Constancia generada correctamente.",
            "codigo_documento": documento.codigo_documento,
            "url_descarga": reverse("documentos:descargar_documento", kwargs={"identificador": documento.identificador}),
        })
    except Exception:
        return JsonResponse({"estado": "fallo", "mensaje": "No fue posible generar la constancia."}, status=500)
