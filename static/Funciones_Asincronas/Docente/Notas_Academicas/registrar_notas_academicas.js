document.addEventListener("DOMContentLoaded", () => {

    const formulario_registrar = document.getElementById("formulario_registrar");

    const select_nucleo_asignado = document.getElementById("nucleo_asignado");
    const select_pnfs_asignado = document.getElementById("pnf_asignado");
    const select_materia_asignada = document.getElementById("materia_asignada");
    const input_periodo_academico = document.getElementById("periodo_academico");
    const select_trayecto_academico = document.getElementById("trayecto_academico");

    const contenedor_seleccion_docente = document.getElementById("contenedor_seleccion_docente");
    const select_seleccion_docente = document.getElementById("seleccion_docente");

    const select_perfiles_asignados = document.getElementById("perfiles_asignados");
    const input_perfil_asignado = document.getElementById("perfil_asignado");

    const contenedor_notas_academicas = document.getElementById("contenedor_notas_academicas");

    let materia = "", pnf = "", nucleo = "", cantidad_evaluaciones = "", docente = "", trayecto = "";
    let perfil_seleccionado = "";

    function obtener_csrf_token() {

        const cookie = document.cookie
            .split("; ")
            .find(row => row.startsWith("csrftoken="));

        return cookie
            ? decodeURIComponent(cookie.split("=")[1])
            : "";
    }

    function limpiar_nucleos() {
        select_nucleo_asignado.innerHTML = "<option value='' selected>Selecciona un núcleo</option>";

        select_pnfs_asignado.innerHTML = "<option value='' selected>Selecciona el núcleo primero</option>";

        select_materia_asignada.innerHTML = "<option value='' selected>Selecciona el pnf primero</option>";

        select_seleccion_docente.innerHTML = "<option value='' selected>Debe seleccionar el docente</option>";

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

            const respuesta = await fetch("/notas_academicas/nucl_reg_not/", {
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

        await pnfs_asignados();

        await calificaciones_materia();

        if (perfil_seleccionado === "DOCENTE") {
            await trayecto_academico();
        }
    });

    async function pnfs_asignados() {
        try {
            const formulario = new FormData();
            formulario.append("nucleo_asignado", nucleo);
            formulario.append("perfil", perfil_seleccionado);

            const respuesta = await fetch("/notas_academicas/pnf_reg_not/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": obtener_csrf_token()
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

        await materias_asignadas();

        await calificaciones_materia();

        if (perfil_seleccionado === "CONTROL_ESTUDIO") {
            await docente_seleccionado();
        } else if (perfil_seleccionado === "DOCENTE") {
            await trayecto_academico();
        }
    });

    async function docente_seleccionado() {
        try {
            if (!pnf || !nucleo) return;

            const formulario = new FormData();
            formulario.append("nucleo_asignado", nucleo);
            formulario.append("pnf_seleccionado", pnf);

            const respuesta = await fetch("/notas_academicas/doc_reg_not/", {
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

        await trayecto_academico();
    });

    async function trayecto_academico() {
        try {
            if (!pnf || !nucleo) return;

            if (perfil_seleccionado === "CONTROL_ESTUDIO" && !docente) return;

            const formulario = new FormData();
            formulario.append("id_nucleo", nucleo);
            formulario.append("id_pnf", pnf);

            if (perfil_seleccionado === "CONTROL_ESTUDIO") {
                formulario.append("docente", docente);
            }

            formulario.append("perfil", perfil_seleccionado);
            console.log(perfil_seleccionado);

            const respuesta = await fetch("/notas_academicas/tray_mat_asig/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": obtener_csrf_token()
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

        await materias_asignadas();
    });

    async function materias_asignadas() {
        try {
            if (!pnf || !nucleo || !trayecto) return;

            const formulario = new FormData();
            formulario.append("id_nucleo", nucleo);
            formulario.append("id_pnf", pnf);
            formulario.append("trayecto", trayecto);
            formulario.append("docente", docente);
            formulario.append("perfil", perfil_seleccionado);

            const respuesta = await fetch("/notas_academicas/mat_not_acad/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": obtener_csrf_token()
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            select_materia_asignada.innerHTML = "<option value='' selected>Selecciona la materia</option>";

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

            resultado.materias.forEach(materia => {
                const option_materia = document.createElement("option");
                option_materia.value = materia.id_materia_asignada;
                option_materia.textContent = materia.nombre;
                select_materia_asignada.append(option_materia);
            });

        } catch (error) {
            console.error(error);
        }
    }

    select_materia_asignada.addEventListener("change", async () => {
        materia = select_materia_asignada.value;

        await periodos_academicos();

        await calificaciones_materia();
    });

    async function periodos_academicos() {
        try {
            if (!pnf || !nucleo || !materia) return;

            const formulario = new FormData();
            formulario.append("id_nucleo", nucleo);
            formulario.append("id_pnf", pnf);
            formulario.append("id_materia_asignada", materia);

            const respuesta = await fetch("/notas_academicas/per_not_acad/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": obtener_csrf_token()
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            if (resultado.estado !== "exito") {
                input_periodo_academico.value = "";
                delete input_periodo_academico.dataset.idPeriodoAcademico;

                await Swal.fire({
                    text: resultado.descripcion,
                    icon: resultado.icon,
                    title: resultado.title,
                    allowOutsideClick: false,
                    allowEscapeKey: false
                });
                return;
            }

            input_periodo_academico.value = resultado.datos.nombre;

            input_periodo_academico.dataset.idPeriodoAcademico = resultado.datos.id_periodo_academico;
        } catch (error) {
            console.error(error);
        }
    }

    async function calificaciones_materia() {
        try {
            if (!nucleo || !pnf || !materia || !perfil_seleccionado || !trayecto) return;
            const idPeriodoAcademico = input_periodo_academico.dataset.idPeriodoAcademico;
            const formulario = new FormData();
            formulario.append("id_nucleo", nucleo);
            formulario.append("id_pnf", pnf);
            formulario.append("id_materia_asignada", materia);
            formulario.append("id_periodo_materia", idPeriodoAcademico);
            formulario.append("trayecto", trayecto);
            formulario.append("docente", docente);
            formulario.append("perfil", perfil_seleccionado);

            const [respuestaEstudiantes, respuestaActividades] = await Promise.all([
                fetch("/notas_academicas/est_not_acad/", {
                    method: "POST",
                    headers: {
                        "X-CSRFToken": obtener_csrf_token()
                    },
                    body: formulario
                }),

                fetch("/notas_academicas/cant_det_pla/", {
                    method: "POST",
                    headers: {
                        "X-CSRFToken": obtener_csrf_token()
                    },
                    body: formulario
                })
            ]);

            const [resultadoEstudiantes, resultadoActividades] = await Promise.all([
                respuestaEstudiantes.json(),
                respuestaActividades.json()
            ]);

            console.log("Estudiante", resultadoEstudiantes);
            console.log("Actividad", resultadoActividades);

            if (resultadoEstudiantes.estado === "fallo") {
                contenedor_notas_academicas.innerHTML = `
                    <p>No fue posible obtener los estudiantes.</p>
                `;
                return;
            }

            if (resultadoActividades.estado === "fallo") {
                contenedor_notas_academicas.innerHTML = `
                    <p>No fue posible obtener las actividades de la materia.</p>
                `;
                return;
            }

            contenedor_notas_academicas.innerHTML = "";

            if (!resultadoEstudiantes.estudiantes || resultadoEstudiantes.estudiantes.length === 0) {
                contenedor_notas_academicas.innerHTML = `
                    <p>No hay estudiantes registrados para esta materia.</p>
                `;
                return;
            }

            cantidad_evaluaciones = Number(resultadoActividades.cantidad_actividades || 0);

            if (cantidad_evaluaciones <= 0) {
                contenedor_notas_academicas.innerHTML = `
                    <p>No hay actividades académicas registradas para esta materia.</p>
                `;
                return;
            }

            const tabla = document.createElement("table");
            tabla.classList.add("tabla-calificaciones");

            let encabezado = `
                <tr>
                    <th>#</th>
                    <th>Estudiante</th>
                    <th>C.I</th>
            `;

            for (let i = 1; i <= cantidad_evaluaciones; i++) {
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
            resultadoEstudiantes.estudiantes.forEach((estudiante, indice) => {
                const fila = document.createElement("tr");

                let controles = "";

                for (let i = 1; i <= cantidad_evaluaciones; i++) {
                    controles += `
                        <td>
                            <input
                                type="text"
                                class="input-calificacion"
                                name="calificacion_${estudiante.id_estudiante}_${i}"
                                data-id-estudiante="${estudiante.id_estudiante}"
                                data-actividad="${i}"
                                min="0"
                                max="20"
                                maxlength="5"
                                autocomplete="off"
                                step="0.01"
                                placeholder="0 - 20">
                        </td>
                    `;
                }

                fila.innerHTML = `
                    <td>${indice + 1}</td>
                    <td>${estudiante.nombre_completo}</td>
                    <td>${estudiante.cedula}</td>
                    ${controles}
                    <td class="celda-asistencia">
                        <input
                            type="text"
                            class="input-asistencia"
                            name="asistencia_${estudiante.id_estudiante}"
                            data-id-estudiante="${estudiante.id_estudiante}"
                            min="0"
                            max="100"
                            maxlength="3"
                            autocomplete="off"
                            step="1"
                            placeholder="%">
                    </td>
                    <td class="celda-promedio">
                        <input
                            type="text"
                            class="input-promedio"
                            name="promedio_${estudiante.id_estudiante}"
                            data-id-estudiante="${estudiante.id_estudiante}"
                            readonly>
                    </td>
                `;
                tbody.appendChild(fila);
            });

            contenedor_notas_academicas.appendChild(tabla);

        } catch (error) {
            console.error(error);

            contenedor_notas_academicas.innerHTML = `
                <p>Ocurrió un error al cargar las calificaciones.</p>
            `;
        }
    }

    contenedor_notas_academicas.addEventListener("input", function (e) {
        const input = e.target;

        // INPUTS CALIFICACIONES
        if (input.classList.contains("input-calificacion")) {

            input.value = input.value.replace(/[^0-9]/g, "");

            // Eliminar ceros al inicio
            if (input.value !== "") {
                input.value = input.value.replace(/^0+/, "");

                // Si solamente eran ceros, dejar un único 0
                if (input.value === "") {
                    input.value = "0";
                }
            }

            // Máximo 20
            if (input.value !== "") {
                const valor = parseInt(input.value, 10);

                if (valor > 20) {
                    input.value = "20";
                }
            }
        }

        // CALCULAR PROMEDIO DEL ESTUDIANTE
        const idEstudiante = input.dataset.idEstudiante;

        const calificaciones = contenedor_notas_academicas.querySelectorAll(
            `.input-calificacion[data-id-estudiante="${idEstudiante}"]`
        );

        let suma = 0;
        let cantidad = 0;

        calificaciones.forEach(calificacion => {
            if (calificacion.value !== "") {
                const valor = parseFloat(calificacion.value);

                if (!isNaN(valor)) {
                    suma += valor;
                    cantidad++;
                }
            }
        });

        const promedio = cantidad > 0 ? Math.round(suma / cantidad) : 0;

        const inputPromedio = contenedor_notas_academicas.querySelector(
            `.input-promedio[data-id-estudiante="${idEstudiante}"]`
        );

        if (inputPromedio) {
            inputPromedio.value = cantidad > 0 ? promedio : "";
        }

        // ASISTENCIA
        if (input.classList.contains("input-asistencia")) {

            input.value = input.value.replace(/[^0-9]/g, "");

            // Eliminar ceros al inicio
            if (input.value !== "") {
                input.value = input.value.replace(/^0+/, "");

                // Si solamente eran ceros, dejar un único 0
                if (input.value === "") {
                    input.value = "0";
                }
            }

            // Máximo 100
            if (input.value !== "") {
                const valor = parseInt(input.value, 10);

                if (valor > 100) {
                    input.value = "100";
                }
            }
        }
    });

    formulario_registrar.addEventListener("submit", async (e) => {
        e.preventDefault();
        try {
            const formulario = new FormData(formulario_registrar);
            const idPeriodoAcademico = input_periodo_academico.dataset.idPeriodoAcademico;
            formulario.append("periodo_academico", idPeriodoAcademico);
            formulario.append("cantidad_evaluaciones", cantidad_evaluaciones);
            formulario.append("perfil", perfil_seleccionado);

            const respuesta = await fetch("/notas_academicas/reg_nota_acad/", {
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
                formulario_registrar.reset();
                contenedor_notas_academicas.innerHTML = "";
                materia = "";
                pnf = "";
                nucleo = "";
                cantidad_evaluaciones = "";
                docente = "";
                trayecto = "";
                perfil_seleccionado = "";
                limpiar_nucleos();

            }
        } catch (error) {
            console.error(error);
        }
    });

});