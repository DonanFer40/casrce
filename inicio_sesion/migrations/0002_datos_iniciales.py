from django.db import migrations

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
    {"pnf": "PNF en Nutrición y Dietética", "codigo": "CARRE004", "periodo_academico": "Trimestre"},
    {"pnf": "PNF en Electricidad", "codigo": "CARRE005", "periodo_academico": "Trimestre"},
    {"pnf": "PNF en Mecánica", "codigo": "CARRE006", "periodo_academico": "Trimestre"},
    {"pnf": "PNF en Agroalimentación", "codigo": "CARRE007", "periodo_academico": "Trimestre"},
    {"pnf": "PNF en Contrucción Civil", "codigo": "CARRE008", "periodo_academico": "Trimestre"},
    {"pnf": "PNF en Ingeniería Industrial", "codigo": "CARRE009", "periodo_academico": "Trimestre"},
]

PNF_NUCLEO = [
    {"municipio": "Barinas", "codigo": "CARRE001"},
    {"municipio": "Barinas", "codigo": "CARRE002"},
    {"municipio": "Barinas", "codigo": "CARRE003"},
    {"municipio": "Barinas", "codigo": "CARRE004"},

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

    