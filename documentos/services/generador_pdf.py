
from io import BytesIO
from xml.sax.saxutils import escape


from django.contrib.staticfiles import finders
from django.core.files.base import ContentFile
from django.db import transaction
from django.urls import reverse

from documentos.models import DocumentoInstitucional
from documentos.services.generador_qr import generar_qr_png

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
)


# =========================================================
# PALETA INSTITUCIONAL CASRCE
# =========================================================

AZUL_PROFUNDO = colors.HexColor("#0F172A")
AZUL_CARD = colors.HexColor("#1E293B")
AZUL_HOVER = colors.HexColor("#2563EB")

ROJO_ACENTO = colors.HexColor("#DC2626")
ROJO_SUAVE = colors.HexColor("#FEF2F2")

BLANCO = colors.HexColor("#FFFFFF")
FONDO_PAGINA = colors.HexColor("#F8FAFC")
BORDE = colors.HexColor("#E2E8F0")

TEXTO_PRINCIPAL = colors.HexColor("#0F172A")
TEXTO_SECUNDARIO = colors.HexColor("#64748B")
TEXTO_MUTADO = colors.HexColor("#94A3B8")


# =========================================================
# GENERADOR PDF INSTITUCIONAL
# =========================================================

def generar_pdf_institucional(
    documento,
    contenido,
    url_verificacion,
):
    """
    Genera un PDF institucional reutilizable para CASRCE.

    Incluye:
        - Encabezado universitario.
        - Logo oficial UPT_LOGO.png.
        - Identidad visual CASRCE.
        - Contenido dinámico.
        - Código documental.
        - Código QR de verificación.
        - Numeración de páginas.
    """

    buffer = BytesIO()

    # =====================================================
    # LOCALIZACIÓN DEL LOGO INSTITUCIONAL
    # =====================================================

    ruta_logo = finders.find("Imagenes/UPT_LOGO.png")

    # =====================================================
    # CONFIGURACIÓN DEL DOCUMENTO
    # =====================================================

    pdf = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=39 * mm,
        bottomMargin=35 * mm,
        title=documento.titulo,
        author="CASRCE - UPTJFR",
        subject=documento.tipo_documento,
    )

    estilos = getSampleStyleSheet()

    estilo_titulo = ParagraphStyle(
        "TituloInstitucionalCASRCE",
        parent=estilos["Title"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=19,
        alignment=TA_CENTER,
        textColor=AZUL_PROFUNDO,
        spaceBefore=2,
        spaceAfter=5,
    )

    estilo_fecha = ParagraphStyle(
        "FechaInstitucionalCASRCE",
        parent=estilos["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        alignment=TA_CENTER,
        textColor=TEXTO_SECUNDARIO,
        spaceAfter=10,
    )

    # =====================================================
    # CÓDIGO QR
    # =====================================================

    qr_buffer = BytesIO(generar_qr_png(url_verificacion))
    qr_reader = ImageReader(qr_buffer)

    # =====================================================
    # ENCABEZADO Y PIE INSTITUCIONAL
    # =====================================================

    def dibujar_estructura(canvas, doc):

        canvas.saveState()

        ancho, alto = letter

        # -------------------------------------------------
        # LOGO UNIVERSITARIO
        # -------------------------------------------------

        if ruta_logo:

            canvas.drawImage(
                ruta_logo,
                20 * mm,
                alto - 31 * mm,
                width=19 * mm,
                height=19 * mm,
                preserveAspectRatio=True,
                anchor="c",
                mask="auto",
            )

        # -------------------------------------------------
        # IDENTIFICACIÓN INSTITUCIONAL
        # -------------------------------------------------

        canvas.setFillColor(AZUL_PROFUNDO)
        canvas.setFont("Helvetica-Bold", 8)

        canvas.drawCentredString(
            ancho / 2,
            alto - 13 * mm,
            "REPÚBLICA BOLIVARIANA DE VENEZUELA",
        )

        canvas.setFont("Helvetica-Bold", 9)

        canvas.drawCentredString(
            ancho / 2,
            alto - 19 * mm,
            "UNIVERSIDAD POLITÉCNICA TERRITORIAL",
        )

        canvas.drawCentredString(
            ancho / 2,
            alto - 24 * mm,
            "DEL ESTADO BARINAS JOSÉ FÉLIX RIBAS",
        )

        # CASRCE destacado en rojo.
        canvas.setFillColor(ROJO_ACENTO)
        canvas.setFont("Helvetica-Bold", 7)

        canvas.drawCentredString(
            ancho / 2,
            alto - 29 * mm,
            "CASRCE - COORDINACIÓN DE ADMISIÓN, REGISTRO Y SEGUIMIENTO",
        )

        # -------------------------------------------------
        # LÍNEA INSTITUCIONAL
        # -------------------------------------------------

        canvas.setStrokeColor(BORDE)
        canvas.setLineWidth(0.8)

        canvas.line(
            20 * mm,
            alto - 34 * mm,
            ancho - 20 * mm,
            alto - 34 * mm,
        )

        # Acento rojo.
        canvas.setStrokeColor(ROJO_ACENTO)
        canvas.setLineWidth(1.8)

        canvas.line(
            20 * mm,
            alto - 34 * mm,
            42 * mm,
            alto - 34 * mm,
        )

        # -------------------------------------------------
        # PIE DE PÁGINA
        # -------------------------------------------------

        canvas.setStrokeColor(BORDE)
        canvas.setLineWidth(0.7)

        canvas.line(
            20 * mm,
            29 * mm,
            ancho - 20 * mm,
            29 * mm,
        )

        # Código documental.
        canvas.setFillColor(AZUL_PROFUNDO)
        canvas.setFont("Helvetica-Bold", 7)

        canvas.drawString(
            20 * mm,
            22 * mm,
            f"CÓDIGO: {documento.codigo_documento}",
        )

        # Texto de verificación.
        canvas.setFillColor(TEXTO_SECUNDARIO)
        canvas.setFont("Helvetica", 6.5)

        canvas.drawString(
            20 * mm,
            17 * mm,
            "Verifique la autenticidad de este documento mediante el código QR.",
        )

        # Numeración de páginas.
        canvas.setFillColor(TEXTO_SECUNDARIO)
        canvas.setFont("Helvetica", 7)

        canvas.drawRightString(
            ancho - 20 * mm,
            22 * mm,
            f"PÁGINA {doc.page}",
        )

        # -------------------------------------------------
        # CÓDIGO QR
        # -------------------------------------------------

        canvas.drawImage(
            qr_reader,
            ancho - 39 * mm,
            7 * mm,
            width=17 * mm,
            height=17 * mm,
            preserveAspectRatio=True,
            mask="auto",
        )

        canvas.restoreState()

    # =====================================================
    # CONTENIDO DEL DOCUMENTO
    # =====================================================

    elementos = []

    titulo_seguro = escape(
        str(documento.titulo)
    )

    elementos.append(
        Paragraph(
            titulo_seguro,
            estilo_titulo,
        )
    )

    elementos.append(
        Paragraph(
            (
                "Fecha de emisión: "
                f"{documento.fecha_emision.strftime('%d/%m/%Y')}"
            ),
            estilo_fecha,
        )
    )

    elementos.append(
        Spacer(1, 3 * mm)
    )

    elementos.extend(contenido)

    # =====================================================
    # GENERACIÓN DEL PDF
    # =====================================================

    pdf.build(
        elementos,
        onFirstPage=dibujar_estructura,
        onLaterPages=dibujar_estructura,
    )

    resultado = buffer.getvalue()

    buffer.close()

    qr_buffer.close()

    return resultado


# =========================================================
# REGISTRO Y ALMACENAMIENTO DEL DOCUMENTO
# =========================================================

@transaction.atomic
def crear_documento_institucional(
    *,
    request,
    tipo_documento,
    titulo,
    contenido,
    emitido_por=None,
    datos_documento=None,
):
    """
    Registra un documento institucional, genera su PDF,
    incorpora su QR y almacena el archivo.
    """

    documento = DocumentoInstitucional.objects.create(
        tipo_documento=tipo_documento,
        titulo=titulo,
        emitido_por=emitido_por,
        datos_documento=datos_documento or {},
    )

    try:

        # URL pública de verificación.
        url_verificacion = request.build_absolute_uri(
            reverse(
                "documentos:verificar_documento",
                kwargs={
                    "identificador": documento.identificador,
                },
            )
        )

        # Generar PDF.
        pdf_bytes = generar_pdf_institucional(
            documento=documento,
            contenido=contenido,
            url_verificacion=url_verificacion,
        )

        # Nombre del archivo.
        nombre_archivo = (
            f"{documento.codigo_documento}.pdf"
        )

        # Almacenamiento.
        documento.archivo_pdf.save(
            nombre_archivo,
            ContentFile(pdf_bytes),
            save=True,
        )

        return documento

    except Exception:

        # Limpiar archivo si llegó a guardarse.
        if documento.archivo_pdf:
            documento.archivo_pdf.delete(
                save=False
            )

        documento.delete()

        raise
