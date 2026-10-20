from django.shortcuts import render
from django.http import JsonResponse
from django.db import transaction
from django.utils import timezone
from decimal import Decimal, InvalidOperation

from inicio_sesion.models import TrayectoAcademico, MateriaAsignada, Usuario, PNFNucleo, Bitacora, Pnf, Materia, PeriodoAcademico, PeriodoAcademicoMateria, DirectorGeneral, ControlEstudio

def tray_reg_acad(request):
    trayectos = TrayectoAcademico.objects.all().values(
        "id_periodo_academico",
        "nombre"
    )

    return JsonResponse({
        "estado": "exito",
        "trayectos": list(trayectos)
    })

def pnf_per_acad(request):
    if request.method == "POST":
        periodo_materia = request.POST.get("periodo_academico")
        usuario = Usuario.objects.get(cedula_identidad=request.session.get("cedula_usuario"))

        if DirectorGeneral.objects.filter(usuario=usuario).exists():
            nucleos = DirectorGeneral.objects.filter(usuario=usuario).values_list("nucleo_id", flat=True)

        elif ControlEstudio.objects.filter(usuario=usuario).exists():
            nucleos = ControlEstudio.objects.filter(usuario=usuario).values_list("nucleo_id", flat=True)

        # Si es reparación muestra todos los PNF del núcleo
        if periodo_materia == "REPARACION":
            pnfs = PNFNucleo.objects.filter(
                id_nucleo__in=nucleos
            ).select_related(
                "id_pnf"
            )
        else:
            if (
                periodo_materia == "INICIAL_TRIMESTRE" or
                periodo_materia.startswith("TRAMO") or
                periodo_materia == "TRIMESTRE"
            ):
                tipo_periodo = "Trimestre"
            elif (
                periodo_materia == "INICIAL_SEMESTRE" or
                periodo_materia.startswith("SEMESTRE")
            ):
                tipo_periodo = "Semestre"

            pnfs = PNFNucleo.objects.filter(
                id_nucleo__in=nucleos,
                id_pnf__periodo_academico=tipo_periodo
            ).select_related(
                "id_pnf"
            )

        datos = {}
        for pnf_nucleo in pnfs:
            nucleo = pnf_nucleo.id_nucleo.municipio
            if nucleo not in datos:
                datos[nucleo] = []

            datos[nucleo].append({
                "id_pnf": pnf_nucleo.id_pnf.id_pnf,
                "pnf": pnf_nucleo.id_pnf.pnf
            })

        return JsonResponse({
            "estado": "exito",
            "nucleos": [ 
                {
                    "nucleo": nucleo,
                    "pnfs": lista
                }
                for nucleo, lista in datos.items()
            ]
        })
    
def mat_lista(request):
    if request.method == "POST":
        cedula_usuario = request.session.get("cedula_usuario")
        nucleo = None

        # BUSCAR DIRECTOR GENERAL
        director = DirectorGeneral.objects.filter(
            usuario__cedula_identidad=cedula_usuario
        ).select_related(
            "nucleo"
        ).first()

        if director:
            nucleo = director.nucleo

        # BUSCAR CONTROL DE ESTUDIO
        if not nucleo:
            control = ControlEstudio.objects.filter(
                usuario__cedula_identidad=cedula_usuario
            ).select_related(
                "nucleo"
            ).first()

            if control:
                nucleo = control.nucleo

        # VALIDAR NÚCLEO
        if not nucleo:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Error",
                "desccripcion": "El usuario no tiene núcleo asignado."
            })

        # PNF ASIGNADOS AL NÚCLEO
        pnfs_usuario = Pnf.objects.filter(pnfnucleo__id_nucleo_id=nucleo.id_nucleo).distinct()

        pnf = request.POST.get("pnf")

        # MATERIAS
        materias_query = Materia.objects.select_related(
            "id_pnf",
            "id_trayecto"
        ).filter(
            id_pnf__in=pnfs_usuario
        )

        # FILTRAR POR PNF
        if pnf and pnf != "ninguno":
            materias_query = materias_query.filter(id_pnf=pnf)

        # OBTENER MATERIAS
        materias = list(
            materias_query.values(
                "id_materia",
                "nombre",
                "codigo",
                "htea",
                "htei",
                "recuperacion",
                "id_pnf",
                "id_trayecto",
                "id_trayecto__nombre",
                "tipo_materia",
            )
        )

        # OBTENER PNFS
        pnfs = list(
            pnfs_usuario.values(
                "id_pnf",
                "pnf",
                "codigo"
            )
        )

        return JsonResponse({
            "estado": "exito",
            "materias": materias,
            "pnfs": pnfs
        })

    return render(request, "Roles/Director_General/materia/visualizar_materia.html")

