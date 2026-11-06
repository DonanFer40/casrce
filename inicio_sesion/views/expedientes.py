from django.contrib import messages
from django.db.models import Q
from django.http import FileResponse, Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from inicio_sesion.models import (
    CoordinadorPNF,
    ControlEstudio,
    DirectorGeneral,
    Estudiante,
    ExpedienteEstudiante,
    HistorialExpedienteEstudiante,
    DocumentosEstudiante,
    Usuario,
)


def _usuario_sesion(request):
    cedula = request.session.get("cedula_usuario")
    if not cedula:
        return None
    return Usuario.objects.filter(cedula_identidad=cedula).first()


def _alcance_expedientes(usuario):
    """Devuelve estudiantes visibles y los perfiles efectivos del funcionario."""
    coordinaciones = list(
        CoordinadorPNF.objects.filter(usuario=usuario, activo=True)
        .values_list("nucleo_id", "pnf_id")
    )
    controles = list(
        ControlEstudio.objects.filter(usuario=usuario, activo=True)
        .values_list("nucleo_id", flat=True)
    )
    es_director = DirectorGeneral.objects.filter(usuario=usuario).exists()
    direcciones = list(
        DirectorGeneral.objects.filter(usuario=usuario)
        .values_list("nucleo_id", flat=True)
    )

    alcance = Q(pk__in=[])
    for nucleo_id, pnf_id in coordinaciones:
        alcance |= Q(nucleo_id=nucleo_id, pnf_id=pnf_id)
    if controles:
        alcance |= Q(nucleo_id__in=controles)
    if direcciones:
        alcance |= Q(nucleo_id__in=direcciones)

    estudiantes = (
        Estudiante.objects.values_list("usuario_id", flat=True).distinct()
        if es_director
        else Estudiante.objects.filter(alcance).values_list("usuario_id", flat=True).distinct()
    )

    return {
        "estudiantes": estudiantes,
        "coordinaciones": coordinaciones,
        "controles": controles,
        "direcciones": direcciones,
        "es_director": es_director,
    }


def _estudiante_en_alcance(alcance, usuario):
    condiciones = Q(pk__in=[])
    for nucleo_id, pnf_id in alcance["coordinaciones"]:
        condiciones |= Q(nucleo_id=nucleo_id, pnf_id=pnf_id)
    if alcance["controles"]:
        condiciones |= Q(nucleo_id__in=alcance["controles"])

    estudiantes = Estudiante.objects.filter(usuario=usuario)
    if alcance["coordinaciones"] or alcance["controles"]:
        estudiante = estudiantes.filter(condiciones).select_related("nucleo", "pnf").first()
        if estudiante:
            return estudiante
    if alcance["es_director"]:
        return estudiantes.select_related("nucleo", "pnf").first()
    return None


def _perfil_para_estudiante(alcance, estudiante):
    if not estudiante:
        return None
    if (estudiante.nucleo_id, estudiante.pnf_id) in alcance["coordinaciones"]:
        return "COORDINADOR_PNF"
    if estudiante.nucleo_id in alcance["controles"]:
        return "CONTROL_ESTUDIO"
    if alcance["es_director"]:
        return "DIRECTOR_GENERAL"
    return None


def _expedientes_visibles(alcance):
    return (
        ExpedienteEstudiante.objects.filter(usuario_id__in=alcance["estudiantes"])
        .select_related("usuario")
        .prefetch_related("documentos", "historial")
        .distinct()
    )


def lista_expedientes(request):
    usuario = _usuario_sesion(request)
    if not usuario:
        return redirect("inicio_sesion")

    alcance = _alcance_expedientes(usuario)
    if not (alcance["coordinaciones"] or alcance["controles"] or alcance["es_director"]):
        return HttpResponseForbidden("No tienes asignaciones para consultar expedientes.")

    expedientes = _expedientes_visibles(alcance)
    estado = request.GET.get("estado", "").strip()
    busqueda = request.GET.get("q", "").strip()
    if estado in dict(ExpedienteEstudiante.ESTADOS):
        expedientes = expedientes.filter(estado=estado)
    if busqueda:
        expedientes = expedientes.filter(
            Q(usuario__nombres__icontains=busqueda)
            | Q(usuario__apellidos__icontains=busqueda)
            | Q(usuario__cedula_identidad__icontains=busqueda)
        )

    return render(request, "Roles/Expedientes/lista_expedientes.html", {
        "expedientes": expedientes,
        "estados": ExpedienteEstudiante.ESTADOS,
        "estado_seleccionado": estado,
        "busqueda": busqueda,
        "total_expedientes": expedientes.count(),
    })


