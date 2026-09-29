from django.shortcuts import render
from django.http import JsonResponse
from django.db import transaction

from inicio_sesion.models import Usuario, Estudiante, Pnf, Contacto, Nucleos, PNFNucleo, DirectorGeneral, Docente, CoordinadorPNF, ControlEstudio

import json

PERFILES = {
    "1": "Coordinador PNF",
    "2": "Control de Estudio",
    "3": "Docente"
}

def datos_perfiles(request):
    director = DirectorGeneral.objects.select_related("nucleo").get(usuario__cedula_identidad=request.session.get("cedula_usuario"))

    nucleo_director = director.nucleo

    perfiles = [
        {
            "id_perfil": 1,
            "perfil": "Coordinador PNF"
        },
        {
            "id_perfil": 3,
            "perfil": "Docente"
        }
    ]

    # Verificar si el núcleo ya tiene Control de Estudio
    existe_control = ControlEstudio.objects.filter(
        nucleo=nucleo_director
    ).exists()
    if not existe_control:
        perfiles.insert(
            1,
            {
                "id_perfil": 2,
                "perfil": "Control de Estudio"
            }
        )

    return JsonResponse({
        "perfiles": perfiles
    })

def pnfs_disp(request):
    if request.method == "POST":
        data = json.loads(request.body)

        perfil_id = int(data.get("id_perfil"))

        director = DirectorGeneral.objects.select_related(
            "nucleo"
        ).get(
            usuario__cedula_identidad=request.session.get("cedula_usuario")
        )

        nucleo = director.nucleo

        pnfs = PNFNucleo.objects.filter(
            id_nucleo=nucleo
        ).select_related("id_pnf")

        # Coordinador PNF (id_perfil = 1)
        if perfil_id == 1:

            pnfs_ocupados = CoordinadorPNF.objects.filter(
                nucleo=nucleo
            ).values_list(
                "pnf_id",
                flat=True
            )

            pnfs = pnfs.exclude(
                id_pnf_id__in=pnfs_ocupados
            )

        resultado = [
            {
                "id_pnf": item.id_pnf.id_pnf,
                "pnf": item.id_pnf.pnf
            }
            for item in pnfs
        ]

        return JsonResponse({
            "pnfs": resultado
        })


def pre_reg_personal(request):
    if request.method == "POST":
        nombres = request.POST.get("nombres")
        apellidos = request.POST.get("apellidos")
        nacionalidad = request.POST.get("nacionalidad")
        num_cedula = request.POST.get("cedula_identidad")
        nombre_correo = request.POST.get("correo_electronico")
        dominio = request.POST.get("dominio")
        prefijo = request.POST.get("prefijo")
        num_telefono = request.POST.get("telefono")

        perfiles_asignados = request.POST.getlist("perfil")

        pnfs_coordinador = request.POST.getlist("pnf_coordinador_pnf")
        pnfs_docente = request.POST.getlist("pnf_docente")

        # Obtener núcleo del Director General
        director = DirectorGeneral.objects.select_related(
            "usuario",
            "nucleo"
        ).get(
            usuario__cedula_identidad=request.session.get("cedula_usuario")
        )

        nucleo_director = director.nucleo

        campos = [
            (nombres, "Nombres", "Por favor, ingresar los nombres del usuario."),
            (apellidos, "Apellidos", "Por favor, ingresar los apellidos del usuario."),
            (nacionalidad, "Nacionalidad", "Por favor, selecciona la nacionalidad."),
            (num_cedula, "Cédula", "Por favor, ingresa la cédula."),
            (nombre_correo, "Correo", "Por favor, ingresa el correo."),
            (dominio, "Dominio", "Por favor, selecciona el dominio."),
            (prefijo, "Prefijo", "Por favor, selecciona el prefijo."),
            (num_telefono, "Teléfono", "Por favor, ingresa el teléfono."),
        ]

        for valor, campo, mensaje in campos:
            if not valor:
                return JsonResponse({
                    "estado": "fallo",
                    "title": campo,
                    "descripcion": mensaje,
                    "icon": "warning"
                })

        perfiles_asignados = [
            perfil for perfil in request.POST.getlist("perfil")
            if perfil.strip()
        ]

        pnfs_coordinador = [
            pnf for pnf in request.POST.getlist("pnf_coordinador_pnf")
            if pnf.strip()
        ]

        pnfs_docente = [
            pnf for pnf in request.POST.getlist("pnf_docente")
            if pnf.strip()
        ]

        # Validar que exista al menos un perfil
        if not perfiles_asignados:
            return JsonResponse({
                "estado": "fallo",
                "title": "Perfil vacío",
                "descripcion": "Debe seleccionar al menos un perfil para el usuario.",
                "icon": "warning"
            })


        # Validar los PNF según el perfil seleccionado
        for perfil_id in perfiles_asignados:

            perfil = PERFILES.get(perfil_id)

            if perfil == "Coordinador PNF":

                if not pnfs_coordinador:
                    return JsonResponse({
                        "estado": "fallo",
                        "title": "PNF vacío",
                        "descripcion": "Debe seleccionar al menos un PNF para el perfil Coordinador PNF.",
                        "icon": "warning"
                    })

            elif perfil == "Docente":

                if not pnfs_docente:
                    return JsonResponse({
                        "estado": "fallo",
                        "title": "PNF vacío",
                        "descripcion": "Debe seleccionar al menos un PNF para el perfil Docente.",
                        "icon": "warning"
                    })
                        

        cedula_identidad = f"{nacionalidad}-{num_cedula}"
        correo_principal = f"{nombre_correo}{dominio}"
        telefono_principal = f"{prefijo}{num_telefono}"

        with transaction.atomic():
            usuario = Usuario.objects.create(
                nombres=nombres,
                apellidos=apellidos,
                cedula_identidad=cedula_identidad
            )

            Contacto.objects.create(
                correo_electronico=correo_principal,
                telefono_personal=telefono_principal,
                id_usuario=usuario
            )

            for perfil_id in perfiles_asignados:
                perfil = PERFILES.get(perfil_id)

                # Control de Estudio
                if perfil == "Control de Estudio":
                    ControlEstudio.objects.create(
                        usuario=usuario,
                        nucleo=nucleo_director
                    )

                # Coordinador PNF
                elif perfil == "Coordinador PNF":
                    for pnf_id in pnfs_coordinador:
                        if PNFNucleo.objects.filter(
                            id_nucleo=nucleo_director,
                            id_pnf_id=pnf_id
                        ).exists():

                            CoordinadorPNF.objects.create(
                                usuario=usuario,
                                nucleo=nucleo_director,
                                pnf_id=pnf_id
                            )

                # Docente
                elif perfil == "Docente":
                    for pnf_id in pnfs_docente:
                        if PNFNucleo.objects.filter(
                            id_nucleo=nucleo_director,
                            id_pnf_id=pnf_id
                        ).exists():
                            Docente.objects.create(
                                usuario=usuario,
                                nucleo=nucleo_director,
                                pnf_id=pnf_id
                            )

        return JsonResponse({
            "estado": "exito",
            "icon": "success",
            "title": "Éxito",
            "descripcion": "Los datos del usuario se registraron exitosamente."
        })

    return render(request, "Roles/Director_General/gestion_personal/pre_registro_personal.html")