def mat_datos(request):
    if request.method == "POST":
        codigo = request.POST.get("codigo")

        if not codigo:
            return JsonResponse({
                "estado": "fallo",
                "title": "Código requerido",
                "icon": "warning",
                "descripcion": "Debe indicar el código de la materia."
            })

        try:
            materia = (
                Materia.objects
                .select_related(
                    "id_pnf",
                    "id_trayecto",
                )
                .prefetch_related(
                    "periodos_academicos__periodo"
                )
                .get(codigo=codigo)
            )
        except Materia.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "title": "Error",
                "icon": "error",
                "descripcion": "La materia no se encuentra registrada."
            })

        # PERÍODOS ACADÉMICOS
        relaciones_periodos = materia.periodos_academicos.all()

        periodos_materia = [
            relacion.periodo.nombre
            for relacion in relaciones_periodos
        ]

        periodos = [
            {
                "id_periodo_academico": relacion.periodo.id_periodo_academico,
                "nombre": relacion.periodo.nombre,
            }
            for relacion in relaciones_periodos
        ]

        # TIPO DE PERÍODO
        mapa_periodos = {
            frozenset(["Inicial Trimestre"]):
                "INICIAL_TRIMESTRE",
            frozenset(["Inicial Semestre"]):
                "INICIAL_SEMESTRE",
            frozenset(["Reparación"]):
                "REPARACION",
            frozenset(["Tramo I"]):
                "TRAMO_I",
            frozenset(["Tramo II"]):
                "TRAMO_II",
            frozenset(["Tramo III"]):
                "TRAMO_III",
            frozenset(["Tramo I", "Tramo II"]):
                "TRAMO_I_II",
            frozenset(["Tramo II", "Tramo III"]):
                "TRAMO_II_III",
            frozenset(["Tramo I", "Tramo III"]):
                "TRAMO_I_III",
            frozenset([
                "Tramo I",
                "Tramo II",
                "Tramo III"
            ]):
                "TRIMESTRE",
            frozenset(["Semestre I"]):
                "SEMESTRE_I",
            frozenset(["Semestre II"]):
                "SEMESTRE_II",
            frozenset([
                "Semestre I",
                "Semestre II"
            ]):
                "SEMESTRE",
        }

        tipo_periodo = mapa_periodos.get(
            frozenset(periodos_materia)
        )

        return JsonResponse({
            "estado": "exito",
            "materia": {
                "id_materia": materia.id_materia,
                "nombre": materia.nombre,
                "codigo": materia.codigo,
                "recuperacion": materia.recuperacion,
                "htea": materia.htea,
                "htei": materia.htei,
                "thte": materia.thte,
                "uc": materia.uc,
                "activa": materia.activa,
                "tipo_materia": materia.tipo_materia,
                "trayecto": {
                    "id_trayecto": materia.id_trayecto.pk,
                    "nombre": materia.id_trayecto.nombre,
                },
                "periodos_academicos": periodos,
                "tipo_periodo": tipo_periodo,
            },
            "pnf": {
                "id_pnf": materia.id_pnf.id_pnf,
                "pnf": materia.id_pnf.pnf,
                "codigo": materia.id_pnf.codigo,
            }
        })

