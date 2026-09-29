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

        await datos_academicos();
    });

    async function trayectos_academicos() {
        try {
            if (!nucleo || !pnf) return;

            const formulario = new FormData();
            formulario.append("id_nucleo", nucleo);
            formulario.append("id_pnf", pnf);

            const respuesta = await fetch("/notas_academicas/tray_est_curs/", {
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
    });

    async function materias_presentada() {
        try {
            if (!nucleo || !pnf || !trayecto) return;

            const formulario = new FormData();
            formulario.append("id_nucleo", nucleo);
            formulario.append("id_pnf", pnf);
            formulario.append("id_trayecto", trayecto);

            const respuesta = await fetch("/notas_academicas/mat_est_vist/", {
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

        await datos_academicos();
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

            const respuesta = await fetch("/notas_academicas/perid_acad_mat/", {
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

        await datos_academicos();
    });

    async function datos_academicos() {
        try {
            if (!nucleo || !pnf || !materia || !trayecto || !periodo) return;

            contenedor_datos_academicos.innerHTML = "";

            const formulario = new FormData();
            formulario.append("id_nucleo", nucleo);
            formulario.append("id_pnf", pnf);
            formulario.append("id_trayecto", trayecto);
            formulario.append("id_materia", materia);
            formulario.append("id_periodo", periodo);

            const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]").value;

            const [respuesta_planificacion, respuesta_notas] = await Promise.all([
                fetch("/notas_academicas/planif_acad_est/", {
                    method: "POST",
                    headers: {
                        "X-CSRFToken": csrfToken
                    },
                    body: formulario
                }),

                fetch("/notas_academicas/calif_est_reg/", {
                    method: "POST",
                    headers: {
                        "X-CSRFToken": csrfToken
                    },
                    body: formulario
                })
            ]);

            const [resultado_planificacion, resultado_notas] = await Promise.all([
                respuesta_planificacion.json(),
                respuesta_notas.json()
            ]);

            console.log("PLANIFICACIÓN:", resultado_planificacion);
            console.log("CALIFICACIONES:", resultado_notas);

            if (resultado_planificacion.estado === "fallo") {
                Swal.fire({
                    icon: resultado_planificacion.icon,
                    title: resultado_planificacion.title,
                    text: resultado_planificacion.descripcion
                });

                return;
            }

            if (resultado_notas.estado === "fallo") {
                Swal.fire({
                    icon: resultado_notas.icon,
                    title: resultado_notas.title,
                    text: resultado_notas.descripcion
                });

                return;
            }

            /*
            ==========================================================
            PLANIFICACIÓN ACADÉMICA
            ==========================================================
            */

            let contenido_planificacion = "";

            if (resultado_planificacion.estado === "no_exite") {

                contenido_planificacion = `
                <div class="bloque_datos_academicos">

                    <div class="titulo_datos_academicos">
                        <h3>Planificación académica</h3>
                    </div>

                    <table class="tabla_plan_estudio">
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
                            <tr>
                                <td colspan="5" class="mensaje_tabla">
                                    ${resultado_planificacion.descripcion}
                                </td>
                            </tr>
                        </tbody>
                    </table>

                </div>
            `;

            } else if (resultado_planificacion.estado === "exito") {

                let filas_planificacion = "";

                resultado_planificacion.unidades.forEach((unidad) => {

                    const evaluaciones = unidad.evaluaciones;

                    if (evaluaciones.length === 0) {

                        filas_planificacion += `
                        <tr>
                            <td>${unidad.titulo_unidad}</td>
                            <td>${unidad.ponderacion}</td>
                            <td>${unidad.contenido_unidad}</td>
                            <td colspan="2">
                                Sin evaluaciones registradas
                            </td>
                        </tr>
                    `;

                        return;
                    }

                    evaluaciones.forEach((evaluacion, indice) => {

                        filas_planificacion += `<tr>`;

                        if (indice === 0) {

                            filas_planificacion += `
                            <td rowspan="${evaluaciones.length}">
                                ${unidad.titulo_unidad}
                            </td>

                            <td rowspan="${evaluaciones.length}">
                                ${unidad.ponderacion}
                            </td>

                            <td rowspan="${evaluaciones.length}">
                                ${unidad.contenido_unidad}
                            </td>
                        `;
                        }

                        filas_planificacion += `
                        <td>
                            ${evaluacion.metodo_evaluacion}
                        </td>

                        <td>
                            ${evaluacion.fecha_evaluacion}
                        </td>
                    `;

                        filas_planificacion += `</tr>`;
                    });
                });

                contenido_planificacion = `
                <div class="bloque_datos_academicos">

                    <div class="titulo_datos_academicos">
                        <h3>Planificación académica</h3>
                    </div>

                    <table class="tabla_plan_estudio">
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
                            ${filas_planificacion}
                        </tbody>
                    </table>

                </div>
            `;
            }

            /*
            ==========================================================
            CALIFICACIONES
            ==========================================================
            */

            let contenido_calificaciones = "";

            if (resultado_notas.registradas === false) {

                contenido_calificaciones = `
                <div class="bloque_datos_academicos">

                    <div class="titulo_datos_academicos">
                        <h3>Calificaciones</h3>
                    </div>

                    <table class="tabla_notas_academicas">
                        <thead>
                            <tr>
                                <th>Unidad</th>
                                <th>Nota de la unidad</th>
                                <th>Fecha de calificación</th>
                            </tr>
                        </thead>

                        <tbody>
                            <tr>
                                <td colspan="3" class="mensaje_tabla">
                                    El estudiante todavía no tiene calificaciones registradas.
                                </td>
                            </tr>
                        </tbody>
                    </table>

                </div>
            `;

            } else if (resultado_notas.registradas === true) {

                let filas_notas = "";

                resultado_notas.evaluaciones.forEach((evaluacion) => {

                    if (!evaluacion.detalles || evaluacion.detalles.length === 0) {
                        return;
                    }

                    evaluacion.detalles.forEach((detalle) => {

                        filas_notas += `
                            <tr>
                                <td>
                                    ${detalle.titulo_unidad}
                                </td>

                                <td>
                                    ${detalle.nota_unidad}
                                </td>

                                <td>
                                    ${detalle.fecha_calificacion}
                                </td>
                            </tr>
                        `;
                    });
                });

                /*
                ==========================================================
                DATOS GENERALES DE LA CALIFICACIÓN
                ==========================================================
                */

                const calificacion = resultado_notas.evaluaciones[0];

                contenido_calificaciones = `
                    <div class="bloque_datos_academicos">

                        <div class="titulo_datos_academicos">
                            <h3>Calificaciones</h3>
                        </div>

                        <div class="resumen_notas_academicas">

                            <div class="dato_nota">
                                <span>Trayecto</span>
                                <strong>${calificacion.trayecto ?? "—"}</strong>
                            </div>

                            <div class="dato_nota">
                                <span>Promedio</span>
                                <strong>${calificacion.promedio_tramo ?? "—"}</strong>
                            </div>

                            <div class="dato_nota">
                                <span>Asistencia</span>
                                <strong>${calificacion.asistencia ?? "—"}%</strong>
                            </div>

                            <div class="dato_nota">
                                <span>Condición</span>
                                <strong>${calificacion.condicion ?? "—"}</strong>
                            </div>

                        </div>

                        <table class="tabla_notas_academicas">

                            <thead>
                                <tr>
                                    <th>Unidad</th>
                                    <th>Nota de la unidad</th>
                                    <th>Fecha de calificación</th>
                                </tr>
                            </thead>

                            <tbody>
                                ${filas_notas ||
                    `
                                    <tr>
                                        <td colspan="3" class="mensaje_tabla">
                                            No existen calificaciones por unidad registradas.
                                        </td>
                                    </tr>
                                    `
                    }
                            </tbody>

                        </table>

                    </div>
                `;
            }

            /*
            ==========================================================
            MOSTRAR TODO EN UN SOLO CONTENEDOR
            ==========================================================
            */

            contenedor_datos_academicos.innerHTML = `
            ${contenido_planificacion}

            ${contenido_calificaciones}
        `;

        } catch (error) {

            console.error(
                "Error al cargar los datos académicos:",
                error
            );

            Swal.fire({
                icon: "error",
                title: "Error",
                text: "Ocurrió un error al cargar la información académica."
            });
        }
    }

});