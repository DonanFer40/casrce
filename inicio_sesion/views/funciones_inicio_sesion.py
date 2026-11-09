
from django.shortcuts import render
from django.contrib.auth.hashers import check_password, make_password
from django.http import JsonResponse
from django.conf import settings
from django.core.mail import send_mail
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.template.loader import render_to_string
from django.utils import timezone
from django.db import transaction
from datetime import timedelta
import secrets
import uuid
from math import ceil

from inicio_sesion.models import (
    Usuario,
    Contacto,
    Cuenta,
    Estudiante,
    VerificacionCodigo,
    Docente,
    CoordinadorPNF,
    ControlEstudio,
)
from inicio_sesion.services.correos import procesar_html_correo
from inicio_sesion.validators import validar_contrasenia_segura


# ============================================================
# PANEL Y VALIDACIONES DE REGISTRO
# ============================================================

def panel_registro(request):
    return render(request, 'Sesion/Login/panel_registro.html')


def val_usuario(request):
    if request.method == "POST":
        nombre_usuario = request.POST.get("nombre_usuario", "").strip()

        existe = Cuenta.objects.filter(
            usuario__iexact=nombre_usuario
        ).exists()

        return JsonResponse({"existe": existe})

    return JsonResponse({"existe": False})


def val_password(request):
    if request.method == "POST":
        password = request.POST.get("password", "")

        existe = any(
            check_password(password, cuenta.clave)
            for cuenta in Cuenta.objects.only("clave")
        )

        return JsonResponse({"existe": existe})

    return JsonResponse({"existe": False})


# ============================================================
# RESPUESTAS DEL REGISTRO ESTUDIANTIL
# ============================================================

def _respuesta_registro(estado, title, descripcion, icon="warning", **extra):
    datos = {
        "estado": estado,
        "title": title,
        "descripcion": descripcion,
        "icon": icon,
    }

    datos.update(extra)

    return JsonResponse(datos)


# ============================================================
# CORREO DE REGISTRO ESTUDIANTIL
# ============================================================

