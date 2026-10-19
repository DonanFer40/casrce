from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import JsonResponse
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
from django.template.loader import render_to_string
from django.contrib import messages
from django.conf import settings
from inicio_sesion.services.correos import procesar_html_correo
from django.views.decorators.cache import never_cache

from inicio_sesion.models import Usuario, Contacto, VerificacionCodigo, Cuenta

import secrets, string, json, uuid
from math import ceil

# Verificado

def bus_usr(request):
    if request.method == "POST":
        nacionalidad = request.POST.get("nacionalidad")
        num_cedula = request.POST.get("cedula")

        if not nacionalidad:
            return JsonResponse({
                "estado": "fallo",
                "title": "Vacío",
                "icon": "warning",
                "descripcion": "Por favor, selecciona la nacionalidad."
            })
        
        if not num_cedula:
            return JsonResponse({
                "estado": "fallo",
                "title": "Vacío",
                "icon": "warning",
                "descripcion": "Por favor, ingresa los números para la cédula de identidad."
            })

        cedula_identidad = nacionalidad + "-" + num_cedula
        
        # Usamos .filter().first() para evitar excepciones no controladas
        usuario = Usuario.objects.filter(cedula_identidad=cedula_identidad).first()
        
        if not usuario:
            return JsonResponse({
                "estado": "fallo",
                "title": "No encontrado",
                "icon": "warning",  # Cambiado a warning para que sea una advertencia amigable
                "descripcion": "El número de cédula ingresado no se encuentra registrado."
            })
        
        # Guardar en sesión si el usuario sí existe
        request.session['cedula_usuario'] = cedula_identidad
        request.session['flujo_verificacion'] = True
        request.session['token_recuperacion'] = str(uuid.uuid4())
        request.session.modified = True

        return JsonResponse({"estado": "exito"})
        
    return render(request, 'Sesion/Recuperar Credenciales/buscar_usuario.html')

def exist_cod(request):
    cedula_usuario = request.session.get("cedula_usuario")

    if not cedula_usuario:
        return JsonResponse({
            "estado": "no_exite",
            "title": "Verificación requerida",
            "icon": "warning",
            "descripcion": "No se encontró una sesión de recuperación activa."
        })

    usuario = Usuario.objects.filter(
        cedula_identidad=cedula_usuario
    ).first()

    if not usuario:
        return JsonResponse({
            "estado": "no_exite",
            "title": "Usuario no encontrado",
            "icon": "warning",
            "descripcion": "No se encontró el usuario solicitado."
        })

    token_sesion = request.session.get("token_recuperacion")

    verificacion = VerificacionCodigo.objects.filter(
        cedula_identidad=usuario.cedula_identidad,
        token=token_sesion,
        activo=1
    ).first()

    if not verificacion:
        return JsonResponse({
            "estado": "no_exite",
            "title": "Código no encontrado",
            "icon": "info",
            "descripcion": "Solicita un código para continuar."
        })

    ahora = timezone.now()

    if verificacion.fecha_expiracion <= ahora:
        return JsonResponse({
            "estado": "expirado",
            "title": "Código expirado",
            "icon": "warning",
            "descripcion": "El código ha expirado. Puedes solicitar uno nuevo."
        })

    fecha_reenvio = verificacion.creado + timedelta(seconds=60)

    return JsonResponse({
        "estado": "vigente",
        "title": "Código vigente",
        "icon": "info",
        "descripcion": "Tu código continúa vigente.",
        "fecha_expiracion": verificacion.fecha_expiracion.isoformat(),
        "fecha_reenvio": fecha_reenvio.isoformat(),
        "numero_reenvios": verificacion.numero_reenvios,
    })

