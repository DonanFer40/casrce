from django.http import JsonResponse
from django.db import transaction
from decimal import Decimal, ROUND_HALF_UP
from django.utils import timezone
from django.db.models import Count, Value, TextField, Q
from django.db.models.functions import Concat

from inicio_sesion.models import Estudiante, EstatusEstudiante, Materia, TrayectoAcademico

from notas_academicas.models import Reparacion, PromedioFinal, Calificaciones

@transaction.atomic
def calc_prom_est(request):

    PERIODOS_INICIALES = {
        "Inicial Trimestre",
        "Inicial Semestre"
    }

    PERIODOS_TRAMOS = {
        "Tramo I",
        "Tramo II",
        "Tramo III"
    }

    PERIODOS_SEMESTRES = {
        "Semestre I",
        "Semestre II"
    }

    NOTA_MINIMA = Decimal("12")
    NOTA_MINIMA_PROYECTO = Decimal("16")
    ASISTENCIA_MINIMA = 75
    MAXIMO_REPROBADAS = 3

    ORDEN_TRAYECTOS = {
        "Trayecto Inicial": 0,
        "Trayecto I": 1,
        "Trayecto II": 2,
        "Trayecto III": 3,
        "Trayecto IV": 4,
        "Trayecto V": 5,
    }

    calificaciones = (
        Calificaciones.objects
        .select_related(
            "estudiante",
            "materia_asignada",
            "materia_asignada__materia",
            "materia_asignada__materia__id_pnf",
            "materia_asignada__materia__id_trayecto",
            "periodo_materia__periodo",
            "trayecto",
        )
        .filter(
            estudiante__isnull=False,
            materia_asignada__isnull=False,
            promedio_tramo__isnull=False,
            periodo_materia__isnull=False,
            fecha_promedio__isnull=False,
        )
    )

    cantidad_guardada = 0
    grupos = {}

    # =========================================================
    # AGRUPAR CALIFICACIONES
    # =========================================================

    for c in calificaciones:

        materia = c.materia_asignada.materia
        trayecto = c.trayecto
        pnf = materia.id_pnf

        if not trayecto or not pnf:
            continue

        nombre_trayecto = (trayecto.nombre or "").strip()
        tipo_periodo = (pnf.periodo_academico or "").strip()

        periodo_nombre = (
            (c.periodo_materia.periodo.nombre or "").strip()
            if c.periodo_materia and c.periodo_materia.periodo
            else ""
        )

        # -----------------------------------------------------
        # REPARACIÓN SE PROCESARÁ APARTE
        # -----------------------------------------------------

        if periodo_nombre == "Reparación":
            continue

        if nombre_trayecto == "Reparación":
            continue

        # -----------------------------------------------------
        # VALIDAR TIPO DE PERÍODO
        # -----------------------------------------------------

        if tipo_periodo not in {"Trimestre", "Semestre"}:
            continue

        # -----------------------------------------------------
        # TRAYECTO INICIAL
        # -----------------------------------------------------

        if nombre_trayecto == "Trayecto Inicial":

            periodo_inicial_esperado = (
                "Inicial Trimestre"
                if tipo_periodo == "Trimestre"
                else "Inicial Semestre"
            )

            if periodo_nombre != periodo_inicial_esperado:
                continue

        # -----------------------------------------------------
        # TRAYECTOS REGULARES
        # -----------------------------------------------------

        else:

            limite = (
                4
                if tipo_periodo == "Trimestre"
                else 5
            )

            trayectos_validos = {
                nombre
                for nombre, posicion in ORDEN_TRAYECTOS.items()
                if posicion <= limite
            }

            if nombre_trayecto not in trayectos_validos:
                continue

            if periodo_nombre in PERIODOS_INICIALES:
                continue

        # -----------------------------------------------------
        # AÑO ACADÉMICO
        # -----------------------------------------------------

        fecha_eval = c.fecha_promedio
        anio = fecha_eval.year

        # -----------------------------------------------------
        # AGRUPACIÓN
        # -----------------------------------------------------

        if nombre_trayecto == "Trayecto Inicial":

            clave = (
                c.estudiante_id,
                c.materia_asignada_id,
                trayecto.id_periodo_academico,
                fecha_eval,
                c.id_calificaciones,
            )

        else:

            clave = (
                c.estudiante_id,
                c.materia_asignada_id,
                trayecto.id_periodo_academico,
                anio,
            )

        grupos.setdefault(
            clave,
            {
                "estudiante": c.estudiante,
                "materia": materia,
                "materia_asignada": c.materia_asignada,
                "trayecto": trayecto,
                "pnf": pnf,
                "anio": anio,
                "fecha_promedio": fecha_eval,
                "calificaciones": [],
            }
        )["calificaciones"].append(c)

    # =========================================================
    # PROCESAR PROMEDIOS NORMALES
    # =========================================================

    for grupo in grupos.values():

        estudiante = grupo["estudiante"]
        materia = grupo["materia"]
        materia_asignada = grupo["materia_asignada"]
        trayecto = grupo["trayecto"]
        pnf = grupo["pnf"]
        anio = grupo["anio"]
        fecha_eval = grupo["fecha_promedio"]
        calificaciones_materia = grupo["calificaciones"]

        nombre_trayecto = (trayecto.nombre or "").strip()
        tipo_periodo = (pnf.periodo_academico or "").strip()
        nombre_materia = (materia.nombre or "").strip().lower()

        # -----------------------------------------------------
        # PROYECTO SOCIO-TECNOLÓGICO
        # -----------------------------------------------------

        es_proyecto = any(
            texto in nombre_materia
            for texto in (
                "proyecto socio tecnologico",
                "proyecto socio-tecnologico",
                "proyecto sociotecnologico",
                "proyecto socio integrador",
                "proyecto socio-integrador",
                "proyecto sociointegrador",
            )
        )

        calificaciones_validas = []
        promedio_final = Decimal("0")

        # =====================================================
        # TRAYECTO INICIAL
        # =====================================================

        if nombre_trayecto == "Trayecto Inicial":

            periodo_inicial_esperado = (
                "Inicial Trimestre"
                if tipo_periodo == "Trimestre"
                else "Inicial Semestre"
            )

            calificaciones_iniciales = [
                c
                for c in calificaciones_materia
                if (
                    c.periodo_materia
                    and c.periodo_materia.periodo
                    and (
                        c.periodo_materia.periodo.nombre or ""
                    ).strip() == periodo_inicial_esperado
                )
            ]

            if not calificaciones_iniciales:
                continue

            calificacion_inicial = calificaciones_iniciales[0]

            calificaciones_validas = [
                calificacion_inicial
            ]

            # NO SE CALCULA.
            # SE TRANSFIERE DIRECTAMENTE.
            promedio_final = (
                calificacion_inicial.promedio_tramo
            )

        # =====================================================
        # TRAYECTOS REGULARES
        # =====================================================

        else:

            periodos_objetivo = (
                PERIODOS_TRAMOS
                if tipo_periodo == "Trimestre"
                else PERIODOS_SEMESTRES
            )

            periodos_configurados = {
                (pm.periodo.nombre or "").strip()
                for pm in materia.periodos_academicos.all()
                if (
                    pm.periodo
                    and (
                        pm.periodo.nombre or ""
                    ).strip() in periodos_objetivo
                )
            }

            if not periodos_configurados:
                continue

            calificaciones_filtradas = [
                c
                for c in calificaciones_materia
                if (
                    c.periodo_materia
                    and c.periodo_materia.periodo
                    and (
                        c.periodo_materia.periodo.nombre or ""
                    ).strip() in periodos_configurados
                )
            ]

            periodos_registrados = {
                (
                    c.periodo_materia.periodo.nombre or ""
                ).strip()
                for c in calificaciones_filtradas
                if (
                    c.periodo_materia
                    and c.periodo_materia.periodo
                )
            }

            # Todos los períodos deben estar registrados.
            if not periodos_configurados.issubset(
                periodos_registrados
            ):
                continue

            calificaciones_validas = (
                calificaciones_filtradas
            )

            if len(periodos_configurados) == 1:

                promedio_final = (
                    calificaciones_validas[0].promedio_tramo
                )

            else:

                promedio_final = (
                    sum(
                        c.promedio_tramo
                        for c in calificaciones_validas
                    )
                    / Decimal(
                        len(calificaciones_validas)
                    )
                )

        # =====================================================
        # REDONDEAR
        # =====================================================

        promedio_final = promedio_final.quantize(
            Decimal("1"),
            rounding=ROUND_HALF_UP
        )

        # =====================================================
        # ASISTENCIA
        # =====================================================

        asistencias = [
            c.asistencia
            for c in calificaciones_validas
            if c.asistencia is not None
        ]

        if asistencias:

            asistencia = int(
                (
                    Decimal(sum(asistencias))
                    / Decimal(len(asistencias))
                ).quantize(
                    Decimal("1"),
                    rounding=ROUND_HALF_UP
                )
            )

        else:

            asistencia = 0

        # =====================================================
        # NOTA MÍNIMA
        # =====================================================

        nota_minima = (
            NOTA_MINIMA_PROYECTO
            if es_proyecto
            else NOTA_MINIMA
        )

        aprobado_nota = (
            promedio_final >= nota_minima
        )

        aprobado_asistencia = (
            asistencia >= ASISTENCIA_MINIMA
        )

        # =====================================================
        # ESTADO NORMAL
        # =====================================================

        if aprobado_nota and aprobado_asistencia:

            estado = "APROBADO"

            motivo = (
                f"Materia aprobada. "
                f"Año académico: {anio}. "
                f"Promedio final: {promedio_final}. "
                f"Nota mínima: {nota_minima}. "
                f"Asistencia: {asistencia}%."
            )

        else:

            estado = "REPROBADO"

            motivos = []

            if not aprobado_nota:

                motivos.append(
                    f"promedio {promedio_final} "
                    f"menor a {nota_minima} pts"
                )

            if not aprobado_asistencia:

                motivos.append(
                    f"asistencia {asistencia}% "
                    f"menor al {ASISTENCIA_MINIMA}% requerido"
                )

            motivo = (
                f"Materia reprobada en el año {anio} "
                f"debido a: "
                + " y ".join(motivos)
                + "."
            )

        # =====================================================
        # CREAR O ACTUALIZAR PROMEDIO FINAL
        # =====================================================

        promedio_existente = (
            PromedioFinal.objects.filter(
                estudiante=estudiante,
                materia_asignacion=materia_asignada,
                trayecto=trayecto,
                fecha_promedio__year=anio
            )
            .first()
        )

        if promedio_existente:

            promedio_existente.promedio_final = promedio_final
            promedio_existente.asistencia = asistencia
            promedio_existente.estado = estado
            promedio_existente.fecha_promedio = fecha_eval
            promedio_existente.motivo = motivo
            promedio_existente.save(
                update_fields=[
                    "promedio_final",
                    "asistencia",
                    "estado",
                    "fecha_promedio",
                    "motivo",
                ]
            )

        else:

            PromedioFinal.objects.create(
                estudiante=estudiante,
                materia_asignacion=materia_asignada,
                trayecto=trayecto,
                promedio_final=promedio_final,
                asistencia=asistencia,
                estado=estado,
                fecha_promedio=fecha_eval,
                motivo=motivo,
            )

        cantidad_guardada += 1

    # =========================================================
    # PROCESAR REPARACIÓN
    # =========================================================

    reparaciones = (
        Calificaciones.objects
        .select_related(
            "estudiante",
            "materia_asignada",
            "materia_asignada__materia",
            "materia_asignada__materia__id_pnf",
            "trayecto",
            "periodo_materia__periodo",
        )
        .filter(
            estudiante__isnull=False,
            materia_asignada__isnull=False,
            promedio_tramo__isnull=False,
            periodo_materia__isnull=False,
            fecha_promedio__isnull=False,
            periodo_materia__periodo__nombre="Reparación",
        )
    )

    for reparacion in reparaciones:

        estudiante = reparacion.estudiante
        materia_asignada = reparacion.materia_asignada
        materia = materia_asignada.materia
        trayecto = reparacion.trayecto
        pnf = materia.id_pnf

        if not trayecto or not pnf:
            continue

        nombre_trayecto = (
            trayecto.nombre or ""
        ).strip()

        # Trayecto Reparación no es un trayecto académico.
        if nombre_trayecto == "Reparación":
            continue

        anio = reparacion.fecha_promedio.year

        nombre_materia = (
            materia.nombre or ""
        ).strip().lower()

        es_proyecto = any(
            texto in nombre_materia
            for texto in (
                "proyecto socio tecnologico",
                "proyecto socio-tecnologico",
                "proyecto sociotecnologico",
                "proyecto socio integrador",
                "proyecto socio-integrador",
                "proyecto sociointegrador",
            )
        )

        nota_minima = (
            NOTA_MINIMA_PROYECTO
            if es_proyecto
            else NOTA_MINIMA
        )

        promedio_reparacion = (
            reparacion.promedio_tramo
        )

        promedio_reparacion = (
            promedio_reparacion.quantize(
                Decimal("1"),
                rounding=ROUND_HALF_UP
            )
        )

        asistencia_reparacion = (
            reparacion.asistencia
            if reparacion.asistencia is not None
            else 0
        )

        asistencia_reparacion = int(
            Decimal(asistencia_reparacion).quantize(
                Decimal("1"),
                rounding=ROUND_HALF_UP
            )
        )

        aprobado_reparacion = (
            promedio_reparacion >= nota_minima
            and asistencia_reparacion >= ASISTENCIA_MINIMA
        )

        promedio_existente = (
            PromedioFinal.objects.filter(
                estudiante=estudiante,
                materia_asignacion=materia_asignada,
                trayecto=trayecto,
                fecha_promedio__year=anio,
            )
            .first()
        )

        # -----------------------------------------------------
        # SI NO EXISTE EL PROMEDIO NORMAL, NO PROCESAR
        # -----------------------------------------------------

        if not promedio_existente:
            continue

        # -----------------------------------------------------
        # SOLO LAS MATERIAS REPROBADAS PUEDEN IR A REPARACIÓN
        # -----------------------------------------------------

        if promedio_existente.estado != "REPROBADO":
            continue

        if aprobado_reparacion:

            estado = "APROBADO_REPARACION"

            motivo = (
                f"Materia aprobada en Reparación. "
                f"Año académico: {anio}. "
                f"Promedio de Reparación: "
                f"{promedio_reparacion}. "
                f"Nota mínima: {nota_minima}. "
                f"Asistencia: "
                f"{asistencia_reparacion}%."
            )

        else:

            estado = "REPROBADO_REPARACION"

            motivos = []

            if promedio_reparacion < nota_minima:

                motivos.append(
                    f"promedio {promedio_reparacion} "
                    f"menor a {nota_minima} pts"
                )

            if asistencia_reparacion < ASISTENCIA_MINIMA:

                motivos.append(
                    f"asistencia {asistencia_reparacion}% "
                    f"menor al {ASISTENCIA_MINIMA}% requerido"
                )

            motivo = (
                f"Materia reprobada en Reparación "
                f"en el año {anio} debido a: "
                + " y ".join(motivos)
                + "."
            )

        # -----------------------------------------------------
        # ACTUALIZAR EL MISMO PROMEDIO FINAL
        # -----------------------------------------------------

        promedio_existente.promedio_final = (
            promedio_reparacion
        )

        promedio_existente.asistencia = (
            asistencia_reparacion
        )

        promedio_existente.estado = estado

        promedio_existente.fecha_promedio = (
            reparacion.fecha_promedio
        )

        promedio_existente.motivo = motivo

        promedio_existente.save(
            update_fields=[
                "promedio_final",
                "asistencia",
                "estado",
                "fecha_promedio",
                "motivo",
            ]
        )

    # =========================================================
    # DETERMINAR MATERIAS REPROBADAS POR TRAYECTO
    # =========================================================

    estados_reprobados = {
        "REPROBADO",
        "REPROBADO_REPARACION",
    }

    estudiantes_trayectos = (
        PromedioFinal.objects
        .filter(
            estado__in=estados_reprobados
        )
        .values(
            "estudiante_id",
            "trayecto_id"
        )
        .annotate(
            cantidad_reprobadas=Count("id_promedio_final")
        )
    )

    # =========================================================
    # ACTUALIZAR MOTIVO CUANDO SUPERA LAS 3 REPROBADAS
    # =========================================================

    for registro in estudiantes_trayectos:

        if (
            registro["cantidad_reprobadas"]
            <= MAXIMO_REPROBADAS
        ):
            continue

        estudiante_id = registro["estudiante_id"]
        trayecto_id = registro["trayecto_id"]

        PromedioFinal.objects.filter(
            estudiante_id=estudiante_id,
            trayecto_id=trayecto_id,
            estado__in=estados_reprobados,
        ).update(
            motivo=Concat(
                "motivo",
                Value(
                    " El estudiante supera el máximo de "
                    f"{MAXIMO_REPROBADAS} materias reprobadas "
                    "para este trayecto y no puede pasar "
                    "al siguiente trayecto académico."
                ),
                output_field=TextField(),
            )
        )

    return JsonResponse({
        "estado": "exito",
        "title": "Éxito",
        "icon": "success",
        "descripcion": (
            f"Se procesaron {cantidad_guardada} "
            f"promedios finales correctamente."
        ),
        "cantidad": cantidad_guardada,
    })

