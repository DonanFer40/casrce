import logging
from pathlib import Path

from django.shortcuts import render
from django.urls import reverse
from django.http import JsonResponse
from django.db import transaction
from django.utils import timezone
from django.db.models import Q

from inicio_sesion.models import (
    Usuario,
    Nucleos,
    TrayectoAcademico,
    Pnf,
    Contacto,
    PNFNucleo,
    Nacimiento,
    Residencia,
    Estudiante,
    Docente,
    CoordinadorPNF,
    ControlEstudio,
    DirectorGeneral,
    ContactoAuxiliar,
    Discapacidad,
    EstatusEstudiante,
    DocumentosEstudiante,
    InformacionSecundaria,
    DatosPreofesion,
    ExpedienteEstudiante,
    HistorialExpedienteEstudiante,
)

from inicio_sesion.services.verificacion_documentos import (
    verificar_documentos_estudiante,
    ErrorVerificacionGemini,
    ErrorArchivoDocumento,
)

from documentos.models import DocumentoInstitucional
from documentos.services.generador_pdf import crear_documento_institucional
from documentos.services.planilla_inscripcion import construir_contenido_planilla
from documentos.services.correo_planilla import enviar_planilla_inscripcion


logger = logging.getLogger(__name__)


def datos_usr_admin(request):

    if not request.session.get("usuario_nombre"):
        return JsonResponse({
            "estado": "no_exite",
            "icon": "error",
            "title": "No Existe",
            "descripcion": (
                "Estimado(a), no ha realizado el proceso autenticación."
            ),
            "url": reverse("inicio_sesion")
        })

    ci_usuario = request.session.get("cedula_usuario")

    datos_basicos = Usuario.objects.filter(
        cedula_identidad=ci_usuario
    ).first()

    if not datos_basicos:
        return JsonResponse({
            "estado": "no_exite",
            "icon": "error",
            "title": "No Existe",
            "descripcion": "Estimado(a), no se encuentra registrado.",
            "url": reverse("inicio_sesion")
        })

    contacto = Contacto.objects.filter(
        id_usuario=datos_basicos
    ).first()

    return JsonResponse({
        "usuario": {
            "nombres": datos_basicos.nombres,
            "apellidos": datos_basicos.apellidos,
            "cedula_identidad": datos_basicos.cedula_identidad,
            "genero": datos_basicos.genero,
            "estado_civil": datos_basicos.estado_civil
        },
        "contacto": {
            "telefono_personal": (
                contacto.telefono_personal if contacto else ""
            ),
            "correo_electronico": (
                contacto.correo_electronico if contacto else ""
            ),
        }
    })


def validar_ci_auxiliar(request):

    if request.method == "POST":

        nacionalidad = request.POST.get("nacionalidad")
        cedula = request.POST.get("cedula")

        existe = ContactoAuxiliar.objects.filter(
            cedula_identidad=f"{nacionalidad}-{cedula}"
        ).exists()

        return JsonResponse({"existe": existe})


def validar_cod_opsu(request):

    if request.method == "POST":

        codigo_opsu = request.POST.get("codigo")

        existe = InformacionSecundaria.objects.filter(
            codigo_sni_opsu=codigo_opsu
        ).exists()

        return JsonResponse({"existe": existe})


def validar_ci_usr(request):

    if request.method == "POST":

        nacionalidad = request.POST.get("nacionalidad")
        cedula = request.POST.get("cedula")

        existe = Usuario.objects.filter(
            cedula_identidad=f"{nacionalidad}-{cedula}"
        ).exists()

        return JsonResponse({"existe": existe})


def validar_email(request):

    if request.method == "POST":

        correo = request.POST.get("correo")
        dominio = request.POST.get("dominio")

        email = f"{correo}{dominio}"

        existe = Contacto.objects.filter(
            Q(correo_electronico__iexact=email) |
            Q(correo_alternativo__iexact=email)
        ).exists()

        return JsonResponse({"existe": existe})


def pnfs_cursar(request):

    nucleo_seleccionado = request.POST.get("nucleo")

    nucleo = Nucleos.objects.filter(
        municipio=nucleo_seleccionado
    ).first()

    if not nucleo:
        return JsonResponse({"pnfs": []})

    pnfs = PNFNucleo.objects.select_related(
        "id_pnf"
    ).filter(id_nucleo=nucleo)

    datos = []

    for pnf_nucleo in pnfs:

        datos.append({
            "id": pnf_nucleo.id_pnf.id_pnf,
            "nombre": pnf_nucleo.id_pnf.pnf
        })

    return JsonResponse({
        "pnfs": datos
    })


