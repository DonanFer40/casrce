from django.shortcuts import render
from django.http import JsonResponse
from django.db import transaction
from django.utils import timezone

from inicio_sesion.models import Nucleos, Pnf, PNFNucleo, Bitacora, DirectorGeneral, ControlEstudio

def obtener_nucleo_usuario(request):

    cedula_usuario = request.session.get("cedula_usuario")

    if not cedula_usuario:
        return None

    # Buscar como Director General
    director = DirectorGeneral.objects.select_related(
        "nucleo"
    ).filter(
        usuario__cedula_identidad=cedula_usuario
    ).first()

    if director:
        return director.nucleo

    # Buscar como Control de Estudio
    control = ControlEstudio.objects.select_related(
        "nucleo"
    ).filter(
        usuario__cedula_identidad=cedula_usuario
    ).first()

    if control:
        return control.nucleo

    return None

# pnfs_registrada
def pnfs_reg(request):
    cedula_usuario = request.session.get("cedula_usuario")

    nucleo = None

    # Buscar como Director General
    director = DirectorGeneral.objects.select_related(
        "nucleo"
    ).filter(
        usuario__cedula_identidad=cedula_usuario
    ).first()

    if director:
        nucleo = director.nucleo

    # Si no es Director, buscar como Control de Estudio
    if not nucleo:
        control = ControlEstudio.objects.select_related(
            "nucleo"
        ).filter(
            usuario__cedula_identidad=cedula_usuario
        ).first()

        if control:
            nucleo = control.nucleo

    if not nucleo:
        return JsonResponse({
            "estado": "error",
            "mensaje": "El usuario no tiene un núcleo asignado."
        }, status=404)

    datos = []

    nucleos = Nucleos.objects.filter(
        id_nucleo=nucleo.id_nucleo
    ).prefetch_related(
        "pnfnucleo_set__id_pnf"
    )

    for nucleo in nucleos:
        datos.append({
            "id_nucleo": nucleo.id_nucleo,
            "municipio": nucleo.municipio,
            "pnfs": [
                {
                    "id_pnf": relacion.id_pnf.id_pnf,
                    "pnf": relacion.id_pnf.pnf,
                    "codigo": relacion.id_pnf.codigo,
                    "periodo_academico": relacion.id_pnf.periodo_academico,
                }
                for relacion in nucleo.pnfnucleo_set.all()
            ]
        })

    return JsonResponse({
        "estado": "exito",
        "nucleos": datos
    })

# datos_pnf
def datos_pnf(request):

    if request.method != "POST":
        return JsonResponse({
            "estado": "fallo",
            "icon": "warning",
            "title": "Solicitud no válida",
            "descripcion": "El método de consulta no está permitido."
        }, status=405)

    codigo_pnf = request.POST.get("codigo")

    nucleo = obtener_nucleo_usuario(request)

    if not nucleo:
        return JsonResponse({
            "estado": "fallo",
            "icon": "error",
            "title": "Acceso denegado",
            "descripcion": "No se pudo identificar el núcleo del usuario."
        }, status=403)

    pnf = Pnf.objects.filter(
        codigo=codigo_pnf
    ).first()

    if not pnf:
        return JsonResponse({
            "estado": "fallo",
            "icon": "error",
            "title": "PNF no encontrado",
            "descripcion": "El programa seleccionado no se encuentra registrado."
        })

    existe_asignacion = PNFNucleo.objects.filter(
        id_pnf=pnf,
        id_nucleo=nucleo
    ).exists()

    if not existe_asignacion:
        return JsonResponse({
            "estado": "fallo",
            "icon": "error",
            "title": "Acceso no permitido",
            "descripcion": "El PNF seleccionado no pertenece a tu núcleo."
        }, status=403)

    return JsonResponse({
        "estado": "exito",
        "title": "PNF encontrado",
        "descripcion": "Se cargaron los datos del programa.",
        "pnf": {
            "id": pnf.id_pnf,
            "nombre": pnf.pnf,
            "codigo": pnf.codigo,
            "periodo_academico": pnf.periodo_academico
        }
    })