def per_reg_asig(request):
    # DIRECTOR GENERAL DE LA SESIÓN
    director = DirectorGeneral.objects.filter(
        usuario__cedula_identidad=request.session.get("cedula_usuario")
    ).select_related(
        "usuario",
        "nucleo"
    ).first()

    if not director:
        return JsonResponse({
            "personal": [],
            "error": "Director General no encontrado"
        }, status=404)

    nucleo = director.nucleo

    # FILTROS OPCIONALES
    pnf_filtro = request.POST.get("pnf", "").strip()
    perfil_filtro = request.POST.get("perfil", "").strip()

    datos = []

    # DOCENTES
    if not perfil_filtro or perfil_filtro == "Docente":
        docentes = Docente.objects.filter(
            nucleo=nucleo
        ).select_related(
            "usuario",
            "pnf"
        )

        for docente in docentes:

            if Estudiante.objects.filter(
                usuario=docente.usuario,
                nucleo=nucleo
            ).exists():
                continue

            if docente.pnf:
                pnf_asignado = docente.pnf.pnf
                id_pnf = str(docente.pnf.id_pnf)
            else:
                pnf_asignado = "NO CUENTA CON P.N.F"
                id_pnf = ""

            # Filtro por PNF
            if pnf_filtro and id_pnf != pnf_filtro:
                continue

            datos.append({
                "id_usuario": docente.usuario.id_usuario,
                "nombres": docente.usuario.nombres,
                "apellidos": docente.usuario.apellidos,
                "cedula": docente.usuario.cedula_identidad,
                "rol": "Docente",
                "pnf": pnf_asignado,
            })

    # COORDINADORES PNF
    if not perfil_filtro or perfil_filtro == "Coordinador de PNF":
        coordinadores = CoordinadorPNF.objects.filter(
            nucleo=nucleo
        ).select_related(
            "usuario",
            "pnf"
        )

        for coordinador in coordinadores:
            if Estudiante.objects.filter(
                usuario=coordinador.usuario,
                nucleo=nucleo
            ).exists():
                continue

            if coordinador.pnf:
                pnf_asignado = coordinador.pnf.pnf
                id_pnf = str(coordinador.pnf.id_pnf)
            else:
                pnf_asignado = "NO CUENTA CON P.N.F"
                id_pnf = ""

            # Filtro por PNF
            if pnf_filtro and id_pnf != pnf_filtro:
                continue

            datos.append({
                "id_usuario": coordinador.usuario.id_usuario,
                "nombres": coordinador.usuario.nombres,
                "apellidos": coordinador.usuario.apellidos,
                "cedula": coordinador.usuario.cedula_identidad,
                "rol": "Coordinador PNF",
                "pnf": pnf_asignado,
            })

    # CONTROL DE ESTUDIO
    if not perfil_filtro or perfil_filtro == "Encargado de Control de Estudio":
        controles = ControlEstudio.objects.filter(
            nucleo=nucleo
        ).select_related("usuario")

        if not pnf_filtro:
            for control in controles:
                if Estudiante.objects.filter(
                    usuario=control.usuario,
                    nucleo=nucleo
                ).exists():
                    continue

                datos.append({
                    "id_usuario": control.usuario.id_usuario,
                    "nombres": control.usuario.nombres,
                    "apellidos": control.usuario.apellidos,
                    "cedula": control.usuario.cedula_identidad,
                    "rol": "Control de Estudio",
                    "pnf": "NO CUENTA CON P.N.F",
                })

    return JsonResponse({ "personal": datos })


