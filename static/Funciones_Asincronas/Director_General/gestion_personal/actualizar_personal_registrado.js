document.addEventListener("DOMContentLoaded", () => {

    const formulario_busqueda = document.getElementById("formulario_busqueda");
    const select_nacionalidad = document.getElementById("nacionalidad");
    const input_cedula_identidad = document.getElementById("cedula_identidad");

    const formulario_actualizar = document.getElementById("formulario_actualizar");
    const input_nombres_usuario = document.getElementById("nombres_usuario");
    const input_apellidos_usuario = document.getElementById("apellidos_usuario");
    const input_cedula_usuario = document.getElementById("cedula_usuario");

    const contenedor_perfiles_asignado = document.getElementById("contenedor_perfiles_asignado");
    const contenedor_asignar_perfiles = document.getElementById("contenedor_asignar_perfiles");

    configurarCedula(select_nacionalidad, input_cedula_identidad);

    formulario_busqueda.addEventListener("submit", async (e) => {
        e.preventDefault();
        try {
            const formulario = new FormData(formulario_busqueda);

            const respuesta = await fetch("/bus_per_asig/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            if (resultado.estado == "fallo") {
                await Swal.fire({
                    title: resultado.title,
                    text: resultado.descripcion,
                    icon: resultado.icon,
                    allowOutsideClick: false,
                    allowEscapeKey: false
                });
                return;
            }

            input_nombres_usuario.value = resultado.usuario.nombres;
            input_apellidos_usuario.value = resultado.usuario.apellidos;
            input_cedula_usuario.value = resultado.usuario.cedula;

            mostrar_perfiles_asignados(resultado.perfiles);

            mostrar_perfiles_disponibles(
                resultado.perfiles_disponibles,
                resultado.pnfs_disponibles_docente,
                resultado.pnfs_disponibles_coordinador
            );
        } catch (error) {
            console.error(error);
        }
    });



    function mostrar_perfiles_asignados(perfiles) {

        contenedor_perfiles_asignado.innerHTML = "";

        if (!perfiles || perfiles.length === 0) {

            contenedor_perfiles_asignado.innerHTML = `
        <div class="mensaje_sin_perfiles" >
            <p>El usuario no tiene perfiles asignados.</p>
            </div >
        `;

            return;
        }


        perfiles.forEach(perfil => {

            const contenedor = document.createElement("div");

            contenedor.classList.add("perfil_asignado");


            const esActivo = perfil.activo === true;


            contenedor.innerHTML = `

        <div class="campo_perfil" >

                <label>Perfil</label>

                <input
                    type="text"
                    value="${perfil.rol}"
                    readonly
                >

            </div>


            <div class="campo_perfil">

                <label>P.N.F</label>

                <input
                    type="text"
                    value="${perfil.pnf}"
                    readonly
                >

            </div>


            <div class="campo_perfil">

                <label>Núcleo</label>

                <input
                    type="text"
                    value="${perfil.nucleo}"
                    readonly
                >

            </div>


            <div class="campo_perfil">

                <label>Estado</label>

                <div class="contenedor_estado_perfil">

                    <label class="switch_estado_perfil">

                        <input
                            type="checkbox"
                            class="checkbox_estado_perfil"

                            name="perfiles_estado"

                            value="${perfil.id_perfil}"

                            ${esActivo ? "checked" : ""}

                            data-tipo="${perfil.tipo}"

                            data-id="${perfil.id_perfil}"
                        >

                        <span class="slider_estado_perfil"></span>

                    </label>


                    <span class="texto_estado_perfil">

                        ${esActivo
                    ? "ACTIVO"
                    : "INHABILITADO"}

                    </span>

                </div>

            </div>

    `;


            contenedor_perfiles_asignado.appendChild(
                contenedor
            );

        });
    }

    contenedor_perfiles_asignado.addEventListener(
        "change",
        async (e) => {

            const checkbox = e.target.closest(
                ".checkbox_estado_perfil"
            );

            if (!checkbox) {
                return;
            }


            const activo = checkbox.checked;

            const contenedor_estado =
                checkbox.closest(".contenedor_estado_perfil");

            const texto_estado =
                contenedor_estado.querySelector(
                    ".texto_estado_perfil"
                );


            texto_estado.textContent = activo
                ? "ACTIVO"
                : "INHABILITADO";


            console.log({
                id_perfil: checkbox.dataset.id,
                tipo: checkbox.dataset.tipo,
                activo: activo
            });

        }
    );

    function mostrar_perfiles_disponibles(perfiles, pnfs_docente, pnfs_coordinador) {

        contenedor_asignar_perfiles.innerHTML = "";

        if (!perfiles || perfiles.length === 0) {
            contenedor_asignar_perfiles.innerHTML = `
            <div class="mensaje_sin_perfiles">
                <p>
                    El usuario no tiene perfiles disponibles para asignar.
                </p>
            </div>
        `;
            return;
        }


        perfiles.forEach(perfil => {
            const contenedor = document.createElement("div");

            contenedor.classList.add("perfil_disponible");

            // DOCENTE
            if (perfil.tipo === "docente") {
                let opciones_pnf = "";

                if (pnfs_docente && pnfs_docente.length > 0) {
                    pnfs_docente.forEach(pnf => {
                        opciones_pnf += `
                        <label class="checkbox_pnf">

                            <input
                                type="checkbox"
                                name="pnfs_docente"
                                value="${pnf.id_pnf}"
                                data-pnf="${pnf.pnf}">
                            <span>${pnf.pnf} (${pnf.codigo})</span>
                        </label>
                    `;
                    });
                } else {

                    opciones_pnf = `
                    <p class="mensaje_sin_pnf">
                        No existen P.N.F disponibles para asignar.
                    </p>
                `;
                }


                contenedor.innerHTML = `
                <div class="campo_perfil">
                    <label>Perfil disponible</label>
                    <input
                        type="text"
                        value="${perfil.rol}"
                        readonly>
                </div>
                <div class="contenedor_pnfs_disponibles">
                    <label class="titulo_pnf">
                        Seleccionar P.N.F
                    </label>
                    <div class="lista_checkbox_pnf">
                        ${opciones_pnf}
                    </div>
                </div>
            `;
            }

            // COORDINADOR PNF
            else if (perfil.tipo === "coordinador_pnf") {
                let opciones_pnf = "";


                if (pnfs_coordinador && pnfs_coordinador.length > 0) {
                    pnfs_coordinador.forEach(pnf => {
                        opciones_pnf += `
                        <label class="checkbox_pnf">

                            <input
                                type="radio"
                                name="pnf_coordinador"
                                value="${pnf.id_pnf}"
                                data-pnf="${pnf.pnf}">

                            <span>${pnf.pnf} (${pnf.codigo})</span>
                        </label>
                    `;
                    });
                } else {

                    opciones_pnf = `
                    <p class="mensaje_sin_pnf">
                        No existen P.N.F disponibles para asignar.
                    </p>
                `;

                }

                contenedor.innerHTML = `
                <div class="campo_perfil">
                    <label>Perfil disponible</label>
                    <input
                        type="text"
                        value="${perfil.rol}"
                        readonly>
                </div>
                <div class="contenedor_pnfs_disponibles">
                    <label class="titulo_pnf">
                        Seleccionar P.N.F
                    </label>
                    <div class="lista_checkbox_pnf">
                        ${opciones_pnf}
                    </div>
                </div>
            `;
            }

            // CONTROL DE ESTUDIO
            else if (perfil.tipo === "control_estudio") {
                contenedor.innerHTML = `
                <div class="campo_perfil">
                    <label>Perfil disponible</label>
                    <div class="seleccionar_perfil">
                        <input
                            type="checkbox"
                            class="checkbox_perfil"
                            name="perfil_disponible"
                            value="control_estudio"
                            data-tipo="control_estudio">
                        <span>${perfil.rol}</span>
                    </div>
                </div>
            `;
            }
            contenedor_asignar_perfiles.appendChild(contenedor);
        });
    }

    formulario_actualizar.addEventListener("submit", async (e) => {
        e.preventDefault();

        try {
            const formulario = new FormData(formulario_actualizar);

            const respuesta = await fetch("/act_per_asig/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            await Swal.fire({
                title: resultado.title,
                text: resultado.descripcion,
                icon: resultado.icon,
                allowOutsideClick: false,
                allowEscapeKey: false
            });

            // ACTUALIZACIÓN EXITOSA
            if (resultado.estado === "exito") {
                // Limpiar todos los campos del formulario
                formulario_actualizar.reset();

                // Limpiar información del usuario encontrado
                input_nombres_usuario.value = "";
                input_apellidos_usuario.value = "";
                input_cedula_usuario.value = "";

                contenedor_perfiles_asignado.innerHTML = ""; // Limpiar perfiles asignados
                contenedor_asignar_perfiles.innerHTML = ""; // Limpiar perfiles disponibles

                // Opcional: mostrar nuevamente el mensaje inicial
                contenedor_perfiles_asignado.innerHTML = `
                    <div class="mensaje_sin_perfiles" >
                        <p>Busque un usuario para visualizar sus perfiles.</p>
                    </div>
                `;

                contenedor_asignar_perfiles.innerHTML = `
                    <div class="mensaje_sin_perfiles" >
                        <p>Busque un usuario para visualizar los perfiles disponibles.</p>
                    </div>
                `;
            }
        } catch (error) {
            console.error(error);
        }
    });

});