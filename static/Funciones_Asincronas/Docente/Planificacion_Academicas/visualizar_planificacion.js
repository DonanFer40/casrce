document.addEventListener("DOMContentLoaded", () => {

    const contenedor_planes_actividades = document.getElementById("contenedor_planes_actividades");

    const dialogo_planes_estudios = document.getElementById("dialogo_planes_estudios");
    const cerrar_dialogo_visualizar = document.getElementById("cerrar_dialogo_visualizar");

    const dialogo_actualizar_plan_estudio = document.getElementById("dialogo_actualizar_plan_estudio");
    const cerrar_dialogo_actualizar = document.getElementById("cerrar_dialogo_actualizar");

    const select_nucleo_asignado = document.getElementById("nucleo_asignado");
    const select_pnfs_asignado = document.getElementById("pnfs_asignado");

    // controles actualización
    const formulario_actualizacion = document.getElementById("formulario_actualizacion");

    const input_id_plan = document.getElementById("id_plan");
    const input_materia = document.getElementById("materia");
    const input_pnf = document.getElementById("pnf");
    const input_nucleo = document.getElementById("nucleo");
    const input_periodo_academico = document.getElementById("periodo_academico");

    const btn_actualizar = document.getElementById("btn_actualizar");

    const contenedor_seleccion_docente = document.getElementById("contenedor_seleccion_docente");
    const select_seleccion_docente = document.getElementById("seleccion_docente");

    const select_perfiles_asignados = document.getElementById("perfiles_asignados");
    const input_perfil_asignado = document.getElementById("perfil_asignado");

    const pestanas_unidades_actualizacion = document.getElementById("pestanas_unidades_actualizacion");
    const contenedor_unidades = document.getElementById("contenedor_unidades");

    let nucleo = "", pnf = "", docente = "";

    let perfil_seleccionado = "";

    async function perfiles_asignados() {
        try {
            const respuesta = await fetch("/notas_academicas/perf_asig/");
            const resultado = await respuesta.json();
            console.log(resultado);

            const tiene_docente = resultado.docente;
            const tiene_control = resultado.control_estudio;

            input_perfil_asignado.value = "";
            select_perfiles_asignados.innerHTML = "";

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

                // Seleccionar realmente DOCENTE
                select_perfiles_asignados.value = "DOCENTE";
                perfil_seleccionado = select_perfiles_asignados.value;

                contenedor_seleccion_docente.style.display = "none";

                select_seleccion_docente.innerHTML = "<option value='' selected>Selecciona un Docente</option>";

                await nucleos_asignados(perfil_seleccionado);
                await pnfs_asignados(perfil_seleccionado);
                await obtenerPlanesActividades(perfil_seleccionado);
            } else if (tiene_docente) {

                // Solamente Docente
                perfil_seleccionado = "DOCENTE";

                input_perfil_asignado.value = "Docente";

                input_perfil_asignado.style.display = "";
                select_perfiles_asignados.style.display = "none";

                contenedor_seleccion_docente.style.display = "none";

                await nucleos_asignados(perfil_seleccionado);
                await pnfs_asignados(perfil_seleccionado);
                await obtenerPlanesActividades(perfil_seleccionado);
            } else if (tiene_control) {

                // Solamente Control de Estudio
                perfil_seleccionado = "CONTROL_ESTUDIO";

                input_perfil_asignado.value = "Encargado de Control de Estudio";

                input_perfil_asignado.style.display = "";
                select_perfiles_asignados.style.display = "none";

                contenedor_seleccion_docente.style.display = "";

                await nucleos_asignados(perfil_seleccionado);
                await pnfs_asignados(perfil_seleccionado);

                await obtenerPlanesActividades(perfil_seleccionado);

            } else {

                // No tiene ningún perfil
                perfil_seleccionado = "";

                input_perfil_asignado.value = "";

                input_perfil_asignado.style.display = "";
                select_perfiles_asignados.style.display = "none";

                contenedor_seleccion_docente.style.display = "none";

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

            select_seleccion_docente.innerHTML = "<option value='' selected>Selecciona un Docente</option>";
        }

        await nucleos_asignados(perfil_seleccionado);
        await pnfs_asignados(perfil_seleccionado);
        await obtenerPlanesActividades(perfil_seleccionado);
    });

    async function nucleos_asignados(perfil) {
        try {
            const formulario = new FormData();
            formulario.append("perfil", perfil);

            const respuesta = await fetch("/notas_academicas/nucl_asig_doc/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);


            select_nucleo_asignado.innerHTML = "<option value='' selected>Selecciona un Núcleo</option>";

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

    select_nucleo_asignado.addEventListener("change", async () => {
        nucleo = select_nucleo_asignado.value;

        await obtenerPlanesActividades(perfil_seleccionado);

        await pnfs_asignados(perfil_seleccionado);
    });

    async function pnfs_asignados(perfil_seleccionado) {
        try {
            const formulario = new FormData();
            formulario.append("nucleo_asignado", nucleo);
            formulario.append("perfil", perfil_seleccionado);
            console.log(perfil_seleccionado)

            const respuesta = await fetch("/notas_academicas/todos_pnfs_asig_doc/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);


            select_pnfs_asignado.innerHTML = "<option value='' selected>Selecciona un P.N.F</option>";

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
    pnfs_asignados();

    select_pnfs_asignado.addEventListener("change", async () => {

        pnf = select_pnfs_asignado.value;

        await obtenerPlanesActividades(perfil_seleccionado);

        if (perfil_seleccionado === "CONTROL_ESTUDIO") {
            await docente_seleccionado();
        }
    });

    async function docente_seleccionado() {
        try {
            const formulario = new FormData();
            formulario.append("id_pnf", pnf);

            const respuesta = await fetch("/notas_academicas/doc_reg/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
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

            resultado.docentes.forEach(docente => {
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

        await obtenerPlanesActividades(perfil_seleccionado);
    });

    async function obtenerPlanesActividades(perfil_seleccionado) {
        try {
            const formulario = new FormData();
            formulario.append("perfil", perfil_seleccionado);
            formulario.append("nucleo", nucleo);
            formulario.append("pnf", pnf);
            formulario.append("docente", docente);

            const respuesta = await fetch("/notas_academicas/pl_reg/", {
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

            contenedor_planes_actividades.innerHTML = "";

            if (!resultado.datos || resultado.datos.length === 0) {
                contenedor_planes_actividades.innerHTML = `
                <tr>
                    <td colspan="8">
                        No hay planes de actividades registrados.
                    </td>
                </tr>
            `;

                return;
            }

            resultado.datos.forEach((plan, index) => {

                let accion = "";

                if (
                    plan.cantidad_unidades >= 4 &&
                    plan.estado_aceptacion === "BORRADOR"
                ) {
                    accion = `
                    <button
                        type="button"
                        class="btn-enviar-plan"
                        data-id-plan="${plan.id_plan}">
                        Enviar al Coordinador
                    </button>
                `;
                }

                if (plan.estado_aceptacion === "DENEGADA") {
                    accion = `
                    <button
                        type="button"
                        class="btn-enviar-plan"
                        data-id-plan="${plan.id_plan}"
                        data-observacion="${plan.observacion || ""}">
                        Enviar nuevamente
                    </button>
                `;
                }

                const fila = document.createElement("tr");

                fila.dataset.idPlan = plan.id_plan;
                fila.dataset.estado = plan.estado_aceptacion;

                fila.innerHTML = `
                <td>${index + 1}</td>
                <td>${plan.materia}</td>
                <td>${plan.estado_aceptacion_display}</td>
                <td>${plan.cantidad_unidades}</td>
                <td>${plan.nucleo}</td>
                <td>${plan.pnf}</td>
                <td>${plan.fecha_registro}</td>
                <td>${accion}</td>
            `;

                contenedor_planes_actividades.appendChild(fila);
            });

        } catch (error) {
            console.error(error);

            contenedor_planes_actividades.innerHTML = `
            <tr>
                <td colspan="8">
                    Ocurrió un error al consultar los planes de actividades.
                </td>
            </tr>
        `;
        }
    }

    contenedor_planes_actividades.addEventListener("click", async (e) => {
        const boton = e.target.closest(".btn-enviar-plan");
        if (boton) {
            e.stopPropagation();

            const id_plan = boton.dataset.idPlan;
            if (!id_plan || id_plan === "undefined") return;

            const resultado = await Swal.fire({
                title: "¿Enviar plan de actividades?",
                text: "¿Está seguro de enviar este plan de actividades al Coordinador PNF?",
                icon: "question",
                showCancelButton: true,
                confirmButtonText: "Sí, enviar",
                cancelButtonText: "Cancelar",
                reverseButtons: true
            });

            if (resultado.isConfirmed) {
                await coordinador_pnf(id_plan);
            }
            return;
        }

        const fila = e.target.closest("tr");
        if (!fila) return;

        const id_plan = fila.dataset.idPlan;
        const estado = fila.dataset.estado;

        if (!id_plan || id_plan === "undefined") return;

        if (estado === "ACEPTADA" || estado === "ENVIADO") {
            await Swal.fire({
                title: "Plan aceptado",
                text: "Este plan ya fue aceptado y no puede ser modificado.",
                icon: "info",
                confirmButtonText: "Visualizar"
            });

            await plan_estudio(id_plan);
            return;
        }

        if (estado === "DENEGADA") {
            const observacion = fila.dataset.observacion || "";

            const resultado = await Swal.fire({
                title: "Plan de actividades denegado",
                html: `
                    <div style="text-align: left;">
                        <p>El Coordinador PNF ha denegado este plan de actividades.</p>
                        <div style="
                            margin-top: 15px;
                            padding: 15px;
                            border-radius: 8px;
                            background: #f8f9fa;
                            border: 1px solid #dee2e6;">
                            <strong>Observación:</strong>
                            <p style="
                                margin-top: 8px;
                                margin-bottom: 0;
                                white-space: pre-wrap;">

                                ${observacion || "No se registró una observación."}
                            </p>
                        </div>
                    </div>
                `,
                icon: "warning",
                showCancelButton: true,
                confirmButtonText: "Modificar plan",
                cancelButtonText: "Cerrar",
                reverseButtons: true
            });

            if (resultado.isConfirmed) {
                await actualizar_plan_estudio(id_plan);
            }
            return;
        }

        const resultado = await Swal.fire({
            title: "¿Qué desea hacer?",
            text: "Seleccione una opción para el plan de actividades.",
            icon: "question",
            showCancelButton: true,
            confirmButtonText: "Visualizar",
            cancelButtonText: "Modificar",
            reverseButtons: true
        });

        if (resultado.isConfirmed) {
            await plan_estudio(id_plan);
            return;
        }

        if (resultado.dismiss === Swal.DismissReason.cancel) {
            await actualizar_plan_estudio(id_plan);
            return;
        }
    });

    async function plan_estudio(id_plan) {
        try {
            const formulario = new FormData();
            formulario.append("id_plan", id_plan);

            const respuesta = await fetch("/notas_academicas/datos_pl_reg/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            const plan = resultado.datos;

            const informacion_plan = document.getElementById("informacion_plan");
            const pestanas_unidades = document.getElementById("pestanas_unidades");
            const contenido_unidades = document.getElementById("contenido_unidades");

            informacion_plan.innerHTML = `
                <p><strong>Materia:</strong>${plan.materia}</p>
                <p><strong>PNF:</strong>${plan.pnf} </p>
                <p><strong>Núcleo:</strong>${plan.nucleo}</p>
                <p><strong>Período:</strong>${plan.periodo_academico} </p>
            `;

            pestanas_unidades.innerHTML = "";
            contenido_unidades.innerHTML = "";

            plan.detalles.forEach((detalle, indice) => {
                const pestana = document.createElement("button");
                pestana.type = "button";
                pestana.className = "pestana_unidad";
                pestana.textContent = detalle.titulo_unidad;
                pestana.dataset.idDetalle = detalle.id_detalle;

                // Primera unidad activa
                if (indice === 0) {
                    pestana.classList.add("activa");
                }
                pestanas_unidades.appendChild(pestana);

                const contenido = document.createElement("div");
                contenido.className = "contenido_unidad";
                contenido.dataset.idDetalle = detalle.id_detalle;

                // Ocultar todas excepto la primera
                if (indice !== 0) {
                    contenido.style.display = "none";
                }

                let evaluacionesHTML = "";

                if (detalle.evaluaciones && detalle.evaluaciones.length > 0) {
                    detalle.evaluaciones.forEach(evaluacion => {
                        evaluacionesHTML += `
                            <div class="evaluacion">
                                <div class="evaluacion_info">
                                    <strong>${evaluacion.metodo_evaluacion}</strong>
                                    <span class="porcentaje_evaluacion">
                                        ${evaluacion.porcentaje_evaluacion}%
                                    </span>
                                </div>
                                <div class="evaluacion_fecha">
                                    <strong>Fecha:</strong>
                                    <span>${evaluacion.fecha_evaluacion}</span>
                                </div>
                            </div>
                        `;
                    });
                } else {
                    evaluacionesHTML = `<p class="sin_evaluaciones">No hay evaluaciones registradas.</p> `;
                }

                contenido.innerHTML = `
                    <h4>${detalle.titulo_unidad}</h4>
                    <div class="dato_unidad">
                        <strong>Ponderación:</strong>
                        <span>${detalle.ponderacion}</span>
                    </div>
                    <div class="contenido_unidad_texto">
                        <strong>Contenido:</strong>
                        <p>${detalle.contenido_unidad}</p>
                    </div>

                    <div class="seccion_evaluaciones">
                        <h4>Evaluaciones</h4>
                        <div class="evaluaciones_unidad">
                            ${evaluacionesHTML}
                        </div>
                    </div>
                `;

                contenido_unidades.appendChild(contenido);
            });

            document.querySelectorAll(".pestana_unidad").forEach(pestana => {
                pestana.addEventListener("click", () => {
                    const idDetalle = pestana.dataset.idDetalle;

                    // QUITAR PESTAÑA ACTIVA
                    document.querySelectorAll(".pestana_unidad").forEach(p => {
                        p.classList.remove("activa");
                    });

                    // OCULTAR CONTENIDOS
                    document.querySelectorAll(".contenido_unidad").forEach(contenido => {
                        contenido.style.display = "none";
                    });

                    pestana.classList.add("activa");

                    const contenido = document.querySelector(`.contenido_unidad[data-id-detalle="${idDetalle}"]`);
                    if (contenido) {
                        contenido.style.display = "block";
                    }
                });
            });

            dialogo_planes_estudios.showModal();
        } catch (error) {
            console.error(error);
        }
    }

    cerrar_dialogo_visualizar.addEventListener("click", () => {
        dialogo_planes_estudios.close();
    });

    function sumarDias(fecha, dias) {
        const fechaObj = new Date(`${fecha}T00:00:00`);
        fechaObj.setDate(fechaObj.getDate() + dias);

        return fechaObj.toISOString().split("T")[0];
    }

    function obtenerUltimaFechaUnidad(detalles, indiceUnidad) {
        let ultimaFecha = null;

        for (let i = 0; i < indiceUnidad; i++) {
            const evaluaciones = detalles[i].evaluaciones || [];

            evaluaciones.forEach(evaluacion => {
                if (
                    evaluacion.fecha_evaluacion &&
                    (!ultimaFecha ||
                        evaluacion.fecha_evaluacion > ultimaFecha)
                ) {
                    ultimaFecha = evaluacion.fecha_evaluacion;
                }
            });
        }

        return ultimaFecha;
    }

    function obtenerFechaMinimaUnidad(detalles, indiceUnidad, fechaInicioPeriodo) {
        const ultimaFecha = obtenerUltimaFechaUnidad(
            detalles,
            indiceUnidad
        );

        if (!ultimaFecha) {
            return fechaInicioPeriodo;
        }

        return sumarDias(ultimaFecha, 7);
    }

    async function actualizar_plan_estudio(id_plan) {
        try {
            const formulario = new FormData();
            formulario.append("id_plan", id_plan);

            const respuesta = await fetch("/notas_academicas/datos_pl_reg/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            dialogo_actualizar_plan_estudio.showModal();

            input_id_plan.value = resultado.datos.id_plan;
            input_materia.value = resultado.datos.materia;
            input_nucleo.value = resultado.datos.nucleo;
            input_pnf.value = resultado.datos.pnf;
            input_periodo_academico.value = resultado.datos.periodo_academico;
            const fechaInicioPeriodo = resultado.datos.fecha_inicio;
            const fechaFinalPeriodo = resultado.datos.fecha_final;

            pestanas_unidades_actualizacion.innerHTML = "";
            contenedor_unidades.innerHTML = "";

            // CREAR UNIDADES
            resultado.datos.detalles.forEach((detalle, i) => {
                const numeroUnidad = i + 1;

                // CREAR PESTAÑA
                const pestana = document.createElement("button");
                pestana.type = "button";
                pestana.classList.add("pestana_unidad_actualizacion");
                pestana.textContent = `Unidad ${numeroUnidad}`;
                if (i === 0) {
                    pestana.classList.add("activa");
                }
                pestanas_unidades_actualizacion.appendChild(pestana);

                // CREAR CONTENIDO DE LA UNIDAD
                const unidad = document.createElement("div");
                unidad.classList.add("unidad_contenido_actualizacion");
                if (i === 0) {
                    unidad.classList.add("activa");
                }
                unidad.innerHTML = `
                    <input type="hidden" name="id_detalle_${i}" value="${detalle.id_detalle}">
                    <label for="titulo_unidad_${i}">Título de la Unidad:</label>
                    <input
                        type="text"
                        name="titulo_unidad_${i}"
                        id="titulo_unidad_${i}"
                        maxlength="100"
                        value="${detalle.titulo_unidad || ""}"
                        autocomplete="off"
                        required>

                    <label for="contenido_unidad_${i}">Contenido de la Unidad:</label>
                    <textarea
                        name="contenido_unidad_${i}"
                        id="contenido_unidad_${i}"
                        required>${detalle.contenido_unidad || ""}</textarea>

                    <h4>Evaluaciones</h4>
                    <div id="contenedor_evaluaciones_${i}" class="contenedor_evaluaciones_actualizacion"></div>
                `;
                contenedor_unidades.appendChild(unidad);

                // CONTENEDOR DE EVALUACIONES
                const contenedorEvaluaciones = unidad.querySelector(`#contenedor_evaluaciones_${i}`);

                // CREAR EVALUACIONES
                detalle.evaluaciones.forEach((evaluacion, j) => {

                    const indice = `${i}_${j}`;

                    let fechaMinimaEvaluacion;

                    if (j === 0) {
                        fechaMinimaEvaluacion = obtenerFechaMinimaUnidad(
                            resultado.datos.detalles,
                            i,
                            fechaInicioPeriodo
                        );
                    } else {
                        const evaluacionAnterior = detalle.evaluaciones[j - 1];

                        fechaMinimaEvaluacion =
                            evaluacionAnterior.fecha_evaluacion;
                    }

                    const contenedor = document.createElement("div");
                    contenedor.classList.add("evaluacion_actualizar");

                    contenedor.innerHTML = `
                        <input
                            type="hidden"
                            name="id_evaluacion_${indice}"
                            value="${evaluacion.id_evaluacion}">

                        <div class="evaluacion_cabecera">
                            <h4>Evaluación ${j + 1}</h4>
                        </div>

                        <div class="campo_formulario">
                            <label for="metodo_evaluacion_${indice}">
                                Método de Evaluación:
                            </label>

                            <input
                                type="text"
                                name="metodo_evaluacion_${indice}"
                                id="metodo_evaluacion_${indice}"
                                list="metodos_evaluacion_${indice}"
                                maxlength="100"
                                placeholder="Seleccione o escriba un método de evaluación"
                                autocomplete="off"
                                value="${evaluacion.metodo_evaluacion || ""}"
                                required>

                            <datalist id="metodos_evaluacion_${indice}">
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
                        </div>

                        <div class="campo_formulario">
                            <label for="porcentaje_evaluacion_${indice}">
                                Porcentaje de Evaluación:
                            </label>

                            <input
                                type="text"
                                name="porcentaje_evaluacion_${indice}"
                                id="porcentaje_evaluacion_${indice}"
                                min="0.01"
                                max="100"
                                step="0.01"
                                placeholder="Ejemplo: 50"
                                value="${evaluacion.porcentaje_evaluacion || ""}"
                                required>
                        </div>

                        <div class="campo_formulario">
                            <label for="fecha_evaluacion_${indice}">
                                Fecha de Evaluación:
                            </label>

                            <input
                                type="date"
                                name="fecha_evaluacion_${indice}"
                                id="fecha_evaluacion_${indice}"
                                value="${evaluacion.fecha_evaluacion || ""}"
                                min="${fechaMinimaEvaluacion}"
                                max="${fechaFinalPeriodo}"
                                required>
                        </div>
                    `;

                    contenedorEvaluaciones.appendChild(contenedor);
                });

                // VALIDAR PORCENTAJES
                const actualizarPorcentajes = validarPorcentajes(contenedorEvaluaciones);

                // CONTROLES DE LA UNIDAD
                const controlesUnidad = document.createElement("div");
                controlesUnidad.classList.add("controles_unidad");
                controlesUnidad.innerHTML = `
                    <button type="button" class="btn_eliminar_unidad">Eliminar unidad</button>
                `;
                unidad.appendChild(controlesUnidad);

                // CONTROLES DE EVALUACIONES
                const controlesEvaluaciones = document.createElement("div");
                controlesEvaluaciones.classList.add("controles_evaluaciones");
                controlesEvaluaciones.innerHTML = `
                    <button type="button" class="btn_agregar_evaluacion">+ Agregar evaluación</button>
                    <button type="button" class="btn_eliminar_evaluacion">Eliminar evaluación</button>
                `;
                unidad.appendChild(controlesEvaluaciones);

                // BOTÓN AGREGAR EVALUACIÓN
                const botonAgregar = controlesEvaluaciones.querySelector(".btn_agregar_evaluacion");

                botonAgregar.addEventListener("click", () => {

                    const evaluaciones = contenedorEvaluaciones.querySelectorAll(
                        ".evaluacion_actualizar"
                    );

                    if (evaluaciones.length >= 2) {
                        return;
                    }

                    const indice = evaluaciones.length;

                    let fechaMinimaEvaluacion = fechaInicioPeriodo;

                    if (evaluaciones.length > 0) {

                        const evaluacionAnterior = evaluaciones[
                            evaluaciones.length - 1
                        ];

                        const fechaAnterior = evaluacionAnterior.querySelector(
                            'input[type="date"]'
                        );

                        if (fechaAnterior && fechaAnterior.value) {
                            fechaMinimaEvaluacion = fechaAnterior.value;
                        }
                    } else {

                        fechaMinimaEvaluacion = obtenerFechaMinimaUnidad(
                            resultado.datos.detalles,
                            i,
                            fechaInicioPeriodo
                        );
                    }

                    const contenedor = document.createElement("div");

                    contenedor.classList.add(
                        "evaluacion_actualizar"
                    );

                    contenedor.innerHTML = `
                        <div class="evaluacion_cabecera">
                            <h4>Evaluación ${indice + 1}</h4>
                        </div>

                        <div class="campo_formulario">
                            <label for="metodo_evaluacion_${i}_${indice}">
                                Método de Evaluación:
                            </label>

                            <input
                                type="text"
                                name="metodo_evaluacion_${i}_${indice}"
                                id="metodo_evaluacion_${i}_${indice}"
                                list="metodos_evaluacion_${i}_${indice}"
                                maxlength="100"
                                placeholder="Seleccione o escriba un método de evaluación"
                                autocomplete="off"
                                required>

                            <datalist id="metodos_evaluacion_${i}_${indice}">
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
                        </div>

                        <div class="campo_formulario">
                            <label for="porcentaje_evaluacion_${i}_${indice}">
                                Porcentaje de Evaluación:
                            </label>

                            <input
                                type="text"
                                name="porcentaje_evaluacion_${i}_${indice}"
                                id="porcentaje_evaluacion_${i}_${indice}"
                                min="1"
                                max="24"
                                step="1"
                                placeholder="Ejemplo: 15"
                                required>
                        </div>

                        <div class="campo_formulario">
                            <label for="fecha_evaluacion_${i}_${indice}">
                                Fecha de Evaluación:
                            </label>

                            <input
                                type="date"
                                name="fecha_evaluacion_${i}_${indice}"
                                id="fecha_evaluacion_${i}_${indice}"
                                min="${fechaMinimaEvaluacion}"
                                max="${fechaFinalPeriodo}"
                                required>
                        </div>
                    `;

                    contenedorEvaluaciones.appendChild(
                        contenedor
                    );

                    actualizarPorcentajes();
                    actualizarControles();
                });

                // BOTÓN ELIMINAR EVALUACIÓN
                const botonEliminar = controlesEvaluaciones.querySelector(".btn_eliminar_evaluacion");

                botonEliminar.addEventListener("click", () => {
                    const evaluaciones = contenedorEvaluaciones.querySelectorAll(".evaluacion_actualizar");
                    if (evaluaciones.length <= 1) {
                        return;
                    }

                    const segunda = evaluaciones[1];
                    const inputId = segunda.querySelector('input[name^="id_evaluacion_"]');

                    if (inputId && inputId.value) {
                        const inputEliminar = document.createElement("input");
                        inputEliminar.type = "hidden";
                        inputEliminar.name = "eliminar_evaluacion[]";
                        inputEliminar.value = inputId.value;
                        formulario_actualizacion.appendChild(inputEliminar);
                    }
                    segunda.remove();
                    actualizarPorcentajes();
                    actualizarControles();
                });

                // BOTÓN ELIMINAR UNIDAD
                const botonEliminarUnidad = controlesUnidad.querySelector(".btn_eliminar_unidad");

                botonEliminarUnidad.addEventListener("click", () => {
                    const unidades = contenedor_unidades.querySelectorAll(".unidad_contenido_actualizacion");
                    // No permitir eliminar la última unidad
                    if (unidades.length <= 1) {
                        return;
                    }

                    // GUARDAR ID DE LA UNIDAD PARA ELIMINAR
                    const inputIdDetalle = unidad.querySelector('input[name^="id_detalle_"]');
                    if (inputIdDetalle && inputIdDetalle.value) {
                        const inputEliminar = document.createElement("input");
                        inputEliminar.type = "hidden";
                        inputEliminar.name = "eliminar_detalle[]";
                        inputEliminar.value = inputIdDetalle.value;
                        formulario_actualizacion.appendChild(inputEliminar);
                    }

                    // ELIMINAR PESTAÑA
                    pestana.remove();

                    // ELIMINAR UNIDAD DEL DOM
                    unidad.remove();

                    // OBTENER NUEVAS PESTAÑAS Y UNIDADES
                    const nuevasPestanas = pestanas_unidades_actualizacion.querySelectorAll(".pestana_unidad_actualizacion");

                    const nuevasUnidades = contenedor_unidades.querySelectorAll(".unidad_contenido_actualizacion");

                    // QUITAR ESTADO ACTIVO
                    nuevasPestanas.forEach(p => p.classList.remove("activa"));
                    nuevasUnidades.forEach(u => u.classList.remove("activa"));

                    // ACTIVAR LA PRIMERA UNIDAD
                    if (nuevasPestanas.length > 0) {
                        nuevasPestanas[0].classList.add("activa");
                        nuevasUnidades[0].classList.add("activa");
                    }

                    // RENOMBRAR LAS PESTAÑAS
                    nuevasPestanas.forEach(
                        (p, indice) => {
                            p.textContent = `Unidad ${indice + 1}`;
                        }
                    );
                });




                // ACTUALIZAR CONTROLES DE EVALUACIONES
                function actualizarControles() {
                    const cantidad = contenedorEvaluaciones.querySelectorAll(".evaluacion_actualizar").length;
                    botonAgregar.disabled = cantidad >= 2;
                    botonEliminar.disabled = cantidad <= 1;
                }
                actualizarControles();

                // CAMBIAR DE PESTAÑA
                pestana.addEventListener("click", () => {
                    document.querySelectorAll(".pestana_unidad_actualizacion")
                        .forEach(
                            p =>
                                p.classList.remove(
                                    "activa"
                                )
                        );


                    document.querySelectorAll(".unidad_contenido_actualizacion")
                        .forEach(
                            u => u.classList.remove(
                                "activa"
                            )
                        );

                    pestana.classList.add("activa");
                    unidad.classList.add("activa");
                });
            });
        } catch (error) {
            console.error(error);
        }
    }

    function validarPorcentajes(contenedorEvaluaciones) {
        if (!contenedorEvaluaciones) {
            return;
        }

        function actualizarPorcentajes() {
            const evaluaciones = contenedorEvaluaciones.querySelectorAll(
                ".evaluacion_actualizar"
            );

            // UNA SOLA EVALUACIÓN
            if (evaluaciones.length === 1) {
                const porcentaje = evaluaciones[0].querySelector(
                    '[name^="porcentaje_evaluacion_"]'
                );

                if (!porcentaje) {
                    return;
                }

                porcentaje.value = "25";
                porcentaje.readOnly = true;
                porcentaje.dataset.valorAnterior = "25";

                return;
            }

            // DOS EVALUACIONES
            if (evaluaciones.length === 2) {
                const porcentaje1 = evaluaciones[0].querySelector(
                    '[name^="porcentaje_evaluacion_"]'
                );

                const porcentaje2 = evaluaciones[1].querySelector(
                    '[name^="porcentaje_evaluacion_"]'
                );

                if (!porcentaje1 || !porcentaje2) {
                    return;
                }

                porcentaje1.readOnly = false;
                porcentaje2.readOnly = false;

                // DIVIDIR AUTOMÁTICAMENTE EL 25%
                porcentaje1.value = "12";
                porcentaje2.value = "13";

                porcentaje1.dataset.valorAnterior = "12";
                porcentaje2.dataset.valorAnterior = "13";

                return;
            }
        }

        // CUANDO CAMBIA UN PORCENTAJE
        contenedorEvaluaciones.addEventListener("input", function (event) {
            if (
                !event.target.matches(
                    '[name^="porcentaje_evaluacion_"]'
                )
            ) {
                return;
            }

            const evaluaciones =
                contenedorEvaluaciones.querySelectorAll(
                    ".evaluacion_actualizar"
                );

            if (evaluaciones.length !== 2) {
                return;
            }

            const porcentaje1 = evaluaciones[0].querySelector(
                '[name^="porcentaje_evaluacion_"]'
            );

            const porcentaje2 = evaluaciones[1].querySelector(
                '[name^="porcentaje_evaluacion_"]'
            );

            if (!porcentaje1 || !porcentaje2) {
                return;
            }

            const valorAnterior1 = Number(
                porcentaje1.dataset.valorAnterior || 12
            );

            const valorAnterior2 = Number(
                porcentaje2.dataset.valorAnterior || 13
            );

            event.target.value = event.target.value.replace(/\D/g, "");

            // PERMITIR BORRAR CON BACKSPACE
            if (event.target.value === "") {
                btn_actualizar.disabled = false;
                return;
            }

            const valor = Number(event.target.value);

            if (valor < 1 || valor > 24) {
                event.target.value =
                    event.target === porcentaje1
                        ? porcentaje1.dataset.valorAnterior
                        : porcentaje2.dataset.valorAnterior;

                return;
            }

            if (event.target === porcentaje1) {
                const valor2 = 25 - valor;

                if (valor2 < 1) {
                    porcentaje1.value = valorAnterior1;
                    porcentaje2.value = valorAnterior2;
                    return;
                }

                porcentaje2.value = valor2;
            }

            if (event.target === porcentaje2) {
                const valor1 = 25 - valor;

                if (valor1 < 1) {
                    porcentaje1.value = valorAnterior1;
                    porcentaje2.value = valorAnterior2;
                    return;
                }

                porcentaje1.value = valor1;
            }

            btn_actualizar.disabled = false;

            porcentaje1.dataset.valorAnterior = porcentaje1.value;
            porcentaje2.dataset.valorAnterior = porcentaje2.value;
        });

        actualizarPorcentajes();

        return actualizarPorcentajes;
    }

    // Enviar el plan de actividades
    async function coordinador_pnf(plan_estudio) {
        try {
            const formulario = new FormData();
            formulario.append("id_plan", plan_estudio);

            const response = await fetch("/notas_academicas/env_pla/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
                },
                body: formulario
            });
            const resultado = await response.json();
            console.log(resultado);

            await Swal.fire({
                text: resultado.descripcion,
                icon: resultado.icon,
                title: resultado.title,
                allowOutsideClick: false,
                allowEscapeKey: false
            });

            await obtenerPlanesActividades(perfil_seleccionado);
        } catch (error) {
            console.error(error);
        }
    }

    formulario_actualizacion.addEventListener("submit", async (e) => {
        e.preventDefault();

        try {
            const formulario = new FormData(formulario_actualizacion);

            const respuesta = await fetch("/notas_academicas/act_pl_reg/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            dialogo_actualizar_plan_estudio.close();

            await Swal.fire({
                text: resultado.descripcion,
                icon: resultado.icon,
                title: resultado.title,
                allowOutsideClick: false,
                allowEscapeKey: false
            });

            await obtenerPlanesActividades(perfil_seleccionado);
        } catch (error) {
            console.error(error);
        }
    });

    cerrar_dialogo_actualizar.addEventListener("click", () => {
        dialogo_actualizar_plan_estudio.close();
    });
});