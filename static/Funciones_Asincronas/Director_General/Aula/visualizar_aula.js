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

    function notificarError(mensaje) {
        NotificacionesCASRCE.mostrar({
            text: mensaje || "No fue posible completar la operación.",
            icon: "error",
            title: "Error",
            allowOutsideClick: false,
            allowEscapeKey: false
        });
    }

    async function respuestaJson(respuesta) {
        const resultado = await respuesta.json();
        if (!respuesta.ok) {
            throw new Error(resultado.descripcion || "Ocurrió un error al comunicarse con el servidor.");
        }
        return resultado;
    }

    async function aulas_registradas() {
        try {
            const respuesta = await fetch("/aulas_reg/");
            const resultado = await respuestaJson(respuesta);
            if (resultado.estado !== "exito") {
                throw new Error(resultado.descripcion || "No se pudieron cargar las aulas.");
            }

            contenedor_aulas.replaceChildren();
            if (resultado.aulas.length === 0) {
                const fila = document.createElement("tr");
                const celda = document.createElement("td");
                celda.colSpan = 7;
                celda.textContent = "Todavía no hay aulas registradas en este núcleo.";
                fila.appendChild(celda);
                contenedor_aulas.appendChild(fila);
                return;
            }

            resultado.aulas.forEach((aula, index) => {
                const fila = document.createElement("tr");
                fila.dataset.id = aula.id_aula;

                [
                    index + 1,
                    aula.nombre_aula,
                    aula.Nota,
                    aula.piso_edificio,
                    aula.tipo_aula,
                    aula.id_seccion__nombre,
                    aula.id_pnf__pnf
                ].forEach(valor => {
                    const celda = document.createElement("td");
                    celda.textContent = valor ?? "";
                    fila.appendChild(celda);
                });

                contenedor_aulas.appendChild(fila);
            });
        } catch (error) {
            notificarError(error.message);
        }
    }

    async function pnfs_registrados() {
        const respuesta = await fetch("/pnfs_reg/");
        const resultado = await respuestaJson(respuesta);
        if (resultado.estado !== "exito") {
            throw new Error(resultado.descripcion || "No se pudieron cargar los P.N.F.");
        }

        select_pnf_actualizar.replaceChildren(new Option("Selecciona el P.N.F.", ""));
        resultado.nucleos.forEach(nucleo => {
            nucleo.pnfs.forEach(pnf => {
                select_pnf_actualizar.add(new Option(pnf.pnf, pnf.id_pnf));
            });
        });
    }

    async function secciones_registradas() {
        const respuesta = await fetch("/sec_reg/");
        const resultado = await respuestaJson(respuesta);
        if (resultado.estado !== "exito") {
            throw new Error(resultado.descripcion || "No se pudieron cargar las secciones.");
        }

        select_seccion_actualizar.replaceChildren(new Option("Selecciona la sección", ""));
        resultado.secciones.forEach(seccion => {
            select_seccion_actualizar.add(new Option(seccion.nombre, seccion.id_seccion));
        });
    }

    const catalogosListos = Promise.all([
        pnfs_registrados(),
        secciones_registradas()
    ]).catch(error => {
        notificarError(error.message);
        return false;
    });

    aulas_registradas();
    window.addEventListener("aulas:actualizadas", aulas_registradas);

    contenedor_aulas.addEventListener("click", async (e) => {
        const fila = e.target.closest("tr");
        if (!fila || !fila.dataset.id) return;

        try {
            if (!(await catalogosListos)) return;
            const formulario = new FormData();
            formulario.append("id_aula", fila.dataset.id);

            const respuesta = await fetch("/datos_aula/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
                },
                body: formulario
            });
            const resultado = await respuestaJson(respuesta);

            if (resultado.estado === "fallo") {
                throw new Error(resultado.descripcion || "No se pudo cargar el aula seleccionada.");
            }

            input_id_aula_oculto.value = resultado.id_aula;
            input_aula_actualizar.value = resultado.nombre_aula;
            input_piso_actualizar.value = resultado.piso_edificio;
            input_nota_actualizar.value = resultado.Nota;
            select_tipos_aulas_actualizar.value = resultado.tipo_aula;
            seleccionarOpcion(select_seccion_actualizar, resultado.id_seccion, resultado.seccion);
            seleccionarOpcion(select_pnf_actualizar, resultado.id_pnf, resultado.pnf);
            dialogo_actualizar_aula.showModal();
        } catch (error) {
            notificarError(error.message);
        }
    });

    function seleccionarOpcion(select, value, label) {
        if (!Array.from(select.options).some(option => option.value === String(value))) {
            select.add(new Option(label, value));
        }
        select.value = value;
    }

    formulario_actualizar.addEventListener("submit", async (e) => {
        e.preventDefault();
        try {
            const datos = new FormData(formulario_actualizar);

            const respuesta = await fetch("/act_aula_acad/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": formulario_actualizar.querySelector("[name=csrfmiddlewaretoken]").value
                },
                body: datos
            });
            const resultado = await respuestaJson(respuesta);

            if (resultado.estado !== "exito") {
                await NotificacionesCASRCE.mostrar({
                    text: resultado.descripcion || "No se pudieron guardar los cambios.",
                    icon: resultado.icon || "error",
                    title: resultado.title || "No se pudo actualizar",
                    allowOutsideClick: false,
                    allowEscapeKey: false
                });
                return;
            }

            dialogo_actualizar_aula.close();
            await NotificacionesCASRCE.mostrar({
                text: resultado.descripcion,
                icon: resultado.icon || "success",
                title: resultado.title || "Aula actualizada",
                allowOutsideClick: false,
                allowEscapeKey: false
            });
            await aulas_registradas();
        } catch (error) {
            notificarError(error.message);
        }
    });

    btn_cerrar_actualizar.addEventListener("click", () => {
        dialogo_actualizar_aula.close();
    });
});