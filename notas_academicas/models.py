from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from inicio_sesion.models import MateriaAsignada, PeriodoAcademico, TrayectoAcademico, Docente, Usuario, PeriodoAcademicoMateria, Estudiante, Materia, DocenteAsignadoMateria, Pnf, Nucleos

class PlanificacionAcademica(models.Model):
    id_planificacion = models.AutoField(primary_key=True)
    pnf = models.ForeignKey(Pnf, models.PROTECT)
    nucleo = models.ForeignKey(Nucleos, models.PROTECT)
    materia_asignacion = models.ForeignKey(MateriaAsignada, on_delete=models.PROTECT, related_name="planificaciones_academicas")
    periodo_academico = models.ForeignKey(PeriodoAcademico, on_delete=models.PROTECT)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    activo = models.BooleanField(default=True)
    observacion = models.TextField(blank=True, null=True)
    ESTADOS_ACEPTACION = [
        ("BORRADOR", "Borrador"),
        ("ENVIADO", "Enviado al Coordinador"),
        ("ACEPTADA", "Aceptada"),
        ("DENEGADA", "Denegada"),
    ]
    estado_aceptacion = models.CharField(max_length=10, choices=ESTADOS_ACEPTACION, default="BORRADOR")

class DetallePlanificacion(models.Model):
    id_detalle = models.AutoField(primary_key=True)
    plan_academico = models.ForeignKey(PlanificacionAcademica, on_delete=models.CASCADE, related_name="detalles")
    titulo_unidad = models.CharField(max_length=255)
    ponderacion = models.DecimalField(max_digits=5, decimal_places=2)
    contenido_unidad = models.TextField()

class DetalleEvaluacion(models.Model):
    id_evaluacion = models.AutoField(primary_key=True)
    detalle_plan = models.ForeignKey(DetallePlanificacion, on_delete=models.CASCADE, related_name="evaluaciones")
    metodo_evaluacion = models.CharField(max_length=100)
    porcentaje_evaluacion = models.DecimalField(max_digits=5, decimal_places=2)
    fecha_evaluacion = models.DateField()

# Promedio de todas las unidades curriculares

class PromedioFinal(models.Model):
    id_promedio_final = models.AutoField(primary_key=True)
    estudiante = models.ForeignKey(Estudiante, on_delete=models.PROTECT, related_name="promedios_finales")
    materia_asignacion = models.ForeignKey(MateriaAsignada, on_delete=models.PROTECT, related_name="promedios_finales")
    trayecto = models.ForeignKey(TrayectoAcademico, models.CASCADE, db_column='trayecto')
    promedio_final = models.DecimalField(max_digits=5, decimal_places=2)
    asistencia = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    estado = models.CharField(max_length=100)
    fecha_promedio = models.DateField()
    motivo = models.TextField(blank=True, null=True)

# Reparación

class EvaluacionReparacion(models.Model):
    id_evaluacion = models.AutoField(primary_key=True)
    pnf = models.ForeignKey(Pnf, models.PROTECT, related_name="evaluaciones_reparacion_pnf", blank=True, null=True)
    nucleo = models.ForeignKey(Nucleos, models.PROTECT, related_name="evaluaciones_reparacion_nucleo", blank=True, null=True)
    materia_asignacion = models.ForeignKey(MateriaAsignada, models.PROTECT, related_name="evaluaciones_reparacion_materia", blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)

class DetalleEvaluacionReparacion(models.Model):
    id_detalle_reparacion = models.AutoField(primary_key=True)
    evaluacion_reparacion = models.ForeignKey(EvaluacionReparacion, on_delete=models.CASCADE, related_name="detalles")
    porcentaje = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    TIPOS_EVALUACION = [
        ("EXAMEN", "Examen"),
        ("INFORME", "Informe"),
        ("PROYECTO", "Proyecto"),
        ("EXPOSICION", "Exposición"),
        ("PRACTICA", "Práctica"),
        ("CUESTIONARIO", "Cuestionario"),
        ("PROGRAMACION", "Desarrollo de Programa"),
        ("DIAGRAMA_FLUJO", "Diagrama de Flujo"),
        ("OTRO", "Otro"),
    ]
    tipo_evaluacion = models.CharField(max_length=50, choices=TIPOS_EVALUACION, default="OTRO")

class Reparacion(models.Model):
    id_reparacion = models.AutoField(primary_key=True)
    estudiante = models.ForeignKey(Estudiante, models.PROTECT, related_name="reparaciones", blank=True, null=True)
    evaluacion_reparacion = models.ForeignKey(EvaluacionReparacion, models.PROTECT, related_name="reparaciones", blank=True, null=True)
    fecha_reparacion = models.DateField(blank=True, null=True)
    calificacion = models.DecimalField(max_digits=5, decimal_places=2, default=0, blank=True, null=True)
    estado = models.CharField(
        max_length=20,
        choices=[
            ("PENDIENTE","Pendiente"),
            ("APROBADO","Aprobado"),
            ("REPROBADO","Reprobado")
        ],
        default="PENDIENTE",
        blank=True, null=True
    )
    
