document.addEventListener("DOMContentLoaded", () => {

    // =====================================================
    // ELEMENTOS DEL FORMULARIO
    // =====================================================

    const formulario = document.getElementById("formulario_registrar_autoridades");

    const usuario_seleccionado = document.getElementById("usuario_seleccionado");

    const input_nombres = document.getElementById("nombres_autoridades");
    const input_apellidos = document.getElementById("apellidos_autoridades");

    const input_cedula = document.getElementById("cedula_identidad");
    const select_nacionalidad = document.getElementById("nacionalidad");
    const mensaje_cedula = document.getElementById("mensaje_cedula_identidad");

    const select_genero = document.getElementById("genero_autoridades");
    const select_cargo = document.getElementById("cargo_autoridades");

    const input_resolucion = document.getElementById("resolucion_autoridades");
    const mensaje_resolucion = document.getElementById("msg_resolucion");

    const boton = document.getElementById("btn_registrar");

    // =====================================================
    // CARGOS DEFINIDOS EN EL SISTEMA
    // =====================================================

    const CARGOS = [
        "Rector",
        "Vicerrector",
        "Responsable Académico"
    ];

    // =====================================================
    // ESTADOS
    // =====================================================

    let cedula_valida = true;
    let resolucion_valida = true;

    let validando_cedula = false;
    let validando_resolucion = false;
    let cargando_cargos = false;
    let enviando_formulario = false;

    let cargo_original = "";

    // Control de peticiones AJAX
    let peticion_cedula = 0;
    let peticion_resolucion = 0;
    let peticion_cargos = 0;
    let peticion_seleccion = 0;
    let secuencia_reset = 0;

    // =====================================================
    // FUNCIONES GENERALES
    // =====================================================

    function esta_modificando() {

        return usuario_seleccionado.value.trim() !== "";

    }

    function obtener_csrf() {

        return document.querySelector(
            "[name=csrfmiddlewaretoken]"
        )?.value || "";

    }

    function actualizar_boton() {

        const formulario_valido = formulario.checkValidity();

        boton.disabled =
            !formulario_valido ||
            !cedula_valida ||
            !resolucion_valida ||
            validando_cedula ||
            validando_resolucion ||
            cargando_cargos ||
            enviando_formulario;

    }

    function mostrar_mensaje(elemento, texto, valido = null) {

        elemento.textContent = texto;

        if (valido === true) {

            elemento.style.color = "#198754";

        } else if (valido === false) {

            elemento.style.color = "#dc3545";

        }

    }

    async function mostrar_notificacion(configuracion) {

        if (typeof NotificacionesCASRCE !== "undefined") {

            return await NotificacionesCASRCE.mostrar(configuracion);

        }

        console.error("No se encontró NotificacionesCASRCE.");

    }

    // =====================================================
    // CONFIRMACIONES
    // =====================================================

    async function confirmar_accion(titulo, texto) {

        // Utilizar SweetAlert si está disponible.
        if (typeof Swal !== "undefined") {

            const resultado = await Swal.fire({

                title: titulo,
                text: texto,
                icon: "warning",
                showCancelButton: true,
                confirmButtonText: "Sí, continuar",
                cancelButtonText: "Cancelar",
                reverseButtons: true,
                allowOutsideClick: false

            });

            return resultado.isConfirmed;

        }

        // Alternativa si SweetAlert no está disponible.
        return window.confirm(`${titulo}\n\n${texto}`);

    }

    // =====================================================
    // CONFIGURACIÓN DE CÉDULA
    // =====================================================

    configurarCedula(select_nacionalidad, input_cedula);

    // =====================================================
    // VALIDAR CÉDULA
    // =====================================================

    async function validar_cedula() {

        // La cédula no se modifica durante una actualización.
        if (esta_modificando()) {

            peticion_cedula++;

            cedula_valida = true;
            validando_cedula = false;

            actualizar_boton();

            return;

        }

        const numero_peticion = ++peticion_cedula;

        const nacionalidad = select_nacionalidad.value;
        const cedula = input_cedula.value.trim();

        if (!cedula) {

            cedula_valida = true;
            validando_cedula = false;

            input_cedula.setCustomValidity("");

            input_cedula.classList.remove(
                "is-valid",
                "is-invalid"
            );

            mostrar_mensaje(mensaje_cedula, "");

            actualizar_boton();

            return;

        }

        validando_cedula = true;

        actualizar_boton();

        try {

            const datos = new FormData();

            datos.append("nacionalidad", nacionalidad);
            datos.append("cedula", cedula);

            const respuesta = await fetch("/val_ci_aut/", {

                method: "POST",

                headers: {
                    "X-CSRFToken": obtener_csrf()
                },

                body: datos

            });

            if (!respuesta.ok) {

                throw new Error("No se pudo validar la cédula.");

            }

            const resultado = await respuesta.json();

            // Ignorar respuestas anteriores.
            if (numero_peticion !== peticion_cedula) return;

            if (resultado.existe) {

                cedula_valida = false;

                input_cedula.setCustomValidity(
                    "Ya existe una autoridad registrada con esta cédula."
                );

                input_cedula.classList.add("is-invalid");
                input_cedula.classList.remove("is-valid");

                mostrar_mensaje(
                    mensaje_cedula,
                    "Esta cédula ya se encuentra registrada.",
                    false
                );

            } else {

                cedula_valida = true;

                input_cedula.setCustomValidity("");

                input_cedula.classList.remove("is-invalid");
                input_cedula.classList.add("is-valid");

                mostrar_mensaje(
                    mensaje_cedula,
                    "La cédula de identidad está disponible.",
                    true
                );

            }

        } catch (error) {

            if (numero_peticion !== peticion_cedula) return;

            console.error("Error al validar la cédula:", error);

            cedula_valida = false;

            mostrar_mensaje(
                mensaje_cedula,
                "No fue posible comprobar la cédula. Intenta nuevamente.",
                false
            );

        } finally {

            if (numero_peticion === peticion_cedula) {

                validando_cedula = false;

                actualizar_boton();

            }

        }

    }

    select_nacionalidad.addEventListener("change", validar_cedula);

    input_cedula.addEventListener("input", validar_cedula);

    // =====================================================
    // FORMATO DE RESOLUCIÓN
    // Formato esperado: ABC12
    // =====================================================

    input_resolucion.addEventListener("input", function () {

        const valor = this.value
            .toUpperCase()
            .replace(/[^A-Z0-9]/g, "");

        const letras = valor
            .replace(/[^A-Z]/g, "")
            .slice(0, 3);

        const numeros = valor
            .replace(/[^0-9]/g, "")
            .slice(0, 2);

        this.value = letras + numeros;

        validar_resolucion();

    });

    // =====================================================
    // VALIDAR RESOLUCIÓN
    // =====================================================

    async function validar_resolucion() {

        const numero_peticion = ++peticion_resolucion;

        const resolucion = input_resolucion.value.trim();

        if (!resolucion) {

            resolucion_valida = true;
            validando_resolucion = false;

            input_resolucion.setCustomValidity("");

            input_resolucion.classList.remove(
                "is-valid",
                "is-invalid"
            );

            mostrar_mensaje(mensaje_resolucion, "");

            actualizar_boton();

            return true;

        }

        validando_resolucion = true;

        actualizar_boton();

        try {

            const datos = new FormData();

            datos.append("resolucion", resolucion);

            // Excluir la autoridad actual durante la modificación.
            if (esta_modificando()) {

                datos.append(
                    "id_autoridad",
                    usuario_seleccionado.value
                );

            }

            const respuesta = await fetch("/val_resolucion/", {

                method: "POST",

                headers: {
                    "X-CSRFToken": obtener_csrf()
                },

                body: datos

            });

            if (!respuesta.ok) {

                throw new Error("No se pudo validar la resolución.");

            }

            const resultado = await respuesta.json();

            if (numero_peticion !== peticion_resolucion) {
                return false;
            }

            if (resultado.existe) {

                resolucion_valida = false;

                input_resolucion.setCustomValidity(
                    "Ya existe una autoridad registrada con esta resolución."
                );

                input_resolucion.classList.add("is-invalid");
                input_resolucion.classList.remove("is-valid");

                mostrar_mensaje(
                    mensaje_resolucion,
                    "Esta resolución ya se encuentra registrada.",
                    false
                );

            } else {

                resolucion_valida = true;

                input_resolucion.setCustomValidity("");

                input_resolucion.classList.remove("is-invalid");
                input_resolucion.classList.add("is-valid");

                mostrar_mensaje(
                    mensaje_resolucion,
                    "La resolución está disponible.",
                    true
                );

            }

            return resolucion_valida;

        } catch (error) {

            if (numero_peticion !== peticion_resolucion) {
                return false;
            }

            console.error("Error al validar la resolución:", error);

            resolucion_valida = false;

            mostrar_mensaje(
                mensaje_resolucion,
                "No fue posible comprobar la resolución. Intenta nuevamente.",
                false
            );

            return false;

        } finally {

            if (numero_peticion === peticion_resolucion) {

                validando_resolucion = false;

                actualizar_boton();

            }

        }

    }

    // =====================================================
    // CARGAR CARGOS
    // =====================================================

    async function cargar_cargos() {

        const numero_peticion = ++peticion_cargos;

        cargando_cargos = true;

        actualizar_boton();

        try {

            const respuesta = await fetch("/cargo_asig_aut/");

            if (!respuesta.ok) {

                throw new Error("No se pudieron cargar los cargos.");

            }

            const datos = await respuesta.json();

            // Evitar que una carga anterior sobrescriba otra.
            if (numero_peticion !== peticion_cargos) return;

            select_cargo.innerHTML = "";

            const opcion_inicial = document.createElement("option");

            opcion_inicial.value = "";
            opcion_inicial.textContent = "Seleccione un cargo";

            select_cargo.appendChild(opcion_inicial);

            let cargos_disponibles = [];

            if (esta_modificando()) {

                // En modificación se permiten todos los cargos.
                cargos_disponibles = CARGOS;

            } else {

                // En registro solamente los cargos libres.
                cargos_disponibles = Array.isArray(datos.cargo)
                    ? datos.cargo
                    : [];

            }

            cargos_disponibles.forEach(nombre_cargo => {

                const opcion = document.createElement("option");

                opcion.value = nombre_cargo;
                opcion.textContent = nombre_cargo;

                select_cargo.appendChild(opcion);

            });

            if (cargos_disponibles.length === 0) {

                opcion_inicial.textContent = esta_modificando()
                    ? "No hay cargos configurados"
                    : "No hay cargos disponibles";

            }

        } catch (error) {

            if (numero_peticion !== peticion_cargos) return;

            console.error("Error al cargar los cargos:", error);

            select_cargo.innerHTML = `
                <option value="">Error al cargar los cargos</option>
            `;

        } finally {

            if (numero_peticion === peticion_cargos) {

                cargando_cargos = false;

                actualizar_boton();

            }

        }

    }

    // =====================================================
    // DETECTAR SELECCIÓN DE AUTORIDAD
    // =====================================================

    window.addEventListener("autoridadSeleccionada", async evento => {

        const autoridad = evento.detail;

        const numero_seleccion = ++peticion_seleccion;

        // Invalidar validaciones anteriores.
        peticion_cedula++;
        peticion_resolucion++;

        cargo_original = autoridad.cargo || "";

        cedula_valida = true;
        resolucion_valida = true;

        validando_cedula = false;
        validando_resolucion = false;

        input_cedula.setCustomValidity("");
        input_resolucion.setCustomValidity("");

        input_cedula.classList.remove("is-valid", "is-invalid");
        input_resolucion.classList.remove("is-valid", "is-invalid");

        mostrar_mensaje(mensaje_cedula, "");
        mostrar_mensaje(mensaje_resolucion, "");

        // Cargar las opciones de cargos.
        await cargar_cargos();

        // Comprobar que esta siga siendo la selección actual.
        if (numero_seleccion !== peticion_seleccion) return;

        // Garantizar que el cargo actual exista.
        const existe_cargo = Array.from(select_cargo.options).some(
            opcion => opcion.value === autoridad.cargo
        );

        if (!existe_cargo && autoridad.cargo) {

            const opcion = document.createElement("option");

            opcion.value = autoridad.cargo;
            opcion.textContent = autoridad.cargo;

            select_cargo.appendChild(opcion);

        }

        select_cargo.value = autoridad.cargo || "";

        // Validar la resolución de la autoridad seleccionada.
        await validar_resolucion();

        if (numero_seleccion !== peticion_seleccion) return;

        actualizar_boton();

    });

    // =====================================================
    // CONFIRMAR CAMBIO O INTERCAMBIO DE CARGO
    // =====================================================

    async function confirmar_cambio_cargo() {

        const cargo_nuevo = select_cargo.value;

        // No hubo cambio de cargo.
        if (cargo_nuevo === cargo_original) {

            return {
                continuar: true,
                cambiar: false
            };

        }

        const datos = new FormData();

        datos.append("cargo", cargo_nuevo);

        datos.append(
            "id_autoridad",
            usuario_seleccionado.value
        );

        try {

            const respuesta = await fetch("/cargo_user/", {

                method: "POST",

                headers: {
                    "X-CSRFToken": obtener_csrf()
                },

                body: datos

            });

            if (!respuesta.ok) {

                throw new Error(
                    "No se pudo comprobar la disponibilidad del cargo."
                );

            }

            const resultado = await respuesta.json();

            let titulo;
            let mensaje;

            if (resultado.existe) {

                const autoridad_afectada = resultado.autoridad || {};

                const nombre_afectado = [
                    autoridad_afectada.nombres || "",
                    autoridad_afectada.apellidos || ""
                ].join(" ").trim();

                titulo = "¿Intercambiar los cargos?";

                mensaje =
                    `El cargo de ${cargo_nuevo} ya está asignado` +
                    (nombre_afectado ? ` a ${nombre_afectado}` : " a otra autoridad") +
                    ". ¿Deseas intercambiar los cargos entre ambas autoridades?";

            } else {

                titulo = "¿Cambiar el cargo?";

                mensaje =
                    `¿Deseas cambiar el cargo de ${cargo_original} ` +
                    `a ${cargo_nuevo}?`;

            }

            const confirmado = await confirmar_accion(titulo, mensaje);

            if (!confirmado) {

                return {
                    continuar: false,
                    cambiar: false
                };

            }

            return {
                continuar: true,
                cambiar: true
            };

        } catch (error) {

            console.error("Error al comprobar el cargo:", error);

            await mostrar_notificacion({

                title: "Error",
                text: "No fue posible comprobar la disponibilidad del cargo.",
                icon: "error"

            });

            return {
                continuar: false,
                cambiar: false
            };

        }

    }

    // =====================================================
    // ENVIAR REGISTRO
    // =====================================================

    async function registrar_autoridad() {

        const datos = new FormData(formulario);

        const respuesta = await fetch("/reg_auts/", {

            method: "POST",

            headers: {
                "X-CSRFToken": obtener_csrf()
            },

            body: datos

        });

        if (!respuesta.ok) {

            throw new Error("No se pudo registrar la autoridad.");

        }

        return await respuesta.json();

    }

    // =====================================================
    // ENVIAR MODIFICACIÓN
    // =====================================================

    async function modificar_autoridad(cambiar_cargo) {

        const datos = new FormData();

        datos.append(
            "usuarioseleccionado",
            usuario_seleccionado.value
        );

        datos.append(
            "nombres_actualizar",
            input_nombres.value.trim()
        );

        datos.append(
            "apellidos_actualizar",
            input_apellidos.value.trim()
        );

        datos.append(
            "genero_actualizar",
            select_genero.value
        );

        datos.append(
            "cargo_actualizar",
            select_cargo.value
        );

        datos.append(
            "resolucion_actualizar",
            input_resolucion.value.trim()
        );

        datos.append(
            "cambiar_cargo",
            cambiar_cargo ? "true" : "false"
        );

        const respuesta = await fetch("/act_datos_aut/", {

            method: "POST",

            headers: {
                "X-CSRFToken": obtener_csrf()
            },

            body: datos

        });

        if (!respuesta.ok) {

            throw new Error(
                "No se pudieron actualizar los datos de la autoridad."
            );

        }

        return await respuesta.json();

    }

    // =====================================================
    // ENVÍO GENERAL DEL FORMULARIO
    // =====================================================

    formulario.addEventListener("submit", async evento => {

        evento.preventDefault();

        if (enviando_formulario) return;

        // Esperar a que terminen las validaciones.
        const resolucion_correcta = await validar_resolucion();

        let cedula_correcta = true;

        if (!esta_modificando()) {

            await validar_cedula();

            cedula_correcta = cedula_valida;

        }

        if (
            !formulario.checkValidity() ||
            !cedula_correcta ||
            !resolucion_correcta ||
            !cedula_valida ||
            !resolucion_valida ||
            validando_cedula ||
            validando_resolucion ||
            cargando_cargos
        ) {

            formulario.reportValidity();

            actualizar_boton();

            return;

        }

        enviando_formulario = true;

        actualizar_boton();

        try {

            let resultado;

            if (esta_modificando()) {

                const confirmacion = await confirmar_cambio_cargo();

                // Si se cancela el cambio, no se envía la modificación.
                if (!confirmacion.continuar) return;

                resultado = await modificar_autoridad(
                    confirmacion.cambiar
                );

            } else {

                resultado = await registrar_autoridad();

            }

            await mostrar_notificacion({

                text: resultado.descripcion,
                icon: resultado.icon,
                title: resultado.title,
                allowOutsideClick: false,
                allowEscapeKey: false

            });

            if (resultado.estado === "exito") {

                // Actualizar la tabla.
                if (typeof window.obtener_autoridades === "function") {

                    await window.obtener_autoridades();

                }

                // Restablecer el formulario.
                if (esta_modificando()) {

                    if (
                        typeof window.cancelar_modificacion_autoridad === "function"
                    ) {

                        window.cancelar_modificacion_autoridad();

                    }

                } else {

                    formulario.reset();

                }

                cedula_valida = true;
                resolucion_valida = true;

                cargo_original = "";

                input_cedula.setCustomValidity("");
                input_resolucion.setCustomValidity("");

                input_cedula.classList.remove("is-valid", "is-invalid");
                input_resolucion.classList.remove("is-valid", "is-invalid");

                mostrar_mensaje(mensaje_cedula, "");
                mostrar_mensaje(mensaje_resolucion, "");

            }

        } catch (error) {

            console.error(
                "Error al procesar la autoridad:",
                error
            );

            await mostrar_notificacion({

                title: "Error",
                text: "Ocurrió un problema al procesar la información.",
                icon: "error"

            });

        } finally {

            enviando_formulario = false;

            actualizar_boton();

        }

    });

    // =====================================================
    // RESTABLECER VALIDACIONES AL CANCELAR O REINICIAR
    // =====================================================

    formulario.addEventListener("reset", () => {

        const numero_reset = ++secuencia_reset;

        // Invalidar peticiones pendientes.
        peticion_cedula++;
        peticion_resolucion++;
        peticion_seleccion++;

        cedula_valida = true;
        resolucion_valida = true;

        validando_cedula = false;
        validando_resolucion = false;

        cargo_original = "";

        setTimeout(async () => {

            // Evitar que un reset anterior interfiera con otra selección.
            if (numero_reset !== secuencia_reset) return;

            input_cedula.disabled = false;
            select_nacionalidad.disabled = false;

            input_cedula.setCustomValidity("");
            input_resolucion.setCustomValidity("");

            input_cedula.classList.remove("is-valid", "is-invalid");
            input_resolucion.classList.remove("is-valid", "is-invalid");

            mostrar_mensaje(mensaje_cedula, "");
            mostrar_mensaje(mensaje_resolucion, "");

            // Actualizar el estado interno de cedula_identidad.js.
            select_nacionalidad.dispatchEvent(
                new Event("change", { bubbles: true })
            );

            await cargar_cargos();

            actualizar_boton();

        }, 0);

    });

    // =====================================================
    // INICIALIZACIÓN
    // =====================================================

    cargar_cargos();

    actualizar_boton();

});