
document.addEventListener("DOMContentLoaded", () => {

    // =========================================================
    // FORMULARIOS
    // =========================================================

    const formulario_buscar_usuario =
        document.getElementById("buscar_usuario");

    const formulario_registrar_credenciales =
        document.getElementById("formulario_registrar_credenciales");

    const formulario_codigo =
        document.getElementById("formulario_codigo_personal");


    // =========================================================
    // BLOQUES
    // =========================================================

    const paso_busqueda =
        document.getElementById("RegistroPersonalCASRCE-paso-busqueda");

    const modal_verificacion =
        document.getElementById("modal_verificacion_personal");


    // =========================================================
    // BÚSQUEDA
    // =========================================================

    const select_nacionalidad =
        document.getElementById("nacionalidad");

    const input_CI =
        document.getElementById("cedula_identidad") ||
        document.getElementById("usuario_ci");

    const btn_buscar_usuario =
        document.getElementById("validar_usuario");


    // =========================================================
    // CREDENCIALES
    // =========================================================

    const input_nombre_usuario =
        document.getElementById("nombre_usuario");

    const input_password =
        document.getElementById("password");

    const btn_registro =
        document.getElementById("btn_registro");


    // =========================================================
    // MOSTRAR / OCULTAR CONTRASEÑA
    // =========================================================

    const input_check_oculta_aparecer =
        document.getElementById("OcultaAparecer");

    const tag_i_mostrar =
        document.getElementById("aparecer_oculta");

    const tag_i_ocultar =
        document.getElementById("oculta_aparecer");


    // =========================================================
    // VERIFICACIÓN
    // =========================================================

    const input_codigo =
        document.getElementById("codigo_verificacion_personal");

    const btn_verificar_codigo =
        document.getElementById("btn_verificar_codigo_personal");

    const btn_reenviar_codigo =
        document.getElementById("btn_reenviar_codigo_personal");

    const texto_correo =
        document.getElementById("correo_verificacion_personal");

    const texto_contador =
        document.getElementById("contador_reenvio_personal");


    // =========================================================
    // ESTADO
    // =========================================================

    let intervalo_reenvio = null;
    let segundos_reenvio = 0;
    let verificacion_completada = false;


    // =========================================================
    // VALIDACIÓN DE ELEMENTOS
    // =========================================================

    if (
        !formulario_buscar_usuario ||
        !formulario_registrar_credenciales ||
        !formulario_codigo ||
        !paso_busqueda ||
        !modal_verificacion ||
        !select_nacionalidad ||
        !input_CI ||
        !input_codigo
    ) {
        console.error(
            "No se encontraron todos los elementos necesarios para el registro de personal."
        );
        return;
    }


    // =========================================================
    // CSRF
    // =========================================================

    function obtenerCSRFToken() {

        const campo = document.querySelector(
            '[name="csrfmiddlewaretoken"]'
        );

        if (campo && campo.value) {
            return campo.value;
        }

        const cookies = document.cookie.split(";");

        for (const cookie of cookies) {

            const elemento = cookie.trim();

            if (elemento.startsWith("csrftoken=")) {
                return decodeURIComponent(
                    elemento.substring("csrftoken=".length)
                );
            }
        }

        return "";
    }


    // =========================================================
    // PETICIÓN JSON
    // =========================================================

    async function enviarFormulario(url, datos) {

        const csrfToken = obtenerCSRFToken();

        const respuesta = await fetch(url, {
            method: "POST",
            body: datos,
            credentials: "same-origin",
            headers: {
                "X-Requested-With": "XMLHttpRequest",
                "X-CSRFToken": csrfToken
            }
        });

        const resultado = await respuesta.json();

        if (!respuesta.ok) {
            throw new Error(
                resultado.descripcion ||
                "No fue posible completar la solicitud."
            );
        }

        return resultado;
    }


    async function enviarSolicitud(url) {

        const csrfToken = obtenerCSRFToken();

        const respuesta = await fetch(url, {
            method: "POST",
            credentials: "same-origin",
            headers: {
                "X-Requested-With": "XMLHttpRequest",
                "X-CSRFToken": csrfToken
            }
        });

        const resultado = await respuesta.json();

        if (!respuesta.ok) {
            throw new Error(
                resultado.descripcion ||
                "No fue posible completar la solicitud."
            );
        }

        return resultado;
    }


    // =========================================================
    // CONFIGURACIÓN DE CÉDULA
    // =========================================================

    if (typeof configurarCedula === "function") {

        configurarCedula(
            select_nacionalidad,
            input_CI
        );

    }


    // =========================================================
    // ESTADO INICIAL
    // =========================================================

    paso_busqueda.hidden = false;

    formulario_registrar_credenciales.hidden = true;

    modal_verificacion.hidden = true;


    // =========================================================
    // NOTIFICACIONES
    // =========================================================

    function notificar(resultado) {

        if (
            typeof NotificacionesCASRCE === "undefined"
        ) {
            alert(
                resultado.descripcion ||
                resultado.title ||
                "Información"
            );
            return;
        }

        const tipo = resultado.icon || "info";

        const mensaje =
            resultado.descripcion ||
            resultado.title ||
            "Información";

        switch (tipo) {

            case "success":
                NotificacionesCASRCE.exito(mensaje);
                break;

            case "error":
                NotificacionesCASRCE.error(mensaje);
                break;

            case "warning":
                NotificacionesCASRCE.advertencia(mensaje);
                break;

            default:
                NotificacionesCASRCE.informacion(mensaje);
                break;
        }
    }


    // =========================================================
    // TEMPORIZADOR DE REENVÍO
    // =========================================================

    function detenerTemporizador() {

        if (intervalo_reenvio) {

            clearInterval(intervalo_reenvio);

            intervalo_reenvio = null;

        }
    }


    function actualizarContador() {

        if (!texto_contador) return;

        const minutos = Math.floor(segundos_reenvio / 60);

        const segundos = segundos_reenvio % 60;

        texto_contador.textContent =
            `Podrás reenviar el código en ${minutos}:` +
            `${String(segundos).padStart(2, "0")}`;
    }


    function iniciarTemporizador(segundos = 60) {

        detenerTemporizador();

        segundos_reenvio = segundos;

        if (btn_reenviar_codigo) {
            btn_reenviar_codigo.disabled = true;
        }

        actualizarContador();

        intervalo_reenvio = setInterval(() => {

            segundos_reenvio--;

            actualizarContador();

            if (segundos_reenvio <= 0) {

                detenerTemporizador();

                if (btn_reenviar_codigo) {
                    btn_reenviar_codigo.disabled = false;
                }

                if (texto_contador) {
                    texto_contador.textContent =
                        "Ya puedes solicitar otro código.";
                }
            }

        }, 1000);
    }


    // =========================================================
    // ABRIR MODAL DE VERIFICACIÓN
    // =========================================================

    function abrirModalVerificacion(correo) {

        verificacion_completada = false;

        formulario_codigo.reset();

        modal_verificacion.hidden = false;

        formulario_registrar_credenciales.hidden = true;

        paso_busqueda.hidden = false;

        if (texto_correo) {

            texto_correo.textContent =
                correo || "tu correo registrado";

        }

        iniciarTemporizador(60);

        input_codigo.focus();
    }


    // =========================================================
    // CERRAR MODAL
    // =========================================================

    function cerrarModalVerificacion() {

        modal_verificacion.hidden = true;

        detenerTemporizador();
    }

    // =========================================================
    // BUSCAR PERSONAL Y SOLICITAR VERIFICACIÓN
    // =========================================================

    formulario_buscar_usuario.addEventListener("submit", async (e) => {

        e.preventDefault();

        if (verificacion_completada) return;

        if (btn_buscar_usuario) {
            btn_buscar_usuario.disabled = true;
        }

        // Mostrar círculo de carga
        NotificacionesCASRCE.cargar("Enviando código de verificación...");

        try {

            const datos = new FormData(formulario_buscar_usuario);

            datos.set("usuario_ci", input_CI.value.trim());

            const resultado = await enviarFormulario(
                "/confirmar_reg/",
                datos
            );

            // Si el servidor confirma el envío del código
            if (resultado.estado === "verificacion_requerida") {

                // Cerrar el círculo de carga
                NotificacionesCASRCE.detenerCarga();

                // Abrir directamente el modal de verificación
                abrirModalVerificacion(resultado.correo);

                return;
            }

            // Si existe otro resultado, mostrar su notificación
            NotificacionesCASRCE.detenerCarga();

            await notificar(resultado);

        } catch (error) {

            console.error(
                "Error al solicitar la verificación del personal:",
                error
            );

            NotificacionesCASRCE.detenerCarga();

            await notificar({
                title: "Error de conexión",
                descripcion: error.message || "No fue posible procesar la solicitud.",
                icon: "error"
            });

        } finally {

            if (btn_buscar_usuario) {
                btn_buscar_usuario.disabled = false;
            }

        }

    });


    // =========================================================
    // VERIFICAR CÓDIGO
    // =========================================================

    formulario_codigo.addEventListener(
        "submit",
        async (e) => {

            e.preventDefault();

            const codigo = input_codigo.value.trim();

            if (!/^\d{6}$/.test(codigo)) {

                await notificar({
                    title: "Código inválido",
                    descripcion:
                        "Introduce los seis dígitos recibidos por correo.",
                    icon: "warning"
                });

                return;
            }

            if (btn_verificar_codigo) {
                btn_verificar_codigo.disabled = true;
            }

            try {

                // Se conserva el CSRF incluido en el formulario.
                const datos = new FormData(formulario_codigo);

                datos.set("codigo", codigo);

                const resultado = await enviarFormulario(
                    "/verificar_codigo_personal/",
                    datos
                );

                // ---------------------------------------------
                // VERIFICACIÓN EXITOSA
                // ---------------------------------------------

                if (resultado.estado === "exito") {

                    verificacion_completada = true;

                    cerrarModalVerificacion();

                    paso_busqueda.hidden = true;

                    formulario_registrar_credenciales.hidden = false;

                    formulario_registrar_credenciales.reset();

                    await notificar(resultado);

                    if (input_nombre_usuario) {
                        input_nombre_usuario.focus();
                    }

                    return;
                }


                // ---------------------------------------------
                // CÓDIGO VENCIDO
                // ---------------------------------------------

                if (resultado.estado === "expirado") {

                    input_codigo.value = "";

                    await notificar(resultado);

                    return;
                }


                // ---------------------------------------------
                // BLOQUEO
                // ---------------------------------------------

                if (resultado.estado === "bloqueado") {

                    detenerTemporizador();

                    if (btn_reenviar_codigo) {
                        btn_reenviar_codigo.disabled = true;
                    }

                    await notificar(resultado);

                    return;
                }


                // ---------------------------------------------
                // CÓDIGO INCORRECTO
                // ---------------------------------------------

                input_codigo.value = "";

                await notificar(resultado);

                // Recuperar el foco después de cerrar Notiflix.
                input_codigo.focus();

            } catch (error) {

                console.error(
                    "Error al verificar código:",
                    error
                );

                await notificar({
                    title: "Error de verificación",
                    descripcion:
                        error.message ||
                        "No fue posible verificar el código.",
                    icon: "error"
                });

            } finally {

                if (btn_verificar_codigo) {
                    btn_verificar_codigo.disabled = false;
                }
            }
        }
    );


    // =========================================================
    // REENVIAR CÓDIGO
    // =========================================================

    if (btn_reenviar_codigo) {

        btn_reenviar_codigo.addEventListener(
            "click",
            async () => {

                if (
                    segundos_reenvio > 0 ||
                    verificacion_completada
                ) {
                    return;
                }

                btn_reenviar_codigo.disabled = true;

                try {

                    const resultado = await enviarSolicitud(
                        "/reenviar_codigo_personal/"
                    );

                    if (
                        resultado.estado === "exito" ||
                        resultado.estado === "espera"
                    ) {

                        iniciarTemporizador(
                            resultado.segundos_reenvio || 60
                        );

                    } else {

                        btn_reenviar_codigo.disabled = false;

                    }

                    await notificar(resultado);

                } catch (error) {

                    console.error(
                        "Error al reenviar código:",
                        error
                    );

                    btn_reenviar_codigo.disabled = false;

                    await notificar({
                        title: "Error de conexión",
                        descripcion:
                            error.message ||
                            "No fue posible reenviar el código.",
                        icon: "error"
                    });
                }
            }
        );
    }


    // =========================================================
    // GUARDAR CREDENCIALES
    // =========================================================

    formulario_registrar_credenciales.addEventListener(
        "submit",
        async (e) => {

            e.preventDefault();

            // Protección adicional en el navegador.
            if (!verificacion_completada) {

                await notificar({
                    title: "Correo no verificado",
                    descripcion:
                        "Debes verificar tu correo antes de crear tus credenciales.",
                    icon: "warning"
                });

                return;
            }

            if (btn_registro) {
                btn_registro.disabled = true;
            }

            try {

                const datos = new FormData(
                    formulario_registrar_credenciales
                );

                // El backend espera exactamente password_usuario.
                if (input_password) {
                    datos.set(
                        "password_usuario",
                        input_password.value
                    );
                }

                const resultado = await enviarFormulario(
                    "/guardar_cred/",
                    datos
                );

                if (resultado.estado === "exito") {

                    verificacion_completada = false;

                    formulario_registrar_credenciales.hidden = true;

                    paso_busqueda.hidden = false;

                    formulario_registrar_credenciales.reset();

                    formulario_buscar_usuario.reset();

                    cerrarModalVerificacion();

                    await notificar(resultado);

                    return;
                }

                await notificar(resultado);

            } catch (error) {

                console.error(
                    "Error al guardar credenciales:",
                    error
                );

                await notificar({
                    title: "Error al guardar",
                    descripcion:
                        error.message ||
                        "No fue posible guardar las credenciales.",
                    icon: "error"
                });

            } finally {

                if (btn_registro) {
                    btn_registro.disabled = false;
                }
            }
        }
    );


    // =========================================================
    // MOSTRAR / OCULTAR CONTRASEÑA
    // =========================================================

    if (
        input_check_oculta_aparecer &&
        input_password
    ) {

        input_check_oculta_aparecer.addEventListener(
            "change",
            function () {

                input_password.type =
                    this.checked ? "text" : "password";

                if (tag_i_mostrar) {
                    tag_i_mostrar.hidden = this.checked;
                }

                if (tag_i_ocultar) {
                    tag_i_ocultar.hidden = !this.checked;
                }
            }
        );
    }


    // =========================================================
    // LIMPIEZA
    // =========================================================

    window.addEventListener("beforeunload", () => {

        detenerTemporizador();

    });

});
