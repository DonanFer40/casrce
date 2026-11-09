from django.contrib import messages
from django.db import transaction
from django.shortcuts import redirect, render

from inicio_sesion.forms import ConfiguracionUsuarioForm
from inicio_sesion.models import (
    Contacto,
    Discapacidad,
    Estudiante,
    Residencia,
    Usuario,
)


def _usuario_de_sesion(request):
    cedula = request.session.get("cedula_usuario")
    if not cedula:
        return None

    usuario = Usuario.objects.filter(cedula_identidad=cedula).first()
    if usuario is None:
        request.session.flush()
    return usuario


def configuracion_usuario(request):
    usuario = _usuario_de_sesion(request)
    if usuario is None:
        return redirect("inicio_sesion")

    contacto = Contacto.objects.filter(id_usuario=usuario).first()
    roles = request.session.get("rol", [])
    rol_usuario = roles[0] if roles else "Usuario"
    return render(
        request,
        "Sesion/actualizar/configuracion_usuarios.html",
        {
            "usuario": usuario,
            "usuario_nombre": f"{usuario.nombres} {usuario.apellidos}",
            "usuario_correo": contacto.correo_electronico if contacto else "",
            "rol_usuario": rol_usuario,
            "foto_perfil_url": (
                usuario.foto_perfil.url if usuario.foto_perfil else ""
            ),
        },
    )


def actualizar_registro_usuario(request):
    usuario = _usuario_de_sesion(request)
    if usuario is None:
        return redirect("inicio_sesion")

    contacto = Contacto.objects.filter(id_usuario=usuario).first()
    residencia = Residencia.objects.filter(id_usuario=usuario).first()
    es_estudiante = Estudiante.objects.filter(usuario=usuario).exists()
    discapacidad = (
        Discapacidad.objects.filter(id_usuario=usuario).first()
        if es_estudiante
        else None
    )
    iniciales = {
        "telefono_personal": contacto.telefono_personal if contacto else "",
        "telefono_suplete": contacto.telefono_suplete if contacto else "",
        "condicion_residencia": (
            residencia.condicion_residencia if residencia else ""
        ),
        "municipio": residencia.municipio if residencia else "",
        "parroquia": residencia.parroquia if residencia else "",
        "direccion_residencia": (
            residencia.direccion_residencia if residencia else ""
        ),
        "carnet_discapacidad": (
            discapacidad.codigo_carnet_discapacidad if discapacidad else ""
        ),
        "registro_medico": (
            discapacidad.nro_registro_medico if discapacidad else ""
        ),
        "tipos_discapacidad": (
            discapacidad.tipo_discapacidad if discapacidad else ""
        ),
        "grado_discapacidad": (
            discapacidad.grado_discapacidad if discapacidad else ""
        ),
        "causa_discapacidad": (
            discapacidad.causa_discapacidad if discapacidad else ""
        ),
    }

    if request.method == "POST":
        form = ConfiguracionUsuarioForm(
            request.POST,
            request.FILES,
            instance=usuario,
        )
        if form.is_valid():
            foto_anterior = usuario.foto_perfil
            with transaction.atomic():
                usuario = form.save()
                if contacto:
                    contacto.telefono_personal = (
                        form.cleaned_data["telefono_personal"]
                        or contacto.telefono_personal
                    )
                    contacto.telefono_suplete = (
                        form.cleaned_data["telefono_suplete"] or None
                    )
                    contacto.save(
                        update_fields=["telefono_personal", "telefono_suplete"]
                    )

                datos_residencia = {
                    "condicion_residencia": form.cleaned_data[
                        "condicion_residencia"
                    ],
                    "municipio": form.cleaned_data["municipio"],
                    "parroquia": form.cleaned_data["parroquia"],
                    "direccion_residencia": form.cleaned_data[
                        "direccion_residencia"
                    ],
                }
                if any(datos_residencia.values()):
                    Residencia.objects.update_or_create(
                        id_usuario=usuario,
                        defaults=datos_residencia,
                    )

                datos_discapacidad = {
                    "codigo_carnet_discapacidad": form.cleaned_data[
                        "carnet_discapacidad"
                    ],
                    "nro_registro_medico": form.cleaned_data["registro_medico"],
                    "tipo_discapacidad": form.cleaned_data["tipos_discapacidad"],
                    "grado_discapacidad": form.cleaned_data["grado_discapacidad"],
                    "causa_discapacidad": form.cleaned_data["causa_discapacidad"],
                }
                if es_estudiante and any(datos_discapacidad.values()):
                    if discapacidad:
                        for campo, valor in datos_discapacidad.items():
                            setattr(discapacidad, campo, valor)
                        discapacidad.save()
                    else:
                        Discapacidad.objects.create(
                            id_usuario=usuario,
                            **datos_discapacidad,
                        )

                foto_actual = usuario.foto_perfil
                if foto_anterior and (
                    not foto_actual or foto_anterior.name != foto_actual.name
                ):
                    transaction.on_commit(
                        lambda archivo=foto_anterior: archivo.storage.delete(
                            archivo.name
                        )
                    )

            iniciales.update(
                telefono_personal=form.cleaned_data["telefono_personal"],
                telefono_suplete=form.cleaned_data["telefono_suplete"],
                **datos_residencia,
            )
            iniciales.update(
                carnet_discapacidad=form.cleaned_data["carnet_discapacidad"],
                registro_medico=form.cleaned_data["registro_medico"],
                tipos_discapacidad=form.cleaned_data["tipos_discapacidad"],
                grado_discapacidad=form.cleaned_data["grado_discapacidad"],
                causa_discapacidad=form.cleaned_data["causa_discapacidad"],
            )
            request.session["usuario_nombre"] = (
                f"{usuario.nombres} {usuario.apellidos}"
            )
            request.session["foto_perfil_url"] = (
                usuario.foto_perfil.url if usuario.foto_perfil else ""
            )
            form = ConfiguracionUsuarioForm(instance=usuario, initial=iniciales)
            messages.success(request, "Tus datos se actualizaron correctamente.")
    else:
        form = ConfiguracionUsuarioForm(instance=usuario, initial=iniciales)

    return render(
        request,
        "Sesion/actualizar/actualizar_registro_usuario.html",
        {
            "form": form,
            "correo_principal": contacto.correo_electronico if contacto else "",
            "es_estudiante": es_estudiante,
        },
    )
