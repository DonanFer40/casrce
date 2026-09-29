from django.shortcuts import render
from django.http import JsonResponse
from ..models import Nucleos


def foro(request):
    contexto = {
        "noticias_carrusel": [],
    }

    return render(request, "Foro/foro.html", contexto)


def noticias_por_nucleo(request):
    nombre_nucleo = request.GET.get("nucleo", "").strip()

    if not nombre_nucleo:
        return JsonResponse(
            {
                "error": "Debe seleccionar una sede."
            },
            status=400
        )

    nucleo = Nucleos.objects.filter(
        municipio__iexact=nombre_nucleo
    ).first()

    if not nucleo:
        return JsonResponse(
            {
                "error": "La sede seleccionada no existe."
            },
            status=404
        )

    noticias = Noticia.objects.filter(
        nucleo=nucleo,
        activa=True
    ).order_by("-fecha_publicacion")

    datos_noticias = []

    for noticia in noticias:
        datos_noticias.append({
            "id": noticia.id_noticia,
            "titulo": noticia.titulo,
            "descripcion": noticia.descripcion,
            "contenido": noticia.contenido,
            "imagen": noticia.imagen.url if noticia.imagen else "",
            "fecha": noticia.fecha_publicacion.strftime("%d/%m/%Y"),
        })

    return JsonResponse({
        "nucleo": nucleo.municipio,
        "noticias": datos_noticias,
    })


def Historia(request):
    return render(request, 'Foro/Historia.html')


def mision_vision(request):
    return render(request, 'Foro/mision_vision.html')


def psc(request):
    return render(request, 'Foro/psc.html')


def pst(request):
    return render(request, 'Foro/pst.html')


def trayectoria(request):
    return render(request, 'Foro/trayectoria.html')


def carreras_impartidas(request):
    return render(request, 'Foro/carreras_impartidas.html')


def Planificacion_Docente(request):
    return render(request, 'Foro/Planificacion_Docente.html')


def barra_lateral(request):
    return render(request, 'Estructura/Barra_Lateral.html')

