document.addEventListener("DOMContentLoaded", () => {

    const select_nucleo_presentar = document.getElementById("nucleo_presentar");
    const select_pnfs_cursar = document.getElementById("pnfs_cursar");
    const select_trayecto_academico = document.getElementById("trayecto_academico");
    const select_materias_presentadas = document.getElementById("materias_presentadas");
    const select_periodo_academico = document.getElementById("periodo_academico");

    const contenedor_datos_academicos = document.getElementById("contenedor_datos_academicos");

    let materia = "", pnf = "", nucleo = "", trayecto = "", periodo = "", id_materia = "";

    async function nucleos_asignados() {
        try {
            const respuesta = await fetch("/notas_academicas/nucl_est_asig/");
            const resultado = await respuesta.json();
            console.log(resultado);

            select_pnfs_cursar.innerHTML = "<option value='' selected>Selecciona el núcleo primero</option>";

            select_nucleo_presentar.innerHTML = "<option value='' selected>Selecciona un núcleo</option>";

            resultado.nucleos.forEach(nucleo => {
                const option_nucleo = document.createElement("option");
                option_nucleo.value = nucleo.id_nucleo;
                option_nucleo.textContent = nucleo.municipio;
                select_nucleo_presentar.append(option_nucleo);
            });
        } catch (error) {
            console.error(error);
        }
    }
    nucleos_asignados();

    select_nucleo_presentar.addEventListener("change", async () => {
        nucleo = select_nucleo_presentar.value;

        await pnfs_asignados();

        await trayectos_academicos();

        await planificaciones_academicas();
    });

    async function pnfs_asignados() {
        try {
            const formulario = new FormData();
            formulario.append("id_nucleo", nucleo);

            const respuesta = await fetch("/notas_academicas/pnfs_est_asig/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            select_materias_presentadas.innerHTML = "<option value='' selected>Selecciona el pnf primero</option>";

            select_pnfs_cursar.innerHTML = "<option value='' selected>Selecciona un P.N.F</option>";

            resultado.pnfs.forEach(pnf => {
                const option_pnf = document.createElement("option");
                option_pnf.value = pnf.id_pnf;
                option_pnf.textContent = pnf.pnf;
                select_pnfs_cursar.append(option_pnf);
            });
        } catch (error) {
            console.error(error);
        }
    }

    select_pnfs_cursar.addEventListener("change", async (e) => {
        pnf = select_pnfs_cursar.value;

        await trayectos_academicos();

        await materias_presentada();

        await planificaciones_academicas();
    });

    async function trayectos_academicos() {
        try {
            if (!nucleo || !pnf) return;

            const formulario = new FormData();
            formulario.append("id_nucleo", nucleo);
            formulario.append("id_pnf", pnf);

            const respuesta = await fetch("/notas_academicas/tray_est_planif/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            select_trayecto_academico.innerHTML = "<option value='' selected>Selecciona la trayecto academico</option>";

            if (resultado.estado == "fallo") {
                await Swal.fire({
                    text: resultado.descripcion,
                    icon: resultado.icon,
                    title: resultado.title,
                    allowOutsideClick: false,
                    allowEscapeKey: false
                });
                return;
            }

            resultado.trayectos.forEach(trayecto => {
                const option_trayecto = document.createElement("option");
                option_trayecto.value = trayecto.id_trayecto;
                option_trayecto.textContent = trayecto.trayecto;
                select_trayecto_academico.append(option_trayecto);
            });
        } catch (error) {
            console.error(error);
        }
    }

    select_trayecto_academico.addEventListener("change", async () => {
        trayecto = select_trayecto_academico.value;

        await materias_presentada();

        await periodo_academico();

        await planificaciones_academicas();
    });

    async function materias_presentada() {
        try {
            if (!nucleo || !pnf || !trayecto) return;

            const formulario = new FormData();
            formulario.append("id_nucleo", nucleo);
            formulario.append("id_pnf", pnf);
            formulario.append("id_trayecto", trayecto);

            const respuesta = await fetch("/notas_academicas/mat_est_planif/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            if (resultado.estado == "fallo") {
                await Swal.fire({
                    text: resultado.descripcion,
                    icon: resultado.icon,
                    title: resultado.title,
                    allowOutsideClick: false,
                    allowEscapeKey: false
                });
                return;
            }

            select_materias_presentadas.innerHTML = "<option value='' selected>Selecciona la materia</option>";

            resultado.materias.forEach(materia => {
                const option_materia = document.createElement("option");
                option_materia.value = materia.id_materia;
                option_materia.textContent = materia.nombre_materia;
                option_materia.dataset.idMateria = materia.id_materia;
                select_materias_presentadas.append(option_materia);
            });
        } catch (error) {
            console.error(error);
        }
    }

    select_materias_presentadas.addEventListener("change", async () => {
        const opcion = select_materias_presentadas.options[
            select_materias_presentadas.selectedIndex
        ];

        materia = opcion.value;
        id_materia = opcion.dataset.idMateria;

        await planificaciones_academicas();

        await periodo_academico();
    });

    async function periodo_academico() {
        try {
            if (!nucleo || !pnf || !trayecto || !materia || !id_materia) return;

            const formulario = new FormData();
            formulario.append("id_nucleo", nucleo);
            formulario.append("id_pnf", pnf);
            formulario.append("id_trayecto", trayecto);
            formulario.append("id_materia", id_materia);

            const respuesta = await fetch("/notas_academicas/per_aca_planif/", {
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

            select_periodo_academico.innerHTML = "<option value='' selected>Selecciona el periodo académico</option>";

            if (resultado.estado == "fallo") {
                await Swal.fire({
                    text: resultado.descripcion,
                    icon: resultado.icon,
                    title: resultado.title,
                    allowOutsideClick: false,
                    allowEscapeKey: false
                });

                return;
            }

            resultado.periodos.forEach(periodo => {
                const option_periodo = document.createElement("option");
                option_periodo.value = periodo.id_periodo;
                option_periodo.textContent = periodo.periodo;
                select_periodo_academico.append(option_periodo);
            });

        } catch (error) {
            console.error(error);
        }
    }

    select_periodo_academico.addEventListener("change", async () => {
        periodo = select_periodo_academico.value;

        await planificaciones_academicas();
    });

    async function planificaciones_academicas() {
        try {
            if (!nucleo || !pnf || !trayecto || !materia || !periodo) return;

            contenedor_datos_academicos.innerHTML = "";

            const formulario = new FormData();
            formulario.append("id_nucleo", nucleo);
            formulario.append("id_pnf", pnf);
            formulario.append("id_trayecto", trayecto);
            formulario.append("id_materia", materia);
            formulario.append("id_periodo", periodo);

            const csrfToken = document.querySelector(
                "[name=csrfmiddlewaretoken]"
            ).value;

            const respuesta = await fetch(
                "/notas_academicas/planif_est_vis/",
                {
                    method: "POST",
                    headers: {
                        "X-CSRFToken": csrfToken
                    },
                    body: formulario
                }
            );

            const resultado = await respuesta.json();

            console.log("PLANIFICACIONES:", resultado);

            if (resultado.estado === "fallo") {
                await Swal.fire({
                    text: resultado.descripcion,
                    icon: resultado.icon,
                    title: resultado.title,
                    allowOutsideClick: false,
                    allowEscapeKey: false
                });

                return;
            }

            if (
                resultado.estado === "no_existe" ||
                !resultado.planificaciones ||
                resultado.planificaciones.length === 0
            ) {
                contenedor_datos_academicos.innerHTML = `
                <div class="mensaje_sin_planificaciones">
                    <span>
                        ${resultado.descripcion ??
                    "No existen planificaciones académicas registradas."}
                    </span>
                </div>
            `;

                return;
            }

            resultado.planificaciones.forEach((planificacion) => {

                let filas = "";

                /*
                ==========================================================
                DETALLES DE LA PLANIFICACIÓN
                ==========================================================
                */

                if (
                    !planificacion.detalles ||
                    planificacion.detalles.length === 0
                ) {
                    filas = `
                    <tr>
                        <td colspan="5" class="mensaje_tabla">
                            No existen unidades registradas para esta
                            planificación académica.
                        </td>
                    </tr>
                `;
                } else {

                    planificacion.detalles.forEach((detalle) => {

                        const evaluaciones = detalle.evaluaciones || [];

                        /*
                        --------------------------------------------------
                        SIN EVALUACIONES
                        --------------------------------------------------
                        */

                        if (evaluaciones.length === 0) {

                            filas += `
                            <tr>
                                <td>
                                    ${detalle.titulo_unidad ?? "—"}
                                </td>

                                <td>
                                    ${detalle.ponderacion ?? "—"}
                                </td>

                                <td>
                                    ${detalle.contenido_unidad ?? "—"}
                                </td>

                                <td>
                                    Sin evaluaciones registradas
                                </td>

                                <td>
                                    —
                                </td>
                            </tr>
                        `;

                            return;
                        }

                        /*
                        --------------------------------------------------
                        CON EVALUACIONES
                        --------------------------------------------------
                        */

                        evaluaciones.forEach((evaluacion, indice) => {

                            filas += `<tr>`;

                            if (indice === 0) {

                                filas += `
                                <td rowspan="${evaluaciones.length}">
                                    ${detalle.titulo_unidad ?? "—"}
                                </td>

                                <td rowspan="${evaluaciones.length}">
                                    ${detalle.ponderacion ?? "—"}
                                </td>

                                <td rowspan="${evaluaciones.length}">
                                    ${detalle.contenido_unidad ?? "—"}
                                </td>
                            `;
                            }

                            filas += `
                            <td>
                                ${evaluacion.metodo_evaluacion ?? "—"}
                            </td>

                            <td>
                                ${evaluacion.fecha_evaluacion ?? "—"}
                            </td>
                        `;

                            filas += `</tr>`;
                        });
                    });
                }

                /*
                ==========================================================
                BLOQUE DE LA PLANIFICACIÓN
                ==========================================================
                */

                const bloque_planificacion = document.createElement("div");

                bloque_planificacion.classList.add(
                    "bloque_planificacion_academica"
                );

                bloque_planificacion.innerHTML = `
                <div class="encabezado_planificacion">

                    <div class="titulo_planificacion">
                        <h3>
                            Planificación académica
                        </h3>

                        <span>
                            ID: ${planificacion.id_planificacion}
                        </span>
                    </div>

                    <div class="datos_planificacion">

                        <div class="dato_planificacion">
                            <span>Materia</span>
                            <strong>
                                ${planificacion.materia ?? "—"}
                            </strong>
                        </div>

                        <div class="dato_planificacion">
                            <span>Código</span>
                            <strong>
                                ${planificacion.codigo_materia ?? "—"}
                            </strong>
                        </div>

                        <div class="dato_planificacion">
                            <span>Trayecto</span>
                            <strong>
                                ${planificacion.trayecto ?? "—"}
                            </strong>
                        </div>

                        <div class="dato_planificacion">
                            <span>Período académico</span>
                            <strong>
                                ${planificacion.periodo ?? "—"}
                            </strong>
                        </div>

                    </div>

                </div>

                <div class="contenedor_tabla_planificacion">

                    <table class="tabla_planificacion_academica">

                        <thead>
                            <tr>
                                <th>Unidad</th>
                                <th>Ponderación</th>
                                <th>Contenido</th>
                                <th>Método de evaluación</th>
                                <th>Fecha de evaluación</th>
                            </tr>
                        </thead>

                        <tbody>
                            ${filas}
                        </tbody>

                    </table>

                </div>

            `;

                contenedor_datos_academicos.appendChild(
                    bloque_planificacion
                );
            });

        } catch (error) {

            console.error(
                "Error al cargar las planificaciones académicas:",
                error
            );
        }
    }


});