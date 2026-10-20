from django.shortcuts import render
from django.http import JsonResponse
from django.utils import timezone
from django.conf import settings

from inicio_sesion.models import Docente, PNFNucleo, ControlEstudio, CalendarioAcademico, Usuario, Contacto, Nacimiento, Residencia, AulaEstudiante, Bitacora, CoordinadorPNF, EstatusEstudiante, DocumentosEstudiante, ContactoAuxiliar, Discapacidad, InformacionSecundaria, Estudiante, AulaAcademica

def perf_asig_coord(request):
    cedula = request.session.get("cedula_usuario")

    tiene_coordinador_pnf = CoordinadorPNF.objects.filter(
        usuario__cedula_identidad=cedula,
        activo=True
    ).exists()

    tiene_control_estudio = ControlEstudio.objects.filter(
        usuario__cedula_identidad=cedula,
        activo=True
    ).exists()

    return JsonResponse({
        "estado": "exito",
        "coordinador_pnf": tiene_coordinador_pnf,
        "control_estudio": tiene_control_estudio
    })

def obt_pnfs_asignado(request):
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

    # COORDINADOR PNF
    if perfil == "COORDINADOR_PNF":
        pnfs = (
            CoordinadorPNF.objects
            .filter(
                usuario__cedula_identidad=cedula,
                activo=True
            )
            .select_related("pnf")
            .values(
                "pnf__id_pnf",
                "pnf__pnf",
                "pnf__codigo",
                "pnf__periodo_academico"
            )
            .distinct()
        )

        resultado = [
            {
                "id_pnf": pnf["pnf__id_pnf"],
                "pnf": pnf["pnf__pnf"],
                "codigo": pnf["pnf__codigo"],
                "periodo_academico": pnf["pnf__periodo_academico"]
            }
            for pnf in pnfs
        ]

    # CONTROL DE ESTUDIO
    elif perfil == "CONTROL_ESTUDIO":
        control = (
            ControlEstudio.objects
            .filter(
                usuario__cedula_identidad=cedula,
                activo=True
            )
            .select_related("nucleo")
            .first()
        )

        if not control:
            return JsonResponse({
                "estado": "fallo",
                "pnfs": []
            })

        pnfs = (
            PNFNucleo.objects
            .filter(
                id_nucleo=control.nucleo
            )
            .select_related("id_pnf")
            .values(
                "id_pnf__id_pnf",
                "id_pnf__pnf",
                "id_pnf__codigo",
                "id_pnf__periodo_academico"
            )
            .distinct()
        )

        resultado = [
            {
                "id_pnf": pnf["id_pnf__id_pnf"],
                "pnf": pnf["id_pnf__pnf"],
                "codigo": pnf["id_pnf__codigo"],
                "periodo_academico": pnf["id_pnf__periodo_academico"]
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

def obt_pre_inscrt(request):
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

    if not cedula or not perfil:
        return JsonResponse({
            "estado": "error",
            "titulo": "Datos incompletos",
            "icon": "warning",
            "descripcion": (
                "No se recibieron todos los datos necesarios."
            )
        })

    # ==========================================================
    # VARIABLES
    # ==========================================================

    nucleo_id = None
    pnf_id = None
    periodo_academico = None

    # ==========================================================
    # COORDINADOR PNF
    # ==========================================================

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
                "estado": "error",
                "titulo": "Asignación no válida",
                "icon": "error",
                "descripcion": (
                    "El usuario no tiene un PNF asignado "
                    "como Coordinador de PNF."
                )
            })

        # El PNF se obtiene de la asignación real
        pnf_id = coordinador.pnf_id

        # El núcleo se obtiene de la asignación real
        nucleo_id = coordinador.nucleo_id

        # Período académico del PNF
        periodo_academico = (
            coordinador.pnf.periodo_academico
        )

    # ==========================================================
    # CONTROL DE ESTUDIO
    # ==========================================================

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
                "estado": "error",
                "titulo": "Asignación no válida",
                "icon": "error",
                "descripcion": (
                    "El usuario no tiene un núcleo asignado "
                    "como encargado de Control de Estudio."
                )
            })

        nucleo_id = control_estudio.nucleo_id

        if not pnf:
            return JsonResponse({
                "estado": "exito",
                "estudiantes": [],
                "aulas": [],
                "inscripcion_disponible": False
            })

        # Validar que el PNF pertenezca al núcleo
        pnf_nucleo = (
            PNFNucleo.objects
            .filter(
                id_nucleo_id=nucleo_id,
                id_pnf_id=pnf
            )
            .select_related(
                "id_pnf"
            )
            .first()
        )

        if not pnf_nucleo:
            return JsonResponse({
                "estado": "error",
                "titulo": "PNF no válido",
                "icon": "error",
                "descripcion": (
                    "El PNF seleccionado no pertenece "
                    "al núcleo asignado al encargado "
                    "de Control de Estudio."
                )
            })

        pnf_id = pnf_nucleo.id_pnf_id

        # Período académico del PNF
        periodo_academico = (
            pnf_nucleo.id_pnf.periodo_academico
        )

    # ==========================================================
    # PERFIL NO VÁLIDO
    # ==========================================================

    else:

        return JsonResponse({
            "estado": "error",
            "titulo": "Perfil no válido",
            "icon": "error",
            "descripcion": (
                "El perfil seleccionado no es válido."
            )
        })

    # ==========================================================
    # DETERMINAR TIPO DE INSCRIPCIÓN
    # ==========================================================

    if periodo_academico == "Trimestre":

        tipo_inscripcion = "INSCRIPCION_TRIMESTRE"

    elif periodo_academico == "Semestre":

        tipo_inscripcion = "INSCRIPCION_SEMESTRE"

    else:

        return JsonResponse({
            "estado": "error",
            "titulo": "Período académico no configurado",
            "icon": "warning",
            "descripcion": (
                "El PNF seleccionado no tiene configurado "
                "un período académico válido."
            )
        })

    # ==========================================================
    # VALIDAR CALENDARIO ACADÉMICO
    # ==========================================================

    fecha_actual = timezone.localdate()

    calendario_inscripcion = (
        CalendarioAcademico.objects
        .filter(
            activo=True,
            tipo=tipo_inscripcion,
            fecha_inicio__year=fecha_actual.year,
            fecha_inicio__lte=fecha_actual,
            fecha_final__gte=fecha_actual
        )
        .order_by(
            "fecha_inicio"
        )
        .first()
    )

    # ==========================================================
    # FUERA DEL PERÍODO DE INSCRIPCIÓN
    # ==========================================================

    if not calendario_inscripcion:

        calendario_proximo = (
            CalendarioAcademico.objects
            .filter(
                activo=True,
                tipo=tipo_inscripcion,
                fecha_inicio__year=fecha_actual.year,
                fecha_inicio__gte=fecha_actual
            )
            .order_by(
                "fecha_inicio"
            )
            .first()
        )

        if calendario_proximo:

            fecha_inicio = (
                calendario_proximo.fecha_inicio.strftime(
                    "%d/%m/%Y"
                )
            )

            fecha_final = (
                calendario_proximo.fecha_final.strftime(
                    "%d/%m/%Y"
                )
            )

            descripcion = (
                "El período de inscripción para los PNF de "
                f"modalidad {periodo_academico.lower()} "
                f"estará disponible desde el "
                f"{fecha_inicio} hasta el {fecha_final}."
            )

        else:

            descripcion = (
                "Actualmente no existe un período de "
                "inscripción configurado para los PNF de "
                f"modalidad {periodo_academico.lower()}."
            )

        return JsonResponse({
            "estado": "exito",
            "estudiantes": [],
            "aulas": [],
            "inscripcion_disponible": False,
            "titulo": "¡Inscripción no disponible!",
            "icon": "info",
            "descripcion": descripcion
        })

    # ==========================================================
    # BUSCAR ESTUDIANTES
    # ==========================================================

    estudiantes = (
        Estudiante.objects
        .filter(
            nucleo_id=nucleo_id,
            pnf_id=pnf_id,
            estatus__estatus="Espera"
        )
        .select_related(
            "usuario"
        )
        .prefetch_related(
            "estatus"
        )
        .distinct()
        .order_by(
            "usuario__nombres",
            "usuario__apellidos"
        )
    )

    datos = []

    for estudiante in estudiantes:

        estatus = (
            estudiante.estatus
            .filter(
                estatus="Espera"
            )
            .select_related(
                "trayecto"
            )
            .order_by(
                "-fecha_ingreso",
                "-id_estatus_estudiante"
            )
            .first()
        )

        if not estatus:
            continue

        datos.append({
            "id_estudiante": estudiante.id_estudiante,
            "cedula_identidad": (
                estudiante.usuario.cedula_identidad
            ),
            "nombres": estudiante.usuario.nombres,
            "apellidos": estudiante.usuario.apellidos,
            "genero": estudiante.usuario.genero,
            "estatus": estatus.estatus,
            "estado": estatus.estado,
            "ingreso": estatus.ingreso,
            "descripcion_ingreso": (
                estatus.descripcion_ingreso
            ),
            "trayecto": estatus.trayecto.nombre,
            "fecha_ingreso": (
                estatus.fecha_ingreso.strftime(
                    "%d/%m/%Y"
                )
            )
        })

    # ==========================================================
    # BUSCAR AULAS
    # ==========================================================

    aulas = list(
        AulaAcademica.objects
        .filter(
            id_nucleo_id=nucleo_id,
            id_pnf_id=pnf_id
        )
        .order_by(
            "nombre_aula"
        )
        .values(
            "id_aula",
            "nombre_aula",
            "tipo_aula",
            "piso_edificio"
        )
    )

    # ==========================================================
    # RESPUESTA
    # ==========================================================

    return JsonResponse({
        "estado": "exito",
        "estudiantes": datos,
        "aulas": aulas,
        "inscripcion_disponible": True,
        "titulo": "Inscripción disponible",
        "icon": "success",
        "descripcion": (
            "El período de inscripción se encuentra vigente."
        ),
        "fecha_inicio": (
            calendario_inscripcion.fecha_inicio.strftime(
                "%d/%m/%Y"
            )
        ),
        "fecha_final": (
            calendario_inscripcion.fecha_final.strftime(
                "%d/%m/%Y"
            )
        )
    })

