document.addEventListener("DOMContentLoaded", () => {

    const select_nucleo_asignado = document.getElementById("nucleo_asignado");
    const select_pnfs_asignado = document.getElementById("pnf_asignado");
    const select_materia_asignada = document.getElementById("materia_asignada");
    const select_fecha_registradas = document.getElementById("fecha_registradas");
    const input_trayecto_academico = document.getElementById("trayecto_academico");

    const contenedor_evaluaciones = document.getElementById("contenedor_evaluaciones");

    let materia = "", pnf = "", nucleo = "", fecha = "";

    function obtener_csrf_token() {

        const cookie = document.cookie
            .split("; ")
            .find(row => row.startsWith("csrftoken="));

        return cookie
            ? decodeURIComponent(cookie.split("=")[1])
            : "";
    }

    async function nucleos_asignados() {
        try {
            const respuesta = await fetch("/notas_academicas/nucl_asig_doc/");
            const resultado = await respuesta.json();
            console.log(resultado);

            select_pnfs_asignado.innerHTML = "<option value='' selected>Selecciona el núcleo primero</option>";

            select_nucleo_asignado.innerHTML = "<option value='' selected>Selecciona un núcleo</option>";

            resultado.datos.forEach(nucleo => {
                const option_nucleo = document.createElement("option");
                option_nucleo.value = nucleo.id_nucleo;
                option_nucleo.textContent = nucleo.municipio;
                select_nucleo_asignado.append(option_nucleo);
            });
        } catch (error) {
            console.error(error);
        }
    }
    nucleos_asignados();

    select_nucleo_asignado.addEventListener("change", async (e) => {
        nucleo = select_nucleo_asignado.value;

        await pnfs_asignados();

        await materias_reparacion();

        await estudiantes_reparacion_visualizar();
    });

    async function pnfs_asignados() {
        try {
            if (!nucleo) return;

            const formulario = new FormData();
            formulario.append("nucleo_asignado", nucleo);

            const respuesta = await fetch("/notas_academicas/pnfs_asig_doc/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": obtener_csrf_token()
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            select_materia_asignada.innerHTML = "<option value='' selected>Selecciona el pnf primero</option>";

            select_pnfs_asignado.innerHTML = "<option value='' selected>Selecciona un P.N.F</option>";

            resultado.datos.forEach(pnf => {
                const option_pnf = document.createElement("option");
                option_pnf.value = pnf.id_pnf;
                option_pnf.textContent = pnf.pnf;
                select_pnfs_asignado.append(option_pnf);
            });
        } catch (error) {
            console.error(error);
        }
    }

    select_pnfs_asignado.addEventListener("change", async (e) => {
        pnf = select_pnfs_asignado.value;

        await materias_reparacion();

        await estudiantes_reparacion_visualizar();
    });

    async function materias_reparacion() {
        try {
            if (!nucleo || !pnf) return;

            const formulario = new FormData();
            formulario.append("id_nucleo", nucleo);
            formulario.append("id_pnf", pnf);

            const respuesta = await fetch("/notas_academicas/mat_vis_not/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": obtener_csrf_token()
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            select_materia_asignada.innerHTML = "<option value='' selected>Selecciona la materia</option>";

            resultado.materias.forEach(materia => {
                const option_materia = document.createElement("option");
                option_materia.value = materia.id_materia_asignada;
                option_materia.textContent = materia.nombre;
                option_materia.dataset.trayecto = materia.trayecto;
                option_materia.dataset.id_trayecto = materia.id_trayecto;
                select_materia_asignada.append(option_materia);
            });
        } catch (error) {
            console.error(error);
        }
    }

    select_materia_asignada.addEventListener("change", async () => {
        const opcion = select_materia_asignada.selectedOptions[0];
        materia = opcion.value;

        const trayecto = opcion.dataset.trayecto;
        input_trayecto_academico.value = trayecto;
        input_trayecto_academico.dataset.id_trayecto = opcion.dataset.id_trayecto;

        await fechas_reparaciones_registradas();

        await estudiantes_reparacion_visualizar();
    });

    async function fechas_reparaciones_registradas() {
        try {
            if (!materia) return;

            const formulario = new FormData();
            formulario.append("id_materia_asignacion", materia);

            const respuesta = await fetch("/notas_academicas/fech_reg_rep/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": obtener_csrf_token()
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            select_fecha_registradas.innerHTML = "<option value='' selected>Selecciona la fecha</option>";

            resultado.fechas.forEach(fecha => {
                const option_fecha = document.createElement("option");
                option_fecha.value = fecha.fecha_iso;
                option_fecha.textContent = `${fecha.fecha_mostrar} (${fecha.año})`;
                select_fecha_registradas.append(option_fecha);
            });
        } catch (error) {
            console.error(error);
        }
    }

    select_fecha_registradas.addEventListener("change", async () => {
        fecha = select_fecha_registradas.value;

        await estudiantes_reparacion_visualizar();
    });

    async function estudiantes_reparacion_visualizar() {
        try {
            const id_trayecto = input_trayecto_academico?.dataset?.id_trayecto;
            if (!nucleo || !pnf || !materia || !id_trayecto || !fecha) return;

            const formulario = new FormData();
            formulario.append("id_nucleo", nucleo);
            formulario.append("id_pnf", pnf);
            formulario.append("id_materia_asignacion", materia);
            formulario.append("fecha_reparacion", fecha);
            formulario.append("id_trayecto", id_trayecto);

            const respuesta = await fetch("/notas_academicas/reg_est_rep/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": obtener_csrf_token()
                },
                body: formulario
            });

            const resultado = await respuesta.json();

            if (resultado.estado !== "exito") {
                contenedor_evaluaciones.innerHTML = `
            <div class="alert alert-warning text-center" role="alert">
                ${resultado.descripcion || "No se pudieron obtener los datos."}
            </div>`;
                return;
            }

            if (resultado.estudiantes.length === 0) {
                contenedor_evaluaciones.innerHTML = `
            <div class="alert alert-info text-center" role="alert">
                No existen registros de reparación para esta materia.
            </div>`;
                return;
            }

            // Tabla HTML en modo lectura / consulta
            let htmlTabla = `
        <div class="table-responsive mt-3">
            <table class="table table-striped table-hover align-middle">
                <thead class="table-dark">
                    <tr>
                        <th>#</th>
                        <th>Cédula</th>
                        <th>Estudiante</th>
                        <th class="text-center">Nota Reparación</th>
                        <th class="text-center">Fecha Registro</th>
                        <th class="text-center">Estado</th>
                    </tr>
                </thead>
                <tbody>`;

            resultado.estudiantes.forEach((est, index) => {
                // Asignar color según el estado
                const esAprobado = est.calificacion >= 10;
                const badgeClase = esAprobado ? "bg-success" : "bg-danger";

                htmlTabla += `
            <tr>
                <td>${index + 1}</td>
                <td>${est.cedula}</td>
                <td>${est.nombre_completo}</td>
                <td class="text-center fw-bold">${est.calificacion.toFixed(2)}</td>
                <td class="text-center">${est.fecha_reparacion}</td>
                <td class="text-center">
                    <span class="badge ${badgeClase}">${est.estado_reparacion}</span>
                </td>
            </tr>`;
            });

            htmlTabla += `
                </tbody>
            </table>
        </div>`;

            contenedor_evaluaciones.innerHTML = htmlTabla;

        } catch (error) {
            console.error("Error al obtener las reparaciones:", error);
        }
    }

});