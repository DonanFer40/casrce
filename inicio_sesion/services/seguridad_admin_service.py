
import hashlib
import logging
import secrets

from datetime import timedelta

import pyotp

from cryptography.fernet import Fernet, InvalidToken

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password, check_password
from django.core.exceptions import ImproperlyConfigured
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone

from inicio_sesion.models import (
    ConfiguracionSeguridadAdmin,
    VerificacionAccesoAdmin,
)


logger = logging.getLogger(__name__)

User = get_user_model()


# ==========================================================
# CONFIGURACIÓN GENERAL
# ==========================================================

DURACION_CODIGO_CORREO = 5
DURACION_SESION_ADMIN = 15
INTERVALO_REENVIO_CORREO = 60

MAX_INTENTOS_CORREO = 5
MAX_INTENTOS_TOTP = 5

DURACION_BLOQUEO = 5

SESION_TOKEN = "admin_gate_token"
SESION_AUTORIZADO = "admin_gate_autorizado"
SESION_USUARIO = "admin_gate_usuario"


# ==========================================================
# SUPERUSUARIO AUTORIZADO
# ==========================================================

def obtener_superusuario_autorizado():

    nombre_usuario = getattr(
        settings,
        "CASRCE_ADMIN_USERNAME",
        None
    )

    if not nombre_usuario:
        raise ImproperlyConfigured(
            "Debes configurar CASRCE_ADMIN_USERNAME."
        )

    try:

        usuario = User.objects.get(
            **{
                User.USERNAME_FIELD: nombre_usuario
            }
        )

    except User.DoesNotExist:

        raise ImproperlyConfigured(
            "No existe el superusuario administrativo configurado."
        )

    if not (
        usuario.is_active
        and usuario.is_staff
        and usuario.is_superuser
    ):

        raise ImproperlyConfigured(
            "La cuenta administrativa no cumple los requisitos de seguridad."
        )

    if not usuario.email:

        raise ImproperlyConfigured(
            "El superusuario no tiene un correo electrónico configurado."
        )

    return usuario


# ==========================================================
# VALIDACIÓN DE CREDENCIALES DE LA PUERTA ADMINISTRATIVA
# ==========================================================

def validar_credenciales_puerta(usuario_ingresado, contrasenia):

    usuario_configurado = getattr(
        settings,
        "CASRCE_ADMIN_GATE_USERNAME",
        ""
    )

    hash_configurado = getattr(
        settings,
        "CASRCE_ADMIN_GATE_PASSWORD_HASH",
        ""
    )

    if not usuario_configurado or not hash_configurado:

        raise ImproperlyConfigured(
            "Las credenciales de acceso administrativo no están configuradas."
        )

    usuario_ingresado = str(usuario_ingresado).strip()
    contrasenia = str(contrasenia)

    try:

        usuario_valido = secrets.compare_digest(
            usuario_ingresado,
            usuario_configurado
        )

        contrasenia_valida = check_password(
            contrasenia,
            hash_configurado
        )

    except Exception:

        logger.exception(
            "Error validando las credenciales de acceso administrativo."
        )

        return False

    return usuario_valido and contrasenia_valida


# ==========================================================
# CIFRADO DEL SECRETO TOTP
# ==========================================================

def obtener_cifrador():

    clave = getattr(
        settings,
        "CASRCE_ADMIN_FERNET_KEY",
        None
    )

    if not clave:

        raise ImproperlyConfigured(
            "Debes configurar CASRCE_ADMIN_FERNET_KEY."
        )

    try:

        if isinstance(clave, str):
            clave = clave.encode("utf-8")

        return Fernet(clave)

    except (ValueError, TypeError) as error:

        raise ImproperlyConfigured(
            "La clave Fernet de CASRCE no es válida."
        ) from error


def cifrar_secreto_totp(secreto):

    return obtener_cifrador().encrypt(
        secreto.encode("utf-8")
    ).decode("utf-8")


