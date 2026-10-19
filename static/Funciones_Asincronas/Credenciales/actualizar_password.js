document.addEventListener("DOMContentLoaded", () => {

    /* =====================================================
       ELEMENTOS DEL FORMULARIO
    ===================================================== */

    const formulario_registro = document.getElementById(
        "cambiar-contrasenia-carsce-formulario"
    );

    if (!formulario_registro) {
        console.error(
            "CASRCE: No se encontró el formulario para cambiar la contraseña."
        );
        return;
    }


    /* =====================================================
       ENVÍO ASÍNCRONO DEL FORMULARIO
    ===================================================== */

    formulario_registro.addEventListener("submit", async function (e) {
        e.preventDefault();

        const boton = formulario_registro.querySelector(
            'button[type="submit"]'
        );

        if (boton) {
            boton.disabled = true;
        }

        try {
            const formulario = new FormData(formulario_registro);

            const respuesta = await fetch("/rec_cont/", {
                method: "POST",
                body: formulario,
                headers: {
                    "X-Requested-With": "XMLHttpRequest"
                }
            });

            const resultado = await respuesta.json();

            console.log("Respuesta de CASRCE:", resultado);


            /* =================================================
               MOSTRAR NOTIFICACIÓN
            ================================================= */

            await NotificacionesCASRCE.mostrar({
                title: resultado.title || "Información",
                text: resultado.descripcion || "La operación ha finalizado.",
                icon: resultado.icon || "info",
                allowOutsideClick: false,
                allowEscapeKey: false
            });


            /* =================================================
               RESULTADO EXITOSO
            ================================================= */

            if (resultado.estado === "exito") {
                window.location.href = resultado.redirect_url;
                return;
            }

        } catch (error) {
            console.error(
                "CASRCE: Error al actualizar la contraseña:",
                error
            );

            if (typeof NotificacionesCASRCE !== "undefined") {
                await NotificacionesCASRCE.mostrar({
                    title: "Error de conexión",
                    text: "No fue posible procesar la solicitud. Inténtalo nuevamente.",
                    icon: "error",
                    allowOutsideClick: false,
                    allowEscapeKey: false
                });
            }

        } finally {
            if (boton) {
                boton.disabled = false;
            }
        }
    });

});