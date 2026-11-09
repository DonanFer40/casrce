
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, FileResponse
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.core.exceptions import ObjectDoesNotExist

from inicio_sesion.models import (
    Cuenta,
    Estudiante,
    DirectorGeneral,
    ControlEstudio,
    CoordinadorPNF,
)

from documentos.models import DocumentoInstitucional

from documentos.services.generador_pdf import (
    crear_documento_institucional,
)

from documentos.services.reporte_academico import (
    construir_contenido_reporte_academico,
)


# =========================================================
# SESIÓN Y AUTENTICACIÓN
# =========================================================

def obtener_usuario_sesion(request):

    id_cuenta = request.session.get("id_cuenta")

    if not id_cuenta:
        return None

    try:
        cuenta = (
            Cuenta.objects
            .select_related("id_usuario")
            .get(id_cuenta=id_cuenta)
        )

        return cuenta.id_usuario

    except Cuenta.DoesNotExist:
        return None


def obtener_roles_sesion(request):

    roles = request.session.get("rol", [])

    if isinstance(roles, str):
        return [roles]

    if not isinstance(roles, list):
        return []

    return roles


# =========================================================
# VALIDACIÓN DE PERMISOS PARA EMITIR REPORTES
# =========================================================

def puede_emitir_reporte(request, usuario, estudiante):

    roles = obtener_roles_sesion(request)

    if "Estudiante" in roles and Estudiante.objects.filter(
        id_estudiante=estudiante.id_estudiante,
        usuario=usuario,
    ).exists():
        return True

    # -----------------------------------------------------
    # DIRECTOR GENERAL
    # -----------------------------------------------------

    if "Director General" in roles:

        autorizado = DirectorGeneral.objects.filter(
            usuario=usuario,
            nucleo_id=estudiante.nucleo_id,
        ).exists()

        if autorizado:
            return True

    # -----------------------------------------------------
    # CONTROL DE ESTUDIO
    # -----------------------------------------------------

    if "Control de Estudio" in roles:

        autorizado = ControlEstudio.objects.filter(
            usuario=usuario,
            nucleo_id=estudiante.nucleo_id,
            activo=True,
        ).exists()

        if autorizado:
            return True

    # -----------------------------------------------------
    # COORDINADOR PNF
    # -----------------------------------------------------

    if "Coordinador PNF" in roles:

        autorizado = CoordinadorPNF.objects.filter(
            usuario=usuario,
            nucleo_id=estudiante.nucleo_id,
            pnf_id=estudiante.pnf_id,
            activo=True,
        ).exists()

        if autorizado:
            return True

    return False


# =========================================================
# VALIDACIÓN DE PERMISOS PARA CONSULTAR REPORTES
# =========================================================

def puede_consultar_reporte(
    request,
    usuario,
    estudiante,
    documento,
):

    roles = obtener_roles_sesion(request)

    datos = documento.datos_documento or {}

    id_estudiante_documento = datos.get("estudiante_id")

    # El documento debe corresponder al estudiante indicado.

    if str(id_estudiante_documento) != str(
        estudiante.id_estudiante
    ):
        return False

    # -----------------------------------------------------
    # ESTUDIANTE
    # -----------------------------------------------------

    if "Estudiante" in roles:

        pertenece_al_usuario = Estudiante.objects.filter(
            id_estudiante=estudiante.id_estudiante,
            usuario=usuario,
        ).exists()

        if pertenece_al_usuario:
            return True

    # -----------------------------------------------------
    # PERSONAL ADMINISTRATIVO
    # -----------------------------------------------------

    if puede_emitir_reporte(
        request,
        usuario,
        estudiante,
    ):
        return True

    return False


# =========================================================
# EMITIR REPORTE DE SITUACIÓN ACADÉMICA
# =========================================================

@require_POST
def emitir_reporte_academico(request, id_estudiante):

    usuario = obtener_usuario_sesion(request)

    if not usuario:

        return JsonResponse({
            "estado": "fallo",
            "mensaje": "La sesión ha expirado. Inicia sesión nuevamente.",
        }, status=401)

    estudiante = get_object_or_404(
        Estudiante.objects.select_related(
            "usuario",
            "nucleo",
            "pnf",
        ),
        id_estudiante=id_estudiante,
    )

    # -----------------------------------------------------
    # VALIDAR PERMISOS
    # -----------------------------------------------------

    if not puede_emitir_reporte(
        request,
        usuario,
        estudiante,
    ):

        return JsonResponse({
            "estado": "fallo",
            "mensaje": (
                "No tienes autorización para emitir "
                "reportes académicos de este estudiante."
            ),
        }, status=403)

    # -----------------------------------------------------
    # CONSTRUIR CONTENIDO DEL REPORTE
    # -----------------------------------------------------

    try:

        contenido = construir_contenido_reporte_academico(
            estudiante
        )

        documento = crear_documento_institucional(
            request=request,
            tipo_documento="REPORTE_ACADEMICO",
            titulo="Reporte de Situación Académica",
            contenido=contenido,
            emitido_por=usuario,
            datos_documento={
                "estudiante_id": estudiante.id_estudiante,
                "nucleo_id": estudiante.nucleo_id,
                "pnf_id": estudiante.pnf_id,
            },
        )

        url_descarga = reverse(
            "documentos:descargar_documento",
            kwargs={
                "identificador": documento.identificador,
            },
        )

        return JsonResponse({
            "estado": "exito",
            "mensaje": "El reporte académico fue generado correctamente.",
            "codigo_documento": documento.codigo_documento,
            "url_descarga": url_descarga,
        })

    except Exception:

        return JsonResponse({
            "estado": "fallo",
            "mensaje": (
                "Ocurrió un error al generar el reporte académico."
            ),
        }, status=500)


