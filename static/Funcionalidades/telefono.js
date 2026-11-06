function configurarTelefono(inputTelefono, selectPrefijo) {

    const prefijos = [
        "0414",
        "0424",
        "0416",
        "0426",
        "0412",
        "0422"
    ];

    function cargarPrefijos() {

        selectPrefijo.innerHTML = "";

        const opcionInicial = document.createElement("option");

        opcionInicial.value = "";
        opcionInicial.textContent = "TLF";
        opcionInicial.selected = true;

        selectPrefijo.appendChild(opcionInicial);

        prefijos.forEach(prefijo => {

            const opcion = document.createElement("option");

            opcion.value = prefijo;
            opcion.textContent = prefijo;

            selectPrefijo.appendChild(opcion);
        });

        inputTelefono.value = "";
        inputTelefono.maxLength = 7;
        inputTelefono.minLength = 7;
        inputTelefono.disabled = true;

        inputTelefono.placeholder = "Seleccione un prefijo";
    }

    selectPrefijo.addEventListener("change", function () {

        inputTelefono.value = "";

        inputTelefono.setCustomValidity("");

        inputTelefono.classList.remove(
            "is-valid",
            "is-invalid"
        );

        if (!this.value) {

            inputTelefono.disabled = true;

            inputTelefono.placeholder = "Seleccione un prefijo";

        } else {

            inputTelefono.disabled = false;

            inputTelefono.placeholder = "Ingrese los 7 dígitos";

            inputTelefono.focus();
        }

    });

    cargarPrefijos();
}