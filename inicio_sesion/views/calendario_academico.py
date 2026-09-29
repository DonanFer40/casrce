from django.shortcuts import render
from django.http import JsonResponse
from datetime import datetime, date
from django.db import transaction
from django.utils import timezone

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
    if request.method == "POST":
        id_calendario = request.POST.get("id_calendario")

        try:
            relacion = (
                CalendarioPeriodo.objects
                .select_related(
                    "periodo",
                    "calendario"
                )
                .get(
                    calendario_id=id_calendario
                )
            )

        except CalendarioPeriodo.DoesNotExist:
            return JsonResponse({
                "estado": "fallo",
                "icon": "error",
                "title": "Error",
                "descripcion": (
                    "No se encuentra registrado "
                    "el calendario académico."
                )
            })

        cal = relacion.calendario
        periodo = relacion.periodo

        return JsonResponse({
            "estado": "exito",
            "calendario": {
                "id": cal.id_calendario_academico,
                "periodo_id": (
                    periodo.id_periodo_academico
                ),
                "periodo": periodo.nombre,
                "fecha_inicio": cal.fecha_inicio.strftime(
                    "%Y-%m-%d"
                ),

                "fecha_final": cal.fecha_final.strftime(
                    "%Y-%m-%d"
                ),
                "descripcion": cal.descripcion,
                "tipo": cal.tipo,
                "tipo_display": cal.get_tipo_display(),
            }
        })

def vis_cal_reg(request):
    return render(request, "Roles/Director_General/calendario/visualizar_calendario.html")

# guardar_actualizar_calendario
def calendario_guardar(request):
    if request.method == "POST":
        id_calendario = request.POST.get("id_calendario")
        inicio = request.POST.get("fecha_inicio")
        final = request.POST.get("fecha_finalizado")

        controles = [
            (inicio, "Fecha de Inicio del Tramo", "Por favor, ingrese la fecha inicial."),
        ]

        for value, field_name, error_message in controles:
            if not value:
                return JsonResponse({
                    "estado": "falla",
                    "icon": "warning",
                    "title": field_name,
                    "descripcion": error_message
                })
        try:
            calendario_original = CalendarioAcademico.objects.get(id_calendario_academico=id_calendario)
        except CalendarioAcademico.DoesNotExist:
            return JsonResponse({
                "estado": "falla",
                "icon": "error",
                "title": "Error",
                "descripcion": "Calendario no encontrado."
            })

        try:
            fecha_inicio = datetime.strptime(inicio, "%Y-%m-%d").date()
            fecha_final = datetime.strptime(final, "%Y-%m-%d").date()
            
            calendario_original.fecha_inicio = fecha_inicio
            calendario_original.fecha_final = fecha_final
            calendario_original.save()
    
            Bitacora.objects.create(
                nombre_usuario=request.session.get("usuario_nombre"),
                fecha_hora=timezone.now(),
                accion=f"Se actualizo el calendario académico."
            ) 
            
            return JsonResponse({
                "estado": "exito",
                "icon": "success",
                "title": "Exito",
                "descripcion": "Se actualizo la fecha exitosamente."
            })
        except Exception as e:
            return JsonResponse({
                "estado": "falla",
                "icon": "error",
                "title": "Error",
                "descripcion": "Ocurrio un error al momento de realizar la prorroga."
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

