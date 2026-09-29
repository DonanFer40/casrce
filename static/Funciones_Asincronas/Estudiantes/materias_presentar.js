document.addEventListener("DOMContentLoaded", () => {

    const select_nucleo_presentar = document.getElementById("nucleo_presentar");
    const select_pnfs_cursar = document.getElementById("pnfs_cursar");
    const select_trayecto_academico = document.getElementById("trayecto_academico");

    const contenedor_datos_academicos = document.getElementById("contenedor_datos_academicos");

    let pnf = "", nucleo = "", trayecto = ""

    async function nucleos_asignados() {
        try {
            const respuesta = await fetch("/notas_academicas/nucl_est_asig/");
            const resultado = await respuesta.json();
            console.log(resultado);

            select_pnfs_cursar.innerHTML = "<option value='' selected>Selecciona el núcleo primero</option>";

            select_nucleo_presentar.innerHTML = "<option value='' selected>Selecciona un núcleo</option>";

            resultado.nucleos.forEach(nucleo => {
                const option_nucleo = document.createElement("option");
                option_nucleo.value = nucleo.id_nucleo;
                option_nucleo.textContent = nucleo.municipio;
                select_nucleo_presentar.append(option_nucleo);
            });
        } catch (error) {
            console.error(error);
        }
    }
    nucleos_asignados();

    select_nucleo_presentar.addEventListener("change", async () => {
        nucleo = select_nucleo_presentar.value;

        await pnfs_asignados();

        await trayectos_academicos();
    });

    async function pnfs_asignados() {
        try {
            const formulario = new FormData();
            formulario.append("id_nucleo", nucleo);

            const respuesta = await fetch("/notas_academicas/pnfs_est_asig/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            select_pnfs_cursar.innerHTML = "<option value='' selected>Selecciona un P.N.F</option>";

            resultado.pnfs.forEach(pnf => {
                const option_pnf = document.createElement("option");
                option_pnf.value = pnf.id_pnf;
                option_pnf.textContent = pnf.pnf;
                select_pnfs_cursar.append(option_pnf);
            });
        } catch (error) {
            console.error(error);
        }
    }

    select_pnfs_cursar.addEventListener("change", async () => {
        pnf = select_pnfs_cursar.value;

        await trayectos_academicos();
    });

    async function trayectos_academicos() {
        try {
            if (!nucleo || !pnf) return;

            const formulario = new FormData();
            formulario.append("id_nucleo", nucleo);
            formulario.append("id_pnf", pnf);

            const respuesta = await fetch("/notas_academicas/tray_est_curs/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            select_trayecto_academico.innerHTML = "<option value='' selected>Selecciona la trayecto academico</option>";

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

            resultado.trayectos.forEach(trayecto => {
                const option_trayecto = document.createElement("option");
                option_trayecto.value = trayecto.id_trayecto;
                option_trayecto.textContent = trayecto.trayecto;
                select_trayecto_academico.append(option_trayecto);
            });
        } catch (error) {
            console.error(error);
        }
    }

    select_trayecto_academico.addEventListener("change", async () => {
        trayecto = select_trayecto_academico.value;

        await materias_presentada();
    });

    async function materias_presentada() {
        try {
            contenedor_datos_academicos.innerHTML = "";

            const formulario = new FormData();
            formulario.append("id_nucleo", nucleo);
            formulario.append("id_pnf", pnf);
            formulario.append("id_trayecto", trayecto);

            const respuesta = await fetch("/notas_academicas/mat_present_est/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector(
                        "[name=csrfmiddlewaretoken]"
                    ).value
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            if (resultado.estado === "fallo") {
                await Swal.fire({
                    text: resultado.descripcion,
                    icon: resultado.icon,
                    title: resultado.title,
                    allowOutsideClick: false,
                    allowEscapeKey: false
                });
                return;
            }

            if (
                resultado.estado === "exito" &&
                (!resultado.trayectos || resultado.trayectos.length === 0)
            ) {
                contenedor_datos_academicos.innerHTML = `
                <div class="mensaje_sin_materias">
                    <span>No existen materias disponibles para mostrar.</span>
                </div>
            `;

                return;
            }

            resultado.trayectos.forEach((trayecto) => {

                let filas = "";

                if (
                    !trayecto.materias ||
                    trayecto.materias.length === 0
                ) {

                    filas = `
                    <tr>
                        <td colspan="10" class="mensaje_tabla">
                            No existen materias registradas para este trayecto.
                        </td>
                    </tr>
                `;

                } else {

                    trayecto.materias.forEach((materia) => {

                        filas += `
                        <tr>

                            <td>
                                ${materia.codigo_materia ?? "—"}
                            </td>

                            <td>
                                ${materia.nombre_materia ?? "—"}
                            </td>

                            <td>
                                ${materia.htea ?? "—"}
                            </td>

                            <td>
                                ${materia.htei ?? "—"}
                            </td>

                            <td>
                                ${materia.thte ?? "—"}
                            </td>

                            <td>
                                ${materia.uc ?? "—"}
                            </td>

                        </tr>
                    `;
                    });
                }

                const bloque_trayecto = document.createElement("div");

                bloque_trayecto.classList.add(
                    "bloque_materias_trayecto"
                );

                bloque_trayecto.innerHTML = `
                <div class="titulo_trayecto">
                    <h3>${trayecto.trayecto}</h3>
                </div>

                <div class="contenedor_tabla_materias">

                    <table class="tabla_materias_presentadas">

                        <thead>
                            <tr>
                                <th>Código</th>
                                <th>Materia</th>
                                <th>HTEA</th>
                                <th>HTEI</th>
                                <th>THTE</th>
                                <th>UC</th>
                            </tr>
                        </thead>

                        <tbody>
                            ${filas}
                        </tbody>

                    </table>

                </div>
            `;

                contenedor_datos_academicos.appendChild(
                    bloque_trayecto
                );
            });

        } catch (error) {
            console.error(error);
        }
    }
    materias_presentada();

});