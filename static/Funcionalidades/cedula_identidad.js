
function configurarCedula(selectNacionalidad, campoCedula) {

    const mensaje = document.getElementById(
        "mensaje_cedula_identidad"
    );

    function mostrarEstado(estado, texto) {

        if (!mensaje) return;

        mensaje.textContent = texto;
        mensaje.className = estado;
    }

    function longitudIdentidad() {

        const nacionalidad = selectNacionalidad.value;

        campoCedula.value = "";
        campoCedula.classList.remove("is-valid", "is-invalid");

        if (nacionalidad === "") {

            campoCedula.disabled = true;
            campoCedula.placeholder = "Seleccione nacionalidad";

            mostrarEstado("estado-pendiente",
                "Seleccione su nacionalidad.");

            return;
        }

        campoCedula.disabled = false;

        switch (nacionalidad) {

            case "V":

                campoCedula.maxLength = 8;
                campoCedula.minLength = 7;
                campoCedula.placeholder = "Cédula (7-8 dígitos)";

                break;

            case "E":

                campoCedula.maxLength = 10;
                campoCedula.minLength = 8;
                campoCedula.placeholder = "Pasaporte/DNI (8-10 dígitos)";

                break;
        }

        mostrarEstado("estado-pendiente",
            "Ingrese su documento de identidad.");
    }

    selectNacionalidad.addEventListener(
        "change",
        longitudIdentidad
    );

    longitudIdentidad();
}
