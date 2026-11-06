"""Construcción de la planilla institucional de inscripción (una página)."""
import unicodedata

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle

from inicio_sesion.models import (
    Contacto, Nacimiento, Residencia, DocumentosEstudiante,
)

AZUL = colors.HexColor("#24364B")
GRIS = colors.HexColor("#64748B")
BORDE = colors.HexColor("#7B8794")
FONDO = colors.HexColor("#F1F3F5")


def _safe(value, fallback="—"):
    value = str(value).strip() if value not in (None, "") else fallback
    return (value.replace("&", "&amp;").replace("<", "&lt;")
                 .replace(">", "&gt;").replace("\\n", " "))


def _normalizar(value):
    value = unicodedata.normalize("NFKD", str(value or "")).encode("ascii", "ignore").decode()
    return " ".join(value.lower().replace("_", " ").replace("-", " ").split())


def _par(text, style):
    return Paragraph(_safe(text), style)


def _tabla(rows, widths, *, header=False, padding=3):
    table = Table(rows, colWidths=widths, hAlign="LEFT")
    commands = [
        ("GRID", (0, 0), (-1, -1), 0.45, BORDE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), padding),
        ("RIGHTPADDING", (0, 0), (-1, -1), padding),
        ("TOPPADDING", (0, 0), (-1, -1), padding),
        ("BOTTOMPADDING", (0, 0), (-1, -1), padding),
    ]
    if header:
        commands.append(("BACKGROUND", (0, 0), (-1, 0), FONDO))
    table.setStyle(TableStyle(commands))
    return table


