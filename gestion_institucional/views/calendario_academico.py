from django.shortcuts import render
from django.http import JsonResponse
from datetime import datetime, date
from django.db import transaction
from django.utils import timezone
from calendar import monthrange

from inicio_sesion.models import PeriodoAcademico, CalendarioAcademico, Bitacora, CalendarioPeriodo

CALENDARIO_ACADEMICA = [

    {
        "mes_inicio": 1,
        "dia_inicio": 1,
        "mes_final": 1,
        "dia_final": 1,
        "descripcion": "Inicio de Año",
        "activo": True,
        "tipo": "NO_LABORABLE"
    },

    {
        "mes_inicio": 4,
        "dia_inicio": 19,
        "mes_final": 4,
        "dia_final": 19,
        "descripcion": "Declaración de Independencia",
        "activo": True,
        "tipo": "NO_LABORABLE"
    },

    {
        "mes_inicio": 5,
        "dia_inicio": 1,
        "mes_final": 5,
        "dia_final": 1,
        "descripcion": "Día del Trabajador",
        "activo": True,
        "tipo": "NO_LABORABLE"
    },

    {
        "mes_inicio": 6,
        "dia_inicio": 24,
        "mes_final": 6,
        "dia_final": 24,
        "descripcion": "Batalla de Carabobo",
        "activo": True,
        "tipo": "NO_LABORABLE"
    },

    {
        "mes_inicio": 7,
        "dia_inicio": 5,
        "mes_final": 7,
        "dia_final": 5,
        "descripcion": "Día de la Independencia de Venezuela",
        "activo": True,
        "tipo": "NO_LABORABLE"
    },

    {
        "mes_inicio": 7,
        "dia_inicio": 24,
        "mes_final": 7,
        "dia_final": 24,
        "descripcion": "Natalicio de Simón Bolívar",
        "activo": True,
        "tipo": "NO_LABORABLE"
    },

    {
        "mes_inicio": 10,
        "dia_inicio": 12,
        "mes_final": 10,
        "dia_final": 12,
        "descripcion": "Día de la Resistencia Indígena",
        "activo": True,
        "tipo": "NO_LABORABLE"
    },

    {
        "mes_inicio": 12,
        "dia_inicio": 5,
        "mes_final": 12,
        "dia_final": 5,
        "descripcion": "Día del Profesor Universitario",
        "activo": True,
        "tipo": "NO_LABORABLE"
    },

    {
        "mes_inicio": 12,
        "dia_inicio": 24,
        "mes_final": 12,
        "dia_final": 24,
        "descripcion": "Noche Buena",
        "activo": True,
        "tipo": "NO_LABORABLE"
    },

    {
        "mes_inicio": 12,
        "dia_inicio": 25,
        "mes_final": 12,
        "dia_final": 25,
        "descripcion": "Día de Navidad",
        "activo": True,
        "tipo": "NO_LABORABLE"
    },

    {
        "mes_inicio": 12,
        "dia_inicio": 31,
        "mes_final": 12,
        "dia_final": 31,
        "descripcion": "Fin de Año",
        "activo": True,
        "tipo": "NO_LABORABLE"
    },

    {
        "mes_inicio": 1,
        "dia_inicio": 1,
        "mes_final": 1,
        "dia_final": 5,
        "descripcion": "Período de Vacaciones",
        "activo": True,
        "tipo": "VACACIONES"
    },

    {
        "mes_inicio": 7,
        "dia_inicio": 29,
        "mes_final": 7,
        "dia_final": 31,
        "descripcion": "Período de Vacaciones",
        "activo": True,
        "tipo": "VACACIONES"
    },

    {
        "mes_inicio": 8,
        "dia_inicio": 1,
        "mes_final": 8,
        "dia_final": 31,
        "descripcion": "Período de Vacaciones",
        "activo": True,
        "tipo": "VACACIONES"
    },

    {
        "mes_inicio": 9,
        "dia_inicio": 1,
        "mes_final": 9,
        "dia_final": 14,
        "descripcion": "Período de Vacaciones",
        "activo": True,
        "tipo": "VACACIONES"
    },

    {
        "mes_inicio": 12,
        "dia_inicio": 16,
        "mes_final": 12,
        "dia_final": 31,
        "descripcion": "Período de Vacaciones",
        "activo": True,
        "tipo": "VACACIONES"
    },

    {
        "mes_inicio": 1,
        "dia_inicio": 31,
        "mes_final": 1,
        "dia_final": 31,
        "descripcion": "Muerte de José Félix Ribas",
        "activo": True,
        "tipo": "NO_LABORABLE"
    },

    {
        "mes_inicio": 7,
        "dia_inicio": 17,
        "mes_final": 7,
        "dia_final": 21,
        "descripcion": "Semana Aniversario de la UPT del Estado Barinas José Félix Ribas y Actividades Académicas y Culturales",
        "activo": True,
        "tipo": "ANIVERSARIO"
    },

    {
        "mes_inicio": 9,
        "dia_inicio": 19,
        "mes_final": 9,
        "dia_final": 19,
        "descripcion": "Natalicio de José Félix Ribas",
        "activo": True,
        "tipo": "NO_LABORABLE"
    },

    {
        "mes_inicio": 11,
        "dia_inicio": 21,
        "mes_final": 11,
        "dia_final": 21,
        "descripcion": "Día del Estudiante",
        "activo": True,
        "tipo": "NO_LABORABLE"
    },

]