def act_per_asig(request):
    return render(request, "Roles/Director_General/gestion_personal/actualizar_personal_registrado.html")
      
def vis_per_asig(request):
    return render(request, "Roles/Director_General/gestion_personal/visualizar_personal_registrado.html")

def bus_per_asig(request):
    if request.method == "POST":
        nacionalidad = request.POST.get("nacionalidad_registrar")
        cedula = request.POST.get("cedula_registrar")

        # VALIDACIONES
        if not nacionalidad:
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Vacio",
                "descripcion": "Por favor, selecciona la nacionalidad."
            })

        if not cedula:
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Vacio",
                "descripcion": (
                    "Por favor, ingrese los números de su "
                    "cedula de identidad."
                )
            })

        request.session['cedula_personal'] = nacionalidad + "-" + cedula

        # BUSCAR USUARIO
        usuario = Usuario.objects.filter(
            cedula_identidad=request.session.get('cedula_personal')
        ).first()

        if not usuario:
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "No encontrado",
                "descripcion": (
                    "No existe un usuario registrado "
                    "con esa cédula."
                )
            })

        # NO PERMITIR ASIGNAR PERFILES AL DIRECTOR GENERAL
        es_director_general = DirectorGeneral.objects.filter(
            usuario=usuario
        ).exists()

        if es_director_general:
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Usuario no disponible",
                "descripcion": (
                    "El Director General no puede recibir "
                    "asignaciones de perfiles."
                )
            })

        # DATOS DEL USUARIO
        datos_usuario = {
            "id_usuario": usuario.id_usuario,
            "nombres": usuario.nombres,
            "apellidos": usuario.apellidos,
            "cedula": usuario.cedula_identidad,
        }

        # DIRECTOR GENERAL ACTUAL
        director_general = DirectorGeneral.objects.filter(
            usuario__cedula_identidad=request.session.get("cedula_usuario")
        ).select_related(
            "nucleo"
        ).first()

        if not director_general:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Error",
                "descripcion": (
                    "No se encontró el Director General."
                )
            })

        nucleo = director_general.nucleo

        # PERFILES ASIGNADOS
        perfiles = []

        # DOCENTES
        docentes = Docente.objects.filter(
            usuario=usuario
        ).select_related(
            "nucleo",
            "pnf"
        )

        for docente in docentes:
            perfiles.append({
                "id_perfil": docente.id_docente,
                "tipo": "docente",
                "rol": "Docente",
                "pnf": docente.pnf.pnf if docente.pnf else (
                    "NO CUENTA CON P.N.F"
                ),
                "nucleo": docente.nucleo.municipio,
                "activo": docente.activo,
                "estado": (
                    "ACTIVO"
                    if docente.activo
                    else "INHABILITADO"
                )
            })

        # COORDINADORES PNF
        coordinadores = CoordinadorPNF.objects.filter(
            usuario=usuario
        ).select_related(
            "nucleo",
            "pnf"
        )

        for coordinador in coordinadores:
            perfiles.append({
                "id_perfil": coordinador.id_coordinador,
                "tipo": "coordinador_pnf",
                "rol": "Coordinador de PNF",
                "pnf": (
                    coordinador.pnf.pnf
                    if coordinador.pnf
                    else "NO CUENTA CON P.N.F"
                ),
                "nucleo": coordinador.nucleo.municipio,
                "activo": coordinador.activo,
                "estado": (
                    "ACTIVO"
                    if coordinador.activo
                    else "INHABILITADO"
                )
            })

        # CONTROL DE ESTUDIO
        controles = ControlEstudio.objects.filter(
            usuario=usuario
        ).select_related(
            "nucleo"
        )

        for control in controles:
            perfiles.append({
                "id_perfil": control.id_control,
                "tipo": "control_estudio",
                "rol": "Encargado de Control de Estudio",
                "pnf": "NO CUENTA CON P.N.F",
                "nucleo": control.nucleo.municipio,
                "activo": control.activo,
                "estado": (
                    "ACTIVO"
                    if control.activo
                    else "INHABILITADO"
                )
            })

        # PNF DEL NÚCLEO ACTUAL
        pnfs_nucleo = list(
            Pnf.objects.filter(
                pnfnucleo__id_nucleo=nucleo
            ).values(
                "id_pnf",
                "pnf",
                "codigo"
            )
        )

        # PNF DISPONIBLES PARA DOCENTE
        pnfs_docente_asignados = set(
            Docente.objects.filter(
                usuario=usuario,
                nucleo=nucleo,
                activo=True
            ).values_list(
                "pnf_id",
                flat=True
            )
        )

        pnfs_disponibles_docente = [
            pnf
            for pnf in pnfs_nucleo
            if pnf["id_pnf"] not in pnfs_docente_asignados
        ]

        # COORDINADOR PNF
        tiene_coordinador = CoordinadorPNF.objects.filter(
            usuario=usuario,
            nucleo=nucleo,
            activo=True
        ).exists()

        pnfs_coordinador_ocupados = set(
            CoordinadorPNF.objects.filter(
                nucleo=nucleo,
                activo=True
            ).values_list(
                "pnf_id",
                flat=True
            )
        )

        pnfs_disponibles_coordinador = [
            pnf
            for pnf in pnfs_nucleo
            if pnf["id_pnf"] not in pnfs_coordinador_ocupados
        ]

        # CONTROL DE ESTUDIO
        tiene_control_estudio = ControlEstudio.objects.filter(
            usuario=usuario,
            nucleo=nucleo,
            activo=True
        ).exists()

        # PERFILES DISPONIBLES
        perfiles_disponibles = []

        if pnfs_disponibles_docente:
            perfiles_disponibles.append({
                "tipo": "docente",
                "rol": "Docente"
            })

        if (not tiene_coordinador and pnfs_disponibles_coordinador):
            perfiles_disponibles.append({
                "tipo": "coordinador_pnf",
                "rol": "Coordinador de PNF"
            })

        if not tiene_control_estudio:
            perfiles_disponibles.append({
                "tipo": "control_estudio",
                "rol": "Encargado de Control de Estudio"
            })

        return JsonResponse({
            "estado": "exito",
            "usuario": datos_usuario,

            # SOLO PERFILES YA ASIGNADOS
            "perfiles": perfiles,

            # PERFILES QUE SE PUEDEN ASIGNAR
            "perfiles_disponibles": perfiles_disponibles,

            "pnfs_disponibles_docente": (
                pnfs_disponibles_docente
            ),

            "pnfs_disponibles_coordinador": (
                pnfs_disponibles_coordinador
            )
        })

