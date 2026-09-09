document.addEventListener("DOMContentLoaded", () => {
    const dialogo = document.getElementById("datos_estudiantes")
    const btn_cerrar_dialogo = document.getElementById("cerrar_dialogo")

    const control_nombre_estudiante = document.getElementById("nombres_estudiante")
    const control_apellido_estudiante = document.getElementById("apellidos_estudiante")
    const control_ci_estudiante = document.getElementById("ci_estudiante")
    const control_genero_estudiante = document.getElementById("genero_estudiante")
    const control_estado_civil_estudiante = document.getElementById("estado_civil_estudiante")

    const control_telefono_principal = document.getElementById("telefono_principal")
    const control_telefono_secundario = document.getElementById("telefono_secundario")
    const control_correo_principal = document.getElementById("correo_principal")
    const control_correo_secundario = document.getElementById("correo_secundario")

    const control_nombres_representante = document.getElementById("nombres_representante")
    const control_apellidos_representante = document.getElementById("apellidos_representante")
    const control_ci_representante = document.getElementById("ci_representante")
    const control_telefono_representante = document.getElementById("telefono_representante")
    const control_parentesco_representante = document.getElementById("parentesco_representante")

    const control_pais_nacimiento = document.getElementById("pais_nacimiento")
    const control_estado_nacimiento = document.getElementById("estado_nacimiento")
    const control_municipio_nacimiento = document.getElementById("municipio_nacimiento")
    const control_parroquia_nacimiento = document.getElementById("parroquia_nacimiento")
    const control_direccion_nacimiento = document.getElementById("direccion_nacimiento")
    const control_fecha_nacimiento = document.getElementById("fecha_nacimiento")

    const control_condicion_residencia = document.getElementById("condicion_residencia")
    const control_municipio_residencia = document.getElementById("municipio_residencia")
    const control_parroquia_residencia = document.getElementById("parroquia_residencia")
    const control_direccion_residencia = document.getElementById("direccion_residencia")

    const control_codigo_carnet = document.getElementById("codigo_carnet")
    const control_nro_registro = document.getElementById("nro_registro")
    const control_tipos_discapacidad = document.getElementById("tipos_discapacidad")
    const control_grados_discapacidad = document.getElementById("grados_discapacidad")
    const control_causa_discapacidad = document.getElementById("causa_discapacidad")

    const control_img_ci = document.getElementById("contenedor_ci_estudiante")
    const control_img_bachiller = document.getElementById("contenedor_titulo_bachiller_estudiante")
    const control_img_sabana = document.getElementById("contenedor_sabana_nota_estudiante")
    const control_img_opsu = document.getElementById("contenedor_opsu_estudiante")

    const select_nucleos_asignados = document.getElementById("nucleos_asignados");
    const select_pnfs_asignado = document.getElementById("pnfs_asignados");

    const contenedor_rechazados = document.getElementById("contenedor_inscripciones_rechazadas");

    let pnf = "", nucleo = "";

    function getCookie(nombre) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== "") {
            const cookies = document.cookie.split(";");

            for (let cookie of cookies) {
                cookie = cookie.trim();

                if (cookie.startsWith(nombre + "=")) {
                    cookieValue = decodeURIComponent(
                        cookie.substring(nombre.length + 1)
                    );
                    break;
                }
            }
        }

        return cookieValue;
    }
    const csrftoken = getCookie("csrftoken");

    async function nucleos_asignados() {
        try {
            const respuesta = await fetch("/obt_nucleos_asignados/");
            const resultado = await respuesta.json();
            console.log(resultado);

            select_pnfs_asignado.innerHTML = "<option value='' selected>Selecciona el núcleo primero</option>";

            select_nucleos_asignados.innerHTML = "<option value='' selected>Selecciona un núcleo</option>";

            resultado.nucleos.forEach(nucleo => {
                const option_nucleo = document.createElement("option");
                option_nucleo.value = nucleo.id_nucleo;
                option_nucleo.textContent = nucleo.municipio;
                select_nucleos_asignados.append(option_nucleo);
            });
        } catch (error) {
            console.error(error);
        }
    }
    nucleos_asignados();

    select_nucleos_asignados.addEventListener("change", async (e) => {
        nucleo = select_nucleos_asignados.value;

        await pnfs_asignados();

        await estudiantes_rechados();
    });

    async function pnfs_asignados() {
        try {
            const formulario = new FormData();
            formulario.append("nucleo_asignado", nucleo);

            const respuesta = await fetch("/obt_pnfs_asignado/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrftoken
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            select_pnfs_asignado.innerHTML = "<option value='' selected>Selecciona un P.N.F</option>";

            resultado.pnfs.forEach(pnf => {
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

        await estudiantes_rechados();
    });

    async function estudiantes_rechados() {
        try {
            if (!nucleo || !pnf) return;

            const formulario = new FormData();
            formulario.append("nucleo_asignado", nucleo);
            formulario.append("pnf_asignado", pnf);

            const respuesta = await fetch("/rech_inscr_est/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrftoken
                },
                body: formulario
            });

            const resultado = await respuesta.json();

            console.log(resultado);

            // ==========================================
            // VALIDAR RESPUESTA DEL SERVIDOR
            // ==========================================

            if (resultado.estado !== "exito") {

                contenedor_rechazados.innerHTML = "";

                Swal.fire({
                    title: resultado.titulo || "¡Advertencia!",
                    text: resultado.descripcion || "No se pudo obtener la información.",
                    icon: resultado.icon || "warning"
                });

                return;
            }

            // LIMPIAR CONTENEDOR

            contenedor_rechazados.innerHTML = "";

            // CONSTRUIR OPCIONES DE AULA

            let opcionesAula = "";

            if (resultado.aulas && resultado.aulas.length > 0) {

                opcionesAula = `
                <option value="" selected>
                    Seleccione un aula
                </option>
            `;

                resultado.aulas.forEach(aula => {

                    opcionesAula += `
                    <option value="${aula.id_aula}">
                        ${aula.nombre_aula} |
                        ${aula.tipo_aula} |
                        Piso ${aula.piso_edificio}
                    </option>
                `;
                });

            } else {

                opcionesAula = `
                <option value="">
                    No hay aulas disponibles
                </option>
            `;
            }

            // ==========================================
            // VALIDAR ESTUDIANTES
            // ==========================================

            if (!resultado.estudiantes || resultado.estudiantes.length === 0) {

                contenedor_rechazados.innerHTML = `
                <tr>
                    <td colspan="7">
                        No hay estudiantes rechazados.
                    </td>
                </tr>
            `;

                return;
            }

            // ==========================================
            // MOSTRAR ESTUDIANTES RECHAZADOS
            // ==========================================

            // MOSTRAR ESTUDIANTES RECHAZADOS
            resultado.estudiantes.forEach((estudiante, index) => {

                contenedor_rechazados.innerHTML += `
        <tr data-cedula="${estudiante.cedula_identidad}">

            <td>
                ${index + 1}
            </td>

            <td>
                ${estudiante.nombres}
            </td>

            <td>
                ${estudiante.apellidos}
            </td>

            <td>
                ${estudiante.cedula_identidad}
            </td>

            <td>
                <span class="estado_rechazado">
                    ${estudiante.estado}
                </span>
            </td>

            <td>
                <select
                    name="aula"
                    class="select_aula">

                    ${opcionesAula}

                </select>
            </td>

            <td>
                <button
                    type="button"
                    class="inscribir">
                    Inscribir
                </button>
            </td>

        </tr>
    `;
            });

        } catch (error) {

            console.error(error);

        }
    }

    contenedor_rechazados.addEventListener("click", async (e) => {
        const fila = e.target.closest("tr");
        if (e.target.closest("select") ||
            e.target.closest("button") ||
            e.target.closest("form")) {
            return;
        }
        dialogo.showModal()

        const formulario = new FormData();
        formulario.append("cedula_estudiante", fila.dataset.cedula);
        formulario.append("nucleo_asignado", nucleo);
        formulario.append("pnf_asignado", pnf);

        const respuesta = await fetch("/obt_data_est/", {
            method: "POST",
            headers: {
                "X-CSRFToken": csrftoken
            },
            body: formulario
        });
        const resultado = await respuesta.json();
        console.log(resultado);

        control_nombre_estudiante.value = resultado.usuario.nombres;
        control_apellido_estudiante.value = resultado.usuario.apellidos;
        control_ci_estudiante.value = resultado.usuario.cedula_identidad;
        control_genero_estudiante.value = resultado.usuario.genero;
        control_estado_civil_estudiante.value = resultado.usuario.estado_civil;

        control_telefono_principal.value = resultado.contacto.telefono_suplete;
        control_telefono_secundario.value = resultado.contacto.telefono_personal;
        control_correo_principal.value = resultado.contacto.correo_electronico;
        control_correo_secundario.value = resultado.contacto.correo_alternativo;

        control_nombres_representante.value = resultado.representantes.nombres;
        control_apellidos_representante.value = resultado.representantes.apellidos;
        control_ci_representante.value = resultado.representantes.cedula_identidad;
        control_telefono_representante.value = resultado.representantes.telefono;
        control_parentesco_representante.value = resultado.representantes.parentesco;

        control_pais_nacimiento.value = resultado.nacimiento.pais
        control_estado_nacimiento.value = resultado.nacimiento.estado
        control_municipio_nacimiento.value = resultado.nacimiento.municipio
        control_parroquia_nacimiento.value = resultado.nacimiento.parroquia
        control_direccion_nacimiento.value = resultado.nacimiento.direccion_nacimiento
        control_fecha_nacimiento.value = resultado.nacimiento.fecha_nacimiento

        control_condicion_residencia.value = resultado.residencia.condicion_residencia
        control_municipio_residencia.value = resultado.residencia.municipio
        control_parroquia_residencia.value = resultado.residencia.parroquia
        control_direccion_residencia.value = resultado.residencia.direccion_residencia

        control_codigo_carnet.value = resultado.discapacidad.codigo_carnet_discapacidad
        control_nro_registro.value = resultado.discapacidad.nro_registro_medico
        control_tipos_discapacidad.value = resultado.discapacidad.tipo_discapacidad
        control_grados_discapacidad.value = resultado.discapacidad.grado_discapacidad
        control_causa_discapacidad.value = resultado.discapacidad.causa_discapacidad

        console.log(resultado.documentos);

        control_img_ci.innerHTML = "";
        control_img_bachiller.innerHTML = "";
        control_img_sabana.innerHTML = "";
        control_img_opsu.innerHTML = "";

        if (Array.isArray(resultado.documentos)) {
            resultado.documentos.forEach(documento => {
                const url = documento.archivo.toLowerCase();
                let elemento;

                if (url.endsWith(".pdf")) {
                    elemento = document.createElement("embed");
                    elemento.src = documento.archivo;
                    elemento.type = "application/pdf";
                    elemento.width = "100%";
                    elemento.height = "400px";
                } else if (
                    url.endsWith(".jpg") || url.endsWith(".jpeg") || url.endsWith(".png") || url.endsWith(".webp")) {
                    elemento = document.createElement("img");
                    elemento.src = documento.archivo;
                    elemento.style.maxWidth = "250px";
                    elemento.style.height = "auto";
                } else {
                    console.warn("Formato no soportado:", documento.archivo);
                    return;
                }

                if (documento.tipo_documento === "Cédula de Identidad") {
                    control_img_ci.appendChild(elemento);
                }
                else if (documento.tipo_documento === "Título de Bachiller") {
                    control_img_bachiller.appendChild(elemento);
                }
                else if (documento.tipo_documento === "Sabana de Notas") {
                    control_img_sabana.appendChild(elemento);
                }
                else if (documento.tipo_documento === "OPSU") {
                    control_img_opsu.appendChild(elemento);
                }
            });
        }
    });

    btn_cerrar_dialogo.addEventListener("click", () => {
        dialogo.close()
    });

    const paginas = [
        document.getElementById("contenedor_datos_basicos"),
        document.getElementById("contacto_estudiante"),
        document.getElementById("contenedor_representante"),
        document.getElementById("contenedor_nacimiento"),
        document.getElementById("contenedor_residencia"),
        document.getElementById("contenedor_discapacidad"),
        document.getElementById("contenedor_ci_estudiante"),
        document.getElementById("contenedor_titulo_bachiller_estudiante"),
        document.getElementById("contenedor_sabana_nota_estudiante"),
        document.getElementById("contenedor_opsu_estudiante")
    ];

    const btnAvanzar = document.getElementById("avanzar");
    const btnRetroceder = document.getElementById("retroceder");

    let paginaActual = 0;

    function mostrarPagina() {
        paginas.forEach((pagina, indice) => {
            pagina.style.display = indice === paginaActual ? "block" : "none";
        });

        btnRetroceder.disabled = paginaActual === 0;
        btnAvanzar.disabled = paginaActual === paginas.length - 1;

        window.scrollTo({ top: 0, behavior: "smooth" });
    }
    mostrarPagina();

    btnAvanzar.addEventListener("click", () => {
        if (paginaActual < paginas.length - 1) {
            paginaActual++;
            mostrarPagina();
        }
    });

    btnRetroceder.addEventListener("click", () => {
        if (paginaActual > 0) {
            paginaActual--;
            mostrarPagina();
        }
    });

    contenedor_rechazados.addEventListener("click", async (e) => {

        if (!e.target.classList.contains("inscribir")) {
            return;
        }

        const fila = e.target.closest("tr");

        if (!fila) {
            return;
        }

        const cedula = fila.dataset.cedula;

        const selectAula = fila.querySelector(".select_aula");

        if (!selectAula) {
            Swal.fire({
                title: "¡Advertencia!",
                text: "No se encontró el selector de aula.",
                icon: "warning"
            });

            return;
        }

        const aula = selectAula.value;

        if (!aula) {
            Swal.fire({
                title: "¡Advertencia!",
                text: "Debe seleccionar un aula.",
                icon: "warning"
            });

            return;
        }

        const accion = "aceptado";

        try {
            const formulario = new FormData();
            formulario.append("cedula", cedula);
            formulario.append("aula", aula);
            formulario.append("accion", accion);
            formulario.append("nucleo_asignado", nucleo);
            formulario.append("pnf_asignado", pnf);

            const respuesta = await fetch("/inscr_est/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrftoken
                },
                body: formulario
            });

            const resultado = await respuesta.json();

            console.log(resultado);

            await Swal.fire({
                title: resultado.titulo,
                text: resultado.descripcion,
                icon: resultado.icon
            });

            if (resultado.estado === "exito") {
                await estudiantes_rechados();
            }

        } catch (error) {
            console.error(error);
        }
    });
});