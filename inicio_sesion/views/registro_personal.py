from django.shortcuts import render
from django.http import JsonResponse
from django.db import transaction

from inicio_sesion.models import Usuario, Estudiante, Pnf, Contacto, PNFNucleo, DirectorGeneral, Docente, CoordinadorPNF, ControlEstudio

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

    return render(request, "Director_General/gestion_personal/pre_registro_personal.html")

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

def vis_per_asig(request):
    return render(request, "Director_General/gestion_personal/visualizar_personal_registrado.html")


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
                "descripcion": "Por favor, ingrese los números de su cedula de identidad."
            })

        cedula_identidad = nacionalidad + "-" + cedula

        # BUSCAR USUARIO
        usuario = Usuario.objects.filter(cedula_identidad=cedula_identidad).first()

        if not usuario:
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "No encontrado",
                "descripcion": "No existe un usuario registrado con esa cédula."
            })

        # BUSCAR DIRECTOR GENERAL
        director = DirectorGeneral.objects.filter(
            usuario__cedula_identidad=request.session.get("cedula_usuario")
        ).select_related(
            "nucleo"
        ).first()

        if not director:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Error",
                "descripcion": "No se encontró el Director General."
            })

        # NÚCLEO DONDE SE REALIZA LA ASIGNACIÓN
        nucleo = director.nucleo

        # DATOS DEL USUARIO
        datos_usuario = {
            "id_usuario": usuario.id_usuario,
            "nombres": usuario.nombres,
            "apellidos": usuario.apellidos,
            "cedula": usuario.cedula_identidad,
        }


        # PERFILES QUE YA TIENE EL USUARIO
        perfiles = []

        # DOCENTE
        docentes = Docente.objects.filter(
            usuario=usuario
        ).select_related(
            "nucleo",
            "pnf"
        )

        for docente in docentes:
            perfiles.append({
                "rol": "Docente",
                "tipo": "docente",
                "id_perfil": docente.id_docente,
                "activo": docente.activo,
                "estado": "ACTIVO" if docente.activo else "INHABILITADO",
                "nucleo": docente.nucleo.municipio,
                "id_pnf": docente.pnf.id_pnf if docente.pnf else None,
                "pnf": docente.pnf.pnf if docente.pnf else "NO CUENTA CON P.N.F",
            })

        # COORDINADOR PNF
        coordinadores = CoordinadorPNF.objects.filter(
            usuario=usuario
        ).select_related(
            "nucleo",
            "pnf"
        )

        for coordinador in coordinadores:
            perfiles.append({
                "rol": "Coordinador de PNF",
                "tipo": "coordinador_pnf",
                "id_perfil": coordinador.id_coordinador,
                "activo": coordinador.activo,
                "estado": "ACTIVO" if coordinador.activo else "INHABILITADO",
                "nucleo": coordinador.nucleo.municipio,
                "id_pnf": coordinador.pnf.id_pnf if coordinador.pnf else None,
                "pnf": coordinador.pnf.pnf if coordinador.pnf else "NO CUENTA CON P.N.F",
            })

        # CONTROL DE ESTUDIO
        controles = ControlEstudio.objects.filter(
            usuario=usuario
        ).select_related(
            "nucleo"
        )

        for control in controles:
            perfiles.append({
                "rol": "Encargado de Control de Estudio",
                "tipo": "control_estudio",
                "id_perfil": control.id_control,
                "activo": control.activo,
                "estado": "ACTIVO" if control.activo else "INHABILITADO",
                "nucleo": control.nucleo.municipio,
                "id_pnf": None,
                "pnf": "NO CUENTA CON P.N.F",
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


        # ==========================================================
        # DOCENTE
        # ==========================================================
        #
        # Un usuario puede tener varios perfiles de Docente,
        # pero NO puede repetir el mismo PNF dentro del mismo núcleo.
        #
        # Ejemplo:
        #
        # Informática     -> ya tiene
        # Administración  -> ya tiene
        # Contaduría      -> disponible
        #
        # Entonces el perfil "Docente" sigue disponible y solamente
        # se podrá seleccionar Contaduría.
        # ==========================================================

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


        # ==========================================================
        # COORDINADOR PNF
        # ==========================================================
        #
        # El usuario solamente puede tener UNA coordinación.
        #
        # Si ya tiene una coordinación, el perfil NO estará
        # disponible nuevamente, independientemente del PNF.
        # ==========================================================

        tiene_coordinador = CoordinadorPNF.objects.filter(
            usuario=usuario,
            activo=True
        ).exists()


        # PNF que ya tienen un coordinador activo en el núcleo
        pnfs_coordinador_ocupados = set(
            CoordinadorPNF.objects.filter(
                nucleo=nucleo,
                activo=True
            ).values_list(
                "pnf_id",
                flat=True
            )
        )


        # PNF que todavía pueden recibir un coordinador
        pnfs_disponibles_coordinador = [
            pnf
            for pnf in pnfs_nucleo
            if pnf["id_pnf"] not in pnfs_coordinador_ocupados
        ]


        # ==========================================================
        # CONTROL DE ESTUDIO
        # ==========================================================
        #
        # Solo puede existir un Control de Estudio por núcleo.
        #
        # Si el usuario ya tiene Control de Estudio en este núcleo,
        # no se muestra nuevamente.
        # ==========================================================

        tiene_control_estudio = ControlEstudio.objects.filter(
            usuario=usuario,
            nucleo=nucleo,
            activo=True
        ).exists()


        # PERFILES DISPONIBLES
        perfiles_disponibles = []


        # ----------------------------------------------------------
        # DOCENTE
        # ----------------------------------------------------------
        #
        # Se muestra si existe al menos un PNF del núcleo que el
        # usuario todavía no tenga asignado como Docente.
        # ----------------------------------------------------------

        if pnfs_disponibles_docente:

            perfiles_disponibles.append({
                "tipo": "docente",
                "rol": "Docente"
            })


        # ----------------------------------------------------------
        # COORDINADOR PNF
        # ----------------------------------------------------------
        #
        # Se muestra solamente si:
        #
        # 1. El usuario todavía NO tiene una coordinación.
        # 2. Existe algún PNF disponible en el núcleo.
        # ----------------------------------------------------------

        if not tiene_coordinador and pnfs_disponibles_coordinador:

            perfiles_disponibles.append({
                "tipo": "coordinador_pnf",
                "rol": "Coordinador de PNF"
            })


        # ----------------------------------------------------------
        # CONTROL DE ESTUDIO
        # ----------------------------------------------------------
        #
        # Se muestra solamente si el usuario todavía no tiene
        # Control de Estudio en el núcleo actual.
        # ----------------------------------------------------------

        if not tiene_control_estudio:

            perfiles_disponibles.append({
                "tipo": "control_estudio",
                "rol": "Encargado de Control de Estudio"
            })

        # RESPUESTA
        return JsonResponse({
            "estado": "exito",
            "usuario": datos_usuario,
            "perfiles": perfiles,
            "perfiles_disponibles": perfiles_disponibles,
            "pnfs_disponibles_docente": pnfs_disponibles_docente,
            "pnfs_disponibles_coordinador": pnfs_disponibles_coordinador
        })



def act_per_asig(request):

    if request.method == "POST":

        # ==========================================================
        # DATOS DEL USUARIO
        # ==========================================================

        cedula_usuario = request.POST.get(
            "cedula_usuario"
        )


        # ==========================================================
        # NUEVAS ASIGNACIONES
        # ==========================================================

        # Docente puede tener varios PNF
        pnfs_docente = request.POST.getlist(
            "pnfs_docente"
        )


        # Coordinador solamente puede seleccionar un PNF
        pnf_coordinador = request.POST.get(
            "pnf_coordinador"
        )


        # Control de Estudio
        control_estudio = request.POST.get(
            "control_estudio"
        )


        # ==========================================================
        # ESTADOS DE LOS PERFILES EXISTENTES
        # ==========================================================

        perfiles_estado = request.POST.getlist(
            "perfiles_estado"
        )


        # ==========================================================
        # DIRECTOR GENERAL
        # ==========================================================

        director = DirectorGeneral.objects.filter(
            usuario__cedula_identidad=request.session.get(
                "cedula_usuario"
            )
        ).select_related(
            "nucleo"
        ).first()


        if not director:

            return JsonResponse({
                "estado": "fallo",
                "title": "Error",
                "descripcion": (
                    "No se encontró el Director General."
                ),
                "icon": "error"
            })


        nucleo = director.nucleo


        # ==========================================================
        # BUSCAR USUARIO
        # ==========================================================

        usuario = Usuario.objects.filter(
            cedula_identidad=cedula_usuario
        ).first()


        if not usuario:

            return JsonResponse({
                "estado": "fallo",
                "title": "Usuario no encontrado",
                "descripcion": (
                    "No existe un usuario registrado "
                    "con esa cédula."
                ),
                "icon": "warning"
            })


        try:

            with transaction.atomic():


                # ==================================================
                # INHABILITAR PERFILES EXISTENTES
                # ==================================================
                #
                # Solo se procesan perfiles pertenecientes al
                # núcleo donde trabaja el Director General.
                #
                # perfiles_estado contiene los ID de los checks
                # que permanecen marcados.
                #
                # Los que NO estén aquí se inhabilitan.
                # ==================================================


                # ----------------------------------------------
                # DOCENTES
                # ----------------------------------------------

                docentes = Docente.objects.filter(
                    usuario=usuario,
                    nucleo=nucleo
                )


                for docente in docentes:

                    if str(docente.id_docente) in perfiles_estado:

                        if not docente.activo:

                            docente.activo = True

                            docente.save(
                                update_fields=["activo"]
                            )

                    else:

                        if docente.activo:

                            docente.activo = False

                            docente.save(
                                update_fields=["activo"]
                            )


                # ----------------------------------------------
                # COORDINADOR PNF
                # ----------------------------------------------

                coordinadores = CoordinadorPNF.objects.filter(
                    usuario=usuario,
                    nucleo=nucleo
                )


                for coordinador in coordinadores:

                    if str(coordinador.id_coordinador) in perfiles_estado:

                        if not coordinador.activo:

                            coordinador.activo = True

                            coordinador.save(
                                update_fields=["activo"]
                            )

                    else:

                        if coordinador.activo:

                            coordinador.activo = False

                            coordinador.save(
                                update_fields=["activo"]
                            )


                # ----------------------------------------------
                # CONTROL DE ESTUDIO
                # ----------------------------------------------

                controles = ControlEstudio.objects.filter(
                    usuario=usuario,
                    nucleo=nucleo
                )


                for control in controles:

                    if str(control.id_control) in perfiles_estado:

                        if not control.activo:

                            control.activo = True

                            control.save(
                                update_fields=["activo"]
                            )

                    else:

                        if control.activo:

                            control.activo = False

                            control.save(
                                update_fields=["activo"]
                            )


                # ==================================================
                # AGREGAR / REACTIVAR DOCENTE
                # ==================================================

                for id_pnf in pnfs_docente:

                    pnf = Pnf.objects.filter(
                        id_pnf=id_pnf
                    ).first()


                    if not pnf:
                        continue


                    # Verificar que el PNF pertenezca al núcleo

                    pertenece_nucleo = PNFNucleo.objects.filter(
                        id_nucleo=nucleo,
                        id_pnf=pnf
                    ).exists()


                    if not pertenece_nucleo:
                        continue


                    docente, creado = Docente.objects.get_or_create(
                        usuario=usuario,
                        nucleo=nucleo,
                        pnf=pnf,
                        defaults={
                            "activo": True
                        }
                    )


                    if not creado and not docente.activo:

                        docente.activo = True

                        docente.save(
                            update_fields=["activo"]
                        )


                # ==================================================
                # AGREGAR / REACTIVAR COORDINADOR
                # ==================================================

                if pnf_coordinador:

                    pnf = Pnf.objects.filter(
                        id_pnf=pnf_coordinador
                    ).first()


                    if pnf:

                        pertenece_nucleo = PNFNucleo.objects.filter(
                            id_nucleo=nucleo,
                            id_pnf=pnf
                        ).exists()


                        if pertenece_nucleo:

                            # --------------------------------------
                            # El usuario no puede tener otra
                            # coordinación activa.
                            # --------------------------------------

                            otra_coordinacion = CoordinadorPNF.objects.filter(
                                usuario=usuario,
                                activo=True
                            ).exclude(
                                pnf=pnf
                            ).first()


                            if otra_coordinacion:

                                return JsonResponse({
                                    "estado": "fallo",
                                    "title": "Coordinación existente",
                                    "descripcion": (
                                        "El usuario ya tiene una "
                                        "Coordinación de PNF activa."
                                    ),
                                    "icon": "warning"
                                })


                            # --------------------------------------
                            # El PNF no puede tener otro coordinador
                            # activo dentro del núcleo.
                            # --------------------------------------

                            pnf_ocupado = CoordinadorPNF.objects.filter(
                                nucleo=nucleo,
                                pnf=pnf,
                                activo=True
                            ).exclude(
                                usuario=usuario
                            ).exists()


                            if pnf_ocupado:

                                return JsonResponse({
                                    "estado": "fallo",
                                    "title": "PNF ocupado",
                                    "descripcion": (
                                        "El P.N.F seleccionado ya "
                                        "tiene un Coordinador asignado."
                                    ),
                                    "icon": "warning"
                                })


                            coordinador, creado = CoordinadorPNF.objects.get_or_create(
                                usuario=usuario,
                                nucleo=nucleo,
                                pnf=pnf,
                                defaults={
                                    "activo": True
                                }
                            )


                            if not creado and not coordinador.activo:

                                coordinador.activo = True

                                coordinador.save(
                                    update_fields=["activo"]
                                )


                # ==================================================
                # AGREGAR / REACTIVAR CONTROL DE ESTUDIO
                # ==================================================

                if control_estudio == "1":

                    control, creado = ControlEstudio.objects.get_or_create(
                        usuario=usuario,
                        nucleo=nucleo,
                        defaults={
                            "activo": True
                        }
                    )


                    if not creado and not control.activo:

                        control.activo = True

                        control.save(
                            update_fields=["activo"]
                        )


            # ======================================================
            # RESPUESTA
            # ======================================================

            return JsonResponse({
                "estado": "exito",
                "title": "Perfiles actualizados",
                "descripcion": (
                    "Los perfiles fueron actualizados correctamente."
                ),
                "icon": "success"
            })


        except Exception as error:

            print("ERROR:", error)

            return JsonResponse({
                "estado": "fallo",
                "title": "Error",
                "descripcion": (
                    "Ocurrió un error al actualizar los perfiles."
                ),
                "icon": "error"
            })


    return render(
        request,
        "Director_General/gestion_personal/actualizar_personal_registrado.html"
    )



