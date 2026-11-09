document.addEventListener("DOMContentLoaded", () => {

    const formulario_registrar = document.getElementById("formulario_registrar");
    const input_registrar_seccion = document.getElementById("registro_seccion");
    const mensaje_nombre_seccion = document.getElementById("mensaje_nombre_seccion");

    const btn_registrar = document.getElementById("btn_registro");

    async function actualizar_siguiente_seccion() {
        try {
            const respuesta = await fetch("/sec_reg/");
            const resultado = await respuesta.json();
            if (!respuesta.ok || resultado.estado !== "exito") {
                throw new Error("No se pudo consultar la siguiente sección.");
            }

            input_registrar_seccion.value = resultado.siguiente || "";
            btn_registrar.disabled = !resultado.siguiente;
            mensaje_nombre_seccion.textContent = resultado.siguiente
                ? `Se asignará automáticamente la sección ${resultado.siguiente}.`
                : "Las letras de la A a la Z están ocupadas. Libera una sección para continuar.";
        } catch (error) {
            console.error(error);
            btn_registrar.disabled = true;
            mensaje_nombre_seccion.textContent = "No se pudo consultar la disponibilidad de secciones.";
        }
    }

    actualizar_siguiente_seccion();

    formulario_registrar.addEventListener("submit", async (e) => {
        e.preventDefault()
        try {
            const formulario = new FormData(formulario_registrar);

            const respuesta = await fetch("/reg_sec/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            NotificacionesCASRCE.mostrar({
                text: resultado.descripcion,
                icon: resultado.icon,
                title: resultado.title,
                allowOutsideClick: false,
                allowEscapeKey: false
            });

            if (resultado.estado == "exito") {
                formulario_registrar.reset();
                await actualizar_siguiente_seccion();
            }
        } catch (error) {
            console.error(error);
        }
    });

});