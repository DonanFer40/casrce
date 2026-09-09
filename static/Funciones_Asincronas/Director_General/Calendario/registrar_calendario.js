document.addEventListener("DOMContentLoaded", () => {

    const formulario_registrar = document.getElementById("formulario_registrar");

    const select_periodo = document.getElementById("periodo");
    const select_tipo = document.getElementById("tipo");
    const input_fecha_inicio = document.getElementById("fecha_inicio");
    const input_fecha_final = document.getElementById("fecha_final");
    const contenedor_periodo = document.getElementById("contenedor_periodo");

    const meses_periodos = {
        "Inicial Trimestre": [9, 11],
        "Inicial Semestre": [9, 11],
        "Reparación": [11, 12],

        "Tramo I": [1, 4],
        "Tramo II": [4, 7],
        "Tramo III": [9, 11],

        "Semestre I": [1, 5],
        "Semestre II": [9, 11]
    };

    const meses_carga_notas = {
        "Inicial Trimestre": 11,
        "Inicial Semestre": 11,
        "Reparación": 12,

        "Tramo I": 4,
        "Tramo II": 7,
        "Tramo III": 11,

        "Semestre I": 5,
        "Semestre II": 11
    };

    const meses_inscripcion = {
        "INSCRIPCION_TRIMESTRE": 9,
        "INSCRIPCION_SEMESTRE": 9
    };

    async function cargarTiposCalendario() {
        try {
            const respuesta = await fetch("/opc_reg_cal/");
            const data = await respuesta.json();
            console.log(data);

            select_tipo.innerHTML = `<option value="">Seleccione el tipo</option>`;
            data.tipos.forEach(tipo => {
                const opcion = document.createElement("option");
                opcion.value = tipo.valor;
                opcion.textContent = tipo.nombre;
                select_tipo.appendChild(opcion);
            });
        } catch (error) {
            console.error(error);
        }
    }
    cargarTiposCalendario();

    function configurarMesInscripcion(tipo) {
        const mes = meses_inscripcion[tipo];
        if (!mes) {
            return;
        }

        const año_actual = new Date().getFullYear();
        const mes_formateado = String(mes).padStart(2, "0");

        // Primer día del mes
        const fecha_minima = `${año_actual}-${mes_formateado}-01`;

        // Último día del mes
        const ultimo_dia = new Date(año_actual, mes, 0).getDate();

        const fecha_maxima = `${año_actual}-${mes_formateado}-${String(ultimo_dia).padStart(2, "0")}`;

        input_fecha_inicio.min = fecha_minima;
        input_fecha_inicio.max = fecha_maxima;

        input_fecha_final.min = fecha_minima;
        input_fecha_final.max = fecha_maxima;

        // La fecha final será automática
        input_fecha_final.readOnly = true;

        input_fecha_inicio.value = "";
        input_fecha_final.value = "";
    }

    function configurarAñoActual() {

        const año_actual = new Date().getFullYear();

        // Primer día del año actual
        const fecha_minima = `${año_actual}-01-01`;

        // Último día del año actual
        const fecha_maxima = `${año_actual}-12-31`;

        input_fecha_inicio.min = fecha_minima;
        input_fecha_inicio.max = fecha_maxima;

        input_fecha_final.min = fecha_minima;
        input_fecha_final.max = fecha_maxima;

        // Limpiar fechas anteriores
        input_fecha_inicio.value = "";
        input_fecha_final.value = "";

        // Ambas fechas pueden seleccionarse manualmente
        input_fecha_inicio.readOnly = false;
        input_fecha_final.readOnly = false;
    }

    select_tipo.addEventListener("change", async () => {
        const tipo_periodo = select_tipo.value;

        try {
            // INSCRIPCIONES
            if (tipo_periodo == "INSCRIPCION_TRIMESTRE" ||
                tipo_periodo == "INSCRIPCION_SEMESTRE") {

                contenedor_periodo.style.display = "none";
                input_fecha_final.readOnly = false;
                configurarMesInscripcion(tipo_periodo);
                return;
            }

            // PERIODO Y CARGA DE NOTAS
            const formulario = new FormData();
            formulario.append("tipo_periodo", tipo_periodo);

            const respuesta = await fetch("/periodos_lista/", {
                method: "POST",
                headers: {
                    "X-CSRFToken":
                        document.querySelector(
                            "[name=csrfmiddlewaretoken]"
                        ).value
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            if (tipo_periodo == "PERIODO") {
                contenedor_periodo.style.display = "block";

                select_periodo.innerHTML = '<option value="">Seleccione el período</option>';

                resultado.periodos.forEach(periodo => {
                    const option = document.createElement("option");
                    option.textContent = periodo.nombre;
                    option.value = periodo.id_periodo_academico;
                    select_periodo.append(option);
                });

                input_fecha_final.readOnly = false;

            } else if (tipo_periodo == "CARGA_NOTAS") {
                contenedor_periodo.style.display = "block";

                select_periodo.innerHTML = '<option value="">Seleccione el período</option>';

                resultado.periodos.forEach(periodo => {
                    const option = document.createElement("option");
                    option.textContent = periodo.nombre;
                    option.value = periodo.id_periodo_academico;
                    select_periodo.append(option);
                });

                input_fecha_final.readOnly = true;
            } else {
                contenedor_periodo.style.display = "none";

                // GRADO ACADÉMICO Y ACTIVIDADES
                if (tipo_periodo == "GRADO_ACADEMICO" || tipo_periodo == "ACTIVIDADES") {
                    configurarAñoActual();
                }
            }
        } catch (error) {
            console.error(error);
        }
    });

    select_periodo.addEventListener("change", () => {

        const periodo = select_periodo.options[
            select_periodo.selectedIndex
        ].textContent;

        const año_actual = new Date().getFullYear();

        // ==========================================================
        // CARGA DE NOTAS
        // ==========================================================

        if (select_tipo.value == "CARGA_NOTAS") {

            const mes = meses_carga_notas[periodo];

            if (!mes) {
                return;
            }

            const mes_formateado = String(mes).padStart(2, "0");

            const fecha_minima =
                `${año_actual}-${mes_formateado}-01`;

            const ultimo_dia =
                new Date(año_actual, mes, 0).getDate();

            const fecha_maxima =
                `${año_actual}-${mes_formateado}-${String(
                    ultimo_dia
                ).padStart(2, "0")}`;

            input_fecha_inicio.min = fecha_minima;
            input_fecha_inicio.max = fecha_maxima;

            input_fecha_final.min = fecha_minima;
            input_fecha_final.max = fecha_maxima;

            input_fecha_inicio.value = "";
            input_fecha_final.value = "";

            return;
        }

        // ==========================================================
        // PERIODO ACADÉMICO
        // ==========================================================

        if (select_tipo.value == "PERIODO") {

            const rango = meses_periodos[periodo];

            if (!rango) {
                return;
            }

            const mes_inicio = rango[0];
            const mes_final = rango[1];

            // ======================================================
            // FECHA INICIAL
            // ======================================================

            const mes_inicio_formateado =
                String(mes_inicio).padStart(2, "0");

            const fecha_minima_inicio =
                `${año_actual}-${mes_inicio_formateado}-01`;

            const ultimo_dia_inicio =
                new Date(
                    año_actual,
                    mes_inicio,
                    0
                ).getDate();

            const fecha_maxima_inicio =
                `${año_actual}-${mes_inicio_formateado}-${String(
                    ultimo_dia_inicio
                ).padStart(2, "0")}`;

            // ======================================================
            // FECHA FINAL
            // SOLO EL ÚLTIMO MES
            // ======================================================

            const mes_final_formateado =
                String(mes_final).padStart(2, "0");

            const fecha_minima_final =
                `${año_actual}-${mes_final_formateado}-01`;

            const ultimo_dia_final =
                new Date(
                    año_actual,
                    mes_final,
                    0
                ).getDate();

            const fecha_maxima_final =
                `${año_actual}-${mes_final_formateado}-${String(
                    ultimo_dia_final
                ).padStart(2, "0")}`;

            // ======================================================
            // APLICAR
            // ======================================================

            input_fecha_inicio.min = fecha_minima_inicio;
            input_fecha_inicio.max = fecha_maxima_inicio;

            input_fecha_final.min = fecha_minima_final;
            input_fecha_final.max = fecha_maxima_final;

            // Limpiar fechas anteriores
            input_fecha_inicio.value = "";
            input_fecha_final.value = "";

            return;
        }
    });

    input_fecha_inicio.addEventListener("change", () => {

        const fecha_inicio = input_fecha_inicio.value;

        if (!fecha_inicio) {
            input_fecha_final.value = "";
            return;
        }

        // ==========================================================
        // INSCRIPCIÓN
        // ==========================================================

        if (
            select_tipo.value == "INSCRIPCION_TRIMESTRE" ||
            select_tipo.value == "INSCRIPCION_SEMESTRE"
        ) {

            const fecha = new Date(
                fecha_inicio + "T00:00:00"
            );

            fecha.setDate(fecha.getDate() + 5);

            const año = fecha.getFullYear();

            const mes = String(
                fecha.getMonth() + 1
            ).padStart(2, "0");

            const dia = String(
                fecha.getDate()
            ).padStart(2, "0");

            input_fecha_final.value =
                `${año}-${mes}-${dia}`;

            return;
        }

        // ==========================================================
        // CARGA DE NOTAS
        // ==========================================================

        if (select_tipo.value == "CARGA_NOTAS") {

            const fecha = new Date(
                fecha_inicio + "T00:00:00"
            );

            input_fecha_final.min = fecha_inicio;

            fecha.setDate(fecha.getDate() + 3);

            const año = fecha.getFullYear();

            const mes = String(
                fecha.getMonth() + 1
            ).padStart(2, "0");

            const dia = String(
                fecha.getDate()
            ).padStart(2, "0");

            input_fecha_final.max =
                `${año}-${mes}-${dia}`;

            input_fecha_final.value =
                `${año}-${mes}-${dia}`;

            return;
        }
    });


    formulario_registrar.addEventListener("submit", async (e) => {
        e.preventDefault()
        try {
            const formulario = new FormData(formulario_registrar);

            const respuesta = await fetch("/reg_calendario/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            await Swal.fire({
                text: resultado.descripcion,
                icon: resultado.icon,
                title: resultado.title,
                allowOutsideClick: false,
                allowEscapeKey: false
            });

            if (resultado.estado == "exito") {
                formulario_registrar.reset();
                await cargarTiposCalendario();
                contenedor_periodo.style.display = "none";
            }
        } catch (error) {
            console.error(error)
        }
    });

});