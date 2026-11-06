document.addEventListener("DOMContentLoaded", () => {
    const formulario_registro = document.getElementById("formulario_registro");

    const select_nacionalidad = document.getElementById("nacionalidad");
    const input_cedula_identidad = document.getElementById("cedula_identidad");
    const mensaje_cedula_identidad = document.getElementById("mensaje_cedula_identidad");

    const input_correo_electronico = document.getElementById("correo_electronico");
    const select_dominio_correo = document.getElementById("dominio");
    const mensaje_correo_electronico = document.getElementById("mensaje_correo_electronico");

    const prefijo_telefono = document.getElementById("prefijo_telefono");
    const numero_telefonico = document.getElementById("numero_telefonico");

    const input_nombre_usuario = document.getElementById("nombre_usuario");
    const mensaje_nombre_usuario = document.getElementById("mensaje_nombre_usuario");
    
    const input_password = document.getElementById("password");
    const mensaje_password = document.getElementById("mensaje_password");

    const btn_registro = document.getElementById("btn_registro");

    configurarCedula(select_nacionalidad, input_cedula_identidad);
    configurarCorreo(input_correo_electronico, select_dominio_correo);
    configurarTelefono(numero_telefonico, prefijo_telefono);

    async function buscar_usuario(nacionalidad, cedula) {
        try {
            const formulario = new FormData();
            formulario.append("nacionalidad", nacionalidad);
            formulario.append("cedula", cedula);

            const respuesta = await fetch("/validar_ci_usr/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            if (resultado.existe == true) {
                input_cedula_identidad.setCustomValidity("Ya se encuentra un usuario registrado con esta cédula de identidad.");

                input_cedula_identidad.classList.add("is-invalid");
                input_cedula_identidad.classList.remove("is-valid");

                mensaje_cedula_identidad.textContent = "Ya se encuentra un usuario registrado con esta cédula de identidad.";
                mensaje_cedula_identidad.style.color = "#dc3545";

                btn_registro.disabled = true;
            }

            if (resultado.existe == false) {
                input_cedula_identidad.setCustomValidity("");

                input_cedula_identidad.classList.remove("is-invalid");
                input_cedula_identidad.classList.add("is-valid");

                mensaje_cedula_identidad.textContent = "La cédula de identidad está disponible.";
                mensaje_cedula_identidad.style.color = "#198754";

                btn_registro.disabled = false;
            }
        } catch (error) {
            console.error(error);
        }
    }
    
    select_nacionalidad.addEventListener("change", () => {
        if (!select_nacionalidad.value || !input_cedula_identidad.value.trim()) {
            mensaje_cedula_identidad.textContent = "";
            return;
        }

        buscar_usuario(select_nacionalidad.value, input_cedula_identidad.value);
    });

    input_cedula_identidad.addEventListener("input", () => {
        if (!select_nacionalidad.value || !input_cedula_identidad.value.trim()) {
            mensaje_cedula_identidad.textContent = "";
            return;
        }

        buscar_usuario(select_nacionalidad.value, input_cedula_identidad.value);
    });

    async function validar_correos(correo, dominio, msg) {
        try {
            const formulario = new FormData();
            formulario.append("correo", correo.value);
            formulario.append("dominio", dominio.value);

            const respuesta = await fetch("/validar_email/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            if (resultado.existe) {
                correo.setCustomValidity("Ya existe un usuario con este correo electrónico.");
                correo.classList.add("is-invalid");
                correo.classList.remove("is-valid");

                msg.textContent = "Ya existe un usuario con este correo electrónico.";
                msg.style.color = "#dc3545";

                btn_registro.disabled = true;
            } else {
                correo.setCustomValidity("");
                correo.classList.add("is-valid");
                correo.classList.remove("is-invalid");

                msg.textContent = "El correo electrónico está disponible.";
                msg.style.color = "#198754";

                btn_registro.disabled = false;
            }
        } catch (error) {
            console.error(error);
        }
    }

    input_correo_electronico.addEventListener("input", () => {
        if (!input_correo_electronico.value.trim() || !select_dominio_correo.value) {
            mensaje_correo_electronico.textContent = "";
            return;
        }

        validar_correos(input_correo_electronico, select_dominio_correo, mensaje_correo_electronico);
    });

    select_dominio_correo.addEventListener("change", () => {
        if (!input_correo_electronico.value.trim() || !select_dominio_correo.value) {
            mensaje_correo_electronico.textContent = "";
            return;
        }

        validar_correos(input_correo_electronico, select_dominio_correo, mensaje_correo_electronico);
    });
    
    async function buscar_nombre_usuario(nombre_usuario) {
        try {
            const formulario = new FormData();
            formulario.append("nombre_usuario", nombre_usuario);

            const respuesta = await fetch("/val_usuario/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);
            
            if (resultado.existe == true) {
                input_nombre_usuario.setCustomValidity("Ya se encuentra un usuario registrado con este nombre de usuario.");

                input_nombre_usuario.classList.add("is-invalid");
                input_nombre_usuario.classList.remove("is-valid");

                mensaje_nombre_usuario.textContent = "Ya se encuentra un usuario registrado con este nombre de usuario.";
                mensaje_nombre_usuario.style.color = "#dc3545";

                btn_registro.disabled = true;
            } else {
                input_nombre_usuario.setCustomValidity("");

                input_nombre_usuario.classList.remove("is-invalid");
                input_nombre_usuario.classList.add("is-valid");

                mensaje_nombre_usuario.textContent = "El nombre de usuario está disponible.";
                mensaje_nombre_usuario.style.color = "#198754";

                btn_registro.disabled = false;
            }
        } catch (error) {
            console.error(error);
        }
    }

    input_nombre_usuario.addEventListener("input", () => {
        if (!input_nombre_usuario.value.trim()) {
            mensaje_nombre_usuario.textContent = "";
            return;
        }

        buscar_nombre_usuario(input_nombre_usuario.value);
    });

    async function buscar_password(password) {
        try {
            const formulario = new FormData();
            formulario.append("password", password);

            const respuesta = await fetch("/val_password/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);
            
            if (resultado.existe == true) {
                input_password.setCustomValidity("Ya se encuentra un usuario registrado con esta contraseña.");

                input_password.classList.add("is-invalid");
                input_password.classList.remove("is-valid");

                mensaje_password.textContent = "Ya se encuentra un usuario registrado con esta contraseña.";
                mensaje_password.style.color = "#dc3545";

                btn_registro.disabled = true;
            } else {
                input_password.setCustomValidity("");

                input_password.classList.remove("is-invalid");
                input_password.classList.add("is-valid");

                mensaje_password.textContent = "La contraseña está disponible.";
                mensaje_password.style.color = "#198754";

                btn_registro.disabled = false;
            }
        } catch (error) {
            console.error(error);
        }
    }

    input_password.addEventListener("input", () => {
        if (!input_password.value.trim()) {
            mensaje_password.textContent = "";
            return;
        }

        buscar_password(input_password.value);
    });

    const modalVerificacion = document.getElementById("modal-verificacion-registro");
    const formularioVerificacion = document.getElementById("formulario-verificacion-registro");
    const inputCodigoVerificacion = document.getElementById("codigo-verificacion-registro");
    const mensajeVerificacion = document.getElementById("mensaje-verificacion-registro");
    const correoDestinoVerificacion = document.getElementById("correo-destino-verificacion");
    const btnConfirmarVerificacion = document.getElementById("btn-confirmar-verificacion");
    const btnReenviarCodigo = document.getElementById("btn-reenviar-codigo-registro");
    const textoTemporizadorReenvio = document.getElementById("texto-temporizador-reenvio");
    let temporizadorReenvio = null;
    let segundosReenvio = 0;

    function mostrarMensajeVerificacion(texto, tipo = "") {
        mensajeVerificacion.textContent = texto;
        mensajeVerificacion.dataset.tipo = tipo;
    }

    function abrirModalVerificacion(correo, segundos = 60) {
        correoDestinoVerificacion.textContent = correo;
        modalVerificacion.classList.add("activo");
        modalVerificacion.setAttribute("aria-hidden", "false");
        inputCodigoVerificacion.value = "";
        mostrarMensajeVerificacion("");
        iniciarTemporizadorReenvio(segundos);
        window.setTimeout(() => inputCodigoVerificacion.focus(), 100);
    }

    function cerrarModalVerificacion() {
        modalVerificacion.classList.remove("activo");
        modalVerificacion.setAttribute("aria-hidden", "true");
        if (temporizadorReenvio) window.clearInterval(temporizadorReenvio);
    }

    function iniciarTemporizadorReenvio(segundos) {
        if (temporizadorReenvio) window.clearInterval(temporizadorReenvio);
        segundosReenvio = Math.max(0, Number(segundos) || 0);
        btnReenviarCodigo.disabled = segundosReenvio > 0;
        actualizarTemporizador();
        temporizadorReenvio = window.setInterval(() => {
            if (segundosReenvio > 0) segundosReenvio--;
            actualizarTemporizador();
            if (segundosReenvio <= 0) window.clearInterval(temporizadorReenvio);
        }, 1000);
    }

    function actualizarTemporizador() {
        if (segundosReenvio > 0) {
            textoTemporizadorReenvio.textContent = `Puedes solicitar otro código en ${segundosReenvio} segundo(s).`;
            btnReenviarCodigo.disabled = true;
        } else {
            textoTemporizadorReenvio.textContent = "¿No recibiste el correo?";
            btnReenviarCodigo.disabled = false;
        }
    }

    async function procesarRespuestaVerificacion(respuesta) {
        const resultado = await respuesta.json();
        if (!respuesta.ok && !resultado.descripcion) throw new Error("No fue posible procesar la solicitud.");
        return resultado;
    }

    formulario_registro.addEventListener("submit", async function(e) {
        e.preventDefault();
        if (!formulario_registro.reportValidity()) return;
        btn_registro.disabled = true;
        try {
            const respuesta = await fetch("/registro_est/", {
                method: "POST",
                headers: { "X-CSRFToken": document.querySelector("#formulario_registro [name=csrfmiddlewaretoken]").value },
                body: new FormData(formulario_registro)
            });
            const resultado = await procesarRespuestaVerificacion(respuesta);
            if (resultado.estado === "verificacion_requerida") {
                abrirModalVerificacion(resultado.correo, resultado.segundos_reenvio || 60);
                mostrarMensajeVerificacion(resultado.descripcion, "info");
                return;
            }
            await NotificacionesCASRCE.mostrar({
                title: resultado.title,
                icon: resultado.icon,
                text: resultado.descripcion,
                allowOutsideClick: false,
                allowEscapeKey: false
            });
        } catch (error) {
            console.error(error);
            await NotificacionesCASRCE.mostrar({ title: "Error", icon: "error", text: "No fue posible iniciar la verificación. Inténtalo nuevamente." });
        } finally {
            btn_registro.disabled = false;
        }
    });

    formularioVerificacion.addEventListener("submit", async function(e) {
        e.preventDefault();
        const codigo = inputCodigoVerificacion.value.trim();
        if (!/^[0-9]{6}$/.test(codigo)) {
            mostrarMensajeVerificacion("Introduce los seis dígitos del código.", "error");
            inputCodigoVerificacion.focus();
            return;
        }
        btnConfirmarVerificacion.disabled = true;
        try {
            const datos = new FormData();
            datos.append("codigo", codigo);
            const respuesta = await fetch("/verificar_codigo_registro/", {
                method: "POST",
                headers: { "X-CSRFToken": document.querySelector("#formulario_registro [name=csrfmiddlewaretoken]").value },
                body: datos
            });
            const resultado = await procesarRespuestaVerificacion(respuesta);
            mostrarMensajeVerificacion(resultado.descripcion || "", resultado.estado === "exito" ? "exito" : "error");
            if (resultado.estado === "exito") {
                if (temporizadorReenvio) window.clearInterval(temporizadorReenvio);
                cerrarModalVerificacion();
                formulario_registro.reset();
                formularioVerificacion.reset();
                await NotificacionesCASRCE.mostrar({ title: resultado.title, icon: resultado.icon, text: resultado.descripcion, allowOutsideClick: false, allowEscapeKey: false });
            } else if (resultado.estado === "expirado") {
                iniciarTemporizadorReenvio(0);
            }
        } catch (error) {
            console.error(error);
            mostrarMensajeVerificacion("No se pudo verificar el código. Comprueba tu conexión e inténtalo nuevamente.", "error");
        } finally {
            btnConfirmarVerificacion.disabled = false;
        }
    });

    btnReenviarCodigo.addEventListener("click", async () => {
        btnReenviarCodigo.disabled = true;
        try {
            const respuesta = await fetch("/reenviar_codigo_registro/", {
                method: "POST",
                headers: { "X-CSRFToken": document.querySelector("#formulario_registro [name=csrfmiddlewaretoken]").value },
                body: new FormData()
            });
            const resultado = await procesarRespuestaVerificacion(respuesta);
            mostrarMensajeVerificacion(resultado.descripcion || "", resultado.estado === "exito" ? "exito" : "error");
            if (resultado.estado === "exito") iniciarTemporizadorReenvio(resultado.segundos_reenvio || 60);
            else if (resultado.estado === "espera") iniciarTemporizadorReenvio(resultado.segundos_reenvio || 1);
            else btnReenviarCodigo.disabled = false;
        } catch (error) {
            console.error(error);
            mostrarMensajeVerificacion("No fue posible reenviar el código. Inténtalo nuevamente.", "error");
            btnReenviarCodigo.disabled = false;
        }
    });

    inputCodigoVerificacion.addEventListener("input", () => {
        inputCodigoVerificacion.value = inputCodigoVerificacion.value.replace(/\D/g, "").slice(0, 6);
    });

});