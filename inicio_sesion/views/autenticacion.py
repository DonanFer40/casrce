from datetime import timedelta
from importlib import import_module
from math import ceil

from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth.hashers import check_password
from django.http import JsonResponse
from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.views.decorators.cache import never_cache

from inicio_sesion.services.seguridad_admin_service import (
    iniciar_verificacion_admin
)

from inicio_sesion.models import (
    Nacimiento,
    Cuenta,
    ControlIntentosInicioSesion,
    SesionActivaNavegador,
    Usuario,
    Estudiante,
    Docente,
    CoordinadorPNF,
    ControlEstudio,
    DirectorGeneral,
)
from bitacora.services.registrar_accion import registrar_accion


INTENTOS_MAXIMOS_INICIO_SESION = 3
DURACION_BLOQUEO_INICIO_SESION = timedelta(minutes=5)
DURACION_SESION_NAVEGADOR = timedelta(hours=8)


def _sesion_del_navegador_activa(identificador_navegador, clave_actual):
    if not identificador_navegador:
        return False

    registro = SesionActivaNavegador.objects.filter(
        identificador_navegador=identificador_navegador
    ).first()
    if not registro:
        return False

    if registro.expira <= timezone.now():
        registro.delete()
        return False

    engine = import_module(settings.SESSION_ENGINE)
    if not engine.SessionStore(session_key=registro.clave_sesion).exists(
        registro.clave_sesion
    ):
        registro.delete()
        return False

    return registro.clave_sesion != clave_actual


