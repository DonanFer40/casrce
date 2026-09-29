from django.shortcuts import render
from django.http import JsonResponse
from django.db import transaction
from django.utils import timezone

from inicio_sesion.models import Autoridades, Bitacora

CARGO = [
    "Rector",
    "Vicerrector",
    "Responsable Académico"
]

# autoridades_registradas
def auts_reg(request):
    autoridades = Autoridades.objects.all().values(
        "id_autoridad",
        "nombres",
        "apellidos",
        "cedula_identidad",
        "cargo",
        "resolucion"
    )

    return JsonResponse(list(autoridades), safe=False)

# datos_autoridad
def datos_aut(request):
    if request.method == "POST":
        nacionalidad = request.POST.get("nacionalidad")
        cedula = request.POST.get("cedula")

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
                "descripcion": "Por favor, ingresa la cedula de identidad."
            })
        
        cedula_identidad = nacionalidad + "-" + cedula

        try:
            autoridad = Autoridades.objects.get(cedula_identidad=cedula_identidad)
        except Autoridades.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Error",
                "descripcion": "El usuario no se encuentra registrado."
            })
        
        return JsonResponse({
            "estado": "exito",
            "id": autoridad.id_autoridad,
            "nombres": autoridad.nombres,
            "apellidos": autoridad.apellidos,
            "genero": autoridad.genero,
            "cargo": autoridad.cargo,
            "resolucion": autoridad.resolucion
        })

# actualizar_datos_autoridad
def act_datos_aut(request):
    if request.method == "POST":
        id_autoridad = request.POST.get("usuarioseleccionado")
        nombres = request.POST.get("nombres_actualizar", "").strip()
        apellidos = request.POST.get("apellidos_actualizar", "").strip()
        genero = request.POST.get("genero_actualizar", "").strip()
        cargo_nuevo = request.POST.get("cargo_actualizar", "").strip()
        resolucion = request.POST.get("resolucion_actualizar", "").strip()

        cambiar_cargo = ( request.POST.get("cambiar_cargo") == "true")
        controles = [
            (nombres, "Nombre de la Autoridad", "Por favor, ingrese el nombre de la autoridad."),
            (apellidos, "Apellido de la Autoridad", "Por favor, ingrese el apellido de la autoridad."),
            (genero, "Genero", "Por favor, selecciona el genero."),
            (cargo_nuevo, "Cargo de la Autoridad", "Por favor, selecciona el cargo de la autoridad."),
            (resolucion, "Resolución", "Por favor, ingrese la resolución de la autoridad."),
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
            autoridad = Autoridades.objects.get(id_autoridad=id_autoridad)
        except Autoridades.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Error",
                "descripcion": "El usuario no se encuentra registrado."
            })

        cargo_anterior = autoridad.cargo

        try:
            with transaction.atomic():
                # Actualizar siempre los demás datos
                autoridad.nombres = nombres
                autoridad.apellidos = apellidos
                autoridad.genero = genero
                autoridad.resolucion = resolucion

                # Solo modificar el cargo si el usuario confirmó
                if cambiar_cargo and cargo_nuevo != cargo_anterior:
                    otra_autoridad = Autoridades.objects.filter(
                        cargo=cargo_nuevo
                    ).exclude(
                        id_autoridad=autoridad.id_autoridad
                    ).first()

                    if otra_autoridad:
                        # Intercambio de cargos
                        otra_autoridad.cargo = cargo_anterior
                        otra_autoridad.save()

                    autoridad.cargo = cargo_nuevo
                else:
                    # Conserva el cargo original
                    autoridad.cargo = cargo_anterior

                autoridad.save()

                Bitacora.objects.create(
                    nombre_usuario=request.session.get("usuario_nombre"),
                    fecha_hora=timezone.now(),
                    accion=(
                        f"Actualizó la autoridad "
                        f"'{nombres}' {apellidos}."
                    )
                )
            return JsonResponse({
                "estado": "exito",
                "icon": "success",
                "title": "Éxito",
                "descripcion": (
                    "Los datos de la autoridad "
                    "se actualizaron exitosamente."
                )
            })

        except Exception as error:
            print(error)
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Error",
                "descripcion": (
                    "Hubo un error al actualizar "
                    "los datos de la autoridad."
                )
            })
    
    return render(request, "Roles/Director_General/autoridades/actualizar_autoridades.html")