def tract_selec_mat(request):
    if request.method == "POST":
        periodo_academico = request.POST.get("periodo_academico")

        if not periodo_academico:
            return JsonResponse({
                "estado": "fallo",
                "title": "Periodo requerido",
                "icon": "warning",
                "descripcion": "Debe seleccionar un periodo académico."
            })

        # TRAYECTO INICIAL
        periodos_iniciales = {
            "INICIAL_TRIMESTRE",
            "INICIAL_SEMESTRE",
        }

        # TRIMESTRE / TRAMOS
        periodos_trimestre = {
            "TRIMESTRE",
            "TRAMO_I",
            "TRAMO_II",
            "TRAMO_III",
            "TRAMO_I_II",
            "TRAMO_II_III",
            "TRAMO_I_III",
        }

        # SEMESTRE
        periodos_semestre = {
            "SEMESTRE",
            "SEMESTRE_I",
            "SEMESTRE_II",
        }

        # DETERMINAR TRAYECTOS
        if periodo_academico in periodos_iniciales:
            trayectos = TrayectoAcademico.objects.filter(nombre="Trayecto Inicial")

        elif periodo_academico in periodos_trimestre:
            trayectos = TrayectoAcademico.objects.filter(
                nombre__in=[
                    "Trayecto I",
                    "Trayecto II",
                    "Trayecto III",
                    "Trayecto IV",
                ]
            )

        elif periodo_academico in periodos_semestre:
            trayectos = TrayectoAcademico.objects.filter(
                nombre__in=[
                    "Trayecto I",
                    "Trayecto II",
                    "Trayecto III",
                    "Trayecto IV",
                    "Trayecto V",
                ]
            )

        elif periodo_academico == "REPARACION":
            # Reparación puede corresponder a cualquiera
            trayectos = TrayectoAcademico.objects.all()

        else:
            return JsonResponse({
                "estado": "fallo",
                "title": "Periodo inválido",
                "icon": "warning",
                "descripcion": "El periodo académico seleccionado no es válido."
            })

        trayectos = trayectos.order_by("id_periodo_academico")
        datos_trayectos = [
            {
                "id_trayecto": trayecto.id_periodo_academico,
                "nombre": trayecto.nombre,
            }
            for trayecto in trayectos
        ]

        return JsonResponse({
            "estado": "exito",
            "trayectos": datos_trayectos
        })

def pnf_selec_mat(request):
    if request.method == "POST":
        periodo_academico = request.POST.get("periodo_academico")

        if not periodo_academico:
            return JsonResponse({
                "estado": "fallo",
                "title": "Periodo requerido",
                "icon": "warning",
                "descripcion": "Debe seleccionar un periodo académico."
            })

        # OBTENER USUARIO
        try:
            usuario = Usuario.objects.get(cedula_identidad=request.session.get("cedula_usuario"))
        except Usuario.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "title": "Usuario no encontrado",
                "icon": "error",
                "descripcion": "No se pudo identificar el usuario."
            })

        # OBTENER NÚCLEOS DEL USUARIO
        if DirectorGeneral.objects.filter(usuario=usuario).exists():
            nucleos = DirectorGeneral.objects.filter(
                usuario=usuario
            ).values_list(
                "nucleo_id",
                flat=True
            )

        elif ControlEstudio.objects.filter(usuario=usuario).exists():
            nucleos = ControlEstudio.objects.filter(
                usuario=usuario
            ).values_list(
                "nucleo_id",
                flat=True
            )
        else:
            return JsonResponse({
                "estado": "fallo",
                "title": "Acceso denegado",
                "icon": "error",
                "descripcion": "El usuario no tiene un núcleo asignado."
            })

        # DETERMINAR TIPO DE PNF
        periodos_trimestre = {
            "TRIMESTRE",
            "TRAMO_I",
            "TRAMO_II",
            "TRAMO_III",
            "TRAMO_I_II",
            "TRAMO_II_III",
            "TRAMO_I_III",
            "INICIAL_TRIMESTRE",
        }

        periodos_semestre = {
            "SEMESTRE",
            "SEMESTRE_I",
            "SEMESTRE_II",
            "INICIAL_SEMESTRE",
        }

        # REPARACIÓN
        if periodo_academico == "REPARACION":
            tipo_pnf = "Todos"

            pnfs = Pnf.objects.filter(
                pnfnucleo__id_nucleo__in=nucleos
            ).order_by("pnf")

        # TRIMESTRE
        elif periodo_academico in periodos_trimestre:
            tipo_pnf = "Trimestre"

            pnfs = Pnf.objects.filter(
                periodo_academico="Trimestre",
                pnfnucleo__id_nucleo__in=nucleos
            ).order_by("pnf")

        # SEMESTRE
        elif periodo_academico in periodos_semestre:
            tipo_pnf = "Semestre"

            pnfs = Pnf.objects.filter(
                periodo_academico="Semestre",
                pnfnucleo__id_nucleo__in=nucleos
            ).order_by("pnf")

        # PERIODO INVÁLIDO
        else:
            return JsonResponse({
                "estado": "fallo",
                "title": "Periodo inválido",
                "icon": "warning",
                "descripcion": "El periodo académico seleccionado no es válido."
            })

        # ELIMINAR DUPLICADOS
        pnfs = pnfs.distinct()

        # CONSTRUIR RESPUESTA
        datos_pnf = [
            {
                "id_pnf": pnf.id_pnf,
                "pnf": pnf.pnf,
                "codigo": pnf.codigo,
                "periodo_academico": pnf.periodo_academico,
            }
            for pnf in pnfs
        ]

        return JsonResponse({
            "estado": "exito",
            "tipo_pnf": tipo_pnf,
            "pnfs": datos_pnf
        })
    
