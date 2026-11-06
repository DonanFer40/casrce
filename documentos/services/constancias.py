"""Contenido reutilizable para constancias institucionales."""
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, Spacer

def construir_constancia_estudios(estudiante):
    base = getSampleStyleSheet()
    titulo = ParagraphStyle(
        "ConstanciaTituloCASRCE", parent=base["Title"],
        fontName="Helvetica-Bold", fontSize=15, leading=19,
        alignment=TA_CENTER, textColor=colors.HexColor("#0F172A"),
        spaceAfter=18,
    )
    cuerpo = ParagraphStyle(
        "ConstanciaCuerpoCASRCE", parent=base["BodyText"],
        fontName="Helvetica", fontSize=11, leading=18,
        alignment=TA_JUSTIFY,
    )
    firma = ParagraphStyle(
        "ConstanciaFirmaCASRCE", parent=base["Normal"],
        fontName="Helvetica", fontSize=9, leading=13,
        alignment=TA_CENTER,
    )
    usuario = estudiante.usuario
    nombre = f"{usuario.nombres} {usuario.apellidos}"
    nucleo = estudiante.nucleo.municipio if estudiante.nucleo else "—"
    pnf = estudiante.pnf.pnf if estudiante.pnf else "—"
    texto = (
        "Quien suscribe, en representación de la Coordinación de "
        "Admisión, Seguimiento, Registro y Control de Estudio (CASRCE), "
        "hace constar que <b>{}</b>, titular de la cédula de identidad "
        "<b>{}</b>, se encuentra registrado(a) como estudiante del "
        "Programa Nacional de Formación <b>{}</b>, adscrito al núcleo "
        "<b>{}</b>, según los datos disponibles en el sistema institucional."
    ).format(nombre, usuario.cedula_identidad, pnf, nucleo)
    return [
        Paragraph("CONSTANCIA DE ESTUDIOS", titulo),
        Spacer(1, 8*mm),
        Paragraph(texto, cuerpo),
        Spacer(1, 22*mm),
        Paragraph("____________________________________<br/><b>Firma y sello autorizado</b>", firma),
    ]
