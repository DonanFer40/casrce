document.addEventListener("DOMContentLoaded", () => {

    const formulario_actualizar = document.getElementById("formulario_actualizar");

    const select_nucleo_asignado = document.getElementById("nucleo_asignado");
    const select_pnfs_asignado = document.getElementById("pnf_asignado");
    const select_materia_asignada = document.getElementById("materia_asignada");
    const input_trayecto_academico = document.getElementById("trayecto_academico");

    const contenedor_notas_academicas = document.getElementById("contenedor_evaluaciones");

    let materia = "", pnf = "", nucleo = "", id_trayecto = "";

    function obtener_csrf_token() {
        const cookie = document.cookie.split("; ").find(row => row.startsWith("csrftoken="));

        return cookie ? decodeURIComponent(cookie.split("=")[1]) : "";
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

        await materias_asignadas();

        await estudiantes_reparacion_modificar();
    });

    async function pnfs_asignados() {
        try {
            const formulario = new FormData();
            formulario.append("nucleo_asignado", nucleo);

            const respuesta = await fetch("/notas_academicas/pnfs_asig_doc/", {
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

        await materias_asignadas();

        await estudiantes_reparacion_modificar();
    });

    async function materias_asignadas() {
        try {
            if (!pnf || !nucleo) return;

            const formulario = new FormData();
            formulario.append("id_nucleo", nucleo);
            formulario.append("id_pnf", pnf);

            const respuesta = await fetch("/notas_academicas/mod_mat_rep_reg/", {
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

        id_trayecto = opcion.dataset.id_trayecto;

        input_trayecto_academico.value = trayecto;

        await estudiantes_reparacion_modificar();
    });

    async function estudiantes_reparacion_modificar() {
        try {
            if (!nucleo || !pnf || !materia || !id_trayecto) return;

            const formulario = new FormData();
            formulario.append("id_nucleo", nucleo);
            formulario.append("id_pnf", pnf);
            formulario.append("id_materia_asignacion", materia);
            formulario.append("id_trayecto", id_trayecto);

            const respuesta = await fetch("/notas_academicas/mod_not_rep_reg/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": obtener_csrf_token()
                },
                body: formulario
            });

            const resultado = await respuesta.json();
            console.log(resultado);

            if (resultado.estado !== "exito") {
                contenedor_notas_academicas.innerHTML = `
            <div class="alert alert-warning text-center" role="alert">
                ${resultado.descripcion || "No se pudieron obtener los datos."}
            </div>`;
                return;
            }

            if (resultado.estudiantes.length === 0) {
                contenedor_notas_academicas.innerHTML = `
            <div class="alert alert-info text-center" role="alert">
                No existen estudiantes registrados en reparación para esta materia.
            </div>`;
                return;
            }

            let htmlTabla = `
                <form id="form_guardar_modificacion_rep">
                    <div class="table-responsive mt-3">
                        <table class="table table-striped table-hover align-middle">
                            <thead class="table-dark">
                                <tr>
                                    <th>#</th>
                                    <th>Cédula</th>
                                    <th>Estudiante</th>
                                    <th class="text-center">Fecha Registro</th>
                                    <th class="text-center" style="width: 160px;">Nota Reparación</th>
                                    <th class="text-center">Estado</th>
                                </tr>
                            </thead>
                            <tbody>`;

            resultado.estudiantes.forEach((est, index) => {
                const esAprobado = est.calificacion >= 10;
                const badgeClase = esAprobado ? "bg-success" : "bg-danger";
                // Formatear nota a entero limpio para compatibilidad con las reglas de entrada
                const notaEntera = Math.round(est.calificacion);

                htmlTabla += `
                    <tr>
                        <td>${index + 1}</td>
                        <td>${est.cedula}</td>
                        <td>${est.nombre_completo}</td>
                        <td class="text-center">${est.fecha_reparacion}</td>
                        <td class="text-center">
                            <input type="text" 
                                class="form-control text-center input-nota-reparacion mx-auto" 
                                style="max-width: 80px;"
                                data-id-reparacion="${est.id_reparacion}"
                                data-id-estudiante="${est.id_estudiante}"
                                value="${notaEntera}" 
                                maxlength="2"
                                autocomplete="off"
                                required>
                        </td>
                        <td class="text-center">
                            <span class="badge ${badgeClase}">${est.estado_reparacion}</span>
                        </td>
                    </tr>`;
            });

            htmlTabla += `
                        </tbody>
                    </table>
                </div>
            </form>`;

            contenedor_notas_academicas.innerHTML = htmlTabla;
        } catch (error) {
            console.error(error);
        }
    }

    // Validación en tiempo real sobre la entrada
    contenedor_notas_academicas.addEventListener("input", (e) => {
        if (e.target.classList.contains("input-nota-reparacion")) {
            let input = e.target;
            let valor = input.value.replace(/[^\d]/g, "");

            if (valor.length > 2) {
                valor = valor.slice(0, 2);
            }

            if (valor !== "" && parseInt(valor, 10) > 20) {
                valor = "20";
            }

            input.value = valor;
        }
    });

    // Limpieza de ceros a la izquierda al perder el foco
    contenedor_notas_academicas.addEventListener("focusout", (e) => {
        if (e.target.classList.contains("input-nota-reparacion")) {
            let input = e.target;
            if (input.value !== "") {
                input.value = parseInt(input.value, 10).toString();
            }
        }
    });

    formulario_actualizar.addEventListener("submit", async (e) => {
        e.preventDefault();
        try {
            const formulario = new FormData(formulario_actualizar);

            // 1. Agregar id_trayecto desde el dataset
            const idTrayecto = input_trayecto_academico?.dataset?.id_trayecto || "";
            formulario.append("id_trayecto", idTrayecto);

            // 2. Extraer las notas e incluir id_reparacion
            const inputsNotas = contenedor_notas_academicas.querySelectorAll(".input-nota-reparacion");
            const listaNotas = [];
            let hayCamposVacios = false;

            inputsNotas.forEach(input => {
                const notaVal = input.value.trim();

                if (notaVal === "") {
                    hayCamposVacios = true;
                    input.classList.add("is-invalid");
                } else {
                    input.classList.remove("is-invalid");
                    listaNotas.push({
                        id_reparacion: input.dataset.idReparacion, // Requerido por el backend
                        id_estudiante: input.dataset.idEstudiante,
                        calificacion: parseInt(notaVal, 10)         // Cambiado de "nota" a "calificacion"
                    });
                }
            });

            // Validar que no existan campos sin nota antes de procesar
            if (hayCamposVacios || listaNotas.length === 0) {
                Swal.fire({
                    title: "Atención",
                    text: "Debe ingresar una nota válida para todos los estudiantes.",
                    icon: "warning"
                });
                return;
            }

            // 3. Serializar con la clave "notas" que espera Django (request.POST.get("notas"))
            formulario.append("notas", JSON.stringify(listaNotas));

            const respuesta = await fetch("/notas_academicas/mod_rep_reg/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": obtener_csrf_token()
                },
                body: formulario
            });

            const resultado = await respuesta.json();

            await Swal.fire({
                text: resultado.descripcion,
                icon: resultado.icon,
                title: resultado.title,
                allowOutsideClick: false,
                allowEscapeKey: false
            });

            if (resultado.estado === "exito") {
                contenedor_notas_academicas.innerHTML = "";
            }
        } catch (error) {
            console.error(error);
        }
    });
});