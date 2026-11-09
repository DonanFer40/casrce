from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth.hashers import check_password
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.conf import settings

from inicio_sesion.services.seguridad_admin_service import (
    iniciar_verificacion_admin
)

from inicio_sesion.models import (
    ConfiguracionSeguridadAdmin,
    Nacimiento,
    Cuenta,
    Usuario,
    Estudiante,
    Docente,
    CoordinadorPNF,
    ControlEstudio,
    DirectorGeneral,
)
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
            "nucleo": docente.nucleo.municipio if docente.nucleo else None,
            "pnf": docente.pnf.pnf if docente.pnf else None,
        })

    # Solo coordinadores activos
    for coordinador in CoordinadorPNF.objects.filter(
        usuario=usuario,
        activo=True
    ).select_related("nucleo", "pnf"):
        roles.append({
            "rol": "Coordinador PNF",
            "nucleo": (
                coordinador.nucleo.municipio if coordinador.nucleo else None
            ),
            "pnf": coordinador.pnf.pnf if coordinador.pnf else None,
        })

    # Solo controles de estudio activos
    for control in ControlEstudio.objects.filter(
        usuario=usuario,
        activo=True
    ).select_related("nucleo"):
        roles.append({
            "rol": "Control de Estudio",
            "nucleo": control.nucleo.municipio if control.nucleo else None,
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
                "descripcion": "La contraseña no coincide con la que esta registrada.",
                "control": "password"
            })

        usuario = credenciales.id_usuario
        
        # --- AQUÍ ASIGNAMOS id_cuenta DESDE credenciales ---
        request.session['id_cuenta'] = credenciales.id_cuenta
        request.session['cedula_usuario'] = usuario.cedula_identidad
        request.session['usuario_nombre'] = f"{usuario.nombres} {usuario.apellidos}"
        request.session["foto_perfil_url"] = (
            usuario.foto_perfil.url if usuario.foto_perfil else ""
        )

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
    
    contexto = {"inicializacion_admin_disponible": False}
    nombre_superusuario = getattr(settings, "CASRCE_ADMIN_USERNAME", "")
    if nombre_superusuario:
        modelo_usuario = get_user_model()
        superusuario = modelo_usuario.objects.filter(
            **{modelo_usuario.USERNAME_FIELD: nombre_superusuario},
            is_active=True,
            is_staff=True,
            is_superuser=True,
        ).first()
        contexto["inicializacion_admin_disponible"] = bool(
            superusuario
            and not ConfiguracionSeguridadAdmin.objects.filter(
                usuario=superusuario,
                totp_activo=True,
            ).exists()
        )

    return render(request, 'Sesion/Login/inicio_sesion.html', contexto)

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