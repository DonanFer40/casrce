document.addEventListener("DOMContentLoaded", () => {

    const formulario_buscar = document.getElementById("buscar_materia");
    const formulario_actualizar = document.getElementById("actualizar_materia");

    const codigos_buscar_materias = document.getElementById("codigos_buscar_materias");

    const input_materia_oculta = document.getElementById("materia_seleccionado");
    const input_actualizar_nombre = document.getElementById("nombres_actualizar_materias");
    const select_actualizar_recuperacion = document.getElementById("reparacion_actualizar_materia");
    const select_actualizar_pnf = document.getElementById("pnfs_actualizar_materia");
    const select_periodo_actualizar_materia = document.getElementById("periodo_actualizar_materia");
    const select_trayecto_actualizar_materia = document.getElementById("trayecto_actualizar_materia");
    const input_thea = document.getElementById("THEA");
    const input_thei = document.getElementById("THEI");

    const btn_registrar = document.getElementById("btn_registrar");

    const periodos_materia = {
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

    document.querySelectorAll("#THEA, #THEI").forEach(input => {
        input.addEventListener("input", function () {
            let valor = this.value.replace(/[^0-9,]/g, "");

            // Permitir una sola coma
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

    controles = [
        input_actualizar_nombre,
        select_actualizar_recuperacion,
        select_actualizar_pnf,
        select_periodo_actualizar_materia,
        select_trayecto_actualizar_materia,
        input_thea,
        input_thei,
        btn_registrar
    ]

    function bloquear_controles(controles, estado) {
        controles.forEach(control => control.disabled = estado);
    }

    bloquear_controles(controles, true);

    formulario_buscar.addEventListener("submit", async (e) => {
        e.preventDefault();
        try {
            const formulario = new FormData(formulario_buscar);

            const respuesta = await fetch("/mat_datos/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            formulario_buscar.reset();

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

            bloquear_controles(controles, false);

            // MATERIA
            input_materia_oculta.value = resultado.materia.id_materia;
            input_actualizar_nombre.value = resultado.materia.nombre;
            input_thea.value = String(resultado.materia.htea).replace(".", ",");
            input_thei.value = String(resultado.materia.htei).replace(".", ",");

            // PERIODO
            const periodo = resultado.materia.tipo_periodo;

            const option_periodo = document.createElement("option");
            option_periodo.value = periodo;
            option_periodo.textContent = periodos_materia[periodo];
            option_periodo.selected = true;
            option_periodo.hidden = true;
            select_periodo_actualizar_materia.append(option_periodo);

            // RECUPERACIÓN
            const option_reparacion = document.createElement("option");
            option_reparacion.value = resultado.materia.recuperacion;
            option_reparacion.textContent = resultado.materia.recuperacion;
            option_reparacion.selected = true;
            option_reparacion.hidden = true;
            select_actualizar_recuperacion.append(option_reparacion);

            // PNF ALMACENADO
            const option_pnf = document.createElement("option");
            option_pnf.value = resultado.pnf.id_pnf;
            option_pnf.textContent = resultado.pnf.pnf;
            option_pnf.selected = true;
            option_pnf.hidden = true;
            select_actualizar_pnf.append(option_pnf);

            // TRAYECTO ALMACENADO
            const option_trayecto = document.createElement("option");
            option_trayecto.value = resultado.materia.trayecto.id_trayecto;
            option_trayecto.textContent = resultado.materia.trayecto.nombre;
            option_trayecto.selected = true;
            option_trayecto.hidden = true;
            select_trayecto_actualizar_materia.append(option_trayecto);

        } catch (error) {
            console.error(error);
        }
    });

    let periodo_academico = "";

    select_periodo_actualizar_materia.addEventListener("change", async () => {
        try {
            periodo_academico = select_periodo_actualizar_materia.value;
            if (!periodo_academico) {
                return;
            }

            // Cargar PNF correspondientes
            await pnfs_registrados(periodo_academico);

            // Cargar trayectos correspondientes
            await trayectos_registrados(periodo_academico);
        } catch (error) {
            console.error(error);
        }
    });

    async function trayectos_registrados(periodo_academico, id_trayecto_actual) {
        try {
            const formulario = new FormData();
            formulario.append("periodo_academico", periodo_academico);

            const respuesta = await fetch("/tract_selec_mat/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            if (resultado.estado == "fallo") {
                return;
            }

            // Limpiar opciones anteriores
            select_trayecto_actualizar_materia.innerHTML = `<option value="">Seleccionar Trayecto</option>`;

            resultado.trayectos.forEach(trayecto => {
                const option = document.createElement("option");
                option.value = trayecto.id_trayecto;
                option.textContent = trayecto.nombre;
                // Seleccionar el trayecto actual
                if (Number(trayecto.id_trayecto) === Number(id_trayecto_actual)) {
                    option.selected = true;
                }
                select_trayecto_actualizar_materia.appendChild(option);
            });
        } catch (error) {
            console.error(error);
        }
    }

    async function pnfs_registrados(periodo_academico, id_pnf_actual) {
        try {
            const formulario = new FormData();
            formulario.append("periodo_academico", periodo_academico);

            const respuesta = await fetch("/pnf_selec_mat/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            if (resultado.estado == "fallo") {
                return;
            }

            // Limpiar las opciones anteriores
            select_actualizar_pnf.innerHTML = `<option value="">Seleccionar PNF</option>`;

            resultado.pnfs.forEach(pnf => {
                const option = document.createElement("option");
                option.value = pnf.id_pnf;
                option.textContent = pnf.pnf;

                // Seleccionar el PNF que pertenece a la materia buscada
                if (Number(pnf.id_pnf) === Number(id_pnf_actual)) {
                    option.selected = true;
                }
                select_actualizar_pnf.appendChild(option);
            });
        } catch (error) {
            console.error(error);
        }
    }

    formulario_actualizar.addEventListener("submit", async (e) => {
        e.preventDefault()
        try {
            const formulario = new FormData(formulario_actualizar)
            const respuesta = await fetch("/mat_guardar/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
                },
                body: formulario
            });
            const resultado = await respuesta.json()
            console.log(resultado);

            await Swal.fire({
                text: resultado.descripcion,
                icon: resultado.icon,
                allowOutsideClick: false,
                allowEscapeKey: false
            });

            if (resultado.estado == "exito") {
                formulario_actualizar.reset();
                bloquear_controles(controles, true);
            }
        } catch (error) {
            console.error(error)
        }
    });

    codigos_buscar_materias.addEventListener("input", function () {
        this.value = this.value
            .toUpperCase()
            .replace(/[^A-Z0-9]/g, "")
            .slice(0, 7);
    });
});