def comp_registro(request):

    if request.method == "POST":

        # ==========================================================
        # VALIDACIÓN DE LONGITUD DE LAS DIRECCIONES
        # ==========================================================

        direccion_nacimiento = (
            request.POST.get("direccion_nacimiento", "") or ""
        )

        direccion_domicilio = (
            request.POST.get("direccion_domicilio", "") or ""
        )

        direcciones = {
            "Dirección de nacimiento": direccion_nacimiento,
            "Dirección de residencia": direccion_domicilio,
        }

        for nombre, direccion in direcciones.items():

            if len(direccion) > 100:

                return JsonResponse({
                    "estado": "fallo",
                    "title": "Dirección demasiado larga",
                    "descripcion": (
                        f"{nombre} no puede superar los 100 caracteres."
                    ),
                    "icon": "warning"
                })

        # ==========================================================
        # VALIDACIÓN GENERAL DE CAMPOS OBLIGATORIOS
        # ==========================================================

        usuario_sesion = Usuario.objects.filter(
            cedula_identidad=request.session.get("cedula_usuario")
        ).first()

        if not usuario_sesion:

            return JsonResponse({
                "estado": "fallo",
                "title": "Sesión no válida",
                "descripcion": (
                    "No se encontró el usuario de la sesión. "
                    "Inicia sesión nuevamente."
                ),
                "icon": "error"
            }, status=401)

        es_estudiante = Estudiante.objects.filter(
            usuario=usuario_sesion
        ).exists()

        if (
            es_estudiante
            and ExpedienteEstudiante.objects.filter(
                usuario=usuario_sesion
            ).exists()
        ):

            return JsonResponse({
                "estado": "fallo",
                "title": "Registro ya recibido",
                "descripcion": (
                    "Este estudiante ya posee un expediente registrado. "
                    "No se sobrescribirá su información ni su historial administrativo."
                ),
                "icon": "info",
            }, status=409)

        # ==========================================================
        # CAMPOS OBLIGATORIOS GENERALES
        # ==========================================================

        campos_requeridos = [
            ("genero", "Género"),
            ("estado_civil", "Estado civil"),
            ("prefijo_telefono_principal", "Prefijo del teléfono principal"),
            ("num_telefono_principal", "Número del teléfono principal"),
            ("correo_principal", "Correo electrónico principal"),
            ("dominio_correo_principal", "Dominio del correo principal"),
            ("pais_nacimiento", "País de nacimiento"),
            ("direccion_nacimiento", "Dirección de nacimiento"),
            ("fecha_nacimiento", "Fecha de nacimiento"),
            ("condicion_residencia", "Condición de residencia"),
            ("municipio_residencia", "Municipio de residencia"),
            ("parroquia_residencia", "Parroquia de residencia"),
            ("direccion_domicilio", "Dirección de residencia"),
        ]

        faltantes = []

        for nombre_campo, etiqueta in campos_requeridos:

            valor = request.POST.get(nombre_campo, "").strip()

            if not valor:
                faltantes.append(etiqueta)

        # ==========================================================
        # VALIDACIÓN DE UBICACIÓN DE NACIMIENTO
        # ==========================================================

        ubicaciones = [
            (
                ("estado_nacimiento", "estado_novzla"),
                "Estado de nacimiento"
            ),
            (
                ("municipio_nacimiento", "municipio_novzla"),
                "Municipio de nacimiento"
            ),
            (
                ("parroquia_nacimiento", "parroquia_novzla"),
                "Parroquia de nacimiento"
            ),
        ]

        for alternativas, etiqueta in ubicaciones:

            valores = [
                request.POST.get(nombre, "").strip()
                for nombre in alternativas
            ]

            if not any(valores):
                faltantes.append(etiqueta)

        # ==========================================================
        # VALIDACIONES ESPECÍFICAS DEL ESTUDIANTE
        # ==========================================================

        if es_estudiante:

            campos_estudiante = [
                ("tipos_secundaria", "Tipo de institución de secundaria"),
                ("nombre_secundaria", "Nombre del liceo"),
                ("fecha_graduacion", "Fecha de graduación"),
                ("codigo_opsu", "Código OPSU"),
            ]

            for nombre_campo, etiqueta in campos_estudiante:

                valor = request.POST.get(nombre_campo, "").strip()

                if not valor:
                    faltantes.append(etiqueta)

            nucleo_formulario = request.POST.get(
                "nucleo_seleccionado", ""
            ).strip()

            pnf_formulario = request.POST.get(
                "pnf_seleccionado", ""
            ).strip()

            if not nucleo_formulario or not pnf_formulario:

                faltantes.append("Seleccionar un núcleo y un PNF")

            elif not PNFNucleo.objects.filter(
                id_nucleo__municipio=nucleo_formulario,
                id_pnf_id=pnf_formulario,
            ).exists():

                return JsonResponse({
                    "estado": "fallo",
                    "title": "Selección académica no válida",
                    "descripcion": (
                        "El PNF seleccionado no pertenece al núcleo indicado."
                    ),
                    "icon": "warning",
                }, status=400)

            documentos_requeridos = [
                ("CI_estudiante", "Cédula de identidad"),
                ("TBachiller_estudiante", "Título de bachiller"),
                ("SNotas_estudiante", "Sábana de notas"),
                ("OPSU_estudiante", "Documento OPSU"),
            ]

            for nombre_campo, etiqueta in documentos_requeridos:

                if not request.FILES.get(nombre_campo):
                    faltantes.append(etiqueta)

        else:

            campos_administrativos = [
                ("profesion_pregrado", "Profesión de egreso"),
                ("universidad_pregrado", "Universidad de egreso"),
                ("pais_profesion", "País de egreso"),
            ]

            for nombre_campo, etiqueta in campos_administrativos:

                valor = request.POST.get(nombre_campo, "").strip()

                if not valor:
                    faltantes.append(etiqueta)

        # ==========================================================
        # RESPUESTA DE CAMPOS FALTANTES
        # ==========================================================

        if faltantes:

            lista_faltantes = "\n".join(
                f"• {campo}" for campo in faltantes
            )

            return JsonResponse({
                "estado": "fallo",
                "title": "Campos obligatorios pendientes",
                "descripcion": (
                    "Completa los siguientes campos antes de continuar:\n"
                    + lista_faltantes
                ),
                "campos_faltantes": faltantes,
                "icon": "warning"
            }, status=400)

        # ==========================================================
        # RECOPILACIÓN DE DATOS
        # ==========================================================

        genero = request.POST.get("genero")
        estado_civil = request.POST.get("estado_civil")

        prefijo_telefono_principal = request.POST.get(
            "prefijo_telefono_principal"
        )

        num_telefono_principal = request.POST.get(
            "num_telefono_principal"
        )

        prefijo_telefono_secundaria = request.POST.get(
            "prefijo_telefono_secundaria"
        )

        num_telefono_secundaria = request.POST.get(
            "num_telefono_secundaria"
        )

        # ==========================================================
        # VALIDACIÓN DEL TELÉFONO SECUNDARIO
        # ==========================================================

        if not prefijo_telefono_secundaria and num_telefono_secundaria:

            return JsonResponse({
                "estado": "fallo",
                "title": "Vacío",
                "descripcion": (
                    "Debe seleccionar el prefijo telefónico o dejar "
                    "vacío el número telefónico."
                ),
                "icon": "warning"
            })

        if prefijo_telefono_secundaria and not num_telefono_secundaria:

            return JsonResponse({
                "estado": "fallo",
                "title": "Vacío",
                "descripcion": (
                    "Debe ingresar el número telefónico o seleccionar "
                    "la opción TLF."
                ),
                "icon": "warning"
            })

        telefono_secundario = (
            prefijo_telefono_secundaria + num_telefono_secundaria
            if prefijo_telefono_secundaria and num_telefono_secundaria
            else "N/A"
        )

        # ==========================================================
        # CORREOS ELECTRÓNICOS
        # ==========================================================

        correo_principal = request.POST.get("correo_principal")

        dominio_correo_principal = request.POST.get(
            "dominio_correo_principal"
        )

        correo_secundaria = request.POST.get(
            "correo_secundaria", ""
        ).strip()

        dominio_correo_secundaria = request.POST.get(
            "dominio_correo_secundaria", ""
        ).strip()

        if bool(correo_secundaria) != bool(dominio_correo_secundaria):

            return JsonResponse({
                "estado": "fallo",
                "title": "Correo alternativo incompleto",
                "descripcion": (
                    "Si deseas registrar un correo alternativo, completa "
                    "tanto el usuario como el dominio. También puedes "
                    "dejar ambos campos vacíos."
                ),
                "icon": "warning",
            }, status=400)

        correo_electronico1 = (
            correo_principal + dominio_correo_principal
        )

        correo_electronico2 = (
            correo_secundaria + dominio_correo_secundaria
            if correo_secundaria and dominio_correo_secundaria
            else None
        )

        if (
            correo_electronico2
            and correo_electronico1 == correo_electronico2
        ):

            return JsonResponse({
                "estado": "fallo",
                "title": "Error",
                "descripcion": (
                    "Por favor, ingrese correos electrónicos diferentes."
                ),
                "icon": "error"
            })

        telefono_principal = (
            prefijo_telefono_principal + num_telefono_principal
        )

        # ==========================================================
        # DATOS DE UBICACIÓN Y RESIDENCIA
        # ==========================================================

        nucleo = request.POST.get("nucleo_seleccionado")
        pnf = request.POST.get("pnf_seleccionado")

        pais_nacimiento = request.POST.get("pais_nacimiento")

        direccion_nacimiento = request.POST.get(
            "direccion_nacimiento"
        )

        fecha_nacimiento = request.POST.get("fecha_nacimiento")

        condicion_residencia = request.POST.get(
            "condicion_residencia"
        )

        municipio_residencia = request.POST.get(
            "municipio_residencia"
        )

        parroquia_residencia = request.POST.get(
            "parroquia_residencia"
        )

        direccion_domicilio = request.POST.get(
            "direccion_domicilio"
        )

        # ==========================================================
        # DATOS PROFESIONALES
        # ==========================================================

        profesion_pregrado = request.POST.get("profesion_pregrado")
        universidad_pregrado = request.POST.get("universidad_pregrado")
        pais_profesion = request.POST.get("pais_profesion")

        # ==========================================================
        # DATOS DE SECUNDARIA
        # ==========================================================

        tipos_secundaria = request.POST.get("tipos_secundaria")
        nombre_secundaria = request.POST.get("nombre_secundaria")
        fecha_graduacion = request.POST.get("fecha_graduacion")
        codigo_opsu = request.POST.get("codigo_opsu")

        # ==========================================================
        # CONTACTO AUXILIAR
        # ==========================================================

        nacionalidad_auxiliar = request.POST.get(
            "nacionalidad_auxiliar"
        )

        ci_auxiliar = request.POST.get("ci_auxiliar")

        prefijo_auxiliar = request.POST.get("prefijo_auxiliar")
        telefono_auxiliar = request.POST.get("telefono_auxiliar")

        nombres_auxiliar = (
            request.POST.get("nombres_auxiliar")
            or "N/A"
        )

        apellidos_auxiliar = (
            request.POST.get("apellidos_auxiliar")
            or "N/A"
        )

        if not nacionalidad_auxiliar and ci_auxiliar:

            return JsonResponse({
                "estado": "fallo",
                "title": "Vacío",
                "descripcion": (
                    "Debe seleccionar la nacionalidad o vaciar el "
                    "campo correspondiente al número de cédula."
                ),
                "icon": "warning"
            })

        if nacionalidad_auxiliar and not ci_auxiliar:

            return JsonResponse({
                "estado": "fallo",
                "title": "Vacío",
                "descripcion": (
                    "Debe ingresar el número de cédula o seleccionar "
                    "la opción N."
                ),
                "icon": "warning"
            })

        cedula_auxiliar = (
            nacionalidad_auxiliar + "-" + ci_auxiliar
            if nacionalidad_auxiliar and ci_auxiliar
            else "N/A"
        )

        if not prefijo_auxiliar and telefono_auxiliar:

            return JsonResponse({
                "estado": "fallo",
                "title": "Vacío",
                "descripcion": (
                    "Debe seleccionar el prefijo telefónico o dejar "
                    "vacío el número telefónico."
                ),
                "icon": "warning"
            })

        if prefijo_auxiliar and not telefono_auxiliar:

            return JsonResponse({
                "estado": "fallo",
                "title": "Vacío",
                "descripcion": (
                    "Debe ingresar el número telefónico o seleccionar "
                    "la opción TLF."
                ),
                "icon": "warning"
            })

        telefono_auxiliar = (
            prefijo_auxiliar + telefono_auxiliar
            if prefijo_auxiliar and telefono_auxiliar
            else "N/A"
        )

        parestenco_auxiliar = (
            request.POST.get("parestenco_auxiliar")
            or "N/A"
        )

        # ==========================================================
        # DATOS DE DISCAPACIDAD
        # ==========================================================

        carnet_dispacidad = (
            request.POST.get("carnet_dispacidad")
            or "N/A"
        )

        registro_medico = (
            request.POST.get("registro_medico")
            or "N/A"
        )

        tipo_discapacidad = (
            request.POST.get("tipo_discapacidad")
            or "N/A"
        )

        grado_discapacidad = (
            request.POST.get("grado_discapacidad")
            or "N/A"
        )

        causa_discapacidad = (
            request.POST.get("causa_discapacidad")
            or "N/A"
        )

        # ==========================================================
        # VALIDACIONES GENERALES COMPLEMENTARIAS
        # ==========================================================

        campos_generales = [
            (
                genero,
                "Género",
                "Por favor, seleccione una de las opciones presentes."
            ),
            (
                estado_civil,
                "Estado Civil",
                "Por favor, seleccione una de las opciones presentadas."
            ),
            (
                prefijo_telefono_principal,
                "Prefijo Telefónico",
                "Por favor, seleccione uno de los prefijos telefónicos."
            ),
            (
                num_telefono_principal,
                "Número Telefónico",
                "Por favor, ingrese el número telefónico."
            ),
            (
                pais_nacimiento,
                "País de Nacimiento",
                "Por favor, seleccione una de las opciones."
            ),
            (
                direccion_nacimiento,
                "Dirección de Nacimiento",
                "Por favor, ingrese la dirección de nacimiento."
            ),
            (
                fecha_nacimiento,
                "Fecha de Nacimiento",
                "Por favor, ingrese la fecha de nacimiento."
            ),
            (
                condicion_residencia,
                "Condición de Residencia",
                "Por favor, seleccione una de las opciones."
            ),
            (
                municipio_residencia,
                "Municipio de Residencia",
                "Por favor, seleccione una de las opciones."
            ),
            (
                parroquia_residencia,
                "Parroquia de Residencia",
                "Por favor, seleccione una de las opciones."
            ),
            (
                direccion_domicilio,
                "Dirección de Residencia",
                "Por favor, ingrese la dirección de domicilio."
            ),
        ]

        for valor, titulo, mensaje in campos_generales:

            if not valor:

                return JsonResponse({
                    "estado": "fallo",
                    "title": titulo,
                    "descripcion": mensaje,
                    "icon": "warning"
                })

        # ==========================================================
        # UBICACIÓN DE NACIMIENTO
        # ==========================================================

        estado_nacimiento = (
            request.POST.get("estado_nacimiento")
            or request.POST.get("estado_novzla")
        )

        if not estado_nacimiento:

            return JsonResponse({
                "estado": "fallo",
                "title": "Vacío",
                "descripcion": (
                    "Por favor, selecciona o ingresa el estado de nacimiento."
                ),
                "icon": "warning"
            })

        municipio_nacimiento = (
            request.POST.get("municipio_nacimiento")
            or request.POST.get("municipio_novzla")
        )

        if not municipio_nacimiento:

            return JsonResponse({
                "estado": "fallo",
                "title": "Vacío",
                "descripcion": (
                    "Por favor, selecciona o ingresa el municipio de nacimiento."
                ),
                "icon": "warning"
            })

        parroquia_nacimiento = (
            request.POST.get("parroquia_nacimiento")
            or request.POST.get("parroquia_novzla")
        )

        if not parroquia_nacimiento:

            return JsonResponse({
                "estado": "fallo",
                "title": "Vacío",
                "descripcion": (
                    "Por favor, selecciona o ingresa la parroquia de nacimiento."
                ),
                "icon": "warning"
            })

        # ==========================================================
        # IDENTIFICACIÓN DEL USUARIO Y SUS ROLES
        # ==========================================================

        usuario = Usuario.objects.get(
            cedula_identidad=request.session.get("cedula_usuario")
        )

        roles = []

        if Estudiante.objects.filter(usuario=usuario).exists():
            roles.append("Estudiante")

        if Docente.objects.filter(usuario=usuario).exists():
            roles.append("Docente")

        if CoordinadorPNF.objects.filter(usuario=usuario).exists():
            roles.append("Coordinador PNF")

        if ControlEstudio.objects.filter(usuario=usuario).exists():
            roles.append("Control de Estudio")

        if DirectorGeneral.objects.filter(usuario=usuario).exists():
            roles.append("Director General")

        # ==========================================================
        # REGISTRO DE USUARIOS ADMINISTRATIVOS
        # ==========================================================

        if "Estudiante" not in roles:

            campos_administrativo = [
                (
                    profesion_pregrado,
                    "Profesión de Egreso",
                    "Por favor, ingrese la profesión de egreso de pregrado."
                ),
                (
                    universidad_pregrado,
                    "Universidad de Egreso",
                    "Por favor, ingrese la universidad de egreso de pregrado."
                ),
                (
                    pais_profesion,
                    "País de Egreso",
                    "Por favor, seleccione una de las opciones presentes."
                ),
            ]

            for valor, titulo, mensaje in campos_administrativo:

                if not valor:

                    return JsonResponse({
                        "estado": "fallo",
                        "title": titulo,
                        "descripcion": mensaje,
                        "icon": "warning"
                    })

            with transaction.atomic():

                usuario.genero = genero
                usuario.estado_civil = estado_civil
                usuario.save()

                contacto, _ = Contacto.objects.get_or_create(
                    id_usuario=usuario
                )

                contacto.telefono_personal = telefono_principal
                contacto.telefono_suplete = telefono_secundario
                contacto.correo_electronico = correo_electronico1
                contacto.correo_alternativo = correo_electronico2
                contacto.save()

                Residencia.objects.create(
                    condicion_residencia=condicion_residencia,
                    municipio=municipio_residencia,
                    parroquia=parroquia_residencia,
                    direccion_residencia=direccion_domicilio,
                    id_usuario=usuario
                )

                Nacimiento.objects.create(
                    pais=pais_nacimiento,
                    estado=estado_nacimiento,
                    municipio=municipio_nacimiento,
                    parroquia=parroquia_nacimiento,
                    direccion_nacimiento=direccion_nacimiento,
                    fecha_nacimiento=fecha_nacimiento,
                    id_usuario=usuario
                )

                DatosPreofesion.objects.create(
                    profesion_pregrado=profesion_pregrado,
                    universidad_egreso_pregrado=universidad_pregrado,
                    pais_profesion_pregrado=pais_profesion,
                    id_usuario=usuario
                )

                request.session["registro_completado"] = True

            return JsonResponse({
                "estado": "exito",
                "title": "Éxito",
                "descripcion": (
                    "Los datos del usuario se registraron exitosamente."
                ),
                "icon": "success",
                "url": reverse("panel_usuario")
            })

        # ==========================================================
        # REGISTRO DE ESTUDIANTES
        # ==========================================================

        campos_estudiantil = [
            (
                tipos_secundaria,
                "Tipo de Institución",
                "Por favor, seleccione una de las opciones presentes."
            ),
            (
                nombre_secundaria,
                "Nombre del Liceo",
                "Por favor, ingrese la institución de bachillerato."
            ),
            (
                codigo_opsu,
                "Código OPSU",
                "Por favor, ingrese el código de la OPSU."
            ),
        ]

        for valor, titulo, mensaje in campos_estudiantil:

            if not valor:

                return JsonResponse({
                    "estado": "fallo",
                    "title": titulo,
                    "descripcion": mensaje,
                    "icon": "warning"
                })

        # ==========================================================
        # VALIDACIÓN DEL NÚCLEO Y PNF
        # ==========================================================

        nucleo_seleccionado = Nucleos.objects.filter(
            municipio=nucleo
        ).first()

        pnf_seleccionado = (
            PNFNucleo.objects.filter(
                id_nucleo=nucleo_seleccionado,
                id_pnf_id=pnf,
            ).select_related("id_pnf").first()
            if nucleo_seleccionado
            else None
        )

        if not pnf_seleccionado:

            return JsonResponse({
                "estado": "fallo",
                "title": "Selección académica no válida",
                "descripcion": (
                    "El núcleo y el PNF seleccionados no corresponden "
                    "a una oferta académica disponible."
                ),
                "icon": "warning",
            }, status=400)

        # ==========================================================
        # DOCUMENTOS OBLIGATORIOS
        # ==========================================================

        documentos = {
            "Cédula de Identidad": request.FILES.get("CI_estudiante"),
            "Título de Bachiller": request.FILES.get("TBachiller_estudiante"),
            "Sabana de Notas": request.FILES.get("SNotas_estudiante"),
            "OPSU": request.FILES.get("OPSU_estudiante"),
        }

        if not all(documentos.values()):

            return JsonResponse({
                "estado": "fallo",
                "title": "Documentos incompletos",
                "descripcion": (
                    "Debe cargar todos los documentos requeridos para continuar."
                ),
                "icon": "warning"
            })

        # ==========================================================
        # REVISIÓN PRELIMINAR CON GEMINI
        # ==========================================================

        archivos_revision = {
            "CI_estudiante": request.FILES.get("CI_estudiante"),
            "TBachiller_estudiante": request.FILES.get("TBachiller_estudiante"),
            "SNotas_estudiante": request.FILES.get("SNotas_estudiante"),
            "OPSU_estudiante": request.FILES.get("OPSU_estudiante"),
        }

        try:

            resultados_verificacion = verificar_documentos_estudiante(
                archivos_revision
            )

            revision_ia_disponible = True

        except ErrorArchivoDocumento as error:

            return JsonResponse({
                "estado": "fallo",
                "title": "Archivo no válido",
                "descripcion": str(error),
                "icon": "warning",
            }, status=400)

        except ErrorVerificacionGemini:

            revision_ia_disponible = False

            resultados_verificacion = {
                campo: {
                    "nombre": nombre,
                    "estado": "REVISION_MANUAL",
                    "tipo_detectado": "No determinado",
                    "legible": False,
                    "motivo": (
                        "La revisión automática no estuvo disponible. "
                        "El documento requiere comprobación por un funcionario."
                    ),
                }
                for campo, nombre in [
                    ("CI_estudiante", "Cédula de identidad"),
                    ("TBachiller_estudiante", "Título de bachiller"),
                    ("SNotas_estudiante", "Sábana de notas"),
                    ("OPSU_estudiante", "Documento OPSU"),
                ]
            }

        # ==========================================================
        # RESULTADOS DE LA REVISIÓN AUTOMÁTICA
        # ==========================================================

        observaciones_ia = [
            (
                f"{resultado['nombre']}: "
                f"{resultado['estado']} — {resultado['motivo']}"
            )
            for resultado in resultados_verificacion.values()
            if resultado["estado"] != "VALIDO"
        ]

        estados_ia = {
            resultado["estado"]
            for resultado in resultados_verificacion.values()
        }

        if not revision_ia_disponible:

            nota_gemini = (
                "REVISIÓN MANUAL REQUERIDA. La revisión automática no estuvo "
                "disponible; los cuatro documentos deben ser comprobados "
                "por un funcionario."
            )

        elif "NO_VALIDO" in estados_ia:

            nota_gemini = (
                "CON OBSERVACIONES. " + " ".join(observaciones_ia)
            )

        elif "REVISION_MANUAL" in estados_ia:

            nota_gemini = (
                "REVISIÓN MANUAL REQUERIDA. " + " ".join(observaciones_ia)
            )

        else:

            nota_gemini = (
                "POSIBLE PARA REGISTRAR. Gemini no detectó observaciones "
                "preliminares; la documentación todavía requiere revisión "
                "y validación humana."
            )

        # ==========================================================
        # ALMACENAMIENTO DEL REGISTRO ESTUDIANTIL
        # ==========================================================

        with transaction.atomic():

            usuario.genero = genero
            usuario.estado_civil = estado_civil
            usuario.save()

            contacto, _ = Contacto.objects.get_or_create(
                id_usuario=usuario
            )

            contacto.telefono_personal = telefono_principal
            contacto.telefono_suplete = telefono_secundario
            contacto.correo_electronico = correo_electronico1
            contacto.correo_alternativo = correo_electronico2
            contacto.save()

            Residencia.objects.create(
                condicion_residencia=condicion_residencia,
                municipio=municipio_residencia,
                parroquia=parroquia_residencia,
                direccion_residencia=direccion_domicilio,
                id_usuario=usuario
            )

            Nacimiento.objects.create(
                pais=pais_nacimiento,
                estado=estado_nacimiento,
                municipio=municipio_nacimiento,
                parroquia=parroquia_nacimiento,
                direccion_nacimiento=direccion_nacimiento,
                fecha_nacimiento=fecha_nacimiento,
                id_usuario=usuario
            )

            # ------------------------------------------------------
            # ASIGNACIÓN DEL NÚCLEO Y PNF
            # ------------------------------------------------------

            estudiante = Estudiante.objects.filter(
                usuario=usuario,
                nucleo__isnull=True,
                pnf__isnull=True,
            ).first()

            if estudiante:

                estudiante.nucleo = nucleo_seleccionado
                estudiante.pnf = pnf_seleccionado.id_pnf

                estudiante.save(
                    update_fields=["nucleo", "pnf"]
                )

            else:

                estudiante, _ = Estudiante.objects.get_or_create(
                    usuario=usuario,
                    nucleo=nucleo_seleccionado,
                    pnf=pnf_seleccionado.id_pnf,
                )

            # ------------------------------------------------------
            # CONTACTO AUXILIAR
            # ------------------------------------------------------

            ContactoAuxiliar.objects.create(
                nombres=nombres_auxiliar,
                apellidos=apellidos_auxiliar,
                cedula_identidad=cedula_auxiliar,
                telefono=telefono_auxiliar,
                parentesco=parestenco_auxiliar,
                id_usuario=usuario
            )

            # ------------------------------------------------------
            # INFORMACIÓN DE DISCAPACIDAD
            # ------------------------------------------------------

            Discapacidad.objects.create(
                codigo_carnet_discapacidad=carnet_dispacidad,
                nro_registro_medico=registro_medico,
                tipo_discapacidad=tipo_discapacidad,
                grado_discapacidad=grado_discapacidad,
                causa_discapacidad=causa_discapacidad,
                id_usuario=usuario
            )

            # ------------------------------------------------------
            # INFORMACIÓN DE SECUNDARIA
            # ------------------------------------------------------

            InformacionSecundaria.objects.create(
                tipo_institucion=tipos_secundaria,
                nombre_institucion=nombre_secundaria,
                fecha_grado=fecha_graduacion,
                codigo_sni_opsu=codigo_opsu,
                id_usuario=usuario
            )

            # ------------------------------------------------------
            # ESTATUS ACADÉMICO INICIAL
            # ------------------------------------------------------

            if not EstatusEstudiante.objects.filter(
                estudiante=estudiante
            ).exists():

                trayecto_inicial = TrayectoAcademico.objects.get(
                    nombre="Trayecto Inicial"
                )

                EstatusEstudiante.objects.create(
                    estudiante=estudiante,
                    estatus="Espera",
                    estado="Espera",
                    ingreso="Bachiller",
                    descripcion_ingreso="En espera de la aceptación.",
                    trayecto=trayecto_inicial,
                    fecha_ingreso=timezone.now().date()
                )

            # ------------------------------------------------------
            # CREACIÓN DEL EXPEDIENTE
            # ------------------------------------------------------

            expediente, _ = ExpedienteEstudiante.objects.get_or_create(
                usuario=usuario,
                defaults={
                    "estado": "PENDIENTE_REVISION",
                    "nota_gemini": nota_gemini,
                    "resultados_gemini": resultados_verificacion,
                    "fecha_revision_gemini": (
                        timezone.now()
                        if revision_ia_disponible
                        else None
                    ),
                },
            )

            expediente.estado = "PENDIENTE_REVISION"
            expediente.nota_gemini = nota_gemini
            expediente.resultados_gemini = resultados_verificacion

            expediente.fecha_revision_gemini = (
                timezone.now()
                if revision_ia_disponible
                else None
            )

            expediente.observacion_actual = ""
            expediente.aprobado_por = None
            expediente.fecha_aprobacion = None
            expediente.perfil_aprobacion = ""

            expediente.save()

            # ------------------------------------------------------
            # HISTORIAL DEL EXPEDIENTE
            # ------------------------------------------------------

            HistorialExpedienteEstudiante.objects.create(
                expediente=expediente,
                estado_anterior="",
                estado_nuevo="PENDIENTE_REVISION",
                accion="REGISTRO_RECIBIDO",
                observacion=(
                    "El estudiante completó su registro. "
                    "La revisión administrativa está pendiente."
                ),
                realizado_por=usuario,
                perfil="ESTUDIANTE",
            )

            # ------------------------------------------------------
            # ALMACENAMIENTO DE LOS DOCUMENTOS
            # ------------------------------------------------------

            for nombre, archivo in documentos.items():

                if archivo:

                    extension = Path(archivo.name).suffix.lower()
                    nuevo_nombre = f"{nombre}{extension}"

                    documento, _ = DocumentosEstudiante.objects.get_or_create(
                        id_usuario=usuario,
                        nombre_documento=nombre,
                    )

                    documento.expediente = expediente

                    documento.archivo.save(
                        nuevo_nombre,
                        archivo,
                        save=True,
                    )

            request.session["registro_completado"] = True

        # ==========================================================
        # GENERACIÓN DE LA PLANILLA DE INSCRIPCIÓN
        #
        # Se ejecuta después de confirmar la transacción
        # del registro estudiantil.
        # ==========================================================

        estado_planilla = "pendiente"
        mensaje_planilla = ""

        documento_planilla = None

        try:

            # ------------------------------------------------------
            # BUSCAR UNA PLANILLA EXISTENTE
            # ------------------------------------------------------

            documento_planilla = DocumentoInstitucional.objects.filter(
                tipo_documento="PLANILLA_INSCRIPCION",
                datos_documento__expediente_id=expediente.pk,
            ).first()

            # ------------------------------------------------------
            # GENERAR LA PLANILLA SI NO EXISTE
            # ------------------------------------------------------

            if documento_planilla is None:

                contenido_planilla = construir_contenido_planilla(
                    estudiante,
                    expediente,
                )

                documento_planilla = crear_documento_institucional(
                    request=request,
                    tipo_documento="PLANILLA_INSCRIPCION",
                    titulo="Constancia de recepción de inscripción",
                    contenido=contenido_planilla,
                    emitido_por=usuario,
                    datos_documento={
                        "estudiante_id": estudiante.pk,
                        "expediente_id": expediente.pk,
                        "nucleo_id": nucleo_seleccionado.pk,
                        "pnf_id": pnf_seleccionado.id_pnf.pk,
                    },
                )

            # ------------------------------------------------------
            # COMPROBAR QUE EL PDF EXISTA
            # ------------------------------------------------------

            if (
                documento_planilla is None
                or not documento_planilla.archivo_pdf
            ):

                raise RuntimeError(
                    "La planilla fue registrada, pero no tiene "
                    "un archivo PDF asociado."
                )

            estado_planilla = "generada"

        except Exception:

            logger.exception(
                "Error al generar la planilla de inscripción "
                "del expediente %s",
                expediente.pk,
            )

            estado_planilla = "pendiente"

            mensaje_planilla = (
                " Tu inscripción fue recibida correctamente, "
                "pero no fue posible completar la generación "
                "de la planilla institucional."
            )

        # ==========================================================
        # ENVÍO DE LA PLANILLA POR CORREO ELECTRÓNICO
        # ==========================================================

        if estado_planilla == "generada":

            try:

                enviar_planilla_inscripcion(
                    contacto=contacto,
                    documento=documento_planilla,
                    usuario=usuario,
                )

                estado_planilla = "enviada"

            except Exception:

                logger.exception(
                    "Error al enviar la planilla de inscripción "
                    "del expediente %s",
                    expediente.pk,
                )

                # El PDF se conserva. Solo queda pendiente
                # completar el envío del correo electrónico.

                estado_planilla = "generada"

                mensaje_planilla = (
                    " Tu inscripción fue recibida y la planilla "
                    "fue generada correctamente, pero no fue posible "
                    "enviarla por correo electrónico."
                )

        # ==========================================================
        # RESPUESTA FINAL DEL REGISTRO ESTUDIANTIL
        # ==========================================================

        return JsonResponse({
            "estado": "exito",
            "title": "Registro recibido",
            "descripcion": (
                "Tu registro estudiantil fue recibido exitosamente. "
                "El expediente se encuentra pendiente de revisión "
                "administrativa."
                + mensaje_planilla
            ),
            "icon": "success",
            "estado_expediente": expediente.estado,
            "estado_planilla": estado_planilla,
            "nota_gemini": nota_gemini,
            "verificacion_documentos": resultados_verificacion,
            "url": reverse("panel_usuario"),
        })

    # ==============================================================
    # CARGA DEL FORMULARIO
    # ==============================================================

    return render(
        request,
        "Sesion/actualizar/completar_registro.html",
        {
            "sin_estilos": True,
            "es_completar_registro": True,
        }
    )