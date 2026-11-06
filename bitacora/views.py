from datetime import datetime, time, timedelta

from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_date

from .models import RegistroAccion


def _es_director(request):
    rol = request.session.get("rol", "")
    if isinstance(rol, (list, tuple, set)):
        return "Director General" in rol
    return "Director General" in str(rol)


def _acceso_denegado(request):
    if not request.session.get("id_cuenta"):
        return redirect("inicio_sesion")
    if not _es_director(request):
        messages.error(request, "No tienes autorización para consultar la bitácora institucional.")
        return redirect("panel_usuario")
    return None


def bitacora_acciones(request):
    denegado = _acceso_denegado(request)
    if denegado:
        return denegado

    registros = RegistroAccion.objects.select_related("usuario").all()

    busqueda = request.GET.get("q", "").strip()
    categoria = request.GET.get("categoria", "").strip()
    resultado = request.GET.get("resultado", "").strip()
    rol = request.GET.get("rol", "").strip()
    modulo = request.GET.get("modulo", "").strip()
    accion = request.GET.get("accion", "").strip()
    desde = parse_date(request.GET.get("desde", ""))
    hasta = parse_date(request.GET.get("hasta", ""))

    if busqueda:
        registros = registros.filter(
            Q(nombre_usuario__icontains=busqueda)
            | Q(cedula_usuario__icontains=busqueda)
            | Q(accion__icontains=busqueda)
            | Q(modulo__icontains=busqueda)
            | Q(descripcion__icontains=busqueda)
        )
    if categoria in dict(RegistroAccion.CATEGORIAS):
        registros = registros.filter(categoria=categoria)
    if resultado in dict(RegistroAccion.RESULTADOS):
        registros = registros.filter(resultado=resultado)
    if rol:
        registros = registros.filter(rol__icontains=rol)
    if modulo:
        registros = registros.filter(modulo__icontains=modulo)
    if accion:
        registros = registros.filter(accion__icontains=accion)
    if desde:
        inicio = timezone.make_aware(datetime.combine(desde, time.min))
        registros = registros.filter(fecha_hora__gte=inicio)
    if hasta:
        fin = timezone.make_aware(datetime.combine(hasta + timedelta(days=1), time.min))
        registros = registros.filter(fecha_hora__lt=fin)

    total = RegistroAccion.objects.count()
    exitosos = RegistroAccion.objects.filter(resultado="EXITOSO").count()
    fallidos = RegistroAccion.objects.filter(resultado__in=["FALLIDO", "RECHAZADO"]).count()
    hoy = timezone.localdate()
    desde_hoy = timezone.make_aware(datetime.combine(hoy, time.min))
    actividad_hoy = RegistroAccion.objects.filter(fecha_hora__gte=desde_hoy).count()

    paginator = Paginator(registros, 25)
    pagina = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "Bitacora/bitacora_acciones.html",
        {
            "pagina": pagina,
            "total_registros": total,
            "total_exitosos": exitosos,
            "total_fallidos": fallidos,
            "actividad_hoy": actividad_hoy,
            "categorias": RegistroAccion.CATEGORIAS,
            "resultados": RegistroAccion.RESULTADOS,
            "modulos": (
                RegistroAccion.objects.order_by("modulo")
                .values_list("modulo", flat=True).distinct()
            ),
            "filtros": {
                "q": busqueda,
                "categoria": categoria,
                "resultado": resultado,
                "rol": rol,
                "modulo": modulo,
                "accion": accion,
                "desde": request.GET.get("desde", ""),
                "hasta": request.GET.get("hasta", ""),
            },
        },
    )


def detalle_accion(request, id_registro):
    denegado = _acceso_denegado(request)
    if denegado:
        return denegado

    registro = get_object_or_404(
        RegistroAccion.objects.select_related("usuario"),
        id_registro=id_registro,
    )
    return render(request, "Bitacora/detalle_accion.html", {"registro": registro})