def _enviar_correo_registro_exitoso(datos):
    html = render_to_string(
        "Email/registro_exitoso.html",
        {
            "nombres": datos["nombres"],
            "apellidos": datos["apellidos"],
            "nombre_usuario": datos["usuario"],
        },
    )

    html = procesar_html_correo(
        html,
        "Estilos/Email/registro_exitoso.css",
    )

    enviados = send_mail(
        subject="¡Tu registro en CASRCE ha sido completado!",
        message=(
            f"Hola, {datos['nombres']} {datos['apellidos']}. "
            "Tu registro en CASRCE se completó correctamente. "
            f"Ya puedes iniciar sesión con el usuario {datos['usuario']}."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[datos["correo_electronico"]],
        html_message=html,
        fail_silently=False,
    )

    if enviados != 1:
        raise RuntimeError(
            "El servidor de correo no confirmó el envío del mensaje de bienvenida."
        )


def _enviar_codigo_registro(request, datos, token, reenviar=False):
    """Genera y envía un código exclusivo del registro estudiantil."""

    cedula = datos["cedula_identidad"]
    ahora = timezone.now()
    codigo = f"{secrets.randbelow(1_000_000):06d}"

    verificacion = VerificacionCodigo.objects.filter(
        cedula_identidad=cedula,
        token=token,
        descripcion="Registro estudiante",
    ).first()

    if verificacion:
        verificacion.codigo = codigo
        verificacion.creado = ahora
        verificacion.fecha_expiracion = ahora + timedelta(minutes=5)
        verificacion.intentos = 0
        verificacion.bloqueado_hasta = None
        verificacion.activo = 1

        if reenviar:
            verificacion.numero_reenvios += 1

        verificacion.save()

    else:
        verificacion = VerificacionCodigo.objects.create(
            cedula_identidad=cedula,
            token=token,
            codigo=codigo,
            creado=ahora,
            intentos=0,
            numero_reenvios=0,
            bloqueado_hasta=None,
            activo=1,
            descripcion="Registro estudiante",
            fecha_expiracion=ahora + timedelta(minutes=5),
        )

    html = render_to_string(
        "Email/enviar_codigo.html",
        {
            "nombres": datos["nombres"],
            "apellidos": datos["apellidos"],
            "codigo": codigo,

            "tipo_proceso": "estudiante",
            "titulo_correo": "Verificación de correo electrónico",
            "mensaje_principal": (
                "Has iniciado tu proceso de registro estudiantil "
                "en el sistema CASRCE."
            ),
            "mensaje_secundario": (
                "Introduce el siguiente código para verificar tu dirección "
                "de correo electrónico y completar tu registro."
            ),
            "vigencia_minutos": 5,
            "aviso_correo": (
                "Si no solicitaste este código, puedes ignorar este mensaje. "
                "No compartas el código con otras personas."
            ),
        }
    )

    html = procesar_html_correo(
        html,
        "Estilos/Email/enviar_codigo.css"
    )

    enviados = send_mail(
        subject="Verificación de correo electrónico - CASRCE",
        message=(
            f"Su código de verificación de CASRCE es: {codigo}. "
            "Vence en 5 minutos."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[datos["correo_electronico"]],
        html_message=html,
        fail_silently=False,
    )

    if enviados != 1:
        raise RuntimeError("No se pudo confirmar el envío del código.")

    return verificacion


# ============================================================
# REGISTRO DE ESTUDIANTES
# ============================================================

def registro_est(request):

    if request.method != "POST":
        return render(
            request,
            "Sesion/Login/registro_estudiantil.html"
        )

    nombres = (request.POST.get("nombres") or "").strip()
    apellidos = (request.POST.get("apellidos") or "").strip()
    nacionalidad = (request.POST.get("nacionalidad") or "").strip()
    num_cedula = (request.POST.get("cedula_identidad") or "").strip()
    nombre_correo = (request.POST.get("correo_electronico") or "").strip()
    dominio = (request.POST.get("dominio") or "").strip()
    prefijo = (request.POST.get("prefijo") or "").strip()
    num_telefono = (request.POST.get("telefono") or "").strip()
    usuario = (request.POST.get("usuario") or "").strip()
    password = request.POST.get("password") or ""

    campos = [
        (nombres, "Nombres", "Por favor, ingrese sus nombres."),
        (apellidos, "Apellidos", "Por favor, ingrese sus apellidos."),
        (nacionalidad, "Nacionalidad", "Por favor, seleccione su nacionalidad."),
        (num_cedula, "Cédula de identidad", "Por favor, ingrese los números de su cédula de identidad."),
        (nombre_correo, "Correo electrónico", "Por favor, ingrese el nombre del correo electrónico."),
        (dominio, "Dominio del correo", "Por favor, seleccione el dominio del correo electrónico."),
        (prefijo, "Prefijo telefónico", "Por favor, seleccione el prefijo telefónico."),
        (num_telefono, "Teléfono", "Por favor, ingrese su número de teléfono."),
        (usuario, "Nombre de usuario", "Por favor, ingrese su nombre de usuario."),
        (password, "Contraseña", "Por favor, ingrese su contraseña."),
    ]

    for valor, titulo, mensaje in campos:
        if not valor:
            return _respuesta_registro(
                "fallo",
                titulo,
                mensaje
            )

    try:
        validar_contrasenia_segura(password)
    except ValidationError as error:
        return _respuesta_registro(
            "fallo",
            "Contraseña insegura",
            error.messages[0],
        )

    correo = f"{nombre_correo}{dominio}".lower()
    cedula = f"{nacionalidad}-{num_cedula}"
    telefono = f"{prefijo}{num_telefono}"

    try:
        validate_email(correo)
    except ValidationError:
        return _respuesta_registro(
            "fallo",
            "Correo inválido",
            "Ingrese una dirección de correo electrónico válida."
        )

    if Usuario.objects.filter(cedula_identidad=cedula).exists():
        return _respuesta_registro(
            "fallo",
            "Cédula registrada",
            "Ya existe un usuario registrado con esta cédula de identidad."
        )

    if Contacto.objects.filter(
        correo_electronico__iexact=correo
    ).exists():
        return _respuesta_registro(
            "fallo",
            "Correo registrado",
            "Ya existe una cuenta asociada a este correo electrónico."
        )

    if Cuenta.objects.filter(usuario__iexact=usuario).exists():
        return _respuesta_registro(
            "fallo",
            "Usuario registrado",
            "Este nombre de usuario ya está en uso."
        )

    if any(
        check_password(password, clave)
        for clave in Cuenta.objects.values_list("clave", flat=True)
    ):
        return _respuesta_registro(
            "fallo",
            "Contraseña no disponible",
            "Por seguridad, seleccione una contraseña diferente a las ya utilizadas."
        )

    datos_pendientes = {
        "nombres": nombres,
        "apellidos": apellidos,
        "cedula_identidad": cedula,
        "correo_electronico": correo,
        "telefono": telefono,
        "usuario": usuario,
        "clave_hash": make_password(password),
    }

    token = str(uuid.uuid4())

    try:
        _enviar_codigo_registro(
            request,
            datos_pendientes,
            token
        )

    except Exception:
        VerificacionCodigo.objects.filter(
            cedula_identidad=cedula,
            token=token,
            descripcion="Registro estudiante",
        ).delete()

        return _respuesta_registro(
            "fallo",
            "No se pudo enviar el código",
            "No fue posible enviar el correo de verificación. Compruebe la configuración del correo e inténtelo nuevamente.",
            icon="error",
        )

    request.session["registro_estudiante_pendiente"] = datos_pendientes
    request.session["token_registro_estudiante"] = token
    request.session.modified = True

    return _respuesta_registro(
        "verificacion_requerida",
        "Verifica tu correo",
        "Enviamos un código de seis dígitos a tu correo electrónico. Tienes cinco minutos para introducirlo.",
        icon="info",
        correo=correo,
        segundos_reenvio=60,
    )


def verificar_codigo_registro(request):

    if request.method != "POST":
        return _respuesta_registro(
            "fallo",
            "Método no permitido",
            "La solicitud no está permitida.",
            icon="error"
        )

    datos = request.session.get("registro_estudiante_pendiente")
    token = request.session.get("token_registro_estudiante")
    codigo = (request.POST.get("codigo") or "").strip()

    if not datos or not token:
        return _respuesta_registro(
            "fallo",
            "Sesión vencida",
            "Vuelve a completar el formulario de registro.",
            icon="error"
        )

    if not codigo or not codigo.isdigit() or len(codigo) != 6:
        return _respuesta_registro(
            "fallo",
            "Código inválido",
            "Introduce el código numérico de seis dígitos."
        )

    verificacion = VerificacionCodigo.objects.filter(
        cedula_identidad=datos["cedula_identidad"],
        token=token,
        descripcion="Registro estudiante",
        activo=1,
    ).first()

    if not verificacion:
        return _respuesta_registro(
            "fallo",
            "Código no disponible",
            "Solicita un nuevo código iniciando nuevamente el registro.",
            icon="error"
        )

    ahora = timezone.now()

    if verificacion.bloqueado_hasta and ahora < verificacion.bloqueado_hasta:
        segundos = max(
            1,
            int((verificacion.bloqueado_hasta - ahora).total_seconds())
        )

        return _respuesta_registro(
            "bloqueado",
            "Verificación bloqueada",
            f"Has superado los intentos permitidos. Inténtalo nuevamente en {ceil(segundos / 60)} minuto(s).",
            icon="error"
        )

    if verificacion.bloqueado_hasta and ahora >= verificacion.bloqueado_hasta:
        verificacion.intentos = 0
        verificacion.bloqueado_hasta = None

    if verificacion.fecha_expiracion and ahora > verificacion.fecha_expiracion:
        verificacion.save(
            update_fields=["intentos", "bloqueado_hasta"]
        )

        return _respuesta_registro(
            "expirado",
            "Código vencido",
            "El código venció. Puedes solicitar otro código."
        )

    if verificacion.codigo != codigo:
        verificacion.intentos += 1

        if verificacion.intentos >= 3:
            verificacion.bloqueado_hasta = ahora + timedelta(minutes=5)

            verificacion.save(
                update_fields=["intentos", "bloqueado_hasta"]
            )

            return _respuesta_registro(
                "bloqueado",
                "Verificación bloqueada",
                "Alcanzaste tres intentos. Inténtalo nuevamente en cinco minutos.",
                icon="error"
            )

        verificacion.save(
            update_fields=["intentos", "bloqueado_hasta"]
        )

        return _respuesta_registro(
            "fallo",
            "Código incorrecto",
            f"El código no coincide. Intentos: {verificacion.intentos}/3."
        )

    try:
        with transaction.atomic():

            if Usuario.objects.filter(
                cedula_identidad=datos["cedula_identidad"]
            ).exists():
                raise ValueError(
                    "Ya existe un usuario registrado con esta cédula."
                )

            if Contacto.objects.filter(
                correo_electronico__iexact=datos["correo_electronico"]
            ).exists():
                raise ValueError(
                    "Ya existe una cuenta asociada a este correo."
                )

            if Cuenta.objects.filter(
                usuario__iexact=datos["usuario"]
            ).exists():
                raise ValueError(
                    "Este nombre de usuario ya está en uso."
                )

            nuevo_usuario = Usuario.objects.create(
                nombres=datos["nombres"],
                apellidos=datos["apellidos"],
                cedula_identidad=datos["cedula_identidad"],
            )

            Contacto.objects.create(
                telefono_personal=datos["telefono"],
                correo_electronico=datos["correo_electronico"],
                id_usuario=nuevo_usuario,
            )

            Cuenta.objects.create(
                usuario=datos["usuario"],
                clave=datos["clave_hash"],
                tipo_cuenta="EST",
                id_usuario=nuevo_usuario,
            )

            Estudiante.objects.create(
                usuario=nuevo_usuario
            )

            _enviar_correo_registro_exitoso(datos)

            verificacion.activo = 0
            verificacion.save(update_fields=["activo"])

    except ValueError as error:
        return _respuesta_registro(
            "fallo",
            "No se pudo completar el registro",
            str(error),
            icon="error"
        )

    except RuntimeError:
        return _respuesta_registro(
            "fallo",
            "No se pudo confirmar el registro",
            "No fue posible enviar el correo de confirmación. No se guardó el registro; inténtalo nuevamente más tarde.",
            icon="error",
        )

    except Exception:
        return _respuesta_registro(
            "fallo",
            "Error al registrar",
            "Ocurrió un error durante el registro. No se completó la operación; inténtalo nuevamente.",
            icon="error",
        )

    request.session.pop("registro_estudiante_pendiente", None)
    request.session.pop("token_registro_estudiante", None)
    request.session.modified = True

    return _respuesta_registro(
        "exito",
        "Registro exitoso",
        "Tu correo fue verificado y los datos del estudiante se registraron correctamente.",
        icon="success"
    )


def reenviar_codigo_registro(request):

    if request.method != "POST":
        return _respuesta_registro(
            "fallo",
            "Método no permitido",
            "La solicitud no está permitida.",
            icon="error"
        )

    datos = request.session.get("registro_estudiante_pendiente")
    token = request.session.get("token_registro_estudiante")

    if not datos or not token:
        return _respuesta_registro(
            "fallo",
            "Sesión vencida",
            "Vuelve a completar el formulario de registro.",
            icon="error"
        )

    verificacion = VerificacionCodigo.objects.filter(
        cedula_identidad=datos["cedula_identidad"],
        token=token,
        descripcion="Registro estudiante",
        activo=1,
    ).first()

    if not verificacion:
        return _respuesta_registro(
            "fallo",
            "Código no disponible",
            "Inicia nuevamente el registro para solicitar otro código.",
            icon="error"
        )

    ahora = timezone.now()

    if verificacion.bloqueado_hasta and ahora < verificacion.bloqueado_hasta:
        segundos = max(
            1,
            int((verificacion.bloqueado_hasta - ahora).total_seconds())
        )

        return _respuesta_registro(
            "bloqueado",
            "Verificación bloqueada",
            f"Espera {ceil(segundos / 60)} minuto(s) antes de continuar.",
            icon="error"
        )

    segundos_desde_envio = (
        ahora - verificacion.creado
    ).total_seconds()

    if segundos_desde_envio < 60:
        restante = max(
            1,
            int(60 - segundos_desde_envio)
        )

        return _respuesta_registro(
            "espera",
            "Espera un momento",
            f"Podrás solicitar otro código en {restante} segundo(s).",
            segundos_reenvio=restante
        )

    try:
        _enviar_codigo_registro(
            request,
            datos,
            token,
            reenviar=True
        )

    except Exception:
        return _respuesta_registro(
            "fallo",
            "No se pudo reenviar",
            "No fue posible enviar otro código. Inténtalo más tarde.",
            icon="error"
        )

    return _respuesta_registro(
        "exito",
        "Código reenviado",
        "Enviamos un nuevo código a tu correo electrónico.",
        icon="success",
        segundos_reenvio=60
    )


# ============================================================
# REGISTRO DE PERSONAL INSTITUCIONAL
# ============================================================

def _es_personal_institucional(usuario):
    """
    Comprueba que el usuario tenga al menos uno de los perfiles
    institucionales autorizados.
    """

    return (
        Docente.objects.filter(usuario=usuario).exists()
        or CoordinadorPNF.objects.filter(usuario=usuario).exists()
        or ControlEstudio.objects.filter(usuario=usuario).exists()
    )


def _correo_enmascarado(correo):
    """Oculta parcialmente el correo electrónico."""

    try:
        nombre, dominio = correo.split("@", 1)

        if len(nombre) <= 2:
            nombre_visible = nombre[0] + "*"
        else:
            nombre_visible = (
                nombre[:2] + "*" * (len(nombre) - 2)
            )

        return f"{nombre_visible}@{dominio}"

    except (ValueError, AttributeError, IndexError):
        return "correo registrado"


def _enviar_codigo_personal(cedula, token, numero_reenvios=0):
    """
    Genera y envía un código de seis dígitos al correo institucional.
    Utiliza la plantilla compartida enviar_codigo.html.
    Vigencia: cinco minutos.
    """

    usuario = Usuario.objects.filter(
        cedula_identidad=cedula
    ).first()

    if not usuario:
        return False, "No se encontró el usuario institucional."

    contacto = Contacto.objects.filter(
        id_usuario=usuario
    ).first()

    if not contacto or not contacto.correo_electronico:
        return False, "El personal no tiene un correo electrónico registrado."

    correo = contacto.correo_electronico.strip()

    try:
        validate_email(correo)
    except ValidationError:
        return False, "El correo institucional registrado no es válido."

    ahora = timezone.now()
    codigo = f"{secrets.randbelow(1_000_000):06d}"

    # Desactivar códigos anteriores de este proceso.
    VerificacionCodigo.objects.filter(
        cedula_identidad=cedula,
        token=token,
        descripcion="Registro personal",
        activo=1
    ).update(activo=0)

    verificacion = VerificacionCodigo.objects.create(
        cedula_identidad=cedula,
        token=token,
        codigo=codigo,
        creado=ahora,
        intentos=0,
        numero_reenvios=numero_reenvios,
        bloqueado_hasta=None,
        activo=1,
        descripcion="Registro personal",
        fecha_expiracion=ahora + timedelta(minutes=5)
    )

    try:
        html = render_to_string(
            "Email/enviar_codigo.html",
            {
                "nombres": usuario.nombres,
                "apellidos": usuario.apellidos,
                "codigo": codigo,

                # Configuración dinámica del correo.
                "tipo_proceso": "personal",
                "titulo_correo": "Verificación de correo electrónico",
                "mensaje_principal": (
                    "Has solicitado completar tu registro de personal "
                    "en el sistema CASRCE."
                ),
                "mensaje_secundario": (
                    "Introduce el siguiente código para verificar tu "
                    "dirección de correo electrónico y continuar con "
                    "la creación de tus credenciales de acceso."
                ),
                "vigencia_minutos": 5,
                "aviso_correo": (
                    "Si no solicitaste este código, puedes ignorar "
                    "este mensaje. No compartas el código con otras personas."
                ),
            }
        )

        html = procesar_html_correo(
            html,
            "Estilos/Email/enviar_codigo.css"
        )

        enviados = send_mail(
            subject="Código de verificación - CASRCE",
            message=(
                f"Hola, {usuario.nombres} {usuario.apellidos}.\n\n"
                "Has solicitado completar tu registro de personal "
                f"en CASRCE. Tu código de verificación es: {codigo}\n\n"
                "Este código vence en cinco minutos. "
                "Si no solicitaste este código, puedes ignorar este mensaje."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[correo],
            html_message=html,
            fail_silently=False
        )

        if enviados != 1:
            raise RuntimeError(
                "El servidor de correo no confirmó el envío."
            )

    except Exception:
        verificacion.activo = 0
        verificacion.save(update_fields=["activo"])

        return False, "No fue posible enviar el correo de verificación."

    return True, correo


def confirmar_reg(request):
    """
    Busca al personal institucional y solicita verificar su correo
    antes de permitir la creación de credenciales.
    """

    if request.method != "POST":
        return render(
            request,
            "Sesion/Login/confirmar_registro_personal.html"
        )

    # Invalidar cualquier proceso anterior de esta sesión.
    for clave in (
        "cedula_personal_pendiente",
        "token_registro_personal",
        "correo_personal_verificado",
        "personal_verificado_hasta",
    ):
        request.session.pop(clave, None)

    nacionalidad = (
        request.POST.get("nacionalidad") or ""
    ).strip().upper()

    numero_cedula = (
        request.POST.get("usuario_ci") or ""
    ).strip()

    if nacionalidad not in ("V", "E"):
        return JsonResponse({
            "estado": "error",
            "title": "Nacionalidad inválida",
            "descripcion": "Selecciona una nacionalidad válida.",
            "icon": "warning"
        })

    if not numero_cedula or not numero_cedula.isdigit():
        return JsonResponse({
            "estado": "error",
            "title": "Cédula inválida",
            "descripcion": "Introduce un número de cédula válido.",
            "icon": "warning"
        })

    cedula = f"{nacionalidad}-{numero_cedula}"

    usuario = Usuario.objects.filter(
        cedula_identidad=cedula
    ).first()

    if not usuario:
        return JsonResponse({
            "estado": "error",
            "title": "Personal no encontrado",
            "descripcion": "No existe un usuario registrado con esos datos.",
            "icon": "error"
        })

    if Estudiante.objects.filter(usuario=usuario).exists():
        return JsonResponse({
            "estado": "error",
            "title": "Registro no permitido",
            "descripcion": "Esta cédula corresponde a un registro estudiantil.",
            "icon": "warning"
        })

    if not _es_personal_institucional(usuario):
        return JsonResponse({
            "estado": "error",
            "title": "Personal no autorizado",
            "descripcion": (
                "No se encontró un perfil de Docente, Coordinador PNF "
                "o Control de Estudio asociado a esta cédula."
            ),
            "icon": "warning"
        })

    if Cuenta.objects.filter(id_usuario=usuario).exists():
        return JsonResponse({
            "estado": "error",
            "title": "Credenciales existentes",
            "descripcion": "Este personal ya posee credenciales de acceso.",
            "icon": "info"
        })

    contacto = Contacto.objects.filter(
        id_usuario=usuario
    ).first()

    if not contacto or not contacto.correo_electronico:
        return JsonResponse({
            "estado": "error",
            "title": "Correo no registrado",
            "descripcion": (
                "No existe un correo electrónico asociado al personal. "
                "El Director General debe registrar sus datos de contacto."
            ),
            "icon": "warning"
        })

    token = str(uuid.uuid4())

    enviado, resultado = _enviar_codigo_personal(
        cedula,
        token
    )

    if not enviado:
        return JsonResponse({
            "estado": "error",
            "title": "No se pudo enviar el código",
            "descripcion": resultado,
            "icon": "error"
        })

    request.session["cedula_personal_pendiente"] = cedula
    request.session["token_registro_personal"] = token
    request.session.modified = True

    return JsonResponse({
        "estado": "verificacion_requerida",
        "title": "Verifica tu correo",
        "descripcion": (
            f"Enviamos un código de verificación a "
            f"{_correo_enmascarado(resultado)}."
        ),
        "correo": _correo_enmascarado(resultado),
        "segundos_reenvio": 60,
        "icon": "success"
    })


def verificar_codigo_personal(request):
    """
    Verifica el código enviado al correo institucional.
    Después de verificarlo, concede diez minutos para crear
    las credenciales de acceso.
    """

    if request.method != "POST":
        return JsonResponse({
            "estado": "error",
            "title": "Solicitud inválida",
            "descripcion": "Método no permitido.",
            "icon": "warning"
        }, status=405)

    cedula = request.session.get("cedula_personal_pendiente")
    token = request.session.get("token_registro_personal")
    codigo = (request.POST.get("codigo") or "").strip()

    if not cedula or not token:
        return JsonResponse({
            "estado": "error",
            "title": "Proceso vencido",
            "descripcion": "Debes iniciar nuevamente la verificación.",
            "icon": "warning"
        })

    if len(codigo) != 6 or not codigo.isdigit():
        return JsonResponse({
            "estado": "error",
            "title": "Código inválido",
            "descripcion": "Introduce el código numérico de seis dígitos.",
            "icon": "warning"
        })

    registro = VerificacionCodigo.objects.filter(
        cedula_identidad=cedula,
        token=token,
        descripcion="Registro personal",
        activo=1
    ).order_by("-creado").first()

    if not registro:
        return JsonResponse({
            "estado": "error",
            "title": "Código no disponible",
            "descripcion": "Solicita un nuevo código de verificación.",
            "icon": "warning"
        })

    ahora = timezone.now()

    if registro.bloqueado_hasta and ahora < registro.bloqueado_hasta:
        segundos = max(
            1,
            ceil((registro.bloqueado_hasta - ahora).total_seconds())
        )

        return JsonResponse({
            "estado": "bloqueado",
            "title": "Verificación bloqueada",
            "descripcion": (
                f"Has superado el límite de intentos. "
                f"Intenta nuevamente en {segundos} segundos."
            ),
            "segundos": segundos,
            "icon": "warning"
        })

    # Restablecer los intentos si el bloqueo anterior ya terminó.
    if registro.bloqueado_hasta and ahora >= registro.bloqueado_hasta:
        registro.intentos = 0
        registro.bloqueado_hasta = None

    if registro.fecha_expiracion and ahora > registro.fecha_expiracion:
        registro.activo = 0
        registro.save(update_fields=["activo"])

        return JsonResponse({
            "estado": "expirado",
            "title": "Código vencido",
            "descripcion": "Solicita un nuevo código para continuar.",
            "icon": "warning"
        })

    if registro.codigo != codigo:
        registro.intentos += 1

        if registro.intentos >= 3:
            registro.bloqueado_hasta = ahora + timedelta(minutes=5)

            registro.save(update_fields=[
                "intentos",
                "bloqueado_hasta"
            ])

            return JsonResponse({
                "estado": "bloqueado",
                "title": "Demasiados intentos",
                "descripcion": (
                    "Has introducido el código incorrectamente tres veces. "
                    "El proceso estará bloqueado durante cinco minutos."
                ),
                "segundos": 300,
                "icon": "error"
            })

        registro.save(update_fields=[
            "intentos",
            "bloqueado_hasta"
        ])

        return JsonResponse({
            "estado": "error",
            "title": "Código incorrecto",
            "descripcion": (
                f"El código no coincide. "
                f"Te quedan {3 - registro.intentos} intentos."
            ),
            "intentos_restantes": 3 - registro.intentos,
            "icon": "warning"
        })

    # Código correcto: desactivar el código utilizado.
    registro.activo = 0
    registro.save(update_fields=["activo"])

    request.session["correo_personal_verificado"] = token

    # Conceder diez minutos desde la verificación exitosa.
    request.session["personal_verificado_hasta"] = int(
        (ahora + timedelta(minutes=10)).timestamp()
    )

    request.session.modified = True

    # IMPORTANTE: el JavaScript espera estado="exito".
    return JsonResponse({
        "estado": "exito",
        "title": "Correo verificado",
        "descripcion": (
            "La dirección de correo fue validada correctamente. "
            "Ya puedes crear tus credenciales de acceso."
        ),
        "icon": "success"
    })


def reenviar_codigo_personal(request):
    """Permite reenviar el código respetando el tiempo de espera."""

    if request.method != "POST":
        return JsonResponse({
            "estado": "error",
            "title": "Solicitud inválida",
            "descripcion": "Método no permitido.",
            "icon": "warning"
        }, status=405)

    cedula = request.session.get("cedula_personal_pendiente")
    token = request.session.get("token_registro_personal")

    if not cedula or not token:
        return JsonResponse({
            "estado": "error",
            "title": "Proceso vencido",
            "descripcion": "Debes iniciar nuevamente el registro.",
            "icon": "warning"
        })

    if request.session.get("correo_personal_verificado") == token:
        return JsonResponse({
            "estado": "error",
            "title": "Correo ya verificado",
            "descripcion": (
                "El correo ya fue verificado. "
                "Continúa con la creación de tus credenciales."
            ),
            "icon": "info"
        })

    registro = VerificacionCodigo.objects.filter(
        cedula_identidad=cedula,
        token=token,
        descripcion="Registro personal",
        activo=1
    ).order_by("-creado").first()

    if not registro:
        return JsonResponse({
            "estado": "error",
            "title": "Código no disponible",
            "descripcion": "Inicia nuevamente el proceso de verificación.",
            "icon": "warning"
        })

    ahora = timezone.now()

    if registro.bloqueado_hasta and ahora < registro.bloqueado_hasta:
        segundos = max(
            1,
            ceil((registro.bloqueado_hasta - ahora).total_seconds())
        )

        return JsonResponse({
            "estado": "bloqueado",
            "title": "Proceso bloqueado",
            "descripcion": f"Intenta nuevamente en {segundos} segundos.",
            "segundos": segundos,
            "icon": "warning"
        })

    segundos_transcurridos = (
        ahora - registro.creado
    ).total_seconds()

    if segundos_transcurridos < 60:
        restantes = max(
            1,
            ceil(60 - segundos_transcurridos)
        )

        return JsonResponse({
            "estado": "espera",
            "title": "Espera un momento",
            "descripcion": (
                f"Podrás solicitar otro código dentro de {restantes} segundos."
            ),
            "segundos_reenvio": restantes,
            "icon": "info"
        })

    enviado, resultado = _enviar_codigo_personal(
        cedula,
        token,
        numero_reenvios=registro.numero_reenvios + 1
    )

    if not enviado:
        return JsonResponse({
            "estado": "error",
            "title": "No se pudo reenviar",
            "descripcion": resultado,
            "icon": "error"
        })

    return JsonResponse({
        "estado": "exito",
        "title": "Código reenviado",
        "descripcion": (
            f"Enviamos un nuevo código a "
            f"{_correo_enmascarado(resultado)}."
        ),
        "correo": _correo_enmascarado(resultado),
        "segundos_reenvio": 60,
        "icon": "success"
    })

# ============================================================
# CORREO DE REGISTRO EXITOSO DEL PERSONAL
# ============================================================

def _enviar_correo_registro_personal(usuario, nombre_usuario):
    """
    Envía al personal un correo de confirmación después
    de crear correctamente sus credenciales de acceso.
    """

    contacto = Contacto.objects.filter(
        id_usuario=usuario
    ).first()

    if not contacto or not contacto.correo_electronico:
        raise RuntimeError(
            "El personal no tiene un correo electrónico registrado."
        )

    correo = contacto.correo_electronico.strip()

    try:
        validate_email(correo)
    except ValidationError as error:
        raise RuntimeError(
            "El correo electrónico del personal no es válido."
        ) from error

    html = render_to_string(
        "Email/registro_exitoso.html",
        {
            "nombres": usuario.nombres,
            "apellidos": usuario.apellidos,
            "nombre_usuario": nombre_usuario,
        },
    )

    html = procesar_html_correo(
        html,
        "Estilos/Email/registro_exitoso.css",
    )

    try:
        enviados = send_mail(
            subject="¡Tus credenciales de CASRCE están listas!",
            message=(
                f"Hola, {usuario.nombres} {usuario.apellidos}.\n\n"
                "Tu registro de personal en CASRCE se completó correctamente.\n\n"
                f"Tu nombre de usuario es: {nombre_usuario}\n\n"
                "Ya puedes ingresar al sistema utilizando tus nuevas "
                "credenciales de acceso."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[correo],
            html_message=html,
            fail_silently=False,
        )

        if enviados != 1:
            raise RuntimeError(
                "El servidor de correo no confirmó el envío."
            )

    except Exception as error:
        raise RuntimeError(
            "No fue posible enviar el correo de confirmación."
        ) from error


def guardar_cred(request):
    """
    Crea las credenciales de acceso del personal institucional
    únicamente después de verificar el correo.
    """

    if request.method != "POST":
        return JsonResponse({
            "estado": "error",
            "title": "Solicitud inválida",
            "descripcion": "Método no permitido.",
            "icon": "warning"
        }, status=405)

    cedula = request.session.get("cedula_personal_pendiente")
    token = request.session.get("token_registro_personal")
    token_verificado = request.session.get("correo_personal_verificado")

    verificado_hasta = request.session.get(
        "personal_verificado_hasta",
        0
    )

    ahora = timezone.now()

    # Comprobar la autorización de diez minutos.
    if (
        not cedula
        or not token
        or token != token_verificado
        or ahora.timestamp() > verificado_hasta
    ):
        request.session.pop("correo_personal_verificado", None)
        request.session.pop("personal_verificado_hasta", None)

        return JsonResponse({
            "estado": "error",
            "title": "Verificación vencida",
            "descripcion": (
                "Debes verificar nuevamente tu correo electrónico "
                "antes de crear tus credenciales."
            ),
            "icon": "warning"
        })

    nombre_usuario = (
        request.POST.get("nombre_usuario") or ""
    ).strip()

    contrasenia = (
        request.POST.get("password_usuario")
        or request.POST.get("password")
        or ""
    )

    if not nombre_usuario or not contrasenia:
        return JsonResponse({
            "estado": "error",
            "title": "Datos incompletos",
            "descripcion": "Debes completar el usuario y la contraseña.",
            "icon": "warning"
        })

    try:
        validar_contrasenia_segura(contrasenia)
    except ValidationError as error:
        return JsonResponse({
            "estado": "error",
            "title": "Contraseña insegura",
            "descripcion": error.messages[0],
            "icon": "warning"
        })

    # Confirmar que existe un registro de verificación completado.
    verificacion = VerificacionCodigo.objects.filter(
        cedula_identidad=cedula,
        token=token,
        descripcion="Registro personal",
        activo=0
    ).order_by("-creado").first()

    if not verificacion:
        return JsonResponse({
            "estado": "error",
            "title": "Verificación no encontrada",
            "descripcion": "No se encontró una verificación válida para este registro.",
            "icon": "warning"
        })

    try:
        with transaction.atomic():

            usuario = Usuario.objects.select_for_update().filter(
                cedula_identidad=cedula
            ).first()

            if not usuario:
                return JsonResponse({
                    "estado": "error",
                    "title": "Usuario no encontrado",
                    "descripcion": "No se encontró el registro de personal.",
                    "icon": "error"
                })

            if Estudiante.objects.filter(usuario=usuario).exists():
                return JsonResponse({
                    "estado": "error",
                    "title": "Registro no permitido",
                    "descripcion": "Esta cédula corresponde a un estudiante.",
                    "icon": "warning"
                })

            if not _es_personal_institucional(usuario):
                return JsonResponse({
                    "estado": "error",
                    "title": "Personal no autorizado",
                    "descripcion": (
                        "El usuario no posee un perfil institucional "
                        "autorizado para crear credenciales."
                    ),
                    "icon": "warning"
                })

            if Cuenta.objects.filter(id_usuario=usuario).exists():
                return JsonResponse({
                    "estado": "error",
                    "title": "Credenciales existentes",
                    "descripcion": "Este personal ya posee una cuenta de acceso.",
                    "icon": "warning"
                })

            if Cuenta.objects.filter(
                usuario__iexact=nombre_usuario
            ).exists():
                return JsonResponse({
                    "estado": "error",
                    "title": "Usuario no disponible",
                    "descripcion": "El nombre de usuario ya está siendo utilizado.",
                    "icon": "warning"
                })

            Cuenta.objects.create(
                usuario=nombre_usuario,
                clave=make_password(contrasenia),
                tipo_cuenta="ADMIN",
                id_usuario=usuario
            )

        # Limpiar la sesión después de crear correctamente la cuenta.
        for clave in (
            "cedula_personal_pendiente",
            "token_registro_personal",
            "correo_personal_verificado",
            "personal_verificado_hasta",
        ):
            request.session.pop(clave, None)

        request.session.modified = True

        return JsonResponse({
            "estado": "exito",
            "title": "Registro completado",
            "descripcion": (
                "Las credenciales del personal fueron creadas "
                "correctamente. Ya puedes iniciar sesión."
            ),
            "icon": "success"
        })

    except Exception:
        return JsonResponse({
            "estado": "error",
            "title": "Error al registrar",
            "descripcion": (
                "Ocurrió un problema al crear las credenciales. "
                "Inténtalo nuevamente."
            ),
            "icon": "error"
        }, status=500)
