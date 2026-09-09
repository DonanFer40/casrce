from django.shortcuts import render
from django.http import JsonResponse
from django.utils import timezone
from django.conf import settings

from inicio_sesion.models import CalendarioAcademico, Usuario, Contacto, Nacimiento, Residencia, AulaEstudiante, Bitacora, CoordinadorPNF, EstatusEstudiante, DocumentosEstudiante, ContactoAuxiliar, Discapacidad, InformacionSecundaria, Estudiante, AulaAcademica

def obt_nucleos_asignados(request):
    cedula = request.session.get("cedula_usuario")

    nucleos = CoordinadorPNF.objects.filter(
        usuario__cedula_identidad=cedula,
        activo=True
    ).select_related(
        "nucleo"
    ).values(
        "nucleo__id_nucleo",
        "nucleo__municipio",
        "nucleo__direccion"
    ).distinct()

    resultado = []
    for nucleo in nucleos:
        resultado.append({
            "id_nucleo": nucleo["nucleo__id_nucleo"],
            "municipio": nucleo["nucleo__municipio"],
            "direccion": nucleo["nucleo__direccion"]
        })

    return JsonResponse({
        "estado": "exito",
        "nucleos": resultado
    })

def obt_pnfs_asignado(request):
    if request.method == "POST":
        cedula = request.session.get("cedula_usuario")
        nucleo = request.POST.get("nucleo_asignado", "").strip()

        pnfs = CoordinadorPNF.objects.filter(
            usuario__cedula_identidad=cedula,
            nucleo_id=nucleo,
            activo=True
        ).select_related(
            "pnf"
        ).values(
            "pnf__id_pnf",
            "pnf__pnf",
            "pnf__codigo",
            "pnf__periodo_academico"
        ).distinct()

        resultado = []

        for pnf in pnfs:
            resultado.append({
                "id_pnf": pnf["pnf__id_pnf"],
                "pnf": pnf["pnf__pnf"],
                "codigo": pnf["pnf__codigo"],
                "periodo_academico": pnf["pnf__periodo_academico"]
            })

        return JsonResponse({
            "estado": "exito",
            "pnfs": resultado
        })

def obt_pre_inscrt(request):
    if request.method == "POST":
        cedula = request.session.get("cedula_usuario")

        nucleo = request.POST.get("nucleo_asignado", "").strip()
        pnf = request.POST.get("pnf_asignado", "").strip()

        # OBTENER COORDINADOR
        coordinador = CoordinadorPNF.objects.filter(
            usuario__cedula_identidad=cedula,
            nucleo_id=nucleo,
            pnf_id=pnf,
            activo=True
        ).select_related(
            "nucleo",
            "pnf"
        ).first()

        if not coordinador:
            return JsonResponse({
                "estado": "error",
                "titulo": "Error",
                "icon": "error",
                "descripcion": "El núcleo y PNF seleccionados no están asignados al coordinador."
            })

        # DETERMINAR TIPO DE INSCRIPCIÓN
        periodo_academico = coordinador.pnf.periodo_academico

        if periodo_academico == "Trimestre":
            tipo_inscripcion = "INSCRIPCION_TRIMESTRE"

        elif periodo_academico == "Semestre":
            tipo_inscripcion = "INSCRIPCION_SEMESTRE"

        else:
            return JsonResponse({
                "estado": "error",
                "titulo": "Período académico no configurado",
                "icon": "warning",
                "descripcion": "El PNF seleccionado no tiene configurado un período académico válido."
            })

        # VALIDAR CALENDARIO ACADÉMICO
        fecha_actual = timezone.now().date()

        calendario_inscripcion = CalendarioAcademico.objects.filter(
            activo=True,
            tipo=tipo_inscripcion,
            fecha_inicio__lte=fecha_actual,
            fecha_final__gte=fecha_actual
        ).first()

        if not calendario_inscripcion:
            return JsonResponse({
                "estado": "error",
                "titulo": "Inscripción no disponible",
                "icon": "warning",
                "descripcion": (
                    f"Actualmente no se encuentra dentro de las fechas de inscripciones "
                    f"establecidas para realizar la inscripción de los PNF "
                    f"de modalidad {periodo_academico.lower()}."
                )
            })

        # OBTENER ESTUDIANTES
        estudiantes = Estudiante.objects.filter(
            nucleo_id=nucleo,
            pnf_id=pnf,
            estatus__estado="Espera",
            estatus__estatus="Espera"
        ).select_related(
            "usuario"
        ).distinct()

        resultado = []

        for estudiante in estudiantes:

            estatus = estudiante.estatus.filter(
                estado="Espera",
                estatus="Espera"
            ).select_related(
                "trayecto"
            ).order_by(
                "-fecha_ingreso"
            ).first()

            if estatus:

                resultado.append({
                    "id_estudiante": estudiante.id_estudiante,
                    "cedula_identidad": estudiante.usuario.cedula_identidad,
                    "nombres": estudiante.usuario.nombres,
                    "apellidos": estudiante.usuario.apellidos,
                    "genero": estudiante.usuario.genero,

                    "estatus": estatus.estatus,
                    "estado": estatus.estado,
                    "ingreso": estatus.ingreso,
                    "descripcion_ingreso": estatus.descripcion_ingreso,
                    "trayecto": estatus.trayecto.nombre,
                    "fecha_ingreso": estatus.fecha_ingreso.strftime("%Y-%m-%d"),
                })

        # OBTENER AULAS
        aulas = AulaAcademica.objects.filter(
            id_nucleo_id=nucleo,
            id_pnf_id=pnf
        ).values(
            "id_aula",
            "nombre_aula",
            "tipo_aula",
            "piso_edificio",
            "id_seccion_id"
        ).order_by(
            "nombre_aula"
        )

        return JsonResponse({
            "estado": "exito",
            "estudiantes": resultado,
            "aulas": list(aulas)
        })

