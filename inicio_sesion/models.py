from django.db import models

# Clases (Tablas) principales 
class Usuario(models.Model):
    id_usuario = models.AutoField(primary_key=True)
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    genero = models.CharField(max_length=50, null=True, blank=True)
    cedula_identidad = models.CharField(max_length=15)
    estado_civil = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return f"{self.nombres} {self.apellidos}"

class Cuenta(models.Model):
    id_cuenta = models.AutoField(primary_key=True)
    id_usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="cuenta")
    usuario = models.CharField(max_length=160, unique=True)
    clave = models.CharField(max_length=160)
    tipo_cuenta = models.CharField(
        max_length=20,
        choices=[
            ("ADMIN", "Administrativo"),
            ("EST", "Estudiante"),
        ]
    )

    def obtener_rol_principal(self):
        """Retorna el nombre del rol o perfil activo del usuario"""
        u = self.id_usuario
        
        if DirectorGeneral.objects.filter(usuario=u).exists():
            return "Director General"
        if ControlEstudio.objects.filter(usuario=u).exists():
            return "Control de Estudio"
        if CoordinadorPNF.objects.filter(usuario=u).exists():
            return "Coordinador de PNF"
        if Docente.objects.filter(usuario=u).exists():
            return "Docente"
        if Estudiante.objects.filter(usuario=u).exists():
            return "Estudiante"
            
        return "Sin Rol Asignado"

class Residencia(models.Model):
    id_residencia = models.AutoField(primary_key=True)
    condicion_residencia = models.CharField(max_length=100)
    municipio = models.CharField(max_length=100)
    parroquia = models.CharField(max_length=100)
    direccion_residencia = models.CharField(max_length=100)
    id_usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='residencia')

class Contacto(models.Model):
    id_contacto = models.AutoField(primary_key=True)
    telefono_suplete = models.CharField(max_length=15, null=True, blank=True)
    telefono_personal = models.CharField(max_length=15)
    correo_electronico = models.EmailField(max_length=100, unique=True)
    correo_alternativo = models.EmailField(max_length=100, unique=True, null=True, blank=True)
    id_usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='contacto')

class Nacimiento(models.Model):
    id_nacimiento = models.AutoField(primary_key=True)
    pais = models.CharField(max_length=100)
    estado = models.CharField(max_length=100)
    municipio = models.CharField(max_length=100)
    parroquia = models.CharField(max_length=100)
    direccion_nacimiento = models.CharField(max_length=100)
    fecha_nacimiento = models.DateField()
    id_usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='nacimiento')

class Pnf(models.Model):
    id_pnf = models.AutoField(primary_key=True)
    pnf = models.CharField(max_length=50)
    codigo = models.CharField(max_length=60)
    periodo_academico = models.CharField(max_length=40, null=True, blank=True)
    
    def __str__(self):
        return self.pnf

class Nucleos(models.Model):
    id_nucleo = models.AutoField(primary_key=True)
    municipio = models.CharField(max_length=50)
    direccion = models.CharField(max_length=100)

    def __str__(self):
        return self.municipio

class PNFNucleo(models.Model):
    id_pnf_nucleo = models.AutoField(primary_key=True)
    id_nucleo = models.ForeignKey(Nucleos, on_delete=models.CASCADE, db_column='id_nucleo')
    id_pnf = models.ForeignKey(Pnf, on_delete=models.CASCADE, db_column='id_pnf')

    def __str__(self):
        return f"{self.id_pnf.pnf} - {self.id_nucleo.municipio}"

class SeccionAcademica(models.Model):
    id_seccion = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=5)
    turno = models.CharField(max_length=10, blank=True, null=True)

    def __str__(self):
        return f"Sección {self.nombre}"
    
class AulaAcademica(models.Model):
    id_aula = models.AutoField(primary_key=True)
    nombre_aula = models.CharField(max_length=100)
    Nota = models.TextField()
    piso_edificio = models.CharField(max_length=100)
    tipo_aula = models.CharField(max_length=100)
    id_seccion = models.ForeignKey(SeccionAcademica, on_delete=models.CASCADE, related_name="aulas") 
    id_pnf = models.ForeignKey(Pnf, on_delete=models.CASCADE, related_name="aulas") 
    id_nucleo = models.ForeignKey(Nucleos, on_delete=models.CASCADE, related_name="aulas")