def descifrar_secreto_totp(secreto_cifrado):

    if not secreto_cifrado:

        raise ValueError(
            "No existe un secreto TOTP configurado."
        )

    try:

        return obtener_cifrador().decrypt(
            secreto_cifrado.encode("utf-8")
        ).decode("utf-8")

    except (InvalidToken, ValueError, TypeError) as error:

        raise ValueError(
            "No se pudo descifrar el secreto TOTP."
        ) from error


# ==========================================================
# CONFIGURACIÓN DE GOOGLE AUTHENTICATOR / AEGIS
# ==========================================================

def preparar_totp():

    usuario = obtener_superusuario_autorizado()

    with transaction.atomic():

        configuracion, _ = (
            ConfiguracionSeguridadAdmin.objects
            .select_for_update()
            .get_or_create(
                usuario=usuario
            )
        )

        if configuracion.totp_activo:

            raise ValueError(
                "La autenticación TOTP ya está configurada."
            )

        # Reutilizar un secreto pendiente de confirmación.
        if configuracion.secreto_totp_cifrado:

            try:

                secreto = descifrar_secreto_totp(
                    configuracion.secreto_totp_cifrado
                )

            except ValueError:

                secreto = pyotp.random_base32()

                configuracion.secreto_totp_cifrado = (
                    cifrar_secreto_totp(secreto)
                )

        else:

            secreto = pyotp.random_base32()

            configuracion.secreto_totp_cifrado = (
                cifrar_secreto_totp(secreto)
            )

        configuracion.ultimo_uso_totp = None

        configuracion.save(
            update_fields=[
                "secreto_totp_cifrado",
                "ultimo_uso_totp",
                "actualizado",
            ]
        )

    aplicacion = pyotp.TOTP(secreto)

    return aplicacion.provisioning_uri(
        name=usuario.email,
        issuer_name="CASRCE"
    )


def confirmar_configuracion_totp(codigo):

    usuario = obtener_superusuario_autorizado()

    codigo = str(codigo).strip()

    if not codigo.isdigit() or len(codigo) != 6:
        return False

    with transaction.atomic():

        configuracion = (
            ConfiguracionSeguridadAdmin.objects
            .select_for_update()
            .filter(
                usuario=usuario
            )
            .first()
        )

        if not configuracion or configuracion.totp_activo:
            return False

        try:

            secreto = descifrar_secreto_totp(
                configuracion.secreto_totp_cifrado
            )

        except ValueError:

            logger.exception(
                "Error recuperando el secreto TOTP administrativo."
            )

            return False

        totp = pyotp.TOTP(secreto)

        ahora = timezone.now()

        contador_actual = totp.timecode(ahora)

        contador_aceptado = None

        for desplazamiento in (-1, 0, 1):

            contador = contador_actual + desplazamiento

            if contador < 0:
                continue

            codigo_generado = totp.at(
                contador * totp.interval
            )

            if secrets.compare_digest(
                codigo_generado,
                codigo
            ):

                contador_aceptado = contador
                break

        if contador_aceptado is None:
            return False

        configuracion.totp_activo = True

        configuracion.ultimo_uso_totp = contador_aceptado

        configuracion.save(
            update_fields=[
                "totp_activo",
                "ultimo_uso_totp",
                "actualizado",
            ]
        )

    return True


# ==========================================================
# IDENTIFICADOR Y VIGENCIA DE SESIÓN
# ==========================================================

def obtener_hash_sesion(token):

    return hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()


def invalidar_registro(verificacion):

    if not verificacion:
        return

    verificacion.activo = False
    verificacion.etapa = "INVALIDADO"

    verificacion.save(
        update_fields=[
            "activo",
            "etapa",
            "actualizado",
        ]
    )


def comprobar_vigencia(verificacion, ahora=None):

    if not verificacion:
        return False

    ahora = ahora or timezone.now()

    limite = (
        verificacion.creado
        + timedelta(minutes=DURACION_SESION_ADMIN)
    )

    if ahora >= limite:

        invalidar_registro(verificacion)

        return False

    return True


