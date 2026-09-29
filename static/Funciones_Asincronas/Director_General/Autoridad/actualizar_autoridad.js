document.addEventListener("DOMContentLoaded", () => {

    const formulario_buscar = document.getElementById("formulario_buscar");
    const select_nacionalidad = document.getElementById("nacionalidad");
    const input_cedula_identidad = document.getElementById("cedula");

    const formulario_actualizar = document.getElementById("formulario_actualizar");

    const input_autoridad_oculto = document.getElementById("usuario_seleccionado");
    const input_nombres_actualizar = document.getElementById("nombres_actualizar");
    const input_apellidos_actualizar = document.getElementById("apellidos_actualizar");
    const select_genero_actualizar = document.getElementById("genero_actualizar");
    const select_cargo_actualizar = document.getElementById("cargo_actualizar");
    const input_resolucion_actualizar = document.getElementById("resolucion_actualizar");
    const msg_resolucion = document.getElementById("msg_resolucion");

    const btn_actualizar = document.getElementById("btn_actualizar");

    configurarCedula(select_nacionalidad, input_cedula_identidad);

    let cargo_anterior = "";

    const cargos = [
        "Rector",
        "Vicerrector",
        "Responsable Académico"
    ];

    controles = [
        input_nombres_actualizar,
        input_apellidos_actualizar,
        select_genero_actualizar,
        select_cargo_actualizar,
        input_resolucion_actualizar,
        btn_actualizar
    ]

    function obtenerTokenCSRF() {
        const cookies = document.cookie.split(";");

        for (const cookie of cookies) {
            const [nombre, valor] = cookie.trim().split("=");

            if (nombre === "csrftoken") {
                return decodeURIComponent(valor);
            }
        }

        return null;
    }

    const token_csrf = obtenerTokenCSRF();

    function bloquear_controles(controles, estado) {
        controles.forEach(control => control.disabled = estado);
    }

    bloquear_controles(controles, true);

    formulario_buscar.addEventListener("submit", async (e) => {
        e.preventDefault();
        try {
            const formulario = new FormData(formulario_buscar);

            const respuesta = await fetch("/datos_aut/", {
                method: "POST",
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            if (resultado.estado == "fallo") {
                await Swal.fire({
                    text: resultado.descripcion,
                    icon: resultado.icon,
                    title: resultado.title,
                    allowOutsideClick: false,
                    allowEscapeKey: false
                });
                return;
            }
            bloquear_controles(controles, false);

            await Swal.fire({
                text: "Se encontraron los datos",
                icon: "success",
                title: "Exito",
                allowOutsideClick: false,
                allowEscapeKey: false
            });

            input_autoridad_oculto.value = resultado.id
            input_nombres_actualizar.value = resultado.nombres
            input_apellidos_actualizar.value = resultado.apellidos

            const option_genero = document.createElement("option")
            option_genero.value = resultado.genero
            option_genero.textContent = resultado.genero
            option_genero.selected = true
            option_genero.hidden = true
            select_genero_actualizar.append(option_genero)

            select_cargo_actualizar.innerHTML = "";

            cargo_anterior = resultado.cargo;

            const optionActual = document.createElement("option");
            optionActual.value = resultado.cargo;
            optionActual.textContent = resultado.cargo;
            optionActual.selected = true;
            optionActual.hidden = true;
            select_cargo_actualizar.append(optionActual);

            cargos.forEach(cargo => {
                if (cargo !== resultado.cargo) {
                    const option = document.createElement("option");
                    option.value = cargo;
                    option.textContent = cargo;
                    select_cargo_actualizar.append(option);
                }
            });

            input_resolucion_actualizar.value = resultado.resolucion;

            formulario_buscar.reset();
        } catch (error) {
            console.error(error)
        }
    });

    formulario_actualizar.addEventListener("submit", async (e) => {
        e.preventDefault();
        try {
            const cargo_nuevo = select_cargo_actualizar.value;
            const id_autoridad = input_autoridad_oculto.value;

            let cambiar_cargo = false;

            // El cargo no cambió
            if (cargo_nuevo === cargo_anterior) {

                cambiar_cargo = false;

            } else {
                // Buscar quién posee actualmente el nuevo cargo
                const formulario_cargo = new FormData();
                formulario_cargo.append("cargo", cargo_nuevo);
                formulario_cargo.append("id_autoridad", id_autoridad);

                const respuesta_cargo = await fetch("/cargo_user/", {
                    method: "POST",
                    headers: {
                        "X-CSRFToken": token_csrf
                    },
                    body: formulario_cargo
                });
                const resultado_cargo = await respuesta_cargo.json();

                if (resultado_cargo.existe) {
                    const autoridad = resultado_cargo.autoridad;
                    const confirmacion = await Swal.fire({
                        title: "¿Cambiar cargo?",
                        html: `
                            <p>El cargo actual es: <strong>${cargo_anterior}</strong></p>
                            <p>Has seleccionado: <strong>${cargo_nuevo}</strong></p>
                            <p>Actualmente este cargo pertenece a: </p>
                            <strong>${autoridad.nombres} ${autoridad.apellidos}</strong>
                            <p style="margin-top: 10px;"> Si continúas, los cargos serán intercambiados.</p>
                        `,
                        icon: "question",
                        showCancelButton: true,
                        confirmButtonText: "Sí, cambiar",
                        cancelButtonText: "No, conservar",
                        allowOutsideClick: false,
                        allowEscapeKey: false
                    });

                    cambiar_cargo = confirmacion.isConfirmed;
                } else {
                    const confirmacion = await Swal.fire({
                        title: "¿Cambiar cargo?",
                        html: `
                            <p>El cargo actual es: <strong>${cargo_anterior}</strong></p>
                            <p>Has seleccionado: <strong>${cargo_nuevo}</strong></p>
                            <p>Este cargo actualmente está disponible.</p>
                        `,
                        icon: "question",
                        showCancelButton: true,
                        confirmButtonText: "Sí, cambiar",
                        cancelButtonText: "No, conservar",
                        allowOutsideClick: false,
                        allowEscapeKey: false
                    });

                    cambiar_cargo = confirmacion.isConfirmed;
                }
            }

            const formulario = new FormData(formulario_actualizar);
            formulario.append("cambiar_cargo", cambiar_cargo ? "true" : "false");

            const respuesta = await fetch("/act_datos_aut/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": token_csrf
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            await Swal.fire({
                text: resultado.descripcion,
                icon: resultado.icon,
                title: resultado.title,
                allowOutsideClick: false,
                allowEscapeKey: false
            });

            if (resultado.estado == "exito") {
                formulario_actualizar.reset();
                bloquear_controles(controles, true);
                cargo_anterior = "";
                select_cargo_actualizar.innerHTML = "<option value=''>Debe realizar la búsqueda</option>";
            }
        } catch (error) {
            console.error(error);
        }
    });

    async function validarResolucion(inputresolucion, mensaje) {
        const resolucion = inputresolucion.value.trim();

        if (resolucion.length === 0) {
            mensaje.textContent = "";
            inputresolucion.setCustomValidity("");
            inputresolucion.classList.remove("is-valid", "is-invalid");
            btn_actualizar.disabled = false;
            return;
        }

        try {
            const formulario = new FormData();
            formulario.append("resolucion", resolucion);
            formulario.append("id_autoridad", input_autoridad_oculto.value);

            const respuesta = await fetch("/val_resolucion/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            if (resultado.existe) {
                inputresolucion.setCustomValidity("Ya existe una autoridad registrada con esta resolución.");
                inputresolucion.classList.add("is-invalid");
                inputresolucion.classList.remove("is-valid");

                mensaje.textContent = "Ya existe una autoridad registrada con esta resolución.";
                mensaje.style.color = "#dc3545";

                btn_actualizar.disabled = true;

            } else {
                inputresolucion.setCustomValidity("");
                inputresolucion.classList.remove("is-invalid");
                inputresolucion.classList.add("is-valid");

                mensaje.textContent = "La resolución está disponible.";
                mensaje.style.color = "#198754";

                btn_actualizar.disabled = false;
            }
        } catch (error) {
            console.error(error);
        }
    }

    input_resolucion_actualizar.addEventListener("input", async () => {
        await validarResolucion(input_resolucion_actualizar, msg_resolucion);
    });

    input_resolucion_actualizar.addEventListener("paste", async () => {
        await validarResolucion(input_resolucion_actualizar, msg_resolucion);
    });

    input_resolucion_actualizar.addEventListener("input", function () {
        let valor = this.value.toUpperCase().replace(/[^A-Z0-9]/g, "");

        let letras = valor.replace(/[^A-Z]/g, "").slice(0, 6);
        let numeros = valor.replace(/[^0-9]/g, "").slice(0, 6);

        this.value = letras + numeros;
    });

});