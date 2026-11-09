document.addEventListener("DOMContentLoaded", () => {

    // =========================================
    // ELEMENTOS DEL FORMULARIO
    // =========================================

    const formulario = document.getElementById("formulario_registrar");

    const input_id_pnf = document.getElementById("id_pnf");
    const input_nombre = document.getElementById("registrar_nombre_pnf");
    const input_codigo = document.getElementById("registrar_codigo_pnf");
    const input_periodo = document.getElementById("registrar_periodo_academico");

    const mensaje_nombre = document.getElementById("mensaje_nombre_pnf");
    const mensaje_codigo = document.getElementById("mensaje_codigo_pnf");

    const aviso_edicion = document.getElementById("aviso_modo_edicion");

    const btn_registro = document.getElementById("btn_registro");
    const btn_cancelar = document.getElementById("btn_cancelar_edicion");

    const texto_btn = document.getElementById("texto_btn_registro");
    const icono_btn = document.getElementById("icono_btn_registro");
    const spinner = document.querySelector(".director-pnf-gestion-carsce-spinner");

    const csrf = document.querySelector("[name=csrfmiddlewaretoken]")?.value;

    let modoEdicion = false;
    let enviando = false;

    // =========================================
    // NOTIFICACIONES
    // =========================================

    async function notificar(resultado) {

        await NotificacionesCASRCE.mostrar({
            title: resultado.title,
            text: resultado.descripcion,
            icon: resultado.icon,
            allowOutsideClick: false,
            allowEscapeKey: false
        });

    }

    // =========================================
    // INDICADOR DE CARGA
    // =========================================

    function mostrarCarga(estado) {

        enviando = estado;

        btn_registro.disabled = estado;
        btn_cancelar.disabled = estado;

        spinner.hidden = !estado;
        icono_btn.hidden = estado;

        if (estado) {

            texto_btn.textContent = modoEdicion
                ? "Guardando cambios..."
                : "Registrando...";

        } else {

            texto_btn.textContent = modoEdicion
                ? "Guardar cambios"
                : "Registrar PNF";

        }

    }

    // =========================================
    // LIMPIAR VALIDACIONES
    // =========================================

    function limpiarValidaciones() {

        input_nombre.setCustomValidity("");
        input_codigo.setCustomValidity("");

        input_nombre.classList.remove("is-valid", "is-invalid");
        input_codigo.classList.remove("is-valid", "is-invalid");

        mensaje_nombre.textContent = "";
        mensaje_codigo.textContent = "";

        btn_registro.disabled = false;

    }

    // =========================================
    // CAMBIAR ENTRE REGISTRO Y MODIFICACIÓN
    // =========================================

    function cambiarModoEdicion(estado) {

        modoEdicion = estado;

        aviso_edicion.hidden = !estado;
        btn_cancelar.hidden = !estado;

        input_id_pnf.value = estado ? input_id_pnf.value : "";

        texto_btn.textContent = estado
            ? "Guardar cambios"
            : "Registrar PNF";

        icono_btn.className = estado
            ? "fa-solid fa-floppy-disk"
            : "fa-solid fa-plus";

        // El código no se modifica durante la actualización.
        input_codigo.readOnly = estado;

        if (estado) {

            input_codigo.classList.remove("is-invalid");
            input_codigo.setCustomValidity("");
            mensaje_codigo.textContent = "";

        } else {

            input_codigo.readOnly = false;

        }

    }

    // =========================================
    // CANCELAR MODIFICACIÓN
    // =========================================

    function cancelarEdicion() {

        formulario.reset();

        input_id_pnf.value = "";

        limpiarValidaciones();

        cambiarModoEdicion(false);

        mostrarCarga(false);

    }

    btn_cancelar.addEventListener("click", cancelarEdicion);

    // =========================================
    // VALIDAR NOMBRE DEL PNF
    // =========================================

    async function validarNombre() {

        if (!input_nombre.value.trim()) {
            mensaje_nombre.textContent = "";
            return true;
        }

        try {

            const datos = new FormData();

            datos.append("nombrepnf", input_nombre.value.trim());
            datos.append("id_pnf", input_id_pnf.value);

            const respuesta = await fetch("/nombre_pnf/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrf
                },
                body: datos
            });

            const resultado = await respuesta.json();

            if (resultado.existe) {

                input_nombre.setCustomValidity(
                    "Ya existe un PNF con ese nombre."
                );

                input_nombre.classList.add("is-invalid");
                input_nombre.classList.remove("is-valid");

                mensaje_nombre.textContent =
                    "Ya existe un PNF con el mismo nombre.";

                mensaje_nombre.style.color = "#dc3545";

                return false;

            }

            input_nombre.setCustomValidity("");

            input_nombre.classList.add("is-valid");
            input_nombre.classList.remove("is-invalid");

            mensaje_nombre.textContent =
                "El nombre del PNF está disponible.";

            mensaje_nombre.style.color = "#198754";

            return true;

        } catch (error) {

            console.error("Error validando nombre:", error);

            return false;

        }

    }

    // =========================================
    // VALIDAR CÓDIGO DEL PNF
    // =========================================

    async function validarCodigo() {

        if (modoEdicion) {
            return true;
        }

        if (!input_codigo.value.trim()) {
            mensaje_codigo.textContent = "";
            return true;
        }

        try {

            const datos = new FormData();

            datos.append("codigopnf", input_codigo.value);
            datos.append("id_pnf", input_id_pnf.value);

            const respuesta = await fetch("/codigo_pnf/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrf
                },
                body: datos
            });

            const resultado = await respuesta.json();

            if (resultado.existe) {

                input_codigo.setCustomValidity(
                    "Ya existe un PNF con ese código."
                );

                input_codigo.classList.add("is-invalid");
                input_codigo.classList.remove("is-valid");

                mensaje_codigo.textContent =
                    "Ya existe un PNF con el mismo código.";

                mensaje_codigo.style.color = "#dc3545";

                return false;

            }

            input_codigo.setCustomValidity("");

            input_codigo.classList.add("is-valid");
            input_codigo.classList.remove("is-invalid");

            mensaje_codigo.textContent =
                "El código del PNF está disponible.";

            mensaje_codigo.style.color = "#198754";

            return true;

        } catch (error) {

            console.error("Error validando código:", error);

            return false;

        }

    }

    // =========================================
    // FORMATO DE LOS CAMPOS
    // =========================================

    input_nombre.addEventListener("input", () => {

        input_nombre.value = input_nombre.value.replace(
            /[^a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s]/g,
            ""
        );

        input_nombre.setCustomValidity("");
        input_nombre.classList.remove("is-valid", "is-invalid");

        mensaje_nombre.textContent = "";

    });

    input_codigo.addEventListener("input", () => {

        input_codigo.value = input_codigo.value
            .toUpperCase()
            .replace(/[^A-Z0-9]/g, "")
            .slice(0, 8);

        input_codigo.setCustomValidity("");
        input_codigo.classList.remove("is-valid", "is-invalid");

        mensaje_codigo.textContent = "";

    });

    input_nombre.addEventListener("blur", validarNombre);
    input_codigo.addEventListener("blur", validarCodigo);

    // =========================================
    // CARGAR DATOS EN EL FORMULARIO
    // =========================================

    window.seleccionarPNF = async function (codigo) {

        try {

            const datos = new FormData();

            datos.append("codigo", codigo);

            const respuesta = await fetch("/datos_pnf/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrf
                },
                body: datos
            });

            const resultado = await respuesta.json();

            if (resultado.estado !== "exito") {

                await notificar(resultado);
                return;

            }

            cancelarEdicion();

            input_id_pnf.value = resultado.pnf.id;
            input_nombre.value = resultado.pnf.nombre;
            input_codigo.value = codigo;
            input_periodo.value = resultado.pnf.periodo_academico;

            cambiarModoEdicion(true);

            limpiarValidaciones();

            // El código queda bloqueado durante la modificación.
            input_codigo.readOnly = true;

            input_nombre.focus();

        } catch (error) {

            console.error("Error al seleccionar PNF:", error);

            await notificar({
                estado: "fallo",
                icon: "error",
                title: "Error",
                descripcion: "No fue posible cargar los datos del PNF seleccionado."
            });

        }

    };

    // =========================================
    // ENVIAR FORMULARIO
    // =========================================

    formulario.addEventListener("submit", async (e) => {

        e.preventDefault();

        if (enviando) return;

        try {

            const nombreValido = await validarNombre();
            const codigoValido = await validarCodigo();

            if (!nombreValido || !codigoValido) {
                return;
            }

            if (!formulario.reportValidity()) {
                return;
            }

            mostrarCarga(true);

            const datos = new FormData(formulario);

            const url = modoEdicion
                ? "/act_pnf/"
                : "/reg_pnf/";

            const respuesta = await fetch(url, {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrf
                },
                body: datos
            });

            const resultado = await respuesta.json();

            mostrarCarga(false);

            await notificar(resultado);

            if (resultado.estado === "exito") {

                cancelarEdicion();

                // Actualizar la tabla sin recargar la página.
                if (typeof window.cargarPNFs === "function") {
                    await window.cargarPNFs();
                }

            }

        } catch (error) {

            console.error("Error al procesar PNF:", error);

            mostrarCarga(false);

            await notificar({
                estado: "fallo",
                icon: "error",
                title: "Error",
                descripcion: "Ocurrió un problema al procesar la información."
            });

        }

    });

});