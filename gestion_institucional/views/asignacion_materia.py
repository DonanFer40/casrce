from django.shortcuts import render
from django.http import JsonResponse
from django.db import transaction
from django.utils import timezone

from inicio_sesion.models import PNFNucleo, ControlEstudio, Usuario, Materia, TrayectoAcademico, MateriaAsignada, DocenteAsignadoMateria, CoordinadorPNF, Docente, Bitacora, Materia, SeccionAcademica

def tray_reg(request):
    coordinador = CoordinadorPNF.objects.get(usuario__cedula_identidad=request.session.get("cedula_usuario"))

    periodo = coordinador.pnf.periodo_academico

    trayectos = TrayectoAcademico.objects.all().order_by("id_periodo_academico")

    if periodo == "Trimestre":
        trayectos = trayectos[:5]

    elif periodo == "Semestre":
        trayectos = trayectos[:6]

    datos = [
        {
            "id_trayecto": trayecto.id_periodo_academico,
            "nombre": trayecto.nombre
        }
        for trayecto in trayectos
    ]

    return JsonResponse({
        "estado": "exito",
        "trayectos": datos
    })

def docs_reg(request):
    if request.method != "POST":
        return JsonResponse({
            "estado": "error",
            "titulo": "Solicitud no válida",
            "icon": "error",
            "descripcion": (
                "La solicitud debe realizarse mediante POST."
            )
        })

    cedula = request.session.get("cedula_usuario")
    pnf = request.POST.get("pnf_asignado", "").strip()
    perfil = request.POST.get("perfil", "").strip()


    if perfil == "COORDINADOR_PNF":

        coordinador = (
            CoordinadorPNF.objects
            .filter(
                usuario__cedula_identidad=cedula,
                activo=True
            )
            .select_related("pnf")
            .first()
        )

        if not coordinador:
            return JsonResponse({
                "estado": "error",
                "titulo": "Asignación no válida",
                "icon": "error",
                "descripcion": (
                    "No cuenta con un perfil activo de "
                    "Coordinador de PNF."
                )
            })

        if not coordinador.pnf_id:
            return JsonResponse({
                "estado": "error",
                "titulo": "PNF no asignado",
                "icon": "warning",
                "descripcion": (
                    "El perfil de Coordinador de PNF no tiene "
                    "un PNF asignado."
                )
            })

        # El PNF sale directamente del perfil del coordinador.
        pnf = coordinador.pnf_id


    # CONTROL DE ESTUDIO
    elif perfil == "CONTROL_ESTUDIO":

        control_estudio = (
            ControlEstudio.objects
            .filter(
                usuario__cedula_identidad=cedula,
                activo=True
            )
            .select_related("nucleo")
            .first()
        )

        if not control_estudio:
            return JsonResponse({
                "estado": "error",
                "titulo": "Asignación no válida",
                "icon": "error",
                "descripcion": (
                    "No cuenta con el perfil activo de "
                    "Control de Estudio."
                ),
                "usuarios": []
            })

        if not control_estudio.nucleo_id:
            return JsonResponse({
                "estado": "error",
                "titulo": "Núcleo no asignado",
                "icon": "warning",
                "descripcion": (
                    "El perfil de Control de Estudio no tiene "
                    "un núcleo asignado."
                ),
                "usuarios": []
            })

        if not pnf:
            return JsonResponse({
                "estado": "error",
                "titulo": "PNF no seleccionado",
                "icon": "warning",
                "descripcion": (
                    "Debe seleccionar un PNF."
                ),
                "usuarios": []
            })

        pnf_nucleo = (
            PNFNucleo.objects
            .filter(
                id_nucleo_id=control_estudio.nucleo_id,
                id_pnf_id=pnf
            )
            .select_related("id_pnf")
            .first()
        )

        if not pnf_nucleo:
            return JsonResponse({
                "estado": "error",
                "titulo": "PNF no válido",
                "icon": "error",
                "descripcion": (
                    "El PNF seleccionado no pertenece al "
                    "núcleo asignado al encargado de "
                    "Control de Estudio."
                ),
                "usuarios": []
            })

        pnf = pnf_nucleo.id_pnf_id
    else:

        return JsonResponse({
            "estado": "error",
            "titulo": "Perfil no válido",
            "icon": "error",
            "descripcion": (
                "El perfil seleccionado no es válido."
            )
        })
    docentes = (
        Docente.objects
        .filter(
            pnf_id=pnf,
            activo=True
        )
        .select_related("usuario")
        .order_by(
            "usuario__nombres",
            "usuario__apellidos"
        )
    )

    usuarios = []

    for docente in docentes:

        usuarios.append({
            "id_usuario": docente.usuario.id_usuario,
            "nombre": (
                f"{docente.usuario.nombres} "
                f"{docente.usuario.apellidos}"
            )
        })

    return JsonResponse({
        "estado": "exito",
        "usuarios": usuarios
    })

