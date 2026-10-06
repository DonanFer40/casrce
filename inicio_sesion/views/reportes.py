import os

from io import BytesIO

from django.conf import settings
from django.http import FileResponse
from django.utils import timezone
from django.shortcuts import render

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
)
from django.db.models import Avg, Count
from inicio_sesion.models import AulaEstudiante, Estudiante
from notas_academicas.models import Calificaciones
from inicio_sesion.services.permisos import requiere_rol_reporte

def reporte_estudiantes_pdf(request):
    """
    Genera un reporte PDF con la información general
    de los estudiantes registrados en CARSCE.
    """

    logo_path = os.path.join(
        settings.BASE_DIR,
        "static",
        "Imagenes",
        "UPT_LOGO.png"
    )

    estudiantes = (
        Estudiante.objects
        .select_related(
            "usuario",
            "nucleo",
            "pnf"
        )
        .prefetch_related(
            "estatus__trayecto"
        )
        .order_by(
            "usuario__apellidos",
            "usuario__nombres"
        )
    )

    buffer = BytesIO()

    documento = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=12 * mm,
        leftMargin=12 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
        title="Reporte General de Estudiantes - CARSCE",
        author="CARSCE",
    )

    estilos = getSampleStyleSheet()

    estilo_titulo = ParagraphStyle(
        "ReporteEstudiantesTitulo",
        parent=estilos["Title"],
        alignment=TA_CENTER,
        fontSize=16,
        leading=20,
        spaceAfter=4 * mm,
    )

    estilo_subtitulo = ParagraphStyle(
        "ReporteEstudiantesSubtitulo",
        parent=estilos["Normal"],
        alignment=TA_CENTER,
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#475569"),
        spaceAfter=2 * mm,
    )

    estilo_normal = ParagraphStyle(
        "ReporteEstudiantesNormal",
        parent=estilos["Normal"],
        fontSize=8,
        leading=10,
    )

    estilo_encabezado = ParagraphStyle(
        "ReporteEstudiantesEncabezado",
        parent=estilos["Normal"],
        fontSize=8,
        leading=10,
        textColor=colors.white,
        alignment=TA_CENTER,
    )

    contenido = []

    # ---------------------------------------------------------
    # ENCABEZADO
    # ---------------------------------------------------------

    logo = Image(
        logo_path,
        width=27 * mm,
        height=27 * mm
    )

    estilo_institucional = ParagraphStyle(
        "ReporteEstudiantesInstitucional",
        parent=estilos["Normal"],
        alignment=TA_CENTER,
        fontSize=12,
        leading=15,
        textColor=colors.HexColor("#0F172A"),
    )

    encabezado_institucional = Paragraph(
        "<b>UNIVERSIDAD POLITÉCNICA TERRITORIAL</b><br/>"
        "DEL ESTADO BARINAS JOSÉ FÉLIX RIBAS",
        estilo_institucional
    )

    tabla_encabezado = Table(
        [
            [
                logo,
                encabezado_institucional,
                ""
            ]
        ],
        colWidths=[
            30 * mm,
            213 * mm,
            30 * mm
        ]
    )

    tabla_encabezado.setStyle(
        TableStyle([
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE"
            ),

            # Logo
            (
                "ALIGN",
                (0, 0),
                (0, 0),
                "CENTER"
            ),

            # Texto institucional
            (
                "ALIGN",
                (1, 0),
                (1, 0),
                "CENTER"
            ),

            # Columna derecha vacía
            (
                "ALIGN",
                (2, 0),
                (2, 0),
                "CENTER"
            ),

            # Eliminar espacios internos
            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                0
            ),
            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                0
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                0
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                0
            ),
        ])
    )

    contenido.append(tabla_encabezado)

    contenido.append(
        Spacer(1, 4 * mm)
    )

    contenido.append(
        Paragraph(
            "<b>CARSCE</b>",
            estilo_subtitulo
        )
    )

    contenido.append(
        Paragraph(
            "REPORTE GENERAL DE ESTUDIANTES",
            estilo_subtitulo
        )
    )

    fecha_generacion = timezone.localtime().strftime(
        "%d/%m/%Y %H:%M"
    )

    contenido.append(
        Paragraph(
            f"Fecha de generación: {fecha_generacion}",
            estilo_subtitulo
        )
    )

    contenido.append(Spacer(1, 5 * mm))

    # ---------------------------------------------------------
    # RESUMEN
    # ---------------------------------------------------------

    total_estudiantes = estudiantes.count()

    resumen_data = [
        [
            Paragraph(
                "<b>TOTAL DE ESTUDIANTES</b>",
                estilo_normal
            ),
            Paragraph(
                f"<b>{total_estudiantes}</b>",
                estilo_normal
            ),
        ]
    ]

    tabla_resumen = Table(
        resumen_data,
        colWidths=[70 * mm, 30 * mm],
    )

    tabla_resumen.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (0, 0),
                colors.HexColor("#E2E8F0")
            ),
            (
                "BACKGROUND",
                (1, 0),
                (1, 0),
                colors.HexColor("#F8FAFC")
            ),
            (
                "BOX",
                (0, 0),
                (-1, -1),
                0.7,
                colors.HexColor("#CBD5E1")
            ),
            (
                "INNERGRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.HexColor("#CBD5E1")
            ),
            (
                "ALIGN",
                (1, 0),
                (1, 0),
                "CENTER"
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE"
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                6
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                6
            ),
        ])
    )

    contenido.append(tabla_resumen)

    contenido.append(Spacer(1, 6 * mm))

    # ---------------------------------------------------------
    # TABLA DE ESTUDIANTES
    # ---------------------------------------------------------

    datos_tabla = [
        [
            Paragraph("CÉDULA", estilo_encabezado),
            Paragraph("ESTUDIANTE", estilo_encabezado),
            Paragraph("NÚCLEO", estilo_encabezado),
            Paragraph("PNF", estilo_encabezado),
            Paragraph("ESTADO", estilo_encabezado),
        ]
    ]

    for estudiante in estudiantes:

        usuario = estudiante.usuario

        nombre_completo = (
            f"{usuario.nombres} {usuario.apellidos}"
        )

        nucleo = (
            estudiante.nucleo.municipio
            if estudiante.nucleo
            else "No asignado"
        )

        pnf = (
            estudiante.pnf.pnf
            if estudiante.pnf
            else "No asignado"
        )

        estatus_actual = (
            estudiante.estatus
            .order_by("-fecha_registro", "-fecha_ingreso")
            .first()
        )

        estado = (
            estatus_actual.estado
            if estatus_actual
            else "Sin estatus"
        )

        datos_tabla.append([
            Paragraph(
                str(usuario.cedula_identidad),
                estilo_normal
            ),
            Paragraph(
                nombre_completo,
                estilo_normal
            ),
            Paragraph(
                str(nucleo),
                estilo_normal
            ),
            Paragraph(
                str(pnf),
                estilo_normal
            ),
            Paragraph(
                str(estado),
                estilo_normal
            ),
        ])

    tabla_estudiantes = Table(
        datos_tabla,
        colWidths=[
            28 * mm,
            55 * mm,
            35 * mm,
            65 * mm,
            30 * mm,
        ],
        repeatRows=1,
    )

    tabla_estudiantes.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#0F172A")
            ),
            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.HexColor("#CBD5E1")
            ),
            (
                "ROWBACKGROUNDS",
                (0, 1),
                (-1, -1),
                [
                    colors.white,
                    colors.HexColor("#F8FAFC")
                ]
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE"
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                5
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                5
            ),
        ])
    )

    contenido.append(tabla_estudiantes)

    contenido.append(Spacer(1, 6 * mm))

    contenido.append(
        Paragraph(
            "Sistema Web para la Gestión de CARSCE",
            estilo_subtitulo
        )
    )

    # ---------------------------------------------------------
    # GENERACIÓN DEL PDF
    # ---------------------------------------------------------

    documento.build(contenido)

    buffer.seek(0)

    return FileResponse(
        buffer,
        as_attachment=False,
        filename="reporte_general_estudiantes.pdf",
        content_type="application/pdf",
    )

