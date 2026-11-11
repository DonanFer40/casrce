
/* =========================================================
   VALIDACION.JS - Validaciones Generales de CASRCE
   ========================================================= */

window.Validaciones = window.Validaciones || {

    // Permitir únicamente letras y espacios.
    permitirSoloLetras(input) {
        input.value = input.value.replace(/[^\p{L}\p{M}\s]/gu, "");
    },

    // Permitir únicamente números.
    permitirSoloNumeros(input) {
        input.value = input.value.replace(/\D/g, "");
    },

    // Permitir letras, números y espacios.
    permitirAlfanumerico(input) {
        input.value = input.value.replace(/[^\p{L}\p{M}0-9\s]/gu, "");
    },

    // Permitir únicamente minúsculas y números.
    permitirSoloMinusculas(input) {
        input.value = input.value.replace(/[^a-z0-9]/g, "");
    },

    // Exigir complejidad mínima para contraseñas nuevas.
    esContraseniaSegura(contrasenia) {
        return (
            contrasenia.length >= 8 &&
            /\p{Lu}/u.test(contrasenia) &&
            /\p{Ll}/u.test(contrasenia) &&
            /\p{Nd}/u.test(contrasenia) &&
            /[^\p{L}\p{N}\s]/u.test(contrasenia)
        );
    },

    // Primera letra de cada palabra en mayúscula.
    normalizarNombre(input) {
        const posicion = input.selectionStart;

        input.value = input.value
            .toLocaleLowerCase("es")
            .replace(/(^|\s)(\p{L})/gu, (coincidencia, espacio, letra) => {
                return espacio + letra.toLocaleUpperCase("es");
            });

        input.setSelectionRange(posicion, posicion);
    },

    // Primera letra del texto en mayúscula.
    normalizarTexto(input) {
        const posicion = input.selectionStart;

        input.value = input.value
            .toLocaleLowerCase("es")
            .replace(/^(\s*)(\p{L})/u, (coincidencia, espacio, letra) => {
                return espacio + letra.toLocaleUpperCase("es");
            });

        input.setSelectionRange(posicion, posicion);
    }
};


// Aplicar las validaciones según la clase CSS del campo.
document.addEventListener("DOMContentLoaded", function () {

    function validarContrasenia(input) {
        if (!input.value || Validaciones.esContraseniaSegura(input.value)) {
            input.setCustomValidity("");
            return;
        }
        input.setCustomValidity(
            "Usa al menos 8 caracteres, una mayúscula, una minúscula, un número y un símbolo."
        );
    }

    document.querySelectorAll(".js-contrasenia-segura").forEach(validarContrasenia);

    document.body.addEventListener("input", function (evento) {

        const input = evento.target;

        if (!(input instanceof HTMLInputElement ||
            input instanceof HTMLTextAreaElement)) {
            return;
        }

        if (input.classList.contains("js-contrasenia-segura")) {
            validarContrasenia(input);
        }

        if (input.classList.contains("js-solo-letras")) {
            Validaciones.permitirSoloLetras(input);
        }

        if (input.classList.contains("js-solo-numeros")) {
            Validaciones.permitirSoloNumeros(input);
        }

        if (input.classList.contains("js-alfanumerico")) {
            Validaciones.permitirAlfanumerico(input);
        }

        if (input.classList.contains("js-solo-minusculas")) {
            Validaciones.permitirSoloMinusculas(input);
        }

        if (input.classList.contains("js-nombre-propio")) {
            Validaciones.normalizarNombre(input);
        }

        if (input.classList.contains("js-texto-normalizado")) {
            Validaciones.normalizarTexto(input);
        }

    });

});