MESES_PERIODOS = {
    "Inicial Trimestre": (9, 11),
    "Inicial Semestre": (9, 11),
    "Reparación": (11, 12),
    "Tramo I": (1, 4),
    "Tramo II": (4, 7),
    "Tramo III": (9, 11),
    "Semestre I": (1, 5),
    "Semestre II": (9, 11),
}

MESES_CARGA_NOTAS = {
    "Inicial Trimestre": 11,
    "Inicial Semestre": 11,
    "Reparación": 12,
    "Tramo I": 4,
    "Tramo II": 7,
    "Tramo III": 11,
    "Semestre I": 5,
    "Semestre II": 11,
}

MESES_INSCRIPCION = {
    "INSCRIPCION_TRIMESTRE": 9,
    "INSCRIPCION_SEMESTRE": 9,
}


def limites_fechas_calendario(calendario, periodo_nombre):
    anio = calendario.fecha_inicio.year

    def limite_mes(mes, ultimo_dia=False):
        dia = monthrange(anio, mes)[1] if ultimo_dia else 1
        return date(anio, mes, dia).isoformat()

    limites = {
        "fecha_inicio_min": date(anio, 1, 1).isoformat(),
        "fecha_inicio_max": date(anio, 12, 31).isoformat(),
        "fecha_final_min": date(anio, 1, 1).isoformat(),
        "fecha_final_max": date(anio, 12, 31).isoformat(),
        "tipo": calendario.tipo,
    }

    if calendario.tipo == "PERIODO":
        rango = MESES_PERIODOS.get(periodo_nombre)
        if not rango:
            return None
        mes_inicio, mes_final = rango
        limites.update({
            "fecha_inicio_min": limite_mes(mes_inicio),
            "fecha_inicio_max": limite_mes(mes_inicio, ultimo_dia=True),
            "fecha_final_min": limite_mes(mes_final),
            "fecha_final_max": limite_mes(mes_final, ultimo_dia=True),
        })
    elif calendario.tipo == "CARGA_NOTAS":
        mes = MESES_CARGA_NOTAS.get(periodo_nombre)
        if not mes:
            return None
        limites.update({
            "fecha_inicio_min": limite_mes(mes),
            "fecha_inicio_max": limite_mes(mes, ultimo_dia=True),
            "fecha_final_min": limite_mes(mes),
            "fecha_final_max": limite_mes(mes, ultimo_dia=True),
        })
    elif calendario.tipo in MESES_INSCRIPCION:
        mes = MESES_INSCRIPCION[calendario.tipo]
        limites.update({
            "fecha_inicio_min": limite_mes(mes),
            "fecha_inicio_max": limite_mes(mes, ultimo_dia=True),
            "fecha_final_min": limite_mes(mes),
            "fecha_final_max": limite_mes(mes, ultimo_dia=True),
        })

    return limites


