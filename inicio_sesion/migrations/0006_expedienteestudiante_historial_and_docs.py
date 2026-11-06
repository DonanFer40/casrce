# Generated for the student administrative expediente workflow.
import django.db.models.deletion
from django.db import migrations, models


def vincular_documentos_existentes(apps, schema_editor):
    Expediente = apps.get_model("inicio_sesion", "ExpedienteEstudiante")
    Documento = apps.get_model("inicio_sesion", "DocumentosEstudiante")
    alias = schema_editor.connection.alias

    usuarios_con_documentos = (
        Documento.objects.using(alias)
        .values_list("id_usuario_id", flat=True)
        .distinct()
    )
    for usuario_id in usuarios_con_documentos.iterator():
        expediente, _ = Expediente.objects.using(alias).get_or_create(
            usuario_id=usuario_id,
            defaults={
                "estado": "PENDIENTE_REVISION",
                "nota_gemini": (
                    "Expediente previo a la incorporación de la revisión automática. "
                    "Los documentos requieren comprobación administrativa manual."
                ),
                "resultados_gemini": {},
            },
        )
        Documento.objects.using(alias).filter(
            id_usuario_id=usuario_id,
            expediente__isnull=True,
        ).update(expediente_id=expediente.pk)


class Migration(migrations.Migration):

    dependencies = [
        ("inicio_sesion", "0005_verificacioncodigo_numero_reenvios"),
    ]

    operations = [
        migrations.CreateModel(
            name="ExpedienteEstudiante",
            fields=[
                ("id_expediente", models.AutoField(primary_key=True, serialize=False)),
                ("estado", models.CharField(
                    choices=[
                        ("PENDIENTE_REVISION", "Pendiente por revisión"),
                        ("EN_REVISION", "En revisión"),
                        ("CON_OBSERVACIONES", "Con observaciones"),
                        ("VALIDADO_ADMINISTRATIVAMENTE", "Validado administrativamente"),
                        ("INSCRIPCION_APROBADA", "Inscripción aprobada"),
                    ],
                    db_index=True,
                    default="PENDIENTE_REVISION",
                    max_length=40,
                )),
                ("nota_gemini", models.TextField(blank=True)),
                ("resultados_gemini", models.JSONField(blank=True, default=dict)),
                ("fecha_revision_gemini", models.DateTimeField(blank=True, null=True)),
                ("observacion_actual", models.TextField(blank=True)),
                ("creado", models.DateTimeField(auto_now_add=True)),
                ("actualizado", models.DateTimeField(auto_now=True)),
                ("fecha_aprobacion", models.DateTimeField(blank=True, null=True)),
                ("perfil_aprobacion", models.CharField(blank=True, max_length=30)),
                ("aprobado_por", models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="expedientes_aprobados",
                    to="inicio_sesion.usuario",
                )),
                ("usuario", models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="expediente_estudiantil",
                    to="inicio_sesion.usuario",
                )),
            ],
            options={"ordering": ["-actualizado", "-id_expediente"]},
        ),
        migrations.CreateModel(
            name="HistorialExpedienteEstudiante",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("estado_anterior", models.CharField(blank=True, max_length=40)),
                ("estado_nuevo", models.CharField(
                    choices=[
                        ("PENDIENTE_REVISION", "Pendiente por revisión"),
                        ("EN_REVISION", "En revisión"),
                        ("CON_OBSERVACIONES", "Con observaciones"),
                        ("VALIDADO_ADMINISTRATIVAMENTE", "Validado administrativamente"),
                        ("INSCRIPCION_APROBADA", "Inscripción aprobada"),
                    ],
                    max_length=40,
                )),
                ("accion", models.CharField(max_length=40)),
                ("observacion", models.TextField(blank=True)),
                ("perfil", models.CharField(max_length=30)),
                ("fecha_hora", models.DateTimeField(auto_now_add=True)),
                ("expediente", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="historial",
                    to="inicio_sesion.expedienteestudiante",
                )),
                ("realizado_por", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="acciones_expedientes",
                    to="inicio_sesion.usuario",
                )),
            ],
            options={"ordering": ["-fecha_hora", "-id"]},
        ),
        migrations.AddField(
            model_name="documentosestudiante",
            name="expediente",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="documentos",
                to="inicio_sesion.expedienteestudiante",
            ),
        ),
        migrations.RunPython(
            vincular_documentos_existentes,
            migrations.RunPython.noop,
        ),
    ]
