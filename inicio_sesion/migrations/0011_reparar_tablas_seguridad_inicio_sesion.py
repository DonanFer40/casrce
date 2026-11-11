from django.db import migrations


def crear_tablas_ausentes(apps, schema_editor):
    modelos = (
        apps.get_model("inicio_sesion", "ControlIntentosInicioSesion"),
        apps.get_model("inicio_sesion", "SesionActivaNavegador"),
    )
    tablas_existentes = set(
        schema_editor.connection.introspection.table_names()
    )

    for modelo in modelos:
        if modelo._meta.db_table not in tablas_existentes:
            schema_editor.create_model(modelo)
            tablas_existentes.add(modelo._meta.db_table)


class Migration(migrations.Migration):

    dependencies = [
        ("inicio_sesion", "0010_horarioacademico"),
    ]

    operations = [
        migrations.RunPython(
            crear_tablas_ausentes,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