def obt_data_est(request):
    if request.method == "POST":
        cedula_estudiante = request.POST.get("cedula_estudiante")

        usuario = Usuario.objects.get(cedula_identidad=cedula_estudiante)

        contacto = Contacto.objects.get(id_usuario=usuario)

        residencia = Residencia.objects.get(id_usuario=usuario)

        nacimiento = Nacimiento.objects.get(id_usuario=usuario)

        informacion_secundaria = InformacionSecundaria.objects.get(id_usuario=usuario)

        discapacidad = Discapacidad.objects.get(id_usuario=usuario)

        representantes = ContactoAuxiliar.objects.get(id_usuario=usuario)

        documentos_estudiante = DocumentosEstudiante.objects.filter(id_usuario=usuario)

        documentos = []
        for doc in documentos_estudiante:
            if doc.archivo:
                ruta = str(doc.archivo).replace("\\", "/")
                if ruta.startswith("media/"):
                    ruta = ruta[6:]

                documentos.append({
                    "tipo_documento": doc.nombre_documento,
                    "archivo": settings.MEDIA_URL + ruta
                })

        return JsonResponse({
            "estado": "exito",
            "usuario": {
                "id_usuario": usuario.id_usuario,
                "nombres": usuario.nombres,
                "apellidos": usuario.apellidos,
                "cedula_identidad": usuario.cedula_identidad,
                "genero": usuario.genero,
                "estado_civil": usuario.estado_civil
            },
            "contacto": {
                "telefono_personal": contacto.telefono_personal,
                "telefono_suplete": contacto.telefono_suplete,
                "correo_electronico": contacto.correo_electronico,
                "correo_alternativo": contacto.correo_alternativo
            },
            "residencia": {
                "condicion_residencia": residencia.condicion_residencia,
                "municipio": residencia.municipio,
                "parroquia": residencia.parroquia,
                "direccion_residencia": residencia.direccion_residencia
            },
            "nacimiento": {
                "pais": nacimiento.pais,
                "estado": nacimiento.estado,
                "municipio": nacimiento.municipio,
                "parroquia": nacimiento.parroquia,
                "direccion_nacimiento": nacimiento.direccion_nacimiento,
                "fecha_nacimiento": nacimiento.fecha_nacimiento.strftime("%Y-%m-%d")
            },
            "informacion_secundaria": {
                "nombre_institucion": informacion_secundaria.nombre_institucion,
                "tipo_institucion": informacion_secundaria.tipo_institucion,
                "fecha_grado": informacion_secundaria.fecha_grado.strftime("%Y-%m-%d"),
                "codigo_sni_opsu": informacion_secundaria.codigo_sni_opsu
            },
            "discapacidad": {
                "codigo_carnet_discapacidad": discapacidad.codigo_carnet_discapacidad,
                "nro_registro_medico": discapacidad.nro_registro_medico,
                "tipo_discapacidad": discapacidad.tipo_discapacidad,
                "grado_discapacidad": discapacidad.grado_discapacidad,
                "causa_discapacidad": discapacidad.causa_discapacidad
            },
            "representantes": {
                "nombres": representantes.nombres,
                "apellidos": representantes.apellidos,
                "cedula_identidad": representantes.cedula_identidad,
                "telefono": representantes.telefono,
                "parentesco": representantes.parentesco
            },
            "documentos": documentos
        })

