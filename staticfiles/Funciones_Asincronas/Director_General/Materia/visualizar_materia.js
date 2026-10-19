document.addEventListener("DOMContentLoaded", () => {

    const select_busqueda_pnf = document.getElementById("buscar_pnf");
    const contenedor_materias = document.getElementById("contenedor_tablas_materia");


    /* =========================================================
       CARGAR P.N.F
       ========================================================= */

    async function pnfs_registrados() {

        try {

            const respuesta = await fetch("/pnfs_reg/");
            const resultado = await respuesta.json();

            select_busqueda_pnf.innerHTML = `
                <option value="" selected>
                    Seleccionar el P.N.F
                </option>
            `;

            resultado.nucleos.forEach(nucleo => {

                nucleo.pnfs.forEach(pnf => {

                    const option = document.createElement("option");

                    option.value = pnf.id_pnf;
                    option.textContent = pnf.pnf;

                    select_busqueda_pnf.appendChild(option);

                });

            });

        } catch (error) {

            console.error(
                "Error al cargar los P.N.F:",
                error
            );

        }
    }


    /* =========================================================
       CONSULTAR MATERIAS
       ========================================================= */

    async function materias_registradas() {

        try {

            const formulario = new FormData();

            formulario.append(
                "pnf",
                select_busqueda_pnf.value
            );


            const respuesta = await fetch("/mat_lista/", {

                method: "POST",

                headers: {
                    "X-CSRFToken":
                        document.querySelector(
                            "[name=csrfmiddlewaretoken]"
                        ).value
                },

                body: formulario

            });


            const resultado = await respuesta.json();

            console.log(resultado);


            contenedor_materias.innerHTML = "";


            /* =================================================
               ORGANIZAR MATERIAS POR PNF
               ================================================= */

            const materiasPorPNF = {};


            resultado.pnfs.forEach(pnf => {

                materiasPorPNF[pnf.id_pnf] = {

                    id: pnf.id_pnf,

                    nombre: pnf.pnf,

                    codigo: pnf.codigo,

                    materias: []

                };

            });


            resultado.materias.forEach(materia => {

                if (materiasPorPNF[materia.id_pnf]) {

                    materiasPorPNF[
                        materia.id_pnf
                    ].materias.push(materia);

                }

            });


            /* =================================================
               GENERAR RESULTADOS
               ================================================= */

            Object.values(materiasPorPNF).forEach(pnf => {

                if (pnf.materias.length === 0) {
                    return;
                }


                /* =============================================
                   CONTENEDOR DEL PNF
                   ============================================= */

                const bloque = document.createElement("div");

                bloque.classList.add(
                    "director-materias-consulta-carsce-bloque"
                );


                /* =============================================
                   CABECERA DEL RESULTADO
                   ============================================= */

                const cabecera = document.createElement("div");

                cabecera.classList.add(
                    "director-materias-consulta-carsce-resultado-cabecera"
                );


                cabecera.innerHTML = `

                    <div class="director-materias-consulta-carsce-resultado-identidad">

                        <div class="director-materias-consulta-carsce-resultado-icono">
                            <i class="fa-solid fa-graduation-cap"></i>
                        </div>

                        <div>

                            <span class="director-materias-consulta-carsce-resultado-etiqueta">
                                PROGRAMA NACIONAL DE FORMACIÓN
                            </span>

                            <h4 class="director-materias-consulta-carsce-resultado-titulo">
                                ${pnf.nombre}
                            </h4>

                        </div>

                    </div>


                    <div class="director-materias-consulta-carsce-contador">

                        <strong>
                            ${pnf.materias.length}
                        </strong>

                        <span>
                            ${pnf.materias.length === 1
                                ? "materia registrada"
                                : "materias registradas"}
                        </span>

                    </div>

                `;


                /* =============================================
                   CONTENEDOR DE TABLA
                   ============================================= */

                const tabla_contenedor = document.createElement("div");

                tabla_contenedor.classList.add(
                    "director-materias-consulta-carsce-tabla-contenedor"
                );


                /* =============================================
                   TABLA
                   ============================================= */

                const tabla = document.createElement("table");

                tabla.classList.add(
                    "director-materias-consulta-carsce-tabla"
                );


                let filas = "";


                pnf.materias.forEach((materia, index) => {

                    filas += `

                        <tr>

                            <td class="director-materias-consulta-carsce-columna-id">
                                ${index + 1}
                            </td>

                            <td class="director-materias-consulta-carsce-columna-materia">
                                ${materia.nombre}
                            </td>

                            <td>
                                ${materia.codigo}
                            </td>

                            <td>
                                ${materia.htea}
                            </td>

                            <td>
                                ${materia.htei}
                            </td>

                            <td>
                                ${materia.id_trayecto__nombre}
                            </td>

                            <td>
                                ${materia.recuperacion}
                            </td>

                            <td>
                                ${materia.tipo_materia}
                            </td>

                        </tr>

                    `;

                });


                tabla.innerHTML = `

                    <thead>

                        <tr>

                            <th>ID</th>
                            <th>Materia</th>
                            <th>Código</th>
                            <th>HTEA</th>
                            <th>HTEI</th>
                            <th>Trayecto</th>
                            <th>Recuperación</th>
                            <th>Tipo de Materia</th>

                        </tr>

                    </thead>

                    <tbody>

                        ${filas}

                    </tbody>

                `;


                tabla_contenedor.appendChild(tabla);

                bloque.appendChild(cabecera);

                bloque.appendChild(tabla_contenedor);

                contenedor_materias.appendChild(bloque);

            });


        } catch (error) {

            console.error(
                "Error al consultar las materias:",
                error
            );

        }

    }


    /* =========================================================
       INICIALIZAR
       ========================================================= */

    pnfs_registrados();

    materias_registradas();


    select_busqueda_pnf.addEventListener(
        "change",
        materias_registradas
    );

});