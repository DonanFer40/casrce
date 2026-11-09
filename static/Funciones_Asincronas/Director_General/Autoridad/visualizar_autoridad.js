document.addEventListener("DOMContentLoaded", () => {

    const contenedor_autoridades = document.getElementById("contenedor_autoridades");

    const formulario = document.getElementById("formulario_registrar_autoridades");

    const usuario_seleccionado = document.getElementById("usuario_seleccionado");

    const nombres = document.getElementById("nombres_autoridades");
    const apellidos = document.getElementById("apellidos_autoridades");
    const nacionalidad = document.getElementById("nacionalidad");
    const cedula = document.getElementById("cedula_identidad");
    const genero = document.getElementById("genero_autoridades");
    const cargo = document.getElementById("cargo_autoridades");
    const resolucion = document.getElementById("resolucion_autoridades");

    const titulo = document.getElementById("titulo_modo_autoridad");
    const etiqueta = document.getElementById("etiqueta_modo_autoridad");
    const descripcion = document.getElementById("descripcion_modo_autoridad");
    const icono = document.getElementById("icono_modo_autoridad");

    const boton = document.getElementById("btn_registrar");
    const boton_cancelar = document.getElementById("btn_cancelar_modificacion");
    const aviso_modificacion = document.getElementById("aviso_modo_modificacion");


    // =====================================================
    // CARGAR AUTORIDADES
    // =====================================================

    async function obtener_autoridades() {

        try {

            const respuesta = await fetch("/auts_reg/");

            if (!respuesta.ok) {
                throw new Error("No se pudieron obtener las autoridades.");
            }

            const resultado = await respuesta.json();

            contenedor_autoridades.innerHTML = "";

            // =====================================================
            // CUANDO NO EXISTEN AUTORIDADES
            // =====================================================

            if (!resultado.length) {

                const fila = document.createElement("tr");
                const celda = document.createElement("td");

                celda.colSpan = 4;
                celda.textContent = "No hay autoridades registradas.";

                fila.appendChild(celda);
                contenedor_autoridades.appendChild(fila);

                return;
            }

            // =====================================================
            // GENERAR FILAS DE AUTORIDADES
            // =====================================================

            resultado.forEach(autoridad => {

                const fila = document.createElement("tr");

                fila.dataset.id = autoridad.id_autoridad;
                fila.tabIndex = 0;
                fila.setAttribute("role", "button");

                fila.setAttribute(
                    "aria-label",
                    `Modificar autoridad ${autoridad.nombres} ${autoridad.apellidos}`
                );

                const datos = [
                    `${autoridad.nombres || ""} ${autoridad.apellidos || ""}`.trim(),
                    autoridad.cedula_identidad,
                    autoridad.cargo,
                    autoridad.resolucion
                ];

                datos.forEach(valor => {

                    const celda = document.createElement("td");

                    celda.textContent = valor ?? "";

                    fila.appendChild(celda);

                });

                // Seleccionar autoridad
                fila.addEventListener("click", () => {

                    seleccionar_autoridad(autoridad, fila);

                });

                // Permitir selección mediante teclado
                fila.addEventListener("keydown", evento => {

                    if (evento.key === "Enter" || evento.key === " ") {

                        evento.preventDefault();

                        seleccionar_autoridad(autoridad, fila);

                    }

                });

                contenedor_autoridades.appendChild(fila);

            });

        } catch (error) {

            console.error("Error al cargar autoridades:", error);

        }

    }


    // =====================================================
    // SELECCIONAR AUTORIDAD
    // =====================================================

    function seleccionar_autoridad(autoridad, fila) {

        console.log("AUTORIDAD COMPLETA:", autoridad);

        usuario_seleccionado.value = autoridad.id_autoridad;

        // Datos personales
        nombres.value = autoridad.nombres || "";
        apellidos.value = autoridad.apellidos || "";
        const genero_actual = autoridad.genero || "No especificado";

        // Comprobar si existe una opción con ese valor
        let opcion_genero = Array.from(genero.options).find(
            opcion => opcion.value === genero_actual
        );

        // Si no existe, crearla
        if (!opcion_genero) {
            opcion_genero = document.createElement("option");
            opcion_genero.value = genero_actual;
            opcion_genero.textContent = genero_actual;
            genero.appendChild(opcion_genero);
        }

        // Seleccionar el género
        genero.value = genero_actual;

        // =====================================================
        // RECUPERAR NACIONALIDAD Y CÉDULA
        // =====================================================

        nacionalidad.disabled = false;
        cedula.disabled = false;

        nacionalidad.value = autoridad.nacionalidad || "";

        nacionalidad.dispatchEvent(
            new Event("change", { bubbles: true })
        );

        cedula.value = autoridad.cedula_identidad || "";

        nacionalidad.disabled = true;
        cedula.disabled = true;

        // Cargo
        const opcion_existente = Array.from(cargo.options).find(
            opcion => opcion.value === autoridad.cargo
        );

        if (!opcion_existente) {
            const opcion = document.createElement("option");

            opcion.value = autoridad.cargo;
            opcion.textContent = autoridad.cargo;

            cargo.appendChild(opcion);
        }

        cargo.value = autoridad.cargo;

        // Resolución
        resolucion.value = autoridad.resolucion || "";

        // Cambiar formulario a modo modificación
        titulo.textContent = "Modificar Autoridad";
        etiqueta.textContent = "MODIFICACIÓN DE DATOS";
        descripcion.textContent = "Modifica la información de la autoridad seleccionada.";

        icono.innerHTML = '<i class="fa-solid fa-user-pen"></i>';

        boton.innerHTML = `
            <i class="fa-solid fa-floppy-disk"></i>
            <span>Guardar Cambios</span>
        `;

        boton_cancelar.hidden = false;
        aviso_modificacion.hidden = false;

        // Marcar fila seleccionada
        document.querySelectorAll("#contenedor_autoridades tr").forEach(fila => {
            fila.classList.remove("autoridad-seleccionada");
        });

        fila.classList.add("autoridad-seleccionada");

        window.dispatchEvent(
            new CustomEvent("autoridadSeleccionada", {
                detail: autoridad
            })
        );
    }


    // =====================================================
    // CANCELAR MODIFICACIÓN
    // =====================================================

    window.cancelar_modificacion_autoridad = function () {

        formulario.reset();

        usuario_seleccionado.value = "";

        nacionalidad.disabled = false;
        cedula.disabled = false;

        titulo.textContent = "Registrar Autoridad";
        etiqueta.textContent = "NUEVO REGISTRO";

        descripcion.textContent =
            "Completa la información personal y administrativa para registrar una nueva autoridad.";

        icono.innerHTML = '<i class="fa-solid fa-user-plus"></i>';

        boton.innerHTML =
            '<i class="fa-solid fa-user-plus"></i><span>Registrar Autoridad</span>';

        boton_cancelar.hidden = true;
        aviso_modificacion.hidden = true;

        // Limpiar selección visual
        document.querySelectorAll(
            "#contenedor_autoridades tr"
        ).forEach(fila => {

            fila.classList.remove("autoridad-seleccionada");

        });

        // Limpiar mensajes de validación
        document.getElementById("mensaje_cedula_identidad").textContent = "";
        document.getElementById("msg_resolucion").textContent = "";

    };


    // =====================================================
    // EVENTOS
    // =====================================================

    boton_cancelar.addEventListener("click", () => {

        window.cancelar_modificacion_autoridad();

    });


    // Permitir que otros scripts actualicen la tabla
    window.obtener_autoridades = obtener_autoridades;


    // Carga inicial
    obtener_autoridades();

});
