from django.shortcuts import render
from django.http import JsonResponse
from django.db import transaction
from django.utils import timezone

from inicio_sesion.models import SeccionAcademica, Bitacora


ALFABETO_SECCIONES = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def obtener_siguiente_nombre_seccion():
    ocupadas = {
        nombre.strip().upper()
        for nombre in SeccionAcademica.objects.values_list(
            "nombre",
            flat=True,
        )
        if nombre
    }
    return next(
        (letra for letra in ALFABETO_SECCIONES if letra not in ocupadas),
        None,
    )


# secciones_registradas
def sec_reg(request):
    secciones = list(
        SeccionAcademica.objects.values(
            "id_seccion",
            "nombre",
            "turno"
        )
    )

    return JsonResponse({
        "estado": "exito",
        "secciones": secciones,
        "siguiente": obtener_siguiente_nombre_seccion(),
    })

# validar el nombre de la sección
def val_sec(request):
    if request.method == "POST":
        seccion = request.POST.get("seccion")
        id_seccion = request.POST.get("id_seccion")

        consulta = SeccionAcademica.objects.filter(nombre=seccion)

        if id_seccion:
            consulta = consulta.exclude(id_seccion=id_seccion)

        existe = consulta.exists()
        
        return JsonResponse({ "existe": existe })

# datos_seccion
def datos_sec(request):
    if request.method == "POST":
        id_seccion = request.POST.get("seccion")

        seccion = SeccionAcademica.objects.filter(
            id_seccion=id_seccion
        ).first()
        if seccion is None:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Error",
                "mensaje": "La sección académica no se encuentra registrada."
            })

        ocupadas = list(
            SeccionAcademica.objects.order_by("nombre").values_list(
                "nombre",
                flat=True,
            )
        )
        return JsonResponse({
            "estado": "exito",
            "seccion": {
                "id_seccion": seccion.id_seccion,
                "seccion": seccion.nombre,
                "turno": seccion.turno
            },
            "ocupadas": ocupadas,
            "siguiente": obtener_siguiente_nombre_seccion(),
        })

# guardar_actualizacion_seccion
def guardar_act_sec(request):
    if request.method == "POST":
        id_seccion = request.POST.get("seccion")
        turno = request.POST.get("actualizar_turno")

        controles = [
            (turno, "Turno Académico", "Por favor, debe seleccionar el turno académico.")
        ]

        for value, field_name, error_message in controles:
            if not value:
                return JsonResponse({
                    "estado": "fallo",
                    "icon": "warning",
                    "title": field_name,
                    "descripcion": error_message
                })
        
            with transaction.atomic():
                try:
                    seccion = SeccionAcademica.objects.get(id_seccion=id_seccion)
                except SeccionAcademica.DoesNotExist:
                    return JsonResponse({
                        "estado": "fallo",
                        "icon": "error",
                        "title": "Error",
                        "descripcion": "No se encuentra registrada la sección."
                    })

                nuevo_seccion = obtener_siguiente_nombre_seccion()
                if nuevo_seccion is None:
                    return JsonResponse({
                        "estado": "fallo",
                        "icon": "warning",
                        "title": "Sin secciones disponibles",
                        "descripcion": (
                            "Las letras de la A a la Z están ocupadas. "
                            "Libera una sección antes de modificar."
                        ),
                    }, status=409)

                seccion.nombre = nuevo_seccion
                seccion.turno = turno
                seccion.save()

                Bitacora.objects.create(
                    nombre_usuario=request.session.get("usuario_nombre"),
                    fecha_hora=timezone.now(),
                    accion=f"Se actualizo la sección {nuevo_seccion} del turno {turno}."
                )
                
                return JsonResponse({
                    "estado": "exito",
                    "icon": "success",
                    "title": "Exito",
                    "descripcion": (
                        f"La sección se actualizó y ahora es {nuevo_seccion}."
                    ),
                    "seccion": nuevo_seccion,
                })

            return JsonResponse({
                "estado": "fallo",
                "icon": "Error",
                "title": "Error",
                "descripcion": "Ocurrio un error al momento de actualizar la sección."
            })

    return render(request, "Roles/Director_General/seccion_academica/visualizar_seccion.html")

# modulo_seccion
def reg_sec(request):
    if request.method == "POST":
        turno = request.POST.get("registro_turno")
        
        controles = [
            (turno, "Turno Académico", "Por favor, debe seleccione un turno académico."),
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
                seccion = obtener_siguiente_nombre_seccion()
                if seccion is None:
                    return JsonResponse({
                        "estado": "fallo",
                        "icon": "warning",
                        "title": "Sin secciones disponibles",
                        "descripcion": (
                            "Las letras de la A a la Z están ocupadas. "
                            "Libera una sección antes de registrar otra."
                        ),
                    }, status=409)

                SeccionAcademica.objects.create(
                    nombre=seccion,
                    turno=turno
                )
        
                Bitacora.objects.create(
                    nombre_usuario=request.session.get("usuario_nombre"),
                    fecha_hora=timezone.now(),
                    accion=f"Se registro la sección {seccion} del turno {turno}."
                )
        
                return JsonResponse({
                    "estado": "exito",
                    "icon": "success",
                    "title": "Exito",
                    "descripcion": "La sección se registró exitosamente.",
                    "seccion": seccion,
                    "siguiente": obtener_siguiente_nombre_seccion(),
                })
        except Exception as e:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Error",
                "descripcion": "Ocurrio un error en registrar la sección académica."
            })
    
    return render(request, "Roles/Director_General/seccion_academica/registrar_seccion.html")
