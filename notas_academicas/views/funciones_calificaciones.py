from django.http import JsonResponse
from django.db import transaction
from decimal import Decimal, ROUND_HALF_UP
from django.utils import timezone

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

    # AGRUPAR CALIFICACIONES
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

        # Ignorar Reparación
        if nombre_trayecto == "Reparación":
            continue

        # Validar tipo de periodo del PNF
        if tipo_periodo not in {"Trimestre", "Semestre"}:
            continue
   
        # TRAYECTO INICIAL
        # Solo puede utilizar:
        # Trimestre -> Inicial Trimestre
        # Semestre  -> Inicial Semestre
        if nombre_trayecto == "Trayecto Inicial":

            periodo_inicial_esperado = (
                "Inicial Trimestre"
                if tipo_periodo == "Trimestre"
                else "Inicial Semestre"
            )

            if periodo_nombre != periodo_inicial_esperado:
                continue

        # TRAYECTOS REGULARES
        else:
            limite = 4 if tipo_periodo == "Trimestre" else 5

            trayectos_validos = {
                nombre
                for nombre, posicion in ORDEN_TRAYECTOS.items()
                if posicion <= limite
            }

            if nombre_trayecto not in trayectos_validos:
                continue

            # Los trayectos regulares NO deben tomar periodos
            # Iniciales.
            if periodo_nombre in PERIODOS_INICIALES:
                continue

        # Año académico
        fecha_eval = c.fecha_promedio
        anio = fecha_eval.year

        # CLAVE DEL GRUPO
        if nombre_trayecto == "Trayecto Inicial":
            # Cada registro de inicial se procesa individualmente.
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

    # PROCESAR CADA GRUPO
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

        # DETERMINAR SI ES PROYECTO
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

        # CASO 1: TRAYECTO INICIAL
        if nombre_trayecto == "Trayecto Inicial":
            periodo_inicial_esperado = (
                "Inicial Trimestre"
                if tipo_periodo == "Trimestre"
                else "Inicial Semestre"
            )

            # Seguridad adicional: verificar nuevamente que el registro realmente sea del periodo inicial.
            calificaciones_iniciales = [
                c
                for c in calificaciones_materia
                if (
                    c.periodo_materia
                    and c.periodo_materia.periodo
                    and (c.periodo_materia.periodo.nombre or "").strip()
                    == periodo_inicial_esperado
                )
            ]

            if not calificaciones_iniciales:
                continue

            # Como el agrupamiento utiliza id_calificaciones, normalmente habrá un solo registro.
            calificacion_inicial = calificaciones_iniciales[0]

            calificaciones_validas = [calificacion_inicial]

            promedio_final = calificacion_inicial.promedio_tramo

        # CASO 2: TRAYECTOS REGULARES / ELECTIVAS
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
                    and (pm.periodo.nombre or "").strip()
                    in periodos_objetivo
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
                    and (c.periodo_materia.periodo.nombre or "").strip()
                    in periodos_configurados
                )
            ]

            periodos_registrados = {
                (c.periodo_materia.periodo.nombre or "").strip()
                for c in calificaciones_filtradas
                if c.periodo_materia and c.periodo_materia.periodo
            }

            # Deben estar todos los periodos configurados.
            if not periodos_configurados.issubset(periodos_registrados):
                continue

            calificaciones_validas = calificaciones_filtradas

            if len(periodos_configurados) == 1:
                promedio_final = calificaciones_validas[0].promedio_tramo

            else:
                promedio_final = (
                    sum(
                        c.promedio_tramo
                        for c in calificaciones_validas
                    )
                    / Decimal(len(calificaciones_validas))
                )

        # NOTA FINAL
        promedio_final = promedio_final.quantize(
            Decimal("1"),
            rounding=ROUND_HALF_UP
        )

        # ASISTENCIA
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

        nota_minima = (
            NOTA_MINIMA_PROYECTO
            if es_proyecto
            else NOTA_MINIMA
        )

        aprobado_nota = promedio_final >= nota_minima
        aprobado_asistencia = asistencia >= ASISTENCIA_MINIMA

        if aprobado_nota and aprobado_asistencia:
            estado = "APROBADO"

            motivo = (
                f"Materia aprobada. Año académico: {anio}. "
                f"Promedio final: {promedio_final}. "
                f"Nota mínima: {nota_minima}. "
                f"Asistencia: {asistencia}%."
            )

        else:
            estado = "REPROBADO"
            motivos = []

            if not aprobado_nota:
                motivos.append(
                    f"promedio {promedio_final} menor a "
                    f"{nota_minima} pts"
                )

            if not aprobado_asistencia:
                motivos.append(
                    f"asistencia {asistencia}% menor al "
                    f"{ASISTENCIA_MINIMA}% requerido"
                )

            motivo = (
                f"Materia reprobada en el año {anio} "
                f"debido a: "
                + " y ".join(motivos)
                + "."
            )

        existe_promedio = PromedioFinal.objects.filter(
            estudiante=estudiante,
            materia_asignacion=materia_asignada,
            trayecto=trayecto,
            fecha_promedio__year=anio
        ).exists()

        if existe_promedio:
            continue

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

    return JsonResponse({
        "estado": "exito",
        "title": "Éxito",
        "icon": "success",
        "descripcion": (
            f"Se registraron {cantidad_guardada} "
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

    trayectos = list(
        TrayectoAcademico.objects.order_by("id_periodo_academico")
    )

    estudiantes = (
        Estudiante.objects
        .select_related("pnf", "nucleo")
        .prefetch_related(
            "estatus",
            "promedios_finales__materia_asignacion__materia"
        )
    )

    actualizados = 0
    no_actualizados = 0
    avances_por_trayecto = {}
    egresados = 0

    trayecto_inicial = None
    for trayecto in trayectos:
        nombre = (trayecto.nombre or "").strip().lower()
        if "inicial" in nombre:
            trayecto_inicial = trayecto
            break

    def es_materia_proyecto(materia, es_inicial=False):
        if es_inicial:
            return False

        nombre = (materia.nombre or "").strip().lower()
        nombre = nombre.replace("-", " ").replace("–", " ").replace("—", " ")

        if "proyecto nacional" in nombre:
            return False

        patrones_validos = [
            "proyecto socio tecnologico",
            "proyecto socio tecnológico",
            "proyecto socio integrador",
            "proyecto sociointegrador"
        ]

        return any(patron in nombre for patron in patrones_validos)

    for estudiante in estudiantes:
        estatus_actual = (
            estudiante.estatus
            .select_related("trayecto")
            .order_by("-fecha_ingreso", "-id_estatus_estudiante")
            .first()
        )

        if not estatus_actual or not estatus_actual.trayecto:
            no_actualizados += 1
            continue

        trayecto_actual = estatus_actual.trayecto
        periodo_pnf = (estudiante.pnf.periodo_academico or "").strip()

        if periodo_pnf not in {"Trimestre", "Semestre"}:
            no_actualizados += 1
            continue

        posicion_actual = next(
            (pos for pos, t in enumerate(trayectos) if t.id_periodo_academico == trayecto_actual.id_periodo_academico),
            None
        )

        if posicion_actual is None:
            no_actualizados += 1
            continue

        todos_los_promedios = list(
            estudiante.promedios_finales
            .select_related("materia_asignacion__materia", "trayecto")
            .order_by("fecha_promedio", "id_promedio_final")
        )

        if not todos_los_promedios:
            no_actualizados += 1
            continue

        def obtener_ultimos_promedios(trayecto_id):
            registros = {}
            for promedio in todos_los_promedios:
                if promedio.trayecto_id != trayecto_id:
                    continue
                
                materia_id = promedio.materia_asignacion.materia.id_materia
                anterior = registros.get(materia_id)

                if anterior is None or promedio.fecha_promedio >= anterior.fecha_promedio:
                    registros[materia_id] = promedio
            return registros


        def evaluar_trayecto(trayecto, es_inicial=False):
            materias = list(
                Materia.objects.filter(
                    id_pnf=estudiante.pnf,
                    id_trayecto=trayecto,
                    activa=True
                )
            )

            if not materias:
                return {"existe": False, "aprobado": False}

            promedios = obtener_ultimos_promedios(trayecto.id_periodo_academico)

            materias_aprobadas = 0
            materias_reprobadas = 0
            proyecto_aprobado = False
            proyecto_reprobado = False

            for materia in materias:
                promedio = promedios.get(materia.id_materia)
                es_proyecto = es_materia_proyecto(materia, es_inicial=es_inicial)

                # 1. SI LA MATERIA NO SE HA CURSADO / NO TIENE NOTA:
                if promedio is None:
                    if es_proyecto:
                        proyecto_reprobado = True
                    # CORRECCIÓN: En Trayecto Inicial NO se cuenta como reprobada si no la ha cursado
                    elif not es_inicial:
                        materias_reprobadas += 1
                    continue

                nota_requerida = NOTA_MINIMA_PROYECTO if es_proyecto else NOTA_MINIMA_GENERAL

                # 2. SI LA MATERIA FUE CURSADA:
                # Se exige nota >= nota_requerida Y asistencia >= 75%
                nota_aprobada = (
                    promedio.promedio_final is not None 
                    and promedio.promedio_final >= nota_requerida
                )
                asistencia_aprobada = (
                    promedio.asistencia is not None 
                    and promedio.asistencia >= ASISTENCIA_MINIMA
                )

                materia_aprobada = nota_aprobada and asistencia_aprobada

                if materia_aprobada:
                    materias_aprobadas += 1
                    if es_proyecto:
                        proyecto_aprobado = True
                else:
                    # Cursó la materia pero reprobó por nota o asistencia
                    if es_proyecto:
                        proyecto_reprobado = True
                    else:
                        materias_reprobadas += 1

            # 3. CRITERIOS DE APROBACIÓN DEL TRAYECTO
            if es_inicial:
                # TRAYECTO INICIAL:
                # - No requiere proyecto.
                # - Aprueba si aprueba al menos 1 materia Y no tiene más de 1 reprobada.
                aprobado = (materias_aprobadas >= 1) and (materias_reprobadas <= 1)
            else:
                # TRAYECTOS REGULARES (I al IV):
                # - Requiere Proyecto Aprobado y máximo 3 materias reprobadas.
                aprobado = (not proyecto_reprobado) and (materias_reprobadas <= MAX_REPROBADAS)

            return {
                "existe": True,
                "aprobado": aprobado,
                "total_materias": len(materias),
                "materias_aprobadas": materias_aprobadas,
                "materias_reprobadas": materias_reprobadas,
                "proyecto_aprobado": proyecto_aprobado,
                "proyecto_reprobado": proyecto_reprobado
            }
        # Evaluamos trayecto actual
        es_tr_inicial = (
            trayecto_inicial 
            and trayecto_actual.id_periodo_academico == trayecto_inicial.id_periodo_academico
        )
        resultado_actual = evaluar_trayecto(trayecto_actual, es_inicial=es_tr_inicial)

        if not resultado_actual["existe"]:
            no_actualizados += 1
            continue

        puede_avanzar = False

        if es_tr_inicial:
            puede_avanzar = resultado_actual["aprobado"]

        elif posicion_actual >= 1:
            inicial_aprobado = True
            if trayecto_inicial:
                res_inicial = evaluar_trayecto(trayecto_inicial, es_inicial=True)
                inicial_aprobado = res_inicial["aprobado"]

            puede_avanzar = inicial_aprobado and resultado_actual["aprobado"]

        if not puede_avanzar:
            no_actualizados += 1
            continue

        # Promoción de Trayecto o Egreso
        es_ultimo_trayecto = (posicion_actual == len(trayectos) - 1)

        if es_ultimo_trayecto:
            if estatus_actual.estado != "Egreso":
                estatus_actual.estado = "Egreso"
                estatus_actual.save(update_fields=["estado"])
                egresados += 1
                actualizados += 1
            else:
                no_actualizados += 1
            continue

        siguiente_trayecto = trayectos[posicion_actual + 1]

        if estatus_actual.trayecto_id != siguiente_trayecto.id_periodo_academico:
            estatus_actual.trayecto = siguiente_trayecto
            estatus_actual.save(update_fields=["trayecto"])

            nombre_siguiente = siguiente_trayecto.nombre
            avances_por_trayecto[nombre_siguiente] = avances_por_trayecto.get(nombre_siguiente, 0) + 1
            actualizados += 1
        else:
            no_actualizados += 1

    detalles_avances = [f"{nombre}: {cantidad}" for nombre, cantidad in avances_por_trayecto.items()]
    descripcion_avances = " | ".join(detalles_avances) if detalles_avances else "No hubo estudiantes que avanzaran de trayecto."

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
        "icon": "success"
    })