def mats_reg(request):
    pnf = request.POST.get("pnf_asignado", "").strip()
    docente_id = request.POST.get("docente_seleccionado", "").strip()
    rol_docente = request.POST.get("rol_docente", "").strip()
    perfil = request.POST.get("perfil", "").strip()
    cedula = request.session.get("cedula_usuario")

    print(perfil)

    if not cedula or not docente_id or not rol_docente or not perfil:
        return JsonResponse({
            "estado": "fallo",
            "title": "Datos incompletos",
            "icon": "warning",
            "descripcion": (
                "No se recibieron todos los datos necesarios."
            ),
            "materias": []
        })

    # VALIDAR ROL DEL DOCENTE
    if rol_docente not in [
        "PRINCIPAL",
        "SECUNDARIO"
    ]:
        return JsonResponse({
            "estado": "fallo",
            "title": "Rol no válido",
            "icon": "warning",
            "descripcion": (
                "El rol seleccionado para el docente no es válido."
            ),
            "materias": []
        })

    # COORDINADOR DE PNF
    if perfil == "COORDINADOR_PNF":
        coordinador = (
            CoordinadorPNF.objects
            .filter(
                usuario__cedula_identidad=cedula,
                activo=True
            )
            .select_related("pnf")
            .first()
        )

        if not coordinador:
            return JsonResponse({
                "estado": "fallo",
                "title": "Asignación no válida",
                "icon": "error",
                "descripcion": (
                    "No cuenta con un perfil activo de "
                    "Coordinador de PNF."
                ),
                "materias": []
            })

        if not coordinador.pnf_id:
            return JsonResponse({
                "estado": "fallo",
                "title": "PNF no asignado",
                "icon": "warning",
                "descripcion": (
                    "El Coordinador de PNF no tiene un "
                    "PNF asignado."
                ),
                "materias": []
            })

        # El PNF sale directamente del perfil.
        pnf_obj = coordinador.pnf
        pnf = coordinador.pnf_id

    # CONTROL DE ESTUDIO
    elif perfil == "CONTROL_ESTUDIO":
        control_estudio = (
            ControlEstudio.objects
            .filter(
                usuario__cedula_identidad=cedula,
                activo=True
            )
            .select_related("nucleo")
            .first()
        )

        if not control_estudio:
            return JsonResponse({
                "estado": "fallo",
                "title": "Asignación no válida",
                "icon": "error",
                "descripcion": (
                    "No cuenta con el perfil activo de "
                    "Control de Estudio."
                ),
                "materias": []
            })

        # Para Control de Estudio el PNF sí viene del frontend.
        if not pnf:
            return JsonResponse({
                "estado": "fallo",
                "title": "PNF no seleccionado",
                "icon": "warning",
                "descripcion": (
                    "Debe seleccionar un PNF."
                ),
                "materias": []
            })

        # Validar que el PNF pertenezca al núcleo
        # del Control de Estudio.
        pnf_nucleo = (
            PNFNucleo.objects
            .filter(
                id_nucleo_id=control_estudio.nucleo_id,
                id_pnf_id=pnf
            )
            .select_related("id_pnf")
            .first()
        )

        if not pnf_nucleo:
            return JsonResponse({
                "estado": "fallo",
                "title": "PNF no válido",
                "icon": "error",
                "descripcion": (
                    "El PNF seleccionado no pertenece al "
                    "núcleo asignado al encargado de "
                    "Control de Estudio."
                ),
                "materias": []
            })

        pnf_obj = pnf_nucleo.id_pnf
    else:
        return JsonResponse({
            "estado": "fallo",
            "title": "Perfil no válido",
            "icon": "error",
            "descripcion": (
                "El perfil seleccionado no es válido."
            ),
            "materias": []
        })

    # VALIDAR DOCENTE
    docente = (
        Docente.objects
        .filter(
            usuario_id=docente_id,
            pnf_id=pnf,
            activo=True
        )
        .select_related("usuario")
        .first()
    )

    if not docente:
        return JsonResponse({
            "estado": "fallo",
            "title": "Docente no encontrado",
            "icon": "error",
            "descripcion": (
                "El docente seleccionado no está asignado "
                "al PNF indicado."
            ),
            "materias": []
        })

    # OBTENER MATERIAS DEL PNF
    materias_pnf = (
        Materia.objects
        .filter(
            id_pnf=pnf_obj
        )
        .select_related(
            "id_trayecto"
        )
        .prefetch_related(
            "asignaciones__docentes"
        )
        .order_by(
            "id_trayecto__nombre",
            "nombre"
        )
    )

    materias = []
    for materia in materias_pnf:
        asignacion = (
            materia.asignaciones
            .filter(
                activo=True
            )
            .first()
        )

        tiene_principal = False
        tiene_secundario = False
        docente_ya_asignado = False
        rol_docente_asignado = None

        if asignacion:
            docentes = asignacion.docentes.all()

            tiene_principal = docentes.filter(rol="PRINCIPAL").exists()

            tiene_secundario = docentes.filter(rol="SECUNDARIO").exists()

            docente_asignado = docentes.filter(docente_id=docente.id_docente).first()

            if docente_asignado:
                docente_ya_asignado = True

                rol_docente_asignado = (
                    docente_asignado.rol
                )

        # DOCENTE YA ASIGNADO
        if docente_ya_asignado:
            estado = "AZUL"
            puede_asignar = False

        # AMBOS ROLES OCUPADOS
        elif tiene_principal and tiene_secundario:
            estado = "ROJO"
            puede_asignar = False

        # ASIGNAR PRINCIPAL
        elif rol_docente == "PRINCIPAL":
            if tiene_principal:
                estado = "AMARILLO"
                puede_asignar = False

            elif tiene_secundario:
                estado = "NARANJA"
                puede_asignar = True

            else:
                estado = "VERDE"
                puede_asignar = True

        # ASIGNAR SECUNDARIO
        elif rol_docente == "SECUNDARIO":
            if tiene_secundario:
                estado = "AMARILLO"
                puede_asignar = False

            elif tiene_principal:
                estado = "NARANJA"
                puede_asignar = True

            else:
                estado = "VERDE"
                puede_asignar = True

        else:
            estado = "ROJO"
            puede_asignar = False

        materias.append({
            "id_materia": materia.id_materia,
            "nombre": materia.nombre,
            "codigo": materia.codigo,

            "id_trayecto": materia.id_trayecto_id,
            "trayecto": materia.id_trayecto.nombre,

            "recuperacion": materia.recuperacion,
            "htea": materia.htea,
            "htei": materia.htei,
            "thte": materia.thte,
            "uc": materia.uc,

            "estado": estado,

            "tiene_principal": tiene_principal,
            "tiene_secundario": tiene_secundario,

            "docente_ya_asignado": docente_ya_asignado,
            "rol_docente_asignado": rol_docente_asignado,

            "puede_asignar": puede_asignar
        })

    return JsonResponse({
        "estado": "exito",
        "materias": materias
    })

