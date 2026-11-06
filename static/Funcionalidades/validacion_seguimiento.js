document.addEventListener("DOMContentLoaded", function () {

    const formulario = document.getElementById("formulario_registro");

    if (!formulario) {
        console.error("No se encontró el formulario_registro");
        return;
    }

    function identificarCampos() {

        ["correo_secundario", "dominio_secundario"].forEach(id => {
            const campo = formulario.querySelector(`#${id}`);
            if (campo) {
                campo.required = false;
                campo.removeAttribute("required");
                campo.setCustomValidity("");
            }
        });

        const grupos = formulario.querySelectorAll(
            ".campo, .registro-completo-documento-info"
        );

        grupos.forEach(grupo => {
            const campos = Array.from(
                grupo.querySelectorAll("input, select, textarea")
            ).filter(campo => {
                return (
                    campo.type !== "hidden" &&
                    !campo.hidden &&
                    !campo.hasAttribute("hidden") &&
                    !campo.readOnly
                );
            });

            if (campos.length === 0) return;

            const etiqueta = grupo.querySelector("label");
            if (!etiqueta) return;

            const obligatorio = campos.some(campo => campo.required);
            let indicador = etiqueta.querySelector(".indicador-campo");

            if (!indicador) {
                indicador = document.createElement("span");
                etiqueta.appendChild(indicador);
            }

            indicador.className = "indicador-campo";
            indicador.classList.add(
                obligatorio ? "campo-obligatorio" : "campo-opcional"
            );
            indicador.textContent = obligatorio ? "Obligatorio" : "Opcional";
        });

        // La pregunta del carnet siempre es obligatoria: se debe elegir Sí o No.
        const carnet = formulario.querySelector("#codigo_carnet_dispacidad");
        if (carnet) {
            const etiqueta = formulario.querySelector('label[for="codigo_carnet_dispacidad"]');
            if (etiqueta) {
                let indicador = etiqueta.querySelector(".indicador-campo");
                if (!indicador) {
                    indicador = document.createElement("span");
                    etiqueta.appendChild(indicador);
                }
                indicador.className = "indicador-campo campo-obligatorio";
                indicador.textContent = "Obligatorio";
            }
        }

        // Indicador del PNF: se actualiza cuando la función de carga termina.
        const contenedorPNF = document.getElementById("contenedor_pnfs_cursar");
        if (contenedorPNF) {
            const radios = contenedorPNF.querySelectorAll('input[type="radio"][name="pnf_seleccionado"]');
            const titulo = contenedorPNF.querySelector(".registro-completo-paso-encabezado h2");
            if (titulo && radios.length > 0) {
                let indicador = titulo.querySelector(".indicador-campo");
                if (!indicador) {
                    indicador = document.createElement("span");
                    titulo.appendChild(indicador);
                }
                const obligatorio = Array.from(radios).some(radio => radio.required);
                indicador.className = `indicador-campo ${obligatorio ? "campo-obligatorio" : "campo-opcional"}`;
                indicador.textContent = obligatorio ? "Obligatorio" : "Opcional";
            }
        }
    }

    const selectorCarnet = formulario.querySelector("#codigo_carnet_dispacidad");
    if (selectorCarnet) {
        selectorCarnet.addEventListener("change", identificarCampos);
    }

    // La carga de PNF avisa explícitamente cuando termina.
    document.addEventListener("casrce:pnfs-actualizados", identificarCampos);
    document.addEventListener("casrce:discapacidad-actualizada", identificarCampos);

    identificarCampos();

});