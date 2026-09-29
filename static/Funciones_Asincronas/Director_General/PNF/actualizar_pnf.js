document.addEventListener("DOMContentLoaded", async () => {

    const formulario_buscar = document.getElementById("formulario_buscar");

    const input_codigo_pnf = document.getElementById("codigo_pnf");
    const input_id_pnf = document.getElementById("id_pnf");
    const actualizar_nombre_pnf = document.getElementById("actualizar_nombre_pnf");
    const actualizar_periodo_academico = document.getElementById("actualizar_periodo_academico");

    const formulario_actualizar = document.getElementById("formulario_actualizar");

    const btn_actualizar = document.getElementById("btn_actualizar");

    const controles_actualizar = [
        actualizar_nombre_pnf,
        actualizar_periodo_academico,
        btn_actualizar
    ]

    function bloquear_controles(controles, estado) {
        controles.forEach(control => control.disabled = estado);
    }

    bloquear_controles(controles_actualizar, true);

    function soloTexto(input) {
        input.value = input.value.replace(/[^a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s]/g, '');
    }

    actualizar_nombre_pnf.addEventListener("input", () => {
        soloTexto(actualizar_nombre_pnf);
    });

    input_codigo_pnf.addEventListener("input", function () {
        this.value = this.value
            .toUpperCase()
            .replace(/[^A-Z0-9]/g, "")
            .slice(0, 8);
    });

    formulario_buscar.addEventListener("submit", async (e) => {
        e.preventDefault();
        try {
            const formulario = new FormData(formulario_buscar);

            const respuesta = await fetch("/datos_pnf/", {
                method: "POST",
                body: formulario,
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            if (resultado.estado == "fallo") {
                await Swal.fire({
                    title: resultado.title,
                    text: resultado.descripcion,
                    icon: resultado.icon,
                    allowOutsideClick: false,
                    allowEscapeKey: false
                });
                return;
            }

            await Swal.fire({
                title: "Exito",
                text: "Se encontraron los datos",
                icon: "success",
                allowOutsideClick: false,
                allowEscapeKey: false
            });

            bloquear_controles(controles_actualizar, false);

            input_id_pnf.value = resultado.pnf.id

            actualizar_nombre_pnf.value = resultado.pnf.nombre;

            const option = document.createElement("option");
            option.value = resultado.pnf.periodo_academico;
            option.textContent = resultado.pnf.periodo_academico;
            option.selected = true;
            option.hidden = true;
            actualizar_periodo_academico.append(option);

            formulario_buscar.reset()
        } catch (error) {
            console.error(error);
        }
    });

    formulario_actualizar.addEventListener("submit", async (e) => {
        e.preventDefault();
        try {
            const formulario = new FormData(formulario_actualizar);

            const respuesta = await fetch("/act_pnf/", {
                method: "POST",
                body: formulario,
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            Swal.fire({
                title: resultado.title,
                text: resultado.descripcion,
                icon: resultado.icon,
                allowOutsideClick: false,
                allowEscapeKey: false
            });

            formulario_actualizar.reset();
            bloquear_controles(controles_actualizar, true);
        } catch (error) {
            console.error(error);
        }
    });

});