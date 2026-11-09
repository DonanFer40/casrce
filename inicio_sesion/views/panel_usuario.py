
from django.shortcuts import render, redirect
from django.db.models import Count, F, Q
from django.utils import timezone

from inicio_sesion.models import (
    AulaEstudiante,
    Bitacora,
    ControlEstudio,
    CoordinadorPNF,
    Cuenta,
    DirectorGeneral,
    Docente,
    Estudiante,
)
from inicio_sesion.views.autenticacion import obtener_roles


def panel_usuario(request):
    id_cuenta = request.session.get("id_cuenta")

    if not id_cuenta:
        return redirect("inicio_sesion")

    try:
        cuenta = Cuenta.objects.select_related("id_usuario").get(
            id_cuenta=id_cuenta
        )
    except Cuenta.DoesNotExist:
        request.session.flush()
        return redirect("inicio_sesion")

    if not cuenta.id_usuario:
        request.session.flush()
        return redirect("inicio_sesion")

    roles = {
        perfil["rol"]
        for perfil in obtener_roles(cuenta.id_usuario)
    }

    es_director = "Director General" in roles
    contexto = {
        "cuenta": cuenta,
        "es_director": es_director,
        "es_control_estudio": "Control de Estudio" in roles,
        "es_coordinador": "Coordinador PNF" in roles,
        "es_docente": "Docente" in roles,
        "es_estudiante": "Estudiante" in roles,
    }

    if es_director:
        hoy = timezone.localdate()
        personal_ids = set(Docente.objects.filter(
            activo=True
        ).values_list("usuario_id", flat=True))
        personal_ids.update(CoordinadorPNF.objects.filter(
            activo=True
        ).values_list("usuario_id", flat=True))
        personal_ids.update(ControlEstudio.objects.filter(
            activo=True
        ).values_list("usuario_id", flat=True))
        personal_ids.update(
            DirectorGeneral.objects.values_list("usuario_id", flat=True)
        )
        contexto.update({
            "fecha_actual": hoy,
            "total_estudiantes": Estudiante.objects.count(),
            "total_inscritos": AulaEstudiante.objects.filter(
                estado="Curso",
                fecha_inicio__lte=hoy,
            ).filter(
                Q(fecha_final__isnull=True) | Q(fecha_final__gte=hoy)
            ).values("estatus__estudiante_id").distinct().count(),
            "total_personal": len(personal_ids),
            "estudiantes_por_nucleo": Estudiante.objects.filter(
                nucleo__isnull=False
            ).values(
                municipio=F("nucleo__municipio")
            ).annotate(
                total=Count("pk")
            ).order_by("municipio"),
            "actividad_reciente": Bitacora.objects.order_by(
                "-fecha_hora"
            )[:3],
        })

    return render(
        request,
        "Logueado/dashboard.html",
        contexto,
    )