@transaction.atomic
def act_prom_rep(request):
    reparaciones = Reparacion.objects.select_related(
        "estudiante",
        "evaluacion_reparacion",
        "evaluacion_reparacion__materia_asignacion",
        "evaluacion_reparacion__materia_asignacion__materia",
        "evaluacion_reparacion__materia_asignacion__materia__id_trayecto"
    ).filter(
        calificacion__isnull=False
    )

    actualizados = 0
    no_encontrados = 0
    errores = 0

    for reparacion in reparaciones:
        try:
            # Validar estudiante y evaluación
            if (not reparacion.estudiante or not reparacion.evaluacion_reparacion):
                no_encontrados += 1
                continue

            evaluacion = reparacion.evaluacion_reparacion

            materia_asignacion = evaluacion.materia_asignacion

            if not materia_asignacion:
                no_encontrados += 1
                continue

            # Obtener trayecto desde Materia
            trayecto = materia_asignacion.materia.id_trayecto

            # Buscar promedio final existente
            promedio = PromedioFinal.objects.filter(
                estudiante=reparacion.estudiante,
                materia_asignacion=materia_asignacion,
                trayecto=trayecto
            ).first()
            if not promedio:
                no_encontrados += 1
                continue

            nota_reparacion = reparacion.calificacion or Decimal("0")

            # Actualizar promedio
            promedio.promedio_final = nota_reparacion
            promedio.fecha_promedio = timezone.now().date()

            if nota_reparacion >= Decimal("12"):
                promedio.estado = "APROBADO_REPARACION"

                promedio.motivo = (
                    f"Aprobado mediante reparación "
                    f"con nota {nota_reparacion}."
                )
            else:
                promedio.estado = "REPROBADO_REPARACION"

                promedio.motivo = (
                    f"Reprobado mediante reparación "
                    f"con nota {nota_reparacion}."
                )

            promedio.save(
                update_fields=[
                    "promedio_final",
                    "estado",
                    "fecha_promedio",
                    "motivo"
                ]
            )

            actualizados += 1

        except Exception:
            errores += 1
            continue

    return JsonResponse({
        "estado": "ok",
        "title": "Proceso completado",
        "icon": "success",
        "descripcion": (
            f"Se actualizaron {actualizados} promedios con reparación. "
            f"No encontrados: {no_encontrados}. "
            f"Errores: {errores}."
        ),
        "actualizados": actualizados,
        "no_encontrados": no_encontrados,
        "errores": errores

    })

