from django.shortcuts import render
from django.http import JsonResponse
from django.utils import timezone
from django.db import transaction

from inicio_sesion.models import AulaAcademica, DirectorGeneral, CoordinadorPNF, Bitacora, Pnf, SeccionAcademica

# aulas_registrados
def aulas_reg(request):

    cedula = request.session.get("cedula_usuario")

    # BUSCAR NÚCLEO DEL DIRECTOR
    director = (
        DirectorGeneral.objects
        .filter(usuario__cedula_identidad=cedula)
        .select_related("nucleo")
        .first()
    )

    if director:
        nucleo = director.nucleo

    else:
        # BUSCAR NÚCLEO DEL COORDINADOR PNF
        coordinador = (
            CoordinadorPNF.objects
            .filter(usuario__cedula_identidad=cedula)
            .select_related("nucleo")
            .first()
        )

        if coordinador:
            nucleo = coordinador.nucleo

        else:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Sin núcleo asignado",
                "descripcion": (
                    "El usuario no tiene un núcleo académico asignado."
                )
            })

    # OBTENER AULAS DEL NÚCLEO
    aulas = (
        AulaAcademica.objects
        .filter(id_nucleo=nucleo)
        .values(
            "id_aula",
            "nombre_aula",
            "Nota",
            "piso_edificio",
            "tipo_aula",
            "id_seccion__nombre",
            "id_pnf__pnf",
        )
    )

    return JsonResponse({
        "estado": "exito",
        "aulas": list(aulas)
    })

# datos_aula
def datos_aula(request):
    if request.method == "POST":
        id_aula = request.POST.get("id_aula")

        director = DirectorGeneral.objects.get(usuario__cedula_identidad=request.session.get("cedula_usuario"))

        aula = AulaAcademica.objects.select_related("id_nucleo").get(
            id_aula=id_aula,
            id_nucleo=director.nucleo
        )

        return JsonResponse({
            "id_aula": aula.id_aula,
            "nombre_aula": aula.nombre_aula,
            "piso_edificio": aula.piso_edificio,
            "Nota": aula.Nota,
            "tipo_aula": aula.tipo_aula,
            "id_seccion": aula.id_seccion.id_seccion,
            "seccion": aula.id_seccion.nombre,
            "id_pnf": aula.id_pnf.id_pnf,
            "pnf": aula.id_pnf.pnf,
        })

def val_aula(request):
    if request.method == "POST":
        aula = request.POST.get("aula")

        existe = AulaAcademica.objects.filter(nombre_aula__iexact=aula).exists()
        if existe:
            return JsonResponse({ "existe": True })

        return JsonResponse({ "existe": False })