def inscr_est(request):
    if request.method != "POST":
        return render(request, "Roles/Control_Estudio/inscripcion/inscripcion_rechazado.html")

    cedula_usuario = request.session.get("cedula_usuario")

    cedula = request.POST.get("cedula", "").strip()
    id_aula = request.POST.get("aula", "").strip()
    accion = request.POST.get("accion", "").strip()
    pnf = request.POST.get("pnf_asignado", "").strip()
    perfil = request.POST.get("perfil", "").strip()

    # VALIDAR SESIÓN
    if not cedula_usuario:
        return JsonResponse({
            "titulo": "¡Sesión no válida!",
            "estado": "fallo",
            "icon": "warning",
            "descripcion": (
                "No se encontró el usuario de la sesión."
            )
        })

    if not cedula or not perfil:
        return JsonResponse({
            "titulo": "¡Datos incompletos!",
            "estado": "fallo",
            "icon": "warning",
            "descripcion": (
                "No se recibieron todos los datos necesarios."
            )
        })

    # OBTENER USUARIO QUE REALIZA LA OPERACIÓN
    usuario_registro = (
        Usuario.objects
        .filter(
            cedula_identidad=cedula_usuario
        )
        .first()
    )

    if not usuario_registro:
        return JsonResponse({
            "titulo": "¡Usuario no encontrado!",
            "estado": "fallo",
            "icon": "warning",
            "descripcion": (
                "No se encontró el usuario que realiza "
                "la operación."
            )
        })

    # VARIABLES DE OPERACIÓN
    periodo_academico = None
    nucleo_id = None
    pnf_id = None


    if perfil == "COORDINADOR_PNF":

        coordinador = (
            CoordinadorPNF.objects
            .select_related(
                "nucleo",
                "pnf"
            )
            .filter(
                usuario__cedula_identidad=cedula_usuario,
                activo=True
            )
            .first()
        )

        if not coordinador:
            return JsonResponse({
                "titulo": "¡Asignación no válida!",
                "estado": "fallo",
                "icon": "warning",
                "descripcion": (
                    "El usuario no tiene un PNF asignado "
                    "como Coordinador de PNF."
                )
            })

        # EL PNF SE OBTIENE DIRECTAMENTE DE LA ASIGNACIÓN
        pnf_id = coordinador.pnf_id

        # EL NÚCLEO TAMBIÉN SE OBTIENE DE LA ASIGNACIÓN
        nucleo_id = coordinador.nucleo_id

        # PERÍODO ACADÉMICO DEL PNF
        periodo_academico = coordinador.pnf.periodo_academico

    elif perfil == "CONTROL_ESTUDIO":

        # Para Control de Estudio sí se utiliza el PNF recibido
        if not pnf:
            return JsonResponse({
                "titulo": "¡PNF no seleccionado!",
                "estado": "fallo",
                "icon": "warning",
                "descripcion": (
                    "Debe seleccionar el PNF para realizar "
                    "la inscripción."
                )
            })

        pnf_id = pnf

        control_estudio = (
            ControlEstudio.objects
            .select_related(
                "nucleo"
            )
            .filter(
                usuario__cedula_identidad=cedula_usuario,
                activo=True
            )
            .first()
        )

        if not control_estudio:
            return JsonResponse({
                "titulo": "¡Asignación no válida!",
                "estado": "fallo",
                "icon": "warning",
                "descripcion": (
                    "El usuario no tiene un núcleo asignado "
                    "como encargado de Control de Estudio."
                )
            })

        # NÚCLEO DEL CONTROL DE ESTUDIO
        nucleo_id = control_estudio.nucleo_id

        # VALIDAR PNF + NÚCLEO
        pnf_nucleo = (
            PNFNucleo.objects
            .select_related(
                "id_pnf"
            )
            .filter(
                id_nucleo_id=nucleo_id,
                id_pnf_id=pnf_id
            )
            .first()
        )

        if not pnf_nucleo:
            return JsonResponse({
                "titulo": "¡PNF no válido!",
                "estado": "fallo",
                "icon": "warning",
                "descripcion": (
                    "El PNF seleccionado no pertenece "
                    "al núcleo asignado al encargado "
                    "de Control de Estudio."
                )
            })

        periodo_academico = (
            pnf_nucleo.id_pnf.periodo_academico
        )

    else:
        return JsonResponse({
            "titulo": "¡Perfil no válido!",
            "estado": "fallo",
            "icon": "warning",
            "descripcion": (
                "El perfil seleccionado no es válido."
            )
        })

    usuario = (
        Usuario.objects
        .filter(
            cedula_identidad=cedula
        )
        .first()
    )

    if not usuario:
        return JsonResponse({
            "titulo": "¡Advertencia!",
            "estado": "fallo",
            "icon": "warning",
            "descripcion": "El estudiante no existe."
        })

    estudiante = (
        Estudiante.objects
        .filter(
            usuario=usuario,
            nucleo_id=nucleo_id,
            pnf_id=pnf_id
        )
        .first()
    )

    if not estudiante:
        return JsonResponse({
            "titulo": "¡Advertencia!",
            "estado": "fallo",
            "icon": "warning",
            "descripcion": (
                "El estudiante no pertenece al PNF "
                "o núcleo asignado."
            )
        })
    
    estatus_estudiante = (
        EstatusEstudiante.objects
        .filter(
            estudiante=estudiante,
            estatus="Espera",
            estado__in=[
                "Espera",
                "No Admitido"
            ]
        )
        .select_related(
            "trayecto"
        )
        .order_by(
            "-fecha_ingreso"
        )
        .first()
    )

    if not estatus_estudiante:
        return JsonResponse({
            "titulo": "¡Advertencia!",
            "estado": "fallo",
            "icon": "warning",
            "descripcion": (
                "No se encontró una preinscripción "
                "pendiente o rechazada para el estudiante."
            )
        })

    if accion == "No Admitido":
        estatus_estudiante.estado = "No Admitido"

        estatus_estudiante.save(
            update_fields=[
                "estado"
            ]
        )

        return JsonResponse({
            "titulo": "¡Éxito!",
            "estado": "exito",
            "icon": "success",
            "descripcion": (
                "La preinscripción fue rechazada."
            )
        })

    if accion != "Admitido":
        return JsonResponse({
            "titulo": "¡Advertencia!",
            "estado": "fallo",
            "icon": "warning",
            "descripcion": (
                "La acción solicitada no es válida."
            )
        })
    
    if not id_aula:
        return JsonResponse({
            "titulo": "¡Advertencia!",
            "estado": "fallo",
            "icon": "warning",
            "descripcion": (
                "Debe seleccionar el aula."
            )
        })
    
    if periodo_academico == "Trimestre":
        tipo_inscripcion = "INSCRIPCION_TRIMESTRE"

    elif periodo_academico == "Semestre":
        tipo_inscripcion = "INSCRIPCION_SEMESTRE"

    else:
        return JsonResponse({
            "titulo": "¡Período académico no configurado!",
            "estado": "fallo",
            "icon": "warning",
            "descripcion": (
                "El PNF seleccionado no tiene configurado "
                "un período académico válido."
            )
        })

    fecha_actual = timezone.localdate()

    calendario_inscripcion = (
        CalendarioAcademico.objects
        .filter(
            activo=True,
            tipo=tipo_inscripcion,
            fecha_inicio__lte=fecha_actual,
            fecha_final__gte=fecha_actual
        )
        .first()
    )

    if not calendario_inscripcion:
        return JsonResponse({
            "titulo": "¡Inscripción no disponible!",
            "estado": "fallo",
            "icon": "warning",
            "descripcion": (
                "Actualmente no existe un período de "
                "inscripción vigente para los PNF de "
                f"modalidad {periodo_academico.lower()}."
            )
        })

    aula = (
        AulaAcademica.objects
        .filter(
            id_aula=id_aula,
            id_nucleo_id=nucleo_id,
            id_pnf_id=pnf_id
        )
        .first()
    )

    if not aula:
        return JsonResponse({
            "titulo": "¡Advertencia!",
            "estado": "fallo",
            "icon": "warning",
            "descripcion": (
                "El aula seleccionada no existe o no pertenece "
                "al núcleo y PNF asignados."
            )
        })

    if AulaEstudiante.objects.filter(
        estatus=estatus_estudiante,
        estado="Curso",
        fecha_final__isnull=True
    ).exists():

        return JsonResponse({
            "titulo": "¡Advertencia!",
            "estado": "fallo",
            "icon": "warning",
            "descripcion": (
                "El estudiante ya posee un aula activa."
            )
        })

    fecha_registro = timezone.now()

    AulaEstudiante.objects.create(
        aula=aula,
        estatus=estatus_estudiante,
        fecha_inicio=fecha_actual,
        estado="Curso"
    )

    estatus_estudiante.estatus = "Inscrito(a)"
    estatus_estudiante.estado = "Activo"
    estatus_estudiante.registrado_por = usuario_registro
    estatus_estudiante.fecha_registro = fecha_registro
    estatus_estudiante.perfil_registro = perfil

    estatus_estudiante.save(
        update_fields=[
            "estatus",
            "estado",
            "registrado_por",
            "fecha_registro",
            "perfil_registro"
        ]
    )

    return JsonResponse({
        "titulo": "¡Éxito!",
        "estado": "exito",
        "icon": "success",
        "descripcion": (
            "El estudiante fue inscrito correctamente."
        )
    })

