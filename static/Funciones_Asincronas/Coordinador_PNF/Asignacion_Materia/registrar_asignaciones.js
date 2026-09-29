document.addEventListener("DOMContentLoaded", function () {

    const formulario_registrar = document.getElementById("formulario_asignar_materia");
    const select_docentes_registrados = document.getElementById("docentes_registrados");
    const select_rol_docente = document.getElementById("rol_docente");
    const contenedor_materias = document.getElementById("contenedor_materias");

    const label_perfil = document.getElementById("label_perfil");
    const select_perfiles_asignados = document.getElementById("perfiles_asignados");
    const input_perfil_asignado = document.getElementById("perfil_asignado");

    const label_pnf = document.getElementById("label_pnf");
    const select_pnfs_asignados = document.getElementById("pnfs_asignados");

    let pnf = "", docente = "", rol_docente = "";

    let perfil_seleccionado = "";

    async function perfiles_asignados() {
        try {
            const respuesta = await fetch("/perf_asig_coord/");
            const resultado = await respuesta.json();

            console.log(resultado);

            const tiene_coordinador_pnf = resultado.coordinador_pnf;
            const tiene_control_estudio = resultado.control_estudio;

            input_perfil_asignado.value = "";

            select_perfiles_asignados.innerHTML = `
                <option value="" selected>
                    Seleccione un perfil
                </option>
            `;

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

            if (tiene_coordinador_pnf) {

                perfil_seleccionado = "COORDINADOR_PNF";

                input_perfil_asignado.value = "Coordinador de PNF";

                label_perfil.style.display = "";
                input_perfil_asignado.style.display = "";
                select_perfiles_asignados.style.display = "none";

                // El coordinador NO selecciona PNF.
                // El PNF se obtiene directamente de su perfil.
                label_pnf.style.display = "none";
                select_pnfs_asignados.style.display = "none";

                select_pnfs_asignados.innerHTML = `
                    <option value="" selected>
                        Seleccione el P.N.F
                    </option>
                `;

                await obtener_pnfs_asignados();
                await obtener_docentes_registrados();
                return;
            }

            if (tiene_control_estudio) {

                perfil_seleccionado = "CONTROL_ESTUDIO";

                input_perfil_asignado.value = "Encargado de Control de Estudio";

                label_perfil.style.display = "";
                input_perfil_asignado.style.display = "";
                select_perfiles_asignados.style.display = "none";

                // Control de Estudio SÍ selecciona PNF.
                label_pnf.style.display = "";
                select_pnfs_asignados.style.display = "";

                await obtener_pnfs_asignados();
                await obtener_docentes_registrados();
                return;
            }

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

            label_pnf.style.display = "";
            select_pnfs_asignados.style.display = "";

        } else if (perfil_seleccionado === "COORDINADOR_PNF") {

            // Nunca muestra el select PNF.
            label_pnf.style.display = "none";
            select_pnfs_asignados.style.display = "none";

            select_pnfs_asignados.innerHTML = `
            <option value="" selected>
                Seleccione el P.N.F
            </option>
        `;
        }

        await obtener_pnfs_asignados();
        await obtener_docentes_registrados();
    });

    async function obtener_pnfs_asignados() {
        try {
            const formulario = new FormData();
            formulario.append("perfil", perfil_seleccionado);

            const respuesta = await fetch("/obt_pnfs_coord/", {
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

            select_pnfs_asignados.innerHTML = `
                <option value="">
                    Seleccione el P.N.F
                </option>
            `;

            if (resultado.estado !== "exito") {
                return;
            }

            resultado.pnfs.forEach(pnf => {
                const opcion = document.createElement("option");
                opcion.value = pnf.id_pnf;
                opcion.textContent = pnf.pnf;
                select_pnfs_asignados.appendChild(opcion);
            });

            if (perfil_seleccionado === "COORDINADOR_PNF") {

                // El PNF existe, pero no se muestra al usuario
                // como un selector.
                label_pnf.style.display = "none";
                select_pnfs_asignados.style.display = "none";
            }

            if (perfil_seleccionado === "CONTROL_ESTUDIO") {

                label_pnf.style.display = "";
                select_pnfs_asignados.style.display = "";
            }

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
            const formulario = new FormData();
            formulario.append("pnf_asignado", pnf);
            formulario.append("perfil", perfil_seleccionado);
            console.log(perfil_seleccionado);

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
            if (!docente || !rol_docente) return;

            const formulario = new FormData();
            formulario.append("pnf_asignado", pnf);
            formulario.append("docente_seleccionado", docente);
            formulario.append("rol_docente", rol_docente);
            formulario.append("perfil", perfil_seleccionado);

            const respuesta = await fetch("/mats_reg/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            contenedor_materias.innerHTML = "";

            if (resultado.estado !== "exito") {
                contenedor_materias.innerHTML = `
                    <p>${resultado.descripcion || "No se pudieron cargar las materias."}</p>
                `;
                return;
            }

            const materias = Array.isArray(resultado.materias) ? resultado.materias : [];

            if (materias.length === 0) {
                contenedor_materias.innerHTML = `
                    <p>No hay materias registradas.</p>
                `;
                return;
            }

            const materiasPorTrayecto = {};

            materias.forEach(materia => {
                const trayecto = String(materia.trayecto ?? "Sin trayecto");

                if (!materiasPorTrayecto[trayecto]) {
                    materiasPorTrayecto[trayecto] = [];
                }

                materiasPorTrayecto[trayecto].push(materia);
            });

            Object.entries(materiasPorTrayecto).forEach(([trayecto, listaMaterias]) => {
                const titulo = document.createElement("h4");
                titulo.textContent = trayecto;
                contenedor_materias.appendChild(titulo);

                const tabla = document.createElement("table");
                tabla.classList.add("tabla-materias");

                tabla.innerHTML = `
                    <thead>
                        <tr>
                            <th style="width:60px; text-align:center;">Asignar</th>
                            <th>Materia</th>
                            <th style="width:160px; text-align:center;">Estado</th>
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
                    fila.classList.add(`materia-${estado.toLowerCase()}`);

                    const puedeAsignar = materia.puede_asignar === true && estado !== "ROJO";

                    fila.innerHTML = `
                        <td style="text-align:center;">
                            <input type="checkbox"  name="materias[]" value="${materia.id_materia}" ${puedeAsignar ? "" : "disabled"}>
                        </td>
                        <td>${materia.nombre}</td>
                        <td style="text-align:center;">${estados[estado] || "Desconocido"}</td>
                    `;
                    tbody.appendChild(fila);
                });

                contenedor_materias.appendChild(tabla);
            });
        } catch (error) {
            console.error(error);
        }
    }

    formulario_registrar.addEventListener("submit", async function (e) {
        e.preventDefault();
        try {
            const formulario = new FormData(formulario_registrar);
            formulario.append("perfil", perfil_seleccionado);

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
                select_docentes_registrados.innerHTML = "<option value=''>Selecciona un docente.</option>";
                select_pnfs_asignados.innerHTML = "<option value=''>Selecciona un P.N.F.</option>";
                select_rol_docente.innerHTML = "<option value=''>Seleccione una opción</option>";
                contenedor_materias.innerHTML = "";
            }
        } catch (error) {
            console.error(error);
        }
    });

});