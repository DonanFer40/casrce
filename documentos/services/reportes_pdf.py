from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import LongTable, Paragraph, Spacer, TableStyle

from inicio_sesion.horarios import DIAS_SEMANA, FRANJAS_HORARIAS


AZUL = colors.HexColor("#18324B")
GRIS = colors.HexColor("#64748B")
BORDE = colors.HexColor("#CBD5E1")


def construir_reporte_tabular(titulo, columnas, filas, *, resumen=None):
    estilos = getSampleStyleSheet()
    estilo_titulo = ParagraphStyle(
        "ReporteTabularTitulo",
        parent=estilos["Title"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=19,
        alignment=TA_CENTER,
        textColor=AZUL,
        spaceAfter=4 * mm,
    )
    estilo_celda = ParagraphStyle(
        "ReporteTabularCelda",
        parent=estilos["BodyText"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=9,
    )
    estilo_cabecera = ParagraphStyle(
        "ReporteTabularCabecera",
        parent=estilo_celda,
        fontName="Helvetica-Bold",
        textColor=colors.white,
        alignment=TA_CENTER,
    )

    contenido = [Paragraph(escape(titulo), estilo_titulo)]
    if resumen:
        contenido.extend(
            Paragraph(f"<b>{escape(str(etiqueta))}:</b> {escape(str(valor))}", estilo_celda)
            for etiqueta, valor in resumen
        )
        contenido.append(Spacer(1, 3 * mm))

    filas_tabla = [[
        Paragraph(escape(str(columna)), estilo_cabecera)
        for columna in columnas
    ]]
    filas_tabla.extend(
        [
            Paragraph(escape("—" if valor in (None, "") else str(valor)), estilo_celda)
            for valor in fila
        ]
        for fila in filas
    )
    if len(filas_tabla) == 1:
        filas_tabla.append([
            Paragraph("No hay registros para los criterios seleccionados.", estilo_celda)
        ] + [""] * (len(columnas) - 1))

    tabla = LongTable(
        filas_tabla,
        colWidths=[(170 * mm) / max(len(columnas), 1)] * len(columnas),
        repeatRows=1,
        hAlign="LEFT",
    )
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), AZUL),
        ("GRID", (0, 0), (-1, -1), 0.4, BORDE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F1F5F9")]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("SPAN", (0, 1), (-1, 1)) if len(filas_tabla) == 2 and not filas else ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    contenido.append(tabla)
    return contenido


def construir_reporte_horario(horarios, titulo):
    horarios = list(horarios)
    if horarios and len({
        (horario.aula_id, horario.trayecto_id, horario.periodo_id)
        for horario in horarios
    }) == 1:
        por_celda = {
            (horario.hora_inicio, horario.dia_semana): horario
            for horario in horarios
        }
        filas = []
        for inicio, fin in FRANJAS_HORARIAS:
            celdas = []
            for dia, _ in DIAS_SEMANA:
                horario = por_celda.get((inicio, dia))
                if horario is None:
                    celdas.append("")
                    continue
                docentes = ", ".join(
                    f"{asignacion.docente.usuario.nombres} "
                    f"{asignacion.docente.usuario.apellidos}"
                    for asignacion in horario.materia_asignada.docentes.all()
                    if asignacion.activo and asignacion.docente.activo
                )
                materia = horario.materia_asignada.materia.nombre
                celdas.append(f"{materia} ({docentes})" if docentes else materia)
            filas.append((
                f"{inicio.strftime('%I:%M').lstrip('0')} - "
                f"{fin.strftime('%I:%M').lstrip('0')}",
                *celdas,
            ))
        aula = horarios[0].aula
        return construir_reporte_tabular(
            titulo,
            ["Hora", *(nombre for _, nombre in DIAS_SEMANA)],
            filas,
            resumen=[
                ("Núcleo", aula.id_nucleo.municipio),
                ("PNF", aula.id_pnf.pnf),
                ("Sección", aula.id_seccion.nombre),
                ("Trayecto", horarios[0].trayecto.nombre),
                ("Período", horarios[0].periodo.nombre),
            ],
        )

    filas = []
    for horario in sorted(
        horarios,
        key=lambda item: (item.aula_id, item.dia_semana, item.hora_inicio),
    ):
        docentes = ", ".join(
            f"{asignacion.docente.usuario.nombres} "
            f"{asignacion.docente.usuario.apellidos}"
            for asignacion in horario.materia_asignada.docentes.all()
            if asignacion.activo and asignacion.docente.activo
        )
        filas.append((
            horario.get_dia_semana_display(),
            horario.hora_inicio.strftime("%H:%M"),
            horario.hora_final.strftime("%H:%M"),
            horario.materia_asignada.materia.nombre,
            docentes or "Sin docente asignado",
            (
                f"{horario.aula.nombre_aula} · "
                f"{horario.aula.id_nucleo.municipio} · "
                f"{horario.aula.id_pnf.pnf} · "
                f"Sección {horario.aula.id_seccion.nombre}"
            ),
        ))
    return construir_reporte_tabular(
        titulo,
        ["Día", "Desde", "Hasta", "Unidad curricular", "Docentes", "Aula"],
        filas,
    )
