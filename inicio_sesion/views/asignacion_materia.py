from django.shortcuts import render
from django.http import JsonResponse
from django.db import transaction
from django.utils import timezone

from inicio_sesion.models import Usuario, Materia, TrayectoAcademico, MateriaAsignada, DocenteAsignadoMateria, CoordinadorPNF, Docente, Bitacora, Materia, SeccionAcademica

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
    if request.method == "POST":
        nucleo = request.POST.get("nucleo_asignado")
        pnf = request.POST.get("pnf_asignado")

        try:
            coordinador = CoordinadorPNF.objects.get(
                usuario__cedula_identidad=request.session.get("cedula_usuario"),
                nucleo_id=nucleo,
                pnf_id=pnf
            )
        except CoordinadorPNF.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "title": "Error",
                "icon": "error",
                "descripcion": "No cuenta con el rol de Coordinador de PNF.",
                "usuarios": []
            })
    
        docentes = Docente.objects.filter(nucleo=coordinador.nucleo,pnf=coordinador.pnf).select_related("usuario")
    
        usuarios = [
            {
                "id_usuario": docente.usuario.id_usuario,
                "nombre": str(docente.usuario)
            }
            for docente in docentes
        ]
    
        return JsonResponse({
            "estado": "exito",
            "usuarios": usuarios
        })

def mats_reg(request):
    nucleo = request.POST.get("nucleo_asignado")
    pnf = request.POST.get("pnf_asignado")
    docente_id = request.POST.get("docente_seleccionado")
    rol_docente = request.POST.get("rol_docente")

    try:
        coordinador = CoordinadorPNF.objects.get(
            usuario__cedula_identidad=request.session.get("cedula_usuario"),
            nucleo_id=nucleo,
            pnf_id=pnf
        )
    except CoordinadorPNF.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "title": "Error",
            "icon": "error",
            "descripcion": "No cuenta con el rol de Coordinador de PNF.",
            "materias": []
        })

    try:
        docente = Docente.objects.get(
            usuario_id=docente_id,
            nucleo_id=nucleo,
            pnf_id=pnf
        )
    except Docente.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "title": "Error",
            "icon": "error",
            "descripcion": "No se encontró el perfil del docente.",
            "materias": []
        })

    materias_pnf = (
        Materia.objects
        .filter(id_pnf=coordinador.pnf)
        .select_related("id_trayecto")
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
            .filter(activo=True)
            .first()
        )

        principal = None
        secundario = None

        if asignacion:
            docentes = asignacion.docentes.filter(
                activo=True
            )

            principal = docentes.filter(
                rol="PRINCIPAL"
            ).first()

            secundario = docentes.filter(
                rol="SECUNDARIO"
            ).first()

        tiene_principal = principal is not None
        tiene_secundario = secundario is not None

        docente_ya_asignado = False

        if asignacion:
            docente_ya_asignado = (
                asignacion.docentes
                .filter(
                    docente_id=docente.id_docente,
                    activo=True
                )
                .exists()
            )

        if docente_ya_asignado:
            estado = "AZUL"

        elif tiene_principal and tiene_secundario:
            estado = "ROJO"

        elif rol_docente == "PRINCIPAL" and tiene_principal:
            estado = "AMARILLO"

        elif rol_docente == "SECUNDARIO" and tiene_secundario:
            estado = "AMARILLO"

        elif tiene_principal or tiene_secundario:
            estado = "NARANJA"

        else:
            estado = "VERDE"

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
            "docente_ya_asignado": docente_ya_asignado
        })

    return JsonResponse({
        "estado": "exito",
        "materias": materias
    })