@transaction.atomic
def act_tray_est(request):

    NOTA_MINIMA_GENERAL = Decimal("12")
    NOTA_MINIMA_PROYECTO = Decimal("16")
    ASISTENCIA_MINIMA = Decimal("75")
    MAX_REPROBADAS = 3

    ANO_ACTUAL = timezone.localdate().year

    ESTADOS_APROBADOS = {
        "APROBADO",
        "APROBADO_REPARACION",
    }

    ESTADOS_REPROBADOS = {
        "REPROBADO",
        "REPROBADO_REPARACION",
    }

    # =========================================================
    # TRAYECTOS ACADÉMICOS
    # =========================================================

    ORDEN_TRAYECTOS = {
        "trayecto inicial": 1,
        "trayecto i": 2,
        "trayecto ii": 3,
        "trayecto iii": 4,
        "trayecto iv": 5,
        "trayecto v": 6,
    }

    def normalizar_nombre(nombre):
        return (nombre or "").strip().lower()

    trayectos_db = list(TrayectoAcademico.objects.all())

    trayectos_por_nombre = {
        normalizar_nombre(trayecto.nombre): trayecto
        for trayecto in trayectos_db
        if normalizar_nombre(trayecto.nombre) in ORDEN_TRAYECTOS
    }

    trayecto_inicial = trayectos_por_nombre.get("trayecto inicial")
    trayecto_i = trayectos_por_nombre.get("trayecto i")

    if trayecto_inicial is None or trayecto_i is None:
        return JsonResponse({
            "success": False,
            "title": "Configuración académica incompleta",
            "icon": "error",
            "descripcion": (
                "No se encontraron los registros Trayecto Inicial "
                "y Trayecto I en la base de datos."
            ),
        })

    trayectos = sorted(
        trayectos_por_nombre.values(),
        key=lambda trayecto: ORDEN_TRAYECTOS[
            normalizar_nombre(trayecto.nombre)
        ],
    )

    posiciones_trayectos = {
        trayecto.id_periodo_academico: posicion
        for posicion, trayecto in enumerate(trayectos)
    }

    # =========================================================
    # ESTUDIANTES
    # =========================================================

    estudiantes = (
        Estudiante.objects
        .select_related("pnf", "nucleo")
        .prefetch_related(
            "estatus",
            "promedios_finales__materia_asignacion__materia",
        )
    )

    actualizados = 0
    no_actualizados = 0
    egresados = 0
    avances_por_trayecto = {}

    # =========================================================
    # IDENTIFICAR PROYECTO SOCIOTECNOLÓGICO
    # =========================================================

    def es_materia_proyecto(materia, es_inicial=False):

        if es_inicial:
            return False

        nombre = normalizar_nombre(materia.nombre)

        nombre = (
            nombre
            .replace("-", " ")
            .replace("–", " ")
            .replace("—", " ")
        )

        if "proyecto nacional" in nombre:
            return False

        patrones_validos = (
            "proyecto socio tecnologico",
            "proyecto socio tecnológico",
            "proyecto socio integrador",
            "proyecto sociointegrador",
        )

        return any(
            patron in nombre
            for patron in patrones_validos
        )

    # =========================================================
    # DETERMINAR SI UN PROMEDIO ESTÁ REPROBADO
    # =========================================================

    def promedio_reprobado(promedio):

        estado = (promedio.estado or "").strip().upper()

        if estado in ESTADOS_REPROBADOS:
            return True

        if estado in ESTADOS_APROBADOS:
            return False

        if (
            promedio.promedio_final is None
            or promedio.asistencia is None
        ):
            return False

        materia = promedio.materia_asignacion.materia

        nota_minima = (
            NOTA_MINIMA_PROYECTO
            if materia and es_materia_proyecto(materia)
            else NOTA_MINIMA_GENERAL
        )

        return (
            promedio.promedio_final < nota_minima
            or promedio.asistencia < ASISTENCIA_MINIMA
        )

    # =========================================================
    # PROCESAR ESTUDIANTES
    # =========================================================

    for estudiante in estudiantes:

        # =====================================================
        # ESTATUS ACTUAL
        # =====================================================

        estatus_actual = (
            estudiante.estatus
            .select_related("trayecto")
            .order_by(
                "-fecha_ingreso",
                "-id_estatus_estudiante",
            )
            .first()
        )

        if not estatus_actual or not estatus_actual.trayecto:
            no_actualizados += 1
            continue

        trayecto_actual = estatus_actual.trayecto

        if estatus_actual.estado == "Egreso":
            no_actualizados += 1
            continue

        # =====================================================
        # VALIDAR PNF
        # =====================================================

        periodo_pnf = (
            estudiante.pnf.periodo_academico or ""
        ).strip()

        if periodo_pnf not in {"Trimestre", "Semestre"}:
            no_actualizados += 1
            continue

        # =====================================================
        # POSICIÓN DEL TRAYECTO ACTUAL
        # =====================================================

        posicion_actual = posiciones_trayectos.get(
            trayecto_actual.id_periodo_academico
        )

        if posicion_actual is None:
            no_actualizados += 1
            continue

        nombre_trayecto_actual = normalizar_nombre(
            trayecto_actual.nombre
        )

        es_tr_inicial = (
            nombre_trayecto_actual == "trayecto inicial"
        )

        es_trayecto_i = (
            nombre_trayecto_actual == "trayecto i"
        )

        # =====================================================
        # OBTENER PROMEDIOS DEL AÑO ACTUAL
        # =====================================================

                
        # =====================================================
        # OBTENER PROMEDIOS ACTUALES E HISTÓRICOS
        # =====================================================

        todos_los_promedios = list(
            estudiante.promedios_finales
            .select_related(
                "materia_asignacion__materia",
                "trayecto",
            )
            .filter(
                Q(fecha_promedio__year=ANO_ACTUAL)
                |
                Q(
                    trayecto=trayecto_i,
                    fecha_promedio__year__lt=ANO_ACTUAL,
                )
            )
            .order_by(
                "fecha_promedio",
                "id_promedio_final",
            )
        )


        # =====================================================
        # ÚLTIMO PROMEDIO POR MATERIA Y TRAYECTO
        # =====================================================

        def obtener_ultimos_promedios(
            trayecto_id,
            incluir_congelados=False,
        ):

            registros = {}

            for promedio in todos_los_promedios:

                if promedio.trayecto_id != trayecto_id:
                    continue

                if (
                    promedio.congelada
                    and not incluir_congelados
                ):
                    continue

                if not promedio.materia_asignacion_id:
                    continue

                materia = promedio.materia_asignacion.materia

                if not materia:
                    continue

                materia_id = materia.id_materia
                anterior = registros.get(materia_id)

                if anterior is None:
                    registros[materia_id] = promedio
                    continue

                clave_actual = (
                    promedio.fecha_promedio,
                    promedio.id_promedio_final,
                )

                clave_anterior = (
                    anterior.fecha_promedio,
                    anterior.id_promedio_final,
                )

                if clave_actual > clave_anterior:
                    registros[materia_id] = promedio

            return registros

        # =====================================================
        # DETECTAR PROMEDIOS CONGELADOS DEL TRAYECTO I
        # =====================================================

        # =====================================================
        # DETECTAR HISTORIAL DEL TRAYECTO I DE AÑOS ANTERIORES
        # =====================================================

        tiene_historial_trayecto_i = (
            PromedioFinal.objects.filter(
                estudiante=estudiante,
                trayecto=trayecto_i,
                fecha_promedio__year__lt=ANO_ACTUAL,
            )
            .exists()
        )

        
        # =====================================================
        # REPROBACIÓN DE MATERIA DE TRAYECTO INICIAL
        # DURANTE TRAYECTO I
        # =====================================================

        if es_trayecto_i:
            # Obtener los últimos promedios del Trayecto Inicial en el año en curso
            promedios_iniciales_actuales = obtener_ultimos_promedios(
                trayecto_inicial.id_periodo_academico,
                incluir_congelados=False
            )

            # Verificar si reprobó alguna materia del Trayecto Inicial
            reprobo_materia_inicial = any(
                promedio_reprobado(promedio)
                for materia_id, promedio in promedios_iniciales_actuales.items()
            )

            if reprobo_materia_inicial:

                # Congelar todos los promedios del Trayecto I
                PromedioFinal.objects.filter(
                    estudiante=estudiante,
                    trayecto=trayecto_i,
                    congelada=False
                ).update(
                    congelada=True,
                    fecha_congelacion=timezone.now()
                )

                # Regresar al Trayecto Inicial
                estatus_actual.trayecto = trayecto_inicial
                estatus_actual.save(update_fields=["trayecto"])

                avances_por_trayecto[trayecto_inicial.nombre] = (
                    avances_por_trayecto.get(trayecto_inicial.nombre, 0) + 1
                )

                actualizados += 1
                continue
        
        # =====================================================
        # EVALUAR UN TRAYECTO
        # =====================================================

        def evaluar_trayecto(
            trayecto,
            es_inicial=False,
            incluir_congelados=False,
        ):

            materias = list(
                Materia.objects.filter(
                    id_pnf=estudiante.pnf,
                    id_trayecto=trayecto,
                    activa=True,
                )
            )

            if not materias:
                return {
                    "existe": False,
                    "aprobado": False,
                    "total_materias": 0,
                    "materias_aprobadas": 0,
                    "materias_reprobadas": 0,
                    "materias_pendientes": 0,
                    "proyecto_aprobado": False,
                    "proyecto_reprobado": False,
                }

            promedios = obtener_ultimos_promedios(
                trayecto.id_periodo_academico,
                incluir_congelados=incluir_congelados,
            )

            materias_aprobadas = 0
            materias_reprobadas = 0
            materias_pendientes = 0
            proyecto_aprobado = False
            proyecto_reprobado = False

            for materia in materias:

                promedio = promedios.get(materia.id_materia)

                if promedio is None:
                    materias_pendientes += 1
                    continue

                es_proyecto = es_materia_proyecto(
                    materia,
                    es_inicial=es_inicial,
                )

                estado = (promedio.estado or "").strip().upper()

                if estado in ESTADOS_APROBADOS:

                    nota_minima = (
                        NOTA_MINIMA_PROYECTO
                        if es_proyecto
                        else NOTA_MINIMA_GENERAL
                    )

                    cumple_requisitos = (
                        promedio.promedio_final is not None
                        and promedio.promedio_final >= nota_minima
                        and promedio.asistencia is not None
                        and promedio.asistencia >= ASISTENCIA_MINIMA
                    )

                    if cumple_requisitos:
                        materias_aprobadas += 1

                        if es_proyecto:
                            proyecto_aprobado = True
                    else:
                        if es_proyecto:
                            proyecto_reprobado = True
                        else:
                            materias_reprobadas += 1

                    continue

                if estado in ESTADOS_REPROBADOS:
                    if es_proyecto:
                        proyecto_reprobado = True
                    else:
                        materias_reprobadas += 1
                    continue

                nota_requerida = (
                    NOTA_MINIMA_PROYECTO
                    if es_proyecto
                    else NOTA_MINIMA_GENERAL
                )

                nota_aprobada = (
                    promedio.promedio_final is not None
                    and promedio.promedio_final >= nota_requerida
                )

                asistencia_aprobada = (
                    promedio.asistencia is not None
                    and promedio.asistencia >= ASISTENCIA_MINIMA
                )

                if nota_aprobada and asistencia_aprobada:
                    materias_aprobadas += 1

                    if es_proyecto:
                        proyecto_aprobado = True
                else:
                    if es_proyecto:
                        proyecto_reprobado = True
                    else:
                        materias_reprobadas += 1

            
            if es_inicial:
                aprobado = (
                    materias_aprobadas >= 1
                    and materias_reprobadas <= MAX_REPROBADAS
                )
            else:
                porcentaje_minimo_aprobado = (
                    (len(materias) * 75 + 99) // 100
                )

                aprobado = (
                    materias_aprobadas >= porcentaje_minimo_aprobado
                    and materias_reprobadas <= MAX_REPROBADAS
                    and proyecto_aprobado
                    and not proyecto_reprobado
                )


            return {
                "existe": True,
                "aprobado": aprobado,
                "total_materias": len(materias),
                "materias_aprobadas": materias_aprobadas,
                "materias_reprobadas": materias_reprobadas,
                "materias_pendientes": materias_pendientes,
                "proyecto_aprobado": proyecto_aprobado,
                "proyecto_reprobado": proyecto_reprobado,
            }

            
        # =====================================================
        # RECUPERAR Y EVALUAR PROMEDIOS CONGELADOS DEL TRAYECTO I
        # =====================================================

        if es_tr_inicial and tiene_historial_trayecto_i:

            promedios_iniciales_actuales = obtener_ultimos_promedios(
                trayecto_inicial.id_periodo_academico,
                incluir_congelados=True,
            )

            materias_iniciales = list(
                Materia.objects.filter(
                    id_pnf=estudiante.pnf,
                    id_trayecto=trayecto_inicial,
                    activa=True,
                )
            )

            quedan_arrastres_reprobados = any(
                promedio_reprobado(
                    promedios_iniciales_actuales[materia.id_materia]
                )
                for materia in materias_iniciales
                if materia.id_materia in promedios_iniciales_actuales
            )

            if quedan_arrastres_reprobados:
                no_actualizados += 1
                continue

            # Evaluar el Trayecto I incluyendo los promedios congelados.
            resultado_trayecto_i = evaluar_trayecto(
                trayecto_i,
                es_inicial=False,
                incluir_congelados=True,
            )

            # Determinar si puede avanzar al Trayecto II.
            puede_pasar_trayecto_ii = (
                resultado_trayecto_i["existe"]
                and resultado_trayecto_i["aprobado"]
                and resultado_trayecto_i["materias_reprobadas"] <= MAX_REPROBADAS
                and resultado_trayecto_i["proyecto_aprobado"]
                and not resultado_trayecto_i["proyecto_reprobado"]
            )

            trayecto_ii = trayectos_por_nombre.get("trayecto ii")

            if puede_pasar_trayecto_ii and trayecto_ii is not None:
                estatus_actual.trayecto = trayecto_ii
                estatus_actual.save(update_fields=["trayecto"])

                avances_por_trayecto["Trayecto II"] = (
                    avances_por_trayecto.get("Trayecto II", 0) + 1
                )
            else:
                estatus_actual.trayecto = trayecto_i
                estatus_actual.save(update_fields=["trayecto"])

                avances_por_trayecto["Trayecto I"] = (
                    avances_por_trayecto.get("Trayecto I", 0) + 1
                )

            # Descongelar los promedios una vez resuelta la evaluación.
            PromedioFinal.objects.filter(
                estudiante=estudiante,
                trayecto=trayecto_i,
                congelada=True,
            ).update(
                congelada=False,
                fecha_congelacion=None,
            )

            actualizados += 1
            continue

        # =====================================================
        # EVALUAR TRAYECTO ACTUAL
        # =====================================================

        resultado_actual = evaluar_trayecto(
            trayecto_actual,
            es_inicial=es_tr_inicial,
            incluir_congelados=es_trayecto_i,
        )

        if not resultado_actual["existe"]:
            no_actualizados += 1
            continue

        materias_reprobadas = resultado_actual[
            "materias_reprobadas"
        ]

        proyecto_aprobado = resultado_actual[
            "proyecto_aprobado"
        ]

        proyecto_reprobado = resultado_actual[
            "proyecto_reprobado"
        ]

        # =====================================================
        # DETERMINAR SI PUEDE AVANZAR
        # =====================================================

        puede_avanzar = resultado_actual["aprobado"]

        if materias_reprobadas > MAX_REPROBADAS:
            puede_avanzar = False

        if not es_tr_inicial:

            if proyecto_reprobado or not proyecto_aprobado:
                puede_avanzar = False

        if not puede_avanzar:
            no_actualizados += 1
            continue

        # =====================================================
        # DETERMINAR SIGUIENTE TRAYECTO
        # =====================================================

        siguiente_posicion = posicion_actual + 1

        if siguiente_posicion >= len(trayectos):

            estatus_actual.estado = "Egreso"

            estatus_actual.save(
                update_fields=["estado"]
            )

            egresados += 1
            actualizados += 1
            continue

        siguiente_trayecto = trayectos[siguiente_posicion]

        if es_tr_inicial:
            siguiente_trayecto = trayecto_i

        # =====================================================
        # ACTUALIZAR TRAYECTO
        # =====================================================

        if (
            estatus_actual.trayecto_id
            != siguiente_trayecto.id_periodo_academico
        ):

            estatus_actual.trayecto = siguiente_trayecto

            estatus_actual.save(
                update_fields=["trayecto"]
            )

            nombre_siguiente = siguiente_trayecto.nombre

            avances_por_trayecto[nombre_siguiente] = (
                avances_por_trayecto.get(nombre_siguiente, 0) + 1
            )

            actualizados += 1

        else:
            no_actualizados += 1

    # =========================================================
    # DESCRIPCIÓN DE AVANCES
    # =========================================================

    detalles_avances = [
        f"{nombre}: {cantidad}"
        for nombre, cantidad in avances_por_trayecto.items()
    ]

    descripcion_avances = (
        " | ".join(detalles_avances)
        if detalles_avances
        else "No hubo estudiantes que avanzaran de trayecto."
    )

    return JsonResponse({
        "success": True,
        "ano": ANO_ACTUAL,
        "actualizados": actualizados,
        "no_actualizados": no_actualizados,
        "egresados": egresados,
        "avances": avances_por_trayecto,
        "title": "Actualización completada",
        "descripcion": (
            f"Año procesado: {ANO_ACTUAL}. "
            f"Actualizados: {actualizados}. "
            f"No actualizados: {no_actualizados}. "
            f"Egresados: {egresados}. "
            f"Avances: {descripcion_avances}"
        ),
        "icon": "success",
    })