
document.addEventListener("DOMContentLoaded", () => {

    // =====================================================
    // ELEMENTOS DEL DOM
    // =====================================================

    const formulario_verificar = document.getElementById("formulario_comprar_usuario");
    const btn_reenviar_codigo = document.getElementById("btn_reenviar_codigo");
    const contador_reenvio = document.getElementById("contador_reenvio");
    const contador_codigo = document.getElementById("contador_codigo");

    const input_password = document.getElementById("password");

    const dialogo_correos = document.getElementById("dialogo_correos");
    const formulario_enviar = document.getElementById("formulario_enviar");

    const label_correo_principal = document.getElementById("label_correo_principal");
    const label_correo_secundario = document.getElementById("label_correo_secundario");

    const input_radios_correo_principal = document.getElementById("correo_principal");
    const input_radios_correo_secundario = document.getElementById("correo_secundario");

    let intervaloCodigo = null;
    let intervaloReenvio = null;
    let esReenvio = false;
    let enviandoCodigo = false;

    // =====================================================
    // NORMALIZAR CÓDIGO INGRESADO
    // =====================================================

    if (input_password) {
        input_password.addEventListener("input", () => {
            input_password.value = input_password.value
                .toUpperCase()
                .replace(/[^A-Z0-9]/g, "");
        });
    }

     // =====================================================
    // VERIFICAR EL CÓDIGO INGRESADO
    // =====================================================

    if (formulario_verificar) {
        formulario_verificar.addEventListener("submit", async (e) => {
            e.preventDefault();

            const codigo = input_password?.value.trim() || "";

            if (!/^[A-Z0-9]{6}$/.test(codigo)) {
                NotificacionesCASRCE.advertencia(
                    "Ingresa un código válido de seis caracteres."
                );
                return;
            }

            const boton = formulario_verificar.querySelector(
                'button[type="submit"]'
            );

            if (boton) boton.disabled = true;

            try {
                const formulario = new FormData(formulario_verificar);

                const respuesta = await fetch("/comp_cod_usr/", {
                    method: "POST",
                    headers: {
                        "X-Requested-With": "XMLHttpRequest"
                    },
                    body: formulario
                });

                const resultado = await respuesta.json();

                if (!respuesta.ok) {
                    throw new Error(
                        resultado.descripcion ||
                        `Error HTTP ${respuesta.status}`
                    );
                }

                if (resultado.estado === "exito") {
                    NotificacionesCASRCE.exito(
                        resultado.descripcion ||
                        "Código verificado correctamente."
                    );

                    window.location.href = "/panel_rec_cred/";
                    return;
                }

                if (
                    resultado.estado === "bloqueado" ||
                    resultado.estado === "expirado"
                ) {
                    NotificacionesCASRCE.advertencia(
                        resultado.descripcion
                    );
                } else {
                    NotificacionesCASRCE.error(
                        resultado.descripcion ||
                        "No se pudo verificar el código."
                    );
                }

            } catch (error) {
                console.error(
                    "Error al verificar el código:",
                    error
                );

                NotificacionesCASRCE.error(
                    error.message ||
                    "Ocurrió un error al verificar el código."
                );

            } finally {
                if (boton) boton.disabled = false;
            }
        });
    }

    // =====================================================
    // CONVERTIR FECHAS DEL SERVIDOR A TIMESTAMP
    // =====================================================

    function convertirFechaTimestamp(fecha) {
        if (fecha === null || fecha === undefined || fecha === "") {
            return 0;
        }

        if (typeof fecha === "number") {
            return fecha < 1000000000000 ? fecha * 1000 : fecha;
        }

        const texto = String(fecha).trim();

        if (/^\d+$/.test(texto)) {
            const numero = Number(texto);
            return numero < 1000000000000 ? numero * 1000 : numero;
        }

        // Django puede devolver microsegundos; JavaScript trabaja
        // con precisión de milisegundos.
        const normalizada = texto.replace(
            /\.(\d{3})\d+(?=[+-]\d{2}:\d{2}$|Z$)/,
            ".$1"
        );

        const timestamp = Date.parse(normalizada);

        return Number.isFinite(timestamp) ? timestamp : 0;
    }

    // =====================================================
    // CONTADOR DE EXPIRACIÓN DEL CÓDIGO
    // =====================================================

    function iniciarContadorCodigo(expiracion) {
        clearInterval(intervaloCodigo);

        if (!contador_codigo) {
            console.error("No se encontró #contador_codigo.");
            return;
        }

        const fecha = convertirFechaTimestamp(expiracion);

        if (!fecha) {
            console.error("Fecha de expiración inválida:", expiracion);
            return;
        }

        function actualizar() {
            const restante = Math.max(
                0,
                Math.ceil((fecha - Date.now()) / 1000)
            );

            if (restante <= 0) {
                contador_codigo.textContent = "Expirado";
                clearInterval(intervaloCodigo);

                // Si ya expiró, permitir solicitar otro código,
                // siempre que no haya una petición en curso.
                if (btn_reenviar_codigo && !enviandoCodigo) {
                    btn_reenviar_codigo.disabled = false;
                }

                return;
            }

            const minutos = Math.floor(restante / 60);
            const segundos = restante % 60;

            contador_codigo.textContent =
                `${String(minutos).padStart(2, "0")}:` +
                `${String(segundos).padStart(2, "0")}`;
        }

        actualizar();
        intervaloCodigo = setInterval(actualizar, 1000);
    }

    // =====================================================
    // CONTADOR PARA HABILITAR EL REENVÍO
    // =====================================================

    function iniciarContadorReenvio(fecha) {
        clearInterval(intervaloReenvio);

        if (!contador_reenvio || !btn_reenviar_codigo) {
            console.error(
                "No se encontró el contador o botón de reenvío."
            );
            return;
        }

        const fechaReenvio = convertirFechaTimestamp(fecha);

        if (!fechaReenvio) {
            console.error("Fecha de reenvío inválida:", fecha);
            return;
        }

        function actualizar() {
            const restante = Math.max(
                0,
                Math.ceil((fechaReenvio - Date.now()) / 1000)
            );

            contador_reenvio.textContent = String(restante);

            // No habilitar durante el envío de una petición.
            btn_reenviar_codigo.disabled =
                restante > 0 || enviandoCodigo;

            if (restante <= 0) {
                clearInterval(intervaloReenvio);
                contador_reenvio.textContent = "0";

                if (!enviandoCodigo) {
                    btn_reenviar_codigo.disabled = false;
                }
            }
        }

        actualizar();
        intervaloReenvio = setInterval(actualizar, 1000);
    }

    // =====================================================
    // ACTUALIZAR AMBOS CONTADORES CON LA RESPUESTA DEL SERVIDOR
    // =====================================================

    function actualizarTemporizadores(resultado) {
        if (resultado.fecha_expiracion) {
            iniciarContadorCodigo(resultado.fecha_expiracion);
        }

        if (resultado.fecha_reenvio) {
            iniciarContadorReenvio(resultado.fecha_reenvio);
        }
    }

    // =====================================================
    // CONSULTAR SI EXISTE UN CÓDIGO VIGENTE
    // =====================================================

    async function exite_codigo() {
        try {
            const respuesta = await fetch("/exist_cod/");
            const resultado = await respuesta.json();

            if (
                resultado.estado === "exito" ||
                resultado.estado === "codigo_enviado" ||
                resultado.estado === "vigente"
            ) {
                actualizarTemporizadores(resultado);
            }

            if (resultado.estado === "expirado") {
                if (btn_reenviar_codigo) {
                    btn_reenviar_codigo.disabled = false;
                }

                if (contador_reenvio) {
                    contador_reenvio.textContent = "0";
                }

                await NotificacionesCASRCE.mostrar({
                    title: resultado.title,
                    text: resultado.descripcion,
                    icon: resultado.icon,
                    allowOutsideClick: false,
                    allowEscapeKey: false
                });

                return;
            }

            if (resultado.estado === "no_exite") {
                if (btn_reenviar_codigo) {
                    btn_reenviar_codigo.disabled = false;
                }

                if (contador_reenvio) {
                    contador_reenvio.textContent = "0";
                }

                await NotificacionesCASRCE.mostrar({
                    title: resultado.title,
                    text: resultado.descripcion,
                    icon: resultado.icon,
                    allowOutsideClick: false,
                    allowEscapeKey: false
                });

                esReenvio = false;
                await correos_electronicos();
            }

        } catch (error) {
            console.error("Error en exite_codigo:", error);
        }
    }

    // =====================================================
    // OBTENER LOS CORREOS REGISTRADOS
    // =====================================================

    async function correos_electronicos() {
        try {
            const respuesta = await fetch("/corr_reg/");
            const resultado = await respuesta.json();

            if (resultado.estado === "exito" && resultado.correos) {
                const correoPrincipal =
                    resultado.correos.correo_principal || "";

                const correoSecundario =
                    resultado.correos.correo_secundario || "";

                if (label_correo_principal) {
                    label_correo_principal.textContent = correoPrincipal;
                }

                if (input_radios_correo_principal) {
                    input_radios_correo_principal.value = correoPrincipal;
                    input_radios_correo_principal.checked =
                        Boolean(correoPrincipal);
                    input_radios_correo_principal.disabled =
                        !correoPrincipal;
                }

                if (label_correo_secundario) {
                    label_correo_secundario.textContent = correoSecundario;
                }

                if (input_radios_correo_secundario) {
                    input_radios_correo_secundario.value = correoSecundario;
                    input_radios_correo_secundario.checked = false;
                    input_radios_correo_secundario.disabled =
                        !correoSecundario;
                }

                // Seleccionar el principal si está disponible;
                // en caso contrario, seleccionar el secundario.
                if (
                    input_radios_correo_principal &&
                    !correoPrincipal &&
                    correoSecundario
                ) {
                    input_radios_correo_secundario.checked = true;
                }

                if (dialogo_correos && !dialogo_correos.open) {
                    dialogo_correos.showModal();
                }

            } else {
                await NotificacionesCASRCE.mostrar({
                    title: resultado.title || "Atención",
                    text: resultado.descripcion ||
                        "No se pudo obtener la información.",
                    icon: resultado.icon || "warning"
                });
            }

        } catch (error) {
            console.error("Error en la petición de correos:", error);
        }
    }

    // =====================================================
    // BOTÓN DE REENVÍO
    // =====================================================

    if (btn_reenviar_codigo) {
        btn_reenviar_codigo.addEventListener("click", async () => {
            if (btn_reenviar_codigo.disabled || enviandoCodigo) {
                return;
            }

            esReenvio = true;
            await correos_electronicos();
        });
    }

    // =====================================================
    // ENVIAR O REENVIAR EL CÓDIGO
    // =====================================================

    if (formulario_enviar) {
        formulario_enviar.addEventListener("submit", async (e) => {
            e.preventDefault();

            if (enviandoCodigo) {
                return;
            }

            enviandoCodigo = true;

            if (btn_reenviar_codigo) {
                btn_reenviar_codigo.disabled = true;
            }

            // Mostrar la carga real de Notiflix.
            NotificacionesCASRCE.cargar(
                "Enviando código, por favor espera..."
            );

            try {
                const formulario = new FormData(formulario_enviar);

                const url = esReenvio
                    ? "/reenv_cod_btn/"
                    : "/env_cod_usr/";

                const csrfTokenElement = formulario_enviar.querySelector(
                    "[name=csrfmiddlewaretoken]"
                );

                const csrfToken = csrfTokenElement
                    ? csrfTokenElement.value
                    : "";

                const respuesta = await fetch(url, {
                    method: "POST",
                    headers: {
                        "X-CSRFToken": csrfToken
                    },
                    body: formulario
                });

                const resultado = await respuesta.json();

                // La respuesta llegó: cerrar la carga inmediatamente.
                NotificacionesCASRCE.detenerCarga();

                if (!respuesta.ok) {
                    throw new Error(
                        resultado.descripcion ||
                        `Error HTTP ${respuesta.status}`
                    );
                }

                const envioExitoso =
                    resultado.estado === "exito" ||
                    resultado.estado === "codigo_enviado";

                if (envioExitoso) {
                    // Reiniciar los contadores con las fechas del servidor.
                    actualizarTemporizadores(resultado);

                    if (dialogo_correos && dialogo_correos.open) {
                        dialogo_correos.close();
                    }

                    // Notificación temporal: no necesita pulsar Enter.
                    NotificacionesCASRCE.exito(
                        resultado.descripcion ||
                        "¡Código enviado! Revisa tu correo electrónico y la carpeta de spam."
                    );
                } else {
                    // Mostrar el motivo del rechazo sin bloquear la pantalla.
                    const mensaje = resultado.descripcion ||
                        "No se pudo enviar el código. Inténtalo nuevamente.";

                    if (
                        resultado.estado === "bloqueado" ||
                        resultado.estado === "expirado"
                    ) {
                        NotificacionesCASRCE.advertencia(mensaje);
                    } else {
                        NotificacionesCASRCE.error(mensaje);
                    }

                    // Actualizar el estado del código según el servidor.
                    await exite_codigo();
                }

            } catch (error) {
                console.error("Error al enviar el código:", error);

                NotificacionesCASRCE.error(
                    error.message ||
                    "No se pudo completar el envío. Comprueba tu conexión e inténtalo nuevamente."
                );

            } finally {
                // Garantizar que la carga desaparezca incluso si ocurre un error.
                NotificacionesCASRCE.detenerCarga();

                enviandoCodigo = false;
                esReenvio = false;

                // El contador de reenvío determina si el botón puede habilitarse.
                if (intervaloReenvio) {
                    // El siguiente tick actualizará el estado del botón.
                } else if (btn_reenviar_codigo && !contador_reenvio) {
                    btn_reenviar_codigo.disabled = false;
                }
            }
        });
    }

    // =====================================================
    // INICIALIZAR
    // =====================================================

    exite_codigo();

});
