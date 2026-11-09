document.addEventListener("DOMContentLoaded", () => {
    const formulario_autenticacion = document.getElementById("formulario_login");

    // Función auxiliar para obtener el token CSRF de las cookies
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    formulario_autenticacion.addEventListener("submit", async (evento) => {
        evento.preventDefault();

        if (!window.CASRCE_BROWSER_ID) {
            NotificacionesCASRCE.reporte(
                "error",
                "No se pudo validar el navegador",
                "Activa el almacenamiento local del navegador y vuelve a cargar la página."
            );
            return;
        }

        NotificacionesCASRCE.cargar("Iniciando sesión...");

        try {
            const formulario = new FormData(formulario_autenticacion);
            const csrftoken = getCookie('csrftoken'); // Obtenemos el token

            let [respuesta] = await Promise.all([
                fetch("/inicio_sesion/", {
                    method: "POST",
                    headers: {
                        'X-CSRFToken': csrftoken // ¡Aquí enviamos el token de seguridad!
                    },
                    body: formulario
                }),
                new Promise(resolve => setTimeout(resolve, 1200)) 
            ]);
            
            if (
                !respuesta.ok
                && respuesta.status !== 429
                && respuesta.status !== 409
            ) {
                throw new Error(
                    `El servidor respondió con el estado ${respuesta.status}.`
                );
            }

            let resultado = await respuesta.json();

            NotificacionesCASRCE.detenerCarga();

            if (resultado.estado === "advertencia") {
                const continuar = window.confirm(
                    `${resultado.title}\n\n${resultado.descripcion}`
                );

                if (!continuar) {
                    return;
                }

                formulario.set("confirmar_nueva_sesion", "1");
                NotificacionesCASRCE.cargar("Iniciando nueva sesión...");

                respuesta = await fetch("/inicio_sesion/", {
                    method: "POST",
                    headers: {
                        "X-CSRFToken": csrftoken
                    },
                    body: formulario
                });

                if (
                    !respuesta.ok
                    && respuesta.status !== 429
                    && respuesta.status !== 409
                ) {
                    throw new Error(
                        `El servidor respondió con el estado ${respuesta.status}.`
                    );
                }

                resultado = await respuesta.json();
                NotificacionesCASRCE.detenerCarga();
            }

            if (resultado.estado === "exito") {
                window.CASRCE_TAB_NAVIGATE(resultado.url);
                return;
            }

            const tiposPermitidos = [
                "exito",
                "error",
                "advertencia",
                "informacion"
            ];

            const tipo = tiposPermitidos.includes(resultado.icon)
                ? resultado.icon
                : "error";

            NotificacionesCASRCE.reporte(
                tipo,
                resultado.title || "No se pudo iniciar sesión",
                resultado.descripcion || "Verifica tus datos e inténtalo nuevamente."
            );

            formulario_autenticacion.reset(); // Corregido para limpiar el form real

        } catch (error) {
            NotificacionesCASRCE.detenerCarga();

            console.error("Error en la autenticación:", error);

            NotificacionesCASRCE.reporte(
                "error",
                "Error de conexión",
                "No fue posible comunicarse con el servidor. Inténtalo nuevamente."
            );
        }
    });
});