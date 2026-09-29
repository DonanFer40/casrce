document.addEventListener("DOMContentLoaded", function () {

    const select_trayecto = document.getElementById("trayecto");
    const input_materia = document.getElementById("materia");

    const label_perfil = document.getElementById("label_perfil");
    const select_perfiles_asignados = document.getElementById("perfiles_asignados");
    const input_perfil_asignado = document.getElementById("perfil_asignado");

    const label_pnf = document.getElementById("label_pnf");
    const select_pnfs_asignados = document.getElementById("pnfs_asignados");

    const contenedor_materias = document.getElementById("contenedor_materias");

    let trayecto = "", nombre = "", pnf = "";

    let perfil_seleccionado = "";

    async function perfiles_asignados() {
        try {
            const respuesta = await fetch("/perf_asig_coord/");
            const resultado = await respuesta.json();

            const tiene_coordinador_pnf = resultado.coordinador_pnf;
            const tiene_control_estudio = resultado.control_estudio;

            input_perfil_asignado.value = "";

            select_perfiles_asignados.innerHTML = `
            <option value="" selected>
                Seleccione un perfil
            </option>
        `;

            // COORDINADOR + CONTROL DE ESTUDIO
            if (tiene_coordinador_pnf && tiene_control_estudio) {

                select_perfiles_asignados.innerHTML = `
                <option value="" selected>
                    Seleccione un perfil
                </option>

                <option value="COORDINADOR_PNF">
                    Coordinador de PNF
                </option>

                <option value="CONTROL_ESTUDIO">
                    Encargado de Control de Estudio
                </option>
            `;

                label_perfil.style.display = "";
                select_perfiles_asignados.style.display = "";

                input_perfil_asignado.style.display = "none";

                label_pnf.style.display = "none";
                select_pnfs_asignados.style.display = "none";
                select_pnfs_asignados.innerHTML = `
                <option value="" selected>
                    Seleccione el P.N.F
                </option>
            `;

                perfil_seleccionado = "";

                return;
            }

            // SOLO COORDINADOR DE PNF
            if (tiene_coordinador_pnf) {

                perfil_seleccionado = "COORDINADOR_PNF";

                input_perfil_asignado.value = "Coordinador de PNF";

                label_perfil.style.display = "";
                input_perfil_asignado.style.display = "";
                select_perfiles_asignados.style.display = "none";

                // Ocultar PNF porque el coordinador ya tiene uno asignado
                label_pnf.style.display = "none";
                select_pnfs_asignados.style.display = "none";
                select_pnfs_asignados.innerHTML = "";

                await obtener_pnfs_asignados(perfil_seleccionado);
                await MateriasRegistrada(perfil_seleccionado);
                await trayectos_registrados(perfil_seleccionado);

                return;
            }

            // SOLO CONTROL DE ESTUDIO
            if (tiene_control_estudio) {

                perfil_seleccionado = "CONTROL_ESTUDIO";

                input_perfil_asignado.value = "Encargado de Control de Estudio";

                label_perfil.style.display = "";
                input_perfil_asignado.style.display = "";
                select_perfiles_asignados.style.display = "none";

                // Control de Estudio puede seleccionar el PNF
                label_pnf.style.display = "";
                select_pnfs_asignados.style.display = "";

                await obtener_pnfs_asignados(perfil_seleccionado);
                await MateriasRegistrada(perfil_seleccionado);
                await trayectos_registrados(perfil_seleccionado);

                return;
            }

            // SIN PERFIL
            perfil_seleccionado = "";

            input_perfil_asignado.value = "";

            label_perfil.style.display = "none";
            select_perfiles_asignados.style.display = "none";
            input_perfil_asignado.style.display = "none";

            label_pnf.style.display = "none";
            select_pnfs_asignados.style.display = "none";

            select_pnfs_asignados.innerHTML = `
            <option value="" selected>
                Seleccione el P.N.F
            </option>
        `;

        } catch (error) {
            console.error(error);
        }
    }
    perfiles_asignados();

    select_perfiles_asignados.addEventListener("change", async () => {

        perfil_seleccionado = select_perfiles_asignados.value;

        if (!perfil_seleccionado) {

            label_pnf.style.display = "none";
            select_pnfs_asignados.style.display = "none";

            select_pnfs_asignados.innerHTML = `
            <option value="" selected>
                Seleccione el P.N.F
            </option>
        `;

            return;
        }

        if (perfil_seleccionado === "CONTROL_ESTUDIO") {

            // Mostrar etiqueta y select del PNF
            label_pnf.style.display = "";
            select_pnfs_asignados.style.display = "";

        } else if (perfil_seleccionado === "COORDINADOR_PNF") {

            // Ocultar etiqueta y select del PNF
            label_pnf.style.display = "none";
            select_pnfs_asignados.style.display = "none";

            select_pnfs_asignados.innerHTML = "";
        }

        await obtener_pnfs_asignados(perfil_seleccionado);
        await MateriasRegistrada(perfil_seleccionado);
        await trayectos_registrados(perfil_seleccionado);
    });

    async function obtener_pnfs_asignados(perfil_seleccionado) {
        try {
            const formulario = new FormData();
            formulario.append("perfil", perfil_seleccionado);

            const respuesta = await fetch("/obt_pnfs_coord/", {
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

        await MateriasRegistrada();

        await trayectos_registrados(perfil_seleccionado);
    });

    async function trayectos_registrados(perfil_seleccionado) {
        try {
            const formulario = new FormData();
            formulario.append("pnf_asignado", pnf);
            formulario.append("perfil", perfil_seleccionado);

            const respuesta = await fetch("/tray_mat_asg/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            select_trayecto.innerHTML = '<option value="">Selecciona un trayecto.</option>';

            resultado.trayectos.forEach(trayecto => {
                const opcion = document.createElement("option");
                opcion.value = trayecto.id_trayecto;
                opcion.textContent = trayecto.nombre;
                select_trayecto.appendChild(opcion);
            });
        } catch (error) {
            console.error(error);
        }
    }

    input_materia.addEventListener("input", async () => {
        nombre = input_materia.value;

        await MateriasRegistrada();
    });

    select_trayecto.addEventListener("change", async () => {
        trayecto = select_trayecto.value;

        await MateriasRegistrada();
    });

    async function MateriasRegistrada() {
        try {
            const formulario = new FormData();
            formulario.append("pnf_asignado", pnf);
            formulario.append("trayecto", trayecto);
            formulario.append("materia", nombre);
            formulario.append("perfil", perfil_seleccionado);

            const respuesta = await fetch("/mats_desact/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            contenedor_materias.innerHTML = "";

            // AGRUPAR MATERIAS POR TRAYECTO
            const materias_por_trayecto = {};
            resultado.materias.forEach(materia => {
                if (!materias_por_trayecto[materia.trayecto]) {
                    materias_por_trayecto[materia.trayecto] = [];
                }

                materias_por_trayecto[materia.trayecto].push(materia);
            });

            Object.entries(materias_por_trayecto).forEach(([trayecto, materias]) => {
                const contenedor_trayecto = document.createElement("div");

                // TÍTULO DEL TRAYECTO
                const titulo = document.createElement("h3");
                titulo.textContent = trayecto;

                const tabla = document.createElement("table");
                tabla.classList.add("tabla-materias");
                tabla.innerHTML = `
                    <thead>
                        <tr>
                            <th>N.º</th>
                            <th>MATERIA</th>
                            <th>CÓDIGO</th>
                            <th>SECCIÓN</th>
                            <th>DOCENTE PRINCIPAL</th>
                            <th>DOCENTE SUPLENTE</th>
                            <th>FECHA DE SUSPENSIÓN</th>
                            <th>ESTADO</th>
                        </tr>
                    </thead>
                    <tbody></tbody>
                `;

                const tbody = tabla.querySelector("tbody");

                // FILAS
                materias.forEach((materia, index) => {
                    const fila = document.createElement("tr");

                    // ID de la asignación.
                    // Se utilizará cuando se seleccione la fila.
                    fila.dataset.id = materia.id_materia_asignada;

                    // DOCENTE PRINCIPAL
                    const nombre_principal = materia.docente_principal ? materia.docente_principal.nombre_completo : "No asignado";

                    // DOCENTE SECUNDARIO
                    const nombre_secundario = materia.docente_secundario ? materia.docente_secundario.nombre_completo : "No asignado";
                    const fecha_suspension = materia.fecha_suspension ? new Date(materia.fecha_suspension).toLocaleString("es-VE") : "No registrada";

                    fila.innerHTML = `
                        <td>${index + 1}</td>
                        <td>${materia.nombre}</td>
                        <td>${materia.codigo}</td>
                        <td>${materia.seccion}</td>
                        <td>${nombre_principal}</td>
                        <td>${nombre_secundario}</td>
                        <td>${fecha_suspension}</td>
                        <td>
                            <button
                                type="button"
                                class="btn-reactivar-materia"
                                data-id="${materia.id_materia_asignada}">
                                Reactivar
                            </button>
                        </td>`;

                    tbody.appendChild(fila);
                });

                contenedor_trayecto.appendChild(titulo);

                contenedor_trayecto.appendChild(tabla);
                contenedor_materias.appendChild(contenedor_trayecto);
            });
        } catch (error) {
            console.error(error);
        }
    }
    MateriasRegistrada();

    document.addEventListener("click", async (e) => {
        const boton = e.target.closest(".btn-reactivar-materia");
        if (!boton) return;

        try {
            const formulario = new FormData();
            formulario.append("materia_asignada", boton.dataset.id);
            formulario.append("perfil", perfil_seleccionado);

            const respuesta = await fetch("/asig_desact/", {
                method: "POST",
                headers: {
                    "X-CSRFToken":
                        document.querySelector("[name=csrfmiddlewaretoken]").value
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

            await MateriasRegistrada();
        } catch (error) {
            console.error(error);
        }
    });

});