def asig_mat_doc(request):
    if request.method == "POST":
        pnf_id = request.POST.get("pnfs_asignados", "").strip()
        docente_id = request.POST.get("docente", "").strip()
        rol_docente = request.POST.get("rol_docente", "").strip()
        materias_ids = request.POST.getlist("materias[]")
        perfil = request.POST.get("perfil", "").strip()
        cedula = request.session.get("cedula_usuario")

        controles = [
            (
                docente_id,
                "Docente",
                "Debe seleccionar un docente."
            ),
            (
                rol_docente,
                "Rol del Docente",
                "Debe seleccionar el rol del docente."
            ),
            (
                materias_ids,
                "Materias Académicas",
                "Debe seleccionar al menos una materia."
            ),
            (
                perfil,
                "Perfil",
                "No se recibió el perfil del usuario."
            )
        ]

        for value, field_name, error_message in controles:

            if not value:
                return JsonResponse({
                    "estado": "fallo",
                    "icon": "warning",
                    "title": field_name,
                    "descripcion": error_message
                })

        # OBTENER USUARIO QUE REALIZA LA OPERACIÓN
        usuario_registro = Usuario.objects.filter(
            cedula_identidad=cedula
        ).first()

        if not usuario_registro:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Usuario no encontrado",
                "descripcion": (
                    "No se encontró el usuario que realiza "
                    "la asignación."
                )
            })

        # COORDINADOR DE PNF
        if perfil == "COORDINADOR_PNF":
            coordinador = (
                CoordinadorPNF.objects
                .filter(
                    usuario__cedula_identidad=cedula,
                    activo=True
                )
                .select_related("pnf")
                .first()
            )

            if not coordinador:
                return JsonResponse({
                    "estado": "fallo",
                    "icon": "error",
                    "title": "Asignación no válida",
                    "descripcion": (
                        "No cuenta con un perfil activo de "
                        "Coordinador de PNF."
                    )
                })

            if not coordinador.pnf_id:
                return JsonResponse({
                    "estado": "fallo",
                    "icon": "warning",
                    "title": "PNF no asignado",
                    "descripcion": (
                        "El perfil de Coordinador de PNF no "
                        "tiene un PNF asignado."
                    )
                })

            # EL PNF SALE EXCLUSIVAMENTE DEL PERFIL
            pnf = coordinador.pnf

            # OBTENER NÚCLEO DEL PNF
            pnf_nucleo = (
                PNFNucleo.objects
                .filter(
                    id_pnf_id=coordinador.pnf_id
                )
                .select_related("id_nucleo")
                .first()
            )

            if not pnf_nucleo:
                return JsonResponse({
                    "estado": "fallo",
                    "icon": "error",
                    "title": "Núcleo no encontrado",
                    "descripcion": (
                        "El PNF asignado al Coordinador no "
                        "está asociado a ningún núcleo."
                    )
                })

            nucleo_id = pnf_nucleo.id_nucleo_id

        # CONTROL DE ESTUDIO
        elif perfil == "CONTROL_ESTUDIO":
            control_estudio = (
                ControlEstudio.objects
                .filter(
                    usuario__cedula_identidad=cedula,
                    activo=True
                )
                .select_related(
                    "nucleo"
                )
                .first()
            )

            if not control_estudio:
                return JsonResponse({
                    "estado": "fallo",
                    "icon": "error",
                    "title": "Asignación no válida",
                    "descripcion": (
                        "No cuenta con el perfil activo de "
                        "Control de Estudio."
                    )
                })

            if not control_estudio.nucleo_id:
                return JsonResponse({
                    "estado": "fallo",
                    "icon": "warning",
                    "title": "Núcleo no asignado",
                    "descripcion": (
                        "El perfil de Control de Estudio no "
                        "tiene un núcleo asignado."
                    )
                })

            # EL PNF VIENE DEL FRONTEND COMO FILTRO
            pnf_nucleo = (
                PNFNucleo.objects
                .filter(
                    id_nucleo_id=control_estudio.nucleo_id,
                    id_pnf_id=pnf_id
                )
                .select_related(
                    "id_pnf"
                )
                .first()
            )

            if not pnf_nucleo:
                return JsonResponse({
                    "estado": "fallo",
                    "icon": "error",
                    "title": "PNF no válido",
                    "descripcion": (
                        "El PNF seleccionado no pertenece "
                        "al núcleo asignado al encargado de "
                        "Control de Estudio."
                    )
                })

            pnf = pnf_nucleo.id_pnf

            nucleo_id = control_estudio.nucleo_id
        else:
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Perfil no válido",
                "descripcion": (
                    "El perfil seleccionado no es válido "
                    "para realizar esta operación."
                )
            })

        # PERÍODO ACADÉMICO DEL PNF
        periodo_academico = pnf.periodo_academico

        if periodo_academico not in [
            "Trimestre",
            "Semestre"
        ]:
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Período académico no configurado",
                "descripcion": (
                    "El PNF seleccionado no tiene configurado "
                    "un período académico válido."
                )
            })

        # OBTENER DOCENTE
        try:
            usuario_docente = Usuario.objects.get(pk=docente_id)
        except Usuario.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "title": "Docente no encontrado",
                "icon": "error",
                "descripcion": (
                    "El usuario seleccionado como docente "
                    "no se encuentra registrado."
                )
            })

        try:
            docente = (
                Docente.objects
                .get(
                    usuario=usuario_docente,
                    nucleo_id=nucleo_id,
                    pnf_id=pnf.id_pnf,
                    activo=True
                )
            )

        except Docente.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "title": "Docente no válido",
                "icon": "error",
                "descripcion": (
                    "El docente seleccionado no se encuentra "
                    "asignado al PNF correspondiente."
                )
            })

        # VALIDAR ROL
        if rol_docente not in ["PRINCIPAL", "SECUNDARIO"]:
            return JsonResponse({
                "estado": "fallo",
                "title": "Rol inválido",
                "icon": "warning",
                "descripcion": (
                    "El rol del docente seleccionado no es válido."
                )
            })

        # OBTENER MATERIAS
        materias = list(
            Materia.objects
            .filter(
                pk__in=materias_ids,
                id_pnf_id=pnf.id_pnf
            )
            .select_related(
                "id_trayecto",
                "id_pnf"
            )
        )

        if len(materias) != len(set(materias_ids)):
            return JsonResponse({
                "estado": "fallo",
                "title": "Materia inválida",
                "icon": "warning",
                "descripcion": (
                    "Una o más materias seleccionadas no existen "
                    "o no pertenecen al PNF seleccionado."
                )
            })

        fecha_registro = timezone.now()

        nombre_perfil = (
            "Coordinador de PNF"
            if perfil == "COORDINADOR_PNF"
            else "Encargado de Control de Estudio"
        )

        nombre_rol = (
            "Docente Principal"
            if rol_docente == "PRINCIPAL"
            else "Docente Secundario"
        )

        # REGISTRAR ASIGNACIONES
        with transaction.atomic():
            for materia in materias:
                asignacion = (
                    MateriaAsignada.objects
                    .filter(
                        materia=materia,
                        activo=True
                    )
                    .first()
                )

                if not asignacion:

                    asignacion = (
                        MateriaAsignada.objects.create(
                            materia=materia,
                            activo=True,
                            registrado_por=usuario_registro,
                            fecha_registro=fecha_registro,
                            perfil_registro=perfil,
                            observacion_registro=(
                                f"{nombre_perfil} "
                                f"{usuario_registro.nombres} "
                                f"{usuario_registro.apellidos} "
                                f"registró la asignación de la materia "
                                f"'{materia.nombre}'."
                            )
                        )
                    )

                docente_existente = (
                    DocenteAsignadoMateria.objects
                    .filter(
                        materia_asignada=asignacion,
                        docente=docente,
                        activo=True
                    )
                    .first()
                )

                if docente_existente:

                    nombre_rol_existente = (
                        "Docente Principal"
                        if docente_existente.rol == "PRINCIPAL"
                        else "Docente Secundario"
                    )

                    return JsonResponse({
                        "estado": "fallo",
                        "icon": "warning",
                        "title": "Docente ya asignado",
                        "descripcion": (
                            f"El docente "
                            f"'{docente.usuario.nombres} "
                            f"{docente.usuario.apellidos}' "
                            f"ya está asignado a la materia "
                            f"'{materia.nombre}' como "
                            f"{nombre_rol_existente}."
                        )
                    })

                docente_rol_existente = (
                    DocenteAsignadoMateria.objects
                    .filter(
                        materia_asignada=asignacion,
                        rol=rol_docente,
                        activo=True
                    )
                    .first()
                )

                if docente_rol_existente:
                    return JsonResponse({
                        "estado": "fallo",
                        "icon": "warning",
                        "title": "Rol ya asignado",
                        "descripcion": (
                            f"La materia '{materia.nombre}' "
                            f"ya tiene un {nombre_rol.lower()} "
                            f"asignado."
                        )
                    })

                activo_docente = (
                    rol_docente == "PRINCIPAL"
                )

                fecha_registro = timezone.now()

                observacion = (
                    f"Se asignó al docente "
                    f"{docente.usuario.nombres} "
                    f"{docente.usuario.apellidos} "
                    f"como "
                    f"{'Docente Principal' if rol_docente == 'PRINCIPAL' else 'Docente Secundario'} "
                    f"de la materia '{materia.nombre}'."
                )

                DocenteAsignadoMateria.objects.create(
                    materia_asignada=asignacion,
                    docente=docente,
                    rol=rol_docente,
                    activo=activo_docente,
                    registrado_por=usuario_registro,
                    fecha_registro=fecha_registro,
                    perfil_registro=perfil,
                    observacion_registro=observacion
                )

                Bitacora.objects.create(
                    nombre_usuario=request.session.get(
                        "usuario_nombre"
                    ),
                    fecha_hora=fecha_registro,
                    accion=(
                        f"{nombre_perfil} "
                        f"{usuario_registro.nombres} "
                        f"{usuario_registro.apellidos} "
                        f"asignó la materia "
                        f"'{materia.nombre}' al docente "
                        f"{docente.usuario.nombres} "
                        f"{docente.usuario.apellidos} "
                        f"como {nombre_rol}."
                    )
                )

        return JsonResponse({
            "estado": "exito",
            "title": "Éxito",
            "icon": "success",
            "descripcion": (
                "Las materias fueron asignadas correctamente."
            )
        })

    return render(request, "Roles/Control_Estudio/asignacion_materia/registrar_asignaciones.html")


