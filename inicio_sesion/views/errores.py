from django.shortcuts import render


def pagina_no_encontrada(request, ruta=None, exception=None):
    return render(
        request,
        "Sesion/Login/404.html",
        status=404,
    )


def pagina_vpn(request):
    return render(request, "Sesion/Login/vpn.html")
