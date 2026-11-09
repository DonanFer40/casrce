document.addEventListener("DOMContentLoaded", () => {
    const flujo = document.getElementById("seguridad-admin-flujo");
    if (!flujo) return;

    const pasoCorreo = document.getElementById("paso-correo");
    const pasoTotp = document.getElementById("paso-totp");
    const formularioCorreo = document.getElementById("form-correo");
    const formularioTotp = document.getElementById("form-totp");
    const formularioCancelar = document.getElementById("form-cancelar");
    const botonReenviar = document.getElementById("reenviar-codigo");
    const mensaje = document.getElementById("mensaje-seguridad");
    const csrfToken = formularioCorreo.querySelector(
        "[name=csrfmiddlewaretoken]"
    ).value;

    async function enviar(url, datos) {
        const respuesta = await fetch(url, {
            method: "POST",
            body: datos,
            headers: {
                "X-CSRFToken": csrfToken,
                "X-Requested-With": "XMLHttpRequest",
            },
            credentials: "same-origin",
        });

        const resultado = await respuesta.json();
        if (!respuesta.ok || !resultado.success) {
            throw new Error(
                resultado.message || "No fue posible completar la verificación."
            );
        }
        return resultado;
    }

    function mostrarMensaje(texto, error = false) {
        mensaje.textContent = texto;
        mensaje.dataset.estado = error ? "error" : "exito";
    }

    formularioCorreo.addEventListener("submit", async (evento) => {
        evento.preventDefault();
        const boton = formularioCorreo.querySelector('button[type="submit"]');
        boton.disabled = true;
        try {
            const resultado = await enviar(
                flujo.dataset.urlCorreo,
                new FormData(formularioCorreo)
            );
            pasoCorreo.hidden = true;
            pasoTotp.hidden = false;
            formularioTotp.querySelector("input[name=codigo]").focus();
            mostrarMensaje(resultado.message);
        } catch (error) {
            mostrarMensaje(error.message, true);
        } finally {
            boton.disabled = false;
        }
    });

    formularioTotp.addEventListener("submit", async (evento) => {
        evento.preventDefault();
        const boton = formularioTotp.querySelector('button[type="submit"]');
        boton.disabled = true;
        try {
            const resultado = await enviar(
                flujo.dataset.urlTotp,
                new FormData(formularioTotp)
            );
            mostrarMensaje(resultado.message);
            window.location.assign(resultado.siguiente);
        } catch (error) {
            mostrarMensaje(error.message, true);
        } finally {
            boton.disabled = false;
        }
    });

    botonReenviar.addEventListener("click", async () => {
        botonReenviar.disabled = true;
        try {
            const resultado = await enviar(
                flujo.dataset.urlReenviar,
                new FormData(formularioCorreo)
            );
            mostrarMensaje(resultado.message);
        } catch (error) {
            mostrarMensaje(error.message, true);
        } finally {
            botonReenviar.disabled = false;
        }
    });

    formularioCancelar.addEventListener("submit", async (evento) => {
        evento.preventDefault();
        const boton = formularioCancelar.querySelector('button[type="submit"]');
        boton.disabled = true;
        try {
            await enviar(
                flujo.dataset.urlCancelar,
                new FormData(formularioCancelar)
            );
            window.location.assign(flujo.dataset.urlLogin);
        } catch (error) {
            mostrarMensaje(error.message, true);
            boton.disabled = false;
        }
    });
});