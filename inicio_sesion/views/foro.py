from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Case, IntegerField, Prefetch, Value, When
from inicio_sesion.models import DocenteAsignadoMateria, Nucleos, Noticia
from notas_academicas.models import PlanificacionAcademica


def foro(request):
    contexto = {
        "noticias_carrusel": [],
    }

    return render(request, "foro/foro.html", contexto)


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
    return render(request, 'foro/Historia.html')


def mision_vision(request):
    return render(request, 'foro/mision_vision.html')


def psc(request):
    return render(request, 'foro/psc.html')


def pst(request):
    return render(request, 'foro/pst.html')


def trayectoria(request):
    return render(request, 'foro/trayectoria.html')


def carreras_impartidas(request):
    return render(request, 'foro/carreras_impartidas.html')


def Planificacion_Docente(request):
    orden_nucleos = ["Barinas", "Barinitas", "Socopo", "Pedraza"]
    docentes_activos = (
        DocenteAsignadoMateria.objects.filter(
            activo=True,
            docente__activo=True,
        )
        .select_related("docente__usuario")
        .order_by(
            "docente__usuario__apellidos",
            "docente__usuario__nombres",
        )
    )
    planes = (
        PlanificacionAcademica.objects.filter(
            activo=True,
            estado_aceptacion="ACEPTADA",
            materia_asignacion__activo=True,
            materia_asignacion__docentes__activo=True,
            materia_asignacion__docentes__docente__activo=True,
        )
        .select_related(
            "pnf",
            "nucleo",
            "periodo_academico",
            "materia_asignacion__materia",
        )
        .prefetch_related(
            Prefetch(
                "materia_asignacion__docentes",
                queryset=docentes_activos,
                to_attr="docentes_activos",
            ),
            "detalles__evaluaciones",
        )
        .distinct()
        .order_by(
            Case(
                When(nucleo__municipio__iexact="Barinas", then=Value(0)),
                When(nucleo__municipio__iexact="Barinitas", then=Value(1)),
                When(nucleo__municipio__iexact="Socopo", then=Value(2)),
                When(nucleo__municipio__iexact="Pedraza", then=Value(3)),
                default=Value(4),
                output_field=IntegerField(),
            ),
            "nucleo__municipio",
            "pnf__pnf",
            "materia_asignacion__materia__nombre",
        )
    )
    ordenados = sorted(
        planes,
        key=lambda plan: (
            orden_nucleos.index(plan.nucleo.municipio)
            if plan.nucleo.municipio in orden_nucleos
            else len(orden_nucleos),
            plan.nucleo.municipio.casefold(),
            plan.pnf.pnf.casefold(),
            plan.materia_asignacion.materia.nombre.casefold(),
        ),
    )
    return render(
        request,
        "foro/Planificacion_Docente.html",
        {"planes": ordenados},
    )


def barra_lateral(request):
    return render(request, 'Estructura/Barra_Lateral.html')
