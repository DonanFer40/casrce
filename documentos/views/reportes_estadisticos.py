import logging
from collections import Counter

from django.db.models import Q
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST

from documentos.models import DocumentoInstitucional
from documentos.services.generador_pdf import crear_documento_institucional
from documentos.services.reportes_pdf import construir_reporte_tabular
from inicio_sesion.models import (
    AulaEstudiante,
    ControlEstudio,
    CoordinadorPNF,
    DirectorGeneral,
    Docente,
    Estudiante,
    EstatusEstudiante,
    Cuenta,
)


logger = logging.getLogger(__name__)
TIPOS_ANUALES = {"inscripciones", "egresados", "estudiantes_anuales"}
TIPOS_REPORTE = {
    "matricula": "Matrícula por núcleo, PNF y trayecto",
    "inscripciones": "Inscripciones por año",
    "egresados": "Egresados por año",
    "estudiantes_anuales": "Estudiantes por año de ingreso",
    "personal": "Personal por núcleo y PNF",
}


def _usuario_actual(request):
    id_cuenta = request.session.get("id_cuenta")
    if not id_cuenta:
        return None
    cuenta = Cuenta.objects.select_related("id_usuario").filter(
        id_cuenta=id_cuenta
    ).first()
    return cuenta.id_usuario if cuenta else None


def _alcance(usuario):
    nucleos = set(DirectorGeneral.objects.filter(
        usuario=usuario
    ).values_list("nucleo_id", flat=True))
    nucleos.update(ControlEstudio.objects.filter(
        usuario=usuario,
        activo=True,
    ).values_list("nucleo_id", flat=True))
    coordinaciones = list(CoordinadorPNF.objects.filter(
        usuario=usuario,
        activo=True,
    ).values_list("nucleo_id", "pnf_id"))
    return nucleos, coordinaciones


def _filtrar_estudiantes(usuario, queryset):
    nucleos, coordinaciones = _alcance(usuario)
    filtro = Q()
    hay_alcance = False
    if nucleos:
        filtro |= Q(nucleo_id__in=nucleos)
        hay_alcance = True
    for nucleo_id, pnf_id in coordinaciones:
        filtro |= Q(nucleo_id=nucleo_id, pnf_id=pnf_id)
        hay_alcance = True
    return queryset.filter(filtro).distinct() if hay_alcance else queryset.none()


def _datos_personal(usuario, modo):
    nucleos, coordinaciones = _alcance(usuario)
    personal = []
    for rol, modelo in (
        ("Docente", Docente),
        ("Coordinador PNF", CoordinadorPNF),
        ("Control de Estudio", ControlEstudio),
    ):
        consulta = modelo.objects.filter(activo=True)
        filtro = Q()
        if nucleos:
            filtro |= Q(nucleo_id__in=nucleos)
        if rol != "Control de Estudio":
            for nucleo_id, pnf_id in coordinaciones:
                filtro |= Q(nucleo_id=nucleo_id, pnf_id=pnf_id)
        consulta = consulta.filter(filtro) if filtro else consulta.none()
        relaciones = ["usuario", "nucleo"]
        if rol != "Control de Estudio":
            relaciones.append("pnf")
        consulta = consulta.select_related(*relaciones)
        for persona in consulta.distinct():
            pnf = getattr(persona, "pnf", None)
            personal.append((
                persona.nucleo.municipio if persona.nucleo else "Sin núcleo",
                pnf.pnf if pnf else "No aplica",
                rol,
                f"{persona.usuario.apellidos}, {persona.usuario.nombres}",
                persona.usuario.cedula_identidad,
            ))

    if modo == "LISTADO":
        return (
            ["Núcleo", "PNF", "Rol", "Apellidos y nombres", "Cédula"],
            personal,
        )

    totales = Counter((nucleo, pnf, rol) for nucleo, pnf, rol, *_ in personal)
    return (
        ["Núcleo", "PNF", "Rol", "Total"],
        [(*clave, total) for clave, total in sorted(totales.items())],
    )