def cargo_user(request):

    if request.method == "POST":

        cargo = request.POST.get("cargo")
        id_autoridad = request.POST.get("id_autoridad")

        consulta = Autoridades.objects.filter(
            cargo=cargo
        )

        if id_autoridad:
            consulta = consulta.exclude(
                id_autoridad=id_autoridad
            )

        autoridad = consulta.first()

        autoridades = Autoridades.objects.all().values(
            "id_autoridad",
            "nombres",
            "apellidos",
            "cargo"
        )

        return JsonResponse({
            "existe": autoridad is not None,

            "autoridad": {
                "id": autoridad.id_autoridad,
                "nombres": autoridad.nombres,
                "apellidos": autoridad.apellidos,
                "cargo": autoridad.cargo
            } if autoridad else None,

            "autoridades": list(autoridades)
        })

    
def cargo_asig_aut(request):
    cargos_registrados = set(
        Autoridades.objects.values_list("cargo", flat=True)
    )

    cargos_disponibles = [
        cargo for cargo in CARGO
        if cargo not in cargos_registrados
    ]

    return JsonResponse({
        "cargo": cargos_disponibles
    })


def val_ci_aut(request):
    if request.method == "POST":
        nacionalidad = request.POST.get("nacionalidad")
        cedula = request.POST.get("cedula")

        existe = Autoridades.objects.filter(cedula_identidad=f"{nacionalidad}-{cedula}").exists()
        if existe:
            return JsonResponse({ "existe": True })

        return JsonResponse({ "existe": False })

def val_resolucion(request):

    if request.method == "POST":

        resolucion = request.POST.get("resolucion", "").strip().upper()
        id_autoridad = request.POST.get("id_autoridad")

        consulta = Autoridades.objects.filter(
            resolucion=resolucion
        )

        if id_autoridad:
            consulta = consulta.exclude(
                id_autoridad=id_autoridad
            )

        existe = consulta.exists()

        return JsonResponse({
            "existe": existe
        })


def reg_auts(request):    
    if request.method == "POST":
        nombres = request.POST.get("nombres_registrar")
        apellidos = request.POST.get("apellidos_registrar")
        nacionalidad = request.POST.get("nacionalidad_registrar")
        cedula = request.POST.get("cedula_registrar")
        genero = request.POST.get("genero_registrar")
        cargo = request.POST.get("cargo_registrar")
        resolucion = request.POST.get("resolucion_registrar")

        controles = [
            (nombres, "Nombre de la Autoridad", "Por favor, ingrese el nombre de la autoridad."),
            (apellidos, "Apellido de la Autoridad", "Por favor, ingrese el apellido de la autoridad."),
            (nacionalidad, "Nacionalidad de la Autoridad", "Por favor, selecciona la nacionalidad."),
            (cedula, "Cedula de la Autoridad", "Por favor, ingresa los números de la cedula de identidad."),
            (genero, "Genero", "Por favor, selecciona el genero."),
            (cargo, "Cargo de la Autoridad", "Por favor, selecciona el cargo de la autoridad."),
            (resolucion, "Resolución", "Por favor, ingrese la resolución de la autoridad."),
        ]

        for value, field_name, error_message in controles:
            if not value:
                return JsonResponse({
                    "estado": "fallo",
                    "icon": "warning",
                    "title": field_name,
                    "descripcion": error_message
                })

        cedula_autoridad = nacionalidad + "-" + cedula

        with transaction.atomic():
            Autoridades.objects.create(nombres=nombres, apellidos=apellidos, cedula_identidad=cedula_autoridad, genero=genero, cargo=cargo, resolucion=resolucion)

            Bitacora.objects.create(
                nombre_usuario=request.session.get("usuario_nombre"),
                fecha_hora=timezone.now(),
                accion=f"Registró la autoridad '{nombres}' {apellidos} de la C.I'{cedula_autoridad}' {cargo}."
            )

            return JsonResponse({
                "estado": "exito",
                "icon": "success",
                "title": "Exito",
                "descripcion": "Los datos de la autoridad se registraron exitosamente."
            })

    return render(request, "Roles/Director_General/autoridades/registrar_autoridades.html")


def vist_auts(request):
    return render(request, "Roles/Director_General/autoridades/visualizar_autoridades.html")
