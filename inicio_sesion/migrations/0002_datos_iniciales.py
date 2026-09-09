from django.db import migrations

CALENDARIO_ACADEMICA = [
    {
        "fecha_inicio": "2026-01-01",
        "fecha_final": "2026-01-01",
        "descripcion": "Inicio de Año",
        "activo": True,
        "tipo": "NO_LABORABLE"
    },
    {
        "fecha_inicio": "2026-02-12",
        "fecha_final": "2026-02-13",
        "descripcion": "Carnaval",
        "activo": True,
        "tipo": "NO_LABORABLE"
    },
    {
        "fecha_inicio": "2026-03-28",
        "fecha_final": "2026-03-29",
        "descripcion": "Jueves y Viernes Santo",
        "activo": True,
        "tipo": "NO_LABORABLE"
    },
    {
        "fecha_inicio": "2026-04-19",
        "fecha_final": "2026-04-19",
        "descripcion": "Declaración de Independencia",
        "activo": True,
        "tipo": "NO_LABORABLE"
    },
    {
        "fecha_inicio": "2026-05-01",
        "fecha_final": "2026-05-01",
        "descripcion": "Día del Trabajador",
        "activo": True,
        "tipo": "NO_LABORABLE"
    },
    {
        "fecha_inicio": "2026-06-24",
        "fecha_final": "2026-06-24",
        "descripcion": "Batalla de Carabobo",
        "activo": True,
        "tipo": "NO_LABORABLE"
    },
    {
        "fecha_inicio": "2026-07-05",
        "fecha_final": "2026-07-05",
        "descripcion": "Día de la Independencia de Venezuela",
        "activo": True,
        "tipo": "NO_LABORABLE"
    },
    {
        "fecha_inicio": "2026-07-24",
        "fecha_final": "2026-07-24",
        "descripcion": "Natalicio de Simón Bolívar",
        "activo": True,
        "tipo": "NO_LABORABLE"
    },
    {
        "fecha_inicio": "2026-10-12",
        "fecha_final": "2026-10-12",
        "descripcion": "Día de la Resistencia Indígena",
        "activo": True,
        "tipo": "NO_LABORABLE"
    },
    {
        "fecha_inicio": "2026-12-05",
        "fecha_final": "2026-12-05",
        "descripcion": "Día del Profesor Universitario",
        "activo": True,
        "tipo": "NO_LABORABLE"
    },
    {
        "fecha_inicio": "2026-12-24",
        "fecha_final": "2026-12-24",
        "descripcion": "Noche Buena",
        "activo": True,
        "tipo": "NO_LABORABLE"
    },
    {
        "fecha_inicio": "2026-12-25",
        "fecha_final": "2026-12-25",
        "descripcion": "Día de Navidad",
        "activo": True,
        "tipo": "NO_LABORABLE"
    },
    {
        "fecha_inicio": "2026-12-31",
        "fecha_final": "2026-12-31",
        "descripcion": "Fin de Año",
        "activo": True,
        "tipo": "NO_LABORABLE"
    },
    {
        "fecha_inicio": "2026-01-01",
        "fecha_final": "2026-01-05",
        "descripcion": "Período de Vacaciones",
        "activo": True,
        "tipo": "VACACIONES"
    },
    {
        "fecha_inicio": "2026-02-12",
        "fecha_final": "2026-02-16",
        "descripcion": "Asueto Carnaval",
        "activo": True,
        "tipo": "VACACIONES"
    },
    {
        "fecha_inicio": "2026-03-25",
        "fecha_final": "2026-03-29",
        "descripcion": "Asueto Semana Santa",
        "activo": True,
        "tipo": "VACACIONES"
    },
    {
        "fecha_inicio": "2026-07-29",
        "fecha_final": "2026-07-31",
        "descripcion": "Período de Vacaciones",
        "activo": True,
        "tipo": "VACACIONES"
    },
    {
        "fecha_inicio": "2026-08-01",
        "fecha_final": "2026-08-31",
        "descripcion": "Período de Vacaciones",
        "activo": True,
        "tipo": "VACACIONES"
    },
    {
        "fecha_inicio": "2026-09-01",
        "fecha_final": "2026-09-14",
        "descripcion": "Período de Vacaciones",
        "activo": True,
        "tipo": "VACACIONES"
    },
    {
        "fecha_inicio": "2026-12-16",
        "fecha_final": "2026-12-31",
        "descripcion": "Período de Vacaciones",
        "activo": True,
        "tipo": "VACACIONES"
    },
    {
        "fecha_inicio": "2026-01-31",
        "fecha_final": "2026-01-31",
        "descripcion": "Muerte de José Félix Ribas",
        "activo": True,
        "tipo": "NO_LABORABLE"
    },
    {
        "fecha_inicio": "2026-07-17",
        "fecha_final": "2026-07-21",
        "descripcion": "Semana Aniversario de la UPT del Estado Barinas José Félix Ribas y Actividades Académicas y Culturales",
        "activo": True,
        "tipo": "ANIVERSARIO"
    },
    {
        "fecha_inicio": "2026-09-19",
        "fecha_final": "2026-09-19",
        "descripcion": "Natalicio de José Félix Ribas",
        "activo": True,
        "tipo": "NO_LABORABLE"
    },
    {
        "fecha_inicio": "2026-11-21",
        "fecha_final": "2026-11-21",
        "descripcion": "Día del Estudiante",
        "activo": True,
        "tipo": "NO_LABORABLE"
    },
    {
        "fecha_inicio": "2026-01-29",
        "fecha_final": "2026-01-29",
        "descripcion": "Inicio de solicitud de solvencia para grado",
        "activo": True,
        "tipo": "GRADUACION"
    },
    {
        "fecha_inicio": "2026-04-25",
        "fecha_final": "2026-04-25",
        "descripcion": "Primer Acto de Grado Solemne",
        "activo": True,
        "tipo": "GRADUACION"
    },
    {
        "fecha_inicio": "2026-06-03",
        "fecha_final": "2026-06-03",
        "descripcion": "Inicio de solicitud de solvencia para grado",
        "activo": True,
        "tipo": "GRADUACION"
    },
    {
        "fecha_inicio": "2026-07-31",
        "fecha_final": "2026-07-31",
        "descripcion": "Segundo Acto de Grado Solemne 2024",
        "activo": True,
        "tipo": "GRADUACION"
    },
    {
        "fecha_inicio": "2026-10-07",
        "fecha_final": "2026-10-07",
        "descripcion": "Inicio de solicitud de solvencia para grado",
        "activo": True,
        "tipo": "GRADUACION"
    },
    {
        "fecha_inicio": "2026-12-05",
        "fecha_final": "2026-12-05",
        "descripcion": "Tercer Acto de Grado Solemne",
        "activo": True,
        "tipo": "GRADUACION"
    },
]

