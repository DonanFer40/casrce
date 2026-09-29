document.addEventListener("DOMContentLoaded", () => {
    const contenedor_pre_inscripcion = document.getElementById("contenedor_pre_inscripcion")

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

    const label_pnf = document.getElementById("label_pnf");
    const select_pnfs_asignado = document.getElementById("pnfs_asignados");

    const select_resultado_admision = document.getElementById("resultado_admision");

    const select_perfiles_asignados = document.getElementById("perfiles_asignados");
    const input_perfil_asignado = document.getElementById("perfil_asignado");
    const select_seleccion_coordinador = document.getElementById("seleccion_coordinador");
    const contenedor_seleccion_coordinador = document.getElementById("contenedor_seleccion_coordinador");

    const csrftoken = document.querySelector("[name=csrfmiddlewaretoken]").value;

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

    let paginaActual = 0, pnf = "", admision = "";
    let perfil_seleccionado = "";

    admision = select_resultado_admision.value;

    select_resultado_admision.addEventListener("change", async () => {
        admision = select_resultado_admision.value;

        await estudiante_pre_inscripcion(perfil_seleccionado);
    });

    async function perfiles_asignados() {
        try {
            const respuesta = await fetch("/perf_asig_coord/");
            const resultado = await respuesta.json();

            console.log(resultado);

            const tiene_coordinador = resultado.coordinador_pnf;
            const tiene_control = resultado.control_estudio;

            input_perfil_asignado.value = "";

            select_perfiles_asignados.innerHTML = `
            <option value="" selected>
                Selecciona un perfil
            </option>
        `;

            if (tiene_coordinador && tiene_control) {

                const option_coordinador = document.createElement("option");
                option_coordinador.value = "COORDINADOR_PNF";
                option_coordinador.textContent = "Coordinador de PNF";

                const option_control = document.createElement("option");
                option_control.value = "CONTROL_ESTUDIO";
                option_control.textContent =
                    "Encargado de Control de Estudio";

                select_perfiles_asignados.append(
                    option_coordinador,
                    option_control
                );

                select_perfiles_asignados.style.display = "";
                input_perfil_asignado.style.display = "";

                perfil_seleccionado = "";

                label_pnf.style.display = "none";
                select_pnfs_asignado.style.display = "none";

            } else if (tiene_coordinador) {

                perfil_seleccionado = "COORDINADOR_PNF";

                input_perfil_asignado.value =
                    "Coordinador de PNF";

                input_perfil_asignado.style.display = "";
                select_perfiles_asignados.style.display = "none";

                label_pnf.style.display = "none";
                select_pnfs_asignado.style.display = "none";

            } else if (tiene_control) {

                perfil_seleccionado = "CONTROL_ESTUDIO";

                input_perfil_asignado.value =
                    "Encargado de Control de Estudio";

                input_perfil_asignado.style.display = "";
                select_perfiles_asignados.style.display = "none";

                label_pnf.style.display = "";
                select_pnfs_asignado.style.display = "";

            } else {

                perfil_seleccionado = "";

                input_perfil_asignado.value = "";

                input_perfil_asignado.style.display = "";
                select_perfiles_asignados.style.display = "none";

                label_pnf.style.display = "none";
                select_pnfs_asignado.style.display = "none";
            }

            await pnfs_asignados(perfil_seleccionado);

            admision = select_resultado_admision.value;

            if (admision) {
                await estudiante_pre_inscripcion(
                    perfil_seleccionado
                );
            }

        } catch (error) {
            console.error(error);
        }
    }

    perfiles_asignados();

    select_perfiles_asignados.addEventListener("change", async () => {
        perfil_seleccionado = select_perfiles_asignados.value;

        if (!perfil_seleccionado) {
            label_pnf.style.display = "none";
            select_pnfs_asignado.style.display = "none";

            contenedor_seleccion_coordinador.style.display = "none";
            return;
        }

        if (perfil_seleccionado === "CONTROL_ESTUDIO") {
            label_pnf.style.display = "";
            select_pnfs_asignado.style.display = "";

            contenedor_seleccion_coordinador.style.display = "";
        } else {

            label_pnf.style.display = "none";
            select_pnfs_asignado.style.display = "none";

            select_pnfs_asignado.value = "";

            contenedor_seleccion_coordinador.style.display = "none";

            select_seleccion_coordinador.innerHTML = `
                <option value="" selected>
                    Selecciona un Coordinador de PNF
                </option>
            `;
        }

        await pnfs_asignados(perfil_seleccionado);
        await estudiante_pre_inscripcion(perfil_seleccionado);
    });

    async function pnfs_asignados(perfil_seleccionado) {
        try {
            const formulario = new FormData();
            formulario.append("perfil", perfil_seleccionado);

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

        await estudiante_pre_inscripcion(perfil_seleccionado);
    });

    async function estudiante_pre_inscripcion(perfil_seleccionado) {
        try {
            const formulario = new FormData();
            formulario.append("perfil", perfil_seleccionado);
            formulario.append("pnf_asignado", pnf);
            formulario.append("admision", admision);

            const endpoint = admision === "NO_ADMITIDO" ? "/rech_inscr_est/" : "/obt_pre_inscrt/";

            const respuesta = await fetch(endpoint, {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrftoken
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            if (resultado.estado !== "exito") {
                contenedor_pre_inscripcion.innerHTML = "";
                Swal.fire({
                    title: resultado.titulo,
                    text: resultado.descripcion,
                    icon: resultado.icon
                });
                return;
            }

            contenedor_pre_inscripcion.innerHTML = "";

            // AULAS
            let opciones_aula = "";

            if (resultado.aulas && resultado.aulas.length > 0) {
                opciones_aula = `
                    <option value="" selected>
                        Seleccione un aula
                    </option>
                `;

                resultado.aulas.forEach(aula => {
                    opciones_aula += `
                        <option value="${aula.id_aula}">
                            ${aula.nombre_aula} |
                            ${aula.tipo_aula} |
                            Piso ${aula.piso_edificio}
                        </option>
                    `;
                });
            } else {
                opciones_aula = `
                    <option value="">
                        No hay aulas disponibles
                    </option>
                `;
            }

            // ESTUDIANTES
            if (!resultado.estudiantes || resultado.estudiantes.length === 0) {
                contenedor_pre_inscripcion.innerHTML = `
                    <tr>
                        <td colspan="7">
                            ${perfil_seleccionado === "CONTROL_ESTUDIO" && !pnf
                        ? "Debe seleccionar un PNF para consultar los estudiantes preinscritos."
                        : admision === "NO_ADMITIDO"
                            ? "No hay estudiantes no admitidos."
                            : "No hay estudiantes pendientes de admisión."
                    }
                        </td>
                    </tr>
                `;
                return;
            }

            resultado.estudiantes.forEach((estudiante, index) => {
                if (admision === "NO_ADMITIDO") {
                    contenedor_pre_inscripcion.innerHTML += `
                    <tr data-cedula="${estudiante.cedula_identidad}">
                        <td>${index + 1}</td>
                        <td>${estudiante.nombres}</td>
                        <td>${estudiante.apellidos}</td>
                        <td>${estudiante.cedula_identidad}</td>
                        <td>
                            <span class="estado_no_admitido">${estudiante.estado}</span>
                        </td>
                        <td>
                            <select name="aula" class="select_aula">
                                ${opciones_aula}
                            </select>
                        </td>
                        <td>
                            <button type="button" class="inscribir"> Admitir</button>
                        </td>
                    </tr>
                `;
                } else {
                    contenedor_pre_inscripcion.innerHTML += `
                        <tr data-cedula="${estudiante.cedula_identidad}">
                            <td>${index + 1}</td>
                            <td>${estudiante.nombres}</td>
                            <td>${estudiante.apellidos}</td>
                            <td>${estudiante.cedula_identidad}</td>
                            <td>
                                <select name="aula" class="select_aula">
                                    ${opciones_aula}
                                </select>
                            </td>
                            <td>
                                <button type="button" class="inscribir">Admitir</button>
                            </td>
                            <td>
                                <button type="button" class="rechazar">No Admitir</button>
                            </td>
                        </tr>
                    `;
                }
            });

        } catch (error) {
            console.error(error);
        }
    }

    contenedor_pre_inscripcion.addEventListener("click", async (e) => {
        const fila = e.target.closest("tr");
        if (e.target.closest("select") ||
            e.target.closest("button") ||
            e.target.closest("form")) {
            return;
        }
        dialogo.showModal()

        const formulario = new FormData();
        formulario.append("cedula_estudiante", fila.dataset.cedula);
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

    contenedor_pre_inscripcion.addEventListener("click", async (e) => {
        if (!e.target.classList.contains("inscribir") &&
            !e.target.classList.contains("rechazar")) {
            return;
        }

        const fila = e.target.closest("tr");
        const cedula = fila.dataset.cedula;

        const accion = e.target.classList.contains("inscribir")
            ? "Admitido"
            : "No Admitido";

        const aula = e.target.classList.contains("inscribir")
            ? fila.querySelector(".select_aula").value
            : "";

        try {
            const formulario = new FormData();

            formulario.append("cedula", cedula);
            formulario.append("aula", aula);
            formulario.append("accion", accion);
            formulario.append("pnf_asignado", pnf);
            formulario.append("perfil", perfil_seleccionado);

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
                await estudiante_pre_inscripcion(perfil_seleccionado);
            }

        } catch (error) {
            console.error(error);
        }
    });

});