@require_POST
def emitir_reporte_academico_actual(request):
    try:
        id_estudiante = int(request.POST.get("estudiante_id", ""))
    except (TypeError, ValueError):
        return JsonResponse({
            "estado": "fallo",
            "mensaje": "Selecciona un perfil estudiantil válido.",
        }, status=400)
    return emitir_reporte_academico(request, id_estudiante)


# =========================================================
# DESCARGAR DOCUMENTO INSTITUCIONAL
# =========================================================

def descargar_documento(request, identificador):

    usuario = obtener_usuario_sesion(request)

    if not usuario:

        return JsonResponse({
            "estado": "fallo",
            "mensaje": "La sesión ha expirado. Inicia sesión nuevamente.",
        }, status=401)

    documento = get_object_or_404(
        DocumentoInstitucional,
        identificador=identificador,
    )

    if documento.estado != "VIGENTE":
        return JsonResponse({
            "estado": "fallo",
            "mensaje": "Este documento fue anulado y ya no está disponible.",
        }, status=410)

    # -----------------------------------------------------
    # COMPROBAR QUE EXISTA EL ARCHIVO
    # -----------------------------------------------------

    if not documento.archivo_pdf:

        return JsonResponse({
            "estado": "fallo",
            "mensaje": "El documento no tiene un archivo PDF disponible.",
        }, status=404)

    # -----------------------------------------------------
    # VALIDAR TIPO DE DOCUMENTO
    # -----------------------------------------------------

    tipos_personales = {
        "REPORTE_ACADEMICO",
        "PLANILLA_INSCRIPCION",
        "CONSTANCIA_ESTUDIOS",
        "CONSTANCIA_INSCRIPCION",
    }
    tipos_estadisticos = {
        "REPORTE_MATRICULA",
        "REPORTE_INSCRIPCIONES",
        "REPORTE_EGRESADOS",
        "REPORTE_ESTUDIANTES_ANUALES",
        "REPORTE_PERSONAL",
    }
    if (
        documento.tipo_documento not in tipos_personales
        and documento.tipo_documento != "HORARIO_ACADEMICO"
        and documento.tipo_documento not in tipos_estadisticos
    ):

        return JsonResponse({
            "estado": "fallo",
            "mensaje": "Este tipo de documento no admite descarga desde esta ruta.",
        }, status=403)

    # -----------------------------------------------------
    # RECUPERAR ESTUDIANTE ASOCIADO AL DOCUMENTO
    # -----------------------------------------------------

    datos = documento.datos_documento or {}

    if documento.tipo_documento in tipos_estadisticos:
        if str(datos.get("generado_por_usuario_id")) != str(usuario.pk):
            return JsonResponse({
                "estado": "fallo",
                "mensaje": "Solo quien generó este reporte puede descargarlo.",
            }, status=403)
        return FileResponse(
            documento.archivo_pdf.open("rb"),
            as_attachment=True,
            filename=f"{documento.codigo_documento}.pdf",
            content_type="application/pdf",
        )

    if documento.tipo_documento == "HORARIO_ACADEMICO":
        if (
            str(datos.get("usuario_id")) != str(usuario.pk)
            and documento.emitido_por_id != usuario.pk
        ):
            return JsonResponse({
                "estado": "fallo",
                "mensaje": "Este horario no corresponde a tu cuenta.",
            }, status=403)
        return FileResponse(
            documento.archivo_pdf.open("rb"),
            as_attachment=True,
            filename=f"{documento.codigo_documento}.pdf",
            content_type="application/pdf",
        )

    id_estudiante = datos.get("estudiante_id")

    if not id_estudiante:

        return JsonResponse({
            "estado": "fallo",
            "mensaje": "No se pudo identificar al estudiante del documento.",
        }, status=403)

    estudiante = get_object_or_404(
        Estudiante.objects.select_related(
            "usuario",
            "nucleo",
            "pnf",
        ),
        id_estudiante=id_estudiante,
    )

    # -----------------------------------------------------
    # VALIDAR PERMISOS
    # -----------------------------------------------------

    if not puede_consultar_reporte(
        request,
        usuario,
        estudiante,
        documento,
    ):

        return JsonResponse({
            "estado": "fallo",
            "mensaje": "No tienes autorización para consultar este documento.",
        }, status=403)

    # -----------------------------------------------------
    # DESCARGAR PDF
    # -----------------------------------------------------

    return FileResponse(
        documento.archivo_pdf.open("rb"),
        as_attachment=True,
        filename=f"{documento.codigo_documento}.pdf",
        content_type="application/pdf",
    )


# =========================================================
# VERIFICACIÓN PÚBLICA DE DOCUMENTOS
# =========================================================

def verificar_documento(request, identificador):

    documento = get_object_or_404(
        DocumentoInstitucional,
        identificador=identificador,
    )

    return render(
        request,
        "documentos/verificar_documentos.html",
        {
            "documento": documento,
            "es_valido": documento.estado == "VIGENTE",
        }
    )
