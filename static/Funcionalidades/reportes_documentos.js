document.addEventListener("submit", async (event) => {
    const form = event.target.closest("form[data-generar-documento]");
    if (!form) return;

    event.preventDefault();
    const tipo = form.querySelector('[name="tipo"]')?.value;
    const anio = form.querySelector('[name="anio"]');
    if (tipo && ["inscripciones", "egresados", "estudiantes_anuales"].includes(tipo)) {
        const valor = Number(anio?.value);
        const maximo = new Date().getFullYear() + 1;
        if (!Number.isInteger(valor) || valor < 1900 || valor > maximo) {
            await NotificacionesCASRCE.mostrar({
                title: "Año requerido",
                text: `Indica un año válido entre 1900 y ${maximo}.`,
                icon: "warning",
            });
            anio?.focus();
            return;
        }
    }

    const ventana = window.open("about:blank", "_blank");
    const boton = form.querySelector('button[type="submit"]');
    if (boton) boton.disabled = true;

    try {
        const response = await fetch(form.action, {
            method: "POST",
            headers: {
                "X-CSRFToken": form.querySelector('[name="csrfmiddlewaretoken"]').value,
            },
            body: new FormData(form),
        });
        const resultado = await response.json();
        if (!response.ok || resultado.estado !== "exito") {
            ventana?.close();
            await NotificacionesCASRCE.mostrar({
                title: "No se pudo generar el documento",
                text: resultado.mensaje || "Verifica los datos e inténtalo nuevamente.",
                icon: "error",
            });
            return;
        }

        if (ventana) {
            ventana.location = resultado.url_descarga;
        } else {
            window.location.assign(resultado.url_descarga);
        }
        await NotificacionesCASRCE.mostrar({
            title: "Documento registrado",
            text: resultado.mensaje,
            icon: "success",
        });
    } catch (error) {
        ventana?.close();
        console.error("Error solicitando un documento institucional.", error);
        await NotificacionesCASRCE.mostrar({
            title: "Error de conexión",
            text: "No se pudo contactar al sistema para generar el documento.",
            icon: "error",
        });
    } finally {
        if (boton) boton.disabled = false;
    }
});
