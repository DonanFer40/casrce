import logging

from django.db import IntegrityError
from django.shortcuts import render
from django.http import JsonResponse
from django.utils import timezone
from django.db import transaction

from inicio_sesion.models import (
    AulaAcademica,
    Bitacora,
    DirectorGeneral,
    PNFNucleo,
    Pnf,
    SeccionAcademica,
)


logger = logging.getLogger(__name__)


def _director_actual(request):
    return DirectorGeneral.objects.filter(
        usuario__cedula_identidad=request.session.get("cedula_usuario")
    ).select_related("nucleo").first()

# aulas_registrados
def aulas_reg(request):
    if request.method != "GET":
        return JsonResponse({"estado": "fallo"}, status=405)
    director = _director_actual(request)
    if director is None:
        return JsonResponse({
            "estado": "fallo",
            "icon": "error",
            "title": "Sin núcleo asignado",
            "descripcion": "No hay un núcleo de Dirección asignado.",
        }, status=403)

    # OBTENER AULAS DEL NÚCLEO
    aulas = list(
        AulaAcademica.objects
        .filter(id_nucleo=director.nucleo)
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

    # CAPITALIZAR TIPO DE AULA
    for aula in aulas:
        aula["tipo_aula"] = aula["tipo_aula"].capitalize() if aula["tipo_aula"] else ""

    return JsonResponse({
        "estado": "exito",
        "aulas": aulas
    })


def visualizar_aula(request):
    if request.method != "GET":
        return JsonResponse({"estado": "fallo"}, status=405)
    director = _director_actual(request)
    if director is None:
        return JsonResponse({"estado": "fallo"}, status=403)
    return render(request, "Roles/Director_General/aula/registrar_aula.html")


# datos_aula
def datos_aula(request):
    if request.method == "POST":
        director = _director_actual(request)
        if director is None:
            return JsonResponse({"estado": "fallo"}, status=403)
        id_aula = request.POST.get("id_aula")
        aula = AulaAcademica.objects.select_related(
            "id_seccion",
            "id_pnf",
        ).filter(
            id_aula=id_aula,
            id_nucleo=director.nucleo
        ).first()
        if aula is None:
            return JsonResponse({
                "estado": "fallo",
                "descripcion": "El aula no existe o no pertenece a tu núcleo.",
            }, status=404)

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
    return JsonResponse({"estado": "fallo"}, status=405)

def val_aula(request):
    if request.method == "POST":
        director = _director_actual(request)
        if director is None:
            return JsonResponse({"existe": False}, status=403)
        aula = (request.POST.get("aula") or "").strip()
        if not aula:
            return JsonResponse({"existe": False}, status=400)

        existe = AulaAcademica.objects.filter(
            id_nucleo=director.nucleo,
            nombre_aula__iexact=aula,
        ).exists()
        if existe:
            return JsonResponse({"existe": True})

        return JsonResponse({"existe": False})
    return JsonResponse({"existe": False}, status=405)

# actualizar_aula_academica
def act_aula_acad(request):

    if request.method == "POST":
        director = _director_actual(request)
        if director is None:
            return JsonResponse({"estado": "fallo"}, status=403)

        id_aula = request.POST.get("aula_seleccionar")
        nombre_aula = (request.POST.get("actualizar_aula") or "").strip()
        descripcion_aula = (request.POST.get("actualizar_nota") or "").strip()
        piso_aula = (request.POST.get("actualizar_piso") or "").strip()
        tipo_aula = (request.POST.get("actualizar_tipos") or "").strip()
        seccion_academica = request.POST.get("actualizar_seccion")
        pnf = request.POST.get("actualizar_pnf")

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
            (seccion_academica, "Sección Académica", "Por favor, debe seleccionar la sección del aula."),
            (pnf, "P.N.F", "Por favor, debe seleccionar el P.N.F."),
        ]

        for value, field_name, error_message in controles:
            if not value or (isinstance(value, str) and not value.strip()):
                return JsonResponse({
                    "estado": "fallo",
                    "icon": "warning",
                    "title": field_name,
                    "descripcion": error_message
                })

        # BUSCAR AULA
        aula = AulaAcademica.objects.filter(
            id_aula=id_aula,
            id_nucleo=director.nucleo,
        ).first()
        if aula is None:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Error",
                "descripcion": (
                    "El aula no se encuentra registrada."
                )
            })

        # BUSCAR SECCIÓN
        seccion_obj = SeccionAcademica.objects.filter(
            id_seccion=seccion_academica
        ).first()
        if seccion_obj is None:
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
        pnf_obj = Pnf.objects.filter(id_pnf=pnf).first()
        if pnf_obj is None:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "PNF no encontrado",
                "descripcion": (
                    "El PNF seleccionado no se encuentra registrado."
                )
            })

        if not PNFNucleo.objects.filter(
            id_pnf=pnf_obj,
            id_nucleo=director.nucleo,
        ).exists():
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "PNF no disponible",
                "descripcion": "El PNF seleccionado no se imparte en este núcleo.",
            }, status=400)

        if AulaAcademica.objects.filter(
            id_nucleo=director.nucleo,
            nombre_aula__iexact=nombre_aula,
        ).exclude(pk=aula.pk).exists():
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Aula duplicada",
                "descripcion": "Ya existe un aula con ese nombre en este núcleo.",
            }, status=409)

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

        except IntegrityError:
            logger.exception("No se pudo actualizar el aula %s.", id_aula)
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Error",
                "descripcion": (
                    "No se pudo guardar el aula por un conflicto de datos."
                )
            }, status=409)

    if request.method == "GET":
        if _director_actual(request) is None:
            return JsonResponse({"estado": "fallo"}, status=403)
        return render(request, "Roles/Director_General/aula/registrar_aula.html")
    return JsonResponse({"estado": "fallo"}, status=405)