# guardar_actuailizacion_pnf
def act_pnf(request):

    if request.method != "POST":
        return JsonResponse({
            "estado": "fallo",
            "icon": "warning",
            "title": "Solicitud no válida",
            "descripcion": "El método de actualización no está permitido."
        }, status=405)

    id_pnf = request.POST.get("id_pnf")
    nombre_pnf = request.POST.get("nombrepnf")
    periodoacademico_pnf = request.POST.get("periodoacademico")

    if not id_pnf or not nombre_pnf or not periodoacademico_pnf:
        return JsonResponse({
            "estado": "fallo",
            "icon": "warning",
            "title": "Datos incompletos",
            "descripcion": "Debe completar todos los campos solicitados."
        })

    if periodoacademico_pnf not in ["Trimestre", "Semestre"]:
        return JsonResponse({
            "estado": "fallo",
            "icon": "warning",
            "title": "Periodo académico",
            "descripcion": "El periodo académico seleccionado no es válido."
        })

    nucleo = obtener_nucleo_usuario(request)

    if not nucleo:
        return JsonResponse({
            "estado": "fallo",
            "icon": "error",
            "title": "Acceso denegado",
            "descripcion": "No se pudo identificar el núcleo del usuario."
        }, status=403)

    try:

        with transaction.atomic():

            pnf = Pnf.objects.select_for_update().filter(
                id_pnf=id_pnf
            ).first()

            if not pnf:
                return JsonResponse({
                    "estado": "fallo",
                    "icon": "error",
                    "title": "PNF no encontrado",
                    "descripcion": "El programa que intenta modificar no existe."
                })

            existe_asignacion = PNFNucleo.objects.filter(
                id_pnf=pnf,
                id_nucleo=nucleo
            ).exists()

            if not existe_asignacion:
                return JsonResponse({
                    "estado": "fallo",
                    "icon": "error",
                    "title": "Acceso no permitido",
                    "descripcion": "No tiene autorización para modificar este programa."
                }, status=403)

            # Comprobar si el nombre ya pertenece a otro PNF.
            nombre_existente = Pnf.objects.filter(
                pnf__iexact=nombre_pnf
            ).exclude(
                id_pnf=pnf.id_pnf
            ).exists()

            if nombre_existente:
                return JsonResponse({
                    "estado": "fallo",
                    "icon": "warning",
                    "title": "Nombre duplicado",
                    "descripcion": "Ya existe otro PNF registrado con ese nombre."
                })

            pnf.pnf = nombre_pnf
            pnf.periodo_academico = periodoacademico_pnf

            pnf.save()

            Bitacora.objects.create(
                nombre_usuario=request.session.get("usuario_nombre"),
                accion=(
                    f"Actualización del PNF: {nombre_pnf}, "
                    f"código: {pnf.codigo} y "
                    f"periodo académico: {periodoacademico_pnf}."
                ),
                fecha_hora=timezone.now()
            )

            return JsonResponse({
                "estado": "exito",
                "icon": "success",
                "title": "PNF actualizado",
                "descripcion": "Los datos del programa se actualizaron correctamente."
            })

    except Exception as error:

        print(f"Error al actualizar PNF: {error}")

        return JsonResponse({
            "estado": "fallo",
            "icon": "error",
            "title": "Error de actualización",
            "descripcion": "Ocurrió un problema al actualizar el programa."
        }, status=500)

def nombre_pnf(request):

    if request.method == "POST":

        nombre = request.POST.get("nombrepnf", "").strip()
        id_pnf = request.POST.get("id_pnf")

        consulta = Pnf.objects.filter(
            pnf__iexact=nombre
        )

        if id_pnf:
            consulta = consulta.exclude(id_pnf=id_pnf)

        return JsonResponse({
            "existe": consulta.exists()
        })

    return JsonResponse({
        "existe": False
    })