def obt_pnfs_coord(request):
    if request.method != "POST":
        return JsonResponse({
            "estado": "fallo",
            "pnfs": []
        })

    cedula = request.session.get("cedula_usuario")
    perfil = request.POST.get("perfil", "").strip()

    if not cedula or not perfil:
        return JsonResponse({
            "estado": "fallo",
            "pnfs": []
        })

    resultado = []

    # COORDINADOR DE PNF
    if perfil == "COORDINADOR_PNF":

        coordinadores = (
            CoordinadorPNF.objects
            .filter(
                usuario__cedula_identidad=cedula,
                activo=True
            )
            .select_related(
                "nucleo",
                "pnf"
            )
        )

        if not coordinadores.exists():
            return JsonResponse({
                "estado": "fallo",
                "pnfs": []
            })

        resultado = [
            {
                "id_pnf": coordinador.pnf_id,
                "pnf": coordinador.pnf.pnf,
                "codigo": coordinador.pnf.codigo,
                "periodo_academico": coordinador.pnf.periodo_academico
            }
            for coordinador in coordinadores
        ]

    # CONTROL DE ESTUDIO
    elif perfil == "CONTROL_ESTUDIO":

        control_estudio = (
            ControlEstudio.objects
            .filter(
                usuario__cedula_identidad=cedula,
                activo=True
            )
            .select_related("nucleo")
            .first()
        )

        if not control_estudio or not control_estudio.nucleo_id:
            return JsonResponse({
                "estado": "fallo",
                "pnfs": []
            })

        pnfs = (
            PNFNucleo.objects
            .filter(
                id_nucleo_id=control_estudio.nucleo_id
            )
            .select_related("id_pnf")
            .order_by("id_pnf__pnf")
        )

        resultado = [
            {
                "id_pnf": pnf.id_pnf_id,
                "pnf": pnf.id_pnf.pnf,
                "codigo": pnf.id_pnf.codigo,
                "periodo_academico": pnf.id_pnf.periodo_academico
            }
            for pnf in pnfs
        ]

    else:
        return JsonResponse({
            "estado": "fallo",
            "pnfs": []
        })

    return JsonResponse({
        "estado": "exito",
        "pnfs": resultado
    })

def mat_asig(request):
    cedula = request.session.get("cedula_usuario")

    if not cedula:
        return JsonResponse({
            "estado": "fallo",
            "icon": "error",
            "title": "Sesión no válida",
            "descripcion": "No se encontró el usuario en la sesión.",
            "materias": []
        })

    if request.method != "POST":
        return JsonResponse({
            "estado": "fallo",
            "icon": "error",
            "title": "Solicitud no válida",
            "descripcion": "La solicitud debe realizarse mediante POST.",
            "materias": []
        })

    pnf = request.POST.get("pnf_asignado", "").strip()
    trayecto = request.POST.get("trayecto", "").strip()
    nombre_materia = request.POST.get("materia", "").strip()
    perfil = request.POST.get("perfil", "").strip()

    # CONTROL DE ESTUDIO
    if perfil == "CONTROL_ESTUDIO":

        control_estudio = (
            ControlEstudio.objects
            .filter(
                usuario__cedula_identidad=cedula,
                activo=True
            )
            .select_related("nucleo")
            .first()
        )

        if not control_estudio:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Asignación no válida",
                "descripcion": (
                    "No cuenta con el perfil de Encargado "
                    "de Control de Estudio."
                ),
                "materias": []
            })

        nucleo_id = control_estudio.nucleo_id

        if not nucleo_id:
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Núcleo no asignado",
                "descripcion": (
                    "El perfil de Control de Estudio no tiene "
                    "un núcleo asignado."
                ),
                "materias": []
            })

        # TODAS LAS ASIGNACIONES DE LOS PNF DEL NÚCLEO
        pnfs_nucleo = PNFNucleo.objects.filter(
            id_nucleo_id=nucleo_id
        ).values_list(
            "id_pnf_id",
            flat=True
        )

        materias = (
            MateriaAsignada.objects
            .filter(
                activo=True,
                materia__id_pnf_id__in=pnfs_nucleo
            )
            .select_related(
                "materia",
                "materia__id_trayecto",
                "materia__id_pnf"
            )
        )

    elif perfil == "COORDINADOR_PNF":

        coordinador = (
            CoordinadorPNF.objects
            .filter(
                usuario__cedula_identidad=cedula,
                activo=True
            )
            .select_related(
                "nucleo",
                "pnf"
            )
            .first()
        )

        if not coordinador:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Asignación no válida",
                "descripcion": (
                    "No cuenta con el perfil de Coordinador de PNF."
                ),
                "materias": []
            })

        pnf_id = coordinador.pnf_id

        materias = (
            MateriaAsignada.objects
            .filter(
                activo=True,
                materia__id_pnf_id=pnf_id
            )
            .select_related(
                "materia",
                "materia__id_trayecto",
                "materia__id_pnf"
            )
        )

    else:
        return JsonResponse({
            "estado": "fallo",
            "icon": "error",
            "title": "Perfil no válido",
            "descripcion": "El perfil seleccionado no es válido.",
            "materias": []
        })


    # FILTRO POR PNF
    if pnf:
        materias = materias.filter(
            materia__id_pnf_id=pnf
        )

    # FILTRO POR TRAYECTO
    if trayecto:
        materias = materias.filter(
            materia__id_trayecto_id=trayecto
        )

    # FILTRO POR NOMBRE DE MATERIA
    if nombre_materia:
        materias = materias.filter(
            materia__nombre__icontains=nombre_materia
        )

    datos = []

    for asignacion in materias:
        materia = asignacion.materia

        datos.append({
            "id_materia_asignada": asignacion.id_materia_asignada,
            "id_materia": materia.id_materia,
            "nombre": materia.nombre,
            "codigo": materia.codigo,

            "id_trayecto": materia.id_trayecto_id,
            "trayecto": materia.id_trayecto.nombre,

            "id_pnf": materia.id_pnf_id,
            "pnf": materia.id_pnf.pnf,

            "htea": materia.htea,
            "htei": materia.htei,
            "thte": materia.thte,
            "uc": materia.uc,
        })

    return JsonResponse({
        "estado": "exito",
        "materias": datos
    })