def construir_contenido_planilla(estudiante, expediente):
    """Devuelve los elementos ReportLab de una planilla compacta de una sola hoja."""
    base = getSampleStyleSheet()
    title = ParagraphStyle(
        "PlanillaTituloCASRCE", parent=base["Title"], fontName="Helvetica-Bold",
        fontSize=12, leading=14, alignment=TA_CENTER, textColor=AZUL, spaceAfter=2,
    )
    subtitle = ParagraphStyle(
        "PlanillaSubCASRCE", parent=base["Normal"], fontName="Helvetica-Bold",
        fontSize=8, leading=10, alignment=TA_CENTER, textColor=GRIS, spaceAfter=5,
    )
    label = ParagraphStyle(
        "PlanillaLabelCASRCE", parent=base["Normal"], fontName="Helvetica-Bold",
        fontSize=6.8, leading=8, textColor=AZUL,
    )
    value = ParagraphStyle(
        "PlanillaValueCASRCE", parent=base["Normal"], fontName="Helvetica",
        fontSize=7.2, leading=8.5, textColor=colors.black,
    )
    section = ParagraphStyle(
        "PlanillaSectionCASRCE", parent=base["Normal"], fontName="Helvetica-Bold",
        fontSize=7.4, leading=9, alignment=TA_CENTER, textColor=AZUL,
    )
    tiny = ParagraphStyle(
        "PlanillaTinyCASRCE", parent=base["Normal"], fontName="Helvetica",
        fontSize=6.5, leading=7.5, textColor=colors.black,
    )

    usuario = estudiante.usuario
    contacto = Contacto.objects.filter(id_usuario=usuario).first()
    nacimiento = Nacimiento.objects.filter(id_usuario=usuario).first()
    residencia = Residencia.objects.filter(id_usuario=usuario).first()
    recibidos = list(DocumentosEstudiante.objects.filter(expediente=expediente))
    nombres_recibidos = [_normalizar(d.nombre_documento) for d in recibidos]

    def recibido(*claves):
        return any(any(clave in nombre for clave in claves) for nombre in nombres_recibidos)

    def celda(etiqueta, dato):
        return [_par(etiqueta, label), _par(dato, value)]

    elementos = [
        Paragraph("PLANILLA DE INSCRIPCIÓN", title),
        Paragraph("PARTE I · LLENADO POR EL ESTUDIANTE", subtitle),
    ]

    fecha = getattr(expediente, "creado", None)
    fecha_texto = fecha.strftime("%d/%m/%Y") if fecha else "________________"
    pnf = estudiante.pnf.pnf if getattr(estudiante, "pnf", None) else "—"
    elementos.append(_tabla([
        [*celda("FECHA", fecha_texto), *celda("PNF", pnf)],
    ], [22*mm, 55*mm, 17*mm, 76*mm], padding=3))

    elementos.append(Spacer(1, 2*mm))
    elementos.append(Paragraph("DATOS PERSONALES", section))
    elementos.append(_tabla([
        [*celda("NOMBRES", usuario.nombres), *celda("APELLIDOS", usuario.apellidos)],
        [*celda("CÉDULA / PASAPORTE", usuario.cedula_identidad),
         *celda("FECHA DE NACIMIENTO", nacimiento.fecha_nacimiento.strftime("%d/%m/%Y") if nacimiento and nacimiento.fecha_nacimiento else "—")],
        [*celda("LUGAR DE NACIMIENTO", ", ".join(filter(None, [
            getattr(nacimiento, "municipio", None), getattr(nacimiento, "estado", None),
            getattr(nacimiento, "pais", None)
        ])) if nacimiento else "—"),
         *celda("TELÉFONO", contacto.telefono_personal if contacto else "—")],
        [*celda("CORREO", contacto.correo_electronico if contacto else "—"),
         *celda("TELÉFONO SECUNDARIO", contacto.telefono_suplete if contacto else "—")],
    ], [25*mm, 60*mm, 25*mm, 60*mm], padding=3))

    elementos.append(Spacer(1, 2*mm))
    elementos.append(Paragraph("DIRECCIÓN DE HABITACIÓN", section))
    direccion = residencia.direccion_residencia if residencia else "—"
    parroquia = residencia.parroquia if residencia else "—"
    municipio = residencia.municipio if residencia else "—"
    estado = getattr(residencia, "estado", None) if residencia else None
    elementos.append(_tabla([
        [*celda("DIRECCIÓN", direccion), *celda("LOCALIDAD / PARROQUIA", parroquia)],
        [*celda("ESTADO", estado or "—"), *celda("MUNICIPIO", municipio)],
    ], [25*mm, 60*mm, 30*mm, 55*mm], padding=3))

    elementos.append(Spacer(1, 2*mm))
    elementos.append(Paragraph("PARTE II · DOCUMENTOS CONSIGNADOS (USO ADMINISTRATIVO)", section))
    checklist = [
        ("Foto tamaño carnet", recibido("foto", "carnet")),
        ("Copia de cédula de identidad", recibido("cedula", "identidad")),
        ("Copia del acta de nacimiento", recibido("nacimiento")),
        ("Certificado de participación OPSU", recibido("opsu", "ops")),
        ("Copia de notas de bachillerato", recibido("notas", "bachillerato")),
        ("Copia del título de bachiller", recibido("titulo", "bachiller")),
    ]
    docs_rows = [[_par("DOCUMENTO", label), _par("RECIBIDO", label)]]
    docs_rows += [[_par(nombre, tiny), _par("[X]" if ok else "[ ]", tiny)] for nombre, ok in checklist]
    elementos.append(_tabla(docs_rows, [150*mm, 20*mm], header=True, padding=2))

    elementos.append(Spacer(1, 2*mm))
    elementos.append(Paragraph("ENTREVISTA · COMPLETAR POR EL FUNCIONARIO", section))
    interview = [
        [_par("¿Practica algún deporte?", tiny), _par("SÍ [ ]   NO [ ]", tiny), _par("¿Cuál? ____________________", tiny)],
        [_par("¿Practica algún oficio / tarea?", tiny), _par("SÍ [ ]   NO [ ]", tiny), _par("¿Cuál? ____________________", tiny)],
        [_par("¿Posee discapacidad y/o patología?", tiny), _par("SÍ [ ]   NO [ ]", tiny), _par("¿Posee informe? _____________", tiny)],
    ]
    elementos.append(_tabla(interview, [65*mm, 35*mm, 70*mm], padding=2))
    elementos.append(Spacer(1, 4*mm))

    firmas = [[
        _par("__________________________________<br/><b>EL / LA ESTUDIANTE</b>", tiny),
        _par("__________________________________<br/><b>RECEPTOR(A) CASRCE</b>", tiny),
    ]]
    elementos.append(_tabla(firmas, [85*mm, 85*mm], padding=3))
    elementos.append(Spacer(1, 2*mm))
    elementos.append(Paragraph(
        "La recepción de esta planilla no implica aprobación definitiva de la inscripción. "
        "El expediente queda sujeto a revisión y validación administrativa.",
        ParagraphStyle("PlanillaNotaCASRCE", parent=tiny, alignment=TA_CENTER, textColor=GRIS),
    ))
    return elementos
