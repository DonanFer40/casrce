document.addEventListener("DOMContentLoaded", () => {

    const select_periodos_academicos = document.getElementById("periodos_academicos");
    const contenedor = document.getElementById("contenedor_visualizar_calendario");

    const input_id_calendario = document.getElementById("id_calendario");
    const dialogo_fecha_academica = document.getElementById("dialogo_fecha_academica");
    const btn_cerrar_dialogo = document.getElementById("cerrar_dialogo");
    const formulario_actualizar = document.getElementById("formulario_actualizar");
    const input_fecha_inicio = document.getElementById("fecha_inicio");
    const input_fecha_finalizado = document.getElementById("fecha_finalizado");
    const input_descripcion = document.getElementById("descripcion_calendario");
    const error_fechas = document.getElementById("error_fechas_calendario");
    const input_tipo_calendario = document.getElementById("tipo_calendario");
    let periodo = "";
    let limites_fechas = null;

    function mostrarErrorFechas(mensaje) {
        error_fechas.textContent = mensaje;
        error_fechas.hidden = false;
    }

    function limpiarErrorFechas() {
        error_fechas.textContent = "";
        error_fechas.hidden = true;
    }

    async function periodos_academicos_registrados() {
        try {
            const respuesta = await fetch("/per_acad_reg/");
            const resultado = await respuesta.json();
            console.log(resultado);

            select_periodos_academicos.innerHTML = "<option value='' selected>Seleccione el periodo</option>";

            resultado.tipos.forEach(tipo => {
                const option = document.createElement("option");
                option.value = tipo;
                option.textContent = tipo;
                select_periodos_academicos.appendChild(option);
            });
        } catch (error) {
            console.error(error);
        }
    }
    periodos_academicos_registrados();

    select_periodos_academicos.addEventListener("change", async () => {
        periodo = select_periodos_academicos.value;

        await calendario_registrado();
    });

    async function calendario_registrado() {
        try {
            const formulario = new FormData();
            formulario.append("periodo", periodo);

            const respuesta = await fetch("/calendarios_lista/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            contenedor.innerHTML = "";
            const tipos = [
                { valor: "PERIODO", nombre: "Período Académico" },
                { valor: "CARGA_NOTAS", nombre: "Carga de Notas" },
                { valor: "NO_LABORABLE", nombre: "Días No Laborables" },
                { valor: "VACACIONES", nombre: "Vacaciones" },
                { valor: "GRADO_ACADEMICO", nombre: "Grado Académico" },
                { valor: "INSCRIPCION_TRIMESTRE", nombre: "Inscripción Trimestre" },
                { valor: "INSCRIPCION_SEMESTRE", nombre: "Inscripción Semestre" }
            ];

            tipos.forEach(tipo => {
                const calendarios = resultado.calendarios.filter(
                    calendario => calendario.tipo_valor === tipo.valor
                );

                if (calendarios.length === 0) {
                    return;
                }

                const contenedor_tipo = document.createElement("div");
                contenedor_tipo.classList.add("contenedor_tipo_calendario");

                const titulo = document.createElement("h3");
                titulo.textContent = tipo.nombre;

                const tabla = document.createElement("table");
                tabla.classList.add("tabla_calendario");

                tabla.innerHTML = `
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>DESCRIPCIÓN</th>
                            <th>FECHA INICIO</th>
                            <th>FECHA FINALIZADA</th>
                            <th>ACCIÓN</th>
                        </tr>
                    </thead>
                    <tbody></tbody>
                `;
                const tbody = tabla.querySelector("tbody");

                /*Insertar registros*/
                calendarios.forEach((calendario, index) => {
                    const fila = document.createElement("tr");
                    fila.dataset.id = calendario.id;
                    fila.dataset.tipo = calendario.tipo_valor;
                    const id_visible = tipo.valor === "CARGA_NOTAS"
                        ? index + 1
                        : calendario.id;

                    fila.innerHTML = `
                        <td>${id_visible}</td>
                        <td>${calendario.descripcion}</td>
                        <td>${calendario.fecha_inicio}</td>
                        <td>${calendario.fecha_final}</td>
                        <td>
                            <button
                                type="button"
                                class="btn_abrir_edicion_calendario"
                                data-id="${calendario.id}">
                                Actualizar
                            </button>
                        </td>
                    `;

                    tbody.appendChild(fila);
                });

                /*Agregar título y tabla*/
                contenedor_tipo.appendChild(titulo);
                contenedor_tipo.appendChild(tabla);

                /*Agregar al contenedor principa*/
                contenedor.appendChild(contenedor_tipo);
            });
        } catch (error) {
            console.error(error);
        }
    }
    calendario_registrado();

    contenedor.addEventListener("click", async (e) => {
        const boton = e.target.closest(".btn_abrir_edicion_calendario");
        if (!boton) {
            return;
        }

        try {
            const formulario = new FormData();
            formulario.append("id_calendario", boton.dataset.id);

            const respuesta = await fetch("/calendario_datos/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector(
                        "[name=csrfmiddlewaretoken]"
                    ).value
                },
                body: formulario
            }
            );
            const resultado = await respuesta.json();
            console.log(resultado);

            if (resultado.estado !== "exito") {
                if (!dialogo_fecha_academica.open) {
                    dialogo_fecha_academica.showModal();
                }
                limpiarErrorFechas();
                mostrarErrorFechas(resultado.descripcion);
                return;
            }

            dialogo_fecha_academica.showModal();
            limpiarErrorFechas();

            input_id_calendario.value = resultado.calendario.id;

            input_descripcion.value = resultado.calendario.descripcion;

            input_fecha_inicio.value = resultado.calendario.fecha_inicio;

            input_fecha_finalizado.value = resultado.calendario.fecha_final;

            input_tipo_calendario.value = resultado.calendario.tipo;

            // -------------------------------------------------
            // CONFIGURAR FECHA DE FINALIZACIÓN
            // -------------------------------------------------

            const esCargaNotas =
                resultado.calendario.tipo === "CARGA_NOTAS";

            input_fecha_finalizado.readOnly = esCargaNotas;

            input_fecha_finalizado.classList.toggle(
                "fecha_solo_lectura",
                esCargaNotas
            );

            limites_fechas = resultado.calendario.limites;

            input_fecha_inicio.min = limites_fechas.fecha_inicio_min;
            input_fecha_inicio.max = limites_fechas.fecha_inicio_max;

            input_fecha_finalizado.min = limites_fechas.fecha_final_min;
            input_fecha_finalizado.max = limites_fechas.fecha_final_max;

            ajustarMinimoFechaFinal();
        } catch (error) {
            console.error(error);
            if (!dialogo_fecha_academica.open) {
                dialogo_fecha_academica.showModal();
            }
            mostrarErrorFechas(
                "No fue posible cargar el calendario. Inténtalo nuevamente."
            );
        }
    });

    function ajustarMinimoFechaFinal() {
        if (!limites_fechas) {
            return;
        }

        input_fecha_finalizado.min = input_fecha_inicio.value > limites_fechas.fecha_final_min
            ? input_fecha_inicio.value
            : limites_fechas.fecha_final_min;
    }

    input_fecha_inicio.addEventListener("change", () => {
        limpiarErrorFechas();
        ajustarMinimoFechaFinal();
    });

    input_fecha_finalizado.addEventListener("change", limpiarErrorFechas);
    input_descripcion.addEventListener("input", limpiarErrorFechas);

    btn_cerrar_dialogo.addEventListener("click", () => {
        dialogo_fecha_academica.close();
    });

    formulario_actualizar.addEventListener("submit", async (e) => {

        e.preventDefault();

        try {

            limpiarErrorFechas();

            const descripcion = input_descripcion.value.trim();

            // -------------------------------------------------
            // VALIDAR DESCRIPCIÓN
            // -------------------------------------------------

            if (!descripcion) {

                mostrarErrorFechas(
                    "La descripción es obligatoria."
                );

                input_descripcion.focus();

                return;
            }

            if (descripcion.length > 150) {

                mostrarErrorFechas(
                    "La descripción no puede superar los 150 caracteres."
                );

                input_descripcion.focus();

                return;
            }

            // -------------------------------------------------
            // VALIDAR FECHAS
            // -------------------------------------------------

            if (
                !input_fecha_inicio.value ||
                !input_fecha_finalizado.value
            ) {

                mostrarErrorFechas(
                    "Debes indicar la fecha de inicio y la fecha de finalización."
                );

                return;
            }

            if (
                input_fecha_inicio.value < input_fecha_inicio.min ||
                input_fecha_inicio.value > input_fecha_inicio.max ||
                input_fecha_finalizado.value < input_fecha_finalizado.min ||
                input_fecha_finalizado.value > input_fecha_finalizado.max
            ) {

                mostrarErrorFechas(
                    "Las fechas deben respetar los límites permitidos para este calendario."
                );

                return;
            }

            if (
                input_fecha_finalizado.value <
                input_fecha_inicio.value
            ) {

                mostrarErrorFechas(
                    "La fecha de finalización no puede ser anterior a la fecha de inicio."
                );

                return;
            }

            // -------------------------------------------------
            // PREPARAR FORMULARIO
            // -------------------------------------------------

            const formulario = new FormData(
                formulario_actualizar
            );

            formulario.set(
                "descripcion",
                descripcion
            );

            // -------------------------------------------------
            // ENVIAR ACTUALIZACIÓN
            // -------------------------------------------------

            const respuesta = await fetch("/calendario_guardar/", {

                method: "POST",

                headers: {
                    "X-CSRFToken": document.querySelector(
                        "[name=csrfmiddlewaretoken]"
                    ).value
                },

                body: formulario

            });

            const resultado = await respuesta.json();

            console.log(resultado);

            // -------------------------------------------------
            // VALIDAR RESPUESTA
            // -------------------------------------------------

            if (resultado.estado !== "exito") {

                mostrarErrorFechas(
                    resultado.descripcion
                );

                return;
            }

            // -------------------------------------------------
            // CERRAR DIÁLOGO
            // -------------------------------------------------

            dialogo_fecha_academica.close();

            // -------------------------------------------------
            // NOTIFICAR ACTUALIZACIÓN
            // -------------------------------------------------

            await NotificacionesCASRCE.mostrar({

                text: resultado.descripcion,

                icon: resultado.icon,

                title: resultado.title,

                allowOutsideClick: false,

                allowEscapeKey: false

            });

            // -------------------------------------------------
            // ACTUALIZAR TABLA
            // -------------------------------------------------

            await calendario_registrado();

        } catch (error) {

            console.error(error);

            mostrarErrorFechas(
                "No fue posible actualizar el calendario. Inténtalo nuevamente."
            );

        }

    });

});