# periodos_academicos
def periodos_lista(request):
    tipo = request.POST.get("tipo_periodo")

    anio_actual = timezone.localdate().year

    periodos = PeriodoAcademico.objects.all()

    if tipo in ["PERIODO", "CARGA_NOTAS"]:

        periodos = periodos.exclude(
            id_periodo_academico__in=CalendarioPeriodo.objects.filter(
                calendario__tipo=tipo,
                calendario__activo=True,
                calendario__fecha_inicio__year=anio_actual
            ).values("periodo_id")
        )

    periodos = list(
        periodos.values(
            "id_periodo_academico",
            "nombre"
        )
    )

    return JsonResponse({
        "estado": "exito",
        "periodos": periodos
    })

def per_acad_reg(request):

    anio_actual = timezone.localdate().year

    tipos = (
        CalendarioAcademico.objects
        .filter(
            activo=True,
            fecha_inicio__year=anio_actual
        )
        .values_list(
            "tipo",
            flat=True
        )
        .distinct()
    )

    return JsonResponse({
        "estado": "exito",
        "tipos": list(tipos)
    })

def opc_reg_cal(request):

    anio_actual = timezone.localdate().year

    tipos_permitidos = [
        ("PERIODO", "Período académico"),
        ("GRADO_ACADEMICO", "Grado Académico"),
        ("CARGA_NOTAS", "Carga de notas"),
        ("INSCRIPCION_TRIMESTRE", "Inscripción Trimestre"),
        ("INSCRIPCION_SEMESTRE", "Inscripción Semestre"),
        ("ACTIVIDADES", "Actividades o operativos"),
    ]

    periodos_requeridos = {
        "Inicial Trimestre",
        "Inicial Semestre",
        "Reparación",
        "Tramo I",
        "Tramo II",
        "Tramo III",
        "Semestre I",
        "Semestre II",
    }

    periodos_registrados = set(
        PeriodoAcademico.objects.filter(
            nombre__in=periodos_requeridos
        ).values_list(
            "nombre",
            flat=True
        )
    )

    # ==========================================================
    # PERÍODO ACADÉMICO COMPLETO DEL AÑO ACTUAL
    # ==========================================================

    periodo_completo = False

    if periodos_registrados == periodos_requeridos:

        cantidad_periodos = (
            CalendarioPeriodo.objects
            .filter(
                periodo__nombre__in=periodos_requeridos,
                calendario__tipo="PERIODO",
                calendario__activo=True,
                calendario__fecha_inicio__year=anio_actual,
            )
            .values("periodo")
            .distinct()
            .count()
        )

        if cantidad_periodos == len(periodos_requeridos):
            periodo_completo = True

    # ==========================================================
    # CARGA DE NOTAS COMPLETA DEL AÑO ACTUAL
    # ==========================================================

    carga_notas_completa = False

    if periodos_registrados == periodos_requeridos:

        cantidad_carga_notas = (
            CalendarioPeriodo.objects
            .filter(
                periodo__nombre__in=periodos_requeridos,
                calendario__tipo="CARGA_NOTAS",
                calendario__activo=True,
                calendario__fecha_inicio__year=anio_actual,
            )
            .values("periodo")
            .distinct()
            .count()
        )

        if cantidad_carga_notas == len(periodos_requeridos):
            carga_notas_completa = True

    # ==========================================================
    # TIPOS REGISTRADOS EN EL AÑO ACTUAL
    # ==========================================================

    tipos_registrados = set(
        CalendarioAcademico.objects
        .filter(
            activo=True,
            fecha_inicio__year=anio_actual
        )
        .values_list(
            "tipo",
            flat=True
        )
    )

    # ==========================================================
    # GRADOS ACADÉMICOS DEL AÑO ACTUAL
    # ==========================================================

    cantidad_grado_academico = (
        CalendarioAcademico.objects
        .filter(
            tipo="GRADO_ACADEMICO",
            activo=True,
            fecha_inicio__year=anio_actual
        )
        .count()
    )

    # ==========================================================
    # TIPOS DISPONIBLES
    # ==========================================================

    tipos_disponibles = []

    for valor, nombre in tipos_permitidos:

        # ------------------------------------------------------
        # PERÍODO ACADÉMICO
        # ------------------------------------------------------

        if valor == "PERIODO":

            if not periodo_completo:
                tipos_disponibles.append({
                    "valor": valor,
                    "nombre": nombre,
                })

            continue

        # ------------------------------------------------------
        # CARGA DE NOTAS
        # ------------------------------------------------------

        if valor == "CARGA_NOTAS":

            if not carga_notas_completa:
                tipos_disponibles.append({
                    "valor": valor,
                    "nombre": nombre,
                })

            continue

        # ------------------------------------------------------
        # ACTIVIDADES
        # REGISTRO ILIMITADO
        # ------------------------------------------------------

        if valor == "ACTIVIDADES":

            tipos_disponibles.append({
                "valor": valor,
                "nombre": nombre,
            })

            continue

        # ------------------------------------------------------
        # GRADO ACADÉMICO
        # MÁXIMO 6 POR AÑO
        # ------------------------------------------------------

        if valor == "GRADO_ACADEMICO":

            if cantidad_grado_academico < 6:
                tipos_disponibles.append({
                    "valor": valor,
                    "nombre": nombre,
                })

            continue

        # DEMÁS TIPOS SOLO UNO ACTIVO POR AÑO

        if valor not in tipos_registrados:

            tipos_disponibles.append({
                "valor": valor,
                "nombre": nombre,
            })

    return JsonResponse({
        "estado": "exito",
        "tipos": tipos_disponibles,
    })

