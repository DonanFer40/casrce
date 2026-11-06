
document.addEventListener("DOMContentLoaded", () => {

    // =========================================================
    // ELEMENTOS DEL FORMULARIO
    // =========================================================

    const formulario_registrar =
        document.getElementById("formulario_registrar");

    const input_cedula_identidad =
        document.getElementById("cedula_identidad");

    const select_nacionalidad =
        document.getElementById("nacionalidad");

    const small_mensaje_cedula_identidad =
        document.getElementById("mensaje_cedula_identidad");

    const input_nombres_usuario =
        document.getElementById("nombres_usuario");

    const input_apellidos_usuario =
        document.getElementById("apellidos_usuario");

    const input_correo_electronico =
        document.getElementById("correo_electronico");

    const select_dominio =
        document.getElementById("dominio");

    const small_mensaje_correo_electronico =
        document.getElementById("mensaje_correo_electronico");

    const input_telefono =
        document.getElementById("numero_telefonico");

    const select_prefijo =
        document.getElementById("prefijo_telefono");

    const contenedorPnfsCoordinador =
        document.getElementById("contenedor_pnfs_coordinador_pnf");

    const contenedorPnfsDocente =
        document.getElementById("contenedor_pnfs_docente");

    const contenedorCheckboxPerfiles =
        document.getElementById("perfil");

    const contenedorCheckboxPNFsCoordinador =
        document.getElementById("pnf_coordinador_pnf");

    const contenedorCheckboxPNFsDocente =
        document.getElementById("pnf_docente");

    const small_mensaje_telefono =
        document.getElementById("mensaje_telefono");

    if (
        !formulario_registrar ||
        !contenedorCheckboxPerfiles ||
        !contenedorPnfsCoordinador ||
        !contenedorPnfsDocente ||
        !contenedorCheckboxPNFsCoordinador ||
        !contenedorCheckboxPNFsDocente
    ) {
        console.error(
            "No se encontraron todos los elementos necesarios del formulario."
        );
        return;
    }

    // =========================================================
    // CONFIGURACIONES EXISTENTES
    // =========================================================

    configurarCedula(
        select_nacionalidad,
        input_cedula_identidad
    );

    configurarCorreo(
        input_correo_electronico,
        select_dominio
    );

    configurarTelefono(
        input_telefono,
        select_prefijo
    );

    // =========================================================
    // CSRF
    // =========================================================

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

    function obtenerCSRFToken() {

        return (
            document.querySelector(
                "[name=csrfmiddlewaretoken]"
            )?.value ||
            getCookie("csrftoken")
        );
    }

    // =========================================================
    // NOTIFICACIONES
    // =========================================================

    async function mostrarNotificacion(
        title,
        text,
        icon = "warning"
    ) {

        if (
            typeof NotificacionesCASRCE !== "undefined" &&
            typeof NotificacionesCASRCE.mostrar === "function"
        ) {

            await NotificacionesCASRCE.mostrar({
                title,
                text,
                icon,
                allowOutsideClick: false,
                allowEscapeKey: false
            });

        } else {

            alert(`${title}\n\n${text}`);
        }
    }

    // =========================================================
    // VALIDACIÓN DE CÉDULA
    // =========================================================

    let controlador_cedula = null;

    async function validarCedula(
        selectNacionalidad,
        inputCedula,
        mensaje
    ) {

        const nacionalidad = selectNacionalidad.value;
        const cedula = inputCedula.value.trim();

        if (controlador_cedula) {
            controlador_cedula.abort();
        }

        if (!nacionalidad || !cedula) {

            mensaje.textContent = "";

            mensaje.classList.remove(
                "exito",
                "error"
            );

            inputCedula.setCustomValidity("");

            inputCedula.classList.remove(
                "is-valid",
                "is-invalid"
            );

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

        if (
            cedula.length < longitudMinima ||
            cedula.length > longitudMaxima
        ) {

            mensaje.textContent = "";

            mensaje.classList.remove(
                "exito",
                "error"
            );

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

            const respuesta = await fetch(
                "/validar_ci_usr/",
                {
                    method: "POST",

                    headers: {
                        "X-CSRFToken": obtenerCSRFToken()
                    },

                    body: formulario,

                    signal: controlador_cedula.signal
                }
            );

            if (!respuesta.ok) {
                throw new Error(
                    "No fue posible validar la cédula."
                );
            }

            const resultado = await respuesta.json();

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

    select_nacionalidad.addEventListener(
        "change",
        async () => {

            await validarCedula(
                select_nacionalidad,
                input_cedula_identidad,
                small_mensaje_cedula_identidad
            );
        }
    );

    input_cedula_identidad.addEventListener(
        "input",
        async () => {

            input_cedula_identidad.value =
                input_cedula_identidad.value.replace(
                    /\D/g,
                    ""
                );

            await validarCedula(
                select_nacionalidad,
                input_cedula_identidad,
                small_mensaje_cedula_identidad
            );
        }
    );

    // =========================================================
    // VALIDACIÓN DE CORREO
    // =========================================================

    let controlador_correo = null;

    async function validar_correos(
        correo,
        dominio,
        msg
    ) {

        const valorCorreo = correo.value.trim();
        const valorDominio = dominio.value;

        if (controlador_correo) {
            controlador_correo.abort();
        }

        if (!valorDominio || !valorCorreo) {

            msg.textContent = "";

            msg.classList.remove(
                "exito",
                "error"
            );

            correo.setCustomValidity("");

            correo.classList.remove(
                "is-valid",
                "is-invalid"
            );

            return;
        }

        controlador_correo = new AbortController();

        try {

            const formulario = new FormData();

            formulario.append("correo", valorCorreo);
            formulario.append("dominio", valorDominio);

            const respuesta = await fetch(
                "/validar_email/",
                {
                    method: "POST",

                    headers: {
                        "X-CSRFToken": obtenerCSRFToken()
                    },

                    body: formulario,

                    signal: controlador_correo.signal
                }
            );

            if (!respuesta.ok) {
                throw new Error(
                    "No fue posible validar el correo electrónico."
                );
            }

            const resultado = await respuesta.json();

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

    input_correo_electronico.addEventListener(
        "input",
        async () => {

            await validar_correos(
                input_correo_electronico,
                select_dominio,
                small_mensaje_correo_electronico
            );
        }
    );

    select_dominio.addEventListener(
        "change",
        async () => {

            await validar_correos(
                input_correo_electronico,
                select_dominio,
                small_mensaje_correo_electronico
            );
        }
    );

    // =========================================================
    // VALIDACIÓN DE TELÉFONO
    // =========================================================

    let controlador_telefono = null;

    async function validar_telefono() {

    const prefijo = select_prefijo.value;
    const telefono = input_telefono.value.trim();

    console.log("Prefijo:", prefijo);
    console.log("Teléfono:", telefono);
    console.log("Longitud:", telefono.length);
    console.log("Solo números:", /^\d{7}$/.test(telefono));

    // =====================================================
    // CANCELAR VALIDACIÓN ANTERIOR
    // =====================================================

    if (controlador_telefono) {
        controlador_telefono.abort();
        controlador_telefono = null;
    }

    // =====================================================
    // VALIDAR CAMPOS VACÍOS
    // =====================================================

    if (!prefijo || !telefono) {

        small_mensaje_telefono.textContent = "";

        small_mensaje_telefono.classList.remove(
            "exito",
            "error",
            "pendiente"
        );

        input_telefono.setCustomValidity("");

        input_telefono.classList.remove(
            "is-valid",
            "is-invalid"
        );

        return;
    }

    // =====================================================
    // VALIDAR FORMATO DEL NÚMERO
    // =====================================================

    if (!/^\d{7}$/.test(telefono)) {

        const mensaje =
            "El número telefónico debe contener exactamente 7 dígitos.";

        small_mensaje_telefono.textContent = mensaje;

        small_mensaje_telefono.classList.add("error");

        small_mensaje_telefono.classList.remove(
            "exito",
            "pendiente"
        );

        input_telefono.setCustomValidity(mensaje);

        input_telefono.classList.add("is-invalid");
        input_telefono.classList.remove("is-valid");

        return;
    }

    // =====================================================
    // PREPARAR CONSULTA
    // =====================================================

    const controlador_actual = new AbortController();

    controlador_telefono = controlador_actual;

    input_telefono.setCustomValidity(
        "Espera mientras comprobamos la disponibilidad del teléfono."
    );

    input_telefono.classList.add("is-invalid");
    input_telefono.classList.remove("is-valid");

    small_mensaje_telefono.textContent =
        "Comprobando disponibilidad del número telefónico...";

    small_mensaje_telefono.classList.add("pendiente");

    small_mensaje_telefono.classList.remove(
        "exito",
        "error"
    );

    try {

        // =================================================
        // PREPARAR DATOS Y TOKEN CSRF
        // =================================================

        const formulario = new FormData();

        formulario.append("prefijo", prefijo);
        formulario.append("telefono", telefono);

        // =================================================
        // CONSULTAR DISPONIBILIDAD
        // =================================================

        const respuesta = await fetch(
            "/validar_telefono/",
            {
                method: "POST",

                headers: {
                    "X-CSRFToken": obtenerCSRFToken()
                },

                body: formulario,

                signal: controlador_actual.signal
            }
        );

        if (!respuesta.ok) {
            throw new Error(
                "No fue posible validar el número telefónico."
            );
        }

        const resultado = await respuesta.json();

        // =================================================
        // COMPROBAR QUE LA CONSULTA SIGA SIENDO VÁLIDA
        // =================================================

        if (
            controlador_telefono !== controlador_actual ||
            select_prefijo.value !== prefijo ||
            input_telefono.value.trim() !== telefono
        ) {
            return;
        }

        // =================================================
        // NÚMERO YA REGISTRADO
        // =================================================

        if (resultado.existe) {

            const mensaje =
                "Este número telefónico ya se encuentra registrado.";

            input_telefono.setCustomValidity(mensaje);

            input_telefono.classList.add("is-invalid");
            input_telefono.classList.remove("is-valid");

            small_mensaje_telefono.textContent = mensaje;

            small_mensaje_telefono.classList.add("error");

            small_mensaje_telefono.classList.remove(
                "exito",
                "pendiente"
            );

        }

        // =================================================
        // NÚMERO DISPONIBLE
        // =================================================

        else {

            input_telefono.setCustomValidity("");

            input_telefono.classList.remove("is-invalid");
            input_telefono.classList.add("is-valid");

            small_mensaje_telefono.textContent =
                "El número telefónico está disponible.";

            small_mensaje_telefono.classList.add("exito");

            small_mensaje_telefono.classList.remove(
                "error",
                "pendiente"
            );
        }

    } catch (error) {

        // =============================================
        // IGNORAR PETICIONES CANCELADAS
        // =============================================

        if (error.name === "AbortError") {
            return;
        }

        // =============================================
        // MOSTRAR ERROR DE VALIDACIÓN
        // =============================================

        console.error(
            "Error al validar el teléfono:",
            error
        );

        // Evitar modificar un campo que ya cambió.
        if (
            controlador_telefono !== controlador_actual ||
            select_prefijo.value !== prefijo ||
            input_telefono.value.trim() !== telefono
        ) {
            return;
        }

        const mensaje =
            "No fue posible comprobar la disponibilidad del teléfono.";

        input_telefono.setCustomValidity(mensaje);

        input_telefono.classList.add("is-invalid");
        input_telefono.classList.remove("is-valid");

        small_mensaje_telefono.textContent =
            "No fue posible comprobar el número. Inténtalo nuevamente.";

        small_mensaje_telefono.classList.add("error");

        small_mensaje_telefono.classList.remove(
            "exito",
            "pendiente"
        );

    } finally {

        // =============================================
        // LIBERAR CONTROLADOR DE LA CONSULTA ACTUAL
        // =============================================

        if (controlador_telefono === controlador_actual) {
            controlador_telefono = null;
        }
    }
}


// =========================================================
// EVENTOS DE VALIDACIÓN
// =========================================================

input_telefono.addEventListener(
    "input",
    validar_telefono
);

select_prefijo.addEventListener(
    "change",
    validar_telefono
);

    // =========================================================
    // CONTENEDORES DE PNF
    // =========================================================

    function ocultar_elementos() {

        contenedorPnfsCoordinador.style.display = "none";
        contenedorPnfsDocente.style.display = "none";
    }

    function limpiar_pnfs() {

        contenedorCheckboxPNFsCoordinador.innerHTML = "";
        contenedorCheckboxPNFsDocente.innerHTML = "";

        ocultar_elementos();
    }

    limpiar_pnfs();

    // =========================================================
    // CARGAR PERFILES DISPONIBLES
    // =========================================================

    async function cargar_perfiles_disponibles() {

        try {

            const respuesta = await fetch(
                "/datos_perfiles/",
                {
                    method: "GET",
                    headers: {
                        "X-Requested-With": "XMLHttpRequest"
                    }
                }
            );

            if (!respuesta.ok) {
                throw new Error(
                    "No fue posible consultar los perfiles."
                );
            }

            const resultado = await respuesta.json();

            if (!Array.isArray(resultado.perfiles)) {
                throw new Error(
                    "La respuesta de perfiles no tiene un formato válido."
                );
            }

            contenedorCheckboxPerfiles.innerHTML = "";

            limpiar_pnfs();

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

            console.error(
                "Error al cargar los perfiles:",
                error
            );

            await mostrarNotificacion(
                "Error al cargar perfiles",
                "No fue posible consultar los perfiles disponibles. Actualiza la página e intenta nuevamente.",
                "error"
            );
        }
    }

    // =========================================================
    // CARGAR PNF DISPONIBLES
    // =========================================================

    async function cargar_pnf_disponible(
        contenedorPnf,
        nombrePnf,
        idPerfil
    ) {

        contenedorPnf.innerHTML = "";

        const respuesta = await fetch(
            "/pnfs_disp/",
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": obtenerCSRFToken()
                },

                body: JSON.stringify({
                    id_perfil: idPerfil
                })
            }
        );

        const resultado = await respuesta.json();

        if (!respuesta.ok) {

            throw new Error(
                resultado.error ||
                "No fue posible consultar los PNF disponibles."
            );
        }

        if (!Array.isArray(resultado.pnfs)) {

            throw new Error(
                "La respuesta de PNF no tiene un formato válido."
            );
        }

        // No hay PNF disponibles.
        if (resultado.pnfs.length === 0) {

            return false;
        }

        resultado.pnfs.forEach(pnf => {

            const label = document.createElement("label");

            label.className = "pnf-opcion";

            const radio = document.createElement("input");

            radio.type = "radio";
            radio.name = nombrePnf;
            radio.value = pnf.id_pnf;

            radio.className = "pnf-opcion-radio";

            // Icono del PNF.
            const icono = document.createElement("i");

            icono.className = "fa-solid";

            const iconoServidor =
                typeof pnf.icono === "string"
                    ? pnf.icono.trim()
                    : "fa-graduation-cap";

            // Se agrega únicamente una clase de icono.
            const claseIcono = /^fa-[a-z0-9-]+$/.test(
                iconoServidor
            )
                ? iconoServidor
                : "fa-graduation-cap";

            icono.classList.add(claseIcono);
            icono.classList.add("pnf-opcion-icono");

            // Nombre del PNF.
            const nombre = document.createElement("span");

            nombre.className = "pnf-opcion-nombre";
            nombre.textContent = pnf.pnf;

            label.appendChild(radio);
            label.appendChild(icono);
            label.appendChild(nombre);

            contenedorPnf.appendChild(label);
        });

        return true;
    }

    // =========================================================
    // GESTIÓN DE PERFILES Y SUS PNF
    // =========================================================

    document.addEventListener(
        "change",
        async function (e) {

            if (
                !e.target.matches(
                    'input[name="perfil"]'
                )
            ) {
                return;
            }

            const checkboxPerfil = e.target;

            const perfil = checkboxPerfil.dataset.perfil;

            const idPerfil = parseInt(
                checkboxPerfil.value,
                10
            );

            // -------------------------------------------------
            // COORDINADOR PNF
            // -------------------------------------------------

            if (perfil === "Coordinador PNF") {

                if (!checkboxPerfil.checked) {

                    contenedorPnfsCoordinador.style.display = "none";

                    contenedorCheckboxPNFsCoordinador.innerHTML = "";

                    return;
                }

                contenedorPnfsCoordinador.style.display = "block";

                contenedorCheckboxPNFsCoordinador.innerHTML = "";

                try {

                    const existenPnfs = await cargar_pnf_disponible(
                        contenedorCheckboxPNFsCoordinador,
                        "pnf_coordinador_pnf",
                        idPerfil
                    );

                    // Comprobar que el perfil siga seleccionado.
                    if (!checkboxPerfil.checked) {
                        return;
                    }

                    // Si no hay PNF disponibles, retirar el perfil.
                    if (!existenPnfs) {

                        checkboxPerfil.checked = false;

                        contenedorPnfsCoordinador.style.display = "none";

                        contenedorCheckboxPNFsCoordinador.innerHTML = "";

                        const etiqueta = checkboxPerfil.closest("label");

                        if (etiqueta) {
                            etiqueta.remove();
                        }

                        await mostrarNotificacion(
                            "Sin PNF disponibles",
                            "Todos los PNF de este núcleo ya tienen un Coordinador asignado. El perfil Coordinador PNF dejará de estar disponible.",
                            "info"
                        );
                    }

                } catch (error) {

                    console.error(
                        "Error al cargar PNF para Coordinador:",
                        error
                    );

                    checkboxPerfil.checked = false;

                    contenedorPnfsCoordinador.style.display = "none";

                    contenedorCheckboxPNFsCoordinador.innerHTML = "";

                    await mostrarNotificacion(
                        "Error al consultar PNF",
                        error.message,
                        "error"
                    );
                }
            }

            // -------------------------------------------------
            // DOCENTE
            // -------------------------------------------------

            if (perfil === "Docente") {

                if (!checkboxPerfil.checked) {

                    contenedorPnfsDocente.style.display = "none";

                    contenedorCheckboxPNFsDocente.innerHTML = "";

                    return;
                }

                contenedorPnfsDocente.style.display = "block";

                contenedorCheckboxPNFsDocente.innerHTML = "";

                try {

                    const existenPnfs = await cargar_pnf_disponible(
                        contenedorCheckboxPNFsDocente,
                        "pnf_docente",
                        idPerfil
                    );

                    if (!checkboxPerfil.checked) {
                        return;
                    }

                    if (!existenPnfs) {

                        checkboxPerfil.checked = false;

                        contenedorPnfsDocente.style.display = "none";

                        contenedorCheckboxPNFsDocente.innerHTML = "";

                        await mostrarNotificacion(
                            "Sin PNF disponibles",
                            "No existen PNF asociados al núcleo para asignar el perfil Docente.",
                            "warning"
                        );
                    }

                } catch (error) {

                    console.error(
                        "Error al cargar PNF para Docente:",
                        error
                    );

                    checkboxPerfil.checked = false;

                    contenedorPnfsDocente.style.display = "none";

                    contenedorCheckboxPNFsDocente.innerHTML = "";

                    await mostrarNotificacion(
                        "Error al consultar PNF",
                        error.message,
                        "error"
                    );
                }
            }
        }
    );

    // =========================================================
    // CARGA INICIAL DE PERFILES
    // =========================================================

    cargar_perfiles_disponibles();

    // =========================================================
    // REGISTRAR PERSONAL
    // =========================================================

    let formulario_enviando = false;

    formulario_registrar.addEventListener(
        "submit",
        async function (e) {

            e.preventDefault();

            // Evitar envíos múltiples.
            if (formulario_enviando) {
                return;
            }

            // Validación HTML nativa.
            if (!formulario_registrar.reportValidity()) {
                return;
            }

            formulario_enviando = true;

            const botonEnviar = formulario_registrar.querySelector(
                'button[type="submit"], input[type="submit"]'
            );

            if (botonEnviar) {
                botonEnviar.disabled = true;
            }

            try {

                const formulario = new FormData(
                    formulario_registrar
                );

                const respuesta = await fetch(
                    "/pre_reg_personal/",
                    {
                        method: "POST",

                        headers: {
                            "X-CSRFToken": obtenerCSRFToken()
                        },

                        body: formulario
                    }
                );

                const resultado = await respuesta.json();

                if (!respuesta.ok) {

                    throw new Error(
                        resultado.descripcion ||
                        resultado.error ||
                        "No fue posible completar el registro."
                    );
                }

                console.log(resultado);

                await mostrarNotificacion(
                    resultado.title || "Resultado del registro",
                    resultado.descripcion || "No se recibió una descripción del servidor.",
                    resultado.icon || "info"
                );

                // -------------------------------------------------
                // REGISTRO EXITOSO
                // -------------------------------------------------

                if (resultado.estado === "exito") {

                    formulario_registrar.reset();

                    small_mensaje_telefono.textContent = "";
                    small_mensaje_cedula_identidad.textContent = "";
                    small_mensaje_correo_electronico.textContent = "";

                    small_mensaje_cedula_identidad.classList.remove(
                        "exito",
                        "error"
                    );

                    small_mensaje_telefono.classList.remove(
                        "exito",
                        "error",
                        "pendiente"
                    );

                    small_mensaje_correo_electronico.classList.remove(
                        "exito",
                        "error"
                    );

                    input_telefono.setCustomValidity("");
                    input_cedula_identidad.setCustomValidity("");
                    input_correo_electronico.setCustomValidity("");

                    input_cedula_identidad.classList.remove(
                        "is-valid",
                        "is-invalid"
                    );

                    input_correo_electronico.classList.remove(
                        "is-valid",
                        "is-invalid"
                    );

                    input_telefono.classList.remove(
                        "is-valid",
                        "is-invalid"
                    );

                    limpiar_pnfs();

                    // Volver a consultar los perfiles.
                    // Coordinador PNF desaparecerá si ya no
                    // existen PNF disponibles.
                    await cargar_perfiles_disponibles();
                }

            } catch (error) {

                console.error(
                    "Error al registrar personal:",
                    error
                );

                await mostrarNotificacion(
                    "Error de registro",
                    error.message ||
                    "Ocurrió un problema al comunicarse con el servidor.",
                    "error"
                );

            } finally {

                formulario_enviando = false;

                if (botonEnviar) {
                    botonEnviar.disabled = false;
                }
            }
        }
    );

});
