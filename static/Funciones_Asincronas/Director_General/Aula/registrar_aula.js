document.addEventListener("DOMContentLoaded", () => {

    const formulario_registrar = document.getElementById("formulario_registrar");
    const select_pnfs_imparte = document.getElementById("pnfs_imparte");
    const select_secciones_registradas = document.getElementById("secciones_registradas");
    const input_nombre_aula = document.getElementById("nombre_aula");

    const mensaje_nombre_aula = document.getElementById("mensaje_nombre_aula");
    const btn_registrar = document.getElementById("btn_registrar");

    async function validar_aula() {
        try {
            const formulario = new FormData();
            formulario.append("aula", input_nombre_aula.value);

            const respuesta = await fetch("/val_aula/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            if (resultado.existe) {
                input_nombre_aula.setCustomValidity("Ya existe una aula con el mismo nombre.");
                input_nombre_aula.classList.add("is-invalid");
                input_nombre_aula.classList.remove("is-valid");

                mensaje_nombre_aula.textContent = "Ya existe una aula con el mismo nombre.";
                mensaje_nombre_aula.style.color = "#dc3545";

                btn_registrar.disabled = true;
            } else {
                input_nombre_aula.setCustomValidity("");
                input_nombre_aula.classList.add("is-valid");
                input_nombre_aula.classList.remove("is-invalid");

                mensaje_nombre_aula.textContent = "El nombre de la aula está disponible.";
                mensaje_nombre_aula.style.color = "#198754";

                btn_registrar.disabled = false;
            }
        } catch (error) {
            console.error(error);
        }
    }

    input_nombre_aula.addEventListener("input", async () => {
        input_nombre_aula.value = input_nombre_aula.value.replace(
            /[^A-Za-z0-9ÁÉÍÓÚáéíóúÑñ\s_-]/g, ""
        );
        await validar_aula();
    });

    input_nombre_aula.addEventListener("paste", async () => {
        setTimeout(async () => {
            input_nombre_aula.value = input_nombre_aula.value.replace(
                /[^A-Za-z0-9ÁÉÍÓÚáéíóúÑñ\s_-]/g, ""
            );
            await validar_seccion();
        }, 0);
    });

    async function pnfs_registrados() {
        try {
            const respuesta = await fetch("/pnfs_reg/");
            const resultado = await respuesta.json();
            console.log(resultado);

            select_pnfs_imparte.innerHTML = "<option value=''>Selecciona una de las opciones</option>";

            resultado.nucleos.forEach(nucleo => {
                nucleo.pnfs.forEach(pnf => {
                    const opcion = document.createElement("option");
                    opcion.value = pnf.id_pnf;
                    opcion.textContent = `${pnf.pnf}`;
                    select_pnfs_imparte.appendChild(opcion);
                });
            });
        } catch (error) {
            console.error(error);
        }
    }
    pnfs_registrados();

    async function secciones_registradas() {
        try {
            const respuesta = await fetch("/sec_reg/");
            const resultado = await respuesta.json();
            console.log(resultado);

            select_secciones_registradas.innerHTML = "<option value=''>Selecciona una de las opciones</option>";

            resultado.secciones.forEach(seccion => {
                const opcion = document.createElement("option");
                opcion.value = seccion.id_seccion;
                opcion.textContent = `${seccion.nombre}`;
                select_secciones_registradas.appendChild(opcion);
            });
        } catch (error) {
            console.error(error);
        }
    }
    secciones_registradas();

    formulario_registrar.addEventListener("submit", async (e) => {
        e.preventDefault()
        try {
            const formulario = new FormData(formulario_registrar)

            const respuesta = await fetch("/reg_aula/", {
                method: "POST",
                body: formulario
            });
            const resultado = await respuesta.json()
            console.log(resultado)

            await Swal.fire({
                text: resultado.descripcion,
                icon: resultado.icon,
                allowOutsideClick: false,
                allowEscapeKey: false
            });

            if (resultado.estado == "exito") {
                formulario_registrar.reset()
            }
        } catch (error) {
            console.error(error);
        }
    });
});