def asig_mat_doc(request):
    if request.method == "POST":
        nucleo_id = request.POST.get("nucleos_asignados")
        pnf_id = request.POST.get("pnfs_asignados")
        docente_id = request.POST.get("docente")
        rol_docente = request.POST.get("rol_docente")
        materias_ids = request.POST.getlist("materias[]")

        controles = [
            (nucleo_id, "Núcleo", "Debe seleccionar un núcleo."),
            (pnf_id, "P.N.F", "Debe seleccionar un P.N.F."),
            (rol_docente, "Rol del Docente", "Debe seleccionar el rol del docente."),
            (materias_ids, "Materias Académicas", "Debe seleccionar al menos una materia."),
        ]

        for value, field_name, error_message in controles:
            if not value:
                return JsonResponse({
                    "estado": "fallo",
                    "icon": "warning",
                    "title": field_name,
                    "descripcion": error_message
                })

        try:
            usuario = Usuario.objects.get(pk=docente_id)
        except Usuario.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "title": "Error",
                "icon": "error",
                "descripcion": "El usuario no se encuentra registrado."
            })

        try:
            docente = Docente.objects.get(
                usuario=usuario,
                nucleo_id=nucleo_id,
                pnf_id=pnf_id
            )
        except Docente.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "title": "Error",
                "icon": "error",
                "descripcion": "No se encontró el perfil de docente."
            })

        if rol_docente not in ["PRINCIPAL", "SECUNDARIO"]:
            return JsonResponse({
                "estado": "fallo",
                "title": "Rol inválido",
                "icon": "warning",
                "descripcion": "El rol del docente seleccionado no es válido."
            })

        materias = list(
            Materia.objects.filter(
                pk__in=materias_ids
            )
        )

        if len(materias) != len(set(materias_ids)):
            return JsonResponse({
                "estado": "fallo",
                "title": "Materia inválida",
                "icon": "warning",
                "descripcion": "Una o más materias seleccionadas no existen."
            })

        with transaction.atomic():

            for materia in materias:

                # BUSCAR LA MATERIA ASIGNADA
                asignacion = (
                    MateriaAsignada.objects
                    .filter(
                        materia=materia,
                        activo=True
                    )
                    .first()
                )

                # SI NO EXISTE, CREAR LA ASIGNACIÓN
                if not asignacion:
                    asignacion = MateriaAsignada.objects.create(
                        materia=materia,
                        activo=True
                    )

                # VALIDAR SI EL MISMO DOCENTE YA ESTÁ ASIGNADO
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
                            f"'{materia.nombre}' "
                            f"como {nombre_rol_existente}."
                        )
                    })

                # VALIDAR SI YA EXISTE EL ROL
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
                    nombre_rol = (
                        "Docente Principal"
                        if rol_docente == "PRINCIPAL"
                        else "Docente Secundario"
                    )

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

                # CREAR ASIGNACIÓN DEL DOCENTE
                activo_docente = (
                    rol_docente == "PRINCIPAL"
                )

                DocenteAsignadoMateria.objects.create(
                    materia_asignada=asignacion,
                    docente=docente,
                    rol=rol_docente,
                    activo=activo_docente
                )

                # BITÁCORA
                Bitacora.objects.create(
                    nombre_usuario=request.session.get(
                        "usuario_nombre"
                    ),
                    fecha_hora=timezone.now(),
                    accion=(
                        f"Asignó la materia '{materia.nombre}' "
                        f"al docente "
                        f"{docente.usuario.nombres} "
                        f"{docente.usuario.apellidos} "
                        f"como "
                        f"{'Docente Principal' if rol_docente == 'PRINCIPAL' else 'Docente Secundario'}."
                    )
                )

        return JsonResponse({
            "estado": "exito",
            "title": "Éxito",
            "icon": "success",
            "descripcion": "Se asignaron las materias correctamente."
        })

    return render(
        request,
        "Coordinador_PNF/asignacion_materia/registrar_asignaciones.html"
    )


