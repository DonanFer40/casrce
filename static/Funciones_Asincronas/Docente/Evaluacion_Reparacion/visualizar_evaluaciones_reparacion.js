document.addEventListener("DOMContentLoaded", () => {

    const contenedor_evaluaciones = document.getElementById("contenedor_evaluaciones");

    async function dato_eval_rep() {
        try {
            const respuesta = await fetch("/notas_academicas/dato_eval_rep/");
            const resultado = await respuesta.json();

            if (resultado.estado !== "exito") {
                Swal.fire({
                    title: resultado.title,
                    text: resultado.descripcion,
                    icon: resultado.icon
                });
                return;
            }

            contenedor_evaluaciones.innerHTML = "";

            resultado.registros.forEach(registro => {
                let evaluacion_1 = "";
                let evaluacion_2 = "";
                let evaluacion_3 = "";

                if (registro.evaluaciones.length >= 1) {
                    evaluacion_1 = `
                        ${registro.evaluaciones[0].tipo_nombre}
                        (${registro.evaluaciones[0].porcentaje}%)
                    `;
                }

                if (registro.evaluaciones.length >= 2) {
                    evaluacion_2 = `
                        ${registro.evaluaciones[1].tipo_nombre}
                        (${registro.evaluaciones[1].porcentaje}%)
                    `;
                }

                if (registro.evaluaciones.length >= 3) {
                    evaluacion_3 = `
                        ${registro.evaluaciones[2].tipo_nombre}
                        (${registro.evaluaciones[2].porcentaje}%)
                    `;
                }

                const fila = document.createElement("tr");
                fila.innerHTML = `
                    <td>
                        ${registro.id_evaluacion}
                    </td>
                    <td>
                        ${registro.pnf}
                    </td>
                    <td>
                        ${registro.materia}
                    </td>
                    <td>
                        ${registro.fecha_creacion}
                    </td>
                    <td>
                        ${evaluacion_1}
                    </td>
                    <td>
                        ${evaluacion_2}
                    </td>
                    <td>
                        ${evaluacion_3}
                    </td>
                `;

                contenedor_evaluaciones.appendChild(fila);
            });
        } catch (error) {
            console.error(error);
        }
    }
    dato_eval_rep();

});