def tray_mat_asg(request):
    if request.method != "POST":
        return JsonResponse({
            "estado": "fallo",
            "icon": "error",
            "title": "Solicitud inválida",
            "descripcion": "La solicitud debe realizarse mediante POST.",
            "trayectos": []
        })

    cedula = request.session.get("cedula_usuario")
    perfil = request.POST.get("perfil", "").strip()

    if not cedula or not perfil:
        return JsonResponse({
            "estado": "fallo",
            "icon": "warning",
            "title": "Datos incompletos",
            "descripcion": "No se recibieron todos los datos necesarios.",
            "trayectos": []
        })

    # COORDINADOR DE PNF
    if perfil == "COORDINADOR_PNF":

        coordinador = (
            CoordinadorPNF.objects
            .filter(
                usuario__cedula_identidad=cedula,
                activo=True
            )
            .select_related(
                "nucleo",
                "pnf"
            )
            .first()
        )

        if not coordinador:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Asignación no válida",
                "descripcion": (
                    "No cuenta con el perfil de Coordinador "
                    "de PNF."
                ),
                "trayectos": []
            })

        if not coordinador.nucleo_id or not coordinador.pnf_id:
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Asignación incompleta",
                "descripcion": (
                    "El perfil de Coordinador de PNF no tiene "
                    "núcleo o PNF asignado."
                ),
                "trayectos": []
            })

        # IMPORTANTE:
        # El PNF se obtiene EXCLUSIVAMENTE del perfil.
        # No se utiliza pnf_asignado del frontend.
        pnf_obj = coordinador.pnf
        
    # CONTROL DE ESTUDIO
    elif perfil == "CONTROL_ESTUDIO":

        pnf = request.POST.get("pnf_asignado", "").strip()

        control_estudio = (
            ControlEstudio.objects
            .filter(
                usuario__cedula_identidad=cedula,
                activo=True
            )
            .select_related("nucleo")
            .first()
        )

        if not control_estudio:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Núcleo no asignado",
                "descripcion": (
                    "No cuenta con el perfil de Encargado "
                    "de Control de Estudio."
                ),
                "trayectos": []
            })

        nucleo_id = control_estudio.nucleo_id

        if not nucleo_id:
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Núcleo no asignado",
                "descripcion": (
                    "El perfil de Control de Estudio no tiene "
                    "un núcleo asignado."
                ),
                "trayectos": []
            })

        # En Control de Estudio sí es obligatorio
        # seleccionar un PNF desde el frontend.
        if not pnf:
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "P.N.F no seleccionado",
                "descripcion": "Debe seleccionar un P.N.F.",
                "trayectos": []
            })

        # Validar que el PNF pertenezca al núcleo
        # del perfil de Control de Estudio.
        pnf_nucleo = (
            PNFNucleo.objects
            .filter(
                id_nucleo_id=nucleo_id,
                id_pnf_id=pnf
            )
            .select_related("id_pnf")
            .first()
        )

        if not pnf_nucleo:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "P.N.F no válido",
                "descripcion": (
                    "El P.N.F seleccionado no pertenece al "
                    "núcleo asignado al Encargado de Control "
                    "de Estudio."
                ),
                "trayectos": []
            })

        pnf_obj = pnf_nucleo.id_pnf

    # PERFIL NO VÁLIDO
    else:
        return JsonResponse({
            "estado": "fallo",
            "icon": "error",
            "title": "Perfil no válido",
            "descripcion": "El perfil seleccionado no es válido.",
            "trayectos": []
        })

    # DETERMINAR TRAYECTOS SEGÚN EL PERÍODO ACADÉMICO
    if pnf_obj.periodo_academico == "Trimestre":

        trayectos_permitidos = [
            "Trayecto Inicial",
            "Trayecto I",
            "Trayecto II",
            "Trayecto III",
            "Trayecto IV"
        ]

    elif pnf_obj.periodo_academico == "Semestre":

        trayectos_permitidos = [
            "Trayecto Inicial",
            "Trayecto I",
            "Trayecto II",
            "Trayecto III",
            "Trayecto IV",
            "Trayecto V"
        ]

    else:
        return JsonResponse({
            "estado": "fallo",
            "icon": "warning",
            "title": "Período académico no configurado",
            "descripcion": (
                f"El PNF '{pnf_obj.pnf}' no tiene configurado "
                "un período académico válido."
            ),
            "trayectos": []
        })

    # OBTENER TODOS LOS TRAYECTOS
    trayectos = (
        TrayectoAcademico.objects
        .all()
        .order_by("id_periodo_academico")
    )

    # Filtrar los trayectos permitidos
    resultado = [
        {
            "id_trayecto": trayecto.id_periodo_academico,
            "nombre": trayecto.nombre
        }
        for trayecto in trayectos
        if trayecto.nombre in trayectos_permitidos
    ]

    return JsonResponse({
        "estado": "exito",
        "periodo_academico": pnf_obj.periodo_academico,
        "id_pnf": pnf_obj.id_pnf,
        "pnf": pnf_obj.pnf,
        "trayectos": resultado
    })