def corr_reg(request):
    cedula_usuario = request.session.get("cedula_usuario")
    if not cedula_usuario:
        return JsonResponse({
            "estado": "fallo",
            "title": "Error de Sesión",
            "icon": "error",
            "descripcion": "No hay información de usuario activa en la sesión."
        }, status=400)

    try:
        usuario = Usuario.objects.get(cedula_identidad=cedula_usuario)
        contacto = Contacto.objects.filter(id_usuario=usuario).first()
    except Usuario.DoesNotExist:
        return JsonResponse({
            "estado": "fallo",
            "title": "Error",
            "icon": "error",
            "descripcion": "Usuario no encontrado."
        }, status=404)

    correos = {}
    if contacto:
        if contacto.correo_electronico:
            correos["correo_principal"] = contacto.correo_electronico
        if contacto.correo_alternativo:
            correos["correo_secundario"] = contacto.correo_alternativo

    return JsonResponse({"estado": "exito", "correos": correos})

# Verificado
def comp_usr(request):
    return render(request, "Sesion/Recuperar Credenciales/comprobar_usuario.html")

def env_cod_usr(request):

    if request.method != "POST":
        return JsonResponse({
            "estado": "fallo",
            "title": "Error",
            "icon": "error",
            "descripcion": "Método no permitido"
        }, status=405)


    correo_seleccionado = request.POST.get("correo_verificacion")

    if not correo_seleccionado:
        return JsonResponse({
            "estado": "fallo",
            "title": "Error",
            "icon": "error",
            "descripcion": "Debe seleccionar un correo electrónico"
        })


    usuario = Usuario.objects.filter(
        cedula_identidad=request.session.get("cedula_usuario")
    ).first()


    if not usuario:
        return JsonResponse({
            "estado": "fallo",
            "title": "Error",
            "icon": "error",
            "descripcion": "Usuario no encontrado"
        })


    resultado = env_cod_ver(
        usuario.nombres,
        usuario.apellidos,
        correo_seleccionado,
        usuario.cedula_identidad,
        request.session.get("token_recuperacion")
    )

    return resultado

# Verificado
def comp_cod_usr(request):
    if request.method == "POST": # Se obtiene el código registrado por el usuario
        codigo_ingresado = request.POST.get("codigo") # Verifica si no se encuentra vacio

        if not codigo_ingresado:
            return JsonResponse({
                "estado": "fallo",
                "title": "Error",
                "icon": "warning",
                "descripcion": "Debe ingresar el código de verificación",
                "accion": "vacio"
            })

        # Obtener el id del usuario
        usuario = Usuario.objects.filter(cedula_identidad=request.session.get("cedula_usuario")).first()

        # Crear un token de seguridad
        token_sesion = request.session.get("token_recuperacion")
        
        verificacion = VerificacionCodigo.objects.filter(
            cedula_identidad=usuario.cedula_identidad, 
            token=token_sesion
        ).first()

        # Aquí se comprueba si el código perdio su vigencia
        if verificacion and verificacion.fecha_expiracion < timezone.now():
            return JsonResponse({
                "estado": "fallo",
                "title": "Error",
                "icon": "error",
                "descripcion": "El código ha expirado, debe solicitar el código a través del botón de reenviar código",
                "accion": "expirado"
            })

        # Se obtiene la respuesta del servidor si esta o no correcto el código
        respuesta = val_cod(
            codigo_ingresado,
            usuario.cedula_identidad,
            token_sesion
        )

        # Convierte la repuesta de un json HTTP a un objecto (Direccionario) que se pueda entender
        datos = json.loads(respuesta.content)

        # Si es exitosa se reinicia los campos para un futuro uso
        if datos.get("estado") == "exito":    
            # Se asigna el valor verdadero como bandera que se verifico el código
            request.session["correo_verificado"] = True

            if verificacion:
                verificacion.intentos = 0
                verificacion.bloqueado_hasta = None
                verificacion.activo = 0
                verificacion.save()

        # Envia la respuesta a la vista
        return respuesta