def calendarios_lista(request):
    if request.method == "POST":
        tipo = request.POST.get("periodo", "").strip()

        filtros = {
            "activo": True
        }

        if tipo:
            filtros["tipo"] = tipo

        calendarios = (
            CalendarioAcademico.objects
            .filter(**filtros)
            .order_by("fecha_inicio")
        )

        datos = [
            {
                "id": calendario.id_calendario_academico,
                "descripcion": calendario.descripcion,
                "fecha_inicio": calendario.fecha_inicio.strftime("%d/%m/%Y"),
                "fecha_final": calendario.fecha_final.strftime("%d/%m/%Y"),
                "tipo_valor": calendario.tipo,
            }
            for calendario in calendarios
        ]

        return JsonResponse({
            "estado": "exito",
            "calendarios": datos
        })

#  datos_calendario
def calendario_datos(request):

    if request.method != "POST":
        return JsonResponse({
            "estado": "fallo",
            "icon": "warning",
            "title": "Solicitud no válida",
            "descripcion": "Método de solicitud no permitido."
        })

    id_calendario = request.POST.get("id_calendario")

    try:
        cal = CalendarioAcademico.objects.get(
            id_calendario_academico=id_calendario
        )

    except (
        CalendarioAcademico.DoesNotExist,
        TypeError,
        ValueError
    ):
        return JsonResponse({
            "estado": "fallo",
            "icon": "error",
            "title": "Calendario no encontrado",
            "descripcion": (
                "No se encuentra registrado "
                "el calendario académico."
            )
        })

    # -------------------------------------------------
    # OBTENER PERÍODO ACADÉMICO
    # -------------------------------------------------

    relacion = (
        CalendarioPeriodo.objects
        .filter(calendario=cal)
        .select_related("periodo")
        .first()
    )

    periodo_nombre = (
        relacion.periodo.nombre
        if relacion else None
    )

    # -------------------------------------------------
    # OBTENER LÍMITES DE FECHAS
    # -------------------------------------------------

    limites = limites_fechas_calendario(
        cal,
        periodo_nombre
    )

    if limites is None:
        return JsonResponse({
            "estado": "fallo",
            "icon": "error",
            "title": "Regla de fechas no disponible",
            "descripcion": (
                "No hay una regla de fechas configurada "
                "para el período académico asociado."
            )
        })

    # -------------------------------------------------
    # RESPUESTA
    # -------------------------------------------------

    return JsonResponse({
        "estado": "exito",

        "calendario": {
            "id": cal.id_calendario_academico,

            "periodo_id": (
                relacion.periodo_id
                if relacion else None
            ),

            "periodo": periodo_nombre,

            "descripcion": cal.descripcion,

            "fecha_inicio": cal.fecha_inicio.strftime(
                "%Y-%m-%d"
            ),

            "fecha_final": cal.fecha_final.strftime(
                "%Y-%m-%d"
            ),

            "tipo": cal.tipo,

            "tipo_display": cal.get_tipo_display(),

            "limites": limites
        }
    })

def vis_cal_reg(request):
    return render(request, "Roles/Director_General/calendario/visualizar_calendario.html")