def codigo_pnf(request):

    if request.method == "POST":

        codigo = request.POST.get("codigopnf", "").strip()
        id_pnf = request.POST.get("id_pnf")

        consulta = Pnf.objects.filter(
            codigo__iexact=codigo
        )

        if id_pnf:
            consulta = consulta.exclude(id_pnf=id_pnf)

        return JsonResponse({
            "existe": consulta.exists()
        })

    return JsonResponse({
        "existe": False
    })

def reg_pnf(request):
    if request.method == "POST":
        nombre_pnf = request.POST.get("nombrepnf", "").strip()
        codigo_pnf = request.POST.get("codigopnf", "").strip()
        periodoacademico_pnf = request.POST.get("periodoacademico", "").strip()

        controles = [
            (nombre_pnf, "Nombre del PNF", "Debe ingresar el nombre del PNF."),
            (codigo_pnf, "Código del PNF", "Debe ingresar el código del PNF."),
            (periodoacademico_pnf, "Periodo Académico", "Debe seleccionar el periodo académico.")
        ]

        for value, field_name, error_message in controles:
            if not value:
                return JsonResponse({
                    "estado": "fallo",
                    "icon": "warning",
                    "title": field_name,
                    "descripcion": error_message
                })

        if len(nombre_pnf) > 50 or len(codigo_pnf) > 60:
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Longitud no válida",
                "descripcion": "El nombre admite hasta 50 caracteres y el código hasta 60.",
            }, status=400)

        if periodoacademico_pnf not in {"Trimestre", "Semestre"}:
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Periodo Académico",
                "descripcion": "El periodo académico seleccionado no es válido.",
            }, status=400)

        director = DirectorGeneral.objects.select_related("nucleo").filter(
            usuario__cedula_identidad=request.session.get("cedula_usuario")
        ).first()
        if director is None:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Acceso denegado",
                "descripcion": "No se encontró un núcleo asignado al Director General.",
            }, status=403)

        nucleo_director = director.nucleo

        with transaction.atomic():
            if Pnf.objects.filter(pnf__iexact=nombre_pnf).exists():
                return JsonResponse({
                    "estado": "fallo",
                    "icon": "warning",
                    "title": "Nombre duplicado",
                    "descripcion": "Ya existe un PNF registrado con ese nombre.",
                }, status=409)

            if Pnf.objects.filter(codigo__iexact=codigo_pnf).exists():
                return JsonResponse({
                    "estado": "fallo",
                    "icon": "warning",
                    "title": "Código duplicado",
                    "descripcion": "Ya existe un PNF registrado con ese código.",
                }, status=409)

            pnf = Pnf.objects.create(pnf=nombre_pnf, codigo=codigo_pnf, periodo_academico=periodoacademico_pnf)

            # Relacionarlo automáticamente con el núcleo del Director
            PNFNucleo.objects.create(id_pnf=pnf, id_nucleo=nucleo_director)

            Bitacora.objects.create(
                nombre_usuario=request.session.get("usuario_nombre"),
                accion=f"Registro del PNF: {nombre_pnf} con código: {codigo_pnf} y periodo académico: {periodoacademico_pnf}.",
                fecha_hora=timezone.now()
            )

            return JsonResponse({
                "estado": "exito",
                "icon": "success",
                "title": "Exito",
                "descripcion": "Los datos del PNF han sido registrados correctamente."
            })

        return JsonResponse({
            "estado": "fallo",
            "icon": "error",
            "title": "Error",
            "descripcion": "Hubo un error al registrar los datos del PNF."
        })
    
    return render(request, "Roles/Director_General/pnf/registrar_pnfs.html")

def ver_pnf(request):
    return render(request, "Roles/Director_General/pnf/visualizar_pnf.html")