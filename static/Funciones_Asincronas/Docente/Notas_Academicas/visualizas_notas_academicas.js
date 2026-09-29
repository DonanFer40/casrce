document.addEventListener("DOMContentLoaded", () => {

    const select_nucleo_asignado = document.getElementById("nucleo_asignado");
    const select_pnfs_asignado = document.getElementById("pnf_asignado");
    const select_materia_asignada = document.getElementById("materia_asignada");
    const select_periodo_academico = document.getElementById("periodo_academico");

    const select_trayecto_academico = document.getElementById("trayecto_academico");

    const select_fecha_registro_academico = document.getElementById("fecha_registro_academico");

    const contenedor_notas_academicas = document.getElementById("contenedor_notas_academicas");

    const contenedor_seleccion_docente = document.getElementById("contenedor_seleccion_docente");
    const select_seleccion_docente = document.getElementById("seleccion_docente");

    const select_perfiles_asignados = document.getElementById("perfiles_asignados");
    const input_perfil_asignado = document.getElementById("perfil_asignado");

    let materia = "", pnf = "", nucleo = "", periodo_academico = "", fecha_calificacion = "";
    let docente = "", trayecto = "", perfil_seleccionado = "";


    function limpiar_select(select, texto) {
        select.innerHTML = `<option value="" selected>${texto}</option>`;
        select.value = "";
    }

    function limpiar_contenido_notas() {
        contenedor_notas_academicas.innerHTML = "";
    }

    function limpiar_desde_nucleo() {
        limpiar_select(
            select_pnfs_asignado,
            "Selecciona un PNF"
        );

        limpiar_select(
            select_seleccion_docente,
            "Selecciona un Docente"
        );

        limpiar_select(
            select_trayecto_academico,
            "Selecciona un Trayecto Académico"
        );

        limpiar_select(
            select_materia_asignada,
            "Selecciona una Materia"
        );

        limpiar_select(
            select_periodo_academico,
            "Selecciona un Periodo Académico"
        );

        limpiar_select(
            select_fecha_registro_academico,
            "Selecciona una Fecha de Registro"
        );

        limpiar_contenido_notas();

        docente = "";
        pnf = "";
        trayecto = "";
        materia = "";
        periodo_academico = "";
        fecha_calificacion = "";
    }

    function limpiar_desde_pnf() {
        limpiar_select(
            select_seleccion_docente,
            "Selecciona un Docente"
        );

        limpiar_select(
            select_trayecto_academico,
            "Selecciona un Trayecto Académico"
        );

        limpiar_select(
            select_materia_asignada,
            "Selecciona una Materia"
        );

        limpiar_select(
            select_periodo_academico,
            "Selecciona un Periodo Académico"
        );

        limpiar_select(
            select_fecha_registro_academico,
            "Selecciona una Fecha de Registro"
        );

        limpiar_contenido_notas();

        docente = "";
        trayecto = "";
        materia = "";
        periodo_academico = "";
        fecha_calificacion = "";
    }

    function limpiar_desde_docente() {
        limpiar_select(
            select_trayecto_academico,
            "Selecciona un Trayecto Académico"
        );

        limpiar_select(
            select_materia_asignada,
            "Selecciona una Materia"
        );

        limpiar_select(
            select_periodo_academico,
            "Selecciona un Periodo Académico"
        );

        limpiar_select(
            select_fecha_registro_academico,
            "Selecciona una Fecha de Registro"
        );

        limpiar_contenido_notas();

        trayecto = "";
        materia = "";
        periodo_academico = "";
        fecha_calificacion = "";
    }

    function limpiar_desde_trayecto() {
        limpiar_select(
            select_materia_asignada,
            "Selecciona una Materia"
        );

        limpiar_select(
            select_periodo_academico,
            "Selecciona un Periodo Académico"
        );

        limpiar_select(
            select_fecha_registro_academico,
            "Selecciona una Fecha de Registro"
        );

        limpiar_contenido_notas();

        materia = "";
        periodo_academico = "";
        fecha_calificacion = "";
    }

    function limpiar_desde_materia() {
        limpiar_select(
            select_periodo_academico,
            "Selecciona un Periodo Académico"
        );

        limpiar_select(
            select_fecha_registro_academico,
            "Selecciona una Fecha de Registro"
        );

        limpiar_contenido_notas();

        periodo_academico = "";
        fecha_calificacion = "";
    }

    function limpiar_desde_periodo() {
        limpiar_select(
            select_fecha_registro_academico,
            "Selecciona una Fecha de Registro"
        );

        limpiar_contenido_notas();

        fecha_calificacion = "";
    }

    function limpiar_nucleos() {
        select_nucleo_asignado.innerHTML = "<option value='' selected>Selecciona un núcleo</option>";

        select_pnfs_asignado.innerHTML = "<option value='' selected>Selecciona el núcleo primero</option>";

        select_materia_asignada.innerHTML = "<option value='' selected>Selecciona el pnf primero</option>";

        select_seleccion_docente.innerHTML = "<option value='' selected>Debe seleccionar el docente</option>";

        select_periodo_academico.innerHTML = "<option value='' selected>Selecciona un periodo académico</option>";

        select_trayecto_academico.innerHTML = "<option value='' selected>Selecciona el Trayecto Académico</option>";
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

        limpiar_desde_nucleo();

        docente = "";
        nucleo = "";
        pnf = "";
        trayecto = "";
        materia = "";
        periodo_academico = "";
        fecha_calificacion = "";

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

            const respuesta = await fetch("/notas_academicas/vis_nucl_not/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            select_pnfs_asignado.innerHTML = "<option value='' selected>Selecciona el núcleo primero</option>";

            select_nucleo_asignado.innerHTML = "<option value='' selected>Selecciona un núcleo</option>";

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

        limpiar_desde_nucleo();

        if (!nucleo) {
            return;
        }

        await pnfs_asignados();

        await fecha_calificaciones_materia();

        await trayecto_academico();

        await docente_seleccionado();
    });

    async function pnfs_asignados() {
        try {
            const formulario = new FormData();
            formulario.append("nucleo_asignado", nucleo);
            formulario.append("perfil", perfil_seleccionado);

            const respuesta = await fetch("/notas_academicas/vis_pnf_not/", {
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

        limpiar_desde_pnf();

        if (!pnf) {
            return;
        }

        if (perfil_seleccionado === "CONTROL_ESTUDIO") {
            await docente_seleccionado();
        }

        if (perfil_seleccionado === "DOCENTE") {
            await trayecto_academico();
        }
    });

    async function docente_seleccionado() {
        try {
            if (!pnf || !nucleo) return;

            const formulario = new FormData();
            formulario.append("nucleo_asignado", nucleo);
            formulario.append("pnf_seleccionado", pnf);

            const respuesta = await fetch("/notas_academicas/vis_doc_not/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            select_seleccion_docente.innerHTML = "<option value='' selected>Debe seleccionar el docente</option>";

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

        limpiar_desde_docente();

        if (!docente) {
            return;
        }

        await materias_registradas();
        await trayecto_academico();
    });

    async function trayecto_academico() {
        try {
            if (!pnf || !nucleo) return;

            const formulario = new FormData();
            formulario.append("id_nucleo", nucleo);
            formulario.append("id_pnf", pnf);

            if (perfil_seleccionado === "CONTROL_ESTUDIO") {
                formulario.append("docente", docente);
            }

            formulario.append("perfil", perfil_seleccionado);
            console.log(perfil_seleccionado);

            const respuesta = await fetch("/notas_academicas/tray_not_reg/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            select_trayecto_academico.innerHTML = "<option value='' selected>Selecciona el Trayecto Académico</option>";

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

            resultado.trayectos.forEach(trayecto => {
                const option = document.createElement("option");
                option.value = trayecto.id_trayecto;
                option.textContent = trayecto.nombre;
                select_trayecto_academico.append(option);
            });
        } catch (error) {
            console.error(error);
        }
    }

    select_trayecto_academico.addEventListener("change", async () => {
        trayecto = select_trayecto_academico.value;

        limpiar_desde_trayecto();

        if (!trayecto) {
            return;
        }

        await materias_registradas();
    });

    async function materias_registradas() {
        try {
            if (!pnf || !nucleo || !trayecto) return;

            const formulario = new FormData();
            formulario.append("id_nucleo", nucleo);
            formulario.append("id_pnf", pnf);
            formulario.append("trayecto", trayecto);
            formulario.append("docente", docente);
            formulario.append("perfil", perfil_seleccionado);

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

                select_materia_asignada.append(option_materia);
            });
        } catch (error) {
            console.error(error);
        }
    }

    select_materia_asignada.addEventListener("change", async () => {
        materia = select_materia_asignada.value;

        limpiar_desde_materia();

        if (!materia) {
            return;
        }

        await periodos_academicos();
        await calificaciones_materia();
        await fecha_calificaciones_materia();
    });

    async function periodos_academicos() {
        try {
            if (!materia || !pnf || !nucleo || !trayecto) return;

            const formulario = new FormData();
            formulario.append("id_pnf", pnf);
            formulario.append("id_nucleo", nucleo);
            formulario.append("id_materia_asignada", materia);
            formulario.append("trayecto", trayecto);
            formulario.append("docente", docente);
            formulario.append("perfil", perfil_seleccionado);

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

    select_periodo_academico.addEventListener("change", async () => {
        periodo_academico = select_periodo_academico.value;

        limpiar_desde_periodo();

        if (!periodo_academico) {
            return;
        }

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
            formulario.append("trayecto", trayecto);
            formulario.append("docente", docente);
            formulario.append("perfil", perfil_seleccionado);

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

    select_fecha_registro_academico.addEventListener("change", async () => {
        fecha_calificacion = select_fecha_registro_academico.value;

        contenedor_notas_academicas.innerHTML = "";

        if (!fecha_calificacion) {
            return;
        }

        await calificaciones_materia();
    });

    async function calificaciones_materia() {
        try {
            if (!nucleo || !pnf || !materia || !periodo_academico || !fecha_calificacion || !perfil_seleccionado || !trayecto) {
                return;
            }

            const formulario = new FormData();
            formulario.append("id_nucleo", nucleo);
            formulario.append("id_pnf", pnf);
            formulario.append("id_materia_asignada", materia);
            formulario.append("id_periodo_materia", periodo_academico);
            formulario.append("fecha_calificacion", fecha_calificacion);
            formulario.append("trayecto", trayecto);
            formulario.append("docente", docente);
            formulario.append("perfil", perfil_seleccionado);

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

            const [resultadoEstudiantes, resultadoActividades] =
                await Promise.all([
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
                <th>ID</th>
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
                        ? parseInt(unidad.nota_unidad)
                        : "";

                    controles += `
                    <td class="celda-calificacion">
                        ${notaUnidad}
                    </td>
                `;
                }

                const promedio =
                    estudiante.promedio !== null &&
                        estudiante.promedio !== undefined
                        ? parseInt(estudiante.promedio)
                        : "";

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
                    ${promedio}
                </td>
            `;

                tbody.appendChild(fila);

                numeroFila++;
            });

            contenedor_notas_academicas.appendChild(tabla);

        } catch (error) {
            console.error(error);
        }
    }

});