# guardar_actualizar_calendario
def calendario_guardar(request):

    if request.method != "POST":
        return JsonResponse({
            "estado": "fallo",
            "icon": "warning",
            "title": "Solicitud no válida",
            "descripcion": "Método de solicitud no permitido."
        })

    # -------------------------------------------------
    # OBTENER DATOS
    # -------------------------------------------------

    id_calendario = request.POST.get("id_calendario")

    inicio = request.POST.get("fecha_inicio")
    final = request.POST.get("fecha_finalizado")

    descripcion = request.POST.get(
        "descripcion", ""
    ).strip()

    # -------------------------------------------------
    # VALIDAR DESCRIPCIÓN
    # -------------------------------------------------

    if not descripcion:
        return JsonResponse({
            "estado": "fallo",
            "icon": "warning",
            "title": "Descripción requerida",
            "descripcion": (
                "Ingrese la descripción del calendario."
            )
        })

    if len(descripcion) > 150:
        return JsonResponse({
            "estado": "fallo",
            "icon": "warning",
            "title": "Descripción demasiado larga",
            "descripcion": (
                "La descripción no puede superar "
                "los 150 caracteres."
            )
        })

    # -------------------------------------------------
    # VALIDAR FECHAS
    # -------------------------------------------------

    controles = [
        (
            inicio,
            "Fecha de Inicio del Tramo",
            "Por favor, ingrese la fecha inicial."
        ),
        (
            final,
            "Fecha de Finalización",
            "Por favor, ingrese la fecha final."
        )
    ]

    for value, field_name, error_message in controles:

        if not value:
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": field_name,
                "descripcion": error_message
            })

    # -------------------------------------------------
    # BUSCAR CALENDARIO
    # -------------------------------------------------

    try:

        calendario_original = (
            CalendarioAcademico.objects.get(
                id_calendario_academico=id_calendario
            )
        )

    except (
        CalendarioAcademico.DoesNotExist,
        TypeError,
        ValueError
    ):

        return JsonResponse({
            "estado": "fallo",
            "icon": "error",
            "title": "Calendario no encontrado",
            "descripcion": (
                "No se encontró el calendario "
                "académico que desea actualizar."
            )
        })

    # -------------------------------------------------
    # CONVERTIR FECHAS
    # -------------------------------------------------

    try:

        fecha_inicio = datetime.strptime(
            inicio,
            "%Y-%m-%d"
        ).date()

        fecha_final = datetime.strptime(
            final,
            "%Y-%m-%d"
        ).date()

    except (ValueError, TypeError):

        return JsonResponse({
            "estado": "fallo",
            "icon": "warning",
            "title": "Fechas no válidas",
            "descripcion": (
                "Ingrese fechas válidas para "
                "actualizar el calendario."
            )
        })

    # -------------------------------------------------
    # OBTENER PERÍODO ACADÉMICO
    # -------------------------------------------------

    relacion = (
        CalendarioPeriodo.objects
        .filter(calendario=calendario_original)
        .select_related("periodo")
        .first()
    )

    periodo_nombre = (
        relacion.periodo.nombre
        if relacion else None
    )

    if (
        calendario_original.tipo in (
            "PERIODO",
            "CARGA_NOTAS"
        )
        and not periodo_nombre
    ):
        return JsonResponse({
            "estado": "fallo",
            "icon": "error",
            "title": "Período no asociado",
            "descripcion": (
                "No se puede validar el calendario "
                "porque no tiene un período académico asociado."
            )
        })

    # -------------------------------------------------
    # OBTENER LÍMITES DE FECHAS
    # -------------------------------------------------

    limites = limites_fechas_calendario(
        calendario_original,
        periodo_nombre
    )

    if limites is None:
        return JsonResponse({
            "estado": "fallo",
            "icon": "error",
            "title": "Regla de fechas no disponible",
            "descripcion": (
                "No hay una regla de fechas configurada "
                "para el período académico asociado."
            )
        })

    # -------------------------------------------------
    # VALIDAR RANGOS PERMITIDOS
    # -------------------------------------------------

    limites_fecha = {
        "fecha_inicio": (
            limites["fecha_inicio_min"],
            limites["fecha_inicio_max"]
        ),

        "fecha_final": (
            limites["fecha_final_min"],
            limites["fecha_final_max"]
        )
    }

    validaciones = [
        (
            "inicio",
            fecha_inicio,
            limites_fecha["fecha_inicio"]
        ),
        (
            "final",
            fecha_final,
            limites_fecha["fecha_final"]
        )
    ]

    for campo, fecha, (minimo, maximo) in validaciones:

        if not (
            date.fromisoformat(minimo)
            <= fecha
            <= date.fromisoformat(maximo)
        ):

            nombre_fecha = (
                "inicio"
                if campo == "inicio"
                else "finalización"
            )

            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Fecha fuera del rango permitido",
                "descripcion": (
                    f"La fecha de {nombre_fecha} debe estar "
                    f"entre {minimo} y {maximo}, según el tipo "
                    "y período académico."
                )
            })

    # -------------------------------------------------
    # VALIDAR ORDEN DE FECHAS
    # -------------------------------------------------

    if fecha_final < fecha_inicio:
        return JsonResponse({
            "estado": "fallo",
            "icon": "warning",
            "title": "Rango de fechas no válido",
            "descripcion": (
                "La fecha final no puede ser anterior "
                "a la fecha de inicio."
            )
        })

    # -------------------------------------------------
    # ACTUALIZAR CALENDARIO
    # -------------------------------------------------

    with transaction.atomic():

        calendario_original.fecha_inicio = fecha_inicio
        calendario_original.fecha_final = fecha_final
        calendario_original.descripcion = descripcion

        calendario_original.save(
            update_fields=[
                "fecha_inicio",
                "fecha_final",
                "descripcion"
            ]
        )

        # -------------------------------------------------
        # REGISTRAR BITÁCORA
        # -------------------------------------------------

        Bitacora.objects.create(
            nombre_usuario=request.session.get(
                "usuario_nombre"
            ),
            fecha_hora=timezone.now(),
            accion=(
                "Se actualizaron la descripción y las fechas "
                "del calendario académico."
            )
        )

    return JsonResponse({
        "estado": "exito",
        "icon": "success",
        "title": "Calendario actualizado",
        "descripcion": (
            "Se actualizaron la descripción y las fechas "
            "del calendario académico exitosamente."
        )
    })

