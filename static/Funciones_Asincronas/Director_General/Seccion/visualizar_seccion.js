document.addEventListener("DOMContentLoaded", () => {

    const contenedor_secciones = document.getElementById("contenedor_secciones");
    const dialogo_actualizar = document.getElementById("dialogo_actualizar_secciones");
    const btn_cerrar = document.getElementById("cerrar_dialogo");

    const formulario_actualizar = document.getElementById("formulario_actualizar_seccion");

    const input_seccion_oculto = document.getElementById("secciones_seleccionado");
    const select_actualizar_turno = document.getElementById("actualizar_turno_registrado");
    const input_actualizar_seccion = document.getElementById("actualizar_seccion_registrado");
    const mensaje_actualizar_seccion = document.getElementById("mensaje_actualizar_seccion");

    const btn_actualizar = document.getElementById("btn_actualizar");

    let filas = "";

    async function secciones_registradas() {
        try {
            const respuesta = await fetch("/sec_reg/");
            const resultado = await respuesta.json();
            console.log(resultado);

            contenedor_secciones.innerHTML = "";
            resultado.secciones.forEach((seccion, index) => {
                filas += `
                    <tr data-id-seccion="${seccion.id_seccion}">
                        <td>${index + 1}</td>
                        <td>${seccion.nombre}</td>
                        <td>${seccion.turno}</td>
                    </tr>
                `;
            });

            contenedor_secciones.innerHTML = filas;
        } catch (error) {
            console.error(error);

        }
    }
    secciones_registradas();

    contenedor_secciones.addEventListener("click", async (e) => {
        const fila = e.target.closest("tr");
        if (!fila) return;

        try {
            const formulario = new FormData();
            formulario.append("seccion", fila.dataset.idSeccion);

            const respuesta = await fetch("/datos_sec/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            if (resultado.estado !== "exito") {
                await NotificacionesCASRCE.mostrar({
                    text: resultado.mensaje,
                    icon: resultado.icon,
                    title: resultado.title
                });
                return;
            }

            dialogo_actualizar.showModal();

            input_seccion_oculto.value = resultado.seccion.id_seccion;
            input_actualizar_seccion.value = resultado.siguiente || "";
            btn_actualizar.disabled = !resultado.siguiente;
            mensaje_actualizar_seccion.textContent = resultado.siguiente
                ? `Ocupadas: ${resultado.ocupadas.join(", ")}. Al guardar se asignará ${resultado.siguiente}.`
                : `Ocupadas: ${resultado.ocupadas.join(", ")}. Libera una letra entre A y Z para modificar.`;

            select_actualizar_turno.replaceChildren(
                select_actualizar_turno.options[0]
            );
            const option_turno = document.createElement("option");
            option_turno.value = resultado.seccion.turno;
            option_turno.textContent = resultado.seccion.turno;
            option_turno.selected = true;
            option_turno.hidden = true;
            select_actualizar_turno.append(option_turno);
        } catch (error) {
            console.error(error);
        }
    });

    btn_cerrar.addEventListener("click", () => {
        dialogo_actualizar.close();
    });

    formulario_actualizar.addEventListener("submit", async (e) => {
        e.preventDefault()
        try {
            const formulario = new FormData(formulario_actualizar);

            const respuesta = await fetch("/guardar_act_sec/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            if (!respuesta.ok || resultado.estado !== "exito") {
                await NotificacionesCASRCE.mostrar({
                    text: resultado.descripcion,
                    icon: resultado.icon,
                    title: resultado.title
                });
                return;
            }

            dialogo_actualizar.close();

            filas = "";
            await secciones_registradas();
            input_actualizar_seccion.value = resultado.seccion;

            await NotificacionesCASRCE.mostrar({
                text: resultado.descripcion,
                icon: resultado.icon,
                allowOutsideClick: false,
                allowEscapeKey: false
            });
        } catch (error) {
            console.error(error);
        }
    });

});