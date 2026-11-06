import json
import logging
from io import BytesIO

from django.conf import settings
from PIL import Image, UnidentifiedImageError
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

DOCUMENTOS_ESTUDIANTE = {
    "CI_estudiante": ("Cédula de identidad", "documento oficial de identidad personal venezolano"),
    "TBachiller_estudiante": ("Título de bachiller", "título o diploma de culminación de educación media"),
    "SNotas_estudiante": ("Sábana de notas", "documento académico con calificaciones certificadas de educación media"),
    "OPSU_estudiante": ("Documento OPSU", "comprobante, constancia o documento de registro de OPSU"),
}
MAX_BYTES_POR_IMAGEN = 4 * 1024 * 1024
FORMATOS_PERMITIDOS = {"JPEG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp"}


class ErrorVerificacionGemini(Exception):
    """Fallo del servicio de revisión automática o de su respuesta."""


class ErrorArchivoDocumento(ErrorVerificacionGemini):
    """Archivo ausente, dañado, demasiado grande o con formato no permitido."""


def _leer_y_validar_imagen(archivo):
    if archivo.size > MAX_BYTES_POR_IMAGEN:
        raise ErrorArchivoDocumento(
            f"El archivo «{archivo.name}» supera el máximo permitido de 4 MB."
        )
    try:
        archivo.seek(0)
        contenido = archivo.read()
        archivo.seek(0)
        imagen = Image.open(BytesIO(contenido))
        formato = imagen.format
        imagen.verify()
    except (UnidentifiedImageError, OSError, ValueError):
        raise ErrorArchivoDocumento(
            f"El archivo «{archivo.name}» no es una imagen válida o está dañado."
        )

    mime_type = FORMATOS_PERMITIDOS.get(formato)
    if not mime_type:
        raise ErrorArchivoDocumento(
            f"El formato de «{archivo.name}» no está permitido. Utiliza JPG, PNG o WEBP."
        )
    return contenido, mime_type


def _analizar_documento(client, model, nombre_documento, descripcion, contenido, mime_type):
    prompt = f"""
Clasifica preliminarmente esta imagen para un registro estudiantil.
Documento esperado: {nombre_documento}.
Descripción: {descripcion}.

Determina si parece corresponder al tipo solicitado y si es suficientemente legible.
No certifiques autenticidad, legalidad, vigencia, firmas, sellos ni legitimidad.
No inventes información. Si existe duda razonable, utiliza REVISION_MANUAL.
Responde únicamente JSON válido con:
{{
  "estado": "VALIDO | NO_VALIDO | REVISION_MANUAL",
  "tipo_detectado": "descripción breve",
  "legible": true,
  "motivo": "explicación breve en español"
}}

VALIDO: parece ser el documento esperado y es legible.
NO_VALIDO: claramente es otro documento, está vacío, dañado o es inservible.
REVISION_MANUAL: no se puede determinar con suficiente confianza.
"""
    response = client.models.generate_content(
        model=model,
        contents=[
            prompt,
            types.Part.from_bytes(data=contenido, mime_type=mime_type),
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.1,
        ),
    )
    if not response.text:
        raise ErrorVerificacionGemini(
            f"Gemini no devolvió una respuesta para «{nombre_documento}»."
        )
    try:
        datos = json.loads(response.text)
    except (json.JSONDecodeError, TypeError):
        datos = {}

    estado = str(datos.get("estado", "")).upper()
    if estado not in {"VALIDO", "NO_VALIDO", "REVISION_MANUAL"}:
        estado = "REVISION_MANUAL"

    legible_dato = datos.get("legible", False)
    legible = (
        legible_dato is True
        or str(legible_dato).strip().lower() in {"true", "1", "si", "sí"}
    )

    return {
        "estado": estado,
        "tipo_detectado": str(datos.get("tipo_detectado", "No determinado"))[:200],
        "legible": legible,
        "motivo": str(datos.get("motivo", "No se obtuvo una observación clara."))[:500],
    }


def verificar_documentos_estudiante(archivos):
    api_key = getattr(settings, "GEMINI_API_KEY", None)
    model = getattr(settings, "GEMINI_MODEL", "gemini-2.5-flash")
    if not api_key:
        raise ErrorVerificacionGemini("La API de Gemini no está configurada en el servidor.")

    resultados = {}
    try:
        with genai.Client(api_key=api_key) as client:
            for campo, (nombre, descripcion) in DOCUMENTOS_ESTUDIANTE.items():
                archivo = archivos.get(campo)
                if not archivo:
                    resultados[campo] = {
                        "nombre": nombre,
                        "estado": "NO_VALIDO",
                        "tipo_detectado": "No recibido",
                        "legible": False,
                        "motivo": "No se recibió el archivo obligatorio.",
                    }
                    continue
                contenido, mime_type = _leer_y_validar_imagen(archivo)
                resultados[campo] = {
                    "nombre": nombre,
                    **_analizar_documento(
                        client, model, nombre, descripcion, contenido, mime_type
                    ),
                }
    except ErrorVerificacionGemini:
        raise
    except Exception as exc:
        logger.exception("Error al comunicarse con Gemini")
        raise ErrorVerificacionGemini(
            "No fue posible completar la verificación automática. Inténtalo nuevamente."
        ) from exc

    return resultados
