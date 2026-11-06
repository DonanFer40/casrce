from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth.hashers import check_password
from django.http import JsonResponse
from django.conf import settings

from inicio_sesion.services.seguridad_admin_service import (
    iniciar_verificacion_admin
)

from inicio_sesion.models import Nacimiento, Cuenta, Usuario, Estudiante, Docente, CoordinadorPNF, ControlEstudio, DirectorGeneral
from bitacora.services.registrar_accion import registrar_accion


def _registrar_evento_seguro(request, **datos):
    # La bitácora no debe impedir que el flujo de autenticación responda.
    try:
        registrar_accion(request, **datos)
    except Exception:
        import logging
        logging.getLogger(__name__).exception("No se pudo registrar el evento de autenticación.")

def obtener_roles(usuario):
    roles = []

    for estudiante in Estudiante.objects.filter(
        usuario=usuario
    ).select_related("nucleo", "pnf"):
        roles.append({
            "rol": "Estudiante",
            "nucleo": estudiante.nucleo.municipio if estudiante.nucleo else None,
            "pnf": estudiante.pnf.pnf if estudiante.pnf else None,
            "registro_completo": (
                estudiante.nucleo is not None
                and estudiante.pnf is not None
            ),
        })

    # Solo docentes activos
    for docente in Docente.objects.filter(
        usuario=usuario,
        activo=True
    ).select_related("nucleo", "pnf"):
        roles.append({
            "rol": "Docente",
            "nucleo": docente.nucleo.municipio,
            "pnf": docente.pnf.pnf,
        })

    # Solo coordinadores activos
    for coordinador in CoordinadorPNF.objects.filter(
        usuario=usuario,
        activo=True
    ).select_related("nucleo", "pnf"):
        roles.append({
            "rol": "Coordinador PNF",
            "nucleo": coordinador.nucleo.municipio,
            "pnf": coordinador.pnf.pnf,
        })

    # Solo controles de estudio activos
    for control in ControlEstudio.objects.filter(
        usuario=usuario,
        activo=True
    ).select_related("nucleo"):
        roles.append({
            "rol": "Control de Estudio",
            "nucleo": control.nucleo.municipio,
        })

    # Director General no tiene campo activo actualmente
    if DirectorGeneral.objects.filter(usuario=usuario).exists():
        roles.append({
            "rol": "Director General",
        })

    return roles

def autenticacion(request):
    if request.method == "POST":
        nombre_usuario = request.POST.get("usuario")
        contrasenia = request.POST.get("contrasenia")

        if not nombre_usuario:
            return JsonResponse({
                "estado": "fallo",
                "title": "Vacio",
                "icon": "warning",
                "descripcion": "Por favor, ingresa su nombre de usuario."
            })
        
        if not contrasenia:
            return JsonResponse({
                "estado": "fallo",
                "title": "Vacio",
                "icon": "warning",
                "descripcion": "Por favor, ingresa su contraseña."
            })

                # ==================================================
        # ACCESO ESPECIAL AL PANEL ADMINISTRATIVO
        # ==================================================

        usuario_gate = settings.CASRCE_ADMIN_GATE_USERNAME
        hash_gate = settings.CASRCE_ADMIN_GATE_PASSWORD_HASH

        if usuario_gate and nombre_usuario == usuario_gate:

            if not hash_gate or not check_password(
                contrasenia,
                hash_gate
            ):
                return JsonResponse({
                    "estado": "fallo",
                    "title": "Acceso denegado",
                    "icon": "error",
                    "descripcion": "Las credenciales especiales no son correctas."
                })

            try:

                exito, mensaje = iniciar_verificacion_admin(
                    request,
                    nombre_usuario,
                    contrasenia,
                )
                if not exito:
                    return JsonResponse({
                        "estado": "fallo",
                        "title": "Acceso denegado",
                        "icon": "error",
                        "descripcion": mensaje,
                    }, status=403)

                return JsonResponse({
                    "estado": "exito",
                    "url": reverse("acceso_admin")
                })

            except Exception:

                import logging

                logging.getLogger(__name__).exception(
                    "Error iniciando el acceso administrativo."
                )

                return JsonResponse({
                    "estado": "fallo",
                    "title": "Error de seguridad",
                    "icon": "error",
                    "descripcion": "No fue posible iniciar la verificación administrativa."
                })
        
        try:
            credenciales = Cuenta.objects.get(usuario=nombre_usuario)
        except Cuenta.DoesNotExist:
            _registrar_evento_seguro(
                request,
                categoria="AUTENTICACION",
                modulo="Inicio de sesión",
                accion="Intento de inicio de sesión",
                descripcion="Se intentó acceder con un nombre de usuario no registrado.",
                resultado="FALLIDO",
                nivel="ADVERTENCIA",
                detalles={"usuario_intentado": nombre_usuario[:160]},
            )
            return JsonResponse({
                "estado": "fallo",
                "title": "Error",
                "icon": "error",
                "descripcion": "El usuario no se encuentra registrado."
            })
        
        coincide = check_password(contrasenia, credenciales.clave)
        if not coincide:
            _registrar_evento_seguro(
                request,
                categoria="AUTENTICACION",
                modulo="Inicio de sesión",
                accion="Intento de inicio de sesión",
                descripcion="Se rechazó un intento de acceso por credenciales incorrectas.",
                resultado="FALLIDO",
                nivel="ADVERTENCIA",
                detalles={"usuario_intentado": nombre_usuario[:160]},
            )
            return JsonResponse({
                "estado": "fallo",
                "title": "Error",
                "icon": "error",
                "descripcion": "La contraseña no coincide con la que esta registrada."
            })

        usuario = credenciales.id_usuario
        
        # --- AQUÍ ASIGNAMOS id_cuenta DESDE credenciales ---
        request.session['id_cuenta'] = credenciales.id_cuenta
        request.session['cedula_usuario'] = usuario.cedula_identidad
        request.session['usuario_nombre'] = f"{usuario.nombres} {usuario.apellidos}"

        roles = obtener_roles(usuario)
        request.session["roles"] = roles
        request.session["rol"] = [r["rol"] for r in roles]

        _registrar_evento_seguro(
            request,
            categoria="AUTENTICACION",
            modulo="Inicio de sesión",
            accion="Inicio de sesión",
            descripcion="El usuario inició sesión correctamente.",
            resultado="EXITOSO",
            detalles={"cantidad_roles_disponibles": len(roles)},
        )

        registro_basico = Nacimiento.objects.filter(id_usuario=usuario).exists()

        if registro_basico:
            request.session['registro_completado'] = True

            return JsonResponse({
                "estado": "exito",
                "url": reverse("panel_usuario")
            })
        else:
            request.session['registro_completado'] = False

            return JsonResponse({
                "estado": "exito",
                "url": reverse("comp_registro")
            })
    
    return render(request, 'Sesion/Login/inicio_sesion.html')

def cerrar_sesion(request):
    _registrar_evento_seguro(
        request,
        categoria="AUTENTICACION",
        modulo="Inicio de sesión",
        accion="Cierre de sesión",
        descripcion="El usuario cerró su sesión.",
        resultado="EXITOSO",
    )
    request.session.flush()
    return redirect("inicio_sesion")