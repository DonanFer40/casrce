document.addEventListener("DOMContentLoaded", () => {

    const select_nucleo_asignado = document.getElementById("nucleo_asignado");
    const select_pnf_asignado = document.getElementById("pnf_asignado");
    const select_materia_asignada = document.getElementById("materia_asignada");
    const input_trayecto_academico = document.getElementById("trayecto_academico");

    const formulario_registrar = document.getElementById("formulario_registrar");

    const contenedor = document.getElementById('contenedor_detalles_evaluacion');
    const btnAgregar = document.getElementById('btn_agregar_detalle');

    let pnf = "", nucleo = "";

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

            select_pnf_asignado.innerHTML = "<option value='' selected>Selecciona el núcleo primero</option>";

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
    });

    async function pnfs_asignados() {
        try {
            if (!nucleo) return;

            const formulario = new FormData();
            formulario.append("nucleo_asignado", nucleo);

            const respuesta = await fetch("/notas_academicas/pnfs_asig_doc/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            select_pnf_asignado.innerHTML = "<option value='' selected>Selecciona un P.N.F</option>";

            resultado.datos.forEach(pnf => {
                const option_pnf = document.createElement("option");
                option_pnf.value = pnf.id_pnf;
                option_pnf.textContent = pnf.pnf;
                select_pnf_asignado.append(option_pnf);
            });
        } catch (error) {
            console.error(error);
        }
    }

    select_pnf_asignado.addEventListener("change", async (e) => {
        pnf = select_pnf_asignado.value;

        await materias_reparacion();
    });

    async function materias_reparacion() {
        try {
            if (!nucleo || !pnf) return;

            const formulario = new FormData();
            formulario.append("id_nucleo", nucleo);
            formulario.append("id_pnf", pnf);

            const respuesta = await fetch("/notas_academicas/mat_rep_not/", {
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

        const trayecto = opcion.dataset.trayecto;
        input_trayecto_academico.value = trayecto;
        input_trayecto_academico.dataset.id_trayecto = opcion.dataset.id_trayecto;
    });

    formulario_registrar.addEventListener("submit", async (e) => {
        e.preventDefault();
        try {
            const formulario = new FormData(formulario_registrar);

            const respuesta = await fetch("/notas_academicas/reg_eval_rep/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": obtener_csrf_token()
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            await Swal.fire({
                text: resultado.descripcion,
                icon: resultado.icon,
                title: resultado.title,
                allowOutsideClick: false,
                allowEscapeKey: false
            });

            if (resultado.estado == "exito") {
                formulario_registrar.reset();

                limpiarContenedoresEvaluacion();
            }
        } catch (error) {
            console.error(error);
        }
    });

    function limpiarContenedoresEvaluacion() {


        // Limpiar contenedor dinámico
        contenedor.innerHTML = "";


        // Crear nuevamente el primer control vacío
        const div = document.createElement("div");

        div.className = "detalle_evaluacion";


        div.innerHTML = `

        <label>Tipo de Evaluación:</label>

        <select 
            name="tipo_evaluacion[]" 
            class="tipo_evaluacion">
        </select>


        <label>Porcentaje:</label>

        <input 
            type="text"
            name="porcentaje[]"
            class="porcentaje_evaluacion"
            value="100"
            readonly>


        <button 
            type="button" 
            class="btn_eliminar_detalle">
            Eliminar
        </button>

    `;


        contenedor.appendChild(div);



        // Cargar opciones del select nuevamente
        const select = div.querySelector(".tipo_evaluacion");

        poblarSelect(select);



        // Actualizar controles
        actualizarOpcionesSelects();

        recalcularPorcentajes();

        verificarLimiteBoton();

    }

    const tipos_evaluacion = [
        ["EXAMEN", "Examen"],
        ["INFORME", "Informe"],
        ["PROYECTO", "Proyecto"],
        ["EXPOSICION", "Exposición"],
        ["PRACTICA", "Práctica"],
        ["CUESTIONARIO", "Cuestionario"],
        ["PROGRAMACION", "Desarrollo de Programa"],
        ["DIAGRAMA_FLUJO", "Diagrama de Flujo"]
    ];

    const LIMITE_MAXIMO = 3;

    const primerSelect = contenedor.querySelector('.tipo_evaluacion');
    poblarSelect(primerSelect);
    actualizarReglasPorcentajes();

    btnAgregar.addEventListener('click', () => {
        const totalDetalles = contenedor.querySelectorAll('.detalle_evaluacion').length;

        if (totalDetalles >= LIMITE_MAXIMO) return;

        const nuevoDetalle = document.createElement('div');
        nuevoDetalle.className = 'detalle_evaluacion';
        nuevoDetalle.innerHTML = `
            <label>Tipo de Evaluación:</label>
            <select name="tipo_evaluacion[]" class="tipo_evaluacion"></select>

            <label>Porcentaje:</label>
            <input type="text" name="porcentaje[]" class="porcentaje_evaluacion" placeholder="Porcentaje">

            <button type="button" class="btn_eliminar_detalle">Eliminar</button>
        `;

        contenedor.appendChild(nuevoDetalle);

        poblarSelect(nuevoDetalle.querySelector('.tipo_evaluacion'));

        actualizarOpcionesSelects();
        recalcularPorcentajes();
        verificarLimiteBoton();
    });

    contenedor.addEventListener('change', (e) => {
        if (e.target.classList.contains('tipo_evaluacion')) {
            actualizarOpcionesSelects();
        }
    });

    contenedor.addEventListener('click', (e) => {
        if (e.target.classList.contains('btn_eliminar_detalle')) {
            const filas = contenedor.querySelectorAll('.detalle_evaluacion');
            if (filas.length > 1) {

                e.target.closest('.detalle_evaluacion').remove();

                actualizarOpcionesSelects();
                recalcularPorcentajes();
                verificarLimiteBoton();
            }
        }
    });

    contenedor.addEventListener('input', (e) => {

        if (e.target.classList.contains('porcentaje_evaluacion')) {

            let input = e.target;

            // Solo números
            input.value = input.value.replace(/[^0-9]/g, '');

            // quitar ceros iniciales
            input.value = input.value.replace(/^0+/, '');


            // Si está vacío no hacer nada mientras escribe
            if (input.value === "") {
                return;
            }


            let valor = parseInt(input.value, 10);


            // máximo permitido
            if (valor > 100) {
                input.value = 100;
            }


            // Solo ajustar cuando tenga 2 o más dígitos
            // evita bloquear 18,25,35...
            if (input.value.length >= 2) {

                if (valor < 10) {
                    input.value = 10;
                }

                const inputs = Array.from(
                    contenedor.querySelectorAll('.porcentaje_evaluacion')
                );


                if (inputs.length > 1) {

                    const otros = inputs.filter(
                        i => i !== input
                    );

                    balancearCamposRestantes(
                        input,
                        otros,
                        parseInt(input.value, 10)
                    );
                }
            }
        }

    });

    contenedor.addEventListener('focusout', (e) => {

        if (e.target.classList.contains('porcentaje_evaluacion')) {

            let input = e.target;

            let valor = parseInt(input.value, 10);


            if (isNaN(valor) || valor < 10) {

                input.value = 10;

            }


            const inputs = Array.from(
                contenedor.querySelectorAll('.porcentaje_evaluacion')
            );


            let suma = inputs.reduce(
                (total, i) => total + (parseInt(i.value, 10) || 0),
                0
            );


            if (suma !== 100) {

                const otros = inputs.filter(
                    i => i !== input
                );

                balancearCamposRestantes(
                    input,
                    otros,
                    parseInt(input.value, 10)
                );
            }

        }

    });

    function balancearCamposRestantes(inputEditado, otrosInputs, valorActual) {

        let restante = 100 - valorActual;


        if (otrosInputs.length === 1) {

            // Dos evaluaciones
            otrosInputs[0].value = restante;

        } else if (otrosInputs.length === 2) {

            // Tres evaluaciones

            let valor1 = parseInt(otrosInputs[0].value, 10) || 10;
            let valor2 = parseInt(otrosInputs[1].value, 10) || 10;


            let suma = valor1 + valor2;


            if (suma > 0) {

                let nuevo1 = Math.round(
                    restante * (valor1 / suma)
                );


                // Mantener mínimo 10
                if (nuevo1 < 10) {
                    nuevo1 = 10;
                }


                let nuevo2 = restante - nuevo1;


                if (nuevo2 < 10) {
                    nuevo2 = 10;
                    nuevo1 = restante - nuevo2;
                }


                otrosInputs[0].value = nuevo1;
                otrosInputs[1].value = nuevo2;

            } else {

                otrosInputs[0].value = 50;
                otrosInputs[1].value = 50;

            }

        }

    }

    function poblarSelect(selectElement) {
        selectElement.innerHTML = '<option value="">Seleccione tipo</option>';
        tipos_evaluacion.forEach(([valor, texto]) => {
            const option = document.createElement('option');
            option.value = valor;
            option.textContent = texto;
            selectElement.appendChild(option);
        });
    }

    function actualizarOpcionesSelects() {
        const todosLosSelects = Array.from(contenedor.querySelectorAll('.tipo_evaluacion'));
        const valoresSeleccionados = todosLosSelects
            .map(s => s.value)
            .filter(v => v !== '');

        todosLosSelects.forEach(selectActual => {
            const valorActual = selectActual.value;

            Array.from(selectActual.options).forEach(option => {
                if (option.value === '') return;

                if (valoresSeleccionados.includes(option.value) && option.value !== valorActual) {
                    option.style.display = 'none';
                    option.disabled = true;
                } else {
                    option.style.display = '';
                    option.disabled = false;
                }
            });
        });
    }

    function actualizarReglasPorcentajes() {
        const inputs = contenedor.querySelectorAll('.porcentaje_evaluacion');

        if (inputs.length === 1) {
            inputs[0].value = 100;
            inputs[0].readOnly = true;
        } else {
            inputs.forEach(input => {
                input.readOnly = false;
            });

            if (inputs.length === 2 && (inputs[0].value === '100' || inputs[0].value === '')) {
                inputs[0].value = 50;
                inputs[1].value = 50;
            } else if (inputs.length === 3) {
                // Si se agrega la tercera fila, divide por defecto aproximadamente (34, 33, 33)
                if (inputs[2].value === '') {
                    inputs[0].value = 34;
                    inputs[1].value = 33;
                    inputs[2].value = 33;
                }
            }
        }
    }

    function verificarLimiteBoton() {
        const total = contenedor.querySelectorAll('.detalle_evaluacion').length;
        if (total >= LIMITE_MAXIMO) {
            btnAgregar.style.display = 'none';
        } else {
            btnAgregar.style.display = 'block';
        }
    }

    function validarPorcentajes() {

        const inputs = Array.from(
            contenedor.querySelectorAll('.porcentaje_evaluacion')
        );


        let suma = 0;


        for (let input of inputs) {

            let valor = parseInt(input.value, 10);


            if (isNaN(valor)) {
                alert("Todos los porcentajes deben estar completos.");
                return false;
            }


            if (valor < 10) {
                alert("Cada porcentaje debe ser mínimo 10%.");
                return false;
            }


            suma += valor;
        }


        if (suma !== 100) {
            alert("La suma de los porcentajes debe ser 100%.");
            return false;
        }


        return true;
    }
    validarPorcentajes();

    function recalcularPorcentajes() {


        const inputs = Array.from(
            contenedor.querySelectorAll(".porcentaje_evaluacion")
        );


        if (inputs.length === 0) {
            return;
        }



        if (inputs.length === 1) {

            inputs[0].value = 100;
            inputs[0].readOnly = true;

            return;

        }



        inputs.forEach(input => {

            input.readOnly = false;

        });



        if (inputs.length === 2) {

            inputs[0].value = 50;
            inputs[1].value = 50;

        }



        if (inputs.length === 3) {

            inputs[0].value = 34;
            inputs[1].value = 33;
            inputs[2].value = 33;

        }

    }
    recalcularPorcentajes()
});