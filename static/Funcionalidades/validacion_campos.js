
function configurarValidacionCampos() {

    const campos = document.querySelectorAll("[data-validacion]");

    const reglas = {
        letras: {
            expresion: /[0-9]/,
            mensaje: "Este campo no permite números."
        },

        numeros: {
            expresion: /[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ]/,
            mensaje: "Este campo no permite letras."
        }
    };

    campos.forEach(campo => {

        const tipo = campo.dataset.validacion;
        const regla = reglas[tipo];

        if (!regla) {
            return;
        }

        let mensaje = campo.parentElement.querySelector(
            `.mensaje-validacion-universal[data-campo="${campo.id}"]`
        );

        if (!mensaje) {

            mensaje = document.createElement("small");

            mensaje.className = "mensaje-validacion-universal";
            mensaje.dataset.campo = campo.id;
            mensaje.setAttribute("aria-live", "polite");

            campo.insertAdjacentElement("afterend", mensaje);
        }

        function validar() {

            const valor = campo.value;

            const contieneCaracterInvalido = regla.expresion.test(valor);

            if (contieneCaracterInvalido) {

                mensaje.textContent = regla.mensaje;

                mensaje.classList.add("error");

                campo.setCustomValidity(regla.mensaje);

                campo.classList.add("is-invalid");
                campo.classList.remove("is-valid");

            } else {

                mensaje.textContent = "";

                mensaje.classList.remove("error");

                campo.setCustomValidity("");

                campo.classList.remove("is-invalid");
            }
        }

        campo.addEventListener("input", validar);

        campo.addEventListener("blur", validar);

    });
}

document.addEventListener(
    "DOMContentLoaded",
    configurarValidacionCampos
);