def mat_guardar(request):
    if request.method == "POST":

        id_materia = request.POST.get("materiaseleccionado")
        nombre = request.POST.get("nombresmaterias")
        thea = request.POST.get("THEA")
        thei = request.POST.get("THEI")
        reparacion_materia = request.POST.get("reparacionmateria")
        pnf_materia = request.POST.get("pnfmateria")
        periodo_materia = request.POST.get("periodomateria")
        trayecto_materia = request.POST.get("trayecto")
        tipo_materia = request.POST.get("tipo_materia")

        cedula_usuario = request.session.get("cedula_usuario")

        if not cedula_usuario:
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Sesión no válida",
                "descripcion": (
                    "No se encontró el usuario en la sesión."
                )
            })

        # OBTENER USUARIO
        usuario_registro = Usuario.objects.filter(
            cedula_identidad=cedula_usuario
        ).first()

        if not usuario_registro:
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Usuario no encontrado",
                "descripcion": (
                    "No se encontró el usuario que realiza "
                    "la modificación."
                )
            })

        # DETERMINAR PERFIL
        perfil_modificacion = None

        director = DirectorGeneral.objects.filter(
            usuario__cedula_identidad=cedula_usuario
        ).first()

        if director:
            perfil_modificacion = "DIRECTOR_GENERAL"

        else:
            control_estudio = ControlEstudio.objects.filter(
                usuario__cedula_identidad=cedula_usuario,
                activo=True
            ).first()

            if control_estudio:
                perfil_modificacion = "CONTROL_ESTUDIO"

        if not perfil_modificacion:
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Perfil no autorizado",
                "descripcion": (
                    "El usuario no posee un perfil autorizado "
                    "para modificar materias."
                )
            })

        # VALIDAR DATOS
        controles = [
            (nombre, "Nombre de la Materia", "Por favor, debe ingresar el nombre de la materia."),
            (reparacion_materia, "Reparación de la Materia", "Por favor, seleccione si la materia tiene posibilidad de reparación."),
            (pnf_materia, "PNF de la Materia", "Por favor, seleccione el PNF al que pertenecerá la materia."),
            (periodo_materia, "Periodo Académico", "Por favor, seleccione el periodo académico de la materia."),
            (trayecto_materia, "Trayecto", "Por favor, seleccione el trayecto de la materia."),
            (thea, "Hora Trabajo Estudio Acompañado (HTEA)", "Por favor, debe ingresar las horas totales de estudio acompañado."),
            (thei, "Hora Trabajo Estudio Independiente (HTEI)", "Por favor, debe ingresar las horas totales de estudio independiente."),
            (tipo_materia, "Tipo de Materia", "Por favor, debe seleccionar el tipo de la materia.")
        ]

        for value, field_name, error_message in controles:
            if not value:
                return JsonResponse({
                    "estado": "fallo",
                    "icon": "warning",
                    "title": field_name,
                    "descripcion": error_message
                })

        # BUSCAR MATERIA
        try:
            materia = Materia.objects.get(id_materia=id_materia)
        except Materia.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "No Existe",
                "descripcion": (
                    "La materia no se encuentra registrada."
                )
            })

        # COMPROBAR ASIGNACIÓN
        asignacion = MateriaAsignada.objects.filter(materia=materia).first()
        if asignacion:
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Materia no modificable",
                "descripcion": (
                    "La materia no puede modificarse porque "
                    "ya se encuentra asignada a un docente."
                )
            })

        # CONVERTIR HORAS
        try:
            htea = Decimal(thea.replace(",", "."))

            htei = Decimal(thei.replace(",", "."))
        except (InvalidOperation, AttributeError):
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Horas inválidas",
                "descripcion": (
                    "Las horas ingresadas no tienen "
                    "un formato válido."
                )
            })

        try:
            with transaction.atomic():
                # ACTUALIZAR MATERIA
                materia.nombre = nombre
                materia.recuperacion = reparacion_materia
                materia.htea = htea
                materia.htei = htei
                materia.tipo_materia = tipo_materia
                materia.id_pnf_id = pnf_materia
                materia.id_trayecto_id = trayecto_materia

                # DATOS DE MODIFICACIÓN
                materia.modificado_por = usuario_registro
                materia.fecha_modificacion = timezone.now()
                materia.perfil_modificacion = perfil_modificacion
                materia.save()

                # ACTUALIZAR PERÍODOS ACADÉMICOS
                mapa_periodos = {
                    "INICIAL_TRIMESTRE": ["Inicial Trimestre"],
                    "INICIAL_SEMESTRE": ["Inicial Semestre"],
                    "REPARACION": ["Reparación"],
                    "TRAMO_I": ["Tramo I"],
                    "TRAMO_II": ["Tramo II"],
                    "TRAMO_III": ["Tramo III"],
                    "TRAMO_I_II": ["Tramo I", "Tramo II"],
                    "TRAMO_II_III": ["Tramo II", "Tramo III"],
                    "TRAMO_I_III": ["Tramo I", "Tramo III"],
                    "TRIMESTRE": [
                        "Tramo I",
                        "Tramo II",
                        "Tramo III"
                    ],
                    "SEMESTRE_I": ["Semestre I"],
                    "SEMESTRE_II": ["Semestre II"],
                    "SEMESTRE": [
                        "Semestre I",
                        "Semestre II"
                    ],
                }

                nombres_periodos = mapa_periodos.get(
                    periodo_materia
                )

                if not nombres_periodos:
                    return JsonResponse({
                        "estado": "fallo",
                        "icon": "warning",
                        "title": "Periodo inválido",
                        "descripcion": (
                            "El periodo académico seleccionado "
                            "no es válido."
                        )
                    })

                periodos = PeriodoAcademico.objects.filter(
                    nombre__in=nombres_periodos
                )

                if periodos.count() != len(nombres_periodos):
                    return JsonResponse({
                        "estado": "fallo",
                        "icon": "error",
                        "title": "Periodo no encontrado",
                        "descripcion": (
                            "Uno o más períodos académicos no "
                            "se encuentran registrados en el sistema."
                        )
                    })

                PeriodoAcademicoMateria.objects.filter(materia=materia).delete()

                PeriodoAcademicoMateria.objects.bulk_create([
                    PeriodoAcademicoMateria(
                        materia=materia,
                        periodo=periodo
                    )
                    for periodo in periodos
                ])

                Bitacora.objects.create(
                    nombre_usuario=request.session.get("usuario_nombre"),
                    fecha_hora=timezone.now(),
                    accion=(
                        f"Actualizó la materia "
                        f"'{materia.nombre}'."
                    )
                )

            return JsonResponse({
                "estado": "exito",
                "icon": "success",
                "title": "Éxito",
                "descripcion": (
                    "La materia se actualizó exitosamente."
                )
            })

        except Exception as e:
            print(e)

            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Error al actualizar",
                "descripcion": (
                    "Ocurrió un error inesperado al actualizar "
                    "la materia. Por favor, intente nuevamente."
                )
            })

    return render(request, "Roles/Director_General/materia/actualizar_materia.html")