# Verificado
def val_cod(codigo, cedula_identidad, token):
    # Se busca el código creado de acuerdo a los valores
    verificacion = VerificacionCodigo.objects.filter(cedula_identidad=cedula_identidad, token=token, activo=1).first()
    if not verificacion:
        return JsonResponse({
            "estado": "fallo",
            "title": "Error",
            "icon": "error",
            "descripcion": "No existe un código de verificación"
        })

    # Aquí se elimina el bloqueo para el usuario
    if (verificacion.bloqueado_hasta and timezone.now() >= verificacion.bloqueado_hasta):
        verificacion.intentos = 0
        verificacion.bloqueado_hasta = None
        verificacion.save()

    # Aquí se calcula el tiempo que le falta al usuario para desbloquearse
    if (verificacion.bloqueado_hasta and timezone.now() < verificacion.bloqueado_hasta):
        tiempo_restante = verificacion.bloqueado_hasta - timezone.now()
        minutos_restantes = ceil(tiempo_restante.total_seconds() / 60)
        return JsonResponse({
            "estado": "bloqueado",
            "title": "Bloqueado",
            "icon": "error",
            "descripcion": f"Demasiados intentos. Intente nuevamente en {minutos_restantes} minuto(s)"
        })

    # Se verifica que el código no se halla pasado del tiempo de vigencia
    if timezone.now() > verificacion.fecha_expiracion:
        return JsonResponse({
            "estado": "expirado",
            "title": "Expirado",
            "icon": "warning",
            "descripcion": "El código expiró. Solicite uno nuevamente con el botón de reenviar código."
        })

    # Si el código coincide con el ingresado por el usuario, se reinicie todos los campos
    if verificacion.codigo == codigo:
        verificacion.intentos = 0
        verificacion.bloqueado_hasta = None
        verificacion.activo = 0
        verificacion.save()

        return JsonResponse({
            "estado": "exito",
            "title": "Exito",
            "icon": "success",
            "descripcion": "Código corretamente."
        })

    # Aquí se suma un intento si ocurrio un error
    verificacion.intentos += 1
    # Se verifica si los intentos superan al limite establecido
    if verificacion.intentos >= 3:
        verificacion.bloqueado_hasta = timezone.now() + timedelta(minutes=5)
        verificacion.save()
        return JsonResponse({
            "estado": "bloqueado",
            "title": "Bloqueado",
            "icon": "error",
            "descripcion": "Ha superado el número máximo de intentos. Intente nuevamente en 5 minutos."
        })

    # Guarda los intentos fallidos
    verificacion.save()

    return JsonResponse({
        "estado": "fallo",
        "title": "Error",
        "icon": "error",
        "descripcion": f"Código incorrecto. Intentos: {verificacion.intentos}/3"
    })

# Verificado
def reenv_cod_btn(request):
    if request.method != "POST":
        return JsonResponse({
            "estado": "fallo",
            "title": "Error",
            "icon": "error",
            "descripcion": "Método no permitido"
        }, status=405)

    # 1. Validar que se haya seleccionado un correo
    codigo_seleccionado = request.POST.get("correo_verificacion")
    if not codigo_seleccionado:
        return JsonResponse({
            "estado": "fallo",
            "title": "Correo requerido",
            "icon": "warning",
            "descripcion": "Por favor, selecciona un correo electrónico para el reenvío."
        })

    # 2. Validar que exista la sesión activa
    cedula_usuario = request.session.get("cedula_usuario")
    if not cedula_usuario or not request.session.get("flujo_verificacion"):
        return JsonResponse({
            "estado": "reenviar",
            "icon": "error",
            "title": "Sesión expirada",
            "icon": "error",
            "descripcion": "La sesión ha expirado. Por favor, vuelva a buscar su cédula.",
            "url": reverse("bus_usr")
        })

    # 3. Buscar al usuario de forma segura
    usuario = Usuario.objects.filter(cedula_identidad=cedula_usuario).first()
    if not usuario:
        return JsonResponse({
            "estado": "fallo",
            "title": "Error",
            "icon": "error",
            "descripcion": "No se encontró el usuario asociado a la sesión."
        })

    token_sesion = request.session.get("token_recuperacion")
    verificacion = VerificacionCodigo.objects.filter(
        cedula_identidad=usuario.cedula_identidad, 
        token=token_sesion
    ).first()

    # 4. Validar bloqueo temporal si aplica
    if (verificacion and verificacion.bloqueado_hasta and timezone.now() < verificacion.bloqueado_hasta):
        tiempo_restante = (verificacion.bloqueado_hasta - timezone.now())
        minutos_restantes = ceil(tiempo_restante.total_seconds() / 60)
        return JsonResponse({
            "estado": "fallo",
            "icon": "error",
            "title": "Bloqueado",
            "descripcion": f"Demasiados intentos. Intente nuevamente en {minutos_restantes} minuto(s)"
        })

    # 5. Ejecutar el reenvío de forma segura
    return reenv_cod(
        usuario.nombres,
        usuario.apellidos,
        codigo_seleccionado,
        usuario.cedula_identidad,
        token_sesion
    )