def reporte_academico_pdf(request):
    """
    Genera un reporte PDF con información académica
    registrada en CARSCE.
    """

    logo_path = os.path.join(
        settings.BASE_DIR,
        "static",
        "Imagenes",
        "UPT_LOGO.png"
    )

    calificaciones = (
        Calificaciones.objects
        .select_related(
            "estudiante__usuario",
            "estudiante__nucleo",
            "estudiante__pnf",
            "materia_asignada__materia",
            "periodo_materia__periodo",
            "trayecto",
        )
        .order_by(
            "estudiante__usuario__apellidos",
            "estudiante__usuario__nombres",
            "materia_asignada__materia__nombre",
        )
    )

    buffer = BytesIO()

    documento = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=12 * mm,
        leftMargin=12 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
        title="Reporte Académico - CARSCE",
        author="CARSCE",
    )

    estilos = getSampleStyleSheet()

    estilo_subtitulo = ParagraphStyle(
        "ReporteAcademicoSubtitulo",
        parent=estilos["Normal"],
        alignment=TA_CENTER,
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#475569"),
        spaceAfter=2 * mm,
    )

    estilo_normal = ParagraphStyle(
        "ReporteAcademicoNormal",
        parent=estilos["Normal"],
        fontSize=8,
        leading=10,
    )

    estilo_encabezado = ParagraphStyle(
        "ReporteAcademicoEncabezado",
        parent=estilos["Normal"],
        fontSize=8,
        leading=10,
        textColor=colors.white,
        alignment=TA_CENTER,
    )

    contenido = []

    # ---------------------------------------------------------
    # ENCABEZADO INSTITUCIONAL
    # ---------------------------------------------------------

    logo = Image(
        logo_path,
        width=27 * mm,
        height=27 * mm
    )

    estilo_institucional = ParagraphStyle(
        "ReporteAcademicoInstitucional",
        parent=estilos["Normal"],
        alignment=TA_CENTER,
        fontSize=12,
        leading=15,
        textColor=colors.HexColor("#0F172A"),
    )

    encabezado_institucional = Paragraph(
        "<b>UNIVERSIDAD POLITÉCNICA TERRITORIAL</b><br/>"
        "DEL ESTADO BARINAS JOSÉ FÉLIX RIBAS",
        estilo_institucional
    )

    tabla_encabezado = Table(
        [
            [
                logo,
                encabezado_institucional,
                ""
            ]
        ],
        colWidths=[
            30 * mm,
            213 * mm,
            30 * mm
        ]
    )

    tabla_encabezado.setStyle(
        TableStyle([
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE"
            ),
            (
                "ALIGN",
                (0, 0),
                (0, 0),
                "CENTER"
            ),
            (
                "ALIGN",
                (1, 0),
                (1, 0),
                "CENTER"
            ),
            (
                "ALIGN",
                (2, 0),
                (2, 0),
                "CENTER"
            ),
            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                0
            ),
            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                0
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                0
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                0
            ),
        ])
    )

    contenido.append(tabla_encabezado)

    contenido.append(
        Spacer(1, 4 * mm)
    )

    contenido.append(
        Paragraph(
            "<b>CARSCE</b>",
            estilo_subtitulo
        )
    )

    contenido.append(
        Paragraph(
            "REPORTE ACADÉMICO",
            estilo_subtitulo
        )
    )

    fecha_generacion = timezone.localtime().strftime(
        "%d/%m/%Y %H:%M"
    )

    contenido.append(
        Paragraph(
            f"Fecha de generación: {fecha_generacion}",
            estilo_subtitulo
        )
    )

    contenido.append(
        Spacer(1, 5 * mm)
    )

    # ---------------------------------------------------------
    # RESUMEN ACADÉMICO
    # ---------------------------------------------------------

    total_registros = calificaciones.count()

    estudiantes_evaluados = (
        calificaciones
        .values("estudiante")
        .distinct()
        .count()
    )

    promedio_general = None

    if total_registros:
        from django.db.models import Avg

        promedio_general = (
            calificaciones
            .aggregate(
                promedio=Avg("promedio_tramo")
            )
            .get("promedio")
        )

    resumen_data = [
        [
            Paragraph(
                "<b>REGISTROS ACADÉMICOS</b>",
                estilo_normal
            ),
            Paragraph(
                "<b>ESTUDIANTES EVALUADOS</b>",
                estilo_normal
            ),
            Paragraph(
                "<b>PROMEDIO GENERAL</b>",
                estilo_normal
            ),
        ],
        [
            Paragraph(
                str(total_registros),
                estilo_normal
            ),
            Paragraph(
                str(estudiantes_evaluados),
                estilo_normal
            ),
            Paragraph(
                str(
                    round(float(promedio_general), 2)
                    if promedio_general is not None
                    else "N/D"
                ),
                estilo_normal
            ),
        ]
    ]

    tabla_resumen = Table(
        resumen_data,
        colWidths=[
            55 * mm,
            55 * mm,
            55 * mm,
        ]
    )

    tabla_resumen.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#E2E8F0")
            ),
            (
                "BACKGROUND",
                (0, 1),
                (-1, 1),
                colors.HexColor("#F8FAFC")
            ),
            (
                "BOX",
                (0, 0),
                (-1, -1),
                0.7,
                colors.HexColor("#CBD5E1")
            ),
            (
                "INNERGRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.HexColor("#CBD5E1")
            ),
            (
                "ALIGN",
                (0, 0),
                (-1, -1),
                "CENTER"
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE"
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                6
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                6
            ),
        ])
    )

    contenido.append(tabla_resumen)

    contenido.append(
        Spacer(1, 6 * mm)
    )

    # ---------------------------------------------------------
    # TABLA ACADÉMICA
    # ---------------------------------------------------------

    datos_tabla = [
        [
            Paragraph("CÉDULA", estilo_encabezado),
            Paragraph("ESTUDIANTE", estilo_encabezado),
            Paragraph("PNF", estilo_encabezado),
            Paragraph("MATERIA", estilo_encabezado),
            Paragraph("TRAYECTO", estilo_encabezado),
            Paragraph("PROMEDIO", estilo_encabezado),
            Paragraph("ASISTENCIA", estilo_encabezado),
            Paragraph("CONDICIÓN", estilo_encabezado),
        ]
    ]

    for registro in calificaciones:

        estudiante = registro.estudiante

        usuario = (
            estudiante.usuario
            if estudiante
            else None
        )

        nombre_completo = (
            f"{usuario.nombres} {usuario.apellidos}"
            if usuario
            else "No asignado"
        )

        cedula = (
            usuario.cedula_identidad
            if usuario
            else "No asignada"
        )

        pnf = (
            estudiante.pnf.pnf
            if estudiante and estudiante.pnf
            else "No asignado"
        )

        materia = (
            registro.materia_asignada.materia.nombre
            if (
                registro.materia_asignada
                and registro.materia_asignada.materia
            )
            else "No asignada"
        )

        trayecto = (
            registro.trayecto.nombre
            if registro.trayecto
            else "No asignado"
        )

        promedio = (
            str(registro.promedio_tramo)
            if registro.promedio_tramo is not None
            else "N/D"
        )

        asistencia = (
            f"{registro.asistencia}%"
            if registro.asistencia is not None
            else "N/D"
        )

        condicion = (
            registro.condicion
            if registro.condicion
            else "Sin condición"
        )

        datos_tabla.append([
            Paragraph(
                str(cedula),
                estilo_normal
            ),
            Paragraph(
                nombre_completo,
                estilo_normal
            ),
            Paragraph(
                str(pnf),
                estilo_normal
            ),
            Paragraph(
                str(materia),
                estilo_normal
            ),
            Paragraph(
                str(trayecto),
                estilo_normal
            ),
            Paragraph(
                promedio,
                estilo_normal
            ),
            Paragraph(
                asistencia,
                estilo_normal
            ),
            Paragraph(
                str(condicion),
                estilo_normal
            ),
        ])

    tabla_academica = Table(
        datos_tabla,
        colWidths=[
            25 * mm,
            48 * mm,
            40 * mm,
            48 * mm,
            28 * mm,
            23 * mm,
            25 * mm,
            30 * mm,
        ],
        repeatRows=1,
    )

    tabla_academica.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#0F172A")
            ),
            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.HexColor("#CBD5E1")
            ),
            (
                "ROWBACKGROUNDS",
                (0, 1),
                (-1, -1),
                [
                    colors.white,
                    colors.HexColor("#F8FAFC")
                ]
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE"
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                5
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                5
            ),
        ])
    )

    contenido.append(tabla_academica)

    contenido.append(
        Spacer(1, 6 * mm)
    )

    contenido.append(
        Paragraph(
            "Sistema Web para la Gestión de CARSCE",
            estilo_subtitulo
        )
    )

    # ---------------------------------------------------------
    # GENERACIÓN
    # ---------------------------------------------------------

    documento.build(contenido)

    buffer.seek(0)

    return FileResponse(
        buffer,
        as_attachment=False,
        filename="reporte_academico.pdf",
        content_type="application/pdf",
    )

