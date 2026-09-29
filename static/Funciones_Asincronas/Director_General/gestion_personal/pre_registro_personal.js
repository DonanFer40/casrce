document.addEventListener("DOMContentLoaded", () => {
    const formulario_registrar = document.getElementById("formulario_registrar");

    const input_cedula_identidad = document.getElementById("cedula_identidad");
    const select_nacionalidad = document.getElementById("nacionalidad");
    const small_mensaje_cedula_identidad = document.getElementById("mensaje_cedula_identidad");

    const input_nombres_usuario = document.getElementById("nombres_usuario");
    const input_apellidos_usuario = document.getElementById("apellidos_usuario");

    const input_correo_electronico = document.getElementById("correo_electronico");
    const select_dominio = document.getElementById("dominio");
    const small_mensaje_correo_electronico = document.getElementById("mensaje_correo_electronico");

    const input_telefono = document.getElementById("numero_telefonico");
    const select_prefijo = document.getElementById("prefijo_telefono");

    const contenedorPnfsCoordinador = document.getElementById("contenedor_pnfs_coordinador_pnf");
    const contenedorPnfsDocente = document.getElementById("contenedor_pnfs_docente");
    const contenedorCheckboxPerfiles = document.getElementById("perfil");

    const contenedorCheckboxPNFsCoordinador = document.getElementById("pnf_coordinador_pnf");
    const contenedorCheckboxPNFsDocente = document.getElementById("pnf_docente");

    configurarCedula(select_nacionalidad, input_cedula_identidad);
    configurarCorreo(input_correo_electronico, select_dominio);
    configurarTelefono(input_telefono, select_prefijo);

    // ===================================

    let controlador_cedula = null;

    async function validarCedula(selectNacionalidad, inputCedula, mensaje) {

        const nacionalidad = selectNacionalidad.value;
        const cedula = inputCedula.value.trim();

        // Cancelar petición anterior
        if (controlador_cedula) {
            controlador_cedula.abort();
        }

        // Campo vacío
        if (!nacionalidad || !cedula) {
            mensaje.textContent = "";
            mensaje.classList.remove("exito", "error");

            inputCedula.setCustomValidity("");
            inputCedula.classList.remove("is-valid", "is-invalid");

            return;
        }

        let longitudMinima;
        let longitudMaxima;

        switch (nacionalidad) {
            case "V":
                longitudMinima = 7;
                longitudMaxima = 8;
                break;

            case "E":
                longitudMinima = 8;
                longitudMaxima = 10;
                break;

            default:
                return;
        }

        // Validar longitud antes de consultar al servidor
        if (
            cedula.length < longitudMinima ||
            cedula.length > longitudMaxima
        ) {
            mensaje.textContent = "";
            mensaje.classList.remove("exito", "error");

            inputCedula.setCustomValidity(
                `La cédula debe tener entre ${longitudMinima} y ${longitudMaxima} números.`
            );

            inputCedula.classList.remove("is-valid");
            inputCedula.classList.add("is-invalid");

            return;
        }

        controlador_cedula = new AbortController();

        try {
            const formulario = new FormData();

            formulario.append("nacionalidad", nacionalidad);
            formulario.append("cedula", cedula);

            const respuesta = await fetch("/validar_ci_usr/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector(
                        "[name=csrfmiddlewaretoken]"
                    ).value
                },
                body: formulario,
                signal: controlador_cedula.signal
            });

            const resultado = await respuesta.json();

            console.log(resultado);

            // Comprobar que los datos sigan siendo los mismos
            if (
                selectNacionalidad.value !== nacionalidad ||
                inputCedula.value.trim() !== cedula
            ) {
                return;
            }

            if (resultado.existe) {

                inputCedula.setCustomValidity(
                    "Ya se encuentra un usuario registrado con esta cédula de identidad."
                );

                inputCedula.classList.add("is-invalid");
                inputCedula.classList.remove("is-valid");

                mensaje.textContent =
                    "Ya se encuentra un usuario registrado con esta cédula de identidad.";

                mensaje.classList.add("error");
                mensaje.classList.remove("exito");

            } else {

                inputCedula.setCustomValidity("");

                inputCedula.classList.remove("is-invalid");
                inputCedula.classList.add("is-valid");

                mensaje.textContent =
                    "La cédula de identidad está disponible.";

                mensaje.classList.add("exito");
                mensaje.classList.remove("error");
            }

        } catch (error) {

            if (error.name === "AbortError") {
                return;
            }

            console.error(
                "Error al validar la cédula:",
                error
            );
        }
    }

    select_nacionalidad.addEventListener("change", async () => {
        await validarCedula(
            select_nacionalidad,
            input_cedula_identidad,
            small_mensaje_cedula_identidad
        );
    });

    input_cedula_identidad.addEventListener("input", async () => {

        input_cedula_identidad.value =
            input_cedula_identidad.value.replace(/\D/g, "");

        await validarCedula(
            select_nacionalidad,
            input_cedula_identidad,
            small_mensaje_cedula_identidad
        );
    });

    let controlador_correo = null;

    async function validar_correos(correo, dominio, msg) {

        const valorCorreo = correo.value.trim();
        const valorDominio = dominio.value;

        // Cancelar petición anterior
        if (controlador_correo) {
            controlador_correo.abort();
        }

        // Correo o dominio vacío
        if (!valorDominio || !valorCorreo) {
            msg.textContent = "";
            msg.classList.remove("exito", "error");

            correo.setCustomValidity("");
            correo.classList.remove("is-valid", "is-invalid");

            return;
        }

        controlador_correo = new AbortController();

        try {
            const formulario = new FormData();

            formulario.append("correo", valorCorreo);
            formulario.append("dominio", valorDominio);

            const respuesta = await fetch("/validar_email/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector(
                        "[name=csrfmiddlewaretoken]"
                    ).value
                },
                body: formulario,
                signal: controlador_correo.signal
            });

            const resultado = await respuesta.json();

            console.log(resultado);

            // Comprobar que el correo y dominio sigan siendo los mismos
            if (
                correo.value.trim() !== valorCorreo ||
                dominio.value !== valorDominio
            ) {
                return;
            }

            if (resultado.existe) {

                correo.setCustomValidity(
                    "Ya existe un usuario con este correo electrónico."
                );

                correo.classList.add("is-invalid");
                correo.classList.remove("is-valid");

                msg.textContent =
                    "Ya existe un usuario con este correo electrónico.";

                msg.classList.add("error");
                msg.classList.remove("exito");

            } else {

                correo.setCustomValidity("");

                correo.classList.add("is-valid");
                correo.classList.remove("is-invalid");

                msg.textContent =
                    "El correo electrónico está disponible.";

                msg.classList.add("exito");
                msg.classList.remove("error");
            }

        } catch (error) {

            if (error.name === "AbortError") {
                return;
            }

            console.error(
                "Error al validar el correo electrónico:",
                error
            );
        }
    }

    input_correo_electronico.addEventListener("input", async () => {

        await validar_correos(
            input_correo_electronico,
            select_dominio,
            small_mensaje_correo_electronico
        );
    });

    select_dominio.addEventListener("change", async () => {

        await validar_correos(
            input_correo_electronico,
            select_dominio,
            small_mensaje_correo_electronico
        );
    });

    function soloTexto(input) {
        input.value = input.value.replace(/[^a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s]/g, '');
    }

    input_nombres_usuario.addEventListener("input", () => {
        soloTexto(input_nombres_usuario);
    });

    input_apellidos_usuario.addEventListener("input", () => {
        soloTexto(input_apellidos_usuario);
    });

    // ==================================

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

    function ocultar_elementos() {
        contenedorPnfsCoordinador.style.display = "none";
        contenedorPnfsDocente.style.display = "none";
    }
    ocultar_elementos();

    async function cargar_perfiles_disponibles() {
        try {
            const respuesta = await fetch("/datos_perfiles/");
            const resultado = await respuesta.json();

            contenedorCheckboxPerfiles.innerHTML = "";

            resultado.perfiles.forEach(perfil => {
                const label = document.createElement("label");
                label.style.display = "block";

                const checkbox = document.createElement("input");
                checkbox.type = "checkbox";
                checkbox.name = "perfil";
                checkbox.value = perfil.id_perfil;
                checkbox.dataset.perfil = perfil.perfil;

                label.appendChild(checkbox);
                label.append(" " + perfil.perfil);

                contenedorCheckboxPerfiles.appendChild(label);
            });
        } catch (error) {
            console.error(error);
        }
    }
    cargar_perfiles_disponibles();

    // Obtener todos los pnfs y crear todos los checkbox
    async function cargar_pnf_disponible(contenedorPnf, nombrePnf, idPerfil) {

        contenedorPnf.innerHTML = "";

        const respuesta = await fetch("/pnfs_disp/", {
            method: "POST",
            headers: {
                "X-CSRFToken": getCookie("csrftoken")
            },
            body: JSON.stringify({
                id_perfil: idPerfil
            })
        });

        const resultado = await respuesta.json();

        resultado.pnfs.forEach(pnf => {

            const label = document.createElement("label");
            label.style.display = "block";

            const check = document.createElement("input");
            check.type = "checkbox";
            check.name = nombrePnf;
            check.value = pnf.id_pnf;

            label.appendChild(check);
            label.append(" " + pnf.pnf);

            contenedorPnf.appendChild(label);
        });
    }

    document.addEventListener("change", async function (e) {
        if (e.target.name !== "perfil")
            return;

        const perfil = e.target.dataset.perfil;
        const idPerfil = parseInt(e.target.value);

        if (perfil === "Coordinador PNF") {
            contenedorPnfsCoordinador.style.display = e.target.checked ? "block" : "none";

            if (e.target.checked) {
                await cargar_pnf_disponible(contenedorCheckboxPNFsCoordinador, "pnf_coordinador_pnf", idPerfil);
            } else {
                contenedorCheckboxPNFsCoordinador.innerHTML = "";
            }
        }

        if (perfil === "Docente") {
            contenedorPnfsDocente.style.display = e.target.checked ? "block" : "none";
            if (e.target.checked) {
                await cargar_pnf_disponible(contenedorCheckboxPNFsDocente, "pnf_docente", idPerfil);
            } else {
                contenedorCheckboxPNFsDocente.innerHTML = "";
            }
        }
    });

    // =========================================

    formulario_registrar.addEventListener("submit", async function (e) {
        e.preventDefault();
        try {
            const formulario = new FormData(formulario_registrar);

            const respuesta = await fetch("/pre_reg_personal/", {
                method: "POST",
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

            if (resultado.estado == "exito") {
                formulario_registrar.reset();
                small_mensaje_cedula_identidad.innerHTML = "";
                small_mensaje_correo_electronico.innerHTML = "";

                contenedorPnfsCoordinador.style.display = "none";
                contenedorPnfsDocente.style.display = "none";

                await cargar_perfiles_disponibles()
            }
        } catch (error) {
            console.error(error);
        }
    });

});