def _datos_estudiantes(usuario, tipo, modo, anio):
    base = _filtrar_estudiantes(usuario, Estudiante.objects.all())
    estados = EstatusEstudiante.objects.filter(
        estudiante__in=base,
    ).select_related(
        "estudiante__usuario",
        "estudiante__nucleo",
        "estudiante__pnf",
        "trayecto",
    )

    if tipo == "inscripciones":
        inscripciones = AulaEstudiante.objects.filter(
            estatus__estudiante__in=base,
            fecha_inicio__year=anio,
        ).select_related(
            "estatus__estudiante__usuario",
            "estatus__estudiante__nucleo",
            "estatus__estudiante__pnf",
            "estatus__trayecto",
            "aula__id_seccion",
        )
        detalle = [
            (
                inscripcion.estatus.estudiante.usuario.cedula_identidad,
                f"{inscripcion.estatus.estudiante.usuario.apellidos}, "
                f"{inscripcion.estatus.estudiante.usuario.nombres}",
                inscripcion.estatus.estudiante.nucleo.municipio
                if inscripcion.estatus.estudiante.nucleo else "Sin núcleo",
                inscripcion.estatus.estudiante.pnf.pnf
                if inscripcion.estatus.estudiante.pnf else "Sin PNF",
                inscripcion.estatus.trayecto.nombre,
                inscripcion.aula.id_seccion.nombre,
                inscripcion.fecha_inicio.strftime("%d/%m/%Y"),
                inscripcion.estado,
            )
            for inscripcion in inscripciones
        ]
        dimensiones = {
            (
                item.estatus.estudiante.nucleo.municipio
                if item.estatus.estudiante.nucleo else "Sin núcleo",
                item.estatus.estudiante.pnf.pnf
                if item.estatus.estudiante.pnf else "Sin PNF",
                item.estatus.trayecto.nombre,
                item.estatus.estudiante_id,
            )
            for item in inscripciones
        }
        columnas_detalle = [
            "Cédula", "Estudiante", "Núcleo", "PNF", "Trayecto",
            "Sección", "Fecha", "Estado",
        ]
    elif tipo == "egresados":
        egresados = AulaEstudiante.objects.filter(
            estatus__estudiante__in=base,
            estado="Egreso",
            fecha_final__year=anio,
        ).select_related(
            "estatus__estudiante__usuario",
            "estatus__estudiante__nucleo",
            "estatus__estudiante__pnf",
            "estatus__trayecto",
            "aula__id_seccion",
        )
        detalle = [
            (
                egreso.estatus.estudiante.usuario.cedula_identidad,
                f"{egreso.estatus.estudiante.usuario.apellidos}, "
                f"{egreso.estatus.estudiante.usuario.nombres}",
                egreso.estatus.estudiante.nucleo.municipio
                if egreso.estatus.estudiante.nucleo else "Sin núcleo",
                egreso.estatus.estudiante.pnf.pnf
                if egreso.estatus.estudiante.pnf else "Sin PNF",
                egreso.estatus.trayecto.nombre,
                egreso.aula.id_seccion.nombre,
                egreso.fecha_final.strftime("%d/%m/%Y"),
            )
            for egreso in egresados
        ]
        dimensiones = {
            (
                item.estatus.estudiante.nucleo.municipio
                if item.estatus.estudiante.nucleo else "Sin núcleo",
                item.estatus.estudiante.pnf.pnf
                if item.estatus.estudiante.pnf else "Sin PNF",
                item.estatus.trayecto.nombre,
                item.estatus.estudiante_id,
            )
            for item in egresados
        }
        columnas_detalle = [
            "Cédula", "Egresado", "Núcleo", "PNF", "Trayecto",
            "Sección", "Fecha de egreso",
        ]
    else:
        estados_ingreso = []
        estudiantes_vistos = set()
        for estado in estados.order_by(
            "estudiante_id",
            "fecha_ingreso",
            "pk",
        ):
            if estado.estudiante_id in estudiantes_vistos:
                continue
            estudiantes_vistos.add(estado.estudiante_id)
            if estado.fecha_ingreso.year == anio:
                estados_ingreso.append(estado)
        detalle = [
            (
                estado.estudiante.usuario.cedula_identidad,
                f"{estado.estudiante.usuario.apellidos}, "
                f"{estado.estudiante.usuario.nombres}",
                estado.estudiante.nucleo.municipio if estado.estudiante.nucleo else "Sin núcleo",
                estado.estudiante.pnf.pnf if estado.estudiante.pnf else "Sin PNF",
                estado.trayecto.nombre,
                estado.fecha_ingreso.strftime("%d/%m/%Y"),
            )
            for estado in estados_ingreso
        ]
        dimensiones = {
            (
                estado.estudiante.nucleo.municipio if estado.estudiante.nucleo else "Sin núcleo",
                estado.estudiante.pnf.pnf if estado.estudiante.pnf else "Sin PNF",
                estado.trayecto.nombre,
                estado.estudiante_id,
            )
            for estado in estados_ingreso
        }
        columnas_detalle = [
            "Cédula", "Estudiante", "Núcleo", "PNF", "Trayecto", "Fecha de ingreso",
        ]

    if modo == "LISTADO":
        return columnas_detalle, detalle

    totales = Counter(
        (nucleo, pnf, trayecto)
        for nucleo, pnf, trayecto, _ in dimensiones
    )
    return (
        ["Núcleo", "PNF", "Trayecto", "Total"],
        [(*clave, total) for clave, total in sorted(totales.items())],
    )


