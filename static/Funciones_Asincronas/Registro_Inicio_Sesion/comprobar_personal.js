document.addEventListener("DOMContentLoaded", () => {

    // =========================================================
    // FORMULARIOS
    // =========================================================

    const formulario_buscar_usuario =
        document.getElementById("buscar_usuario");

    const formulario_registrar_credenciales =
        document.getElementById(
            "formulario_registrar_credenciales"
        );


    // =========================================================
    // BLOQUES DE LOS PASOS
    // =========================================================

    const paso_busqueda =
        document.getElementById(
            "RegistroPersonalCASRCE-paso-busqueda"
        );


    // =========================================================
    // CONTROLES DE BÚSQUEDA
    // =========================================================

    const select_nacionalidad =
        document.getElementById("nacionalidad");

    const input_CI =
        document.getElementById("cedula_identidad");

    const btn_buscar_usuario =
        document.getElementById("validar_usuario");


    // =========================================================
    // CONTROLES DE CREDENCIALES
    // =========================================================

    const input_nombre_usuario =
        document.getElementById("nombre_usuario");

    const msg_nombre_usuario =
        document.getElementById("mensaje_nombre_usuario");

    const input_password =
        document.getElementById("password");

    const msg_password =
        document.getElementById("mensaje_password");

    const btn_registro =
        document.getElementById("btn_registro");


    // =========================================================
    // CONTROLES DE CONTRASEÑA
    // =========================================================

    const input_check_oculta_aparecer =
        document.getElementById("OcultaAparecer");

    const tag_i_mostrar =
        document.getElementById("aparecer_oculta");

    const tag_i_ocultar =
        document.getElementById("oculta_aparecer");


    // =========================================================
    // CONFIGURACIÓN DE CÉDULA
    // =========================================================

    configurarCedula(
        select_nacionalidad,
        input_CI
    );


    // =========================================================
    // ESTADO INICIAL
    // =========================================================

    paso_busqueda.hidden = false;

    formulario_registrar_credenciales.hidden = true;


    // =========================================================
    // BUSCAR USUARIO
    // =========================================================

    formulario_buscar_usuario.addEventListener(
        "submit",
        async function (e) {

            e.preventDefault();

            try {

                const datos =
                    new FormData(
                        formulario_buscar_usuario
                    );


                const respuesta =
                    await fetch(
                        "/confirmar_reg/",
                        {
                            method: "POST",
                            body: datos
                        }
                    );


                const resultado =
                    await respuesta.json();


                console.log(resultado);


                // =================================================
                // USUARIO ENCONTRADO
                // =================================================

                if (resultado.estado === "exito") {

                    /*
                     * Ocultamos completamente
                     * el Paso 01.
                     */
                    paso_busqueda.hidden = true;


                    /*
                     * Mostramos completamente
                     * el Paso 02.
                     */
                    formulario_registrar_credenciales.hidden = false;


                    /*
                     * Mensaje de confirmación.
                     */
                    await Swal.fire({

                        title: "Éxito",

                        text: "Se encontraron los datos.",

                        icon: "success",

                        allowOutsideClick: false,

                        allowEscapeKey: false

                    });

                }


                // =================================================
                // USUARIO NO ENCONTRADO
                // =================================================

                else {

                    await Swal.fire({

                        title: resultado.title,

                        text: resultado.descripcion,

                        icon: resultado.icon,

                        allowOutsideClick: false,

                        allowEscapeKey: false

                    });

                }

            }

            catch (error) {

                console.error(error);

            }

        }
    );


    // =========================================================
    // GUARDAR CREDENCIALES
    // =========================================================

    formulario_registrar_credenciales.addEventListener(
        "submit",
        async function (e) {

            e.preventDefault();

            try {

                const datos =
                    new FormData(
                        formulario_registrar_credenciales
                    );


                const respuesta =
                    await fetch(
                        "/guardar_cred/",
                        {
                            method: "POST",
                            body: datos
                        }
                    );


                const resultado =
                    await respuesta.json();


                // =================================================
                // REGISTRO COMPLETADO
                // =================================================

                if (resultado.estado === "exito") {

                    /*
                     * Ocultamos nuevamente
                     * el Paso 02.
                     */
                    formulario_registrar_credenciales.hidden = true;


                    /*
                     * Mostramos nuevamente
                     * el Paso 01.
                     */
                    paso_busqueda.hidden = false;


                    /*
                     * Limpiamos las credenciales.
                     */
                    formulario_registrar_credenciales.reset();
                    input_CI.reset();

                }


                // =================================================
                // MENSAJE DEL SERVIDOR
                // =================================================

                await Swal.fire({

                    title: resultado.title,

                    text: resultado.descripcion,

                    icon: resultado.icon,

                    allowOutsideClick: false,

                    allowEscapeKey: false

                });

            }

            catch (error) {

                console.error(error);

            }

        }
    );

});