def rech_inscr_est(request):
    if request.method == "POST":
        cedula = request.session.get("cedula_usuario")
        pnf = request.POST.get("pnf_asignado", "").strip()
        perfil = request.POST.get("perfil", "").strip()

        if not cedula:
            return JsonResponse({
                "estado": "error",
                "titulo": "Sesión no válida",
                "icon": "warning",
                "descripcion": (
                    "No se encontró el usuario en la sesión."
                )
            })

        if not pnf or not perfil:
            return JsonResponse({
                "estado": "error",
                "titulo": "Datos incompletos",
                "icon": "warning",
                "descripcion": (
                    "No se recibieron todos los datos necesarios."
                )
            })

        # OBTENER NÚCLEO Y PNF SEGÚN EL PERFIL
        periodo_academico = None

        # COORDINADOR PNF
        if perfil == "COORDINADOR_PNF":
            coordinador = (
                CoordinadorPNF.objects
                .select_related(
                    "nucleo",
                    "pnf"
                )
                .filter(
                    usuario__cedula_identidad=cedula,
                    activo=True
                )
                .first()
            )

            if not coordinador:
                return JsonResponse({
                    "estado": "error",
                    "titulo": "Perfil no autorizado",
                    "icon": "warning",
                    "descripcion": (
                        "No se encontró un perfil activo de "
                        "Coordinador de PNF."
                    )
                })

            # El núcleo y PNF salen del perfil asignado
            nucleo_id = coordinador.nucleo_id
            pnf_id = coordinador.pnf_id

            # El PNF del coordinador debe coincidir con el solicitado
            if str(pnf_id) != str(pnf):
                return JsonResponse({
                    "estado": "error",
                    "titulo": "PNF no autorizado",
                    "icon": "warning",
                    "descripcion": (
                        "El PNF seleccionado no corresponde "
                        "al PNF asignado al Coordinador."
                    )
                })

            periodo_academico = coordinador.pnf.periodo_academico

        # CONTROL DE ESTUDIO
        elif perfil == "CONTROL_ESTUDIO":

            control_estudio = (
                ControlEstudio.objects
                .select_related(
                    "nucleo"
                )
                .filter(
                    usuario__cedula_identidad=cedula,
                    activo=True
                )
                .first()
            )

            if not control_estudio:
                return JsonResponse({
                    "estado": "error",
                    "titulo": "Perfil no autorizado",
                    "icon": "warning",
                    "descripcion": (
                        "No se encontró un perfil activo de "
                        "Control de Estudio."
                    )
                })

            # El núcleo sale directamente del perfil
            nucleo_id = control_estudio.nucleo_id

            # Validar que el PNF pertenezca al núcleo
            pnf_nucleo = (
                PNFNucleo.objects
                .select_related(
                    "id_pnf"
                )
                .filter(
                    id_nucleo_id=nucleo_id,
                    id_pnf_id=pnf
                )
                .first()
            )

            if not pnf_nucleo:
                return JsonResponse({
                    "estado": "error",
                    "titulo": "PNF no válido",
                    "icon": "warning",
                    "descripcion": (
                        "El PNF seleccionado no pertenece "
                        "al núcleo asignado al encargado "
                        "de Control de Estudio."
                    )
                })

            pnf_id = pnf_nucleo.id_pnf_id
            periodo_academico = pnf_nucleo.id_pnf.periodo_academico

        else:

            return JsonResponse({
                "estado": "error",
                "titulo": "Perfil no válido",
                "icon": "warning",
                "descripcion": (
                    "El perfil seleccionado no es válido."
                )
            })

        # DETERMINAR TIPO DE INSCRIPCIÓN
        if periodo_academico == "Trimestre":
            tipo_inscripcion = "INSCRIPCION_TRIMESTRE"

        elif periodo_academico == "Semestre":
            tipo_inscripcion = "INSCRIPCION_SEMESTRE"

        else:

            return JsonResponse({
                "estado": "error",
                "titulo": "Período académico no configurado",
                "icon": "warning",
                "descripcion": (
                    "El PNF seleccionado no tiene configurado "
                    "un período académico válido."
                )
            })

        # VALIDAR CALENDARIO ACADÉMICO
        fecha_actual = timezone.localdate()

        calendario_inscripcion = (
            CalendarioAcademico.objects
            .filter(
                activo=True,
                tipo=tipo_inscripcion,
                fecha_inicio__lte=fecha_actual,
                fecha_final__gte=fecha_actual
            )
            .first()
        )

        if not calendario_inscripcion:

            return JsonResponse({
                "estado": "error",
                "titulo": "Inscripción no disponible",
                "icon": "warning",
                "descripcion": (
                    f"Actualmente no se encuentra dentro del período "
                    f"establecido para realizar la inscripción de los "
                    f"PNF de modalidad "
                    f"{periodo_academico.lower()}."
                )
            })

        # OBTENER ESTUDIANTES NO ADMITIDOS
        estudiantes = (
            Estudiante.objects
            .filter(
                nucleo_id=nucleo_id,
                pnf_id=pnf_id,
                estatus__estado="No Admitido"
            )
            .select_related(
                "usuario"
            )
            .distinct()
        )

        resultado = []

        for estudiante in estudiantes:

            estatus = (
                estudiante.estatus
                .filter(
                    estado="No Admitido"
                )
                .select_related(
                    "trayecto"
                )
                .order_by(
                    "-fecha_ingreso",
                    "-id_estatus_estudiante"
                )
                .first()
            )

            if not estatus:
                continue

            resultado.append({
                "id_estudiante": estudiante.id_estudiante,
                "cedula_identidad": (
                    estudiante.usuario.cedula_identidad
                ),
                "nombres": estudiante.usuario.nombres,
                "apellidos": estudiante.usuario.apellidos,
                "genero": estudiante.usuario.genero,
                "estatus": estatus.estatus,
                "estado": estatus.estado,
                "ingreso": estatus.ingreso,
                "descripcion_ingreso": (
                    estatus.descripcion_ingreso
                ),
                "trayecto": estatus.trayecto.nombre,
                "fecha_ingreso": (
                    estatus.fecha_ingreso.strftime("%Y-%m-%d")
                )
            })

        # OBTENER AULAS
        aulas = (
            AulaAcademica.objects
            .filter(
                id_nucleo_id=nucleo_id,
                id_pnf_id=pnf_id
            )
            .order_by(
                "nombre_aula"
            )
            .values(
                "id_aula",
                "nombre_aula",
                "tipo_aula",
                "piso_edificio"
            )
        )

        return JsonResponse({
            "estado": "exito",
            "estudiantes": resultado,
            "aulas": list(aulas)
        })