def info_per_asig(request):

    if request.method != "POST":
        return JsonResponse({
            "estado": "fallo",
            "icon": "error",
            "title": "Método no permitido",
            "descripcion": "La solicitud debe realizarse mediante POST."
        })

    rol = request.POST.get("rol", "").strip()

    if not rol:
        return JsonResponse({
            "estado": "fallo",
            "icon": "warning",
            "title": "Rol no indicado",
            "descripcion": "No se indicó el perfil del usuario."
        })

    # =========================================================
    # USUARIO SELECCIONADO
    # =========================================================

    usuario = Usuario.objects.filter(
        cedula_identidad=request.session.get("cedula_personal")
    ).first()

    if not usuario:
        return JsonResponse({
            "estado": "fallo",
            "icon": "warning",
            "title": "Usuario no encontrado",
            "descripcion": (
                "No existe un usuario registrado con esa cédula."
            )
        })

    # =========================================================
    # DIRECTOR GENERAL
    # =========================================================

    director = DirectorGeneral.objects.select_related(
        "nucleo"
    ).filter(
        usuario__cedula_identidad=request.session.get(
            "cedula_usuario"
        )
    ).first()

    if not director:
        return JsonResponse({
            "estado": "fallo",
            "icon": "error",
            "title": "Director General no encontrado",
            "descripcion": (
                "No se encontró el Director General "
                "de la sesión actual."
            )
        })

    nucleo_director = director.nucleo

    # =========================================================
    # TODOS LOS PNF DEL NÚCLEO
    # =========================================================

    pnfs_nucleo = list(
        Pnf.objects.filter(
            pnfnucleo__id_nucleo=nucleo_director
        ).values(
            "id_pnf",
            "pnf",
            "codigo"
        ).distinct()
    )

    # =========================================================
    # VARIABLES
    # =========================================================

    perfiles = []
    pnfs_asignados = []
    pnfs_disponibles = []

    # =========================================================
    # DOCENTE
    # =========================================================

    if rol == "Docente":

        perfiles = Docente.objects.filter(
            usuario=usuario,
            nucleo=nucleo_director
        ).select_related(
            "nucleo",
            "pnf"
        )

        for docente in perfiles:

            if docente.pnf:
                pnfs_asignados.append({
                    "id_pnf": docente.pnf.id_pnf,
                    "nombre": docente.pnf.pnf,
                    "codigo": docente.pnf.codigo,
                    "activo": docente.activo
                })

        # Para docente puede seleccionar cualquier PNF
        pnfs_disponibles = pnfs_nucleo

    # =========================================================
    # COORDINADOR DE PNF
    # =========================================================

    elif rol == "Coordinador de PNF":

        perfiles = CoordinadorPNF.objects.filter(
            usuario=usuario,
            nucleo=nucleo_director
        ).select_related(
            "nucleo",
            "pnf"
        )

        # PNF que ya tiene asignado ESTE usuario
        ids_pnf_usuario = set()

        for coordinador in perfiles:

            if coordinador.pnf:

                ids_pnf_usuario.add(
                    coordinador.pnf.id_pnf
                )

                pnfs_asignados.append({
                    "id_pnf": coordinador.pnf.id_pnf,
                    "nombre": coordinador.pnf.pnf,
                    "codigo": coordinador.pnf.codigo,
                    "activo": coordinador.activo
                })

        # =====================================================
        # PNF QUE YA ESTÁN ASIGNADOS A OTROS COORDINADORES
        # =====================================================

        ids_pnf_otros_coordinadores = set(
            CoordinadorPNF.objects.filter(
                nucleo=nucleo_director
            ).exclude(
                usuario=usuario
            ).exclude(
                pnf__isnull=True
            ).values_list(
                "pnf_id",
                flat=True
            )
        )

        # =====================================================
        # DISPONIBLES PARA ESTE COORDINADOR
        #
        # Se excluyen los de otros coordinadores,
        # pero se conserva el que ya pertenece al usuario.
        # =====================================================

        pnfs_disponibles = [
            pnf
            for pnf in pnfs_nucleo
            if (
                pnf["id_pnf"] not in ids_pnf_otros_coordinadores
                or
                pnf["id_pnf"] in ids_pnf_usuario
            )
        ]

    # =========================================================
    # CONTROL DE ESTUDIO
    # =========================================================

    elif rol == "Encargado de Control de Estudio":

        perfil = ControlEstudio.objects.filter(
            usuario=usuario,
            nucleo=nucleo_director
        ).select_related(
            "nucleo"
        ).first()

        if not perfil:
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Perfil no encontrado",
                "descripcion": (
                    f"El usuario no posee el perfil {rol} "
                    f"en el núcleo "
                    f"{nucleo_director.municipio}."
                )
            })

    else:

        return JsonResponse({
            "estado": "fallo",
            "icon": "warning",
            "title": "Perfil no válido",
            "descripcion": (
                "El perfil indicado no corresponde "
                "a un perfil registrado."
            )
        })

    # =========================================================
    # VALIDAR PERFIL
    # =========================================================

    if rol in ("Docente", "Coordinador de PNF"):

        if not perfiles.exists():
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Perfil no encontrado",
                "descripcion": (
                    f"El usuario no posee el perfil {rol} "
                    f"en el núcleo "
                    f"{nucleo_director.municipio}."
                )
            })

        activo = any(
            perfil.activo
            for perfil in perfiles
        )

    else:

        activo = perfil.activo

    # =========================================================
    # RESPUESTA
    # =========================================================

    return JsonResponse({
        "estado": "exito",

        "rol": rol,

        "activo": activo,

        "estado_perfil": (
            "ACTIVO"
            if activo
            else "DESACTIVADO"
        ),

        "nucleo": {
            "id_nucleo": nucleo_director.id_nucleo,
            "municipio": nucleo_director.municipio
        },

        # TODOS LOS PNF DEL NÚCLEO
        "pnfs_nucleo": pnfs_nucleo,

        # PNF ASIGNADOS AL USUARIO
        "pnfs_asignados": pnfs_asignados,

        # PNF QUE SE PUEDEN SELECCIONAR
        "pnfs_disponibles": pnfs_disponibles
    })