TRAYECTOS_ACADEMICOS = [
    {"nombre": "Trayecto Inicial"},
    {"nombre": "Trayecto I"},
    {"nombre": "Trayecto II"},
    {"nombre": "Trayecto III"},
    {"nombre": "Trayecto IV"},
    {"nombre": "Trayecto V"},
]

PERIODOS_ACADEMICOS = [
    {"nombre": "Inicial Trimestre"},
    {"nombre": "Inicial Semestre"},
    {"nombre": "Reparación"},
    {"nombre": "Tramo I"},
    {"nombre": "Tramo II"},
    {"nombre": "Tramo III"},
    {"nombre": "Semestre I"},
    {"nombre": "Semestre II"},
]

NUCLEOS = [
    {"municipio": "Barinas", "direccion": "Dirección Barinas"},
    {"municipio": "Barinitas", "direccion": "Dirección Barinitas"},
    {"municipio": "Socopo", "direccion": "Dirección Socopó"},
    {"municipio": "Pedraza", "direccion": "Dirección Ciudad Bolivia"},
]

PNF = [
    {"pnf": "PNF en Sistema e Informática", "codigo": "CARRE001", "periodo_academico": "Trimestre"},
    {"pnf": "PNF en Electrónica", "codigo": "CARRE002", "periodo_academico": "Trimestre"},
    {"pnf": "PNF en Mediciona Veterinaria", "codigo": "CARRE003", "periodo_academico": "Semestre"},
    {"pnf": "PNF en Electricidad", "codigo": "CARRE004", "periodo_academico": "Trimestre"},
    {"pnf": "PNF en Mecánica", "codigo": "CARRE005", "periodo_academico": "Trimestre"},
    {"pnf": "PNF en Agroalimentación", "codigo": "CARRE006", "periodo_academico": "Trimestre"},
    {"pnf": "PNF en Contrucción Civil", "codigo": "CARRE007", "periodo_academico": "Trimestre"},
    {"pnf": "PNF en Ingeniería Industrial", "codigo": "CARRE008", "periodo_academico": "Trimestre"},
]