def busc_mat(request):
    id_asignacion = request.POST.get("id_asignacion")
    if not id_asignacion:
        return JsonResponse({
            "estado": "fallo",
            "title": "Error",
            "icon": "error",
            "descripcion": "No se recibió el ID de la asignación."
        })

    try:
        asignacion = (
            MateriaAsignada.objects
            .select_related(
                "materia",
                "materia__id_pnf",
                "materia__id_trayecto"
            )
            .prefetch_related(
                "docentes__docente__usuario"
            )
            .get(
                id_materia_asignada=id_asignacion,
                activo=True
            )
        )
    except MateriaAsignada.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "title": "Error",
            "icon": "error",
            "descripcion": "No se encontró la materia asignada."
        })

    materia = asignacion.materia

    docentes = []
    for asignacion_docente in asignacion.docentes.all():
        docente = asignacion_docente.docente
        usuario = docente.usuario

        docentes.append({
            "id_asignacion_docente": asignacion_docente.pk,
            "id_docente": docente.id_docente,
            "nombres": usuario.nombres,
            "apellidos": usuario.apellidos,
            "nombre_completo": f"{usuario.nombres} {usuario.apellidos}",
            "cedula": usuario.cedula_identidad,
            "rol": asignacion_docente.rol,
            "activo": asignacion_docente.activo,
            "fecha_asignacion": asignacion_docente.fecha_asignacion,
            "fecha_suspension": asignacion_docente.fecha_suspension,
        })

    datos = {
        "id_materia_asignada": asignacion.id_materia_asignada,
        "activo": asignacion.activo,
        "fecha_asignacion": asignacion.fecha_asignacion,
        "fecha_suspension": asignacion.fecha_suspension,

        "id_materia": materia.id_materia,
        "nombre": materia.nombre,
        "codigo": materia.codigo,

        "id_trayecto": materia.id_trayecto_id,
        "trayecto": materia.id_trayecto.nombre,

        "pnf": materia.id_pnf.pnf,
        "id_pnf": materia.id_pnf.id_pnf,

        "docentes": docentes
    }

    return JsonResponse({
        "estado": "exito",
        "materia": datos
    })

def act_asig(request):
    if request.method != "POST":
        return render(request, "Roles/Control_Estudio/asignacion_materia/visualizar_asignaciones.html")

    materia_asignada_id = request.POST.get("materia_asignada")
    estado_principal = request.POST.get("estado_principal")
    estado_secundario = request.POST.get("estado_secundario")
    estado_materia = request.POST.get("estado_materia")
    perfil = request.POST.get("perfil", "").strip()

    cedula = request.session.get("cedula_usuario")

    if not materia_asignada_id:
        return JsonResponse({
            "estado": "fallo",
            "icon": "warning",
            "title": "Asignación",
            "descripcion": (
                "No se especificó la asignación de la materia."
            )
        })

    if estado_principal not in ["ACTIVO", "INACTIVO"]:
        return JsonResponse({
            "estado": "fallo",
            "icon": "warning",
            "title": "Docente principal",
            "descripcion": (
                "El estado del docente principal no es válido."
            )
        })

    if estado_materia not in ["ACTIVA", "SUSPENDIDA"]:
        return JsonResponse({
            "estado": "fallo",
            "icon": "warning",
            "title": "Materia",
            "descripcion": (
                "El estado de la materia no es válido."
            )
        })

    if not cedula:
        return JsonResponse({
            "estado": "fallo",
            "icon": "error",
            "title": "Sesión",
            "descripcion": (
                "No se encontró el usuario en la sesión."
            )
        })

    if perfil not in ["COORDINADOR_PNF", "CONTROL_ESTUDIO"]:
        return JsonResponse({
            "estado": "fallo",
            "icon": "warning",
            "title": "Perfil no válido",
            "descripcion": (
                "El perfil utilizado para modificar la asignación "
                "no es válido."
            )
        })

    # OBTENER USUARIO QUE REALIZA LA MODIFICACIÓN
    usuario_modificacion = (
        Usuario.objects
        .filter(
            cedula_identidad=cedula
        )
        .first()
    )

    if not usuario_modificacion:
        return JsonResponse({
            "estado": "fallo",
            "icon": "error",
            "title": "Usuario no encontrado",
            "descripcion": (
                "No se encontró el usuario que realiza "
                "la modificación."
            )
        })

    # NOMBRE DEL PERFIL
    nombre_perfil = (
        "Coordinador de PNF"
        if perfil == "COORDINADOR_PNF"
        else "Encargado de Control de Estudio"
    )

    # OBTENER ASIGNACIÓN
    try:
        materia_asignada = (
            MateriaAsignada.objects
            .select_related(
                "materia"
            )
            .get(
                pk=materia_asignada_id
            )
        )

    except MateriaAsignada.DoesNotExist:

        return JsonResponse({
            "estado": "fallo",
            "icon": "error",
            "title": "Asignación no encontrada",
            "descripcion": (
                "No se encontró la asignación de la materia."
            )
        })

    # OBTENER DOCENTES
    docentes = materia_asignada.docentes.all()

    principal = (
        docentes
        .filter(
            rol="PRINCIPAL"
        )
        .first()
    )

    secundario = (
        docentes
        .filter(
            rol="SECUNDARIO"
        )
        .first()
    )

    if not principal:
        return JsonResponse({
            "estado": "fallo",
            "icon": "warning",
            "title": "Docente principal",
            "descripcion": (
                "La asignación no tiene un docente principal."
            )
        })

    # VALIDAR ESTADO DEL SECUNDARIO
    if secundario:
        if estado_secundario not in [ "ACTIVO", "INACTIVO"]:
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Docente secundario",
                "descripcion": (
                    "El estado del docente secundario "
                    "no es válido."
                )
            })

        if estado_materia == "ACTIVA":
            if estado_principal == estado_secundario:
                return JsonResponse({
                    "estado": "fallo",
                    "icon": "warning",
                    "title": "Estado de los docentes",
                    "descripcion": (
                        "Mientras la materia esté activa, al menos uno de "
                        "los docentes debe permanecer activo. No se puede "
                        "mantener la materia activa si el docente principal "
                        "y el docente secundario están inactivos."
                    )
                })

    else:
        if (estado_materia == "ACTIVA" and estado_principal == "INACTIVO"):
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Docente principal",
                "descripcion": (
                    "No se puede desactivar al docente principal "
                    "mientras la materia esté activa y no exista "
                    "un docente secundario asignado."
                )
            })

    # ESTADOS ANTERIORES
    estado_materia_anterior = (
        "ACTIVA"
        if materia_asignada.activo
        else "SUSPENDIDA"
    )

    estado_principal_anterior = (
        "ACTIVO"
        if principal.activo
        else "INACTIVO"
    )

    estado_secundario_anterior = None

    if secundario:
        estado_secundario_anterior = (
            "ACTIVO"
            if secundario.activo
            else "INACTIVO"
        )

    # NUEVOS ESTADOS
    nuevo_estado_principal = (
        "ACTIVO"
        if (
            estado_principal == "ACTIVO"
            and estado_materia == "ACTIVA"
        )
        else "INACTIVO"
    )

    nuevo_estado_secundario = None

    if secundario:
        nuevo_estado_secundario = (
            "ACTIVO"
            if (
                estado_secundario == "ACTIVO"
                and estado_materia == "ACTIVA"
            )
            else "INACTIVO"
        )

    # DETERMINAR QUÉ CAMBIÓ
    cambios = []
    if estado_materia_anterior != estado_materia:
        cambios.append(
            f"estado de la materia: "
            f"{estado_materia_anterior} → {estado_materia}"
        )

    if estado_principal_anterior != nuevo_estado_principal:
        cambios.append(
            f"estado del docente principal: "
            f"{estado_principal_anterior} → {nuevo_estado_principal}"
        )

    if secundario:
        if estado_secundario_anterior != nuevo_estado_secundario:
            cambios.append(
                f"estado del docente secundario: "
                f"{estado_secundario_anterior} → "
                f"{nuevo_estado_secundario}"
            )

    # SI NO EXISTE NINGÚN CAMBIO

    if not cambios:
        return JsonResponse({
            "estado": "fallo",
            "icon": "info",
            "title": "Sin cambios",
            "descripcion": (
                "No se detectaron modificaciones en "
                "la asignación."
            )
        })

    fecha_modificacion = timezone.now()

    observacion = (
        f"{nombre_perfil} "
        f"{usuario_modificacion.nombres} "
        f"{usuario_modificacion.apellidos} "
        f"modificó la asignación de la materia "
        f"'{materia_asignada.materia.nombre}'. "
        f"Cambios realizados: "
        f"{'; '.join(cambios)}."
    )

    # ACTUALIZAR
    with transaction.atomic():

        # MATERIA
        if estado_materia == "SUSPENDIDA":
            materia_asignada.activo = False
            materia_asignada.fecha_suspension = fecha_modificacion

        else:
            materia_asignada.activo = True
            materia_asignada.fecha_suspension = None

        materia_asignada.modificado_por = (usuario_modificacion)
        materia_asignada.fecha_modificacion = (fecha_modificacion)
        materia_asignada.perfil_modificacion = (perfil)
        materia_asignada.observacion_modificacion = (observacion)
        materia_asignada.save()

        # DOCENTE PRINCIPAL
        principal.activo = (
            estado_principal == "ACTIVO"
            and estado_materia == "ACTIVA"
        )

        principal.fecha_suspension = (
            None
            if principal.activo
            else fecha_modificacion
        )

        principal.modificado_por = usuario_modificacion
        principal.fecha_modificacion = fecha_modificacion
        principal.perfil_modificacion = perfil
        principal.observacion_modificacion = observacion
        principal.save()

        # DOCENTE SECUNDARIO
        if secundario:
            secundario.activo = (
                estado_secundario == "ACTIVO"
                and estado_materia == "ACTIVA"
            )
            secundario.fecha_suspension = (
                None
                if secundario.activo
                else fecha_modificacion
            )
            secundario.modificado_por = usuario_modificacion
            secundario.fecha_modificacion = fecha_modificacion
            secundario.perfil_modificacion = perfil
            secundario.observacion_modificacion = observacion
            secundario.save()

        Bitacora.objects.create(
            nombre_usuario=request.session.get(
                "usuario_nombre"
            ),
            fecha_hora=fecha_modificacion,
            accion=(
                f"{nombre_perfil} "
                f"{usuario_modificacion.nombres} "
                f"{usuario_modificacion.apellidos} "
                f"modificó la asignación de la materia "
                f"'{materia_asignada.materia.nombre}'. "
                f"{'; '.join(cambios)}."
            )
        )

    return JsonResponse({
        "estado": "exito",
        "icon": "success",
        "title": "Éxito",
        "descripcion": (
            "La asignación se modificó correctamente."
        )
    })