def _respuesta_sesion_activa():
    return JsonResponse({
        "estado": "sesion_activa_otro_tab",
        "title": "Ya hay una sesión activa",
        "icon": "advertencia",
        "descripcion": (
            "Este navegador ya tiene una sesión iniciada en otra pestaña. "
            "Cierra esa sesión antes de iniciar otra."
        ),
    }, status=409)


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
        identificador_navegador = request.headers.get(
            "X-CASRCE-Browser-Id"
        )
        if not identificador_navegador:
            return JsonResponse({
                "estado": "fallo",
                "title": "No se pudo validar el navegador",
                "icon": "error",
                "descripcion": (
                    "Recarga la página e inténtalo nuevamente."
                ),
            }, status=400)

        clave_sesion_actual = request.session.session_key
        if _sesion_del_navegador_activa(
            identificador_navegador,
            clave_sesion_actual,
        ):
            return _respuesta_sesion_activa()

        id_cuenta_actual = request.session.get("id_cuenta")
        if id_cuenta_actual:
            cuenta_actual = Cuenta.objects.filter(
                id_cuenta=id_cuenta_actual
            ).exists()

            if not cuenta_actual:
                request.session.flush()
            elif request.POST.get("confirmar_nueva_sesion") != "1":
                return JsonResponse({
                    "estado": "advertencia",
                    "title": "Ya tienes una sesión iniciada",
                    "icon": "advertencia",
                    "descripcion": (
                        "Si continúas, se cerrará la sesión actual en este "
                        "navegador y se iniciará una nueva. ¿Deseas continuar?"
                    ),
                })

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

            if id_cuenta_actual and cuenta_actual:
                request.session.flush()

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
        
        with transaction.atomic():
            control, _ = ControlIntentosInicioSesion.objects.get_or_create(
                cuenta=credenciales
            )
            control = ControlIntentosInicioSesion.objects.select_for_update().get(
                pk=control.pk
            )
            ahora = timezone.now()

            if control.bloqueado_hasta and ahora < control.bloqueado_hasta:
                segundos_restantes = max(
                    1,
                    ceil((control.bloqueado_hasta - ahora).total_seconds()),
                )
                minutos_restantes = ceil(segundos_restantes / 60)
                return JsonResponse({
                    "estado": "bloqueado",
                    "title": "Acceso temporalmente bloqueado",
                    "icon": "advertencia",
                    "descripcion": (
                        "Has superado los 3 intentos permitidos. "
                        f"Inténtalo nuevamente en {minutos_restantes} "
                        "minuto(s)."
                    ),
                    "segundos_restantes": segundos_restantes,
                }, status=429)

            if control.bloqueado_hasta:
                control.intentos = 0
                control.bloqueado_hasta = None

            coincide = check_password(contrasenia, credenciales.clave)
            if coincide:
                control.intentos = 0
                control.bloqueado_hasta = None
            else:
                control.intentos += 1
                if control.intentos >= INTENTOS_MAXIMOS_INICIO_SESION:
                    control.intentos = INTENTOS_MAXIMOS_INICIO_SESION
                    control.bloqueado_hasta = (
                        ahora + DURACION_BLOQUEO_INICIO_SESION
                    )

            control.save(update_fields=[
                "intentos",
                "bloqueado_hasta",
                "actualizado",
            ])

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
            if control.bloqueado_hasta:
                return JsonResponse({
                    "estado": "bloqueado",
                    "title": "Acceso temporalmente bloqueado",
                    "icon": "advertencia",
                    "descripcion": (
                        "Has realizado 3 intentos fallidos. "
                        "Inténtalo nuevamente en 5 minutos."
                    ),
                    "segundos_restantes": int(
                        DURACION_BLOQUEO_INICIO_SESION.total_seconds()
                    ),
                }, status=429)

            return JsonResponse({
                "estado": "fallo",
                "title": "Error",
                "icon": "error",
                "descripcion": (
                    "La contraseña no coincide con la que está registrada. "
                    f"Te quedan {INTENTOS_MAXIMOS_INICIO_SESION - control.intentos} "
                    "intento(s)."
                )
            })

        usuario = credenciales.id_usuario

        # This custom login does not use django.contrib.auth.login(), so rotate
        # the session explicitly and discard any data from a previous account.
        with transaction.atomic():
            registro, _ = SesionActivaNavegador.objects.get_or_create(
                identificador_navegador=identificador_navegador,
                defaults={
                    "cuenta": credenciales,
                    "clave_sesion": "",
                    "expira": timezone.now(),
                },
            )
            registro = SesionActivaNavegador.objects.select_for_update().get(
                pk=registro.pk
            )

            if (
                registro.clave_sesion
                and registro.expira > timezone.now()
                and registro.clave_sesion != clave_sesion_actual
            ):
                engine = import_module(settings.SESSION_ENGINE)
                if engine.SessionStore(
                    session_key=registro.clave_sesion
                ).exists(registro.clave_sesion):
                    return _respuesta_sesion_activa()

            request.session.flush()
            request.session.create()
            registro.cuenta = credenciales
            registro.clave_sesion = request.session.session_key
            registro.expira = timezone.now() + DURACION_SESION_NAVEGADOR
            registro.save(update_fields=[
                "cuenta",
                "clave_sesion",
                "expira",
                "actualizado",
            ])

        # --- AQUÍ ASIGNAMOS id_cuenta DESDE credenciales ---
        request.session['id_cuenta'] = credenciales.id_cuenta
        request.session['cedula_usuario'] = usuario.cedula_identidad
        request.session['usuario_nombre'] = f"{usuario.nombres} {usuario.apellidos}"
        request.session.set_expiry(DURACION_SESION_NAVEGADOR.total_seconds())

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
                "tab_auth_required": True,
                "url": reverse("panel_usuario")
            })
        else:
            request.session['registro_completado'] = False

            return JsonResponse({
                "estado": "exito",
                "tab_auth_required": True,
                "url": reverse("comp_registro")
            })
    
    return render(request, 'Sesion/Login/inicio_sesion.html')

@never_cache
def cerrar_sesion(request):
    identificador_navegador = (
        request.headers.get("X-CASRCE-Browser-Id")
        or request.GET.get("browser_auth_id")
    )
    if identificador_navegador and request.session.session_key:
        SesionActivaNavegador.objects.filter(
            identificador_navegador=identificador_navegador,
            clave_sesion=request.session.session_key,
        ).delete()

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