PNF_NUCLEO = [
    {"municipio": "Barinas", "codigo": "CARRE001"},
    {"municipio": "Barinas", "codigo": "CARRE002"},
    {"municipio": "Barinas", "codigo": "CARRE003"},

    {"municipio": "Barinitas", "codigo": "CARRE004"},
    {"municipio": "Barinitas", "codigo": "CARRE005"},
    {"municipio": "Barinitas", "codigo": "CARRE006"},
    {"municipio": "Barinitas", "codigo": "CARRE007"},
    {"municipio": "Barinitas", "codigo": "CARRE008"},
    {"municipio": "Barinitas", "codigo": "CARRE001"},
    {"municipio": "Barinitas", "codigo": "CARRE003"},

    {"municipio": "Socopo", "codigo": "CARRE004"},
    {"municipio": "Socopo", "codigo": "CARRE006"},
    {"municipio": "Socopo", "codigo": "CARRE007"},
    {"municipio": "Socopo", "codigo": "CARRE001"},
    {"municipio": "Socopo", "codigo": "CARRE003"},

    {"municipio": "Pedraza", "codigo": "CARRE006"},
    {"municipio": "Pedraza", "codigo": "CARRE003"},
]

def crear_datos(apps, schema_editor):
    Nucleo = apps.get_model("inicio_sesion", "Nucleos")
    PeriodoAcademico = apps.get_model("inicio_sesion", "PeriodoAcademico")
    TrayectoAcademico = apps.get_model("inicio_sesion", "TrayectoAcademico")
    carrera = apps.get_model("inicio_sesion", "Pnf")
    PNFNucleo = apps.get_model("inicio_sesion", "PNFNucleo")
    Calendario = apps.get_model("inicio_sesion", "CalendarioAcademico")
        
    # Calendario Académico
    for calendario in CALENDARIO_ACADEMICA:
        Calendario.objects.get_or_create(
            fecha_inicio=calendario["fecha_inicio"],
            fecha_final=calendario["fecha_final"],
            tipo=calendario["tipo"],
            defaults={
                "descripcion": calendario["descripcion"],
                "activo": calendario["activo"],
            },
        )

    # Núcleos
    for nucleo in NUCLEOS:
        Nucleo.objects.get_or_create(
            municipio=nucleo["municipio"],
            defaults={
                "direccion": nucleo["direccion"],
            },
        )

    # Trayectos académicos
    for trayecto in TRAYECTOS_ACADEMICOS:
        TrayectoAcademico.objects.get_or_create(
            nombre=trayecto["nombre"]
        )

    # Períodos académicos
    for periodo in PERIODOS_ACADEMICOS:
        PeriodoAcademico.objects.get_or_create(
            nombre=periodo["nombre"]
        )

    # PNF
    for datos in PNF:
        carrera.objects.get_or_create(
            codigo=datos["codigo"],
            defaults={
                "pnf": datos["pnf"],
                "periodo_academico": datos["periodo_academico"],
            },
        )

    # Relación PNF - Núcleo
    for relacion in PNF_NUCLEO:
        nucleo = Nucleo.objects.get(
            municipio=relacion["municipio"]
        )

        pnf = carrera.objects.get(
            codigo=relacion["codigo"]
        )

        PNFNucleo.objects.get_or_create(
            id_nucleo=nucleo,
            id_pnf=pnf,
        )

class Migration(migrations.Migration):
    dependencies = [
        ("inicio_sesion", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            crear_datos,
        ),
    ]

    