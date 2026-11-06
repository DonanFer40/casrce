from inicio_sesion.models import Cuenta
from bitacora.models import RegistroAccion


def registrar_accion(
    request,
    *,
    categoria="OTRO",
    modulo="Sistema",
    accion,
    descripcion,
    resultado="EXITOSO",
    nivel="INFO",
    objeto=None,
    detalles=None,
):
    """
    Registra una acción de forma centralizada.

    Uso desde cualquier vista:
        registrar_accion(
            request,
            categoria="ACADEMICO",
            modulo="Calificaciones",
            accion="Actualización de calificación",
            descripcion="Se actualizó una calificación.",
            objeto=calificacion,
        )

    No incluir contraseñas, códigos de verificación, tokens ni datos sensibles
    en descripcion o detalles.
    """
    cuenta = None
    usuario = None
    id_cuenta = request.session.get("id_cuenta") if request else None

    if id_cuenta:
        cuenta = (
            Cuenta.objects.select_related("id_usuario")
            .filter(id_cuenta=id_cuenta)
            .first()
        )
        if cuenta:
            usuario = cuenta.id_usuario

    nombre_usuario = ""
    cedula_usuario = ""
    if usuario:
        nombre_usuario = f"{usuario.nombres} {usuario.apellidos}".strip()
        cedula_usuario = usuario.cedula_identidad or ""

    ip = None
    ruta = ""
    metodo = ""
    if request:
        # REMOTE_ADDR evita confiar en X-Forwarded-For enviado por el cliente.
        ip = request.META.get("REMOTE_ADDR") or None
        ruta = request.path[:500]
        metodo = request.method[:10]

    rol = request.session.get("rol", "") if request else ""
    if not isinstance(rol, str):
        rol = ", ".join(str(item) for item in rol)[:60]

    tipo_objeto = ""
    identificador_objeto = ""
    if objeto is not None:
        tipo_objeto = objeto.__class__.__name__[:100]
        identificador_objeto = str(getattr(objeto, "pk", ""))[:100]

    return RegistroAccion.objects.create(
        usuario=usuario,
        nombre_usuario=nombre_usuario,
        cedula_usuario=cedula_usuario,
        rol=rol[:60],
        categoria=categoria,
        modulo=modulo[:100],
        accion=accion[:120],
        descripcion=descripcion,
        resultado=resultado,
        nivel=nivel,
        tipo_objeto=tipo_objeto,
        identificador_objeto=identificador_objeto,
        direccion_ip=ip,
        ruta=ruta,
        metodo_http=metodo,
        detalles=detalles or {},
    )
