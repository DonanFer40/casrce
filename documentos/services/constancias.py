"""Contenido reutilizable para constancias institucionales."""
from datetime import date
from xml.sax.saxutils import escape

from django.db.models import Q
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, Spacer
from inicio_sesion.models import AulaEstudiante

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


def construir_constancia_inscripcion(estudiante, anio):
    inicio = date(anio, 1, 1)
    fin = date(anio, 12, 31)
    inscripciones = list(
        AulaEstudiante.objects.filter(
            estatus__estudiante=estudiante,
            fecha_inicio__lte=fin,
        )
        .filter(
            Q(fecha_final__isnull=True) | Q(fecha_final__gte=inicio)
        )
        .select_related("aula__id_nucleo", "aula__id_pnf")
    )
    if not inscripciones:
        raise ValueError("No hay inscripción registrada para ese año.")

    base = getSampleStyleSheet()
    titulo = ParagraphStyle(
        "ConstanciaInscripcionTituloCASRCE",
        parent=base["Title"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=19,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=18,
    )
    cuerpo = ParagraphStyle(
        "ConstanciaInscripcionCuerpoCASRCE",
        parent=base["BodyText"],
        fontName="Helvetica",
        fontSize=11,
        leading=18,
        alignment=TA_JUSTIFY,
    )
    firma = ParagraphStyle(
        "ConstanciaInscripcionFirmaCASRCE",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        alignment=TA_CENTER,
    )
    usuario = estudiante.usuario
    nombres = f"{usuario.nombres} {usuario.apellidos}"
    pnf = estudiante.pnf.pnf if estudiante.pnf else "—"
    nucleo = estudiante.nucleo.municipio if estudiante.nucleo else "—"
    return [
        Paragraph("CONSTANCIA DE INSCRIPCIÓN", titulo),
        Spacer(1, 8 * mm),
        Paragraph(
            (
                "Se hace constar que <b>{}</b>, titular de la cédula "
                "de identidad <b>{}</b>, registra inscripción durante "
                "el año <b>{}</b> en el Programa Nacional de Formación "
                "<b>{}</b>, núcleo <b>{}</b>, según los registros "
                "académicos disponibles."
            ).format(
                escape(nombres),
                escape(usuario.cedula_identidad),
                anio,
                escape(pnf),
                escape(nucleo),
            ),
            cuerpo,
        ),
        Spacer(1, 22 * mm),
        Paragraph(
            "____________________________________<br/><b>Firma y sello autorizado</b>",
            firma,
        ),
    ]