def reporte_inscripciones_pdf(request):
    usuario_generador = request.session.get(
        "usuario_nombre",
        "Usuario no identificado"
    )
    
    inscripciones = (
        AulaEstudiante.objects
        .select_related(
            "estatus__estudiante__usuario",
            "aula__id_nucleo",
            "aula__id_pnf",
            "aula__id_seccion",
        )
        .order_by(
            "aula__id_nucleo__municipio",
            "aula__id_pnf__pnf",
            "estatus__estudiante__usuario__apellidos",
            "estatus__estudiante__usuario__nombres",
        )
    )

    total_inscripciones = inscripciones.count()

    estudiantes_inscritos = (
        inscripciones
        .values("estatus__estudiante")
        .distinct()
        .count()
    )

    inscripciones_activas = inscripciones.filter(
        estado="Curso"
    ).count()

    buffer = BytesIO()

    documento = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=12 * mm,
        leftMargin=12 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
        title="Reporte General de Inscripciones - CARSCE",
        author="CARSCE",
    )

    estilos = getSampleStyleSheet()

    estilo_titulo = ParagraphStyle(
        "TituloInstitucional",
        parent=estilos["Normal"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#0F172A"),
    )

    estilo_subtitulo = ParagraphStyle(
        "SubtituloInstitucional",
        parent=estilos["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=11,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#64748B"),
    )

    estilo_celda = ParagraphStyle(
        "CeldaReporte",
        parent=estilos["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=9,
        textColor=colors.HexColor("#0F172A"),
    )

    estilo_celda_centrada = ParagraphStyle(
        "CeldaCentrada",
        parent=estilo_celda,
        alignment=TA_CENTER,
    )

    elementos = []


    # =========================================================
    # ENCABEZADO INSTITUCIONAL
    # =========================================================

    logo_path = os.path.join(
        settings.BASE_DIR,
        "static",
        "Imagenes",
        "UPT_LOGO.png"
    )

    if os.path.exists(logo_path):

        logo = Image(
            logo_path,
            width=22 * mm,
            height=22 * mm,
        )

        nombre_universidad = Paragraph(
            "UNIVERSIDAD POLITÉCNICA TERRITORIAL<br/>"
            "DEL ESTADO BARINAS JOSÉ FÉLIX RIBAS",
            estilo_titulo
        )

        encabezado = Table(
            [[
                logo,
                nombre_universidad,
                ""
            ]],
            colWidths=[
                45 * mm,
                165 * mm,
                45 * mm
            ],
            hAlign="CENTER"
        )

        encabezado.setStyle(
            TableStyle([
                # Logo
                (
                    "ALIGN",
                    (0, 0),
                    (0, 0),
                    "RIGHT"
                ),

                # Nombre de la universidad
                (
                    "ALIGN",
                    (1, 0),
                    (1, 0),
                    "CENTER"
                ),

                # Alineación vertical
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE"
                ),

                # Sin espacios internos
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    0
                ),

                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    0
                ),

                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    0
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    0
                ),
            ])
        )

        elementos.append(encabezado)

    elementos.append(
        Spacer(1, 4 * mm)
    )

    elementos.append(
        Paragraph(
            "CARSCE — REPORTE GENERAL DE INSCRIPCIONES",
            estilo_titulo
        )
    )

    elementos.append(
        Paragraph(
            f"Fecha de generación: "
            f"{timezone.localtime().strftime('%d/%m/%Y %H:%M')}",
            estilo_subtitulo
        )
    )

    elementos.append(
        Paragraph(
            f"Generado por: {usuario_generador}",
            estilo_subtitulo
        )
    )

    elementos.append(Spacer(1, 5 * mm))

    # =========================================================
    # RESUMEN
    # =========================================================

    resumen = Table(
        [[
            Paragraph(
                f"<b>{total_inscripciones}</b><br/>"
                f"Total de inscripciones",
                estilo_celda_centrada
            ),
            Paragraph(
                f"<b>{estudiantes_inscritos}</b><br/>"
                f"Estudiantes inscritos",
                estilo_celda_centrada
            ),
            Paragraph(
                f"<b>{inscripciones_activas}</b><br/>"
                f"Inscripciones activas",
                estilo_celda_centrada
            ),
        ]],
        colWidths=[
            85 * mm,
            85 * mm,
            85 * mm,
        ],
    )

    resumen.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ])
    )

    elementos.append(resumen)

    elementos.append(Spacer(1, 5 * mm))

    # =========================================================
    # TABLA
    # =========================================================

    datos = [[
        "CÉDULA",
        "ESTUDIANTE",
        "NÚCLEO",
        "PNF",
        "SECCIÓN",
        "TURNO",
        "AULA",
        "FECHA INICIO",
        "ESTADO",
    ]]

    for inscripcion in inscripciones:

        estudiante = inscripcion.estatus.estudiante
        usuario = estudiante.usuario
        aula = inscripcion.aula

        nombre_estudiante = (
            f"{usuario.apellidos}, {usuario.nombres}"
        )

        datos.append([
            Paragraph(
                usuario.cedula_identidad or "N/D",
                estilo_celda
            ),

            Paragraph(
                nombre_estudiante,
                estilo_celda
            ),

            Paragraph(
                aula.id_nucleo.municipio
                if aula.id_nucleo else "N/D",
                estilo_celda
            ),

            Paragraph(
                aula.id_pnf.pnf
                if aula.id_pnf else "N/D",
                estilo_celda
            ),

            Paragraph(
                aula.id_seccion.nombre
                if aula.id_seccion else "N/D",
                estilo_celda_centrada
            ),

            Paragraph(
                aula.id_seccion.turno
                if aula.id_seccion and aula.id_seccion.turno
                else "N/D",
                estilo_celda_centrada
            ),

            Paragraph(
                aula.nombre_aula or "N/D",
                estilo_celda
            ),

            Paragraph(
                inscripcion.fecha_inicio.strftime("%d/%m/%Y")
                if inscripcion.fecha_inicio
                else "N/D",
                estilo_celda_centrada
            ),

            Paragraph(
                inscripcion.estado or "N/D",
                estilo_celda_centrada
            ),
        ])

    tabla = Table(
        datos,
        repeatRows=1,
        colWidths=[
            24 * mm,
            48 * mm,
            28 * mm,
            38 * mm,
            18 * mm,
            22 * mm,
            28 * mm,
            25 * mm,
            25 * mm,
        ],
    )

    tabla.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#0F172A")
            ),

            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white
            ),

            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold"
            ),

            (
                "FONTSIZE",
                (0, 0),
                (-1, 0),
                7
            ),

            (
                "ALIGN",
                (0, 0),
                (-1, 0),
                "CENTER"
            ),

            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE"
            ),

            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.4,
                colors.HexColor("#E2E8F0")
            ),

            (
                "ROWBACKGROUNDS",
                (0, 1),
                (-1, -1),
                [
                    colors.white,
                    colors.HexColor("#F8FAFC")
                ]
            ),

            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                5
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                5
            ),

            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                4
            ),

            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                4
            ),
        ])
    )

    elementos.append(tabla)

    elementos.append(Spacer(1, 5 * mm))

    elementos.append(
        Paragraph(
            "Sistema Web para la Gestión de CARSCE",
            estilo_subtitulo
        )
    )

    documento.build(elementos)

    buffer.seek(0)

    return FileResponse(
        buffer,
        as_attachment=False,
        filename="reporte_inscripciones.pdf",
    )

@requiere_rol_reporte(
    "Director General",
    "Control de Estudio"
)
def reportes_control_estudio(request):
    return render(request, "Roles/Reportes/Puente_Reportes.html")