def obtener_verificacion_activa(request):

    token = request.session.get(SESION_TOKEN)

    if not token:
        return None

    try:

        verificacion = (
            VerificacionAccesoAdmin.objects
            .select_related("usuario")
            .get(
                token_sesion_hash=obtener_hash_sesion(token),
                activo=True,
            )
        )

    except VerificacionAccesoAdmin.DoesNotExist:
        return None

    if not comprobar_vigencia(verificacion):
        return None

    return verificacion


def obtener_verificacion_bloqueada(request, etapas=None):

    token = request.session.get(SESION_TOKEN)

    if not token:
        return None

    consulta = (
        VerificacionAccesoAdmin.objects
        .select_for_update()
        .select_related("usuario")
        .filter(
            token_sesion_hash=obtener_hash_sesion(token),
            activo=True,
        )
    )

    if etapas:
        consulta = consulta.filter(etapa__in=etapas)

    verificacion = consulta.first()

    if not verificacion:
        return None

    if not comprobar_vigencia(verificacion):

        request.session.pop(SESION_TOKEN, None)
        request.session.pop(SESION_AUTORIZADO, None)
        request.session.pop(SESION_USUARIO, None)

        return None

    # La verificación debe pertenecer al superusuario configurado.
    usuario_autorizado = obtener_superusuario_autorizado()

    if verificacion.usuario_id != usuario_autorizado.pk:

        invalidar_registro(verificacion)

        return None

    return verificacion


# ==========================================================
# GENERACIÓN Y ENVÍO DEL CÓDIGO POR CORREO
# ==========================================================

def generar_codigo_correo():

    return str(
        secrets.randbelow(900000) + 100000
    )


def enviar_codigo_correo(usuario, codigo):

    asunto = "Código de seguridad administrativa - CASRCE"

    mensaje = (
        "Se ha solicitado un acceso al panel administrativo "
        "de CASRCE.\n\n"
        f"Tu código de verificación es: {codigo}\n\n"
        f"Este código vence en {DURACION_CODIGO_CORREO} minutos.\n\n"
        "Si no has solicitado este acceso, ignora este mensaje."
    )

    return send_mail(
        subject=asunto,
        message=mensaje,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[usuario.email],
        fail_silently=False,
    )


# ==========================================================
# INICIAR VERIFICACIÓN ADMINISTRATIVA
# ==========================================================

def iniciar_verificacion_admin(
    request,
    usuario_ingresado,
    contrasenia
):

    if not validar_credenciales_puerta(
        usuario_ingresado,
        contrasenia
    ):

        return False, "Credenciales administrativas incorrectas."

    usuario = obtener_superusuario_autorizado()

    configuracion = (
        ConfiguracionSeguridadAdmin.objects
        .filter(
            usuario=usuario,
            totp_activo=True,
        )
        .first()
    )

    if not configuracion:

        return False, (
            "Primero debes configurar y activar la autenticación TOTP."
        )

    token = secrets.token_urlsafe(48)

    codigo = generar_codigo_correo()

    ahora = timezone.now()

    with transaction.atomic():

        VerificacionAccesoAdmin.objects.filter(
            usuario=usuario,
            activo=True,
        ).update(
            activo=False,
            etapa="INVALIDADO",
        )

        verificacion = VerificacionAccesoAdmin.objects.create(
            usuario=usuario,
            token_sesion_hash=obtener_hash_sesion(token),
            etapa="CORREO",
            codigo_correo_hash=make_password(codigo),
            fecha_expiracion_codigo=(
                ahora + timedelta(minutes=DURACION_CODIGO_CORREO)
            ),
            ultimo_envio_codigo=ahora,
        )

        try:

            enviar_codigo_correo(
                usuario,
                codigo
            )

        except Exception:

            logger.exception(
                "No se pudo enviar el código de acceso administrativo."
            )

            invalidar_registro(verificacion)

            raise

    # Rotar la clave de sesión antes de guardar el nuevo token.
    request.session.cycle_key()

    request.session[SESION_TOKEN] = token
    request.session[SESION_AUTORIZADO] = False

    request.session.pop(
        SESION_USUARIO,
        None
    )

    request.session.set_expiry(
        DURACION_SESION_ADMIN * 60
    )

    return True, "Código de seguridad enviado correctamente."


