document.addEventListener("DOMContentLoaded", () => {

    const select_pnf_asignado = document.getElementById("pnf_asignado");
    const select_seleccion_docente = document.getElementById("seleccion_docente");
    const select_trayecto_academico = document.getElementById("trayecto_academico");
    const select_materia_asignada = document.getElementById("materia_asignada");
    const input_periodo_academico = document.getElementById("periodo_academico");

    const contenedor_notas_academicas = document.getElementById("contenedor_notas_academicas");

    let pnf = "", docente = "", trayecto = "", materia = "";

    async function pnfs_asignados() {
        try {
            const respuesta = await fetch("/notas_academicas/pnfs_rem_not_acad/");
            const resultado = await respuesta.json();
            console.log(resultado);

            select_pnf_asignado.innerHTML = "<option value='' selected>Selecciona un P.N.F</option>";

            if (resultado.estado !== "exito") {
                await Swal.fire({
                    title: resultado.title,
                    text: resultado.descripcion,
                    icon: resultado.icon
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
    pnfs_asignados();

    select_pnf_asignado.addEventListener("change", async (e) => {
        pnf = select_pnf_asignado.value;

        await docente_seleccionado();

        await calificaciones_materia();
    });

    async function docente_seleccionado() {
        try {
            if (!pnf) return;

            const formulario = new FormData();
            formulario.append("pnf_seleccionado", pnf);

            const respuesta = await fetch("/notas_academicas/doc_rem_not_acad/", {
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
                    title: resultado.title,
                    text: resultado.descripcion,
                    icon: resultado.icon
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

        await trayecto_academico();

        await calificaciones_materia();

        await periodo_academico();
    });

    async function trayecto_academico() {
        try {
            if (!pnf || !docente) return;

            const formulario = new FormData();
            formulario.append("pnf_seleccionado", pnf);
            formulario.append("docente_seleccionado", docente);

            const respuesta = await fetch("/notas_academicas/tray_rem_not/", {
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
                    title: resultado.title,
                    text: resultado.descripcion,
                    icon: resultado.icon
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

        await materias_registradas();

        await calificaciones_materia();

        await periodo_academico();
    });

    async function materias_registradas() {
        try {
            if (!pnf || !trayecto || !docente) return;

            const formulario = new FormData();
            formulario.append("pnf_seleccionado", pnf);
            formulario.append("trayecto_seleccionado", trayecto);
            formulario.append("docente_seleccionado", docente);

            const respuesta = await fetch("/notas_academicas/mat_rem_not/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            select_materia_asignada.innerHTML = "<option value='' selected>Selecciona la materia</option>";

            if (resultado.estado !== "exito") {
                await Swal.fire({
                    title: resultado.title,
                    text: resultado.descripcion,
                    icon: resultado.icon
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

        await periodo_academico();

        await calificaciones_materia();

        await periodo_academico();
    });

    async function periodo_academico() {
        try {
            if (!pnf || !trayecto || !docente || !materia) return;

            const formulario = new FormData();
            formulario.append("pnf_seleccionado", pnf);
            formulario.append("materia_seleccionado", materia);
            formulario.append("trayecto_seleccionado", trayecto);
            formulario.append("docente_seleccionado", docente);

            const respuesta = await fetch("/notas_academicas/perid_rem_not/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            if (resultado.estado !== "exito") {
                await Swal.fire({
                    title: resultado.title,
                    text: resultado.descripcion,
                    icon: resultado.icon
                });
                return;
            }

            input_periodo_academico.value = resultado.datos.nombre;

            input_periodo_academico.dataset.idPeriodo = resultado.datos.id_periodo_academico;
        } catch (error) {
            console.error(error);
        }
    }

    async function calificaciones_materia() {
        try {
            if (!pnf || !materia || !trayecto || !docente) {
                return;
            }

            const idPeriodo = input_periodo_academico.dataset.idPeriodo;

            const formulario = new FormData();
            formulario.append("pnf_seleccionado", pnf);
            formulario.append("materia_seleccionado", materia);
            formulario.append("trayecto_seleccionado", trayecto);
            formulario.append("periodo_academico_seleccionado", idPeriodo);
            formulario.append("docente_seleccionado", docente);

            const respuesta = await fetch("/notas_academicas/rem_calif_mod/", {
                method: "POST",
                headers: {
                    "X-CSRFToken":
                        document.querySelector(
                            "[name=csrfmiddlewaretoken]"
                        ).value
                },
                body: formulario
            });

            const resultado = await respuesta.json();
            console.log(resultado);

            contenedor_notas_academicas.innerHTML = "";

            if (resultado.estado !== "exito") {
                contenedor_notas_academicas.innerHTML = `
                    <p>${resultado.descripcion || "No existen modificaciones de notas."}</p>
                `;
                return;
            }

            if (!resultado.datos || resultado.datos.length === 0) {
                contenedor_notas_academicas.innerHTML = `
                    <p>
                        No existen estudiantes con modificaciones
                        de notas para los criterios seleccionados.
                    </p>
                `;
                return;
            }

            const estudiantes = resultado.datos;

            const tabla = document.createElement("table");
            tabla.classList.add("tabla-calificaciones");

            tabla.innerHTML = `
                <thead>
                    <tr>
                        <th>ID Historial</th>
                        <th>Estudiante</th>
                        <th>C.I.</th>
                        <th>ID Calificación</th>
                        <th>Período Académico</th>
                        <th>Trayecto</th>
                        <th>Perfil Modificación</th>
                        <th>Usuario Modifica</th>
                        <th>C.I. Usuario</th>
                        <th>Fecha Modificación</th>
                        <th>Motivo</th>
                        <th>Tipo Modificación</th>
                        <th>Promedio</th>
                        <th>Asistencia</th>
                        <th>Condición</th>
                        <th>Revertir</th>
                    </tr>
                </thead>
                <tbody></tbody>
            `;

            const tbody = tabla.querySelector("tbody");
            estudiantes.forEach((estudiante) => {

                const fila = document.createElement("tr");
                fila.innerHTML = `
                    <td>${estudiante.id_historial ?? ""}</td>
                    <td>${estudiante.nombre_completo ?? ""}</td>
                    <td>${estudiante.cedula ?? ""}</td>
                    <td>${estudiante.id_calificaciones ?? ""}</td>
                    <td>${estudiante.periodo_academico ?? ""}</td>
                    <td>${estudiante.trayecto ?? ""}</td>
                    <td>${estudiante.perfil_modificacion ?? ""}</td>
                    <td>${estudiante.usuario_modifica ?? ""}</td>
                    <td>${estudiante.cedula_usuario_modifica ?? ""}</td>
                    <td>${estudiante.fecha_modificacion ?? ""}</td>
                    <td>${estudiante.motivo ?? ""}</td>
                    <td>${estudiante.tipo_modificacion ?? ""}</td>
                    <td>${estudiante.promedio_tramo ?? ""}</td>
                    <td>${estudiante.asistencia ?? ""}</td>
                    <td>${estudiante.condicion ?? ""}</td>
                    <td>
                        <button
                            type="button"
                            class="boton-reversion"
                            data-id-historial="${estudiante.id_historial}"
                            data-id-estudiante="${estudiante.id_estudiante}">
                            Revertir
                        </button>
                    </td>
                `;

                tbody.appendChild(fila);
            });

            contenedor_notas_academicas.appendChild(tabla);
        } catch (error) {
            console.error(error);
        }
    }

    contenedor_notas_academicas.addEventListener("click", async (e) => {
        e.preventDefault();
        try {
            const botonReversion = e.target.closest(".boton-reversion");
            if (!botonReversion) {
                return;
            }

            const idHistorial = botonReversion.dataset.idHistorial;
            if (!idHistorial) {
                console.error("No se encontró el ID del historial.");
                return;
            }

            const confirmar = await Swal.fire({
                title: "¿Revertir modificación?",
                text: (
                    "Se restaurarán las calificaciones, "
                    + "asistencia y promedio anteriores."
                ),
                icon: "warning",
                showCancelButton: true,
                confirmButtonText: "Sí, revertir",
                cancelButtonText: "Cancelar"
            });

            if (!confirmar.isConfirmed) {
                return;
            }

            const formulario = new FormData();
            formulario.append("id_historial", idHistorial);
            console.log(idHistorial)

            const respuesta = await fetch("/notas_academicas/rem_camb_not/", {
                method: "POST",
                headers: {
                    "X-CSRFToken":
                        document.querySelector(
                            "[name=csrfmiddlewaretoken]"
                        ).value
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            if (resultado.estado !== "exito") {
                await Swal.fire({
                    title: resultado.title,
                    text: resultado.descripcion,
                    icon: resultado.icon
                });
                return;
            }

            await Swal.fire({
                title: resultado.title,
                text: resultado.descripcion,
                icon: resultado.icon
            });

            contenedor_notas_academicas.innerHTML = "";
            await calificaciones_materia();
        } catch (error) {
            console.error(error);
        }
    });

});