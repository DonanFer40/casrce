document.addEventListener("DOMContentLoaded", () => {

    const pasos = document.querySelectorAll(".paso_formulario");
    const barra = document.querySelectorAll(".paso_barra");

    const btnAnterior = document.getElementById("btn_anterior");
    const btnSiguiente = document.getElementById("btn_siguiente");
    const btnRegistro = document.getElementById("btn_registro");

    let pasoActual = 0;
    let animando = false;


    console.log("Cantidad de pasos:", pasos.length);

    pasos.forEach((paso, index) => {
        console.log(index, paso.id, paso.className);
    });


    /*
    =========================================================
    ANIMACIÓN DE LOS PASOS
    =========================================================
    */

    function mostrarPaso(index, direccion = "siguiente") {

        if (animando || index < 0 || index >= pasos.length) {
            return;
        }

        const pasoAnterior = pasos[pasoActual];
        const pasoNuevo = pasos[index];

        if (pasoAnterior === pasoNuevo) {
            actualizarBarra(index);
            actualizarBotones(index);
            return;
        }

        animando = true;


        /*
        -----------------------------------------------------
        Limpiar estados de animación anteriores
        -----------------------------------------------------
        */

        pasos.forEach(paso => {
            paso.classList.remove(
                "activo",
                "entrando-derecha",
                "entrando-izquierda",
                "saliendo-derecha",
                "saliendo-izquierda"
            );
        });


        /*
        -----------------------------------------------------
        Preparar dirección de movimiento
        -----------------------------------------------------

        Siguiente:
            actual → izquierda
            nuevo  ← derecha

        Anterior:
            actual → derecha
            nuevo  ← izquierda
        -----------------------------------------------------
        */

        if (direccion === "siguiente") {

            pasoAnterior.classList.add("activo", "saliendo-izquierda");
            pasoNuevo.classList.add("entrando-derecha");

        } else {

            pasoAnterior.classList.add("activo", "saliendo-derecha");
            pasoNuevo.classList.add("entrando-izquierda");

        }


        /*
        -----------------------------------------------------
        Forzar el navegador a reconocer el estado inicial
        antes de activar la transición.
        -----------------------------------------------------
        */

        void pasoNuevo.offsetWidth;


        /*
        -----------------------------------------------------
        Activar el movimiento
        -----------------------------------------------------
        */

        requestAnimationFrame(() => {

            pasoAnterior.classList.remove("activo");

            pasoNuevo.classList.remove(
                "entrando-derecha",
                "entrando-izquierda"
            );

            pasoNuevo.classList.add("activo");

        });


        /*
        -----------------------------------------------------
        Esperar a que termine la animación
        -----------------------------------------------------
        */

        setTimeout(() => {

            pasos.forEach(paso => {
                paso.classList.remove(
                    "saliendo-derecha",
                    "saliendo-izquierda",
                    "entrando-derecha",
                    "entrando-izquierda"
                );
            });

            pasoActual = index;
            animando = false;

            actualizarBarra(index);
            actualizarBotones(index);

        }, 450);
    }


    /*
    =========================================================
    BARRA DE PROGRESO
    =========================================================
    */

    function actualizarBarra(index) {

        barra.forEach((item, i) => {

            item.classList.remove("activo");

            if (i < index) {
                item.classList.add("completado");
            } else {
                item.classList.remove("completado");
            }

            if (i === index) {
                item.classList.add("activo");
            }

        });

    }


    /*
    =========================================================
    BOTONES DE NAVEGACIÓN
    =========================================================
    */

    function actualizarBotones(index) {

        btnAnterior.style.display =
            index === 0 ? "none" : "block";


        btnSiguiente.style.display =
            index === pasos.length - 1 ? "none" : "block";


        btnRegistro.style.display =
            index === pasos.length - 1 ? "block" : "none";

    }


    /*
    =========================================================
    VALIDACIÓN DEL PASO ACTUAL
    =========================================================
    */

    function validarPasoActual() {

        const paso = pasos[pasoActual];

        const campos = paso.querySelectorAll(
            "input, select, textarea"
        );

        let valido = true;
        let primerCampo = null;


        campos.forEach(campo => {

            if (
                campo.hasAttribute("required") &&
                !campo.value.trim()
            ) {

                campo.classList.add("error");

                if (!primerCampo) {
                    primerCampo = campo;
                }

                valido = false;

            } else {

                campo.classList.remove("error");

            }

        });


        if (primerCampo) {
            primerCampo.focus();
        }


        return valido;

    }


    /*
    =========================================================
    SIGUIENTE
    =========================================================
    */

    btnSiguiente.addEventListener("click", () => {

        if (animando) {
            return;
        }


        if (!validarPasoActual()) {

            Swal.fire({
                title: "Campos incompletos",
                text: "Debe completar todos los campos obligatorios antes de continuar.",
                icon: "warning",
                confirmButtonText: "Entendido",
                confirmButtonColor: "#2563eb",
                allowOutsideClick: false,
                allowEscapeKey: false
            });

            return;
        }


        if (pasoActual < pasos.length - 1) {

            mostrarPaso(
                pasoActual + 1,
                "siguiente"
            );

        }

    });


    /*
    =========================================================
    ANTERIOR
    =========================================================
    */

    btnAnterior.addEventListener("click", () => {

        if (animando) {
            return;
        }


        if (pasoActual > 0) {

            mostrarPaso(
                pasoActual - 1,
                "anterior"
            );

        }

    });


    /*
    =========================================================
    QUITAR ERROR AL MODIFICAR UN CAMPO
    =========================================================
    */

    document
        .querySelectorAll("input, select, textarea")
        .forEach(campo => {

            campo.addEventListener("input", () => {
                campo.classList.remove("error");
            });

            campo.addEventListener("change", () => {
                campo.classList.remove("error");
            });

        });


    /*
    =========================================================
    INICIAR FORMULARIO
    =========================================================
    */

    pasos.forEach((paso, index) => {

        paso.classList.remove(
            "activo",
            "entrando-derecha",
            "entrando-izquierda",
            "saliendo-derecha",
            "saliendo-izquierda"
        );

        if (index === 0) {
            paso.classList.add("activo");
        }

    });


    actualizarBarra(0);
    actualizarBotones(0);

});