class TrayectoAcademico(models.Model):
    id_periodo_academico = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=50)

    def __str__(self):
        return self.nombre
    
class PeriodoAcademico(models.Model):
    id_periodo_academico = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=50)

    def __str__(self):
        return self.nombre

class CalendarioAcademico(models.Model):
    id_calendario_academico = models.AutoField(primary_key=True)
    fecha_inicio = models.DateField()
    fecha_final = models.DateField()
    descripcion = models.CharField(max_length=150)
    activo = models.BooleanField(default=True)
    tipo = models.CharField(
        max_length=30,
        choices=[
        ("PERIODO", "Período académico"),
        ("CARGA_NOTAS", "Carga de notas"),
        ("NO_LABORABLE", "No laborable"),
        ("VACACIONES", "Vacaciones"),
        ("INSCRIPCION_TRIMESTRE", "Inscripción Trimestre"),
        ("INSCRIPCION_SEMESTRE", "Inscripción Semestre"),
        ("ANIVERSARIO", "Días de aniversarios"),
        ("GRADUACION", "Días de graduación"),
        ("ACTIVIDADES", "Actividades o operativos"),
    ])

class CalendarioPeriodo(models.Model):
    periodo = models.ForeignKey(PeriodoAcademico, on_delete=models.PROTECT, related_name="calendarios")
    calendario = models.ForeignKey(CalendarioAcademico, on_delete=models.PROTECT, related_name="periodo")

class Materia(models.Model):
    id_materia = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    codigo = models.CharField(max_length=20)
    recuperacion = models.CharField(max_length=100)
    htea = models.DecimalField(max_digits=3, decimal_places=1)
    htei = models.DecimalField(max_digits=3, decimal_places=1)
    activa = models.BooleanField(default=True)
    tipo_materia = models.CharField(max_length=20, default="Curso")

    id_trayecto = models.ForeignKey(TrayectoAcademico, models.CASCADE, db_column='trayecto')
    id_pnf = models.ForeignKey(Pnf, models.CASCADE, db_column='pnf')

    registrado_por = models.ForeignKey(Usuario, on_delete=models.PROTECT, related_name="materias_registradas", blank=True, null=True)
    fecha_registro = models.DateTimeField(blank=True, null=True)
    perfil_registro = models.CharField(max_length=50, blank=True, null=True)

    modificado_por = models.ForeignKey(Usuario, on_delete=models.PROTECT, related_name="materias_modificadas", blank=True, null=True)
    fecha_modificacion = models.DateTimeField(blank=True, null=True)
    perfil_modificacion = models.CharField(max_length=50, blank=True, null=True)

    @property
    def thte(self):
        return self.htea + self.htei

    @property
    def uc(self):
        return self.thte // 25

class PeriodoAcademicoMateria(models.Model):
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE, related_name="periodos_academicos")
    periodo = models.ForeignKey(PeriodoAcademico, on_delete=models.CASCADE, related_name="materias")

class DatosPreofesion(models.Model):
    id_dato_academico = models.AutoField(primary_key=True)
    profesion_pregrado = models.CharField(max_length=150)
    universidad_egreso_pregrado = models.CharField(max_length=150)
    pais_profesion_pregrado = models.CharField(max_length=150)
    id_usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='id_profesional')

#ACTUALIZACION / PROPUESTA

class HistorialAsignaciones(models.Model):
    id_historial = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="historial_asignaciones")
    tipo_perfil = models.CharField(max_length=50)
    nucleo = models.ForeignKey(Nucleos, on_delete=models.SET_NULL, null=True, blank=True)
    pnf = models.ForeignKey(Pnf, on_delete=models.SET_NULL, null=True, blank=True)
    accion = models.CharField(max_length=30)
    fecha_hora = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha_hora"]

    def __str__(self):
        return f"{self.usuario} - {self.tipo_perfil} - {self.accion}"

class RolAcademico(models.Model): # Modelo creado para no redundar en datos de 3 usuarios
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    nucleo = models.ForeignKey(Nucleos, on_delete=models.CASCADE, blank=True, null=True)
    pnf = models.ForeignKey(Pnf, on_delete=models.CASCADE, blank=True, null=True)

    class Meta:
        abstract = True