def obt_data_est(request):
    if request.method == "POST":
        nucleo = request.POST.get("nucleo_asignado", "").strip()
        pnf = request.POST.get("pnf_asignado", "").strip()

        nucleo = int(nucleo)
        pnf = int(pnf)

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

    if request.method == "POST":

        cedula = request.POST.get("cedula")
        id_aula = request.POST.get("aula")
        accion = request.POST.get("accion")
        nucleo = request.POST.get("nucleo_asignado")
        pnf = request.POST.get("pnf_asignado")

        # ==========================================
        # OBTENER COORDINADOR
        # ==========================================

        coordinador = CoordinadorPNF.objects.select_related(
            "nucleo",
            "pnf"
        ).filter(
            usuario__cedula_identidad=request.session.get("cedula_usuario"),
            nucleo_id=nucleo,
            pnf_id=pnf,
            activo=True
        ).first()

        if not coordinador:

            return JsonResponse({
                "titulo": "¡Advertencia!",
                "estado": "fallo",
                "icon": "warning",
                "descripcion": "El núcleo y PNF seleccionados no están asignados al coordinador."
            })

        # ==========================================
        # BUSCAR USUARIO
        # ==========================================

        usuario = Usuario.objects.filter(
            cedula_identidad=cedula
        ).first()

        if not usuario:

            return JsonResponse({
                "titulo": "¡Advertencia!",
                "estado": "fallo",
                "icon": "warning",
                "descripcion": "El estudiante no existe."
            })

        # ==========================================
        # BUSCAR ESTUDIANTE
        # ==========================================

        estudiante = Estudiante.objects.filter(
            usuario=usuario,
            nucleo_id=nucleo,
            pnf_id=pnf
        ).first()

        if not estudiante:

            return JsonResponse({
                "titulo": "¡Advertencia!",
                "estado": "fallo",
                "icon": "warning",
                "descripcion": "El estudiante no pertenece al PNF o núcleo del coordinador."
            })

        # ==========================================
        # BUSCAR ESTATUS
        # ESPERA O RECHAZADO
        # ==========================================

        estatus_estudiante = EstatusEstudiante.objects.filter(
            estudiante=estudiante,
            estatus="Espera",
            estado__in=[
                "Espera",
                "Rechazado"
            ]
        ).order_by(
            "-fecha_ingreso"
        ).first()

        if not estatus_estudiante:

            return JsonResponse({
                "titulo": "¡Advertencia!",
                "estado": "fallo",
                "icon": "warning",
                "descripcion": "No se encontró una preinscripción pendiente o rechazada para el estudiante."
            })

        # ==========================================
        # RECHAZAR
        # ==========================================

        if accion == "rechazado":

            estatus_estudiante.estado = "Rechazado"

            estatus_estudiante.save(
                update_fields=["estado"]
            )

            return JsonResponse({
                "titulo": "¡Éxito!",
                "estado": "exito",
                "icon": "success",
                "descripcion": "La preinscripción fue rechazada."
            })

        # ==========================================
        # VALIDAR ACCIÓN
        # ==========================================

        if accion != "aceptado":

            return JsonResponse({
                "titulo": "¡Advertencia!",
                "estado": "fallo",
                "icon": "warning",
                "descripcion": "La acción solicitada no es válida."
            })

        # ==========================================
        # VALIDAR AULA
        # ==========================================

        if not id_aula:

            return JsonResponse({
                "titulo": "¡Advertencia!",
                "estado": "fallo",
                "icon": "warning",
                "descripcion": "Debe seleccionar el aula."
            })

        # ==========================================
        # VALIDAR CALENDARIO ACADÉMICO
        # ==========================================

        periodo_academico = coordinador.pnf.periodo_academico

        if periodo_academico == "Trimestre":

            tipo_inscripcion = "INSCRIPCION_TRIMESTRE"

        elif periodo_academico == "Semestre":

            tipo_inscripcion = "INSCRIPCION_SEMESTRE"

        else:

            return JsonResponse({
                "titulo": "¡Advertencia!",
                "estado": "fallo",
                "icon": "warning",
                "descripcion": "El PNF no tiene configurado un período académico válido."
            })

        fecha_actual = timezone.now().date()

        calendario_inscripcion = CalendarioAcademico.objects.filter(
            activo=True,
            tipo=tipo_inscripcion,
            fecha_inicio__lte=fecha_actual,
            fecha_final__gte=fecha_actual
        ).first()

        if not calendario_inscripcion:

            return JsonResponse({
                "titulo": "¡Inscripción no disponible!",
                "estado": "fallo",
                "icon": "warning",
                "descripcion": (
                    f"Actualmente no existe un período de inscripción "
                    f"vigente para los PNF de modalidad "
                    f"{periodo_academico.lower()}."
                )
            })

        # ==========================================
        # BUSCAR AULA
        # ==========================================

        aula = AulaAcademica.objects.filter(
            id_aula=id_aula,
            id_nucleo_id=nucleo,
            id_pnf_id=pnf
        ).first()

        if not aula:

            return JsonResponse({
                "titulo": "¡Advertencia!",
                "estado": "fallo",
                "icon": "warning",
                "descripcion": (
                    "El aula seleccionada no existe o no pertenece "
                    "al núcleo y PNF seleccionados."
                )
            })

        # ==========================================
        # VALIDAR AULA ACTIVA
        # ==========================================

        if AulaEstudiante.objects.filter(
            estatus=estatus_estudiante,
            estado="Curso",
            fecha_final__isnull=True
        ).exists():

            return JsonResponse({
                "titulo": "¡Advertencia!",
                "estado": "fallo",
                "icon": "warning",
                "descripcion": "El estudiante ya posee un aula activa."
            })

        # ==========================================
        # REGISTRAR AULA
        # ==========================================

        AulaEstudiante.objects.create(
            aula=aula,
            estatus=estatus_estudiante,
            fecha_inicio=fecha_actual,
            estado="Curso"
        )

        # ==========================================
        # ACTUALIZAR ESTATUS
        # ==========================================

        estatus_estudiante.estatus = "Inscrito(a)"
        estatus_estudiante.estado = "Activo"

        estatus_estudiante.save(
            update_fields=[
                "estatus",
                "estado"
            ]
        )

        return JsonResponse({
            "titulo": "¡Éxito!",
            "estado": "exito",
            "icon": "success",
            "descripcion": "El estudiante fue inscrito correctamente."
        })

    return render(
        request,
        "Coordinador_PNF/inscripcion/inscripcion_estudiante.html"
    )