def mats_desact(request):
    materias = (
        MateriaAsignada.objects
        .filter(activo=False)
        .select_related(
            "materia",
            "materia__id_trayecto"
        )
        .prefetch_related(
            "docentes__docente__usuario"
        )
    )

    if request.method == "POST":
        trayecto = request.POST.get("trayecto", "").strip()
        nombre_materia = request.POST.get("materia", "").strip()

        if trayecto:
            materias = materias.filter(
                materia__id_trayecto_id=trayecto
            )

        if nombre_materia:
            materias = materias.filter(
                materia__nombre__icontains=nombre_materia
            )

    datos = []

    for asignacion in materias:
        materia = asignacion.materia

        docente_principal = (
            asignacion.docentes
            .filter(rol="PRINCIPAL")
            .first()
        )

        docente_secundario = (
            asignacion.docentes
            .filter(rol="SECUNDARIO")
            .first()
        )

        datos.append({
            "id_materia_asignada": asignacion.id_materia_asignada,
            "activo": asignacion.activo,
            "fecha_asignacion": asignacion.fecha_asignacion,
            "fecha_suspension": asignacion.fecha_suspension,

            "id_materia": materia.id_materia,
            "nombre": materia.nombre,
            "codigo": materia.codigo,

            "id_trayecto": materia.id_trayecto_id,
            "trayecto": materia.id_trayecto.nombre,

            "recuperacion": materia.recuperacion,
            "htea": materia.htea,
            "htei": materia.htei,
            "thte": materia.thte,
            "uc": materia.uc,

            "docente_principal": (
                {
                    "id_asignacion_docente": docente_principal.id,
                    "id_docente": docente_principal.docente.id_docente,
                    "nombres": docente_principal.docente.usuario.nombres,
                    "apellidos": docente_principal.docente.usuario.apellidos,
                    "nombre_completo": (
                        f"{docente_principal.docente.usuario.nombres} "
                        f"{docente_principal.docente.usuario.apellidos}"
                    ),
                    "cedula": docente_principal.docente.usuario.cedula_identidad,
                    "rol": docente_principal.rol,
                    "activo": docente_principal.activo,
                    "fecha_asignacion": docente_principal.fecha_asignacion,
                    "fecha_suspension": docente_principal.fecha_suspension,
                }
                if docente_principal
                else None
            ),

            "docente_secundario": (
                {
                    "id_asignacion_docente": docente_secundario.id,
                    "id_docente": docente_secundario.docente.id_docente,
                    "nombres": docente_secundario.docente.usuario.nombres,
                    "apellidos": docente_secundario.docente.usuario.apellidos,
                    "nombre_completo": (
                        f"{docente_secundario.docente.usuario.nombres} "
                        f"{docente_secundario.docente.usuario.apellidos}"
                    ),
                    "cedula": docente_secundario.docente.usuario.cedula_identidad,
                    "rol": docente_secundario.rol,
                    "activo": docente_secundario.activo,
                    "fecha_asignacion": docente_secundario.fecha_asignacion,
                    "fecha_suspension": docente_secundario.fecha_suspension,
                }
                if docente_secundario
                else None
            ),
        })

    return JsonResponse({
        "materias": datos
    })

