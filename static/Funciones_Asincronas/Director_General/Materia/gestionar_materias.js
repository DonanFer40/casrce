document.addEventListener("DOMContentLoaded", () => {
    // =========================================================
    // 1. REFERENCIAS DE ELEMENTOS DEL DOM
    // =========================================================
    const formularioMateria = document.getElementById("formulario_materia");
    const inputMateriaSeleccionado = document.getElementById("materia_seleccionado");
    
    // Botones y Cabecera Dinámica del Formulario
    const btnAccionMateria = document.getElementById("btn_accion_materia");
    const iconoBtnAccion = document.getElementById("icono_btn_accion");
    const textoBtnAccion = document.getElementById("texto_btn_accion");
    
    const etiquetaModoForm = document.getElementById("etiqueta_modo_form");
    const tituloForm = document.getElementById("titulo_form");
    const descripcionForm = document.getElementById("descripcion_form");
    const iconoCabeceraForm = document.getElementById("icono_cabecera_form");

    // Inputs y Selects del Formulario (Izquierda)
    const inputNombresMaterias = document.getElementById("nombres_materias");
    const inputCodigosMaterias = document.getElementById("codigos_materias");
    const mensajeCodigoMateria = document.getElementById("mensaje_codigo_materia");
    const selectPeriodoMateria = document.getElementById("periodo_materia");
    const selectTrayectoMateria = document.getElementById("trayecto_materia");
    const selectPnfMateria = document.getElementById("pnfs_materia");
    const selectTipoMateria = document.getElementById("tipo_materia");
    const selectReparacionMateria = document.getElementById("reparacion_materia");

    // Elementos de Visualización y Búsqueda (Derecha)
    const select_busqueda_pnf = document.getElementById("buscar_pnf");
    const contenedor_materias = document.getElementById("contenedor_tablas_materia");

    // Alerta de Modo Edición
    const alertaEdicion = document.getElementById("alerta_modo_edicion");
    const badgeNombreMateria = document.getElementById("nombre_materia_edicion_badge");
    const btnCancelarEdicion = document.getElementById("btn_cancelar_edicion");

    const periodos_textos = {
        "INICIAL_TRIMESTRE": "Inicial Trimestre (P.I.U)",
        "INICIAL_SEMESTRE": "Inicial Semestre (P.I.U)",
        "REPARACION": "Reparación",
        "TRIMESTRE": "Trimestre",
        "TRAMO_I": "I Tramo",
        "TRAMO_II": "II Tramo",
        "TRAMO_III": "III Tramo",
        "TRAMO_I_II": "I y II Tramos",
        "TRAMO_II_III": "II y III Tramos",
        "TRAMO_I_III": "I y III Tramos",
        "SEMESTRE": "Semestre",
        "SEMESTRE_I": "I Semestre",
        "SEMESTRE_II": "II Semestre"
    };


    // =========================================================
    // 2. VALIDACIONES DE ENTRADA (THEA, THEI, TEXTO Y CÓDIGO)
    // =========================================================
    document.querySelectorAll("#THEA, #THEI").forEach(input => {
        input.addEventListener("input", function () {
            let valor = this.value.replace(/[^0-9,]/g, "");
            const partes = valor.split(",");
            if (partes.length > 2) {
                valor = partes[0] + "," + partes.slice(1).join("");
            }
            if (valor.includes(",")) {
                let [entero, decimal] = valor.split(",");
                valor = entero.slice(0, 2) + "," + decimal.slice(0, 1);
            } else {
                valor = valor.slice(0, 2);
            }
            this.value = valor;
        });
    });

    if (inputNombresMaterias) {
        inputNombresMaterias.addEventListener("input", function () {
            this.value = this.value.replace(/[^a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s]/g, '');
        });
    }

    if (inputCodigosMaterias) {
        inputCodigosMaterias.addEventListener("input", function () {
            this.value = this.value
                .toUpperCase()
                .replace(/[^A-Z0-9]/g, "")
                .slice(0, 7);
        });
        inputCodigosMaterias.addEventListener("input", validar_codigo_materia);
    }

    async function validar_codigo_materia() {
        if (inputMateriaSeleccionado && inputMateriaSeleccionado.value !== "") return;
        if (!inputCodigosMaterias || inputCodigosMaterias.value.length < 7) return;

        try {
            const formulario = new FormData();
            formulario.append("codigo", inputCodigosMaterias.value);

            const respuesta = await fetch("/codigo_materia/", {
                method: "POST",
                headers: { "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value },
                body: formulario
            });
            const resultado = await respuesta.json();

            if (resultado.existe) {
                inputCodigosMaterias.setCustomValidity("Ya existe una materia con ese código.");
                inputCodigosMaterias.classList.add("is-invalid");
                if (mensajeCodigoMateria) {
                    mensajeCodigoMateria.textContent = "Ya existe una materia con ese código.";
                    mensajeCodigoMateria.style.color = "#dc3545";
                }
                if (btnAccionMateria) btnAccionMateria.disabled = true;
            } else {
                inputCodigosMaterias.setCustomValidity("");
                inputCodigosMaterias.classList.remove("is-invalid");
                if (mensajeCodigoMateria) {
                    mensajeCodigoMateria.textContent = "El código de la materia está disponible.";
                    mensajeCodigoMateria.style.color = "#198754";
                }
                if (btnAccionMateria) btnAccionMateria.disabled = false;
            }
        } catch (error) {
            console.error(error);
        }
    }


    // =========================================================
    // 3. CARGAR P.N.F (SECTOR DE BÚSQUEDA - DERECHA)
    // =========================================================
    async function pnfs_registrados() {
        if (!select_busqueda_pnf) return;
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
            console.error("Error al cargar los P.N.F:", error);
        }
    }


    // =========================================================
    // 4. CONSULTAR Y RENDERIZAR MATERIAS (DERECHA CON CLIC)
    // =========================================================
    async function materias_registradas() {
        if (!select_busqueda_pnf || !contenedor_materias) return;

        try {
            const formulario = new FormData();
            formulario.append("pnf", select_busqueda_pnf.value);

            const respuesta = await fetch("/mat_lista/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
                },
                body: formulario
            });

            const resultado = await respuesta.json();
            contenedor_materias.innerHTML = "";

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
                    materiasPorPNF[materia.id_pnf].materias.push(materia);
                }
            });

            Object.values(materiasPorPNF).forEach(pnf => {
                if (pnf.materias.length === 0) {
                    return;
                }

                const bloque = document.createElement("div");
                bloque.classList.add("director-materias-consulta-carsce-bloque");

                const cabecera = document.createElement("div");
                cabecera.classList.add("director-materias-consulta-carsce-resultado-cabecera");

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
                        <strong>${pnf.materias.length}</strong>
                        <span>${pnf.materias.length === 1 ? "materia registrada" : "materias registradas"}</span>
                    </div>
                `;

                const tabla_contenedor = document.createElement("div");
                tabla_contenedor.classList.add("director-materias-consulta-carsce-tabla-contenedor");

                const tabla = document.createElement("table");
                tabla.classList.add("director-materias-consulta-carsce-tabla");

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
                    <tbody></tbody>
                `;

                const tbody = tabla.querySelector("tbody");
                pnf.materias.forEach((materia, index) => {
                    const tr = document.createElement("tr");
                    tr.style.cursor = "pointer";
                    tr.innerHTML = `
                        <td class="director-materias-consulta-carsce-columna-id">${index + 1}</td>
                        <td class="director-materias-consulta-carsce-columna-materia">${materia.nombre}</td>
                        <td>${materia.codigo}</td>
                        <td>${materia.htea}</td>
                        <td>${materia.htei}</td>
                        <td>${materia.id_trayecto__nombre || ''}</td>
                        <td>${materia.recuperacion || ''}</td>
                        <td>${materia.tipo_materia || ''}</td>
                    `;

                    // Evento al hacer clic en la fila para cargar datos de edición
                    tr.addEventListener("click", async () => {
                        await cargarDatosMateriaParaEditar(materia.codigo);
                    });

                    tbody.appendChild(tr);
                });

                tabla_contenedor.appendChild(tabla);
                bloque.appendChild(cabecera);
                bloque.appendChild(tabla_contenedor);
                contenedor_materias.appendChild(bloque);
            });

        } catch (error) {
            console.error("Error al consultar las materias:", error);
        }
    }


    // =========================================================
    // 5. CARGAR DATOS COMPLETOS PARA EDITAR (DESDE /mat_datos/)
    // =========================================================
    async function cargarDatosMateriaParaEditar(codigoMateria) {
        try {
            const formulario = new FormData();
            formulario.append("codigo", codigoMateria);

            const respuesta = await fetch("/mat_datos/", {
                method: "POST",
                headers: { "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value },
                body: formulario
            });
            const resultado = await respuesta.json();

            if (resultado.estado == "fallo") {
                await NotificacionesCASRCE.mostrar({
                    text: resultado.descripcion,
                    icon: resultado.icon,
                    title: resultado.title,
                    allowOutsideClick: false,
                    allowEscapeKey: false
                });
                return;
            }

            // Activar Modo Edición visualmente en el formulario izquierdo
            if (alertaEdicion) alertaEdicion.style.display = "flex";
            if (badgeNombreMateria) badgeNombreMateria.textContent = resultado.materia.nombre;

            if (etiquetaModoForm) etiquetaModoForm.textContent = "MODIFICACIÓN DE REGISTRO";
            if (tituloForm) tituloForm.textContent = "Modificar Materia";
            if (descripcionForm) descripcionForm.textContent = `Actualizando los parámetros académicos de ${resultado.materia.nombre}.`;
            if (iconoCabeceraForm) iconoCabeceraForm.innerHTML = `<i class="fa-solid fa-pen-to-square"></i>`;

            if (btnAccionMateria) {
                btnAccionMateria.classList.add("modo-actualizar");
                btnAccionMateria.disabled = false;
            }
            if (iconoBtnAccion) iconoBtnAccion.className = "fa-solid fa-floppy-disk";
            if (textoBtnAccion) textoBtnAccion.textContent = "Actualizar Materia";

            // Asignar valores a los campos
            if (inputMateriaSeleccionado) inputMateriaSeleccionado.value = resultado.materia.id_materia;
            if (inputNombresMaterias) inputNombresMaterias.value = resultado.materia.nombre;
            if (inputCodigosMaterias) inputCodigosMaterias.value = resultado.materia.codigo;
            document.getElementById("THEA").value = String(resultado.materia.htea).replace(".", ",");
            document.getElementById("THEI").value = String(resultado.materia.htei).replace(".", ",");
            if (selectReparacionMateria) selectReparacionMateria.value = resultado.materia.recuperacion;
            if (selectTipoMateria) selectTipoMateria.value = resultado.materia.tipo_materia;

            const periodo = resultado.materia.tipo_periodo;
            if (selectPeriodoMateria) {
                selectPeriodoMateria.innerHTML = `<option value="${periodo}" selected>${periodos_textos[periodo] || periodo}</option>`;
            }

            // Cargar selectores dependientes de PNF y Trayecto
            await cargarPnfsPorPeriodoEdicion(periodo, resultado.pnf.id_pnf);
            await cargarTrayectosPorPeriodoEdicion(periodo, resultado.materia.trayecto.id_trayecto);

            document.getElementById("director-materias-formulario-carsce")?.scrollIntoView({ behavior: 'smooth' });

        } catch (error) {
            console.error(error);
        }
    }


    // =========================================================
    // 6. CAMBIO DE PERIODO ACADÉMICO (REGISTRO Y DINÁMICO)
    // =========================================================
    if (selectPeriodoMateria) {
        selectPeriodoMateria.addEventListener("change", async () => {
            const valor = selectPeriodoMateria.value;
            if (selectTrayectoMateria) selectTrayectoMateria.disabled = true;

            if (!valor) return;

            selectTipoMateria.innerHTML = `
                <option value=''>Seleccionar el Tipo de Materia</option>
                <option value="Curso">Curso</option>
                <option value="Electiva">Electiva</option>
            `;

            const option_electiva = selectTipoMateria.querySelector("option[value='Electiva']");
            if (valor === "INICIAL_TRIMESTRE" || valor === "INICIAL_SEMESTRE" || valor === "TRIMESTRE") {
                if (option_electiva) option_electiva.hidden = true;
                selectTipoMateria.value = "Curso";
            } else {
                if (option_electiva) option_electiva.hidden = false;
                selectTipoMateria.value = "";
            }

            await cargarPnfsPorPeriodo(valor);
            await cargarTrayectosPorPeriodo(valor);
        });
    }

    async function cargarPnfsPorPeriodo(valor) {
        try {
            const formulario = new FormData();
            formulario.append("periodo_academico", valor);

            const respuesta = await fetch("/pnf_per_acad/", {
                method: "POST",
                headers: { "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value },
                body: formulario
            });
            const resultado = await respuesta.json();

            if (selectPnfMateria) selectPnfMateria.innerHTML = "<option value=''>Seleccionar el P.N.F</option>";
            if (resultado.estado === "exito") {
                resultado.nucleos.forEach(nucleo => {
                    nucleo.pnfs.forEach(pnf => {
                        const option = document.createElement("option");
                        option.value = pnf.id_pnf;
                        option.textContent = pnf.pnf;
                        if (selectPnfMateria) selectPnfMateria.appendChild(option);
                    });
                });
            }
        } catch (error) {
            console.error(error);
        }
    }

    async function cargarTrayectosPorPeriodo(valor) {
        try {
            const respuesta = await fetch("/tray_reg_acad/");
            const resultado = await respuesta.json();

            if (resultado.estado === "exito") {
                let opciones = [];
                if (valor === "INICIAL_TRIMESTRE" || valor === "INICIAL_SEMESTRE") {
                    opciones = ["Trayecto Inicial"];
                } else if (valor === "TRIMESTRE" || valor.startsWith("TRAMO_")) {
                    opciones = ["Trayecto I", "Trayecto II", "Trayecto III", "Trayecto IV"];
                } else {
                    opciones = ["Trayecto I", "Trayecto II", "Trayecto III", "Trayecto IV", "Trayecto V"];
                }

                const trayectos = resultado.trayectos.filter(t => opciones.includes(t.nombre));

                if (selectTrayectoMateria) {
                    selectTrayectoMateria.innerHTML = "<option value=''>Seleccionar el Trayecto</option>";
                    if (trayectos.length > 0) {
                        selectTrayectoMateria.disabled = false;
                        trayectos.forEach(trayecto => {
                            const option = document.createElement("option");
                            option.value = trayecto.id_periodo_academico;
                            option.textContent = trayecto.nombre;
                            selectTrayectoMateria.appendChild(option);
                        });
                    } else {
                        selectTrayectoMateria.innerHTML = `<option value="">No disponible</option>`;
                    }
                }
            }
        } catch (error) {
            console.error(error);
        }
    }

    async function cargarPnfsPorPeriodoEdicion(periodo, id_pnf_actual) {
        try {
            const formulario = new FormData();
            formulario.append("periodo_academico", periodo);

            const respuesta = await fetch("/pnf_per_acad/", {
                method: "POST",
                headers: { "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value },
                body: formulario
            });
            const resultado = await respuesta.json();

            if (selectPnfMateria) selectPnfMateria.innerHTML = "<option value=''>Seleccionar el P.N.F</option>";
            if (resultado.estado === "exito") {
                resultado.nucleos.forEach(nucleo => {
                    nucleo.pnfs.forEach(pnf => {
                        const option = document.createElement("option");
                        option.value = pnf.id_pnf;
                        option.textContent = pnf.pnf;
                        if (Number(pnf.id_pnf) === Number(id_pnf_actual)) {
                            option.selected = true;
                        }
                        if (selectPnfMateria) selectPnfMateria.appendChild(option);
                    });
                });
            }
        } catch (error) {
            console.error(error);
        }
    }

    async function cargarTrayectosPorPeriodoEdicion(valor, id_trayecto_actual) {
        try {
            const respuesta = await fetch("/tray_reg_acad/");
            const resultado = await respuesta.json();

            if (resultado.estado === "exito") {
                let opciones = [];
                if (valor === "INICIAL_TRIMESTRE" || valor === "INICIAL_SEMESTRE") {
                    opciones = ["Trayecto Inicial"];
                } else if (valor === "TRIMESTRE" || valor.startsWith("TRAMO_")) {
                    opciones = ["Trayecto I", "Trayecto II", "Trayecto III", "Trayecto IV"];
                } else {
                    opciones = ["Trayecto I", "Trayecto II", "Trayecto III", "Trayecto IV", "Trayecto V"];
                }

                const trayectos = resultado.trayectos.filter(t => opciones.includes(t.nombre));

                if (selectTrayectoMateria) {
                    selectTrayectoMateria.innerHTML = "<option value=''>Seleccionar el Trayecto</option>";
                    if (trayectos.length > 0) {
                        selectTrayectoMateria.disabled = false;
                        trayectos.forEach(trayecto => {
                            const option = document.createElement("option");
                            option.value = trayecto.id_periodo_academico;
                            option.textContent = trayecto.nombre;
                            if (Number(trayecto.id_periodo_academico) === Number(id_trayecto_actual)) {
                                option.selected = true;
                            }
                            selectTrayectoMateria.appendChild(option);
                        });
                    }
                }
            }
        } catch (error) {
            console.error(error);
        }
    }


    // =========================================================
    // 7. CANCELAR MODO EDICIÓN (RESTAURAR A REGISTRO)
    // =========================================================
    function restaurarModoRegistro() {
        if (!alertaEdicion) return;

        alertaEdicion.style.display = "none";
        formularioMateria.reset();
        if (inputMateriaSeleccionado) inputMateriaSeleccionado.value = "";

        if (etiquetaModoForm) etiquetaModoForm.textContent = "NUEVO REGISTRO";
        if (tituloForm) tituloForm.textContent = "Registrar Materia";
        if (descripcionForm) descripcionForm.textContent = "Completa la información académica y horaria correspondiente a la asignatura.";
        if (iconoCabeceraForm) iconoCabeceraForm.innerHTML = `<i class="fa-solid fa-book"></i>`;

        if (btnAccionMateria) {
            btnAccionMateria.classList.remove("modo-actualizar");
            btnAccionMateria.disabled = false;
        }
        if (iconoBtnAccion) iconoBtnAccion.className = "fa-solid fa-plus";
        if (textoBtnAccion) textoBtnAccion.textContent = "Registrar Materia";

        if (selectTrayectoMateria) {
            selectTrayectoMateria.innerHTML = "<option value=''>Seleccionar el Trayecto</option>";
            selectTrayectoMateria.disabled = true;
        }
        if (selectPnfMateria) selectPnfMateria.innerHTML = "<option value=''>Seleccionar el P.N.F</option>";
        if (selectTipoMateria) selectTipoMateria.innerHTML = "<option value=''>Seleccionar el Tipo de Materia</option>";
        if (mensajeCodigoMateria) mensajeCodigoMateria.textContent = "";
    }

    if (btnCancelarEdicion) {
        btnCancelarEdicion.addEventListener("click", restaurarModoRegistro);
    }


    // =========================================================
    // 8. ENVÍO DE FORMULARIO (REGISTRAR O ACTUALIZAR)
    // =========================================================
    if (formularioMateria) {
        formularioMateria.addEventListener("submit", async (e) => {
            e.preventDefault();
            try {
                const esEdicion = inputMateriaSeleccionado && inputMateriaSeleccionado.value !== "";
                const urlDestino = esEdicion ? "/mat_guardar/" : "/reg_mat/";

                const formulario = new FormData(formularioMateria);
                const respuesta = await fetch(urlDestino, {
                    method: "POST",
                    headers: { "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value },
                    body: formulario
                });
                const resultado = await respuesta.json();

                await NotificacionesCASRCE.mostrar({
                    text: resultado.descripcion,
                    icon: resultado.icon,
                    title: resultado.title || "Aviso",
                    allowOutsideClick: false,
                    allowEscapeKey: false
                });

                if (resultado.estado == "exito") {
                    restaurarModoRegistro();
                    materias_registradas(); // Refrescar las tablas de la derecha
                }
            } catch (error) {
                console.error(error);
            }
        });
    }


    // =========================================================
    // 9. INICIALIZACIÓN GENERAL
    // =========================================================
    pnfs_registrados();
    materias_registradas();

    if (select_busqueda_pnf) {
        select_busqueda_pnf.addEventListener("change", materias_registradas);
    }
});