def per_dis_asi(request):
    # DIRECTOR GENERAL
    director_general = DirectorGeneral.objects.filter(
        usuario__cedula_identidad=request.session.get("cedula_usuario")
    ).select_related(
        "nucleo"
    ).first()

    if not director_general:
        return JsonResponse({
            "estado": "fallo",
            "icon": "error",
            "title": "Error",
            "descripcion": (
                "No se encontró el Director General."
            )
        })

    # USUARIO
    usuario = Usuario.objects.filter(
        cedula_identidad=request.session.get('cedula_personal')
    ).first()

    if not usuario:
        return JsonResponse({
            "estado": "fallo",
            "icon": "warning",
            "title": "Usuario no encontrado",
            "descripcion": (
                "No existe un usuario registrado "
                "con esa cédula."
            )
        })

    nucleo = director_general.nucleo

    # PNF OFERTADOS EN EL NÚCLEO DEL DIRECTOR
    pnfs_nucleo = list(
        PNFNucleo.objects.filter(
            id_nucleo=nucleo
        ).select_related(
            "id_pnf"
        ).values(
            "id_pnf",
            "id_pnf__pnf",
            "id_pnf__codigo"
        )
    )

    perfiles = []

    # DOCENTE
    docente = Docente.objects.filter(
        usuario=usuario,
        nucleo=nucleo
    ).first()

    if not docente:
        perfiles.append({
            "rol": "Docente",
            "pnfs": pnfs_nucleo
        })

    # COORDINADOR DE PNF
    coordinaciones_usuario = set(
        CoordinadorPNF.objects.filter(
            usuario=usuario
        ).values_list(
            "pnf_id",
            flat=True
        )
    )

    pnfs_coordinador_disponibles = [
        pnf
        for pnf in pnfs_nucleo
        if pnf["id_pnf"] not in coordinaciones_usuario
    ]

    if pnfs_coordinador_disponibles:

        perfiles.append({
            "rol": "Coordinador de PNF",
            "pnfs": pnfs_coordinador_disponibles
        })

    # CONTROL DE ESTUDIO
    if not ControlEstudio.objects.filter(
        usuario=usuario,
        nucleo=nucleo
    ).exists():

        perfiles.append({
            "rol": "Encargado de Control de Estudio",
            "pnfs": []
        })

    return JsonResponse({
        "estado": "exito",
        "nucleo": {
            "id_nucleo": nucleo.id_nucleo,
            "municipio": nucleo.municipio
        },
        "perfiles": perfiles
    })