def rech_inscr_est(request):
    if request.method == "POST":
        cedula = request.session.get("cedula_usuario")
        nucleo = request.POST.get("nucleo_asignado", "").strip()
        pnf = request.POST.get("pnf_asignado", "").strip()

        # OBTENER COORDINADOR
        coordinador = CoordinadorPNF.objects.filter(
            usuario__cedula_identidad=cedula,
            nucleo_id=nucleo,
            pnf_id=pnf,
            activo=True
        ).select_related(
            "nucleo",
            "pnf"
        ).first()

        if not coordinador:

            return JsonResponse({
                "estado": "error",
                "titulo": "Error",
                "icon": "error",
                "descripcion": (
                    "El núcleo y PNF seleccionados "
                    "no están asignados al coordinador."
                )
            })

        # DETERMINAR TIPO DE INSCRIPCIÓN
        periodo_academico = coordinador.pnf.periodo_academico
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
        fecha_actual = timezone.now().date()

        calendario_inscripcion = CalendarioAcademico.objects.filter(
            activo=True,
            tipo=tipo_inscripcion,
            fecha_inicio__lte=fecha_actual,
            fecha_final__gte=fecha_actual
        ).first()

        if not calendario_inscripcion:
            return JsonResponse({
                "estado": "error",
                "titulo": "Inscripción no disponible",
                "icon": "warning",
                "descripcion": (
                    f"Actualmente no se encuentra dentro del período "
                    f"establecido para realizar la inscripción de los PNF "
                    f"de modalidad {periodo_academico.lower()}."
                )
            })

        # OBTENER ESTUDIANTES RECHAZADOS
        estudiantes = Estudiante.objects.filter(
            nucleo_id=nucleo,
            pnf_id=pnf,
            estatus__estado="Rechazado"
        ).select_related(
            "usuario"
        ).distinct()

        resultado = []

        for estudiante in estudiantes:

            # Obtener el último estatus rechazado
            estatus = estudiante.estatus.filter(
                estado="Rechazado"
            ).select_related(
                "trayecto"
            ).order_by(
                "-fecha_ingreso",
                "-id_estatus_estudiante"
            ).first()

            if not estatus:
                continue

            resultado.append({
                "id_estudiante": estudiante.id_estudiante,

                "cedula_identidad":
                    estudiante.usuario.cedula_identidad,

                "nombres":
                    estudiante.usuario.nombres,

                "apellidos":
                    estudiante.usuario.apellidos,

                "genero":
                    estudiante.usuario.genero,

                "estatus":
                    estatus.estatus,

                "estado":
                    estatus.estado,

                "ingreso":
                    estatus.ingreso,

                "descripcion_ingreso":
                    estatus.descripcion_ingreso,

                "trayecto":
                    estatus.trayecto.nombre,

                "fecha_ingreso":
                    estatus.fecha_ingreso.strftime("%Y-%m-%d")
            })

        # ==========================================
        # OBTENER AULAS DEL NÚCLEO Y PNF
        # ==========================================

        aulas = AulaAcademica.objects.filter(
            id_nucleo_id=nucleo,
            id_pnf_id=pnf
        ).order_by(
            "nombre_aula"
        ).values(
            "id_aula",
            "nombre_aula",
            "tipo_aula",
            "piso_edificio"
        )

        # Convertir QuerySet a lista antes de enviarlo
        aulas = list(aulas)

        # ==========================================
        # RESPUESTA
        # ==========================================

        return JsonResponse({
            "estado": "exito",
            "estudiantes": resultado,
            "aulas": aulas
        })

    return render(
        request,
        "Coordinador_PNF/inscripcion/inscripcion_rechazado.html"
    )