class ModificacionReparacion(models.Model):
    id_modificacion = models.AutoField(primary_key=True)
    evaluacion_reparacion = models.ForeignKey(EvaluacionReparacion, on_delete=models.PROTECT, related_name="modificaciones")
    fecha_modificacion = models.DateTimeField(auto_now_add=True)
    motivo = models.CharField(max_length=255, default="Modificación de nota de reparación")

    def __str__(self):
        return f"Modificación {self.id_modificacion}"

class DetalleModificacionReparacion(models.Model):
    id_detalle_modificacion = models.AutoField(primary_key=True)
    modificacion = models.ForeignKey(ModificacionReparacion, on_delete=models.CASCADE, related_name="detalles")
    reparacion = models.ForeignKey(Reparacion, on_delete=models.PROTECT, related_name="historial_modificaciones")
    nota_anterior = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    nota_nueva = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    estado_anterior = models.CharField(max_length=20, blank=True, null=True)
    estado_nuevo = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"{self.reparacion.estudiante} - modificación"

# CALIFICACIONES 

class Calificaciones(models.Model):
    id_calificaciones = models.AutoField(primary_key=True)
    planificacion_academica = models.ForeignKey(PlanificacionAcademica, on_delete=models.PROTECT, related_name="calificaciones_planificacion", blank=True, null=True)
    periodo_materia = models.ForeignKey(PeriodoAcademicoMateria, on_delete=models.PROTECT, related_name="calificaciones_periodo", blank=True, null=True)
    materia_asignada = models.ForeignKey(MateriaAsignada, on_delete=models.PROTECT, related_name="calificaciones_materia", blank=True, null=True)
    estudiante = models.ForeignKey(Estudiante, on_delete=models.PROTECT, related_name="calificaciones_estudiante", blank=True, null=True)
    promedio_tramo = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    asistencia = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100)
        ],
        default=0, blank=True, null=True
    )
    condicion = models.CharField(max_length=100, blank=True, null=True)
    trayecto = models.ForeignKey(TrayectoAcademico, models.CASCADE, db_column='trayecto', blank=True, null=True)
    fecha_promedio = models.DateField(blank=True, null=True)

class DetalleCalificacionesUnidad(models.Model):
    id_detalle_calificaciones_unidad = models.AutoField(primary_key=True)
    calificacion = models.ForeignKey(Calificaciones, on_delete=models.PROTECT, related_name="detalles_unidad")
    unidad = models.ForeignKey(DetallePlanificacion, on_delete=models.PROTECT, related_name="calificaciones_unidad")
    nota_unidad = models.DecimalField(max_digits=5, decimal_places=2)
    fecha_calificacion = models.DateField(auto_now_add=True)

# Respaldo de notas académicas

class HistorialModificacionNotas(models.Model):
    id_historial = models.AutoField(primary_key=True)
    docente_asignado = models.ForeignKey(DocenteAsignadoMateria, on_delete=models.PROTECT)
    periodo_academico = models.ForeignKey(PeriodoAcademico, on_delete=models.PROTECT)
    trayecto = models.ForeignKey(TrayectoAcademico, models.CASCADE, db_column='trayecto', blank=True, null=True)
    fecha_modificacion = models.DateTimeField(auto_now_add=True)
    usuario_modifica = models.ForeignKey(Usuario, on_delete=models.PROTECT)
    motivo = models.TextField()

    def __str__(self):
        return f"Modificación {self.id_historial}"

class HistorialDetalleNota(models.Model):
    id_detalle = models.AutoField(primary_key=True)
    historial = models.ForeignKey(HistorialModificacionNotas, on_delete=models.CASCADE, related_name="detalles")
    estudiante = models.ForeignKey(Estudiante, on_delete=models.PROTECT)
    numero_unidad = models.PositiveSmallIntegerField(null=True, blank=True)
    nota_anterior = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    nota_nueva = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    asistencia_anterior = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    asistencia_nueva = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    promedio_anterior = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    promedio_nuevo = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

# Promedio Final y Actualización de Trayecto

class HistorialTrayectoEstudiante(models.Model):
    id_historial = models.AutoField(primary_key=True)
    estudiante = models.ForeignKey(Estudiante, on_delete=models.PROTECT, related_name="historiales_trayecto")
    anio = models.PositiveIntegerField()
    trayecto_anterior = models.ForeignKey(TrayectoAcademico, on_delete=models.PROTECT, related_name="historiales_trayecto_anterior")
    trayecto_nuevo = models.ForeignKey(TrayectoAcademico, on_delete=models.PROTECT, related_name="historiales_trayecto_nuevo")
    cantidad_materias = models.PositiveSmallIntegerField()
    materias_reprobadas = models.PositiveSmallIntegerField()
    materias_mala_asistencia = models.PositiveSmallIntegerField()
    estado = models.CharField(max_length=50)
    puede_pasar = models.BooleanField(default=False)
    motivo = models.TextField()
    fecha_procesamiento = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return (
            f"{self.estudiante} - "
            f"{self.anio} - "
            f"{self.trayecto_anterior}"
        )