def per_reg(request):
    cedula_personal = request.session.get("cedula_personal")

    if not cedula_personal:
        return JsonResponse({
            "estado": "exito",
            "usuario": {
                "cedula": "",
                "nombres": "",
                "apellidos": ""
            },
            "cantidad": 0,
            "perfiles": []
        })

    usuario = Usuario.objects.filter(
        cedula_identidad=cedula_personal
    ).first()

    perfiles = []

    docentes = Docente.objects.filter(
        usuario=usuario
    ).select_related(
        "nucleo",
        "pnf"
    )

    for docente in docentes:
        perfiles.append({
            "id_perfil": docente.id_docente,
            "tipo": "docente",
            "rol": "Docente",
            "activo": docente.activo,
            "estado": "ACTIVO" if docente.activo else "DESACTIVADO",
            "nucleo": {
                "id": docente.nucleo.id_nucleo,
                "municipio": docente.nucleo.municipio
            },
            "pnf": {
                "id": docente.pnf.id_pnf,
                "nombre": docente.pnf.pnf
            } if docente.pnf else None
        })

    coordinadores = CoordinadorPNF.objects.filter(
        usuario=usuario
    ).select_related(
        "nucleo",
        "pnf"
    )

    for coordinador in coordinadores:
        perfiles.append({
            "id_perfil": coordinador.id_coordinador,
            "tipo": "coordinador_pnf",
            "rol": "Coordinador de PNF",
            "activo": coordinador.activo,
            "estado": "ACTIVO" if coordinador.activo else "DESACTIVADO",
            "nucleo": {
                "id": coordinador.nucleo.id_nucleo,
                "municipio": coordinador.nucleo.municipio
            },
            "pnf": {
                "id": coordinador.pnf.id_pnf,
                "nombre": coordinador.pnf.pnf
            } if coordinador.pnf else None
        })

    controles = ControlEstudio.objects.filter(
        usuario=usuario
    ).select_related(
        "nucleo"
    )

    for control in controles:
        perfiles.append({
            "id_perfil": control.id_control,
            "tipo": "control_estudio",
            "rol": "Encargado de Control de Estudio",
            "activo": control.activo,
            "estado": "ACTIVO" if control.activo else "DESACTIVADO",
            "nucleo": {
                "id": control.nucleo.id_nucleo,
                "municipio": control.nucleo.municipio
            },
            "pnf": None
        })

    return JsonResponse({
        "estado": "exito",
        "usuario": {
            "cedula": usuario.cedula_identidad,
            "nombres": usuario.nombres,
            "apellidos": usuario.apellidos
        },
        "cantidad": len(perfiles),
        "perfiles": perfiles
    })

def eli_var_sec(request):
    if "cedula_personal" in request.session:
        del request.session["cedula_personal"]

    return JsonResponse({
        "estado": "exito"
    })


@transaction.atomic
def agr_per_asig(request):
    if request.method != "POST":
        return JsonResponse({
            "estado": "fallo",
            "icon": "error",
            "title": "Método no permitido",
            "descripcion": "La solicitud debe realizarse mediante POST."
        })

    perfiles = request.POST.getlist("perfiles")

    pnfs_docente = request.POST.getlist("pnfs_docente")
    pnfs_coordinador = request.POST.getlist("pnfs_coordinador_pnf")


    if not perfiles:
        return JsonResponse({
            "estado": "fallo",
            "icon": "warning",
            "title": "Perfiles no seleccionados",
            "descripcion": "Debe seleccionar al menos un perfil."
        })

    # DIRECTOR GENERAL
    director_general = DirectorGeneral.objects.filter(
        usuario__cedula_identidad=request.session.get(
            "cedula_usuario"
        )
    ).select_related(
        "nucleo"
    ).first()

    if not director_general:
        return JsonResponse({
            "estado": "fallo",
            "icon": "error",
            "title": "Director General no encontrado",
            "descripcion": (
                "No se encontró el Director General "
                "de la sesión actual."
            )
        })

    nucleo = director_general.nucleo

    # USUARIO
    usuario = Usuario.objects.filter(
        cedula_identidad=request.session.get('cedula_personal')
    ).first()

    if not usuario:
        return JsonResponse({
            "estado": "fallo",
            "icon": "warning",
            "title": "Usuario no encontrado",
            "descripcion": (
                "No existe un usuario registrado "
                "con esa cédula."
            )
        })

    # PNF DISPONIBLES EN EL NÚCLEO DEL DIRECTOR
    pnfs_nucleo = set(
        PNFNucleo.objects.filter(
            id_nucleo=nucleo
        ).values_list(
            "id_pnf_id",
            flat=True
        )
    )

    registrados = []

    # DOCENTE
    if "Docente" in perfiles:
        if not pnfs_docente:
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "PNF no seleccionado",
                "descripcion": (
                    "Debe seleccionar al menos un PNF "
                    "para el perfil Docente."
                )
            })

        try:
            ids_pnf_docente = {
                int(pnf)
                for pnf in pnfs_docente
            }
        except ValueError:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "PNF inválido",
                "descripcion": (
                    "Uno de los PNF seleccionados "
                    "no es válido."
                )
            })

        if not ids_pnf_docente.issubset(pnfs_nucleo):
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "PNF no permitido",
                "descripcion": (
                    "Uno de los PNF seleccionados "
                    "no pertenece al núcleo del Director General."
                )
            })

        for id_pnf in ids_pnf_docente:
            if Docente.objects.filter(
                usuario=usuario,
                nucleo=nucleo,
                pnf_id=id_pnf
            ).exists():
                continue

            Docente.objects.create(
                usuario=usuario,
                nucleo=nucleo,
                pnf_id=id_pnf,
                activo=True
            )

            registrados.append(f"Docente - PNF {id_pnf}")

    # COORDINADOR DE PNF
    if "Coordinador de PNF" in perfiles:
        if not pnfs_coordinador:
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "PNF no seleccionado",
                "descripcion": (
                    "Debe seleccionar un PNF "
                    "para el perfil Coordinador de PNF."
                )
            })

        try:
            ids_pnf_coordinador = {
                int(pnf)
                for pnf in pnfs_coordinador
            }
        except ValueError:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "PNF inválido",
                "descripcion": (
                    "Uno de los PNF seleccionados "
                    "no es válido."
                )
            })

        if not ids_pnf_coordinador.issubset(pnfs_nucleo):
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "PNF no permitido",
                "descripcion": (
                    "Uno de los PNF seleccionados "
                    "no pertenece al núcleo del Director General."
                )
            })

        # Un PNF solo puede tener un Coordinador activo
        pnfs_ocupados = set(
            CoordinadorPNF.objects.filter(
                nucleo=nucleo,
                pnf_id__in=ids_pnf_coordinador,
                activo=True
            ).values_list(
                "pnf_id",
                flat=True
            )
        )

        if pnfs_ocupados:
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "PNF no disponible",
                "descripcion": (
                    "Uno o más PNF seleccionados "
                    "ya tienen un Coordinador activo."
                )
            })

        for id_pnf in ids_pnf_coordinador:
            if CoordinadorPNF.objects.filter(
                usuario=usuario,
                pnf_id=id_pnf
            ).exists():
                continue

            CoordinadorPNF.objects.create(
                usuario=usuario,
                nucleo=nucleo,
                pnf_id=id_pnf,
                activo=True
            )

            registrados.append(
                f"Coordinador de PNF - PNF {id_pnf}"
            )

    # CONTROL DE ESTUDIO
    if "Encargado de Control de Estudio" in perfiles:
        if ControlEstudio.objects.filter(
            usuario=usuario,
            nucleo=nucleo
        ).exists():
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Perfil ya registrado",
                "descripcion": (
                    "El usuario ya posee el perfil "
                    "Encargado de Control de Estudio "
                    "en este núcleo."
                )
            })

        ControlEstudio.objects.create(
            usuario=usuario,
            nucleo=nucleo,
            activo=True
        )

        registrados.append(
            "Encargado de Control de Estudio"
        )

    # SIN CAMBIOS
    if not registrados:
        return JsonResponse({
            "estado": "fallo",
            "icon": "warning",
            "title": "Sin cambios",
            "descripcion": (
                "Los perfiles seleccionados "
                "ya se encuentran registrados."
            )
        })

    return JsonResponse({
        "estado": "exito",
        "icon": "success",
        "title": "Perfiles registrados",
        "descripcion": (
            "Los perfiles fueron registrados correctamente."
        ),
        "perfiles": registrados
    })