class Estudiante(RolAcademico):
    id_estudiante = models.AutoField(primary_key=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["usuario", "nucleo", "pnf"],
                name="uq_estudiante_usuario_nucleo_pnf"
            )
        ]

    def __str__(self):
        return f"{self.usuario}"

class EstatusEstudiante(models.Model):
    PERFIL_COORDINADOR_PNF = "COORDINADOR_PNF"
    PERFIL_CONTROL_ESTUDIO = "CONTROL_ESTUDIO"

    PERFILES_REGISTRO = [
        (PERFIL_COORDINADOR_PNF, "Coordinador de PNF"),
        (PERFIL_CONTROL_ESTUDIO, "Control de Estudio"),
    ]

    id_estatus_estudiante = models.AutoField(primary_key=True)
    estatus = models.CharField(max_length=50)
    estado = models.CharField(max_length=50)
    ingreso = models.CharField(max_length=50)
    descripcion_ingreso = models.CharField(max_length=30)
    fecha_ingreso = models.DateField()

    trayecto = models.ForeignKey(TrayectoAcademico, models.CASCADE, db_column='trayecto')
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE, related_name="estatus")

    registrado_por = models.ForeignKey(Usuario, on_delete=models.PROTECT, related_name="estatus_estudiantes_registrados", blank=True, null=True)
    fecha_registro = models.DateTimeField(blank=True, null=True)
    perfil_registro = models.CharField(max_length=50, choices=PERFILES_REGISTRO, blank=True, null=True)

class AulaEstudiante(models.Model):
    id_aula_estudiante = models.AutoField(primary_key=True)
    aula = models.ForeignKey(AulaAcademica, on_delete=models.CASCADE, related_name="estudiantes")
    estatus = models.ForeignKey(EstatusEstudiante, on_delete=models.CASCADE, related_name="aulas_estudiante")
    fecha_inicio = models.DateField()
    fecha_final = models.DateField(null=True, blank=True)
    estado = models.CharField(
        max_length=20,
        choices=[
            ("Retiro", "Retiro"),
            ("Egreso", "Egreso"),
            ("Congelado", "Congelado"),
            ("Curso", "Curso")
        ],
        default="Curso"
    )

class DocumentosEstudiante(models.Model):
    id_documento = models.AutoField(primary_key=True)
    nombre_documento = models.CharField(max_length=50)
    archivo = models.FileField(upload_to="documentos_estudiante/")
    id_usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="documentos")

class InformacionSecundaria(models.Model):
    id_secundaria = models.AutoField(primary_key=True)
    tipo_institucion = models.CharField(max_length=100)
    nombre_institucion = models.CharField(max_length=100)
    fecha_grado = models.DateField()
    codigo_sni_opsu = models.CharField(max_length=100, unique=True)
    id_usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="informacion_secundaria")

class ContactoAuxiliar(models.Model):
    id_representante = models.AutoField(primary_key=True)
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    cedula_identidad = models.CharField(max_length=15)
    telefono = models.CharField(max_length=15)
    parentesco = models.CharField(max_length=25)
    id_usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="contactos_auxiliares")

class Discapacidad(models.Model):
    id_discapacidad = models.AutoField(primary_key=True)
    codigo_carnet_discapacidad = models.CharField(max_length=50)
    nro_registro_medico = models.CharField(max_length=5)
    tipo_discapacidad = models.CharField(max_length=20)
    grado_discapacidad = models.CharField(max_length=50)
    causa_discapacidad = models.CharField(max_length=50)
    id_usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="discapacidades")

class Docente(RolAcademico):
    id_docente = models.AutoField(primary_key=True)
    activo = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["usuario", "nucleo", "pnf"],
                name="uq_docente_usuario_nucleo_pnf"
            )
        ]

    def __str__(self):
        return f"{self.usuario}"

class MateriaAsignada(models.Model):
    id_materia_asignada = models.AutoField(primary_key=True)
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE, related_name="asignaciones")
    activo = models.BooleanField(default=True)
    fecha_asignacion = models.DateTimeField(auto_now_add=True)
    fecha_suspension = models.DateTimeField(null=True, blank=True)

    registrado_por = models.ForeignKey(Usuario, on_delete=models.PROTECT, related_name="asignaciones_materias_registradas", blank=True, null=True)
    fecha_registro = models.DateTimeField(blank=True, null=True)
    perfil_registro = models.CharField(max_length=50, blank=True, null=True)
    observacion_registro = models.TextField(blank=True, null=True)

    modificado_por = models.ForeignKey(Usuario, on_delete=models.PROTECT, related_name="asignaciones_materias_modificadas", blank=True, null=True)
    fecha_modificacion = models.DateTimeField(blank=True, null=True)
    perfil_modificacion = models.CharField(max_length=50, blank=True, null=True)
    observacion_modificacion = models.TextField(blank=True, null=True)

