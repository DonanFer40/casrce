
/**
 * Notificaciones generales del sistema CASRCE
 * Centraliza mensajes, reportes y estados de carga.
 */

(() => {
    "use strict";

    // Evitar errores si Notiflix no se ha cargado.
    const notiflixDisponible = () =>
        typeof Notiflix !== "undefined";

    function configurarNotiflix() {
        if (!notiflixDisponible()) return;

        Notiflix.Notify.init({
            width: "320px",
            position: "right-top",
            distance: "18px",
            opacity: 1,
            borderRadius: "10px",
            timeout: 3500,
            clickToClose: true,
            fontSize: "14px",
            useIcon: true,
            cssAnimationStyle: "fade"
        });

        Notiflix.Report.init({
            width: "360px",
            backgroundColor: "#FFFFFF",
            borderRadius: "14px",
            titleFontSize: "19px",
            messageFontSize: "14px",
            buttonFontSize: "14px",
            plainText: false,
            svgSize: "80px",
            backOverlay: true,
            backOverlayColor: "rgba(15, 23, 42, 0.69)",
            fontFamily: "Poppins, Arial, sans-serif",
            buttonBackground: "#2563EB",
            cssAnimationStyle: "fade"
        });

        Notiflix.Confirm.init({
            width: "380px",
            backgroundColor: "#FFFFFF",
            borderRadius: "14px",
            titleColor: "#0F172A",
            messageColor: "#334155",
            buttonColor: "#FFFFFF",
            okButtonBackground: "#2563EB",
            cancelButtonBackground: "#64748B",
            titleFontSize: "18px",
            messageFontSize: "14px",
            buttonFontSize: "14px",
            plainText: false,
            fontFamily: "Poppins, Arial, sans-serif",
            backOverlay: true,
            backOverlayColor: "rgba(15, 23, 42, 0.69)",
            cssAnimationStyle: "fade"
        });

        Notiflix.Loading.init({
            backgroundColor: "rgba(15, 23, 42, 0.69)",
            messageColor: "#FFFFFF",
            svgColor: "#2563EB",
            fontFamily: "Poppins, Arial, sans-serif",
            clickToClose: false
        });
    }

    const NotificacionesCASRCE = {
        exito(mensaje) {
            if (notiflixDisponible()) {
                Notiflix.Notify.success(mensaje);
            }
        },

        error(mensaje) {
            if (notiflixDisponible()) {
                Notiflix.Notify.failure(mensaje);
            }
        },

        advertencia(mensaje) {
            if (notiflixDisponible()) {
                Notiflix.Notify.warning(mensaje);
            }
        },

        informacion(mensaje) {
            if (notiflixDisponible()) {
                Notiflix.Notify.info(mensaje);
            }
        },

        reporte(tipo, titulo, mensaje, boton = "Aceptar") {
            if (!notiflixDisponible()) return;

            const reportes = {
                exito: Notiflix.Report.success,
                error: Notiflix.Report.failure,
                advertencia: Notiflix.Report.warning,
                informacion: Notiflix.Report.info
            };

            const mostrarReporte =
                reportes[tipo] || Notiflix.Report.info;

            mostrarReporte(titulo, mensaje, boton);
        },

        /**
         * Muestra un reporte o confirmación con Notiflix.
         * Devuelve una promesa con una forma compatible con los resultados
         * que consume el proyecto: { isConfirmed, isDismissed, value, dismiss }.
         */
        mostrar(opciones = {}) {
            if (!notiflixDisponible()) {
                return Promise.resolve({ isConfirmed: false, isDismissed: true, dismiss: "notiflix-no-disponible" });
            }

            if (typeof opciones === "string") opciones = { text: opciones };
            const titulo = opciones.title || "CASRCE";
            const mensaje = opciones.html || opciones.text || "";
            const botonAceptar = opciones.confirmButtonText || "Aceptar";
            const botonCancelar = opciones.cancelButtonText || "Cancelar";
            const icono = String(opciones.icon || "info").toLowerCase();

            // Notiflix no incluye un prompt de texto/textarea. Se utiliza un
            // diálogo propio para conservar el dato que las vistas necesitan.
            if (opciones.input === "textarea" || opciones.input === "text") {
                return this._solicitarTexto(opciones);
            }

            return new Promise((resolve) => {
                if (opciones.showCancelButton || opciones.showDenyButton) {
                    Notiflix.Confirm.show(
                        titulo,
                        mensaje,
                        botonAceptar,
                        botonCancelar,
                        () => resolve({ isConfirmed: true, isDenied: false, isDismissed: false, value: true }),
                        () => resolve({ isConfirmed: false, isDenied: false, isDismissed: true, dismiss: "cancel" })
                    );
                    return;
                }

                const reportes = {
                    success: Notiflix.Report.success,
                    error: Notiflix.Report.failure,
                    warning: Notiflix.Report.warning,
                    info: Notiflix.Report.info,
                    question: Notiflix.Report.info
                };
                const mostrarReporte = reportes[icono] || Notiflix.Report.info;
                mostrarReporte(titulo, mensaje, botonAceptar, () => {
                    resolve({ isConfirmed: true, isDenied: false, isDismissed: false, value: true });
                });
            });
        },

        _solicitarTexto(opciones) {
            return new Promise((resolve) => {
                const anterior = document.getElementById("notificaciones-casrce-dialogo-texto");
                if (anterior) anterior.remove();

                const overlay = document.createElement("div");
                overlay.id = "notificaciones-casrce-dialogo-texto";
                overlay.setAttribute("role", "dialog");
                overlay.setAttribute("aria-modal", "true");
                overlay.setAttribute("aria-label", opciones.title || "Introducir texto");
                overlay.style.cssText = "position:fixed;inset:0;z-index:2147483000;display:flex;align-items:center;justify-content:center;padding:18px;background:rgba(15,23,42,.69);font-family:Poppins,Arial,sans-serif;";

                const panel = document.createElement("section");
                panel.style.cssText = "box-sizing:border-box;width:min(100%,460px);max-height:90vh;overflow:auto;background:#fff;border-radius:14px;padding:24px;box-shadow:0 20px 60px rgba(0,0,0,.25);color:#0F172A;";
                const titulo = document.createElement("h2");
                titulo.textContent = opciones.title || "Introducir texto";
                titulo.style.cssText = "margin:0 0 12px;font-size:19px;line-height:1.35;";
                panel.appendChild(titulo);

                if (opciones.text) {
                    const descripcion = document.createElement("p");
                    descripcion.textContent = opciones.text;
                    descripcion.style.cssText = "margin:0 0 16px;color:#475569;font-size:14px;line-height:1.5;";
                    panel.appendChild(descripcion);
                }

                if (opciones.inputLabel) {
                    const label = document.createElement("label");
                    label.textContent = opciones.inputLabel;
                    label.style.cssText = "display:block;margin:0 0 7px;font-size:14px;font-weight:600;";
                    label.htmlFor = "notificaciones-casrce-texto";
                    panel.appendChild(label);
                }

                const campo = document.createElement(opciones.input === "textarea" ? "textarea" : "input");
                campo.id = "notificaciones-casrce-texto";
                campo.placeholder = opciones.inputPlaceholder || "";
                campo.value = opciones.inputValue || "";
                campo.setAttribute("aria-label", (opciones.inputAttributes && opciones.inputAttributes["aria-label"]) || opciones.inputLabel || "Texto");
                campo.style.cssText = "box-sizing:border-box;width:100%;min-height:" + (opciones.input === "textarea" ? "120px" : "42px") + ";padding:11px 12px;border:1px solid #CBD5E1;border-radius:8px;font:14px Poppins,Arial,sans-serif;resize:vertical;outline-color:#2563EB;";
                panel.appendChild(campo);

                const acciones = document.createElement("div");
                acciones.style.cssText = "display:flex;justify-content:flex-end;gap:10px;margin-top:20px;flex-wrap:wrap;";
                const crearBoton = (texto, color) => {
                    const boton = document.createElement("button");
                    boton.type = "button";
                    boton.textContent = texto;
                    boton.style.cssText = "border:0;border-radius:8px;padding:10px 15px;background:" + color + ";color:#fff;font:600 14px Poppins,Arial,sans-serif;cursor:pointer;";
                    acciones.appendChild(boton);
                    return boton;
                };
                const cancelar = crearBoton(opciones.cancelButtonText || "Cancelar", "#64748B");
                const aceptar = crearBoton(opciones.confirmButtonText || "Aceptar", "#2563EB");
                panel.appendChild(acciones);
                overlay.appendChild(panel);
                document.body.appendChild(overlay);

                let resuelto = false;
                const cerrar = (resultado) => {
                    if (resuelto) return;
                    resuelto = true;
                    overlay.remove();
                    document.removeEventListener("keydown", teclaEscape);
                    resolve(resultado);
                };
                const teclaEscape = (evento) => {
                    if (evento.key === "Escape" && opciones.allowEscapeKey !== false) {
                        cerrar({ isConfirmed: false, isDismissed: true, dismiss: "cancel" });
                    }
                };
                cancelar.addEventListener("click", () => cerrar({ isConfirmed: false, isDismissed: true, dismiss: "cancel" }));
                aceptar.addEventListener("click", async () => {
                    const valor = campo.value;
                    if (typeof opciones.inputValidator === "function") {
                        const error = await opciones.inputValidator(valor);
                        if (error) {
                            Notiflix.Notify.warning(String(error));
                            campo.focus();
                            return;
                        }
                    }
                    cerrar({ isConfirmed: true, isDismissed: false, value: valor });
                });
                document.addEventListener("keydown", teclaEscape);
                campo.focus();
            });
        },

        DismissReason: { cancel: "cancel" },

        cargar(mensaje = "Procesando...") {
            if (notiflixDisponible()) {
                Notiflix.Loading.standard(mensaje);
            }
        },

        detenerCarga() {
            if (notiflixDisponible()) {
                Notiflix.Loading.remove();
            }
        }
    };

    window.NotificacionesCASRCE = NotificacionesCASRCE;

    configurarNotiflix();
})();