def asig_desact(request):
    if request.method == "POST":
        materia_asignada_id = request.POST.get("materia_asignada")
        perfil = request.POST.get("perfil", "").strip()
        cedula = request.session.get("cedula_usuario")

        if not materia_asignada_id:
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Asignación",
                "descripcion": (
                    "No se especificó la asignación "
                    "que se desea reactivar."
                )
            })

        if not perfil:
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Perfil",
                "descripcion": (
                    "No se recibió el perfil del usuario "
                    "que realiza la operación."
                )
            })

        usuario_modificacion = (
            Usuario.objects
            .filter(
                cedula_identidad=cedula
            )
            .first()
        )

        if not usuario_modificacion:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Usuario no encontrado",
                "descripcion": (
                    "No se encontró el usuario que "
                    "realiza la operación."
                )
            })

        # BUSCAR ASIGNACIÓN SUSPENDIDA
        try:

            materia_asignada = (
                MateriaAsignada.objects
                .select_related("materia")
                .get(
                    id_materia_asignada=materia_asignada_id,
                    activo=False
                )
            )

        except MateriaAsignada.DoesNotExist:

            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Asignación no encontrada",
                "descripcion": (
                    "No se encontró una asignación "
                    "suspendida con el ID indicado."
                )
            })

        # COMPROBAR OTRA ASIGNACIÓN ACTIVA
        asignacion_existente = (
            MateriaAsignada.objects
            .filter(
                materia=materia_asignada.materia,
                activo=True
            )
            .exclude(
                pk=materia_asignada.pk
            )
            .first()
        )

        if asignacion_existente:
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Materia ya asignada",
                "descripcion": (
                    f"La materia "
                    f"'{materia_asignada.materia.nombre}' "
                    f"ya se encuentra asignada y activa. "
                    f"No se puede reactivar esta asignación."
                )
            })

        fecha_modificacion = timezone.now()

        nombre_perfil = (
            "Coordinador de PNF"
            if perfil == "COORDINADOR_PNF"
            else "Encargado de Control de Estudio"
        )

        # REACTIVAR
        with transaction.atomic():
            materia_asignada.activo = True
            materia_asignada.fecha_suspension = None

            materia_asignada.modificado_por = usuario_modificacion
            materia_asignada.fecha_modificacion = fecha_modificacion
            materia_asignada.perfil_modificacion = perfil
            materia_asignada.observacion_modificacion = (
                f"{nombre_perfil} "
                f"{usuario_modificacion.nombres} "
                f"{usuario_modificacion.apellidos} "
                f"reactivó la asignación de la materia "
                f"'{materia_asignada.materia.nombre}'."
            )

            materia_asignada.save(
                update_fields=[
                    "activo",
                    "fecha_suspension",
                    "modificado_por",
                    "fecha_modificacion",
                    "perfil_modificacion",
                    "observacion_modificacion"
                ]
            )

            # OBTENER DOCENTES
            docentes = (
                materia_asignada.docentes
                .select_related(
                    "docente__usuario"
                )
                .all()
            )

            principal = (
                docentes
                .filter(
                    rol="PRINCIPAL"
                )
                .first()
            )

            secundario = (
                docentes
                .filter(
                    rol="SECUNDARIO"
                )
                .first()
            )

            # ACTIVAR DOCENTE PRINCIPAL
            if principal:
                principal.activo = True
                principal.fecha_suspension = None

                principal.modificado_por = usuario_modificacion
                principal.fecha_modificacion = fecha_modificacion
                principal.perfil_modificacion = perfil
                principal.observacion_modificacion = (
                    f"{nombre_perfil} "
                    f"{usuario_modificacion.nombres} "
                    f"{usuario_modificacion.apellidos} "
                    f"reactivó al docente "
                    f"{principal.docente.usuario.nombres} "
                    f"{principal.docente.usuario.apellidos} "
                    f"como Docente Principal de la materia "
                    f"'{materia_asignada.materia.nombre}'."
                )

                principal.save(
                    update_fields=[
                        "activo",
                        "fecha_suspension",
                        "modificado_por",
                        "fecha_modificacion",
                        "perfil_modificacion",
                        "observacion_modificacion"
                    ]
                )

            # DESACTIVAR DOCENTE SECUNDARIO
            if secundario:
                secundario.activo = False
                secundario.fecha_suspension = fecha_modificacion
                secundario.modificado_por = usuario_modificacion
                secundario.fecha_modificacion = fecha_modificacion
                secundario.perfil_modificacion = perfil
                secundario.observacion_modificacion = (
                    f"{nombre_perfil} "
                    f"{usuario_modificacion.nombres} "
                    f"{usuario_modificacion.apellidos} "
                    f"reactivó la materia y dejó inactivo "
                    f"al docente secundario "
                    f"{secundario.docente.usuario.nombres} "
                    f"{secundario.docente.usuario.apellidos}."
                )

                secundario.save(
                    update_fields=[
                        "activo",
                        "fecha_suspension",
                        "modificado_por",
                        "fecha_modificacion",
                        "perfil_modificacion",
                        "observacion_modificacion"
                    ]
                )

            Bitacora.objects.create(
                nombre_usuario=request.session.get(
                    "usuario_nombre"
                ),
                fecha_hora=fecha_modificacion,
                accion=(
                    f"{nombre_perfil} "
                    f"{usuario_modificacion.nombres} "
                    f"{usuario_modificacion.apellidos} "
                    f"reactivó la asignación de la materia "
                    f"'{materia_asignada.materia.nombre}'."
                )
            )

        return JsonResponse({
            "estado": "exito",
            "icon": "success",
            "title": "Asignación reactivada",
            "descripcion": (
                f"La materia "
                f"'{materia_asignada.materia.nombre}' "
                f"fue reactivada correctamente."
            )
        })

    return render(request, "Roles/Control_Estudio/asignacion_materia/reactivar_asignaciones.html")
