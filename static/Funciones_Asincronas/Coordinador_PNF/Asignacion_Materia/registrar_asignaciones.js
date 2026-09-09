document.addEventListener("DOMContentLoaded", function () {

    const formulario_registrar = document.getElementById("formulario_asignar_materia");
    const select_docentes_registrados = document.getElementById("docentes_registrados");
    const select_rol_docente = document.getElementById("rol_docente");
    const select_nucleos_asignados = document.getElementById("nucleos_asignados");
    const select_pnfs_asignados = document.getElementById("pnfs_asignados");
    const contenedor_materias = document.getElementById("contenedor_materias");

    let pnf = "", nucleo = "", docente = "", rol_docente = "";

    async function obtener_nucleos_asignados() {
        try {
            const respuesta = await fetch("/obt_nucleos_asignados/");
            const resultado = await respuesta.json();
            console.log(resultado)

            select_nucleos_asignados.innerHTML = '<option value="">Selecciona un Núcleo.</option>';

            resultado.nucleos.forEach(nucleo => {
                const opcion = document.createElement("option");
                opcion.value = nucleo.id_nucleo;
                opcion.textContent = nucleo.municipio;
                select_nucleos_asignados.appendChild(opcion);
            });
        } catch (error) {
            console.error(error);
        }
    }
    obtener_nucleos_asignados();

    select_nucleos_asignados.addEventListener("change", async () => {
        nucleo = select_nucleos_asignados.value;

        await obtener_pnfs_asignados();

        await obtener_docentes_registrados();

        await obtener_materias_registradas();
    });

    async function obtener_pnfs_asignados() {
        try {
            const formulario = new FormData();
            formulario.append("nucleo_asignado", nucleo);

            const respuesta = await fetch("/obt_pnfs_asignado/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado)

            select_pnfs_asignados.innerHTML = '<option value="">Selecciona un P.N.F.</option>';

            resultado.pnfs.forEach(pnf => {
                const opcion = document.createElement("option");
                opcion.value = pnf.id_pnf;
                opcion.textContent = pnf.pnf;
                select_pnfs_asignados.appendChild(opcion);
            });
        } catch (error) {
            console.error(error);
        }
    }

    select_pnfs_asignados.addEventListener("change", async () => {
        pnf = select_pnfs_asignados.value;

        await obtener_docentes_registrados();

        await obtener_materias_registradas();
    });

    async function obtener_docentes_registrados() {
        try {
            if (!pnf || !nucleo) return;

            const formulario = new FormData();
            formulario.append("nucleo_asignado", nucleo);
            formulario.append("pnf_asignado", pnf);

            const respuesta = await fetch("/docs_reg/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado)

            select_docentes_registrados.innerHTML = '<option value="">Selecciona un docente.</option>';

            resultado.usuarios.forEach(usuario => {
                const opcion = document.createElement("option");
                opcion.value = usuario.id_usuario;
                opcion.textContent = usuario.nombre;
                select_docentes_registrados.appendChild(opcion);
            });
        } catch (error) {
            console.error(error);
        }
    }

    select_docentes_registrados.addEventListener("change", async () => {
        docente = select_docentes_registrados.value;
        await obtener_materias_registradas();
    });

    select_rol_docente.addEventListener("change", async () => {
        rol_docente = select_rol_docente.value;
        await obtener_materias_registradas();
    });

    async function obtener_materias_registradas() {
        try {
            if (!pnf || !nucleo || !docente || !rol_docente) return;

            const formulario = new FormData();
            formulario.append("nucleo_asignado", nucleo);
            formulario.append("pnf_asignado", pnf);
            formulario.append("docente_seleccionado", docente);
            formulario.append("rol_docente", rol_docente);

            const respuesta = await fetch("/mats_reg/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
                },
                body: formulario
            });

            const resultado = await respuesta.json();

            contenedor_materias.innerHTML = "";

            if (resultado.estado !== "exito") {
                contenedor_materias.innerHTML = `
                <p>${resultado.descripcion || "No se pudieron cargar las materias."}</p>
            `;
                return;
            }

            const materias = Array.isArray(resultado.materias)
                ? resultado.materias
                : [];

            if (materias.length === 0) {
                contenedor_materias.innerHTML = `
                <p>No hay materias registradas.</p>
            `;
                return;
            }

            const materiasPorTrayecto = {};

            materias.forEach(materia => {
                const trayecto = String(
                    materia.trayecto ?? "Sin trayecto"
                );

                if (!materiasPorTrayecto[trayecto]) {
                    materiasPorTrayecto[trayecto] = [];
                }

                materiasPorTrayecto[trayecto].push(materia);
            });

            Object.entries(materiasPorTrayecto).forEach(
                ([trayecto, listaMaterias]) => {

                    const titulo = document.createElement("h4");
                    titulo.textContent = trayecto;
                    contenedor_materias.appendChild(titulo);

                    const tabla = document.createElement("table");
                    tabla.classList.add("tabla-materias");

                    tabla.innerHTML = `
                    <thead>
                        <tr>
                            <th style="width:60px; text-align:center;">
                                Asignar
                            </th>
                            <th>Materia</th>
                            <th style="width:160px; text-align:center;">
                                Estado
                            </th>
                        </tr>
                    </thead>
                    <tbody></tbody>
                `;

                    const tbody = tabla.querySelector("tbody");

                    listaMaterias.forEach(materia => {

                        const fila = document.createElement("tr");

                        const estados = {
                            VERDE: "Disponible",
                            AMARILLO: "Rol ocupado",
                            NARANJA: "Un rol disponible",
                            ROJO: "Ocupada",
                            AZUL: "Ya asignada al docente"
                        };

                        const estado = materia.estado || "ROJO";

                        fila.classList.add(
                            `materia-${estado.toLowerCase()}`
                        );

                        const puedeAsignar = [
                            "VERDE",
                            "NARANJA"
                        ].includes(estado);

                        fila.innerHTML = `
                        <td style="text-align:center;">
                            <input
                                type="checkbox"
                                name="materias[]"
                                value="${materia.id_materia}"
                                ${puedeAsignar ? "" : "disabled"}
                            >
                        </td>

                        <td>
                            ${materia.nombre}
                        </td>

                        <td style="text-align:center;">
                            ${estados[estado] || "Desconocido"}
                        </td>
                    `;

                        tbody.appendChild(fila);
                    });

                    contenedor_materias.appendChild(tabla);
                }
            );

        } catch (error) {
            console.error("Error al obtener las materias:", error);
        }
    }

    formulario_registrar.addEventListener("submit", async function (e) {
        e.preventDefault();
        try {
            const formulario = new FormData(formulario_registrar);

            const respuesta = await fetch("/asig_mat_doc/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
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
                contenedor_materias.innerHTML = "";
            }
        } catch (error) {
            console.error(error);
        }
    });

});