def nombre_materia(request):
    if request.method == "POST":
        nombre = request.POST.get("nombre")

        existe = Materia.objects.filter(nombre__iexact=nombre).exists()
        if existe:
            return JsonResponse({ "existe": True })

        return JsonResponse({ "existe": False })

def codigo_materia(request):
    if request.method == "POST":
        codigo = request.POST.get("codigo")

        existe = Materia.objects.filter(codigo__iexact=codigo).exists()
        if existe:
            return JsonResponse({ "existe": True })

        return JsonResponse({ "existe": False })

def reg_mat(request):
    if request.method == "POST":
        nombre = request.POST.get("nombresmaterias")
        codigo = request.POST.get("codigosmaterias")
        periodo_materia = request.POST.get("periodomateria")
        thea = request.POST.get("THEA")
        thei = request.POST.get("THEI")
        trayecto = request.POST.get("trayectomateria")
        reparacion = request.POST.get("reparacionmateria")
        pnf = request.POST.get("pnfmateria")
        tipo_materia = request.POST.get("tipo_materia")

        controles = [
            (nombre, "Nombre de la Materia", "Por favor, debe ingresar el nombre de la materia."),
            (codigo, "Código de la Materia", "Por favor, debe ingresar el código de la Materia."),
            (periodo_materia, "Periodo Académico", "Por favor, debe seleccionar el periodo académico."),
            (trayecto, "Trayecto Académico", "Por favor, debe seleccionar el taryecto académico."),
            (reparacion, "Reparación", "Por favor, debe seleccionar la posibilidad de reparación."),
            (thea, "Hora Trabajo Estudio Acompañado (HTEA)", "Por favor, debe ingresar las hotas totales de estudio acompañado."),
            (thei, "Hora Trabajo Estudio Independiente (HTEI)", "Por favor, debe ingresar las hotas totales de estudio independiente."),
            (pnf, "P.N.F", "Por favor, debe seleccionar el PNF."),
            (tipo_materia, "Tipo de Materia", "Por favor, debe seleccionar el Tipo de Materia.")
        ]

        for value, field_name, error_message in controles:
            if not value:
                return JsonResponse({
                    "estado": "fallo",
                    "icon": "warning",
                    "title": field_name,
                    "descripcion": error_message
                })

        pnf_obj = Pnf.objects.get(id_pnf=pnf)
        trayecto_obj = TrayectoAcademico.objects.get(id_periodo_academico=trayecto)

        mapa_periodo_bd = {
            "INICIAL_TRIMESTRE": ["Inicial Trimestre"],
            "INICIAL_SEMESTRE": ["Inicial Semestre"],
            "REPARACION": ["Reparación"],
            "TRIMESTRE": ["Tramo I", "Tramo II", "Tramo III"],
            "TRAMO_I": ["Tramo I"],
            "TRAMO_II": ["Tramo II"],
            "TRAMO_III": ["Tramo III"],
            "TRAMO_I_II": ["Tramo I", "Tramo II"],
            "TRAMO_II_III": ["Tramo II", "Tramo III"],
            "TRAMO_I_III": ["Tramo I", "Tramo III"],
            "SEMESTRE": ["Semestre I", "Semestre II"],
            "SEMESTRE_I": ["Semestre I"],
            "SEMESTRE_II": ["Semestre II"],
        }

        valores = mapa_periodo_bd.get(periodo_materia)
        if not valores:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Error",
                "descripcion": "Periodo inválido."
            })

        periodos = PeriodoAcademico.objects.filter(nombre__in=valores)
        if not periodos.exists():
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "descripcion": "No existen periodos académicos."
            })

        cedula_usuario = request.session.get("cedula_usuario")

        usuario_registro = Usuario.objects.filter(
            cedula_identidad=cedula_usuario
        ).first()

        if not usuario_registro:
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Usuario no encontrado",
                "descripcion": (
                    "No se encontró el usuario que realiza el registro."
                )
            })
        
        perfil_registro = None
        nucleo_registro = None

        director = DirectorGeneral.objects.select_related(
            "nucleo"
        ).filter(
            usuario=usuario_registro
        ).first()

        if director:
            perfil_registro = "DIRECTOR_GENERAL"
            nucleo_registro = director.nucleo

        else:
            control_estudio = ControlEstudio.objects.select_related(
                "nucleo"
            ).filter(
                usuario=usuario_registro,
                activo=True
            ).first()

            if control_estudio:
                perfil_registro = "CONTROL_ESTUDIO"
                nucleo_registro = control_estudio.nucleo

        pnf_nucleo = PNFNucleo.objects.filter(id_nucleo=nucleo_registro, id_pnf=pnf_obj).exists()
        if not pnf_nucleo:
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "PNF no válido",
                "descripcion": (
                    "El PNF seleccionado no pertenece al núcleo "
                    "asignado al usuario."
                )
            })


        with transaction.atomic():
            materia = Materia.objects.create(
                nombre=nombre,
                codigo=codigo,
                htea=Decimal(thea.replace(",", ".")),
                htei=Decimal(thei.replace(",", ".")),
                recuperacion=reparacion,
                id_trayecto=trayecto_obj,
                id_pnf=pnf_obj,
                tipo_materia=tipo_materia,
                registrado_por=usuario_registro,
                fecha_registro=timezone.now(),
                perfil_registro=perfil_registro
            )

            periodo_materias = []

            for periodo in periodos:
                pm = PeriodoAcademicoMateria.objects.create(
                    materia=materia,
                    periodo=periodo
                )
                periodo_materias.append(pm)

            Bitacora.objects.create(
                nombre_usuario=request.session.get("usuario_nombre"),
                fecha_hora=timezone.now(),
                accion=f"Registró la materia '{materia.nombre}' ({materia.codigo}) en el PNF '{pnf_obj.pnf}'."
            )

            return JsonResponse({
                "estado": "exito",
                "icon": "success",
                "title": "Éxito",
                "descripcion": "Materia registrada correctamente."
            })

        return JsonResponse({
            "estado": "fallo",
            "icon": "error",
            "title": "Error",
            "descripcion": "Hubo un error al registrar los datos del PNF."
        })

    return render(request, "Roles/Director_General/materia/registrar_materias.html")