# ==========================================================
# REENVÍO DEL CÓDIGO DE CORREO
# ==========================================================

def reenviar_codigo_correo(request):

    with transaction.atomic():

        verificacion = obtener_verificacion_bloqueada(
            request,
            etapas=["CORREO"]
        )

        if not verificacion:

            return False, "La verificación ya no está disponible."

        ahora = timezone.now()

        if (
            verificacion.bloqueado_hasta
            and ahora < verificacion.bloqueado_hasta
        ):

            return False, "El acceso está temporalmente bloqueado."

        if verificacion.ultimo_envio_codigo:

            espera = (
                verificacion.ultimo_envio_codigo
                + timedelta(seconds=INTERVALO_REENVIO_CORREO)
            )

            if ahora < espera:

                segundos = int(
                    (espera - ahora).total_seconds()
                )

                return False, (
                    f"Debes esperar {segundos} segundos antes de solicitar otro código."
                )

        codigo = generar_codigo_correo()

        # Enviar antes de sustituir el código anterior.
        # Si falla el correo, la transacción no guarda los cambios.
        try:

            enviar_codigo_correo(
                verificacion.usuario,
                codigo
            )

        except Exception:

            logger.exception(
                "Error reenviando el código administrativo."
            )

            raise

        verificacion.codigo_correo_hash = make_password(codigo)

        verificacion.fecha_expiracion_codigo = (
            ahora + timedelta(minutes=DURACION_CODIGO_CORREO)
        )

        verificacion.ultimo_envio_codigo = ahora

        verificacion.save(
            update_fields=[
                "codigo_correo_hash",
                "fecha_expiracion_codigo",
                "ultimo_envio_codigo",
                "actualizado",
            ]
        )

    return True, "Código enviado correctamente."


# ==========================================================
# VALIDACIÓN DEL CÓDIGO DE CORREO
# ==========================================================

def verificar_codigo_correo(request, codigo):

    codigo = str(codigo).strip()

    if not codigo.isdigit() or len(codigo) != 6:

        return False, "Introduce un código de seis dígitos."

    with transaction.atomic():

        verificacion = obtener_verificacion_bloqueada(
            request,
            etapas=["CORREO"]
        )

        if not verificacion:

            return False, "No existe una verificación activa."

        ahora = timezone.now()

        if (
            verificacion.bloqueado_hasta
            and ahora < verificacion.bloqueado_hasta
        ):

            return False, "Demasiados intentos. Inténtalo más tarde."

        if (
            not verificacion.fecha_expiracion_codigo
            or ahora >= verificacion.fecha_expiracion_codigo
        ):

            return False, "El código ha expirado. Solicita uno nuevo."

        if not check_password(
            codigo,
            verificacion.codigo_correo_hash
        ):

            verificacion.intentos_correo += 1

            if verificacion.intentos_correo >= MAX_INTENTOS_CORREO:

                verificacion.bloqueado_hasta = (
                    ahora + timedelta(minutes=DURACION_BLOQUEO)
                )

            verificacion.save(
                update_fields=[
                    "intentos_correo",
                    "bloqueado_hasta",
                    "actualizado",
                ]
            )

            return False, "El código ingresado es incorrecto."

        verificacion.correo_verificado = True
        verificacion.codigo_correo_hash = ""
        verificacion.fecha_expiracion_codigo = None
        verificacion.etapa = "TOTP"

        verificacion.save(
            update_fields=[
                "correo_verificado",
                "codigo_correo_hash",
                "fecha_expiracion_codigo",
                "etapa",
                "actualizado",
            ]
        )

    return True, "Correo verificado correctamente."


# ==========================================================
# VALIDACIÓN TOTP
# ==========================================================

