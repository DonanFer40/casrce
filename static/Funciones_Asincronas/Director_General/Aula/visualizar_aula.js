document.addEventListener("DOMContentLoaded", () => {
    const formulario_actualizar = document.getElementById("formulario_actualizar");
    const contenedor_aulas = document.getElementById("contenedor_aulas");

    const dialogo_actualizar_aula = document.getElementById("dialogo_actualizar_aula");

    const input_id_aula_oculto = document.getElementById("aula_seleccionar");
    const input_aula_actualizar = document.getElementById("actualizar_nombre_aula");
    const input_piso_actualizar = document.getElementById("actualizar_piso_edificio");
    const input_nota_actualizar = document.getElementById("actualizar_nota_aula");
    const select_tipos_aulas_actualizar = document.getElementById("actualizar_tipos_aulas");
    const select_seccion_actualizar = document.getElementById("actualizar_seccion");
    const select_pnf_actualizar = document.getElementById("actualizar_pnf");

    const btn_cerrar_actualizar = document.getElementById("cerrar_dialogo");

    async function aulas_registradas() {
        try {
            const respuesta = await fetch("/aulas_reg/");
            const resultado = await respuesta.json();
            console.log(resultado);

            let filas = "";
            resultado.aulas.forEach((aula, index) => {
                filas += `
                <tr data-id="${aula.id_aula}">
                    <td>${index + 1}</td>
                    <td>${aula.nombre_aula}</td>
                    <td>${aula.Nota}</td>
                    <td>${aula.piso_edificio}</td>
                    <td>${aula.tipo_aula}</td>
                    <td>${aula.id_seccion__nombre}</td>
                    <td>${aula.id_pnf__pnf}</td>
                </tr>
            `;
            });

            contenedor_aulas.innerHTML = filas;
        } catch (error) {
            console.error(error);
        }
    }
    aulas_registradas();

    async function pnfs_registrados() {
        try {
            const respuesta = await fetch("/pnfs_reg/");
            const resultado = await respuesta.json();
            console.log(resultado);

            select_pnf_actualizar.innerHTML = "<option value=''>Selecciona el P.N.F</option>";

            resultado.nucleos.forEach(nucleo => {
                nucleo.pnfs.forEach(pnf => {
                    const opcion = document.createElement("option");
                    opcion.value = pnf.id_pnf;
                    opcion.textContent = `${pnf.pnf}`;
                    select_pnf_actualizar.appendChild(opcion);
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

            select_seccion_actualizar.innerHTML = "<option value=''>Selecciona la sección</option>";

            resultado.secciones.forEach(seccion => {
                const option = document.createElement("option");
                option.value = seccion.id_seccion;
                option.textContent = seccion.nombre;
                select_seccion_actualizar.appendChild(option);
            });
        } catch (error) {
            console.error(error);
        }
    }
    secciones_registradas();

    contenedor_aulas.addEventListener("click", async (e) => {
        const fila = e.target.closest("tr");
        if (!fila) return;

        try {
            const formulario = new FormData();
            formulario.append("id_aula", fila.dataset.id);

            const respuesta = await fetch("/datos_aula/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            dialogo_actualizar_aula.showModal();

            if (resultado.estado === "fallo") {
                Swal.fire({
                    text: resultado.descripcion,
                    icon: resultado.icon,
                    title: resultado.title,
                    allowOutsideClick: false,
                    allowEscapeKey: false
                });
                return;
            }

            input_id_aula_oculto.value = resultado.id_aula;
            input_aula_actualizar.value = resultado.nombre_aula;
            input_piso_actualizar.value = resultado.piso_edificio;
            input_nota_actualizar.value = resultado.Nota;

            const option_tipo_aula = document.createElement("option");
            option_tipo_aula.value = resultado.tipo_aula;
            option_tipo_aula.textContent = resultado.tipo_aula;
            option_tipo_aula.selected = true;
            option_tipo_aula.hidden = true;
            select_tipos_aulas_actualizar.append(option_tipo_aula);

            const option_seccion = document.createElement("option");
            option_seccion.value = resultado.id_seccion;
            option_seccion.textContent = resultado.seccion;
            option_seccion.selected = true;
            option_seccion.hidden = true;
            select_seccion_actualizar.append(option_seccion);

            const option_pnf = document.createElement("option");
            option_pnf.value = resultado.id_pnf;
            option_pnf.textContent = resultado.pnf;
            option_pnf.selected = true;
            option_pnf.hidden = true;
            select_pnf_actualizar.append(option_pnf);
        } catch (error) {
            console.error(error)
        }
    });

    formulario_actualizar.addEventListener("submit", async (e) => {
        e.preventDefault()
        try {
            const formulario = new FormData(formulario_actualizar);

            const respuesta = await fetch("/act_aula_acad/", {
                method: "POST",
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            dialogo_actualizar_aula.close();

            await Swal.fire({
                text: resultado.descripcion,
                icon: resultado.icon,
                title: resultado.title,
                allowOutsideClick: false,
                allowEscapeKey: false
            });

            if (resultado.estado == "exito") {
                await aulas_registradas();
            }
        } catch (error) {
            console.error(error);
        }
    });

    btn_cerrar_actualizar.addEventListener("click", () => {
        dialogo_actualizar_aula.close()
    });
});