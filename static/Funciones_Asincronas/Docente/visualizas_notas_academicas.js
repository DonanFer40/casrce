document.addEventListener("DOMContentLoaded", () => {

    const select_nucleo_asignado = document.getElementById("nucleo_asignado");
    const select_pnfs_asignado = document.getElementById("pnf_asignado");
    const select_materia_asignada = document.getElementById("materia_asignada");
    const select_periodo_academico = document.getElementById("periodo_academico");
    const input_trayecto_academico = document.getElementById("trayecto_academico");
    const select_fecha_registro_academico = document.getElementById("fecha_registro_academico");

    const contenedor_notas_academicas = document.getElementById("contenedor_notas_academicas");

    let materia = "", pnf = "", nucleo = "", periodo_academico = "", cantidad_evaluaciones = "", fecha_calificacion = "";

    function limpiar_desde_nucleo() {
        pnf = "";
        materia = "";
        periodo_academico = "";
        fecha_calificacion = "";

        select_pnfs_asignado.innerHTML =
            "<option value='' selected>Selecciona un P.N.F</option>";

        select_materia_asignada.innerHTML =
            "<option value='' selected>Selecciona la materia</option>";

        select_periodo_academico.innerHTML =
            "<option value='' selected>Selecciona un Periodo Académico</option>";

        select_fecha_registro_academico.innerHTML =
            "<option value='' selected>Selecciona una fecha</option>";

        contenedor_notas_academicas.innerHTML = "";

        cantidad_evaluaciones = 0;
    }

    function limpiar_desde_pnf() {
        materia = "";
        periodo_academico = "";
        fecha_calificacion = "";

        select_materia_asignada.innerHTML =
            "<option value='' selected>Selecciona la materia</option>";

        select_periodo_academico.innerHTML =
            "<option value='' selected>Selecciona un Periodo Académico</option>";

        select_fecha_registro_academico.innerHTML =
            "<option value='' selected>Selecciona una fecha</option>";

        contenedor_notas_academicas.innerHTML = "";

        cantidad_evaluaciones = 0;
    }

    function limpiar_desde_materia() {
        periodo_academico = "";
        fecha_calificacion = "";

        select_periodo_academico.innerHTML =
            "<option value='' selected>Selecciona un Periodo Académico</option>";

        select_fecha_registro_academico.innerHTML =
            "<option value='' selected>Selecciona una fecha</option>";

        contenedor_notas_academicas.innerHTML = "";

        cantidad_evaluaciones = 0;
    }

    function limpiar_desde_periodo() {
        fecha_calificacion = "";

        select_fecha_registro_academico.innerHTML =
            "<option value='' selected>Selecciona una fecha</option>";

        contenedor_notas_academicas.innerHTML = "";

        cantidad_evaluaciones = 0;
    }

    function limpiar_desde_fecha() {
        fecha_calificacion = "";

        contenedor_notas_academicas.innerHTML = "";

        cantidad_evaluaciones = 0;
    }

    async function nucleos_asignados() {
        try {
            const respuesta = await fetch("/notas_academicas/nucl_asig_doc/");
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
    nucleos_asignados();

    select_nucleo_asignado.addEventListener("change", async (e) => {
        limpiar_desde_nucleo();

        nucleo = select_nucleo_asignado.value;

        if (!nucleo) {
            return;
        }

        await pnfs_asignados();

        await materias_registradas();

        await periodos_academicos();

        await fecha_calificaciones_materia();
    });

    async function pnfs_asignados() {
        try {
            const formulario = new FormData();
            formulario.append("nucleo_asignado", nucleo);

            const respuesta = await fetch("/notas_academicas/pnfs_asig_doc/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            select_materia_asignada.innerHTML = "<option value='' selected>Selecciona el pnf primero</option>";

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

    select_pnfs_asignado.addEventListener("change", async (e) => {
        limpiar_desde_pnf();

        pnf = select_pnfs_asignado.value;
        if (!pnf) {
            return;
        }

        await materias_registradas();

        await calificaciones_materia();

        await periodos_academicos();

        await fecha_calificaciones_materia();
    });

    async function materias_registradas() {
        try {
            if (!pnf || !nucleo) return;

            const formulario = new FormData();
            formulario.append("id_pnf", pnf);
            formulario.append("id_nucleo", nucleo);

            const respuesta = await fetch("/notas_academicas/mat_reg_not/", {
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

            select_periodo_academico.innerHTML = "<option value='' selected>Debe seleccionar la materia</option>";

            select_materia_asignada.innerHTML = "<option value='' selected>Selecciona la materia</option>";

            resultado.materias.forEach(materia => {
                const option_materia = document.createElement("option");

                option_materia.value = materia.id_materia_asignada;
                option_materia.textContent = materia.nombre_materia;
                option_materia.dataset.trayecto = materia.trayecto_materia;

                select_materia_asignada.append(option_materia);
            });
        } catch (error) {
            console.error(error);
        }
    }

    select_materia_asignada.addEventListener("change", async () => {

        limpiar_desde_materia();

        const opcion = select_materia_asignada.selectedOptions[0];

        if (!opcion || !opcion.value) {
            return;
        }

        materia = opcion.value;

        const trayecto = opcion.dataset.trayecto;

        input_trayecto_academico.value = trayecto;

        select_periodo_academico.innerHTML = "<option value='' selected>Selecciona un Periodo Académico</option>";

        contenedor_notas_academicas.innerHTML = "";

        await periodos_academicos();

        await calificaciones_materia();

        await fecha_calificaciones_materia();
    });

    async function periodos_academicos() {
        try {
            if (!materia || !pnf || !nucleo) return;

            const formulario = new FormData();
            formulario.append("id_pnf", pnf);
            formulario.append("id_nucleo", nucleo);
            formulario.append("id_materia_asignada", materia);

            const respuesta = await fetch("/notas_academicas/perd_reg_not/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            select_periodo_academico.innerHTML = "<option value='' selected>Selecciona un Periodo Académico</option>";

            resultado.periodos.forEach(periodo => {
                const option_periodo = document.createElement("option");
                option_periodo.value = periodo.id_periodo_academico;
                option_periodo.textContent = periodo.nombre_periodo;
                select_periodo_academico.append(option_periodo);
            });
        } catch (error) {
            console.error(error);
        }
    }

    select_periodo_academico.addEventListener("change", async (e) => {
        limpiar_desde_periodo();

        periodo_academico = select_periodo_academico.value;

        if (!periodo_academico) {
            return;
        }

        select_fecha_registro_academico.innerHTML = "<option value='' selected>Selecciona un Periodo Académico</option>";

        contenedor_notas_academicas.innerHTML = "";

        await fecha_calificaciones_materia();
    });

    async function fecha_calificaciones_materia() {
        try {
            if (!materia || !pnf || !nucleo || !periodo_academico) return;

            const formulario = new FormData();
            formulario.append("id_pnf", pnf);
            formulario.append("id_nucleo", nucleo);
            formulario.append("id_materia_asignada", materia);
            formulario.append("id_periodo_academico", periodo_academico);

            const respuesta = await fetch("/notas_academicas/fech_reg_not/", {
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

            select_fecha_registro_academico.innerHTML = "<option value='' selected>Selecciona un Periodo Académico</option>";

            resultado.fechas.forEach(fecha => {
                const option_fecha = document.createElement("option");
                option_fecha.value = fecha;
                option_fecha.textContent = fecha;
                select_fecha_registro_academico.append(option_fecha);
            });
        } catch (error) {
            console.error(error);
        }
    }

    select_fecha_registro_academico.addEventListener("change", async (e) => {
        limpiar_desde_fecha();

        fecha_calificacion = select_fecha_registro_academico.value;

        if (!fecha_calificacion) {
            return;
        }

        await calificaciones_materia()
    });

    async function calificaciones_materia() {
        try {
            if (!nucleo || !pnf || !materia || !periodo_academico || !fecha_calificacion) {
                return;
            }

            const formulario = new FormData();
            formulario.append("id_nucleo", nucleo);
            formulario.append("id_pnf", pnf);
            formulario.append("id_materia_asignada", materia);
            formulario.append("id_periodo_materia", periodo_academico);
            formulario.append("fecha_calificacion", fecha_calificacion);

            const [respuestaEstudiantes, respuestaActividades] = await Promise.all([
                fetch("/notas_academicas/calf_reg_not/", {
                    method: "POST",
                    headers: {
                        "X-CSRFToken": document.querySelector(
                            "[name=csrfmiddlewaretoken]"
                        ).value
                    },
                    body: formulario
                }),

                fetch("/notas_academicas/cant_det_pla/", {
                    method: "POST",
                    headers: {
                        "X-CSRFToken": document.querySelector(
                            "[name=csrfmiddlewaretoken]"
                        ).value
                    },
                    body: formulario
                })
            ]);

            const [resultadoEstudiantes, resultadoActividades] = await Promise.all([
                respuestaEstudiantes.json(),
                respuestaActividades.json()
            ]);

            console.log("Calificaciones:", resultadoEstudiantes);
            console.log("Actividades:", resultadoActividades);

            if (resultadoEstudiantes.estado !== "exito") {
                return;
            }

            if (resultadoActividades.estado !== "exito") {
                console.error(
                    "Error al obtener actividades:",
                    resultadoActividades
                );
                return;
            }

            const cantidadActividades =
                Number(resultadoActividades.cantidad_actividades) || 0;

            cantidad_evaluaciones = cantidadActividades;

            contenedor_notas_academicas.innerHTML = "";

            const tabla = document.createElement("table");
            tabla.classList.add("tabla-calificaciones");

            let encabezado = `
            <tr>
                <th>#</th>
                <th>Estudiante</th>
                <th>C.I</th>
        `;

            for (let i = 1; i <= cantidadActividades; i++) {
                encabezado += `
                <th>Unidad ${i}</th>
            `;
            }

            encabezado += `
                <th>Asistencia</th>
                <th>Promedio</th>
            </tr>
        `;

            tabla.innerHTML = `
            <thead>
                ${encabezado}
            </thead>
            <tbody></tbody>
        `;

            const tbody = tabla.querySelector("tbody");

            const estudiantesMostrados = new Set();

            let numeroFila = 1;

            resultadoEstudiantes.calificaciones.forEach((estudiante) => {

                const idEstudiante = estudiante.id_estudiante;

                if (estudiantesMostrados.has(idEstudiante)) {
                    return;
                }

                estudiantesMostrados.add(idEstudiante);

                const fila = document.createElement("tr");

                let controles = "";

                for (let i = 1; i <= cantidadActividades; i++) {

                    const unidad = estudiante.unidades?.[i - 1];

                    const notaUnidad = unidad
                        ? unidad.nota_unidad
                        : "";

                    controles += `
                    <td class="celda-calificacion">
                        ${notaUnidad}
                    </td>
                `;
                }

                fila.innerHTML = `
                <td>
                    ${numeroFila}
                </td>

                <td>
                    ${estudiante.nombre_estudiante}
                </td>

                <td>
                    ${estudiante.cedula_identidad}
                </td>

                ${controles}

                <td class="celda-asistencia">
                    ${estudiante.asistencia}%
                </td>

                <td class="celda-promedio">
                    ${estudiante.promedio}
                </td>
            `;

                tbody.appendChild(fila);

                numeroFila++;
            });

            contenedor_notas_academicas.appendChild(tabla);

        } catch (error) {
            console.error(
                "Error al obtener las calificaciones:",
                error
            );
        }
    }
});