# Verificado

def reenv_cod(nombres_usuario, apellidos_usuario, correo_electronico, cedula_identidad, token):
    # Buscar la verificación existente
    verificacion = VerificacionCodigo.objects.filter(
        cedula_identidad=cedula_identidad,
        token=token
    ).first()

    # Comprobar si el usuario continúa bloqueado
    ahora = timezone.now()

    if (
        verificacion
        and verificacion.bloqueado_hasta
        and ahora < verificacion.bloqueado_hasta
    ):
        tiempo_restante = (
            verificacion.bloqueado_hasta - ahora
        )

        minutos_restantes = max(
            1,
            ceil(tiempo_restante.total_seconds() / 60)
        )

        return JsonResponse({
            "estado": "fallo",
            "title": "Bloqueado",
            "icon": "error",
            "descripcion": (
                f"Demasiados intentos. Intente nuevamente "
                f"en {minutos_restantes} minuto(s)."
            )
        })

    # Generar un nuevo código
    codigo_generado = ''.join(
        secrets.choice(string.ascii_uppercase + string.digits)
        for _ in range(6)
    )

    # Configurar ambos temporizadores
    fecha_expiracion = ahora + timedelta(minutes=5)
    fecha_reenvio = ahora + timedelta(seconds=60)

    # Actualizar el registro existente o crear uno nuevo
    if verificacion:
        verificacion.codigo = codigo_generado
        verificacion.creado = ahora
        verificacion.fecha_expiracion = fecha_expiracion
        verificacion.intentos = 0
        verificacion.activo = 1
        verificacion.bloqueado_hasta = None
        verificacion.descripcion = (
            f"Recup. credenciales: {nombres_usuario}"
        )
        verificacion.save()

    else:
        verificacion = VerificacionCodigo.objects.create(
            cedula_identidad=cedula_identidad,
            token=token,
            codigo=codigo_generado,
            creado=ahora,
            intentos=0,
            activo=1,
            fecha_expiracion=fecha_expiracion,
            bloqueado_hasta=None,
            descripcion=f"Recup. credenciales: {nombres_usuario}"
        )

    # Incrementar el número de reenvíos
    verificacion.numero_reenvios += 1
    verificacion.save(update_fields=["numero_reenvios"])

    print(
        f"[DEBUG] Número de reenvíos enviado al correo: "
        f"{verificacion.numero_reenvios}"
    )

    # Preparar el correo
    html = render_to_string(
        "Email/reenviar_codigo.html",
        {
            "nombres": nombres_usuario,
            "apellidos": apellidos_usuario,
            "codigo": codigo_generado,
            "numero_intento": verificacion.numero_reenvios,
        }
    )

    html = procesar_html_correo(
        html,
        "Estilos/Email/reenviar_codigo.css",
    )

    # Enviar el nuevo código
    send_mail(
        subject="Nuevo código de autenticación - UPT José Félix Ribas",
        message=(
            f"Su nuevo código de autenticación es: "
            f"{codigo_generado}"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[correo_electronico],
        html_message=html,
        fail_silently=False,
    )

    # Responder al JavaScript con ambas fechas
    return JsonResponse({
        "estado": "exito",
        "title": "Código enviado",
        "icon": "success",
        "descripcion": (
            "Se ha enviado un nuevo código de verificación."
        ),
        "fecha_expiracion": fecha_expiracion.isoformat(),
        "fecha_reenvio": fecha_reenvio.isoformat(),
        "numero_reenvios": verificacion.numero_reenvios,
    })


# Verificado

def env_cod_ver(nombres_usuario, apellidos_usuario, correo_electronico, cedula_identidad, token):
    # =====================================================
    # GENERAR EL CÓDIGO DE VERIFICACIÓN
    # =====================================================

    codigo_generado = ''.join(
        secrets.choice(string.ascii_uppercase + string.digits)
        for _ in range(6)
    )

    # =====================================================
    # CONFIGURAR LOS TEMPORIZADORES
    # =====================================================

    ahora = timezone.now()

    fecha_expiracion = ahora + timedelta(minutes=5)
    fecha_reenvio = ahora + timedelta(seconds=60)

    # =====================================================
    # BUSCAR UNA VERIFICACIÓN EXISTENTE
    # =====================================================

    verificacion = VerificacionCodigo.objects.filter(
        cedula_identidad=cedula_identidad,
        token=token
    ).first()

    if verificacion:
        # Actualizar el registro existente
        verificacion.codigo = codigo_generado
        verificacion.creado = ahora
        verificacion.fecha_expiracion = fecha_expiracion
        verificacion.intentos = 0
        verificacion.numero_reenvios = 0
        verificacion.activo = 1
        verificacion.bloqueado_hasta = None
        verificacion.descripcion = (
            f"Recup. credenciales: {nombres_usuario}"
        )

        verificacion.save()

    else:
        # Crear el registro solamente si no existe
        verificacion = VerificacionCodigo.objects.create(
            cedula_identidad=cedula_identidad,
            token=token,
            codigo=codigo_generado,
            creado=ahora,
            numero_reenvios=0,
            intentos=0,
            activo=1,
            fecha_expiracion=fecha_expiracion,
            bloqueado_hasta=None,
            descripcion=f"Recup. credenciales: {nombres_usuario}"
        )

    # =====================================================
    # PREPARAR EL CORREO ELECTRÓNICO
    # =====================================================

    html = render_to_string(
        "Email/enviar_codigo.html",
        {
            "nombres": nombres_usuario,
            "apellidos": apellidos_usuario,
            "codigo": codigo_generado,
        }
    )

    html = procesar_html_correo(
        html,
        "Estilos/Email/enviar_codigo.css",
    )

    # =====================================================
    # ENVIAR EL CÓDIGO
    # =====================================================

    send_mail(
        subject="Código de Autenticación - UPT José Félix Ribas",
        message=(
            f"Su código de autenticación es: {codigo_generado}"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[correo_electronico],
        html_message=html,
        fail_silently=False,
    )

    # =====================================================
    # RESPUESTA PARA LOS TEMPORIZADORES DEL JAVASCRIPT
    # =====================================================

    return JsonResponse({
        "estado": "codigo_enviado",
        "title": "Código enviado",
        "icon": "success",
        "descripcion": "Se ha enviado un código de verificación.",
        "fecha_expiracion": fecha_expiracion.isoformat(),
        "fecha_reenvio": fecha_reenvio.isoformat()
    })

# Verificado
def panel_rec_cred(request):
    # Se verififca si paso por las todas las validaciones
    if not request.session.get("flujo_verificacion"):
        return redirect("buscar_usuario")
    
    if not request.session['correo_verificado']:
        return redirect("buscar_usuario")

    #Obtener el token creado
    token = request.session.get("token_recuperacion")

    # Comprobar si el codigo esta verificado o no
    verificacion = VerificacionCodigo.objects.filter(token=token, activo=0).first()
    if not verificacion:
        return redirect("bus_usr")
    
    return render(request, 'Sesion/Recuperar Credenciales/panel_recuperar_credenciales.html')

# Verificado
@never_cache
def rec_cont(request):
    if not request.session.get("flujo_verificacion"):
        return redirect("bus_usr")
    
    if not request.session.get("correo_verificado"):
        return redirect("comp_usr")
    
    token = request.session.get("token_recuperacion")

    verificacion = VerificacionCodigo.objects.filter(token=token, activo=0).first()
    if not verificacion:
        return redirect("bus_usr")

    if request.method == "POST":
        password = request.POST.get("nueva_contrasenia")
        confirmar_password = request.POST.get("confirmar_contrasenia")

        # Se envia los mensajes de advertencia
        if not password:
            return JsonResponse({
                "estado": "fallo",
                "title": "Vacio",
                "icon": "warning",
                "descripcion": "Por favor, ingresa la nueva contraseña."
            })
        
        if not confirmar_password:
            return JsonResponse({
                "estado": "fallo",
                "title": "Vacio",
                "icon": "warning",
                "descripcion": "Por favor, ingresa la confirmación de la nueva contraseña."
            })

        if password != confirmar_password:
            return JsonResponse({
                "estado": "fallo",
                "title": "Error",
                "icon": "error",
                "descripcion": "No coincide las contraseñas."
            })

        usuario = Usuario.objects.filter(cedula_identidad=request.session.get("cedula_usuario")).first()
        
        credenciales = Cuenta.objects.filter(id_usuario=usuario).first()
        if not credenciales:
            return JsonResponse({
                "estado": "fallo",
                "title": "Error",
                "icon": "error",
                "descripcion": "No existen credenciales registradas."
            })

        # Se guardaron la nuevas contraseña
        credenciales.clave = make_password(password)
        credenciales.save()

        # Se reinicia los campos
        verificacion = VerificacionCodigo.objects.filter(cedula_identidad=request.session["cedula_usuario"]).first()
        if verificacion:
            verificacion.token = ""
            verificacion.save()

        # =====================================================
        # INVALIDAR EL FLUJO DE RECUPERACIÓN
        # =====================================================

        request.session.pop("flujo_verificacion", None)
        request.session.pop("correo_verificado", None)
        request.session.pop("cedula_usuario", None)
        request.session.pop("token_recuperacion", None)

        request.session.modified = True

        return JsonResponse({
            "estado": "exito",
            "title": "Exito",
            "icon": "success",
            "descripcion": "Contraseña actualizada correctamente.",
            "redirect_url": reverse("inicio_sesion")
        })

    return render(request, "Sesion/Recuperar Credenciales/recuperar_contrasenia.html")

# Verificado
def rec_usr(request):
    # Verificar que el flujo de recuperación sea válido
    if not request.session.get("flujo_verificacion"):
        return redirect("bus_usr")

    if not request.session.get("correo_verificado"):
        return redirect("comp_usr")

    try:
        usuario_reg = Usuario.objects.get(cedula_identidad=request.session.get("cedula_usuario"))
    except Usuario.DoesNotExist:
        messages.error(
            request,
            "Ocurrió un error al momento de buscar los datos del usuario."
        )
        return redirect("bus_usr")

    contacto = Contacto.objects.filter(id_usuario=usuario_reg).first()
    if not contacto or not contacto.correo_electronico:
        messages.error(
            request,
            "Ocurrió un error al momento de obtener el correo electrónico registrado."
        )
        return redirect("bus_usr")

    credenciales = Cuenta.objects.filter(id_usuario=usuario_reg).first()
    if not credenciales:
        messages.error(
            request,
            "Ocurrió un error al momento de obtener las credenciales del usuario."
        )
        return redirect("bus_usr")

    # Generar plantilla del correo
    html = render_to_string(
        "Email/recuperar_usuario.html",
        {
            "nombres": usuario_reg.nombres,
            "apellidos": usuario_reg.apellidos,
            "nombre_usuario": credenciales.usuario,
        }
    )
    
    html = procesar_html_correo(
        html,
        "Estilos/Email/correo_recuperacion_usuario.css",
    )

    try:
        send_mail(
            subject="Recuperación de usuario - UPT José Félix Ribas",
            message=f"Su nombre de usuario es: {credenciales.usuario}",
            from_email="ejemplo@gmail.com",
            recipient_list=[contacto.correo_electronico],
            html_message=html,
            fail_silently=False,
        )
    except Exception:
        messages.error(
            request,
            "Ocurrió un error al enviar el correo electrónico."
        )
        return redirect("buscar_usuario")

    # Eliminar variables de sesión
    request.session.pop("correo_verificado", None)
    request.session.pop("cedula_usuario", None)
    request.session.pop("token_recuperacion", None)
    request.session.pop("flujo_verificacion", None)

    return render(request, "Sesion/Recuperar Credenciales/recuperar_usuario.html")