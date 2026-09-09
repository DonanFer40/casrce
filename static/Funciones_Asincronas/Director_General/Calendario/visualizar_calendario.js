document.addEventListener("DOMContentLoaded", () => {

    const select_periodos_academicos = document.getElementById("periodos_academicos");
    const contenedor = document.getElementById("contenedor_visualizar_calendario");

    const input_id_calendario = document.getElementById("id_calendario");
    const dialogo_fecha_academica = document.getElementById("dialogo_fecha_academica");
    const btn_cerrar_dialogo = document.getElementById("cerrar_dialogo");
    const formulario_actualizar = document.getElementById("formulario_actualizar");
    const input_fecha_inicio = document.getElementById("fecha_inicio");
    const input_fecha_finalizado = document.getElementById("fecha_finalizado");

    let periodo = "";

    async function periodos_academicos_registrados() {
        try {
            const respuesta = await fetch("/per_acad_reg/");
            const resultado = await respuesta.json();
            console.log(resultado);

            select_periodos_academicos.innerHTML = "<option value='' selected>Seleccione el periodo</option>";

            resultado.tipos.forEach(tipo => {
                const option = document.createElement("option");
                option.value = tipo;
                option.textContent = tipo;
                select_periodos_academicos.appendChild(option);
            });
        } catch (error) {
            console.error(error);
        }
    }
    periodos_academicos_registrados();

    select_periodos_academicos.addEventListener("change", async () => {
        periodo = select_periodos_academicos.value;

        await calendario_registrado();
    });

    async function calendario_registrado() {
        try {
            const formulario = new FormData();
            formulario.append("periodo", periodo);

            const respuesta = await fetch("/calendarios_lista/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            contenedor.innerHTML = "";
            const tipos = [
                { valor: "PERIODO", nombre: "Período Académico" },
                { valor: "CARGA_NOTAS", nombre: "Carga de Notas" },
                { valor: "NO_LABORABLE", nombre: "Días No Laborables" },
                { valor: "VACACIONES", nombre: "Vacaciones" },
                { valor: "GRADO_ACADEMICO", nombre: "Grado Académico" },
                { valor: "INSCRIPCION_TRIMESTRE", nombre: "Inscripción Trimestre" },
                { valor: "INSCRIPCION_SEMESTRE", nombre: "Inscripción Semestre" }
            ];

            tipos.forEach(tipo => {
                const calendarios = resultado.calendarios.filter(
                    calendario => calendario.tipo_valor === tipo.valor
                );

                if (calendarios.length === 0) {
                    return;
                }

                const contenedor_tipo = document.createElement("div");
                contenedor_tipo.classList.add("contenedor_tipo_calendario");

                const titulo = document.createElement("h3");
                titulo.textContent = tipo.nombre;

                const tabla = document.createElement("table");
                tabla.classList.add("tabla_calendario");

                if (tipo.valor === "CARGA_NOTAS") {
                    tabla.innerHTML = `
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>DESCRIPCIÓN</th>
                                <th>FECHA INICIO</th>
                                <th>FECHA FINALIZADA</th>
                                <th>ACCIÓN</th>
                            </tr>
                        </thead>
                        <tbody></tbody>
                    `;
                } else {
                    tabla.innerHTML = `
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>DESCRIPCIÓN</th>
                                <th>FECHA INICIO</th>
                                <th>FECHA FINALIZADA</th>
                            </tr>
                        </thead>
                        <tbody></tbody>
                    `;
                }
                const tbody = tabla.querySelector("tbody");

                /*Insertar registros*/
                calendarios.forEach((calendario, index) => {
                    const fila = document.createElement("tr");
                    fila.dataset.id = calendario.id;
                    fila.dataset.tipo = calendario.tipo_valor;

                    if (tipo.valor === "CARGA_NOTAS") {
                        fila.innerHTML = `
                            <td>${index + 1}</td>
                            <td>${calendario.descripcion}</td>
                            <td>${calendario.fecha_inicio}</td>
                            <td>${calendario.fecha_final}</td>
                            <td>
                                <button 
                                    type="button" 
                                    class="btn_abrir_carga_notas" 
                                    data-id="${calendario.id}" 
                                    data-tipo="CARGA_NOTAS">
                                    Ver
                                </button>
                            </td>
                        `;
                    } else {
                        fila.innerHTML = `
                            <td>${calendario.id}</td>
                            <td>${calendario.descripcion}</td>
                            <td>${calendario.fecha_inicio}</td>
                            <td>${calendario.fecha_final}</td>
                        `;
                    }

                    tbody.appendChild(fila);
                });

                /*Agregar título y tabla*/
                contenedor_tipo.appendChild(titulo);
                contenedor_tipo.appendChild(tabla);

                /*Agregar al contenedor principa*/
                contenedor.appendChild(contenedor_tipo);
            });
        } catch (error) {
            console.error(error);
        }
    }
    calendario_registrado();

    contenedor.addEventListener("click", async (e) => {
        const boton = e.target.closest(".btn_abrir_carga_notas");
        if (!boton) {
            return;
        }

        try {
            const formulario = new FormData();
            formulario.append("id_calendario", boton.dataset.id);

            const respuesta = await fetch("/calendario_datos/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector(
                        "[name=csrfmiddlewaretoken]"
                    ).value
                },
                body: formulario
            }
            );
            const resultado = await respuesta.json();
            console.log(resultado);

            if (resultado.estado !== "exito") {
                return;
            }

            dialogo_fecha_academica.showModal();

            input_id_calendario.value = resultado.calendario.id;
            input_fecha_inicio.value = resultado.calendario.fecha_inicio;
            input_fecha_finalizado.value = resultado.calendario.fecha_final;
            input_fecha_inicio.min = resultado.calendario.fecha_inicio;
        } catch (error) {
            console.error(error);
        }
    });

    input_fecha_inicio.addEventListener("change", () => {
        const fecha_ingresada = input_fecha_inicio.value;
        if (!fecha_ingresada) {
            return;
        }

        const fecha = new Date(
            fecha_ingresada + "T00:00:00"
        );

        fecha.setDate(fecha.getDate() + 3);

        const año = fecha.getFullYear();
        const mes = String(fecha.getMonth() + 1).padStart(2, "0");
        const dia = String(fecha.getDate()).padStart(2, "0");

        input_fecha_finalizado.value = `${año}-${mes}-${dia}`;
    });

    btn_cerrar_dialogo.addEventListener("click", () => {
        dialogo_fecha_academica.close();
    });

    formulario_actualizar.addEventListener("submit", async (e) => {
        e.preventDefault();
        try {
            const formulario = new FormData(formulario_actualizar);

            const respuesta = await fetch("/calendario_guardar/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            dialogo_fecha_academica.close();

            await Swal.fire({
                text: resultado.descripcion,
                icon: resultado.icon,
                title: resultado.title,
                allowOutsideClick: false,
                allowEscapeKey: false
            });

            await calendario_registrado()
        } catch (error) {
            console.error(error)
        }
    });

});