# modulo_aula_academica
def reg_aula(request):
    if request.method == "POST":
        nombre_aula = (request.POST.get("nombre_aula") or "").strip()
        observacion = (request.POST.get("observacion_aula") or "").strip()
        piso = (request.POST.get("piso_edificio") or "").strip()
        tipos_aulas = (request.POST.get("tipos_aulas") or "").strip()
        pnf = request.POST.get("pnfs_imparte")
        seccion = request.POST.get("secciones_registradas")
        director = _director_actual(request)
        if director is None:
            return JsonResponse({"estado": "fallo"}, status=403)

        controles = [
            (nombre_aula, "Nombre/Número del Aula", "Por favor, debe ingresar el nombre del aula."),
            (observacion, "Observación", "Por favor, debe ingresar la observación del aula."),
            (piso, "Piso de la Ubicación del Aula", "Por favor, debe ingresar el piso donde se encuentra el aula."),
            (tipos_aulas, "Tipos de Aulas", "Por favor, debe seleccionar el tipo de aula."),
            (pnf, "P.N.F", "Por favor, debe seleccionar el P.N.F."),
            (seccion, "Sección Académica", "Por favor, debe seleccionar la sección académico.")
        ]
        for value, field_name, error_message in controles:
            if not value or (isinstance(value, str) and not value.strip()):
                return JsonResponse({
                    "estado": "fallo",
                    "icon": "warning",
                    "title": field_name,
                    "descripcion": error_message
                }, status=400)

        pnf_seleccionado = Pnf.objects.filter(id_pnf=pnf).first()
        seccion_seleccionada = SeccionAcademica.objects.filter(
            id_seccion=seccion
        ).first()
        if pnf_seleccionado is None or seccion_seleccionada is None:
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Datos no válidos",
                "descripcion": "Selecciona un PNF y una sección registrados.",
            }, status=400)
        if not PNFNucleo.objects.filter(
            id_pnf=pnf_seleccionado,
            id_nucleo=director.nucleo,
        ).exists():
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "PNF no disponible",
                "descripcion": "El PNF seleccionado no se imparte en este núcleo.",
            }, status=400)
        if AulaAcademica.objects.filter(
            id_nucleo=director.nucleo,
            nombre_aula__iexact=nombre_aula,
        ).exists():
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Aula duplicada",
                "descripcion": "Ya existe un aula con ese nombre en este núcleo.",
            }, status=409)

        try:
            with transaction.atomic():
                AulaAcademica.objects.create(
                    nombre_aula=nombre_aula,
                    Nota=observacion,
                    piso_edificio=piso,
                    tipo_aula=tipos_aulas,
                    id_seccion=seccion_seleccionada,
                    id_pnf=pnf_seleccionado,
                    id_nucleo=director.nucleo
                )
        
                Bitacora.objects.create(
                    nombre_usuario=request.session.get("usuario_nombre"),
                    fecha_hora=timezone.now(),
                    accion=f"Se registró el aula {nombre_aula} del piso {piso}."
                )
        
                return JsonResponse({
                    "estado": "exito",
                    "icon": "success",
                    "title": "Exito",
                    "descripcion": "Se registró exitosamente el aula académica."
                })
        except IntegrityError:
            logger.exception("No se pudo registrar el aula %s.", nombre_aula)
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Error",
                "descripcion": "No se pudo guardar el aula por un conflicto de datos."
            }, status=409)

    if request.method == "GET":
        if _director_actual(request) is None:
            return JsonResponse({"estado": "fallo"}, status=403)
        return render(request, "Roles/Director_General/aula/registrar_aula.html")
    return JsonResponse({"estado": "fallo"}, status=405)
