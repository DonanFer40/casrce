from django.shortcuts import render, redirect
from django.contrib import messages
from pathlib import Path

from inicio_sesion.models import (
    Usuario,
    DirectorGeneral,
    Noticia
)

from inicio_sesion.services.procesar_imagen_noticia import (
    procesar_imagen_noticia
)


def visualizar_noticias(request):
    """
    Visualiza únicamente las noticias pertenecientes
    al núcleo asignado al Director General autenticado.
    """

    cedula_usuario = request.session.get("cedula_usuario")

    if not cedula_usuario:
        return redirect("inicio_sesion")

    try:
        usuario = Usuario.objects.get(
            cedula_identidad=cedula_usuario
        )

    except Usuario.DoesNotExist:
        request.session.flush()
        return redirect("inicio_sesion")

    try:
        director = DirectorGeneral.objects.select_related(
            "usuario",
            "nucleo"
        ).get(
            usuario=usuario
        )

    except DirectorGeneral.DoesNotExist:
        return redirect("panel_usuario")

    noticias = Noticia.objects.filter(
        nucleo=director.nucleo
    ).select_related(
        "nucleo",
        "registrado_por"
    )

    contexto = {
        "noticias": noticias,
        "director": director,
        "nucleo": director.nucleo,
        "nucleo_usuario": director.nucleo.municipio,
        "total_noticias": noticias.count(),
        "rol_principal": "Director General",
    }

    return render(
        request,
        "Roles/Director_General/noticias/visualizar_noticias.html",
        contexto
    )


def registrar_noticia(request):
    cedula = request.session.get("cedula_usuario")

    if not cedula:
        messages.error(
            request,
            "Debe iniciar sesión para realizar esta acción."
        )
        return redirect("inicio_sesion")

    try:
        usuario = Usuario.objects.get(cedula_identidad=cedula)
        director = DirectorGeneral.objects.select_related(
            "usuario",
            "nucleo"
        ).get(usuario=usuario)

    except (Usuario.DoesNotExist, DirectorGeneral.DoesNotExist):
        messages.error(
            request,
            "No se pudo verificar la información del Director General."
        )
        return redirect("inicio_sesion")

    if request.method == "POST":

        titulo = request.POST.get("titulo", "").strip()
        descripcion = request.POST.get("descripcion", "").strip()
        contenido = request.POST.get("contenido", "").strip()
        imagen = request.FILES.get("imagen")

        errores = []

        # ==========================================
        # VALIDACIÓN DEL TÍTULO
        # ==========================================

        if not titulo:
            errores.append(
                "El título de la noticia es obligatorio."
            )

        elif len(titulo) > 200:
            errores.append(
                "El título no puede superar los 200 caracteres."
            )

        # ==========================================
        # VALIDACIÓN DE LA DESCRIPCIÓN
        # ==========================================

        if not descripcion:
            errores.append(
                "La descripción de la noticia es obligatoria."
            )

        elif len(descripcion) > 300:
            errores.append(
                "La descripción no puede superar los 300 caracteres."
            )

        # ==========================================
        # VALIDACIÓN DEL CONTENIDO
        # ==========================================

        if not contenido:
            errores.append(
                "El contenido de la noticia es obligatorio."
            )

        # ==========================================
        # VALIDACIÓN DE LA IMAGEN
        # ==========================================

        if imagen:
            extension = Path(imagen.name).suffix.lower()

            if extension not in [".jpg", ".jpeg", ".png"]:
                errores.append(
                    "La imagen debe estar en formato JPG, JPEG o PNG."
                )

        # ==========================================
        # SI HAY ERRORES, NO CONTINUAR
        # ==========================================

        if errores:

            for error in errores:
                messages.error(request, error)

            contexto = {
                "director": director,
                "nucleo": director.nucleo,
                "nucleo_usuario": director.nucleo.municipio,
                "rol_principal": "Director General",
            }

            return render(
                request,
                "Roles/Director_General/noticias/registrar_noticia.html",
                contexto
            )

        # ==========================================
        # PROCESAMIENTO DE LA IMAGEN
        # ==========================================

        imagen_procesada = None

        if imagen:

            try:
                imagen_procesada = procesar_imagen_noticia(
                    imagen
                )

            except Exception:
                messages.error(
                    request,
                    "No fue posible procesar la imagen seleccionada."
                )

                contexto = {
                    "director": director,
                    "nucleo": director.nucleo,
                    "nucleo_usuario": director.nucleo.municipio,
                    "rol_principal": "Director General",
                }

                return render(
                    request,
                    "Roles/Director_General/noticias/registrar_noticias.html",
                    contexto
                )

        # ==========================================
        # REGISTRO DE LA NOTICIA
        # ==========================================

        Noticia.objects.create(
            titulo=titulo,
            descripcion=descripcion,
            contenido=contenido,
            imagen=imagen_procesada,
            nucleo=director.nucleo,
            registrado_por=usuario
        )

        messages.success(
            request,
            "La noticia fue registrada correctamente."
        )

        return redirect("visualizar_noticias")

    # ==============================================
    # GET
    # ==============================================

    contexto = {
        "director": director,
        "nucleo": director.nucleo,
        "nucleo_usuario": director.nucleo.municipio,
        "rol_principal": "Director General",
    }

    return render(
        request,
        "Roles/Director_General/noticias/registrar_noticias.html",
        contexto
    )

