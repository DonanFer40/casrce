
from pathlib import Path
import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from inicio_sesion.services.correos import procesar_html_correo


logger = logging.getLogger(__name__)


def enviar_planilla_inscripcion(*, contacto, documento, usuario):
    """
    Envía al estudiante su planilla institucional de inscripción
    como archivo PDF adjunto.

    Args:
        contacto: Registro de contacto del estudiante.
        documento: DocumentoInstitucional que contiene el PDF.
        usuario: Usuario propietario del registro.

    Returns:
        bool: True si Django reporta el envío del correo.
    """

    # ==========================================================
    # VALIDACIÓN DEL CORREO ELECTRÓNICO
    # ==========================================================

    correo_destinatario = (
        contacto.correo_electronico or ""
    ).strip()

    if not correo_destinatario:
        raise ValueError(
            "El estudiante no tiene un correo electrónico principal registrado."
        )

    # ==========================================================
    # VALIDACIÓN DEL DOCUMENTO
    # ==========================================================

    if not documento or not documento.archivo_pdf:
        raise ValueError(
            "No existe un archivo PDF asociado a la planilla de inscripción."
        )

    # ==========================================================
    # OBTENCIÓN DEL ARCHIVO PDF
    # ==========================================================

    try:
        documento.archivo_pdf.open("rb")
        archivo_pdf = documento.archivo_pdf.read()

    finally:
        if documento.archivo_pdf:
            documento.archivo_pdf.close()

    if not archivo_pdf:
        raise ValueError(
            "El archivo PDF de la planilla de inscripción está vacío."
        )

    nombre_archivo = Path(
        documento.archivo_pdf.name
    ).name

    # ==========================================================
    # DATOS PARA LA PLANTILLA
    # ==========================================================

    contexto = {
        "usuario": usuario,
        "contacto": contacto,
        "documento": documento,
        "nombre_estudiante": (
            f"{usuario.nombres} {usuario.apellidos}"
        ),
        "codigo_documento": documento.codigo_documento,
        "titulo_documento": documento.titulo,
        "fecha_emision": documento.fecha_emision,
    }

    # ==========================================================
    # GENERACIÓN DEL CONTENIDO HTML
    # ==========================================================

    html_mensaje = render_to_string(
        "documentos/email/planilla_inscripcion.html",
        contexto,
    )

    html_mensaje = procesar_html_correo(
        html_mensaje,
        "Estilos/Email/planilla_inscripcion.css",
    )

    mensaje_texto = strip_tags(html_mensaje)

    # ==========================================================
    # CONFIGURACIÓN DEL CORREO
    # ==========================================================

    asunto = (
        "CASRCE | Planilla de inscripción recibida"
    )

    remitente = settings.DEFAULT_FROM_EMAIL

    correo = EmailMultiAlternatives(
        subject=asunto,
        body=mensaje_texto,
        from_email=remitente,
        to=[correo_destinatario],
    )

    correo.attach_alternative(
        html_mensaje,
        "text/html",
    )

    # ==========================================================
    # ADJUNTAR PLANILLA PDF
    # ==========================================================

    correo.attach(
        nombre_archivo,
        archivo_pdf,
        "application/pdf",
    )

    # ==========================================================
    # ENVÍO DEL CORREO
    # ==========================================================

    try:

        resultado = correo.send(fail_silently=False)

        if resultado != 1:
            raise RuntimeError(
                "El servidor de correo no confirmó el envío del mensaje."
            )

        logger.info(
            "Planilla de inscripción enviada correctamente. "
            "Usuario: %s | Documento: %s | Destinatario: %s",
            usuario.cedula_identidad,
            documento.codigo_documento,
            correo_destinatario,
        )

        return True

    except Exception:

        logger.exception(
            "No se pudo enviar la planilla de inscripción. "
            "Usuario: %s | Documento: %s",
            usuario.cedula_identidad,
            documento.codigo_documento,
        )

        raise
