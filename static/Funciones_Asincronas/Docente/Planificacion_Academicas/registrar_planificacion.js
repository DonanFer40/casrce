document.addEventListener("DOMContentLoaded", () => {

    const formulario_plan_estudio = document.getElementById("formulario_registrar");

    const select_nucleo_asignado = document.getElementById("nucleo_asignado");
    const select_pnfs_asignado = document.getElementById("pnfs_asignado");

    const select_asignacion_materia = document.getElementById("asignacion_materia");
    const input_periodo_academico = document.getElementById("periodo_academico");
    const select_seleccion_docente = document.getElementById("seleccion_docente");

    const contenedor_seleccion_docente = document.getElementById("contenedor_seleccion_docente");

    const select_perfiles_asignados = document.getElementById("perfiles_asignados");
    const input_perfil_asignado = document.getElementById("perfil_asignado");

    const cantidad_evaluaciones = document.getElementById("cantidad_evaluaciones");
    const contenedor_evaluacion = document.getElementById("contenedor_evaluacion");

    const estado_unidades = document.getElementById("estado_unidades");

    let materia = "", nucleo = "", pnf = "", periodo = "", docente = "";
    let fecha_inicio_periodo = "";
    let fecha_final_periodo = "";
    let evaluaciones_registradas = [];

    function obtener_csrf_token() {

        const cookie = document.cookie
            .split("; ")
            .find(row => row.startsWith("csrftoken="));

        return cookie
            ? decodeURIComponent(cookie.split("=")[1])
            : "";
    }

    let perfil_seleccionado = "";

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

                select_perfiles_asignados.append(
                    option_docente,
                    option_control
                );

                select_perfiles_asignados.style.display = "";
                input_perfil_asignado.style.display = "none";

                // Todavía no hay perfil seleccionado
                perfil_seleccionado = "";

                // No cargar núcleos todavía
                limpiar_nucleos();
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

        if (!perfil_seleccionado) {
            limpiar_nucleos();
            return;
        }

        if (perfil_seleccionado === "CONTROL_ESTUDIO") {

            contenedor_seleccion_docente.style.display = "";

        } else {

            contenedor_seleccion_docente.style.display = "none";

            select_seleccion_docente.innerHTML =
                "<option value='' selected>Selecciona un Docente</option>";
        }

        await nucleos_asignados(perfil_seleccionado);
    });

    function limpiar_nucleos() {

        select_nucleo_asignado.innerHTML = "<option value='' selected>Selecciona un núcleo</option>";

        select_pnfs_asignado.innerHTML = "<option value='' selected>Selecciona el núcleo primero</option>";
    }

    async function nucleos_asignados(perfil) {
        try {
            const formulario = new FormData();
            formulario.append("perfil", perfil);

            const respuesta = await fetch("/notas_academicas/nucl_asig_doc/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": obtener_csrf_token()
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            select_pnfs_asignado.innerHTML = "<option value='' selected>Selecciona el núcleo primero</option>";

            select_nucleo_asignado.innerHTML = "<option value='' selected>Selecciona un núcleo</option>";

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

        await materias_asignadas();
    });

    async function pnfs_asignados() {
        try {
            const formulario = new FormData();
            formulario.append("nucleo_asignado", nucleo);
            formulario.append("perfil", perfil_seleccionado);

            const respuesta = await fetch("/notas_academicas/pnfs_asig_doc/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": obtener_csrf_token()
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            select_pnfs_asignado.innerHTML = "<option value='' selected>Selecciona un P.N.F</option>";

            if (resultado.estado !== "exito") {
                await Swal.fire({
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
                select_pnfs_asignado.append(option_pnf);
            });
        } catch (error) {
            console.error(error);
        }
    }

    select_pnfs_asignado.addEventListener("change", async () => {

        pnf = select_pnfs_asignado.value;

        if (!pnf || !nucleo) {
            return;
        }

        if (perfil_seleccionado === "CONTROL_ESTUDIO") {

            // Primero debe seleccionar el docente
            await docente_seleccionado();

        } else if (perfil_seleccionado === "DOCENTE") {

            // El docente ya es el usuario de la sesión
            await materias_asignadas();
        }
    });

    async function docente_seleccionado() {
        try {
            if (!pnf || !nucleo) return;

            const formulario = new FormData();
            formulario.append("nucleo_asignado", nucleo);
            formulario.append("pnf_seleccionado", pnf);

            const respuesta = await fetch("/notas_academicas/doc_selec/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": obtener_csrf_token()
                },
                body: formulario
            });

            const resultado = await respuesta.json();
            console.log(resultado);

            select_seleccion_docente.innerHTML = "<option value='' selected>Selecciona un Docente</option>";

            if (resultado.estado !== "exito") {
                await Swal.fire({
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

        await materias_asignadas();
    });

    async function materias_asignadas() {
        try {
            if (!nucleo || !pnf) return;

            const formulario = new FormData();
            formulario.append("id_nucleo", nucleo);
            formulario.append("id_pnf", pnf);
            formulario.append("perfil", perfil_seleccionado);

            if (perfil_seleccionado === "CONTROL_ESTUDIO") {
                if (!docente) return;

                formulario.append("docente", docente);
            }

            const respuesta = await fetch(
                "/notas_academicas/mat_asig_doc/",
                {
                    method: "POST",
                    headers: {
                        "X-CSRFToken": obtener_csrf_token()
                    },
                    body: formulario
                }
            );

            const resultado = await respuesta.json();

            console.log(resultado);

            select_asignacion_materia.innerHTML =
                "<option value='' selected>Selecciona la materia</option>";

            if (resultado.estado !== "exito") {
                await Swal.fire({
                    text: resultado.descripcion,
                    icon: resultado.icon,
                    title: resultado.title,
                    allowOutsideClick: false,
                    allowEscapeKey: false
                });

                return;
            }

            resultado.datos.forEach(materia => {
                const option_materia =
                    document.createElement("option");

                option_materia.value =
                    materia.id_materia_asignada;

                option_materia.textContent =
                    materia.nombre;

                select_asignacion_materia.append(
                    option_materia
                );
            });

            if (
                resultado.periodos_academicos &&
                resultado.periodos_academicos.length > 0
            ) {
                const periodo =
                    resultado.periodos_academicos[0];

                input_periodo_academico.value =
                    periodo.nombre;

                input_periodo_academico.dataset.id_periodo_academico =
                    periodo.id_periodo;

                input_periodo_academico.dataset.fecha_inicio =
                    periodo.fecha_inicio;

                input_periodo_academico.dataset.fecha_final =
                    periodo.fecha_final;
            } else {
                input_periodo_academico.value = "";

                delete input_periodo_academico.dataset.id_periodo_academico;
                delete input_periodo_academico.dataset.fecha_inicio;
                delete input_periodo_academico.dataset.fecha_final;
            }

        } catch (error) {
            console.error(error);
        }
    }

    select_asignacion_materia.addEventListener("change", async () => {
        materia = select_asignacion_materia.value;

        periodo = input_periodo_academico.dataset.id_periodo_academico;

        await fecha_periodo_seleccionado();

        await unidades_registradas();
    });

    async function fecha_periodo_seleccionado() {
        try {
            const formulario = new FormData();
            formulario.append("id_periodo", periodo);

            const respuesta = await fetch("/notas_academicas/fech_cal_mat/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": obtener_csrf_token()
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            if (resultado.estado === "exito") {
                fecha_inicio_periodo = resultado.fecha_inicio;
                fecha_final_periodo = resultado.fecha_final;

                document.querySelectorAll('input[type="date"][name^="fecha_evaluacion_"]')
                    .forEach(input => {
                        input.min = fecha_inicio_periodo;
                        input.max = fecha_final_periodo;
                    });
            }
        } catch (error) {
            console.error(error);
        }
    }

    function sumar_dias(fecha, dias) {
        const fecha_obj = new Date(`${fecha}T00:00:00`);
        fecha_obj.setDate(fecha_obj.getDate() + dias);

        return fecha_obj.toISOString().split("T")[0];
    }

    function obtener_ultima_fecha_evaluacion() {

        if (!evaluaciones_registradas.length) {
            return fecha_inicio_periodo;
        }

        const fechas = evaluaciones_registradas
            .map(evaluacion => evaluacion.fecha_evaluacion)
            .filter(Boolean)
            .sort();

        if (!fechas.length) {
            return fecha_inicio_periodo;
        }

        return sumar_dias(fechas[fechas.length - 1], 7);
    }

    function mostrar_controles_evaluacion() {

        const cantidad = Number(cantidad_evaluaciones.value);

        contenedor_evaluacion.innerHTML = "";

        if (cantidad === 0) {
            contenedor_evaluacion.innerHTML = `
            <p class="ayuda_evaluaciones">
                Seleccione la cantidad de evaluaciones que tendrá esta unidad.
            </p>
        `;
            return;
        }

        const fecha_minima = obtener_ultima_fecha_evaluacion();

        for (let i = 1; i <= cantidad; i++) {

            const evaluacion = document.createElement("div");

            evaluacion.classList.add("bloque_evaluacion");

            evaluacion.innerHTML = `
                <h3>Evaluación ${i}</h3>

                <label for="metodo_evaluacion_${i}">Método de Evaluación:</label>
                <input
                    type="text"
                    name="metodo_evaluacion_${i}"
                    id="metodo_evaluacion_${i}"
                    list="metodos_evaluacion_${i}"
                    maxlength="120"
                    placeholder="Seleccione o escriba un método de evaluación"
                    autocomplete="off"
                    required>

                <datalist id="metodos_evaluacion_${i}">
                    <option value="Prueba escrita">
                    <option value="Exposición">
                    <option value="Taller">
                    <option value="Debate">
                    <option value="Práctica">
                    <option value="Ensayo">
                    <option value="Investigación">
                    <option value="Proyecto">
                    <option value="Seminario">
                    <option value="Estudio de caso">
                    <option value="Portafolio">
                </datalist>

                <label for="fecha_evaluacion_${i}">Fecha de Evaluación:</label>
                <input
                    type="date"
                    name="fecha_evaluacion_${i}"
                    id="fecha_evaluacion_${i}"
                    class="fecha_evaluacion"
                    min="${fecha_minima}"
                    max="${fecha_final_periodo}"
                    required>

                <label for="porcentaje_evaluacion_${i}">Porcentaje de Evaluación:</label>
                <input
                    type="text"
                    name="porcentaje_evaluacion_${i}"
                    id="porcentaje_evaluacion_${i}"
                    ${cantidad === 1 ? `value="25" readonly` : `maxlength="3"
                        placeholder="Ingrese el porcentaje"
                        autocomplete="off"`
                }
                    required>
            `;

            contenedor_evaluacion.appendChild(evaluacion);
        }

        actualizar_limites_fechas();

        if (cantidad === 2) {
            validarPorcentajes();
        }
    }

    function actualizar_limites_fechas() {
        const fechas = contenedor_evaluacion.querySelectorAll(".fecha_evaluacion");
        if (!fechas.length) return;

        let limite = obtener_ultima_fecha_evaluacion();

        fechas.forEach((fecha, indice) => {
            fecha.min = limite;
            fecha.max = fecha_final_periodo;

            if (fecha.value && (fecha.value < fecha.min || fecha.value > fecha.max)) {
                fecha.value = "";
            }

            if (fecha.value) {
                limite = fecha.value;
            }
        });
    }

    contenedor_evaluacion.addEventListener("change", (e) => {

        if (!e.target.classList.contains("fecha_evaluacion")) {
            return;
        }

        actualizar_limites_fechas();
    });

    function validarPorcentajes() {
        const porcentaje1 = document.getElementById("porcentaje_evaluacion_1");
        const porcentaje2 = document.getElementById("porcentaje_evaluacion_2");

        if (!porcentaje1 || !porcentaje2) {
            return;
        }

        // CUANDO CAMBIA EL PRIMER PORCENTAJE
        porcentaje1.addEventListener("input", function () {
            // Solo números
            this.value = this.value.replace(/\D/g, "");

            let valor1 = Number(this.value || 0);

            // Nunca puede superar el 25%
            if (valor1 > 25) {
                valor1 = 25;
                this.value = "25";
            }

            // La segunda evaluación completa el 25%
            const valor2 = 25 - valor1;

            porcentaje2.value = valor2;
        });

        // CUANDO CAMBIA EL SEGUNDO PORCENTAJE
        porcentaje2.addEventListener("input", function () {

            // Solo números
            this.value = this.value.replace(/\D/g, "");

            let valor2 = Number(this.value || 0);

            // Nunca puede superar el 25%
            if (valor2 > 25) {
                valor2 = 25;
                this.value = "25";
            }

            // La primera evaluación completa el 25%
            const valor1 = 25 - valor2;

            porcentaje1.value = valor1;
        });
    }

    cantidad_evaluaciones.addEventListener("change", mostrar_controles_evaluacion);

    async function unidades_registradas() {
        try {
            if (!materia || !periodo) return;

            const formulario = new FormData();
            formulario.append("id_asignacion", materia);
            formulario.append("id_periodo_academico", periodo);

            const respuesta = await fetch("/notas_academicas/datos_unid_reg/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": obtener_csrf_token()
                },
                body: formulario
            });

            const resultado = await respuesta.json();

            console.log(resultado);

            if (resultado.estado !== "exito") {
                estado_unidades.className = "estado_unidades estado_error";
                estado_unidades.innerHTML = `
                <p>${resultado.descripcion || "No se pudieron consultar las unidades."}</p>
            `;
                return;
            }

            evaluaciones_registradas = resultado.evaluaciones || [];

            const cantidad = Number(resultado.cantidad || 0);

            estado_unidades.innerHTML = `
            <strong>Unidades registradas:</strong> ${cantidad} de 6
            <span class="separador">|</span>
            <strong>Mínimo:</strong> 4
            <span class="separador">|</span>
            <strong>Máximo:</strong> 6
        `;

            if (cantidad < 4) {
                estado_unidades.className = "estado_unidades estado_advertencia";

                estado_unidades.innerHTML += `
                <p>El plan aún no cumple con el mínimo de <strong>4 unidades</strong>.</p>
            `;
            } else if (cantidad <= 6) {
                estado_unidades.className = "estado_unidades estado_correcto";

                estado_unidades.innerHTML += `
                <p>El plan cumple con la cantidad de unidades requerida.</p>
            `;
            } else {
                estado_unidades.className = "estado_unidades estado_error";

                estado_unidades.innerHTML += `
                <p>El plan supera el máximo permitido de <strong>6 unidades</strong>.</p>
            `;
            }

            mostrar_controles_evaluacion();

        } catch (error) {
            console.error(error);
        }
    }

    formulario_plan_estudio.addEventListener("submit", async (e) => {
        e.preventDefault();
        try {
            const formulario = new FormData(formulario_plan_estudio);
            formulario.append("id_periodo", input_periodo_academico.dataset.id_periodo_academico);

            const respuesta = await fetch("/notas_academicas/reg_pl_act/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": obtener_csrf_token()
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
                formulario_plan_estudio.reset();
                contenedor_evaluacion.innerHTML = "";
                estado_unidades.innerHTML = "";
            }
        } catch (error) {
            console.error(error);
        }
    });
});