def modificar_noticia(request, id_noticia):

    cedula = request.session.get("cedula_usuario")

    if not cedula:
        messages.error(
            request,
            "Debe iniciar sesión para realizar esta acción."
        )
        return redirect("inicio_sesion")

    try:
        usuario = Usuario.objects.get(
            cedula_identidad=cedula
        )

        director = DirectorGeneral.objects.select_related(
            "usuario",
            "nucleo"
        ).get(usuario=usuario)

    except (Usuario.DoesNotExist, DirectorGeneral.DoesNotExist):
        messages.error(
            request,
            "No se pudo verificar la información del Director General."
        )
        return redirect("inicio_sesion")

    try:
        noticia = Noticia.objects.get(
            id_noticia=id_noticia,
            nucleo=director.nucleo
        )

    except Noticia.DoesNotExist:
        messages.error(
            request,
            "La noticia no existe o no pertenece a su núcleo."
        )
        return redirect("visualizar_noticias")

    # ==================================================
    # POST
    # ==================================================

    if request.method == "POST":

        titulo = request.POST.get("titulo", "").strip()
        descripcion = request.POST.get("descripcion", "").strip()
        contenido = request.POST.get("contenido", "").strip()
        imagen = request.FILES.get("imagen")

        errores = []

        # ----------------------------------------------
        # TÍTULO
        # ----------------------------------------------

        if not titulo:
            errores.append(
                "El título de la noticia es obligatorio."
            )

        elif len(titulo) > 200:
            errores.append(
                "El título no puede superar los 200 caracteres."
            )

        # ----------------------------------------------
        # DESCRIPCIÓN
        # ----------------------------------------------

        if not descripcion:
            errores.append(
                "La descripción de la noticia es obligatoria."
            )

        elif len(descripcion) > 300:
            errores.append(
                "La descripción no puede superar los 300 caracteres."
            )

        # ----------------------------------------------
        # CONTENIDO
        # ----------------------------------------------

        if not contenido:
            errores.append(
                "El contenido de la noticia es obligatorio."
            )

        # ----------------------------------------------
        # IMAGEN
        # ----------------------------------------------

        if imagen:

            extension = Path(imagen.name).suffix.lower()

            if extension not in [".jpg", ".jpeg", ".png"]:
                errores.append(
                    "La imagen debe estar en formato JPG, JPEG o PNG."
                )

        # ----------------------------------------------
        # ERRORES DE VALIDACIÓN
        # ----------------------------------------------

        if errores:

            for error in errores:
                messages.error(request, error)

            contexto = {
                "noticia": noticia,
                "director": director,
                "nucleo": director.nucleo,
                "nucleo_usuario": director.nucleo.municipio,
                "rol_principal": "Director General",
            }

            return render(
                request,
                "Roles/Director_General/noticias/modificar_noticia.html",
                contexto
            )

        # ----------------------------------------------
        # ACTUALIZAR DATOS
        # ----------------------------------------------

        noticia.titulo = titulo
        noticia.descripcion = descripcion
        noticia.contenido = contenido

        # ----------------------------------------------
        # PROCESAR NUEVA IMAGEN
        # ----------------------------------------------

        if imagen:

            try:

                imagen_procesada = procesar_imagen_noticia(
                    imagen
                )

                noticia.imagen = imagen_procesada

            except Exception:

                messages.error(
                    request,
                    "No fue posible procesar la imagen seleccionada."
                )

                contexto = {
                    "noticia": noticia,
                    "director": director,
                    "nucleo": director.nucleo,
                    "nucleo_usuario": director.nucleo.municipio,
                    "rol_principal": "Director General",
                }

                return render(
                    request,
                    "Roles/Director_General/noticias/modificar_noticias.html",
                    contexto
                )

        # ----------------------------------------------
        # GUARDAR
        # ----------------------------------------------

        noticia.save()

        messages.success(
            request,
            "La noticia fue modificada correctamente."
        )

        return redirect("visualizar_noticias")

    # ==================================================
    # GET
    # ==================================================

    contexto = {
        "noticia": noticia,
        "director": director,
        "nucleo": director.nucleo,
        "nucleo_usuario": director.nucleo.municipio,
        "rol_principal": "Director General",
    }

    return render(
        request,
        "Roles/Director_General/noticias/modificar_noticias.html",
        contexto
    )