class DocenteAsignadoMateria(models.Model):
    materia_asignada = models.ForeignKey(MateriaAsignada, on_delete=models.CASCADE, related_name="docentes")
    docente = models.ForeignKey(Docente, on_delete=models.CASCADE, related_name="materias_asignadas")
    rol = models.CharField(
        max_length=20,
        choices=[
            ("PRINCIPAL", "Docente Principal"),
            ("SECUNDARIO", "Docente Secundario"),
        ]
    )
    activo = models.BooleanField(default=True)
    fecha_asignacion = models.DateTimeField(auto_now_add=True)
    fecha_suspension = models.DateTimeField(null=True, blank=True)

    registrado_por = models.ForeignKey(Usuario, on_delete=models.PROTECT, related_name="asignaciones_docentes_registradas", blank=True, null=True)
    fecha_registro = models.DateTimeField(blank=True, null=True)
    perfil_registro = models.CharField(max_length=50, blank=True, null=True)
    observacion_registro = models.TextField(blank=True, null=True)

    modificado_por = models.ForeignKey(Usuario, on_delete=models.PROTECT, related_name="asignaciones_docentes_modificadas", blank=True, null=True)
    fecha_modificacion = models.DateTimeField(blank=True, null=True)
    perfil_modificacion = models.CharField(max_length=50, blank=True, null=True)
    observacion_modificacion = models.TextField(blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["materia_asignada"],
                condition=models.Q(
                    rol="PRINCIPAL",
                    activo=True
                ),
                name="uq_docente_principal_activo"
            ),
            models.UniqueConstraint(
                fields=["materia_asignada"],
                condition=models.Q(
                    rol="SECUNDARIO"
                ),
                name="uq_docente_secundario"
            ),
        ]

class CoordinadorPNF(RolAcademico):
    id_coordinador = models.AutoField(primary_key=True)
    activo = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["usuario", "nucleo", "pnf"],
                name="uq_coordinadorpnf_usuario_nucleo_pnf"
            )
        ]
    
    def __str__(self):
        return f"{self.usuario}"

class ControlEstudio(models.Model):
    id_control = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name="controles_estudio"
    )
    nucleo = models.ForeignKey(
        Nucleos,
        on_delete=models.CASCADE,
        related_name="controles_estudio"
    )
    activo = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["usuario", "nucleo"],
                name="uq_control_usuario_nucleo"
            )
        ]

    def __str__(self):
        return f"{self.usuario}"

class DirectorGeneral(models.Model):
    id_director = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name="directores_generales"
    )
    nucleo = models.ForeignKey(
        Nucleos,
        on_delete=models.CASCADE,
        related_name="directores_generales"
    )
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["usuario", "nucleo"],
                name="uq_director_usuario"
            )
        ]

    def __str__(self):
        return f"{self.usuario}"


class Autoridades(models.Model):
    id_autoridad = models.AutoField(primary_key=True)
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    cedula_identidad = models.CharField(max_length=15, unique=True)
    genero = models.CharField(max_length=50)
    cargo = models.CharField(max_length=100)
    resolucion = models.CharField(max_length=100, unique=True)

class Bitacora(models.Model):
    id_bitacora = models.AutoField(primary_key=True)
    nombre_usuario = models.CharField(max_length=50)
    fecha_hora = models.DateTimeField()
    accion = models.TextField()

class VerificacionCodigo(models.Model):
    id_codigo = models.AutoField(primary_key=True)
    cedula_identidad = models.CharField(max_length=12)
    token = models.CharField(null=True, blank=True)
    codigo = models.CharField(max_length=10)
    creado = models.DateTimeField()
    intentos = models.PositiveIntegerField(default=0)
    bloqueado_hasta = models.DateTimeField(null=True, blank=True)
    activo = models.IntegerField()
    descripcion = models.CharField(max_length=100)
    fecha_expiracion = models.DateTimeField(null=True, blank=True)