# actualizar_aula_academica
def act_aula_acad(request):

    if request.method == "POST":

        id_aula = request.POST.get("aula_seleccionar")
        nombre_aula = request.POST.get("actualizar_aula")
        descripcion_aula = request.POST.get("actualizar_nota")
        piso_aula = request.POST.get("actualizar_piso")
        tipo_aula = request.POST.get("actualizar_tipos")
        seccion_academica = request.POST.get("actualizar_seccion")
        pnf = request.POST.get("actualizar_pnf")

        print(seccion_academica)
        print(pnf)

        # VALIDAR CAMPOS VACÍOS
        controles = [
            (
                nombre_aula,
                "Aula Académica",
                "Por favor, debe ingresar el nombre/número del aula."
            ),
            (
                descripcion_aula,
                "Descripción del Aula",
                "Por favor, debe ingresar la nota/descripción del aula."
            ),
            (
                piso_aula,
                "Piso del Aula",
                "Por favor, debe ingresar el piso del aula."
            ),
            (
                tipo_aula,
                "Tipo Aula Académica",
                "Por favor, debe seleccionar el tipo de aula."
            ),
            (
                seccion_academica,
                "Sección Académica",
                "Por favor, debe seleccionar la sección del aula."
            ),
            (
                pnf,
                "P.N.F",
                "Por favor, debe seleccionar el P.N.F."
            ),
        ]

        for value, field_name, error_message in controles:
            if not value or not value.strip():
                return JsonResponse({
                    "estado": "fallo",
                    "icon": "warning",
                    "title": field_name,
                    "descripcion": error_message
                })

        # BUSCAR AULA
        try:
            aula = AulaAcademica.objects.get(id_aula=id_aula)
        except AulaAcademica.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Error",
                "descripcion": (
                    "El aula no se encuentra registrada."
                )
            })

        # BUSCAR SECCIÓN
        try:
            seccion_obj = SeccionAcademica.objects.get(id_seccion=seccion_academica)
        except SeccionAcademica.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Sección no encontrada",
                "descripcion": (
                    "La sección académica seleccionada "
                    "no se encuentra registrada."
                )
            })
        
        # BUSCAR PNF
        try:
            pnf_obj = Pnf.objects.get(id_pnf=pnf)
        except Pnf.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "PNF no encontrado",
                "descripcion": (
                    "El PNF seleccionado no se encuentra registrado."
                )
            })

        # ACTUALIZAR
        try:
            with transaction.atomic():
                aula.nombre_aula = nombre_aula.strip()
                aula.Nota = descripcion_aula.strip()
                aula.piso_edificio = piso_aula.strip()
                aula.tipo_aula = tipo_aula.strip()
                aula.id_seccion = seccion_obj
                aula.id_pnf = pnf_obj

                aula.save()

                # BITÁCORA
                Bitacora.objects.create(
                    nombre_usuario=request.session.get("usuario_nombre"),
                    fecha_hora=timezone.now(),
                    accion=(
                        f"Se actualizó el aula académica "
                        f"'{nombre_aula}' como {tipo_aula}."
                    )
                )

            return JsonResponse({
                "estado": "exito",
                "icon": "success",
                "title": "Éxito",
                "descripcion": (
                    "Se actualizaron los datos del aula "
                    "académica exitosamente."
                )
            })

        except Exception as error:
            print("ERROR:", error)
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Error",
                "descripcion": (
                    "Ocurrió un error al momento de "
                    "actualizar el aula."
                )
            })

    return render(request, "Roles/Director_General/aula/visualizar_aulas.html")

# modulo_aula_academica
def reg_aula(request):
    if request.method == "POST":
        nombre_aula = request.POST.get("nombre_aula")
        observacion = request.POST.get("observacion_aula")
        piso = request.POST.get("piso_edificio")
        tipos_aulas = request.POST.get("tipos_aulas")
        pnf = request.POST.get("pnfs_imparte")
        seccion = request.POST.get("secciones_registradas")

        controles = [
            (nombre_aula, "Nombre/Número del Aula", "Por favor, debe ingresar el nombre del aula."),
            (observacion, "Observación", "Por favor, debe ingresar la observación del aula."),
            (piso, "Piso de la Ubicación del Aula", "Por favor, debe ingresar el piso donde se encuentra el aula."),
            (tipos_aulas, "Tipos de Aulas", "Por favor, debe seleccionar el tipo de aula."),
            (pnf, "P.N.F", "Por favor, debe seleccionar el P.N.F."),
            (seccion, "Sección Académica", "Por favor, debe seleccionar la sección académico.")
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
            with transaction.atomic():
                director = DirectorGeneral.objects.get(usuario__cedula_identidad=request.session.get("cedula_usuario"))
                
                pnf_seleccionado = Pnf.objects.get(id_pnf=pnf)
                seccion_seleccionado = SeccionAcademica.objects.get(id_seccion=seccion)
        
                AulaAcademica.objects.create(
                    nombre_aula=nombre_aula,
                    Nota=observacion,
                    piso_edificio=piso,
                    tipo_aula=tipos_aulas,
                    id_seccion=seccion_seleccionado,
                    id_pnf=pnf_seleccionado,
                    id_nucleo=director.nucleo
                )
        
                Bitacora.objects.create(
                    nombre_usuario=request.session.get("usuario_nombre"),
                    fecha_hora=timezone.now(),
                    accion=f"Se registro la aula {nombre_aula} del piso {piso}."
                )
        
                return JsonResponse({
                    "estado": "exito",
                    "icon": "success",
                    "title": "Exito",
                    "descripcion": "Se registró exitosamente el aula académica."
                })
        except Exception as e:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Error",
                "descripcion": "Ocurrio un error al momento de regsitrar el aula académica."
            })

    return render(request, "Roles/Director_General/aula/registrar_aula.html")