def _datos_matricula(usuario, modo):
    estudiantes = _filtrar_estudiantes(usuario, Estudiante.objects.all())
    estados = list(EstatusEstudiante.objects.filter(
        estudiante__in=estudiantes,
    ).select_related(
        "estudiante__usuario",
        "estudiante__nucleo",
        "estudiante__pnf",
        "trayecto",
    ).order_by("estudiante_id", "-fecha_ingreso", "-pk"))
    estado_actual = {}
    for estado in estados:
        estado_actual.setdefault(estado.estudiante_id, estado)
    perfiles = list(estudiantes.select_related("usuario", "nucleo", "pnf"))

    filas = []
    dimensiones = set()
    for perfil in perfiles:
        estado = estado_actual.get(perfil.pk)
        nucleo = perfil.nucleo.municipio if perfil.nucleo else "Sin núcleo"
        pnf = perfil.pnf.pnf if perfil.pnf else "Sin PNF"
        trayecto = estado.trayecto.nombre if estado else "Sin trayecto"
        dimensiones.add((nucleo, pnf, trayecto, perfil.pk))
        filas.append((
            perfil.usuario.cedula_identidad,
            f"{perfil.usuario.apellidos}, {perfil.usuario.nombres}",
            nucleo,
            pnf,
            trayecto,
        ))
    if modo == "LISTADO":
        return ["Cédula", "Estudiante", "Núcleo", "PNF", "Trayecto"], filas

    conteos = Counter(
        (nucleo, pnf, trayecto)
        for nucleo, pnf, trayecto, _ in dimensiones
    )
    return (
        ["Núcleo", "PNF", "Trayecto", "Total de registros"],
        [(*clave, total) for clave, total in sorted(conteos.items())],
    )


@require_POST
def emitir_reporte_estadistico(request):
    usuario = _usuario_actual(request)
    if usuario is None:
        return JsonResponse({"estado": "fallo", "mensaje": "Inicia sesión nuevamente."}, status=401)

    tipo = request.POST.get("tipo", "")
    modo = request.POST.get("modo", "TOTAL").upper()
    if tipo not in TIPOS_REPORTE or modo not in {"TOTAL", "LISTADO"}:
        return JsonResponse({"estado": "fallo", "mensaje": "Selecciona un tipo y formato válido."}, status=400)
    if not _alcance(usuario)[0] and not _alcance(usuario)[1]:
        return JsonResponse({"estado": "fallo", "mensaje": "No tienes permisos para generar estadísticas institucionales."}, status=403)

    anio = None
    if tipo in TIPOS_ANUALES:
        try:
            anio = int(request.POST.get("anio", ""))
        except (TypeError, ValueError):
            return JsonResponse({"estado": "fallo", "mensaje": "Indica un año válido."}, status=400)
        if anio < 1900 or anio > timezone.localdate().year + 1:
            return JsonResponse({"estado": "fallo", "mensaje": "El año está fuera del rango permitido."}, status=400)

    if tipo == "personal":
        columnas, filas = _datos_personal(usuario, modo)
    elif tipo == "matricula":
        columnas, filas = _datos_matricula(usuario, modo)
    else:
        columnas, filas = _datos_estudiantes(usuario, tipo, modo, anio)

    titulo = TIPOS_REPORTE[tipo]
    if anio:
        titulo = f"{titulo} · {anio}"
    titulo = f"{titulo} · {'Listado' if modo == 'LISTADO' else 'Totales'}"
    try:
        documento = crear_documento_institucional(
            request=request,
            tipo_documento=f"REPORTE_{tipo.upper()}",
            titulo=titulo,
            contenido=construir_reporte_tabular(titulo, columnas, filas),
            emitido_por=usuario,
            datos_documento={
                "tipo_reporte": tipo,
                "modo": modo,
                "anio": anio,
                "generado_por_usuario_id": usuario.pk,
            },
        )
    except Exception:
        logger.exception("No se pudo generar el reporte estadístico %s.", tipo)
        return JsonResponse({"estado": "fallo", "mensaje": "No se pudo crear el PDF del reporte."}, status=500)

    return JsonResponse({
        "estado": "exito",
        "mensaje": "El reporte quedó registrado y contiene un QR de verificación.",
        "codigo_documento": documento.codigo_documento,
        "url_descarga": f"/documentos/descargar/{documento.identificador}/",
    })