def detalle_expediente(request, id_expediente):
    usuario = _usuario_sesion(request)
    if not usuario:
        return redirect("inicio_sesion")

    alcance = _alcance_expedientes(usuario)
    if not (alcance["coordinaciones"] or alcance["controles"] or alcance["es_director"]):
        return HttpResponseForbidden("No tienes permisos para consultar expedientes.")

    expediente = get_object_or_404(
        _expedientes_visibles(alcance),
        id_expediente=id_expediente,
    )
    estudiante = _estudiante_en_alcance(alcance, expediente.usuario)
    perfil = _perfil_para_estudiante(alcance, estudiante) if estudiante else None
    puede_gestionar = perfil in {"COORDINADOR_PNF", "CONTROL_ESTUDIO"}

    return render(request, "Roles/Expedientes/detalle_expediente.html", {
        "expediente": expediente,
        "estudiante": estudiante,
        "perfil_gestor": perfil,
        "puede_gestionar": puede_gestionar,
        "historial": expediente.historial.select_related("realizado_por"),
        "documentos": expediente.documentos.all(),
    })


@require_POST
def actualizar_estado_expediente(request, id_expediente):
    usuario = _usuario_sesion(request)
    if not usuario:
        return redirect("inicio_sesion")

    alcance = _alcance_expedientes(usuario)
    if not (alcance["coordinaciones"] or alcance["controles"]):
        return HttpResponseForbidden("No tienes permisos para modificar expedientes.")

    expediente = get_object_or_404(
        _expedientes_visibles(alcance),
        id_expediente=id_expediente,
    )
    estudiante = _estudiante_en_alcance(alcance, expediente.usuario)
    perfil = _perfil_para_estudiante(alcance, estudiante) if estudiante else None
    if perfil not in {"COORDINADOR_PNF", "CONTROL_ESTUDIO"}:
        return HttpResponseForbidden("No tienes autoridad para gestionar este expediente.")

    nuevo_estado = request.POST.get("estado", "").strip()
    observacion = request.POST.get("observacion", "").strip()
    transiciones = {
        "PENDIENTE_REVISION": {"EN_REVISION", "CON_OBSERVACIONES"},
        "EN_REVISION": {"CON_OBSERVACIONES", "VALIDADO_ADMINISTRATIVAMENTE"},
        "CON_OBSERVACIONES": {"EN_REVISION", "CON_OBSERVACIONES"},
        "VALIDADO_ADMINISTRATIVAMENTE": {"CON_OBSERVACIONES", "INSCRIPCION_APROBADA"},
        "INSCRIPCION_APROBADA": set(),
    }

    if nuevo_estado not in transiciones.get(expediente.estado, set()):
        messages.error(request, "La transición solicitada no está permitida para el estado actual.")
        return redirect("detalle_expediente", id_expediente=expediente.id_expediente)

    if nuevo_estado == "CON_OBSERVACIONES" and not observacion:
        messages.error(request, "Debes indicar las observaciones antes de devolver el expediente.")
        return redirect("detalle_expediente", id_expediente=expediente.id_expediente)

    estado_anterior = expediente.estado
    expediente.estado = nuevo_estado
    expediente.observacion_actual = observacion if nuevo_estado == "CON_OBSERVACIONES" else ""

    if nuevo_estado == "INSCRIPCION_APROBADA":
        expediente.aprobado_por = usuario
        expediente.fecha_aprobacion = timezone.now()
        expediente.perfil_aprobacion = perfil
        accion = "APROBO_INSCRIPCION"
    elif nuevo_estado == "VALIDADO_ADMINISTRATIVAMENTE":
        accion = "VALIDO_ADMINISTRATIVAMENTE"
    elif nuevo_estado == "CON_OBSERVACIONES":
        accion = "DEVOLVIO_CON_OBSERVACIONES"
    elif nuevo_estado == "EN_REVISION":
        accion = "INICIO_REVISION"
    else:
        accion = "CAMBIO_ESTADO"

    expediente.save()
    HistorialExpedienteEstudiante.objects.create(
        expediente=expediente,
        estado_anterior=estado_anterior,
        estado_nuevo=nuevo_estado,
        accion=accion,
        observacion=observacion,
        realizado_por=usuario,
        perfil=perfil,
    )

    messages.success(request, f"El expediente ahora está: {expediente.get_estado_display()}.")
    return redirect("detalle_expediente", id_expediente=expediente.id_expediente)


def descargar_documento_expediente(request, id_documento):
    usuario = _usuario_sesion(request)
    if not usuario:
        return redirect("inicio_sesion")

    alcance = _alcance_expedientes(usuario)
    documento = get_object_or_404(
        DocumentosEstudiante.objects.select_related("expediente", "id_usuario"),
        id_documento=id_documento,
        expediente__isnull=False,
        expediente__usuario_id__in=alcance["estudiantes"],
    )
    if not documento.archivo:
        raise Http404("El archivo no está disponible.")

    try:
        archivo = documento.archivo.open("rb")
    except (FileNotFoundError, OSError):
        raise Http404("El archivo no está disponible.")

    nombre = documento.archivo.name.rsplit("/", 1)[-1]
    return FileResponse(archivo, as_attachment=True, filename=nombre)
