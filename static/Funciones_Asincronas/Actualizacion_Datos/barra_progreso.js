
document.addEventListener("DOMContentLoaded", () => {

    /*
    =========================================================
    ELEMENTOS DEL FORMULARIO
    =========================================================
    */

    const seccion = document.getElementById("completar_registro");
    const formulario = document.getElementById("formulario_registro");

    if (!seccion || !formulario) {
        console.error("No se encontró el formulario de registro.");
        return;
    }

    const pasos = Array.from(
        formulario.querySelectorAll(".paso_formulario")
    );

    const barra = Array.from(
        seccion.querySelectorAll(".paso_barra")
    );

    const btnAnterior = document.getElementById("btn_anterior");
    const btnSiguiente = document.getElementById("btn_siguiente");
    const btnRegistro = document.getElementById("btn_registro");

    if (
        pasos.length === 0 ||
        !btnAnterior ||
        !btnSiguiente ||
        !btnRegistro
    ) {
        console.error("Faltan elementos necesarios para la navegación.");
        return;
    }

    if (barra.length !== pasos.length) {
        console.warn(
            `Hay ${pasos.length} formularios y ${barra.length} indicadores.`
        );
    }

    let pasoActual = -1;
    let animando = false;

    // Evitar la validación automática de campos ocultos.
    formulario.noValidate = true;


    /*
    =========================================================
    ACTUALIZAR BARRA DE PROGRESO
    =========================================================
    */

    function actualizarBarra(index) {

        barra.forEach((elemento, i) => {

            elemento.classList.remove("activo", "completado");

            if (i < index) {
                elemento.classList.add("completado");
            }

            if (i === index) {
                elemento.classList.add("activo");
            }

        });

    }


    /*
    =========================================================
    ACTUALIZAR BOTONES
    =========================================================
    */

    function actualizarBotones(index) {

        const esPrimerPaso = index === 0;
        const esUltimoPaso = index === pasos.length - 1;

        btnAnterior.style.display = esPrimerPaso
            ? "none"
            : "inline-flex";

        btnSiguiente.style.display = esUltimoPaso
            ? "none"
            : "inline-flex";

        btnRegistro.style.display = esUltimoPaso
            ? "inline-flex"
            : "none";

        btnAnterior.disabled = animando;
        btnSiguiente.disabled = animando;

    }

    function actualizarRequisitosContacto() {

        // Grupos de teléfono.
        const telefonos = [
            {
                prefijo: document.getElementById("prefijo_principal"),
                numero: document.getElementById("numero_telefonico_principal")
            },
            {
                prefijo: document.getElementById("prefijo_secundario"),
                numero: document.getElementById("numero_telefonico_secundario")
            }
        ];

        // Grupos de correo electrónico.
        const correos = [
            {
                usuario: document.getElementById("correo_principal"),
                dominio: document.getElementById("dominio_principal")
            },
            {
                usuario: document.getElementById("correo_secundario"),
                dominio: document.getElementById("dominio_secundario")
            }
        ];

        // Validación condicional de teléfonos.
        telefonos.forEach(({ prefijo, numero }) => {

            if (!prefijo || !numero) return;

            const tienePrefijo = prefijo.value.trim() !== "";
            const tieneNumero = numero.value.trim() !== "";

            const iniciado = tienePrefijo || tieneNumero;

            prefijo.required = iniciado;
            numero.required = iniciado;

            if (iniciado && tieneNumero) {
                const numeroLimpio = numero.value.trim();

                numero.setCustomValidity(
                    /^\d{7,15}$/.test(numeroLimpio)
                        ? ""
                        : "Introduzca un número telefónico válido de entre 7 y 15 dígitos."
                );
            } else {
                numero.setCustomValidity("");
            }
        });

        // Validación condicional de correos.
        correos.forEach(({ usuario, dominio }) => {

            if (!usuario || !dominio) return;

            const tieneUsuario = usuario.value.trim() !== "";

            // Un dominio solo cuenta si se seleccionó una opción válida.
            const tieneDominio =
                dominio.value.trim() !== "" &&
                dominio.selectedIndex >= 0 &&
                dominio.options[dominio.selectedIndex].value.trim() !== "";

            const iniciado = tieneUsuario || tieneDominio;

            usuario.required = iniciado;
            dominio.required = iniciado;

            // Evitar espacios y otro símbolo @ dentro del usuario.
            if (iniciado && tieneUsuario) {
                const correoLocal = usuario.value.trim();

                usuario.setCustomValidity(
                    /^[^\s@]+$/.test(correoLocal)
                        ? ""
                        : "Introduzca correctamente el nombre del correo electrónico."
                );
            } else {
                usuario.setCustomValidity("");
            }
        });
    }

    // Aplicar los requisitos desde el inicio.
    actualizarRequisitosContacto();


    /*
    =========================================================
    MOSTRAR PASO CON ANIMACIÓN
    =========================================================
    */

    function mostrarPaso(index) {
        if (
            animando ||
            index < 0 ||
            index >= pasos.length ||
            index === pasoActual
        ) {
            return;
        }

        const pasoAnterior = pasos[pasoActual];
        const siguientePaso = pasos[index];
        const direccion = index > pasoActual ? 1 : -1;

        animando = true;

        // Ocultar el paso anterior, si existe.
        if (pasoAnterior) {
            pasoAnterior.classList.remove("activo");
        }

        // Mostrar el paso seleccionado.
        siguientePaso.classList.add("activo");
        pasoActual = index;

        actualizarBarra(index);
        actualizarBotones(index);

        // Respetar las preferencias de accesibilidad.
        const movimientoReducido = window.matchMedia(
            "(prefers-reduced-motion: reduce)"
        ).matches;

        if (movimientoReducido) {
            animando = false;
            actualizarBotones(pasoActual);
            return;
        }

        const animacion = siguientePaso.animate(
            [
                {
                    opacity: 0,
                    transform: `translateX(${direccion * 60}px)`
                },
                {
                    opacity: 1,
                    transform: "translateX(0)"
                }
            ],
            {
                duration: 400,
                easing: "cubic-bezier(0.22, 1, 0.36, 1)"
            }
        );

        animacion.onfinish = () => {
            animando = false;
            actualizarBotones(pasoActual);
        };

        animacion.oncancel = () => {
            animando = false;
            actualizarBotones(pasoActual);
        };
    }

    /*
    =========================================================
    COMPROBAR CAMPOS OCULTOS
    =========================================================
    */

    function campoEstaOculto(campo) {

        return (
            campo.type === "hidden" ||
            campo.hidden ||
            campo.closest("[hidden]") !== null
        );

    }


    /*
    =========================================================
    VALIDAR UN PASO
    =========================================================
    */

    function validarPaso(index, mostrarAviso = true) {

        const paso = pasos[index];

        if (!paso) return false;

        // Validación especial del paso de Núcleo y PNF.
        if (paso.id === "contenedor_pnfs_cursar") {

            const nucleoSeleccionado = paso.querySelector(
                'input[name="nucleo_seleccionado"]:checked'
            );

            if (nucleoSeleccionado) {

                const contenedorPNF = document.getElementById(
                    `contenedor_pnfs_${nucleoSeleccionado.value}`
                );

                const estado = contenedorPNF?.dataset.estado;

                // Evitar avanzar mientras se cargan los PNF.
                if (estado === "cargando" || !estado) {

                    if (mostrarAviso) {

                        const mensaje = "Espere mientras se cargan los programas de formación.";

                        if (typeof Swal !== "undefined") {
                            Swal.fire({
                                title: "Cargando programas",
                                text: mensaje,
                                icon: "info",
                                confirmButtonText: "Entendido",
                                confirmButtonColor: "#2563EB"
                            });
                        } else {
                            alert(mensaje);
                        }
                    }

                    return false;
                }

                // Comprobar errores o ausencia de programas.
                if (estado !== "listo") {

                    if (mostrarAviso) {

                        const mensaje = estado === "vacio"
                            ? "No hay programas de formación disponibles para el núcleo seleccionado."
                            : "No se pudieron cargar los PNF. Seleccione nuevamente el núcleo para intentarlo otra vez.";

                        if (typeof Swal !== "undefined") {
                            Swal.fire({
                                title: "Programas no disponibles",
                                text: mensaje,
                                icon: "warning",
                                confirmButtonText: "Entendido",
                                confirmButtonColor: "#2563EB"
                            });
                        } else {
                            alert(mensaje);
                        }
                    }

                    return false;
                }

                // Comprobar que se haya seleccionado un PNF.
                const pnfSeleccionado = contenedorPNF.querySelector(
                    'input[name="pnf_seleccionado"]:checked'
                );

                if (!pnfSeleccionado) {

                    if (mostrarAviso) {

                        const mensaje = "Debe seleccionar un Programa Nacional de Formación (PNF).";

                        if (typeof Swal !== "undefined") {
                            Swal.fire({
                                title: "Selección requerida",
                                text: mensaje,
                                icon: "warning",
                                confirmButtonText: "Entendido",
                                confirmButtonColor: "#2563EB"
                            });
                        } else {
                            alert(mensaje);
                        }
                    }

                    return false;
                }
            }
        }

        // Validación general de los campos del paso.
        const campos = Array.from(
            paso.querySelectorAll("input, select, textarea")
        );

        let primerCampoInvalido = null;

        campos.forEach(campo => {

            if (
                campo.disabled ||
                campoEstaOculto(campo) ||
                !campo.willValidate
            ) {
                campo.classList.remove("error");
                campo.removeAttribute("aria-invalid");
                return;
            }

            const invalido = !campo.checkValidity();

            campo.classList.toggle("error", invalido);

            if (invalido) {

                campo.setAttribute("aria-invalid", "true");

                if (!primerCampoInvalido) {
                    primerCampoInvalido = campo;
                }

            } else {

                campo.removeAttribute("aria-invalid");

            }

        });

        if (primerCampoInvalido) {

            if (mostrarAviso) {

                const enfocarCampo = () => {
                    primerCampoInvalido.focus();
                };

                if (typeof Swal !== "undefined") {

                    Swal.fire({
                        title: "Campos incompletos",
                        text: "Debe completar correctamente los campos requeridos antes de continuar.",
                        icon: "warning",
                        confirmButtonText: "Entendido",
                        confirmButtonColor: "#2563EB",
                        allowOutsideClick: false,
                        allowEscapeKey: false
                    }).then(enfocarCampo);

                } else {

                    alert(
                        "Debe completar correctamente los campos requeridos antes de continuar."
                    );

                    enfocarCampo();

                }

            }

            return false;
        }

        return true;
    }


    /*
    =========================================================
    BOTÓN SIGUIENTE
    =========================================================
    */

    btnSiguiente.addEventListener("click", () => {

        if (animando) {
            return;
        }

        if (!validarPaso(pasoActual)) {
            return;
        }

        if (pasoActual < pasos.length - 1) {
            mostrarPaso(pasoActual + 1);
        }

    });


    /*
    =========================================================
    BOTÓN ANTERIOR
    =========================================================
    */

    btnAnterior.addEventListener("click", () => {

        if (animando) {
            return;
        }

        if (pasoActual > 0) {
            mostrarPaso(pasoActual - 1);
        }

    });


    /*
    =========================================================
    LIMPIAR ERRORES AL MODIFICAR CAMPOS
    =========================================================
    */

    function limpiarError(campo) {

        if (!campo || !campo.matches("input, select, textarea")) {
            return;
        }

        if (campo.willValidate && campo.checkValidity()) {

            campo.classList.remove("error");
            campo.removeAttribute("aria-invalid");

        }

    }

    formulario.addEventListener("input", event => {
        actualizarRequisitosContacto();
        limpiarError(event.target);
    });

    formulario.addEventListener("change", event => {

        actualizarRequisitosContacto();

        const campo = event.target;

        if (campo.type === "radio" && campo.name) {

            formulario
                .querySelectorAll('input[type="radio"]')
                .forEach(radio => {

                    if (radio.name === campo.name) {
                        limpiarError(radio);
                    }

                });

        } else {

            limpiarError(campo);

        }

    });


    /*
    =========================================================
    VALIDACIÓN FINAL ANTES DE ENVIAR
    =========================================================
    */

    formulario.addEventListener("submit", event => {

        for (let i = 0; i < pasos.length; i++) {

            if (!validarPaso(i, false)) {

                event.preventDefault();

                const pasoInvalido = pasos[i];

                const primerInvalido = Array.from(
                    pasoInvalido.querySelectorAll(
                        "input, select, textarea"
                    )
                ).find(campo => {

                    return (
                        !campo.disabled &&
                        !campoEstaOculto(campo) &&
                        campo.willValidate &&
                        !campo.checkValidity()
                    );

                });

                // Mostrar el paso que contiene el campo inválido.
                if (i !== pasoActual) {
                    mostrarPaso(i);
                }

                const enfocarCampo = () => {

                    if (primerInvalido) {
                        primerInvalido.focus();
                    }

                };

                const mostrarAviso = () => {

                    if (typeof Swal !== "undefined") {

                        Swal.fire({
                            title: "Registro incompleto",
                            text: "Hay información pendiente. Revise el paso indicado antes de finalizar.",
                            icon: "warning",
                            confirmButtonText: "Entendido",
                            confirmButtonColor: "#2563EB"
                        }).then(() => {

                            // Esperar a que termine la animación.
                            setTimeout(enfocarCampo, 420);

                        });

                    } else {

                        alert(
                            "Hay información pendiente. Revise el paso indicado."
                        );

                        setTimeout(enfocarCampo, 420);

                    }

                };

                mostrarAviso();

                return;
            }

        }

    });


    /*
    =========================================================
    INICIALIZAR FORMULARIO
    =========================================================
    */

    // Establecer directamente el primer paso.
    // No utilizar mostrarPaso(0), porque el paso actual ya es 0.

    pasos.forEach((paso, index) => {

        paso.classList.toggle("activo", index === 0);

        paso.classList.remove(
            "animacion-entrada-derecha",
            "animacion-entrada-izquierda"
        );

    });

    pasoActual = 0;
    animando = false;

    actualizarBarra(0);
    actualizarBotones(0);

    console.log(
        `Formulario iniciado correctamente. Pasos: ${pasos.length}`
    );

});
