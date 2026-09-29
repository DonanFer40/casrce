document.addEventListener("DOMContentLoaded", function () {

    const dialogo_actualizar_asignacion = document.getElementById("dialogo_actualizar");
    const btn_cerrar_dialogo = document.getElementById("cerrar_dialogo");
    const formulario_actualizar = document.getElementById("formulario_actualizar");

    const select_trayecto = document.getElementById("trayecto");
    const input_materia = document.getElementById("materia");

    const input_actualizar_id = document.getElementById("materia_asignada");
    const input_actualizar_nombre_materia = document.getElementById("nombre_materia");

    const input_actualizar_docente_principal_nombre = document.getElementById("docente_principal_nombre");
    const input_radius_principal_activo = document.getElementById("principal_activo");
    const input_radius_principal_inactivo = document.getElementById("principal_inactivo");

    const input_actualizar_docente_secundario_nombre = document.getElementById("docente_secundario_nombre");
    const input_radius_secundario_activo = document.getElementById("secundario_activo");
    const input_radius_secundario_inactivo = document.getElementById("secundario_inactivo");

    const input_radius_materia_activa = document.getElementById("materia_activa");
    const input_radius_materia_suspendida = document.getElementById("materia_suspendida");

    const contenedor_materias = document.getElementById("contenedor_materias");

    const label_perfil = document.getElementById("label_perfil");
    const select_perfiles_asignados = document.getElementById("perfiles_asignados");
    const input_perfil_asignado = document.getElementById("perfil_asignado");

    const label_pnf = document.getElementById("label_pnf");
    const select_pnfs_asignados = document.getElementById("pnfs_asignados");

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
    trayectos_registrados(perfil_seleccionado);

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

            const respuesta = await fetch("/mat_asig/", {
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
                contenedor_materias.innerHTML = `<p>${resultado.descripcion || "No se pudieron cargar las materias."}</p>`;
                return;
            }

            const materias_por_pnf = {};
            resultado.materias.forEach(materia => {
                const pnf = materia.pnf || "Sin PNF";
                const trayecto = materia.trayecto || "Sin trayecto";

                if (!materias_por_pnf[pnf]) {
                    materias_por_pnf[pnf] = {};
                }

                if (!materias_por_pnf[pnf][trayecto]) {
                    materias_por_pnf[pnf][trayecto] = [];
                }

                materias_por_pnf[pnf][trayecto].push(materia);
            });

            Object.entries(materias_por_pnf).forEach(([pnf, trayectos]) => {
                const contenedor_pnf = document.createElement("div");
                contenedor_pnf.classList.add("contenedor_pnf_materias");

                const titulo_pnf = document.createElement("h2");
                titulo_pnf.textContent = `P.N.F. ${pnf}`;

                contenedor_pnf.appendChild(titulo_pnf);

                Object.entries(trayectos).forEach(([trayecto, materias]) => {
                    const contenedor_trayecto = document.createElement("div");
                    contenedor_trayecto.classList.add("contenedor_trayecto_materias");

                    const titulo_trayecto = document.createElement("h3");
                    titulo_trayecto.textContent = trayecto;

                    const tabla = document.createElement("table");
                    tabla.classList.add("tabla-materias");

                    tabla.innerHTML = `
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>MATERIA</th>
                                <th>CÓDIGO</th>
                            </tr>
                        </thead>
                        <tbody></tbody>
                    `;

                    const tbody = tabla.querySelector("tbody");

                    materias.forEach((materia, index) => {
                        const fila = document.createElement("tr");
                        fila.dataset.id = materia.id_materia_asignada;

                        fila.innerHTML = `
                            <td>${index + 1}</td>
                            <td>${materia.nombre}</td>
                            <td>${materia.codigo}</td>
                        `;
                        tbody.appendChild(fila);
                    });

                    contenedor_trayecto.appendChild(titulo_trayecto);
                    contenedor_trayecto.appendChild(tabla);
                    contenedor_pnf.appendChild(contenedor_trayecto);
                });

                contenedor_materias.appendChild(contenedor_pnf);
            });
        } catch (error) {
            console.error(error);
        }
    }
    MateriasRegistrada();

    document.addEventListener("click", async (e) => {
        const fila = e.target.closest(".tabla-materias tbody tr");
        if (!fila) return;

        try {
            const formulario = new FormData();
            formulario.append("id_asignacion", fila.dataset.id);

            const respuesta = await fetch("/busc_mat/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            if (resultado.estado === "fallo") {
                await Swal.fire({
                    text: resultado.descripcion,
                    icon: resultado.icon,
                    title: resultado.title,
                    allowOutsideClick: false,
                    allowEscapeKey: false
                });
                return;
            }
            const materia = resultado.materia;

            dialogo_actualizar_asignacion.showModal();

            input_actualizar_id.value = materia.id_materia_asignada;
            input_actualizar_nombre_materia.value = materia.nombre;

            const docente_principal = materia.docentes.find(
                docente => docente.rol === "PRINCIPAL"
            );

            const docente_secundario = materia.docentes.find(
                docente => docente.rol === "SECUNDARIO"
            );

            if (docente_principal) {
                input_actualizar_docente_principal_nombre.value = docente_principal.nombre_completo;

                input_radius_principal_activo.checked = docente_principal.activo;

                input_radius_principal_inactivo.checked = !docente_principal.activo;
            } else {
                input_actualizar_docente_principal_nombre.value = "No asignado";
                input_radius_principal_activo.checked = false;
                input_radius_principal_inactivo.checked = false;
            }

            if (docente_secundario) {
                input_actualizar_docente_secundario_nombre.value = docente_secundario.nombre_completo;

                input_radius_secundario_activo.checked = docente_secundario.activo;

                input_radius_secundario_inactivo.checked = !docente_secundario.activo;

                input_radius_secundario_activo.disabled = false;
                input_radius_secundario_inactivo.disabled = false;
            } else {
                input_actualizar_docente_secundario_nombre.value = "No asignado";
                input_radius_secundario_activo.checked = false;
                input_radius_secundario_inactivo.checked = false;

                input_radius_secundario_activo.disabled = true;
                input_radius_secundario_inactivo.disabled = true;
            }

            input_radius_materia_activa.checked = materia.activo;
            input_radius_materia_suspendida.checked = !materia.activo;

            if (materia.activo && docente_principal && !docente_secundario) {
                input_radius_principal_activo.disabled = false;
                input_radius_principal_inactivo.disabled = true;

                input_radius_principal_activo.checked = true;
                input_radius_principal_inactivo.checked = false;
            } else {
                input_radius_principal_activo.disabled = false;
                input_radius_principal_inactivo.disabled = false;
            }
        } catch (error) {
            console.error(error);
        }
    });

    // CAMBIO DE ESTADO DE LA MATERIA
    input_radius_materia_activa.addEventListener("change", () => {
        if (!input_radius_materia_activa.checked) {
            return;
        }

        const existe_secundario = input_actualizar_docente_secundario_nombre.value.trim() !== "" &&
            input_actualizar_docente_secundario_nombre.value.trim() !== "No asignado";

        // NO EXISTE SECUNDARIO
        if (!existe_secundario) {
            input_radius_principal_activo.checked = true;
            input_radius_principal_inactivo.checked = false;

            input_radius_principal_inactivo.disabled = true;

            input_radius_secundario_activo.disabled = true;
            input_radius_secundario_inactivo.disabled = true;
            return;
        }

        // EXISTE SECUNDARIO
        input_radius_principal_inactivo.disabled = false;
        input_radius_secundario_activo.disabled = false;
        input_radius_secundario_inactivo.disabled = false;
    });

    // MATERIA SUSPENDIDA
    input_radius_materia_suspendida.addEventListener("change", () => {
        if (!input_radius_materia_suspendida.checked) {
            return;
        }

        // Los docentes quedan inactivos. La materia está suspendida.
        input_radius_principal_activo.checked = false;
        input_radius_principal_inactivo.checked = true;

        if (input_actualizar_docente_secundario_nombre.value.trim() !== "" &&
            input_actualizar_docente_secundario_nombre.value.trim() !== "No asignado") {
            input_radius_secundario_activo.checked = false;

            input_radius_secundario_inactivo.checked = true;
        } else {
            input_radius_secundario_activo.checked = false;
            input_radius_secundario_inactivo.checked = false;
        }

        input_radius_principal_inactivo.disabled = false;

        if (input_actualizar_docente_secundario_nombre.value.trim() === "" ||
            input_actualizar_docente_secundario_nombre.value.trim() === "No asignado") {
            input_radius_secundario_activo.disabled = true;

            input_radius_secundario_inactivo.disabled = true;
        } else {
            input_radius_secundario_activo.disabled = false;
            input_radius_secundario_inactivo.disabled = false;
        }
    });

    // PRINCIPAL ACTIVO
    input_radius_principal_activo.addEventListener("change", () => {

        if (!input_radius_principal_activo.checked) {
            // No permitir que ambos queden falsos
            input_radius_principal_inactivo.checked = true;
            return;
        }

        const existe_secundario =
            input_actualizar_docente_secundario_nombre.value.trim() !== "" &&
            input_actualizar_docente_secundario_nombre.value.trim() !== "No asignado";

        // No existe secundario
        if (!existe_secundario) {
            input_radius_principal_activo.checked = true;
            input_radius_principal_inactivo.checked = false;

            input_radius_principal_inactivo.disabled = true;
            return;
        }

        // Principal activo → secundario inactivo
        input_radius_principal_inactivo.checked = false;

        input_radius_secundario_activo.checked = false;
        input_radius_secundario_inactivo.checked = true;
    });

    // PRINCIPAL INACTIVO
    input_radius_principal_inactivo.addEventListener("change", () => {

        if (!input_radius_principal_inactivo.checked) {
            // No permitir ambos falsos
            input_radius_principal_activo.checked = true;
            return;
        }

        const existe_secundario =
            input_actualizar_docente_secundario_nombre.value.trim() !== "" &&
            input_actualizar_docente_secundario_nombre.value.trim() !== "No asignado";

        if (!existe_secundario) {
            // Sin secundario, el principal obligatoriamente debe estar activo
            input_radius_principal_activo.checked = true;
            input_radius_principal_inactivo.checked = false;
            return;
        }

        // Principal inactivo → secundario activo
        input_radius_principal_activo.checked = false;

        input_radius_secundario_activo.checked = true;
        input_radius_secundario_inactivo.checked = false;
    });

    // SECUNDARIO ACTIVO
    input_radius_secundario_activo.addEventListener("change", () => {
        if (!input_radius_secundario_activo.checked) {
            return;
        }

        const existe_principal =
            input_actualizar_docente_principal_nombre.value.trim() !== "" &&
            input_actualizar_docente_principal_nombre.value.trim() !== "No asignado";

        if (!existe_principal) {
            input_radius_secundario_activo.checked = false;
            input_radius_secundario_inactivo.checked = true;
            return;
        }

        // Si el secundario queda activo,
        // el principal debe quedar inactivo.
        input_radius_principal_activo.checked = false;
        input_radius_principal_inactivo.checked = true;
    });

    // SECUNDARIO INACTIVO
    input_radius_secundario_inactivo.addEventListener("change", () => {
        if (!input_radius_secundario_inactivo.checked) {
            return;
        }

        const existe_principal =
            input_actualizar_docente_principal_nombre.value.trim() !== "" &&
            input_actualizar_docente_principal_nombre.value.trim() !== "No asignado";

        if (!existe_principal) {
            return;
        }

        // Si el secundario queda inactivo,
        // el principal debe quedar activo.
        input_radius_secundario_activo.checked = false;
        input_radius_principal_activo.checked = true;
        input_radius_principal_inactivo.checked = false;
    });


    formulario_actualizar.addEventListener("submit", async function (e) {
        e.preventDefault();
        try {
            const formulario = new FormData(formulario_actualizar);
            formulario.append("perfil", perfil_seleccionado);

            const respuesta = await fetch("/act_asig/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            dialogo_actualizar_asignacion.close();

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

    btn_cerrar_dialogo.addEventListener("click", () => {
        dialogo_actualizar_asignacion.close();
    });

});