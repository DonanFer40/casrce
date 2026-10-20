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

        NotificacionesCASRCE.cargar("Iniciando sesión...");

        try {
            const formulario = new FormData(formulario_autenticacion);
            const csrftoken = getCookie('csrftoken'); // Obtenemos el token

            const [respuesta] = await Promise.all([
                fetch("/inicio_sesion/", {
                    method: "POST",
                    headers: {
                        'X-CSRFToken': csrftoken // ¡Aquí enviamos el token de seguridad!
                    },
                    body: formulario
                }),
                new Promise(resolve => setTimeout(resolve, 1200)) 
            ]);
            
            if (!respuesta.ok) {
                throw new Error(
                    `El servidor respondió con el estado ${respuesta.status}.`
                );
            }

            const resultado = await respuesta.json();

            NotificacionesCASRCE.detenerCarga();

            if (resultado.estado === "exito") {
                window.location.href = resultado.url;
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