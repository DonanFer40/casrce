
from django.shortcuts import render, redirect
from inicio_sesion.models import Cuenta


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

    return render(
        request,
        "Logueado/dashboard.html",
        {"cuenta": cuenta}
    )
