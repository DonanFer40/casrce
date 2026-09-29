document.addEventListener("DOMContentLoaded", () => {

    const formulario_busqueda = document.getElementById("formulario_busqueda");
    const select_nacionalidad = document.getElementById("nacionalidad");
    const input_cedula_identidad = document.getElementById("cedula_identidad");

    const btn_agregar_perfil = document.getElementById("btn_agregar_perfil");
    const btn_limpiar_controles = document.getElementById("btn_limpiar_controles");

    const input_nombres_usuario = document.getElementById("nombres_usuario");
    const input_apellidos_usuario = document.getElementById("apellidos_usuario");
    const input_ci_usuario_visualizar = document.getElementById("ci_usuario_visualizar");

    const dialogo_registrar = document.getElementById("dialogo_registrar");
    const cerrar_dialogo_registrar = document.getElementById("cerrar_dialogo_registrar");

    const input_rol_seleccionado = document.getElementById("rol_seleccionado");
    const input_perfil_seleccionado = document.getElementById("perfil_seleccionado");
    const input_estado_perfil_seleccionado = document.getElementById("estado_perfil_seleccionado");
    const formulario_registrar = document.getElementById("formulario_registrar");
    const contenedor_nuevo_perfiles = document.getElementById("contenedor_nuevo_perfiles");

    const contenedor_pnfs = document.getElementById("contenedor_pnfs");

    const dialogo_actualizar = document.getElementById("dialogo_actualizar");
    const cerrar_dialogo_actualizar = document.getElementById("cerrar_dialogo_actualizar");

    const formulario_actualizar = document.getElementById("formulario_actualizar");

    const input_habilitar_perfil = document.getElementById("habilitar_perfil");
    const input_deshabilitar_perfil = document.getElementById("deshabilitar_perfil");

    const contenedor_perfiles = document.getElementById("contenedor_perfiles");

    configurarCedula(select_nacionalidad, input_cedula_identidad);

    function getCookie(nombre) {
        let cookieValue = null;

        if (document.cookie && document.cookie !== "") {
            const cookies = document.cookie.split(";");

            for (let cookie of cookies) {
                cookie = cookie.trim();

                if (cookie.startsWith(nombre + "=")) {
                    cookieValue = decodeURIComponent(
                        cookie.substring(nombre.length + 1)
                    );
                    break;
                }
            }
        }

        return cookieValue;
    }

    formulario_busqueda.addEventListener("submit", async (e) => {
        e.preventDefault();
        try {
            const formulario = new FormData(formulario_busqueda);

            const respuesta = await fetch("/bus_per_asig/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": getCookie("csrftoken")
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            formulario_busqueda.reset();

            if (resultado.estado == "fallo") {
                await Swal.fire({
                    title: resultado.title,
                    text: resultado.descripcion,
                    icon: resultado.icon,
                    allowOutsideClick: false,
                    allowEscapeKey: false
                });
                return;
            }

            await Swal.fire({
                title: "Exito",
                text: "Se encontro los datos del usuario.",
                icon: "success",
                allowOutsideClick: false,
                allowEscapeKey: false
            });

            btn_agregar_perfil.disabled = false;

            input_nombres_usuario.value = resultado.usuario.nombres;
            input_apellidos_usuario.value = resultado.usuario.apellidos;

            input_ci_usuario_visualizar.value = resultado.usuario.cedula;

            contenedor_perfiles.innerHTML = "";

            if (resultado.perfiles && resultado.perfiles.length > 0) {
                resultado.perfiles.forEach((perfil, index) => {
                    const fila = document.createElement("tr");
                    fila.dataset.idPerfil = perfil.id_perfil;
                    fila.dataset.rol = perfil.rol;

                    fila.innerHTML = `
                        <td>${index + 1}</td>
                        <td>${perfil.rol}</td>
                        <td>${perfil.pnf}</td>
                        <td>${perfil.nucleo}</td>
                        <td>${perfil.estado}</td>
                    `;

                    contenedor_perfiles.appendChild(fila);
                });

            } else {
                const fila = document.createElement("tr");
                fila.innerHTML = `
                    <td colspan="3" class="sin_perfiles">
                        No hay perfiles registrados para este usuario.
                    </td>
                `;
                contenedor_perfiles.appendChild(fila);
            }
        } catch (error) {
            console.error(error);
        }
    });

    contenedor_perfiles.addEventListener("click", async (e) => {
        const fila = e.target.closest("tr");
        if (!fila || !fila.dataset.rol) return;

        const rol = fila.dataset.rol;
        const idPerfil = fila.dataset.idPerfil;

        console.log(rol)

        try {
            const formulario = new FormData();
            formulario.append("rol", rol);
            const respuesta = await fetch("/info_per_asig/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": getCookie("csrftoken")
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);
            if (resultado.estado !== "exito") {
                await Swal.fire({
                    icon: resultado.icon,
                    title: resultado.title,
                    text: resultado.descripcion
                });
                return;
            }
            input_rol_seleccionado.value = rol;
            input_perfil_seleccionado.value = idPerfil;

            input_estado_perfil_seleccionado.value = resultado.activo;
            input_habilitar_perfil.checked = false;
            input_deshabilitar_perfil.checked = false;


            if (resultado.activo === true) {
                input_habilitar_perfil.checked = true;
            } else if (resultado.activo === false) {
                input_deshabilitar_perfil.checked = true;
            }
            contenedor_pnfs.innerHTML = "";
            const pnfsAsignados = new Set(
                (resultado.pnfs_asignados || []).map(
                    pnf => String(pnf.id_pnf)
                )
            );

            const pnfsDisponibles = resultado.pnfs_disponibles || [];
            pnfsDisponibles.forEach((pnf) => {

                const idPnf = String(pnf.id_pnf);

                const asignado = pnfsAsignados.has(idPnf);

                const contenedor = document.createElement("div");

                contenedor.classList.add("pnf_opcion");

                const tipoInput = rol === "Coordinador de PNF" ? "radio" : "checkbox";
                const nombreInput = rol === "Coordinador de PNF" ? "pnf_coordinador" : "pnf";

                contenedor.innerHTML = `
                <label>
                    <input
                        type="${tipoInput}"
                        name="${nombreInput}"
                        value="${pnf.id_pnf}"
                        ${asignado ? "checked" : ""}
                    >
                    <span>${pnf.pnf}</span>
                    <small>${pnf.codigo}</small>
                </label>
            `;
                contenedor_pnfs.appendChild(contenedor);
            });

            if (pnfsDisponibles.length === 0) {
                contenedor_pnfs.innerHTML = `
                <div class="sin_pnfs">
                    No hay PNF disponibles para asignar.
                </div>
            `;
            }

            dialogo_actualizar.showModal();
        } catch (error) {
            console.error(error);
        }
    });

    formulario_actualizar.addEventListener("submit", async (e) => {
        e.preventDefault();
        const perfilActivo = input_habilitar_perfil.checked;
        input_estado_perfil_seleccionado.value = perfilActivo ? "true" : "false";

        try {
            const formulario = new FormData(formulario_actualizar);

            console.log("ROL:", formulario.get("rol"));
            console.log("ID PERFIL:", formulario.get("id_perfil"));
            console.log("ESTADO:", formulario.get("estado_perfil"));

            const respuesta = await fetch("/act_per_reg/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": getCookie("csrftoken")
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);
            dialogo_actualizar.close();
            await Swal.fire({
                title: resultado.title,
                text: resultado.descripcion,
                icon: resultado.icon,
                allowOutsideClick: false,
                allowEscapeKey: false
            });
            if (resultado.estado === "exito") {
                await perfiles_registrados();
            }
        } catch (error) {
            console.error(error);
        }
    });

    cerrar_dialogo_actualizar.addEventListener("click", () => {
        dialogo_actualizar.close();
    });

    btn_agregar_perfil.addEventListener("click", async () => {
        try {
            const respuesta = await fetch("/per_dis_asi/");
            const resultado = await respuesta.json();

            if (resultado.estado !== "exito") {
                Swal.fire({
                    icon: resultado.icon,
                    title: resultado.title,
                    text: resultado.descripcion
                });
                return;
            }

            contenedor_nuevo_perfiles.innerHTML = "";

            if (!resultado.perfiles?.length) {
                contenedor_nuevo_perfiles.innerHTML = `
                    <p class="mensaje_sin_perfiles">
                        No existen perfiles disponibles para asignar
                        en el núcleo ${resultado.nucleo.municipio}.
                    </p>
                `;

                dialogo_registrar.showModal();
                return;
            }

            resultado.perfiles.forEach((perfil) => {
                const contenedor = document.createElement("div");
                contenedor.className = "perfil_disponible";

                const clavePerfil = {
                    "Docente": "docente",
                    "Coordinador de PNF": "coordinador_pnf",
                    "Encargado de Control de Estudio": "control_estudio"
                }[perfil.rol];

                const idPerfil = `perfil_${clavePerfil}`;

                contenedor.innerHTML = `
                    <label class="checkbox_pnf perfil_principal">
                        <input
                            type="checkbox"
                            name="perfiles"
                            value="${perfil.rol}"
                            id="${idPerfil}"
                        >

                        <span>${perfil.rol}</span>
                    </label>
                `;

                /* PNF DEL PERFIL */
                if (perfil.pnfs?.length) {
                    const contenedorPnfs = document.createElement("div");
                    contenedorPnfs.className = "contenedor_pnfs_disponibles";
                    contenedorPnfs.hidden = true;

                    contenedorPnfs.innerHTML = `
                        <p class="titulo_pnf">
                            PNF disponibles en ${resultado.nucleo.municipio}
                        </p>
                        <div class="lista_checkbox_pnf"></div>
                    `;

                    const listaPnfs = contenedorPnfs.querySelector(".lista_checkbox_pnf");

                    perfil.pnfs.forEach((pnf) => {
                        const etiqueta = document.createElement("label");
                        etiqueta.className = "checkbox_pnf";
                        etiqueta.innerHTML = `
                            <input type="checkbox" name="pnfs_${clavePerfil}" value="${pnf.id_pnf}">
                            <span>
                                ${pnf.id_pnf__pnf}
                                <small>
                                    (${pnf.id_pnf__codigo})
                                </small>
                            </span>
                        `;
                        listaPnfs.appendChild(etiqueta);
                    });

                    contenedor.appendChild(contenedorPnfs);

                    /* MOSTRAR / OCULTAR PNF */
                    const checkboxPerfil = contenedor.querySelector(`#${idPerfil}`);

                    checkboxPerfil.addEventListener("change", () => {
                        if (checkboxPerfil.checked) {
                            contenedorPnfs.hidden = false;
                        } else {
                            contenedorPnfs.hidden = true;

                            contenedorPnfs.querySelectorAll(
                                'input[type="checkbox"]'
                            )
                                .forEach((checkbox) => {
                                    checkbox.checked = false;
                                });
                        }
                    });
                }

                contenedor_nuevo_perfiles.appendChild(contenedor);
            });

            dialogo_registrar.showModal();
        } catch (error) {
            console.error(error);
        }
    });

    cerrar_dialogo_registrar.addEventListener("click", () => {
        dialogo_registrar.close();
    });

    formulario_registrar.addEventListener("submit", async (e) => {
        e.preventDefault();

        try {
            const formulario = new FormData(formulario_registrar);

            if (!formulario.getAll("perfiles").length) {
                Swal.fire({
                    icon: "warning",
                    title: "Perfil no seleccionado",
                    text: "Debe seleccionar al menos un perfil."
                });
                return;
            }

            const respuesta = await fetch("/agr_per_asig/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": getCookie("csrftoken")
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            dialogo_registrar.close();

            await perfiles_registrados();

            await Swal.fire({
                title: resultado.title,
                text: resultado.descripcion,
                icon: resultado.icon,
                allowOutsideClick: false,
                allowEscapeKey: false
            });
        } catch (error) {
            console.error(error);
        }
    });

    async function limpiar_controles() {
        try {
            const respuesta = await fetch("/eli_var_sec/");
            const resultado = await respuesta.json();
            console.log(resultado);
            input_nombres_usuario.value = "";
            input_apellidos_usuario.value = "";
            input_cedula_identidad.value = "";
            contenedor_perfiles.innerHTML = "";
            btn_agregar_perfil.disabled = true;
        } catch (error) {
            console.error(error);
        }
    }

    btn_limpiar_controles.addEventListener("click", async () => {
        await limpiar_controles();
    });

    window.addEventListener("load", async () => {
        await limpiar_controles();
    });

    async function perfiles_registrados() {
        try {
            const respuesta = await fetch("/per_reg/");
            const resultado = await respuesta.json();
            console.log(resultado);
            if (resultado.estado === "fallo") {
                await Swal.fire({
                    title: resultado.title,
                    text: resultado.descripcion,
                    icon: resultado.icon,
                    allowOutsideClick: false,
                    allowEscapeKey: false
                });
                return;
            }
            contenedor_perfiles.innerHTML = "";
            if (!resultado.perfiles || resultado.perfiles.length === 0) {
                const fila = document.createElement("tr");
                fila.innerHTML = `
                <td colspan="5" class="sin_perfiles">
                    No hay perfiles registrados.
                </td>
            `;
                contenedor_perfiles.appendChild(fila);
                return;
            }
            resultado.perfiles.forEach((perfil, index) => {
                const fila = document.createElement("tr");
                fila.dataset.idPerfil = perfil.id_perfil;
                fila.dataset.rol = perfil.rol;
                console.log(fila.dataset.idPerfil);
                fila.innerHTML = `
                <td>
                    ${index + 1}
                </td>
                <td>
                    ${perfil.rol}
                </td>
                <td>
                    ${perfil.pnf
                        ? perfil.pnf.nombre
                        : "NO CUENTA CON P.N.F"
                    }
                </td>
                <td>
                    ${perfil.nucleo
                        ? perfil.nucleo.municipio
                        : "NO CUENTA CON NÚCLEO"
                    }
                </td>
                <td>
                    ${perfil.estado}
                </td>
            `;
                contenedor_perfiles.appendChild(fila);
            });
        } catch (error) {
            console.error(error);
        }
    }
    perfiles_registrados();
});