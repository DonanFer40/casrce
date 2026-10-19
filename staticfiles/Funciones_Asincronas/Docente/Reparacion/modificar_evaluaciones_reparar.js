document.addEventListener("DOMContentLoaded", () => {

    const formulario_actualizar = document.getElementById("formulario_actualizar");

    const select_nucleo_asignado = document.getElementById("nucleo_asignado");
    const select_pnf_asignado = document.getElementById("pnf_asignado");

    const contenedor_seleccion_docente = document.getElementById("contenedor_seleccion_docente");
    const select_seleccion_docente = document.getElementById("seleccion_docente");

    const select_perfiles_asignados = document.getElementById("perfiles_asignados");
    const input_perfil_asignado = document.getElementById("perfil_asignado");

    const select_materia_asignada = document.getElementById("materia_asignada");
    const input_trayecto_academico = document.getElementById("trayecto_academico");

    const contenedor_evaluaciones = document.getElementById("contenedor_evaluaciones");
    const btn_agregar_detalle = document.getElementById("btn_agregar_detalle");

    let pnf = "", nucleo = "", materia = "", docente = "";
    let perfil_seleccionado = "";

    function obtener_csrf_token() {
        const cookie = document.cookie
            .split("; ")
            .find(row => row.startsWith("csrftoken="));

        return cookie
            ? decodeURIComponent(cookie.split("=")[1])
            : "";
    }

    async function perfiles_asignados() {
        try {
            const respuesta = await fetch("/notas_academicas/perf_asig/");
            const resultado = await respuesta.json();
            console.log(resultado);

            const tiene_docente = resultado.docente;
            const tiene_control = resultado.control_estudio;

            input_perfil_asignado.value = "";

            select_perfiles_asignados.innerHTML = "<option value='' selected>Selecciona un perfil</option>";

            // Tiene ambos perfiles
            if (tiene_docente && tiene_control) {
                const option_docente = document.createElement("option");
                option_docente.value = "DOCENTE";
                option_docente.textContent = "Docente";

                const option_control = document.createElement("option");
                option_control.value = "CONTROL_ESTUDIO";
                option_control.textContent = "Encargado de Control de Estudio";

                select_perfiles_asignados.append(option_docente, option_control);

                select_perfiles_asignados.style.display = "";
                input_perfil_asignado.style.display = "none";

                perfil_seleccionado = ""; // Todavía no hay perfil seleccionado

                limpiar_nucleos(); // No cargar núcleos todavía
            }

            // Solamente Docente
            else if (tiene_docente) {
                perfil_seleccionado = "DOCENTE";

                input_perfil_asignado.value = "Docente";

                input_perfil_asignado.style.display = "";
                select_perfiles_asignados.style.display = "none";

                await nucleos_asignados(perfil_seleccionado);
            }

            // Solamente Control de Estudio
            else if (tiene_control) {
                perfil_seleccionado = "CONTROL_ESTUDIO";

                input_perfil_asignado.value = "Encargado de Control de Estudio";

                input_perfil_asignado.style.display = "";
                select_perfiles_asignados.style.display = "none";

                await nucleos_asignados(perfil_seleccionado);

                limpiar_nucleos();
            }

            // No tiene ningún perfil
            else {
                perfil_seleccionado = "";

                input_perfil_asignado.value = "";

                input_perfil_asignado.style.display = "";
                select_perfiles_asignados.style.display = "none";

                limpiar_nucleos();
            }
        } catch (error) {
            console.error(error);
        }
    }
    perfiles_asignados();

    select_perfiles_asignados.addEventListener("change", async () => {
        perfil_seleccionado = select_perfiles_asignados.value;

        limpiar_nucleos();

        if (perfil_seleccionado === "CONTROL_ESTUDIO") {
            contenedor_seleccion_docente.style.display = "";
        } else {
            contenedor_seleccion_docente.style.display = "none";
        }

        await nucleos_asignados(perfil_seleccionado);
    });

    async function nucleos_asignados(perfil) {
        try {
            const formulario = new FormData();
            formulario.append("perfil", perfil);

            const respuesta = await fetch("/notas_academicas/nucl_not_rep/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": obtener_csrf_token()
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            select_nucleo_asignado.innerHTML = "<option value='' selected>Selecciona un núcleo</option>";

            if (resultado.estado !== "exito") {
                await NotificacionesCASRCE.mostrar({
                    text: resultado.descripcion,
                    icon: resultado.icon,
                    title: resultado.title,
                    allowOutsideClick: false,
                    allowEscapeKey: false
                });
                return;
            }

            resultado.datos.forEach(nucleo => {
                const option_nucleo = document.createElement("option");
                option_nucleo.value = nucleo.id_nucleo;
                option_nucleo.textContent = nucleo.municipio;
                select_nucleo_asignado.append(option_nucleo);
            });
        } catch (error) {
            console.error(error);
        }
    }

    select_nucleo_asignado.addEventListener("change", async (e) => {
        nucleo = select_nucleo_asignado.value;

        await pnfs_asignados();

        await materias_registradas();

        await evaluaciones_registradas();
    });

    async function pnfs_asignados() {
        try {
            const formulario = new FormData();
            formulario.append("nucleo_asignado", nucleo);
            formulario.append("perfil", perfil_seleccionado);

            const respuesta = await fetch("/notas_academicas/pnf_not_rep/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": obtener_csrf_token()
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            select_materia_asignada.innerHTML = "<option value='' selected>Selecciona el pnf primero</option>";

            select_pnf_asignado.innerHTML = "<option value='' selected>Selecciona un P.N.F</option>";

            if (resultado.estado !== "exito") {
                await NotificacionesCASRCE.mostrar({
                    text: resultado.descripcion,
                    icon: resultado.icon,
                    title: resultado.title,
                    allowOutsideClick: false,
                    allowEscapeKey: false
                });
                return;
            }

            resultado.datos.forEach(pnf => {
                const option_pnf = document.createElement("option");
                option_pnf.value = pnf.id_pnf;
                option_pnf.textContent = pnf.pnf;
                select_pnf_asignado.append(option_pnf);
            });
        } catch (error) {
            console.error(error);
        }
    }

    select_pnf_asignado.addEventListener("change", async () => {
        pnf = select_pnf_asignado.value;

        await materias_registradas();

        if (perfil_seleccionado === "CONTROL_ESTUDIO") {
            await docente_seleccionado();
        }
    });

    async function docente_seleccionado() {
        try {
            if (!pnf || !nucleo) return;

            const formulario = new FormData();
            formulario.append("nucleo_asignado", nucleo);
            formulario.append("pnf_seleccionado", pnf);

            const respuesta = await fetch("/notas_academicas/doc_not_rep/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": obtener_csrf_token()
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            select_seleccion_docente.innerHTML = "<option value='' selected>Debe seleccionar el docente</option>";

            if (resultado.estado !== "exito") {
                await NotificacionesCASRCE.mostrar({
                    text: resultado.descripcion,
                    icon: resultado.icon,
                    title: resultado.title,
                    allowOutsideClick: false,
                    allowEscapeKey: false
                });
                return;
            }

            resultado.datos.forEach(docente => {
                const option = document.createElement("option");
                option.value = docente.cedula;
                option.textContent = docente.nombres + " " + docente.apellidos;
                select_seleccion_docente.append(option);
            });

        } catch (error) {
            console.error(error);
        }
    }

    select_seleccion_docente.addEventListener("change", async () => {
        docente = select_seleccion_docente.value;

        await materias_registradas();
    });

    async function materias_registradas() {
        try {
            if (!nucleo || !pnf) return;

            const formulario = new FormData();
            formulario.append("id_nucleo", nucleo);
            formulario.append("id_pnf", pnf);
            formulario.append("docente", docente);
            formulario.append("perfil", perfil_seleccionado);

            const respuesta = await fetch("/notas_academicas/mat_reg_eval/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": obtener_csrf_token()
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            select_materia_asignada.innerHTML = "<option value='' selected>Selecciona la materia</option>";

            resultado.materias.forEach(materia => {
                const option_materia = document.createElement("option");
                option_materia.value = materia.id_materia_asignada;
                option_materia.textContent = materia.nombre;
                option_materia.dataset.trayecto = materia.trayecto;
                option_materia.dataset.id_trayecto = materia.id_trayecto;
                select_materia_asignada.append(option_materia);
            });
        } catch (error) {
            console.error(error);
        }
    }

    select_materia_asignada.addEventListener("change", async () => {
        const opcion = select_materia_asignada.selectedOptions[0];
        materia = opcion.value;

        const trayecto = opcion.dataset.trayecto;
        input_trayecto_academico.value = trayecto;
        input_trayecto_academico.dataset.id_trayecto = opcion.dataset.id_trayecto;

        await evaluaciones_registradas();
    });

    async function evaluaciones_registradas() {
        if (!nucleo || !pnf || !materia) return;

        const formulario = new FormData();
        formulario.append("id_pnf", pnf);
        formulario.append("id_nucleo", nucleo);
        formulario.append("id_materia_asignada", materia);
        formulario.append("docente", docente);
        formulario.append("perfil", perfil_seleccionado);

        try {
            const respuesta = await fetch("/notas_academicas/eval_reg_rep/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": obtener_csrf_token()
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            if (resultado.estado !== "exito") {
                await NotificacionesCASRCE.mostrar({
                    title: resultado.title,
                    text: resultado.descripcion,
                    icon: resultado.icon
                });
                return;
            }

            contenedor_evaluaciones.innerHTML = "";

            const registro = resultado.evaluaciones[0];
            registro.detalles.forEach(detalle => {
                const div = document.createElement("div");
                div.classList.add("detalle_evaluacion");
                div.innerHTML = `
                    <input type="hidden" name="id_detalle[]" value="${detalle.id_detalle}">
                    
                    <label>Tipo de Evaluación:</label>
                    <select name="tipo_evaluacion[]" class="tipo_evaluacion"></select>

                    <label>Porcentaje:</label>
                    <input type="text" name="porcentaje[]" class="porcentaje_evaluacion" value="${detalle.porcentaje}">

                    <button type="button" class="btn_eliminar_detalle">Eliminar</button>

                `;
                contenedor_evaluaciones.appendChild(div);

                const select = div.querySelector(".tipo_evaluacion");
                poblarSelect(select);

                select.value = detalle.tipo_evaluacion;
            });

            actualizarOpcionesSelects();
            recalcularPorcentajes();
            verificarLimiteBoton();
        } catch (error) {
            console.error(error);
        }
    }

    formulario_actualizar.addEventListener("submit", async (e) => {
        e.preventDefault();
        try {
            const formulario = new FormData(formulario_actualizar);
            formulario.append("perfil", perfil_seleccionado);

            const respuesta = await fetch("/notas_academicas/mod_eval_rep/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": obtener_csrf_token()
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            await NotificacionesCASRCE.mostrar({
                text: resultado.descripcion,
                icon: resultado.icon,
                title: resultado.title,
                allowOutsideClick: false,
                allowEscapeKey: false
            });

            if (resultado.estado == "exito") {
                formulario_actualizar.reset();
                limpiarEvaluaciones();
            }
        } catch (error) {
            console.error(error);
        }
    });

    function limpiarEvaluaciones() {
        // Vaciar controles dinámicos
        contenedor_evaluaciones.innerHTML = "";

        // Crear nuevamente el primer control
        const div = document.createElement("div");
        div.classList.add("detalle_evaluacion");

        div.innerHTML = `
            <label>Tipo de Evaluación:</label>
            <select name="tipo_evaluacion[]" class="tipo_evaluacion"></select>

            <label>Porcentaje:</label>
            <input type="text" name="porcentaje[]" class="porcentaje_evaluacion" value="">

            <button type="button" class="btn_eliminar_detalle">Eliminar</button>
        `;

        contenedor_evaluaciones.appendChild(div);

        // Cargar opciones del select
        const select = div.querySelector(".tipo_evaluacion");
        poblarSelect(select);

        // Aplicar reglas iniciales
        recalcularPorcentajes();
        actualizarOpcionesSelects();
        verificarLimiteBoton();
    }

    const tipos_evaluacion = [
        ["EXAMEN", "Examen"],
        ["INFORME", "Informe"],
        ["PROYECTO", "Proyecto"],
        ["EXPOSICION", "Exposición"],
        ["PRACTICA", "Práctica"],
        ["CUESTIONARIO", "Cuestionario"],
        ["PROGRAMACION", "Desarrollo de Programa"],
        ["DIAGRAMA_FLUJO", "Diagrama de Flujo"],
        ["OTRO", "Otro"]
    ];

    function poblarSelect(selectElement) {
        selectElement.innerHTML = '<option value="">Seleccione tipo</option>';

        tipos_evaluacion.forEach(([valor, texto]) => {
            const option = document.createElement("option");
            option.value = valor;
            option.textContent = texto;
            selectElement.appendChild(option);
        });
    }

    const LIMITE_MAXIMO = 3;

    btn_agregar_detalle.addEventListener("click", () => {
        const cantidad = contenedor_evaluaciones.querySelectorAll(".detalle_evaluacion").length;
        if (cantidad >= LIMITE_MAXIMO) {
            return;
        }

        const div = document.createElement("div");
        div.classList.add("detalle_evaluacion");

        div.innerHTML = `
            <label>Tipo de Evaluación:</label>
            <select name="tipo_evaluacion[]" class="tipo_evaluacion"></select>

            <label>Porcentaje:</label>
            <input type="text" name="porcentaje[]" class="porcentaje_evaluacion" value="">

            <button type="button" class="btn_eliminar_detalle">Eliminar</button>
        `;

        contenedor_evaluaciones.appendChild(div);


        const select = div.querySelector(".tipo_evaluacion");
        poblarSelect(select);

        actualizarOpcionesSelects();
        recalcularPorcentajes();
        verificarLimiteBoton();
    });

    contenedor_evaluaciones.addEventListener("input", function (e) {
        if (!e.target.classList.contains("porcentaje_evaluacion")) {
            return;
        }

        const input = e.target;

        let valor = input.value;
        // Solo números
        valor = valor.replace(/\D/g, "");
        // Máximo 3 dígitos
        valor = valor.substring(0, 3);
        // Evitar ceros iniciales
        valor = valor.replace(/^0+(?=\d)/, "");

        // Si queda vacío mantener vacío mientras escribe
        if (valor === "") {
            input.value = "";
            return;
        }

        valor = Number(valor);
        // Máximo permitido
        if (valor > 100) {
            valor = 100;
        }

        input.value = valor;

        // Recalcular los demás porcentajes
        const inputs = Array.from(contenedor_evaluaciones.querySelectorAll(".porcentaje_evaluacion"));

        const otros = inputs.filter(item => item !== input);

        balancearCamposRestantes(input, otros, valor);
    });

    function balancearCamposRestantes(inputEditado, otrosInputs, valorActual) {
        let restante = 100 - valorActual;

        if (otrosInputs.length === 1) {
            otrosInputs[0].value = restante;
        } else if (otrosInputs.length === 2) {
            let valor1 = parseInt(otrosInputs[0].value) || 0;
            let valor2 = parseInt(otrosInputs[1].value) || 0;

            let suma = valor1 + valor2;

            if (suma === 0) {
                otrosInputs[0].value = Math.floor(restante / 2);
                otrosInputs[1].value = restante - Number(otrosInputs[0].value);
            } else {
                let nuevo1 = Math.round(restante * (valor1 / suma));

                let nuevo2 = restante - nuevo1;

                otrosInputs[0].value = nuevo1;
                otrosInputs[1].value = nuevo2;
            }
        }
    }

    contenedor_evaluaciones.addEventListener("click", (e) => {
        if (e.target.classList.contains("btn_eliminar_detalle")) {
            const detalles = contenedor_evaluaciones.querySelectorAll(".detalle_evaluacion");

            // Siempre debe quedar mínimo uno
            if (detalles.length > 1) {
                e.target.closest(".detalle_evaluacion").remove();

                actualizarOpcionesSelects();
                recalcularPorcentajes();
                verificarLimiteBoton();
            }
        }
    });

    contenedor_evaluaciones.addEventListener("change", function (e) {
        if (e.target.classList.contains("tipo_evaluacion")) {
            actualizarOpcionesSelects();
        }
    });

    function verificarLimiteBoton() {
        const cantidad = contenedor_evaluaciones.querySelectorAll(".detalle_evaluacion").length;

        if (cantidad >= LIMITE_MAXIMO) {
            btn_agregar_detalle.style.display = "none";
        } else {
            btn_agregar_detalle.style.display = "block";
        }
    }

    function actualizarOpcionesSelects() {
        const selects = Array.from(contenedor_evaluaciones.querySelectorAll(".tipo_evaluacion"));

        // Obtener valores seleccionados actualmente
        const valoresSeleccionados = selects.map(select => select.value).filter(valor => valor !== "");

        selects.forEach(selectActual => {
            const valorActual = selectActual.value;

            Array.from(selectActual.options).forEach(option => {
                // Mantener opción vacía disponible
                if (option.value === "") {
                    return;
                }
                // Si está seleccionada en otro select, bloquearla
                if (valoresSeleccionados.includes(option.value) && option.value !== valorActual) {
                    option.disabled = true;
                    option.style.display = "none";
                } else {
                    option.disabled = false;
                    option.style.display = "";
                }
            });
        });
    }

    function recalcularPorcentajes() {
        const inputs = Array.from(contenedor_evaluaciones.querySelectorAll(".porcentaje_evaluacion"));
        if (inputs.length === 1) {
            inputs[0].value = 100;
            inputs[0].readOnly = true;
            return;
        }
        inputs.forEach(input => { input.readOnly = false; });

        if (inputs.length === 2) {
            inputs[0].value = 50;
            inputs[1].value = 50;
        }

        if (inputs.length === 3) {
            inputs[0].value = 34;
            inputs[1].value = 33;
            inputs[2].value = 33;
        }
    }

    function actualizarOpcionesSelects() {
        const selects = Array.from(
            contenedor_evaluaciones.querySelectorAll(".tipo_evaluacion")
        );

        // Obtener valores seleccionados actualmente
        const valoresSeleccionados = selects
            .map(select => select.value)
            .filter(valor => valor !== "");

        selects.forEach(selectActual => {
            const valorActual = selectActual.value;

            Array.from(selectActual.options).forEach(option => {
                // Mantener opción vacía disponible
                if (option.value === "") {
                    return;
                }

                // Si está seleccionada en otro select, bloquearla
                if (valoresSeleccionados.includes(option.value) && option.value !== valorActual) {
                    option.disabled = true;
                    option.style.display = "none";
                } else {
                    option.disabled = false;
                    option.style.display = "";
                }
            });
        });
    }

});