def act_per_reg(request):

    if request.method != "POST":
        return JsonResponse({
            "estado": "fallo",
            "title": "Método no permitido",
            "descripcion": "La solicitud debe realizarse mediante POST.",
            "icon": "error"
        })

    try:

        # =========================================================
        # DATOS RECIBIDOS
        # =========================================================

        rol = request.POST.get("rol", "").strip()
        id_perfil = request.POST.get("id_perfil", "").strip()
        estado = request.POST.get("estado_perfil", "").strip()

        # Docente -> puede recibir varios PNF
        pnfs = request.POST.getlist("pnf")

        # Coordinador -> solamente un PNF
        pnf_coordinador = request.POST.get(
            "pnf_coordinador",
            ""
        ).strip()

        # =========================================================
        # VALIDACIONES GENERALES
        # =========================================================

        if not rol:
            return JsonResponse({
                "estado": "fallo",
                "title": "Perfil requerido",
                "descripcion": (
                    "No se recibió el perfil "
                    "que desea actualizar."
                ),
                "icon": "warning"
            })

        if not id_perfil:
            return JsonResponse({
                "estado": "fallo",
                "title": "Perfil no identificado",
                "descripcion": (
                    "No se recibió el identificador "
                    "del perfil que desea actualizar."
                ),
                "icon": "warning"
            })

        if estado not in ("true", "false"):
            return JsonResponse({
                "estado": "fallo",
                "title": "Estado no válido",
                "descripcion": (
                    "Debe seleccionar Habilitar "
                    "o Deshabilitar."
                ),
                "icon": "warning"
            })

        nuevo_estado = estado == "true"

        # =========================================================
        # USUARIO
        # =========================================================

        usuario = Usuario.objects.filter(
            cedula_identidad=request.session.get(
                "cedula_personal"
            )
        ).first()

        if not usuario:
            return JsonResponse({
                "estado": "fallo",
                "title": "Usuario no encontrado",
                "descripcion": (
                    "No se encontró un usuario "
                    "con la cédula indicada."
                ),
                "icon": "warning"
            })

        # =========================================================
        # DIRECTOR GENERAL
        # =========================================================

        director = DirectorGeneral.objects.select_related(
            "nucleo"
        ).filter(
            usuario__cedula_identidad=request.session.get(
                "cedula_usuario"
            )
        ).first()

        if not director:
            return JsonResponse({
                "estado": "fallo",
                "title": "Director General no encontrado",
                "descripcion": (
                    "No se encontró el Director General "
                    "de la sesión actual."
                ),
                "icon": "error"
            })

        nucleo_director = director.nucleo

        # =========================================================
        # ACTUALIZACIÓN
        # =========================================================

        with transaction.atomic():

            # =====================================================
            # DOCENTE
            # =====================================================

            if rol == "Docente":

                perfil = Docente.objects.filter(
                    id_docente=id_perfil,
                    usuario=usuario,
                    nucleo=nucleo_director
                ).first()

                if not perfil:
                    return JsonResponse({
                        "estado": "fallo",
                        "title": "Perfil no encontrado",
                        "descripcion": (
                            "No se encontró el perfil Docente "
                            "en el núcleo correspondiente."
                        ),
                        "icon": "warning"
                    })

                # -------------------------------------------------
                # VALIDAR PNF SELECCIONADOS
                # -------------------------------------------------

                if not pnfs:
                    return JsonResponse({
                        "estado": "fallo",
                        "title": "PNF requerido",
                        "descripcion": (
                            "Debe seleccionar al menos "
                            "un PNF para el docente."
                        ),
                        "icon": "warning"
                    })

                # -------------------------------------------------
                # VALIDAR QUE LOS PNF PERTENEZCAN AL NÚCLEO
                # -------------------------------------------------

                pnfs_validos = list(
                    Pnf.objects.filter(
                        id_pnf__in=pnfs,
                        pnfnucleo__id_nucleo=nucleo_director
                    ).distinct()
                )

                if len(pnfs_validos) != len(set(pnfs)):
                    return JsonResponse({
                        "estado": "fallo",
                        "title": "PNF no válido",
                        "descripcion": (
                            "Uno o más PNF seleccionados "
                            "no pertenecen al núcleo del "
                            "Director General."
                        ),
                        "icon": "warning"
                    })

                # -------------------------------------------------
                # ACTUALIZAR ESTADO
                # -------------------------------------------------

                perfil.activo = nuevo_estado

                perfil.save(
                    update_fields=["activo"]
                )

            # =====================================================
            # COORDINADOR DE PNF
            # =====================================================

            elif rol == "Coordinador de PNF":

                perfil = CoordinadorPNF.objects.filter(
                    id_coordinador=id_perfil,
                    usuario=usuario,
                    nucleo=nucleo_director
                ).first()

                if not perfil:
                    return JsonResponse({
                        "estado": "fallo",
                        "title": "Perfil no encontrado",
                        "descripcion": (
                            "No se encontró el perfil "
                            "Coordinador de PNF en el "
                            "núcleo correspondiente."
                        ),
                        "icon": "warning"
                    })

                # -------------------------------------------------
                # VALIDAR PNF
                # -------------------------------------------------

                if not pnf_coordinador:
                    return JsonResponse({
                        "estado": "fallo",
                        "title": "PNF requerido",
                        "descripcion": (
                            "Debe seleccionar un PNF "
                            "para el Coordinador de PNF."
                        ),
                        "icon": "warning"
                    })

                try:

                    id_pnf = int(
                        pnf_coordinador
                    )

                except ValueError:

                    return JsonResponse({
                        "estado": "fallo",
                        "title": "PNF no válido",
                        "descripcion": (
                            "El PNF seleccionado "
                            "no es válido."
                        ),
                        "icon": "warning"
                    })

                # -------------------------------------------------
                # BUSCAR PNF EN EL NÚCLEO
                # -------------------------------------------------

                pnf = Pnf.objects.filter(
                    id_pnf=id_pnf,
                    pnfnucleo__id_nucleo=nucleo_director
                ).first()

                if not pnf:
                    return JsonResponse({
                        "estado": "fallo",
                        "title": "PNF no encontrado",
                        "descripcion": (
                            "El PNF seleccionado "
                            "no pertenece al núcleo "
                            "del Director General."
                        ),
                        "icon": "warning"
                    })

                # -------------------------------------------------
                # COMPROBAR SI ESTÁ ASIGNADO A OTRO COORDINADOR
                # -------------------------------------------------

                existe_otro = CoordinadorPNF.objects.filter(
                    nucleo=nucleo_director,
                    pnf=pnf
                ).exclude(
                    id_coordinador=perfil.id_coordinador
                ).exists()

                if existe_otro:
                    return JsonResponse({
                        "estado": "fallo",
                        "title": "PNF no disponible",
                        "descripcion": (
                            "El PNF seleccionado ya está "
                            "asignado a otro Coordinador "
                            "de PNF."
                        ),
                        "icon": "warning"
                    })

                # -------------------------------------------------
                # ACTUALIZAR PNF Y ESTADO
                # -------------------------------------------------

                perfil.pnf = pnf
                perfil.activo = nuevo_estado

                perfil.save()

            # =====================================================
            # CONTROL DE ESTUDIO
            # =====================================================

            elif rol == "Encargado de Control de Estudio":

                perfil = ControlEstudio.objects.filter(
                    id_control=id_perfil,
                    usuario=usuario,
                    nucleo=nucleo_director
                ).first()

                if not perfil:
                    return JsonResponse({
                        "estado": "fallo",
                        "title": "Perfil no encontrado",
                        "descripcion": (
                            "No se encontró el perfil "
                            "de Control de Estudio "
                            "en el núcleo correspondiente."
                        ),
                        "icon": "warning"
                    })

                perfil.activo = nuevo_estado

                perfil.save(
                    update_fields=["activo"]
                )

            # =====================================================
            # ROL NO VÁLIDO
            # =====================================================

            else:

                return JsonResponse({
                    "estado": "fallo",
                    "title": "Perfil no válido",
                    "descripcion": (
                        f"El perfil '{rol}' "
                        "no puede ser actualizado."
                    ),
                    "icon": "warning"
                })
            
        return JsonResponse({
            "estado": "exito",
            "title": "Perfil actualizado",
            "descripcion": (
                "El perfil fue habilitado correctamente."
                if nuevo_estado
                else
                "El perfil fue deshabilitado correctamente."
            ),
            "icon": "success",
            "activo": nuevo_estado
        })

    except Exception as error:
        print(f"Error en act_per_reg: {error}")

        return JsonResponse({
            "estado": "fallo",
            "title": "Error",
            "descripcion": (
                "Ocurrió un error al actualizar "   
                "el estado del perfil."
            ),
            "icon": "error"
        })