def mat_asig(request):
    materias = (
        MateriaAsignada.objects
        .filter(activo=True)
        .select_related(
            "materia",
            "materia__id_trayecto",
            "materia__id_pnf"
        )
    )

    if request.method == "POST":
        trayecto = request.POST.get("trayecto", "").strip()
        nombre_materia = request.POST.get("materia", "").strip()

        if trayecto:
            materias = materias.filter(
                materia__id_trayecto=trayecto
            )

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
    if request.method == "POST":
        materia_asignada_id = request.POST.get("materia_asignada")
        estado_principal = request.POST.get("estado_principal")
        estado_secundario = request.POST.get("estado_secundario")
        estado_materia = request.POST.get("estado_materia")

        if not materia_asignada_id:
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Asignación",
                "descripcion": "No se especificó la asignación de la materia."
            })

        if estado_principal not in ["ACTIVO", "INACTIVO"]:
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Docente principal",
                "descripcion": "El estado del docente principal no es válido."
            })

        if estado_materia not in ["ACTIVA", "SUSPENDIDA"]:
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Materia",
                "descripcion": "El estado de la materia no es válido."
            })

        try:
            materia_asignada = (
                MateriaAsignada.objects
                .select_related("materia")
                .get(pk=materia_asignada_id)
            )

        except MateriaAsignada.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Asignación no encontrada",
                "descripcion": "No se encontró la asignación de la materia."
            })

        docentes = materia_asignada.docentes.all()

        principal = docentes.filter(
            rol="PRINCIPAL"
        ).first()

        secundario = docentes.filter(
            rol="SECUNDARIO"
        ).first()

        if not principal:
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Docente principal",
                "descripcion": "La asignación no tiene un docente principal."
            })

        if secundario:

            if estado_secundario not in ["ACTIVO", "INACTIVO"]:
                return JsonResponse({
                    "estado": "fallo",
                    "icon": "warning",
                    "title": "Docente secundario",
                    "descripcion": "El estado del docente secundario no es válido."
                })

            if estado_materia == "ACTIVA":

                if estado_principal == estado_secundario:
                    return JsonResponse({
                        "estado": "fallo",
                        "icon": "warning",
                        "title": "Estado de los docentes",
                        "descripcion": (
                            "Cuando la materia está activa, el docente "
                            "principal y el docente secundario deben "
                            "tener estados diferentes. Si uno está activo, "
                            "el otro debe estar inactivo."
                        )
                    })

        else:

            if (
                estado_materia == "ACTIVA"
                and estado_principal == "INACTIVO"
            ):
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

        with transaction.atomic():

            if estado_materia == "SUSPENDIDA":
                materia_asignada.activo = False
                materia_asignada.fecha_suspension = timezone.now()

            else:
                materia_asignada.activo = True
                materia_asignada.fecha_suspension = None

            materia_asignada.save(
                update_fields=[
                    "activo",
                    "fecha_suspension"
                ]
            )

            principal.activo = (
                estado_principal == "ACTIVO"
                and estado_materia == "ACTIVA"
            )

            principal.fecha_suspension = (
                None
                if principal.activo
                else timezone.now()
            )

            principal.save(
                update_fields=[
                    "activo",
                    "fecha_suspension"
                ]
            )

            if secundario:

                secundario.activo = (
                    estado_secundario == "ACTIVO"
                    and estado_materia == "ACTIVA"
                )

                secundario.fecha_suspension = (
                    None
                    if secundario.activo
                    else timezone.now()
                )

                secundario.save(
                    update_fields=[
                        "activo",
                        "fecha_suspension"
                    ]
                )

            Bitacora.objects.create(
                nombre_usuario=request.session.get(
                    "usuario_nombre"
                ),
                fecha_hora=timezone.now(),
                accion=(
                    f"Actualizó la asignación de la materia "
                    f"'{materia_asignada.materia.nombre}'."
                )
            )

        return JsonResponse({
            "estado": "exito",
            "icon": "success",
            "title": "Éxito",
            "descripcion": "La asignación se actualizó correctamente."
        })

    return render(
        request,
        "Coordinador_PNF/asignacion_materia/visualizar_asignaciones.html"
    )


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

        # COMPROBAR SI LA MATERIA YA TIENE OTRA ASIGNACIÓN ACTIVA
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

        # REACTIVAR
        with transaction.atomic():

            # ==========================================
            # REACTIVAR MATERIA
            # ==========================================

            materia_asignada.activo = True
            materia_asignada.fecha_suspension = None

            materia_asignada.save(
                update_fields=[
                    "activo",
                    "fecha_suspension"
                ]
            )

            # ==========================================
            # OBTENER DOCENTES
            # ==========================================

            docentes = (
                materia_asignada.docentes
                .select_related(
                    "docente__usuario"
                )
                .all()
            )

            principal = (
                docentes
                .filter(rol="PRINCIPAL")
                .first()
            )

            secundario = (
                docentes
                .filter(rol="SECUNDARIO")
                .first()
            )

            # ==========================================
            # ACTIVAR DOCENTE PRINCIPAL
            # ==========================================

            if principal:
                principal.activo = True
                principal.fecha_suspension = None

                principal.save(
                    update_fields=[
                        "activo",
                        "fecha_suspension"
                    ]
                )

            # ==========================================
            # DESACTIVAR DOCENTE SECUNDARIO / SUPLENTE
            # ==========================================

            if secundario:
                secundario.activo = False
                secundario.fecha_suspension = timezone.now()

                secundario.save(
                    update_fields=[
                        "activo",
                        "fecha_suspension"
                    ]
                )

            # ==========================================
            # BITÁCORA
            # ==========================================

            Bitacora.objects.create(
                nombre_usuario=request.session.get(
                    "usuario_nombre"
                ),
                fecha_hora=timezone.now(),
                accion=(
                    f"Reactivó la materia "
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
                f"fue reactivada correctamente. "
                f"El docente principal quedó activo "
                f"y el docente secundario quedó inactivo."
            )
        })

    return render(
        request,
        "Coordinador_PNF/asignacion_materia/reactivar_asignaciones.html"
    )
