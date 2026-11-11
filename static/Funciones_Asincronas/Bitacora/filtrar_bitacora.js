document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("filtros-bitacora");
    const resultados = document.getElementById("bitacora-resultados");
    if (!form || !resultados) return;

    let solicitudActual;
    let temporizadorBusqueda;

    async function cargarResultados(parametros, reemplazarHistorial = true) {
        solicitudActual?.abort();
        solicitudActual = new AbortController();
        resultados.setAttribute("aria-busy", "true");

        try {
            const url = new URL(form.action || window.location.href);
            url.search = parametros.toString();
            const respuesta = await fetch(url, {
                headers: { "X-Requested-With": "XMLHttpRequest" },
                signal: solicitudActual.signal,
            });

            if (!respuesta.ok || respuesta.redirected) {
                throw new Error(`El servidor respondió con estado ${respuesta.status}.`);
            }

            const contenido = await respuesta.text();
            const documento = new DOMParser().parseFromString(contenido, "text/html");
            if (documento.querySelector("#bitacora-resultados")) {
                throw new Error("La respuesta no contiene los resultados filtrados.");
            }

            resultados.innerHTML = contenido;
            if (reemplazarHistorial) {
                window.history.replaceState({}, "", `${url.pathname}${url.search}`);
            }
        } catch (error) {
            if (error.name !== "AbortError") {
                console.error("No se pudieron actualizar los filtros de bitácora:", error);
                NotificacionesCASRCE.reporte(
                    "error",
                    "No se pudieron cargar los resultados",
                    "Verifica tu conexión e inténtalo nuevamente."
                );
            }
        } finally {
            resultados.removeAttribute("aria-busy");
        }
    }

    function parametrosFormulario() {
        const parametros = new URLSearchParams(new FormData(form));
        parametros.delete("page");
        return parametros;
    }

    form.addEventListener("submit", (evento) => {
        evento.preventDefault();
        cargarResultados(parametrosFormulario());
    });

    form.addEventListener("change", (evento) => {
        if (evento.target.matches("select, input[type='date']")) {
            cargarResultados(parametrosFormulario());
        }
    });

    form.addEventListener("input", (evento) => {
        if (evento.target.matches("input[type='search'], input[name='rol'], input[name='accion']")) {
            window.clearTimeout(temporizadorBusqueda);
            temporizadorBusqueda = window.setTimeout(
                () => cargarResultados(parametrosFormulario()),
                300
            );
        }
    });

    document.addEventListener("click", (evento) => {
        const enlaceLimpiar = evento.target.closest(".bitacora-acciones-carsce-boton-limpiar");
        if (enlaceLimpiar) {
            evento.preventDefault();
            form.reset();
            cargarResultados(new URLSearchParams());
            return;
        }

        const enlacePagina = evento.target.closest("#bitacora-resultados .bitacora-acciones-carsce-pag-btn");
        if (!enlacePagina) return;

        evento.preventDefault();
        const url = new URL(enlacePagina.href);
        cargarResultados(url.searchParams);
    });
});