def verificar_codigo_totp(request, codigo):

    codigo = str(codigo).strip()

    if not codigo.isdigit() or len(codigo) != 6:

        return False, "Introduce un código TOTP de seis dígitos."

    with transaction.atomic():

        verificacion = obtener_verificacion_bloqueada(
            request,
            etapas=["TOTP"]
        )

        if not verificacion or not verificacion.correo_verificado:

            return False, "Debes verificar primero tu correo."

        ahora = timezone.now()

        if (
            verificacion.bloqueado_hasta
            and ahora < verificacion.bloqueado_hasta
        ):

            return False, "Demasiados intentos. Inténtalo más tarde."

        configuracion = (
            ConfiguracionSeguridadAdmin.objects
            .select_for_update()
            .filter(
                usuario=verificacion.usuario,
                totp_activo=True,
            )
            .first()
        )

        if not configuracion:

            return False, "La autenticación TOTP no está configurada."

        try:

            secreto = descifrar_secreto_totp(
                configuracion.secreto_totp_cifrado
            )

            totp = pyotp.TOTP(secreto)

        except ValueError:

            logger.exception(
                "No se pudo recuperar el secreto TOTP administrativo."
            )

            return False, "No se pudo validar el autenticador."

        contador_actual = totp.timecode(ahora)

        contador_aceptado = None

        # Tolerancia de un intervalo anterior y uno posterior.
        for desplazamiento in (-1, 0, 1):

            contador = contador_actual + desplazamiento

            if contador < 0:
                continue

            codigo_generado = totp.at(
                contador * totp.interval
            )

            if secrets.compare_digest(
                codigo_generado,
                codigo
            ):

                contador_aceptado = contador
                break

        codigo_no_reutilizado = (
            contador_aceptado is not None
            and (
                configuracion.ultimo_uso_totp is None
                or contador_aceptado > configuracion.ultimo_uso_totp
            )
        )

        if not codigo_no_reutilizado:

            verificacion.intentos_totp += 1

            if verificacion.intentos_totp >= MAX_INTENTOS_TOTP:

                verificacion.bloqueado_hasta = (
                    ahora + timedelta(minutes=DURACION_BLOQUEO)
                )

            verificacion.save(
                update_fields=[
                    "intentos_totp",
                    "bloqueado_hasta",
                    "actualizado",
                ]
            )

            return False, (
                "El código TOTP es incorrecto o ya fue utilizado."
            )

        # Registrar el contador aceptado para impedir su reutilización.
        configuracion.ultimo_uso_totp = contador_aceptado

        configuracion.save(
            update_fields=[
                "ultimo_uso_totp",
                "actualizado",
            ]
        )

        verificacion.totp_verificado = True
        verificacion.etapa = "COMPLETADO"
        verificacion.completado = ahora

        verificacion.save(
            update_fields=[
                "totp_verificado",
                "etapa",
                "completado",
                "actualizado",
            ]
        )

    # Mantener el registro activo para que el middleware
    # pueda comprobar la autorización.
    request.session.cycle_key()

    request.session[SESION_AUTORIZADO] = True
    request.session[SESION_USUARIO] = verificacion.usuario_id

    request.session.set_expiry(
        DURACION_SESION_ADMIN * 60
    )

    return True, "Autenticación administrativa completada."


# ==========================================================
# INVALIDAR ACCESO ADMINISTRATIVO
# ==========================================================

def invalidar_verificacion_admin(request):

    token = request.session.get(SESION_TOKEN)

    if token:

        with transaction.atomic():

            verificacion = (
                VerificacionAccesoAdmin.objects
                .select_for_update()
                .filter(
                    token_sesion_hash=obtener_hash_sesion(token),
                    activo=True,
                )
                .first()
            )

            if verificacion:

                invalidar_registro(verificacion)

    request.session.pop(
        SESION_TOKEN,
        None
    )

    request.session.pop(
        SESION_AUTORIZADO,
        None
    )

    request.session.pop(
        SESION_USUARIO,
        None
    )

    return True
