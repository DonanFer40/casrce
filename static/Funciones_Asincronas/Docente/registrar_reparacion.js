document.addEventListener("DOMContentLoaded", () => {

    const select_nucleo_asignado = document.getElementById("nucleo_asignado");
    const select_pnfs_asignado = document.getElementById("pnf_asignado");
    const select_materia_asignada = document.getElementById("materia_asignada");
    const input_trayecto_academico = document.getElementById("trayecto_academico");

    const formulario_registrar = document.getElementById("formulario_registrar");

    const contenedor_evaluaciones = document.getElementById("contenedor_evaluaciones");

    let materia = "", pnf = "", nucleo = "";

    function obtener_csrf_token() {

        const cookie = document.cookie
            .split("; ")
            .find(row => row.startsWith("csrftoken="));

        return cookie
            ? decodeURIComponent(cookie.split("=")[1])
            : "";
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
        nucleo = select_nucleo_asignado.value;

        await pnfs_asignados();

        await evaluacion_reparacion();

        await estudiantes_reparacion();
    });

    async function pnfs_asignados() {
        try {
            if (!nucleo) return;

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
        pnf = select_pnfs_asignado.value;

        await evaluacion_reparacion();

        await estudiantes_reparacion();
    });

    async function evaluacion_reparacion() {
        try {
            if (!nucleo || !pnf) return;

            const formulario = new FormData();
            formulario.append("id_nucleo", nucleo);
            formulario.append("id_pnf", pnf);

            const respuesta = await fetch("/notas_academicas/eval_mat_rep/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            select_materia_asignada.innerHTML = "<option value='' selected>Selecciona la materia</option>";

            resultado.evaluaciones.forEach(materia => {
                const option_materia = document.createElement("option");
                option_materia.value = materia.id_materia_asignada;
                option_materia.textContent = materia.materia;
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

        await estudiantes_reparacion();
    });

    async function estudiantes_reparacion() {
        try {
            const id_trayecto = input_trayecto_academico?.dataset?.id_trayecto;

            if (!nucleo || !pnf || !materia || !id_trayecto) {
                return;
            }

            const formulario = new FormData();
            formulario.append("id_nucleo", nucleo);
            formulario.append("id_pnf", pnf);
            formulario.append("id_materia_asignacion", materia);
            formulario.append("id_trayecto", id_trayecto);

            const respuesta = await fetch("/notas_academicas/est_rep_not/", {
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

            contenedor_evaluaciones.innerHTML = "";

            if (resultado.mensaje && resultado.estudiantes.length === 0) {
                contenedor_evaluaciones.innerHTML = `
                    <div class="alert alert-info text-center">
                        ${resultado.mensaje}
                    </div>
                `;
                return;
            }

            // Validación segura
            if (!Array.isArray(resultado.estudiantes) || resultado.estudiantes.length === 0) {
                contenedor_evaluaciones.innerHTML = `
                    <div class="alert alert-info text-center">
                        No existen estudiantes reprobados aptos para reparación en esta materia.
                    </div>
                `;
                return;
            }

            if (resultado.estado !== "exito") {
                contenedor_evaluaciones.innerHTML = `
                    <div class="alert alert-warning text-center">
                        ${resultado.descripcion}
                    </div>
                `;
                return;
            }

            if (resultado.mensaje && resultado.estudiantes.length === 0) {
                contenedor_evaluaciones.innerHTML = `
                    <div class="alert alert-info text-center">
                        ${resultado.mensaje}
                    </div>
                `;
                return;
            }

            if (!resultado.estudiantes || resultado.estudiantes.length === 0) {
                contenedor_evaluaciones.innerHTML = `
                    <div class="alert alert-info text-center">
                        No existen estudiantes reprobados aptos para reparación en esta materia.
                    </div>
                `;
                return;
            }

            let htmlTabla = `
                <div class="table-responsive mt-3">
                    <table class="table table-striped table-hover align-middle">
                        <thead class="table-dark">
                            <tr>
                                <th>#</th>
                                <th>Cédula</th>
                                <th>Estudiante</th>
                                <th class="text-center">
                                    % Asistencia
                                </th>
                                <th class="text-center">
                                    Promedio final
                                </th>
                                <th class="text-center">
                                    Nota Reparación
                                </th>
                            </tr>
                        </thead>
                        <tbody>

                `;
            resultado.estudiantes.forEach((est, index) => {
                htmlTabla += `
                <tr>
                    <td>
                        ${index + 1}
                    </td>
                    <td>
                        ${est.cedula}
                    </td>
                    <td>
                        ${est.nombre_completo}
                    </td>
                    <td class="text-center">
                        ${est.asistencia}%
                    </td>
                    <td class="text-center">
                        <span class="badge bg-danger">${est.promedio_final}</span>
                    </td>
                    <td class="text-center">
                        <input 
                            type="text"
                            class="form-control form-control-sm text-center input-nota-reparacion"
                            data-id-estudiante="${est.id_estudiante}"
                            data-id-promedio="${est.id_promedio_final}"
                            data-id-trayecto="${est.id_trayecto}"
                            min="0"
                            max="20"
                            step="0.1"
                            placeholder="0.0">
                    </td>
                </tr>
            `;
            });

            htmlTabla += `
                        </tbody>
                    </table>
                </div>
            `;
            contenedor_evaluaciones.innerHTML = htmlTabla;
        } catch (error) {
            console.error(error);
        }
    }

    contenedor_evaluaciones.addEventListener("input", (e) => {
        if (e.target.classList.contains("input-nota-reparacion")) {
            let input = e.target;

            // 1. Eliminar cualquier carácter que NO sea un dígito
            let valor = input.value.replace(/[^\d]/g, "");

            // 2. Limitar a máximo 2 dígitos
            if (valor.length > 2) {
                valor = valor.slice(0, 2);
            }

            // 3. Validar que no supere el límite máximo de 20
            if (valor !== "" && parseInt(valor, 10) > 20) {
                valor = "20";
            }

            // Asignar el valor limpio al campo
            input.value = valor;
        }
    });

    // Listener opcional para formatear ceros a la izquierda al perder el foco (blur)
    contenedor_evaluaciones.addEventListener("focusout", (e) => {
        if (e.target.classList.contains("input-nota-reparacion")) {
            let input = e.target;
            if (input.value !== "") {
                // Convierte valores como "05" a "5"
                input.value = parseInt(input.value, 10).toString();
            }
        }
    });

    formulario_registrar.addEventListener("submit", async (e) => {
        e.preventDefault();

        try {
            const formulario = new FormData(formulario_registrar);

            const listaNotas = [];
            const inputsNotas = contenedor_evaluaciones.querySelectorAll(".input-nota-reparacion");

            inputsNotas.forEach(input => {
                const nota = input.value.trim();
                if (nota !== "") {
                    listaNotas.push({
                        id_estudiante: input.dataset.idEstudiante,
                        nota: parseFloat(nota)
                    });
                }
            });

            if (listaNotas.length === 0) {
                Swal.fire({
                    title: "Atención",
                    text: "Debe ingresar al menos una nota de reparación.",
                    icon: "warning"
                });
                return;
            }
            formulario.append("notas_reparacion", JSON.stringify(listaNotas));

            const respuesta = await fetch("/notas_academicas/reg_rep_not/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": obtener_csrf_token()
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            await Swal.fire({
                title: resultado.title,
                text: resultado.descripcion,
                icon: resultado.icon,
                allowOutsideClick: false,
                allowEscapeKey: false
            });

            if (resultado.estado === "exito") {
                formulario_registrar.reset();
                contenedor_evaluaciones.innerHTML = "";
                select_materia_asignada.innerHTML = "<option value='' selected>Selecciona la materia</option>";
            }

        } catch (error) {
            console.error(error);
        }
    });

});