def registrar_calendario_anual(anio):
    for evento in CALENDARIO_ACADEMICA:

        fecha_inicio = date(
            anio,
            evento["mes_inicio"],
            evento["dia_inicio"]
        )

        fecha_final = date(
            anio,
            evento["mes_final"],
            evento["dia_final"]
        )

        CalendarioAcademico.objects.get_or_create(
            fecha_inicio=fecha_inicio,
            fecha_final=fecha_final,
            descripcion=evento["descripcion"],
            tipo=evento["tipo"],
            defaults={
                "activo": evento["activo"]
            }
        )

# registrar calendario
def reg_calendario(request):
    if request.method == "POST":
        tipo = request.POST.get("tipo")
        periodo_id = request.POST.get("periodo")
        fecha_inicio_str = request.POST.get("fecha_inicio")
        fecha_final_str = request.POST.get("fecha_final")
        descripcion = request.POST.get("descripcion")

        if not tipo or not fecha_inicio_str or not fecha_final_str or not descripcion:
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Campos incompletos",
                "descripcion": (
                    "Por favor complete todos los campos "
                    "obligatorios del formulario."
                )
            })

        try:
            fecha_inicio = datetime.strptime(fecha_inicio_str, "%Y-%m-%d").date()

            fecha_final = datetime.strptime(fecha_final_str, "%Y-%m-%d").date()
        except ValueError:
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Fecha inválida",
                "descripcion": "Las fechas proporcionadas no son válidas."
            })

        # VALIDAR RANGO
        if fecha_inicio > fecha_final:
            return JsonResponse({
                "estado": "fallo",
                "icon": "warning",
                "title": "Rango de fechas inválido",
                "descripcion": (
                    "La fecha de inicio no puede ser "
                    "posterior a la fecha final."
                )
            })

        # AÑO DEL CALENDARIO
        anio_calendario = fecha_inicio.year

        # PERÍODO ACADÉMICO
        periodo_obj = None

        tipos_sin_periodo = [
            "VACACIONES",
            "NO_LABORABLE",
            "INSCRIPCION_TRIMESTRE",
            "INSCRIPCION_SEMESTRE",
            "GRADUACION",
            "ANIVERSARIO",
            "ACTIVIDADES",
        ]

        if tipo not in tipos_sin_periodo:
            if not periodo_id:
                return JsonResponse({
                    "estado": "fallo",
                    "icon": "warning",
                    "title": "Período académico requerido",
                    "descripcion": (
                        "Debe seleccionar un período académico "
                        "para este tipo de registro."
                    )
                })

            try:
                periodo_obj = PeriodoAcademico.objects.get(pk=periodo_id)
            except PeriodoAcademico.DoesNotExist:
                return JsonResponse({
                    "estado": "fallo",
                    "icon": "warning",
                    "title": "Período no encontrado",
                    "descripcion": (
                        "El período académico seleccionado "
                        "no existe."
                    )
                })

        try:
            with transaction.atomic():
                # DESACTIVAR REGISTROS DE AÑOS ANTERIORES
                CalendarioAcademico.objects.filter(
                    tipo=tipo,
                    activo=True,
                    fecha_inicio__year__lt=anio_calendario
                ).update(
                    activo=False
                )

                # VALIDAR DUPLICADO PARA PERÍODOS ACADÉMICOS
                if tipo in ["PERIODO", "CARGA_NOTAS"]:

                    if periodo_obj:

                        existe = CalendarioPeriodo.objects.filter(
                            periodo=periodo_obj,
                            calendario__tipo=tipo,
                            calendario__activo=True,
                            calendario__fecha_inicio__year=anio_calendario
                        ).exists()

                        if existe:
                            return JsonResponse({
                                "estado": "fallo",
                                "icon": "warning",
                                "title": "Registro existente",
                                "descripcion": (
                                    f"El período "
                                    f"'{periodo_obj.nombre}' "
                                    f"ya tiene un calendario "
                                    f"registrado para el año "
                                    f"{anio_calendario}."
                                )
                            })

                # TIPOS QUE SOLO PUEDEN TENER UN REGISTRO POR AÑO
                elif tipo == "ANIVERSARIO":

                    existe = CalendarioAcademico.objects.filter(
                        tipo=tipo,
                        activo=True,
                        fecha_inicio__year=anio_calendario
                    ).exists()

                    if existe:
                        return JsonResponse({
                            "estado": "fallo",
                            "icon": "warning",
                            "title": "Registro existente",
                            "descripcion": (
                                "Ya existe un calendario activo "
                                f"de tipo '{tipo}' para el año "
                                f"{anio_calendario}."
                            )
                        })

                # GENERAR CALENDARIO BASE DEL AÑO
                existe_calendario_anio = CalendarioAcademico.objects.filter(
                    fecha_inicio__year=anio_calendario
                ).exists()

                if not existe_calendario_anio:
                    registrar_calendario_anual(
                        anio_calendario
                    )

                # CREAR CALENDARIO MANUAL
                calendario = CalendarioAcademico.objects.create(
                    fecha_inicio=fecha_inicio,
                    fecha_final=fecha_final,
                    descripcion=descripcion,
                    tipo=tipo,
                    activo=True
                )

                # RELACIÓN CON PERÍODO
                if periodo_obj:
                    CalendarioPeriodo.objects.create(
                        periodo=periodo_obj,
                        calendario=calendario
                    )

                # BITÁCORA
                Bitacora.objects.create(
                    nombre_usuario=request.session.get(
                        "usuario_nombre"
                    ),
                    fecha_hora=timezone.now(),
                    accion=(
                        f"Registró un evento en el calendario: "
                        f"{descripcion} ({tipo}) "
                        f"correspondiente al año "
                        f"{anio_calendario}."
                    )
                )

            return JsonResponse({
                "estado": "exito",
                "icon": "success",
                "title": "Éxito",
                "descripcion": (
                    f"El calendario del año "
                    f"{anio_calendario} se registró "
                    "exitosamente."
                )
            })

        except Exception as e:

            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Error del sistema",
                "descripcion": (
                    "Ocurrió un error interno al guardar "
                    "los datos: "
                    f"{str(e)}"
                )
            })

    return render(request, "Roles/Director_General/calendario/registrar_calendario.html")