def desactivar_noticia(request, id_noticia):
    """
    Desactiva una noticia perteneciente al núcleo
    del Director General autenticado.
    """

    if request.method != "POST":
        messages.error(
            request,
            "Solicitud no válida."
        )
        return redirect("visualizar_noticias")

    cedula_usuario = request.session.get("cedula_usuario")

    if not cedula_usuario:
        return redirect("inicio_sesion")

    try:
        usuario = Usuario.objects.get(
            cedula_identidad=cedula_usuario
        )

    except Usuario.DoesNotExist:
        request.session.flush()
        return redirect("inicio_sesion")

    try:
        director = DirectorGeneral.objects.select_related(
            "nucleo"
        ).get(
            usuario=usuario
        )

    except DirectorGeneral.DoesNotExist:
        return redirect("panel_usuario")

    try:
        noticia = Noticia.objects.get(
            id_noticia=id_noticia,
            nucleo=director.nucleo
        )

    except Noticia.DoesNotExist:
        messages.error(
            request,
            "La noticia no existe o no pertenece a su núcleo."
        )
        return redirect("visualizar_noticias")

    if not noticia.activa:
        messages.warning(
            request,
            "La noticia ya se encuentra desactivada."
        )
        return redirect("visualizar_noticias")

    noticia.activa = False
    noticia.save(update_fields=["activa"])

    messages.success(
        request,
        "La noticia fue desactivada correctamente."
    )

    return redirect("visualizar_noticias")


def activar_noticia(request, id_noticia):
    """
    Activa una noticia perteneciente al núcleo
    del Director General autenticado.
    """

    if request.method != "POST":
        messages.error(
            request,
            "Solicitud no válida."
        )
        return redirect("visualizar_noticias")

    cedula_usuario = request.session.get("cedula_usuario")

    if not cedula_usuario:
        return redirect("inicio_sesion")

    try:
        usuario = Usuario.objects.get(
            cedula_identidad=cedula_usuario
        )

    except Usuario.DoesNotExist:
        request.session.flush()
        return redirect("inicio_sesion")

    try:
        director = DirectorGeneral.objects.select_related(
            "nucleo"
        ).get(
            usuario=usuario
        )

    except DirectorGeneral.DoesNotExist:
        return redirect("panel_usuario")

    try:
        noticia = Noticia.objects.get(
            id_noticia=id_noticia,
            nucleo=director.nucleo
        )

    except Noticia.DoesNotExist:
        messages.error(
            request,
            "La noticia no existe o no pertenece a su núcleo."
        )
        return redirect("visualizar_noticias")

    if noticia.activa:
        messages.warning(
            request,
            "La noticia ya se encuentra activa."
        )
        return redirect("visualizar_noticias")

    noticia.activa = True
    noticia.save(update_fields=["activa"])

    messages.success(
        request,
        "La noticia fue activada correctamente."
    )

    return redirect("visualizar_noticias")