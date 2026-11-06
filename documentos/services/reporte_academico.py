"""Constructor del reporte de situación académica CASRCE."""
from decimal import Decimal
from xml.sax.saxutils import escape

from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle

from notas_academicas.models import Calificaciones


AZUL = colors.HexColor("#263746")
GRIS = colors.HexColor("#64748B")
BORDE = colors.HexColor("#AAB4BE")
FONDO = colors.HexColor("#EEF1F4")


def texto_seguro(valor):
    if valor in (None, ""):
        return "—"
    return escape(str(valor))


def construir_contenido_reporte_academico(estudiante):
    """Genera una tabla paginada con año, trayecto, unidad, nota y condición."""
    base = getSampleStyleSheet()
    titulo = ParagraphStyle(
        "SituacionAcademicaTitulo", parent=base["Title"],
        fontName="Helvetica-Bold", fontSize=14, leading=17,
        alignment=TA_CENTER, textColor=AZUL, spaceAfter=3,
    )
    normal = ParagraphStyle(
        "SituacionAcademicaNormal", parent=base["Normal"],
        fontName="Helvetica", fontSize=8, leading=10,
    )
    etiqueta = ParagraphStyle(
        "SituacionAcademicaEtiqueta", parent=normal,
        fontName="Helvetica-Bold", textColor=AZUL,
    )
    celda = ParagraphStyle(
        "SituacionAcademicaCelda", parent=normal,
        fontSize=7.1, leading=8.5,
    )
    cabecera = ParagraphStyle(
        "SituacionAcademicaCabecera", parent=celda,
        fontName="Helvetica-Bold", textColor=colors.white,
        alignment=TA_CENTER,
    )

    usuario = estudiante.usuario
    registros = list(
        Calificaciones.objects.filter(estudiante=estudiante)
        .select_related(
            "materia_asignada__materia",
            "periodo_materia__materia",
            "trayecto",
        )
        .order_by("fecha_promedio", "id_calificaciones")
    )

    filas = [[
        Paragraph("AÑO", cabecera),
        Paragraph("TRAYECTO", cabecera),
        Paragraph("UNIDAD CURRICULAR CURSADA", cabecera),
        Paragraph("NOTA", cabecera),
        Paragraph("ASIST.", cabecera),
        Paragraph("U.C.", cabecera),
        Paragraph("CONDICIÓN", cabecera),
    ]]
    total_ponderado = Decimal("0")
    total_uc = Decimal("0")

    for registro in registros:
        materia = (
            registro.materia_asignada.materia
            if registro.materia_asignada else
            registro.periodo_materia.materia
            if registro.periodo_materia else None
        )
        nota = registro.promedio_tramo
        uc = Decimal(str(getattr(materia, "uc", 0) or 0))
        if nota is not None and uc > 0:
            total_ponderado += Decimal(str(nota)) * uc
            total_uc += uc

        anio = registro.fecha_promedio.year if registro.fecha_promedio else "—"
        trayecto = registro.trayecto.nombre if registro.trayecto else "—"
        filas.append([
            Paragraph(texto_seguro(anio), celda),
            Paragraph(texto_seguro(trayecto), celda),
            Paragraph(texto_seguro(materia.nombre if materia else None), celda),
            Paragraph(texto_seguro(nota), celda),
            Paragraph(texto_seguro(registro.asistencia), celda),
            Paragraph(texto_seguro(uc if materia else None), celda),
            Paragraph(texto_seguro(registro.condicion), celda),
        ])

    if len(filas) == 1:
        filas.append([Paragraph("No existen calificaciones registradas.", celda), "", "", "", "", "", ""])

    indice = (total_ponderado / total_uc).quantize(Decimal("0.01")) if total_uc else None
    identificacion = [
        [Paragraph("<b>Documento de identidad:</b>", etiqueta),
         Paragraph(texto_seguro(usuario.cedula_identidad), normal),
         Paragraph("<b>Apellidos y nombres:</b>", etiqueta),
         Paragraph(texto_seguro(f"{usuario.apellidos}, {usuario.nombres}"), normal)],
        [Paragraph("<b>PNF:</b>", etiqueta),
         Paragraph(texto_seguro(estudiante.pnf.pnf if estudiante.pnf else None), normal),
         Paragraph("<b>Índice académico acumulado:</b>", etiqueta),
         Paragraph(texto_seguro(indice), normal)],
    ]

    tabla_identificacion = Table(
        identificacion, colWidths=[31*mm, 40*mm, 34*mm, 65*mm],
    )
    tabla_identificacion.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 0.45, BORDE),
        ("BACKGROUND", (0,0), (0,-1), FONDO),
        ("BACKGROUND", (2,0), (2,-1), FONDO),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING", (0,0), (-1,-1), 4),
        ("RIGHTPADDING", (0,0), (-1,-1), 4),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ]))

    tabla = Table(
        filas,
        colWidths=[13*mm, 24*mm, 73*mm, 15*mm, 17*mm, 12*mm, 16*mm],
        repeatRows=1,
        hAlign="LEFT",
    )
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), AZUL),
        ("GRID", (0,0), (-1,-1), 0.4, BORDE),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING", (0,0), (-1,-1), 3),
        ("RIGHTPADDING", (0,0), (-1,-1), 3),
        ("TOPPADDING", (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, FONDO]),
        ("SPAN", (0,1), (-1,1)) if len(filas) == 2 else ("LINEBELOW", (0,0), (-1,0), 0.5, BORDE),
    ]))

    return [
        Paragraph("SITUACIÓN ACADÉMICA", titulo),
        Paragraph(
            f"Fecha de emisión: {timezone.localtime().strftime('%d/%m/%Y %H:%M')}",
            ParagraphStyle("SituacionFecha", parent=normal, alignment=TA_CENTER, textColor=GRIS),
        ),
        Spacer(1, 3*mm),
        tabla_identificacion,
        Spacer(1, 4*mm),
        tabla,
    ]
