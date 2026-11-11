document.addEventListener("DOMContentLoaded", () => {

    const btn_discapacidad = document.getElementById("btn_discapacidad");
    const campos_discapacidad = document.getElementById("campos_discapacidad");

    const formulario_registro = document.getElementById("formulario_registro");

    // Campos registrado por el director general
    const nombres_usuario = document.getElementById("nombres_usuario");
    const apellidos_usuario = document.getElementById("apellidos_usuario");
    const CI_usuario = document.getElementById("CI");
    const genero_usuario = document.getElementById("genero_usuario");
    const estado_civil_usuario = document.getElementById("estado_civil_usuario");

    // Campos que puede ser que el director lo regitra o no del usuario
    const prefijo_principal = document.getElementById("prefijo_principal");
    const numero_telefonico_principal = document.getElementById("numero_telefonico_principal");

    const correo_principal = document.getElementById("correo_principal");
    const dominio_principal = document.getElementById("dominio_principal");

    const pais_profesion = document.getElementById("pais_profesion");

    const genero = ["Masculino", "Femenino"];
    const estado_civil = ["Soltero(a)", "Casado(a)", "Divorsiado(a)", "Viudo(a)"];

    // Controles para validar
    const nacionalidad_auxiliar = document.getElementById("nacionalidad_auxiliar");
    const cedula_auxiliar = document.getElementById("cedula_auxiliar");

    const prefijo_secundario = document.getElementById("prefijo_secundario");
    const numero_telefonico_secundario = document.getElementById("numero_telefonico_secundario");

    const prefijo_telefono_auxiliar = document.getElementById("prefijo_telefono_auxiliar");
    const numero_telefono_auxiliar = document.getElementById("numero_telefono_auxiliar");

    const correo_secundario = document.getElementById("correo_secundario");
    const dominio_secundario = document.getElementById("dominio_secundario");

    const fecha_grado = document.getElementById("fecha_grado");
    const codigo_sin_opsu = document.getElementById("codigo_sin_opsu");

    const nucleos = document.querySelectorAll(
        "#contenedor_pnfs_cursar input[type='radio'][name='nucleo_seleccionado']"
    );

    // Mensaje de validar
    const msg_ced_aux = document.getElementById("msg_ced_aux");
    const msg_correo_princ = document.getElementById("msg_correo_princ");
    const msg_correo_sec = document.getElementById("msg_correo_sec");
    const msg_codigo_opsu = document.getElementById("msg_codigo_opsu");

    function opciones_select() {
        genero_usuario.innerHTML = "<option value='' selected>Selecciona una opción</option>";

        genero.forEach(genero => {
            const option = document.createElement("option");
            option.value = genero;
            option.textContent = genero;
            genero_usuario.append(option);
        });

        estado_civil_usuario.innerHTML = "<option value='' selected>Selecciona una opción</option>";

        estado_civil.forEach(estado_civil => {
            const option = document.createElement("option");
            option.value = estado_civil;
            option.textContent = estado_civil;
            estado_civil_usuario.append(option);
        });
    }
    opciones_select();

    async function datos_registrado() {
        try {
            const respuesta = await fetch("/datos_usr_admin/");
            const resultado = await respuesta.json();
            console.log(resultado);

            if (resultado.estado == "no_exite") {
                await NotificacionesCASRCE.mostrar({
                    title: resultado.title,
                    text: resultado.descripcion,
                    icon: resultado.icon,
                    allowOutsideClick: false,
                    allowEscapeKey: false
                });
                window.CASRCE_TAB_NAVIGATE(resultado.url);
            }

            nombres_usuario.value = resultado.usuario.nombres;
            apellidos_usuario.value = resultado.usuario.apellidos;
            CI_usuario.value = resultado.usuario.cedula_identidad;

            if (resultado.usuario.genero) {
                genero_usuario.classList.add("no-interaccion");

                const option_genero = document.createElement("option");
                option_genero.value = resultado.usuario.genero;
                option_genero.textContent = resultado.usuario.genero;
                option_genero.selected = true;
                option_genero.hidden = true;
                genero_usuario.append(option_genero);
            } else {
                genero_usuario.classList.remove("no-interaccion");
            }

            if (resultado.usuario.estado_civil) {
                estado_civil_usuario.classList.add("no-interaccion");

                const option_civil = document.createElement("option");
                option_civil.value = resultado.usuario.estado_civil;
                option_civil.textContent = resultado.usuario.estado_civil;
                option_civil.selected = true;
                option_civil.hidden = true;
                estado_civil_usuario.append(option_civil);
            } else {
                estado_civil_usuario.classList.remove("no-interaccion");
            }

            if (resultado.contacto.telefono_personal) {
                prefijo_principal.classList.add("no-interaccion");
                numero_telefonico_principal.readOnly = true;

                const prefijo_registrado = resultado.contacto.telefono_personal.slice(0, 4);
                const numero_telefonico = resultado.contacto.telefono_personal.slice(4, 11);

                const prefijo = document.createElement("option");
                prefijo.value = prefijo_registrado;
                prefijo.textContent = prefijo_registrado;
                prefijo.selected = true;
                prefijo.hidden = true;
                prefijo_principal.append(prefijo);

                numero_telefonico_principal.value = numero_telefonico;
            } else {
                numero_telefonico_principal.readOnly = false;
                prefijo_principal.classList.remove("no-interaccion");
            }

            if (resultado.contacto.correo_electronico) {
                correo_principal.readOnly = true;
                dominio_principal.classList.add("no-interaccion");

                const [nombre_correo, dominio_correo] = resultado.contacto.correo_electronico.split("@");

                correo_principal.value = nombre_correo;

                const dominio = document.createElement("option");
                dominio.value = "@" + dominio_correo;
                dominio.textContent = "@" + dominio_correo;
                dominio.selected = true;
                dominio.hidden = true;
                dominio_principal.append(dominio);
            } else {
                correo_principal.readOnly = false;
                dominio_principal.classList.remove("no-interaccion");
            }

        } catch (error) {
            console.error(error);
        }
    }
    datos_registrado();

    // Función para validar los controles
    if (nacionalidad_auxiliar && cedula_auxiliar && fecha_grado) {
        configurarCedula(nacionalidad_auxiliar, cedula_auxiliar);
        configurarFechaGrado(fecha_grado, 1);
    }

    configurarCorreo(correo_principal, dominio_principal);
    configurarCorreo(correo_secundario, dominio_secundario);

    configurarTelefono(numero_telefonico_principal, prefijo_principal);
    configurarTelefono(numero_telefonico_secundario, prefijo_secundario);

    if (prefijo_telefono_auxiliar && numero_telefono_auxiliar) {
        configurarTelefono(numero_telefono_auxiliar, prefijo_telefono_auxiliar);
    }

    if (pais_profesion) {
        cargarPaises(pais_profesion);
    }

    async function validar_cedula_auxiliar(nacionalidad_auxiliar, cedula_auxiliar, msg) {

        if (!nacionalidad_auxiliar.value || !cedula_auxiliar.value.trim()) {
            msg.textContent = "";
            msg.classList.remove("exito", "error");

            cedula_auxiliar.setCustomValidity("");
            cedula_auxiliar.classList.remove("is-valid", "is-invalid");

            return;
        }

        let longitudMinima;
        let longitudMaxima;

        switch (nacionalidad_auxiliar.value) {
            case "V":
                longitudMinima = 7;
                longitudMaxima = 8;
                break;

            case "E":
                longitudMinima = 8;
                longitudMaxima = 10;
                break;

            default:
                return;
        }

        const cedula = cedula_auxiliar.value.trim();

        if (cedula.length < longitudMinima || cedula.length > longitudMaxima) {

            msg.textContent = "";
            msg.classList.remove("exito", "error");

            cedula_auxiliar.setCustomValidity(
                `La cédula debe tener entre ${longitudMinima} y ${longitudMaxima} números.`
            );

            cedula_auxiliar.classList.remove("is-valid");
            cedula_auxiliar.classList.add("is-invalid");

            return;
        }

        try {
            const formulario = new FormData();

            formulario.append(
                "nacionalidad",
                nacionalidad_auxiliar.value
            );

            formulario.append(
                "cedula",
                cedula
            );

            const respuesta = await fetch("/validar_ci_auxiliar/", {
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

            if (resultado.existe) {

                cedula_auxiliar.setCustomValidity(
                    "Ya se encuentra la cédula de identidad registrada."
                );

                cedula_auxiliar.classList.add("is-invalid");
                cedula_auxiliar.classList.remove("is-valid");

                msg.textContent =
                    "Ya se encuentra la cédula de identidad registrada.";

                msg.classList.add("error");
                msg.classList.remove("exito");

            } else {

                cedula_auxiliar.setCustomValidity("");

                cedula_auxiliar.classList.add("is-valid");
                cedula_auxiliar.classList.remove("is-invalid");

                msg.textContent =
                    "Cédula de Identidad disponible.";

                msg.classList.add("exito");
                msg.classList.remove("error");
            }

        } catch (error) {
            console.error("Error al validar la cédula del auxiliar:", error);
        }
    }

    function limpiarMensajeCedula() {
        if (msg_ced_aux) {
            msg_ced_aux.textContent = "";
            msg_ced_aux.className = "";
            cedula_auxiliar.style.border = "#000";
        }
    }

    if (cedula_auxiliar) {
        cedula_auxiliar.addEventListener("input", async () => {

            const nacionalidad = nacionalidad_auxiliar.value;
            const cedula = cedula_auxiliar.value.trim();

            if (!nacionalidad || !cedula) {
                limpiarMensajeCedula();
                return;
            }

            await validar_cedula_auxiliar(
                nacionalidad_auxiliar,
                cedula_auxiliar,
                msg_ced_aux
            );
        });
    }

    if (nacionalidad_auxiliar) {
        nacionalidad_auxiliar.addEventListener("change", async () => {

            const nacionalidad = nacionalidad_auxiliar.value;
            const cedula = cedula_auxiliar.value.trim();

            if (!nacionalidad || !cedula) {
                limpiarMensajeCedula();
                return;
            }

            await validar_cedula_auxiliar(
                nacionalidad_auxiliar,
                cedula_auxiliar,
                msg_ced_aux
            );
        });
    }

    let controlador_correo_principal = null;
    let controlador_correo_secundario = null;

    async function validar_correos(correo, dominio, msg, tipo) {
        const valorCorreo = correo.value.trim();
        const valorDominio = dominio.value;

        let controlador;

        if (tipo === "principal") {
            if (controlador_correo_principal) {
                controlador_correo_principal.abort();
            }

            controlador_correo_principal = new AbortController();
            controlador = controlador_correo_principal;

        } else {
            if (controlador_correo_secundario) {
                controlador_correo_secundario.abort();
            }

            controlador_correo_secundario = new AbortController();
            controlador = controlador_correo_secundario;
        }

        if (!valorDominio || !valorCorreo) {
            msg.textContent = "";
            msg.classList.remove("exito", "error");

            correo.setCustomValidity("");
            correo.classList.remove("is-valid", "is-invalid");

            return;
        }

        try {
            const formulario = new FormData();

            formulario.append("correo", valorCorreo);
            formulario.append("dominio", valorDominio);

            const respuesta = await fetch("/validar_email/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector(
                        "[name=csrfmiddlewaretoken]"
                    ).value
                },
                body: formulario,
                signal: controlador.signal
            });

            const resultado = await respuesta.json();

            console.log(resultado);

            // Verificar que los valores sigan siendo los mismos
            if (
                correo.value.trim() !== valorCorreo ||
                dominio.value !== valorDominio
            ) {
                return;
            }

            if (resultado.existe) {

                correo.setCustomValidity(
                    "Ya existe un usuario con este correo electrónico."
                );

                correo.classList.add("is-invalid");
                correo.classList.remove("is-valid");

                msg.textContent =
                    "Ya existe un usuario con este correo electrónico.";

                msg.classList.add("error");
                msg.classList.remove("exito");

            } else {

                correo.setCustomValidity("");

                correo.classList.add("is-valid");
                correo.classList.remove("is-invalid");

                msg.textContent =
                    "El correo electrónico está disponible.";

                msg.classList.add("exito");
                msg.classList.remove("error");
            }

        } catch (error) {

            if (error.name === "AbortError") {
                return;
            }

            console.error(
                "Error al validar el correo electrónico:",
                error
            );
        }
    }

    correo_secundario.addEventListener("input", async () => {
        await validar_correos(
            correo_secundario,
            dominio_secundario,
            msg_correo_sec,
            "secundario"
        );
    });

    dominio_secundario.addEventListener("change", async () => {
        await validar_correos(
            correo_secundario,
            dominio_secundario,
            msg_correo_sec,
            "secundario"
        );
    });

    correo_principal.addEventListener("input", async () => {
        await validar_correos(
            correo_principal,
            dominio_principal,
            msg_correo_princ,
            "principal"
        );
    });

    dominio_principal.addEventListener("change", async () => {
        await validar_correos(
            correo_principal,
            dominio_principal,
            msg_correo_princ,
            "principal"
        );
    });

    let controlador_codigo_opsu = null;

    async function codigo_opsu() {
        const valorCodigo = codigo_sin_opsu.value.trim();

        if (controlador_codigo_opsu) {
            controlador_codigo_opsu.abort();
        }

        if (!valorCodigo) {
            msg_codigo_opsu.textContent = "";
            msg_codigo_opsu.classList.remove("exito", "error");

            codigo_sin_opsu.setCustomValidity("");
            codigo_sin_opsu.classList.remove("is-valid", "is-invalid");

            return;
        }

        controlador_codigo_opsu = new AbortController();

        try {
            const formulario = new FormData();

            formulario.append("codigo", valorCodigo);

            const respuesta = await fetch("/validar_cod_opsu/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector(
                        "[name=csrfmiddlewaretoken]"
                    ).value
                },
                body: formulario,
                signal: controlador_codigo_opsu.signal
            });

            const resultado = await respuesta.json();

            console.log(resultado);

            // Comprobar que el código siga siendo el mismo
            if (codigo_sin_opsu.value.trim() !== valorCodigo) {
                return;
            }

            if (resultado.existe) {

                codigo_sin_opsu.setCustomValidity(
                    "Ya se encuentra un estudiante con el mismo código OPSU."
                );

                codigo_sin_opsu.classList.add("is-invalid");
                codigo_sin_opsu.classList.remove("is-valid");

                msg_codigo_opsu.textContent =
                    "Ya se encuentra un estudiante con el mismo código OPSU.";

                msg_codigo_opsu.classList.add("error");
                msg_codigo_opsu.classList.remove("exito");

            } else {

                codigo_sin_opsu.setCustomValidity("");

                codigo_sin_opsu.classList.add("is-valid");
                codigo_sin_opsu.classList.remove("is-invalid");

                msg_codigo_opsu.textContent =
                    "Código OPSU se encuentra disponible.";

                msg_codigo_opsu.classList.add("exito");
                msg_codigo_opsu.classList.remove("error");
            }

        } catch (error) {

            if (error.name === "AbortError") {
                return;
            }

            console.error(
                "Error al validar el código OPSU:",
                error
            );
        }
    }

    if (codigo_sin_opsu) {

        codigo_sin_opsu.addEventListener("input", async () => {
            await codigo_opsu();
        });

        codigo_sin_opsu.addEventListener("keypress", function (e) {
            if (!/[0-9]/.test(e.key)) {
                e.preventDefault();
            }
        });
    }

    formulario_registro.addEventListener("submit", async (e) => {
        e.preventDefault();
        try {
            const formulario = new FormData(formulario_registro);

            const respuesta = await fetch("/comp_registro/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
                },
                body: formulario
            });
            const resultado = await respuesta.json();
            console.log(resultado);

            await NotificacionesCASRCE.mostrar({
                title: resultado.title,
                text: resultado.descripcion,
                icon: resultado.icon,
                allowOutsideClick: false,
                allowEscapeKey: false
            });

            if (resultado.estado == "exito") {
                window.CASRCE_TAB_NAVIGATE(resultado.url);
            }
        } catch (error) {
            console.error(error);
        }
    });

    if (btn_discapacidad && campos_discapacidad) {

        btn_discapacidad.addEventListener("click", () => {

            campos_discapacidad.classList.toggle("activo");

            if (campos_discapacidad.classList.contains("activo")) {
                btn_discapacidad.textContent = "Ocultar";
            } else {
                btn_discapacidad.textContent = "Mostrar";
            }

        });
    }

    nucleos.forEach(nucleo => {

        nucleo.addEventListener("change", async function () {

            if (!this.checked) return;

            // Limpiar los PNF de los demás núcleos.
            nucleos.forEach(otroNucleo => {

                if (otroNucleo === this) return;

                const otroContenedor = document.getElementById(
                    `contenedor_pnfs_${otroNucleo.value}`
                );

                if (otroContenedor) {
                    otroContenedor.innerHTML = "";
                }

            });

            // Cargar los PNF del núcleo seleccionado.
            await cursarpnfs(this.value);
        });
    });

    function obtenerIconoPNF(nombre) {
        const texto = String(nombre || "").toLowerCase();
        if (/sistema|informática|informatica|computación|computacion|software/.test(texto)) return "fa-laptop-code";
        if (/electr[oó]nica|electricidad|eléctric|electric/.test(texto)) return "fa-bolt";
        if (/veterinaria|animal/.test(texto)) return "fa-paw";
        if (/agroaliment|agronom|agro/.test(texto)) return "fa-leaf";
        if (/construcci[oó]n|civil|edificaci/.test(texto)) return "fa-hard-hat";
        if (/mec[aá]nica|mecanic/.test(texto)) return "fa-gears";
        if (/industrial|industria/.test(texto)) return "fa-industry";
        if (/administraci[oó]n|gesti[oó]n/.test(texto)) return "fa-briefcase";
        if (/contadur[ií]a|contable/.test(texto)) return "fa-calculator";
        if (/turismo|hotel/.test(texto)) return "fa-hotel";
        return "fa-graduation-cap";
    }

    async function cursarpnfs(nucleo) {

        const contenedor = document.getElementById(
            `contenedor_pnfs_${nucleo}`
        );

        if (!contenedor) {
            console.error(`No se encontró el contenedor de PNF para ${nucleo}.`);
            return;
        }

        try {

            // Indicar que los PNF se están cargando.
            contenedor.dataset.estado = "cargando";
            contenedor.innerHTML = `
                <p class="registro-completo-pnf-mensaje">
                    <i class="fa-solid fa-spinner fa-spin"></i>
                    Cargando programas de formación...
                </p>
            `;

            const csrfToken = document.querySelector(
                "[name=csrfmiddlewaretoken]"
            )?.value;

            if (!csrfToken) {
                throw new Error("No se encontró el token CSRF.");
            }

            const formulario = new FormData();
            formulario.append("nucleo", nucleo);

            const respuesta = await fetch("/pnfs_cursar/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrfToken
                },
                body: formulario
            });

            if (!respuesta.ok) {
                throw new Error(
                    `Error al consultar los PNF. Código HTTP: ${respuesta.status}`
                );
            }

            const resultado = await respuesta.json();

            if (!resultado || !Array.isArray(resultado.pnfs)) {
                throw new Error("La respuesta del servidor no contiene una lista válida de PNF.");
            }

            console.log(resultado);

            // Limpiar el contenedor.
            contenedor.innerHTML = "";

            // Comprobar si existen programas disponibles.
            if (resultado.pnfs.length === 0) {

                contenedor.dataset.estado = "vacio";

                contenedor.innerHTML = `
                    <p class="registro-completo-pnf-mensaje">
                        No hay programas de formación disponibles para este núcleo.
                    </p>
                `;

            } else {

                // Generar las opciones de PNF.
                resultado.pnfs.forEach(pnf => {

                    const icono = obtenerIconoPNF(pnf.nombre);

                    const etiqueta = document.createElement("label");
                    etiqueta.className = "registro-completo-pnf-opcion";

                    const iconoContenedor = document.createElement("span");
                    iconoContenedor.className = "registro-completo-pnf-icono";
                    iconoContenedor.setAttribute("aria-hidden", "true");

                    const elementoIcono = document.createElement("i");
                    elementoIcono.className = `fa-solid ${icono}`;

                    iconoContenedor.appendChild(elementoIcono);

                    const nombre = document.createElement("span");
                    nombre.className = "registro-completo-pnf-nombre";
                    nombre.textContent = pnf.nombre;

                    const input = document.createElement("input");
                    input.type = "radio";
                    input.value = pnf.id;
                    input.name = "pnf_seleccionado";
                    input.required = true;

                    etiqueta.appendChild(iconoContenedor);
                    etiqueta.appendChild(nombre);
                    etiqueta.appendChild(input);

                    contenedor.appendChild(etiqueta);
                });

                contenedor.dataset.estado = "listo";
            }

            // Notificar que terminó la actualización.
            document.dispatchEvent(
                new CustomEvent("casrce:pnfs-actualizados", {
                    detail: {
                        nucleo,
                        cantidad: resultado.pnfs.length,
                        estado: contenedor.dataset.estado
                    }
                })
            );

        } catch (error) {

            console.error("Error al cargar los PNF:", error);

            contenedor.dataset.estado = "error";

            contenedor.innerHTML = `
                <p class="registro-completo-pnf-mensaje">
                    <i class="fa-solid fa-circle-exclamation"></i>
                    No se pudieron cargar los programas de formación.
                    Selecciona nuevamente el núcleo para intentarlo otra vez.
                </p>
            `;

            document.dispatchEvent(
                new CustomEvent("casrce:pnfs-actualizados", {
                    detail: {
                        nucleo,
                        cantidad: 0,
                        estado: "error"
                    }
                })
            );
        }
    }
});

// ==========================================================
// VALIDACIÓN DE CAMPOS POR PASO

const formulario_registro = document.getElementById("formulario_registro");

// ==========================================================

const btnAnterior = document.getElementById("btn_anterior");
const btnSiguiente = document.getElementById("btn_siguiente");

const pasosFormulario = Array.from(
    document.querySelectorAll("#formulario_registro .paso_formulario")
);

// Campos opcionales: se indica expresamente que pueden quedar vacíos.
const nombresOpcionales = [
    "correo_secundaria",
    "dominio_correo_secundaria",
    "prefijo_telefono_secundaria",
    "num_telefono_secundaria",
    "nombres_auxiliar",
    "apellidos_auxiliar",
    "nacionalidad_auxiliar",
    "ci_auxiliar",
    "prefijo_auxiliar",
    "telefono_auxiliar",
    "parestenco_auxiliar",
    "carnet_dispacidad",
    "registro_medico",
    "tipos_discapacidad",
    "tipo_discapacidad",
    "grado_discapacidad",
    "causa_discapacidad"
];

// Marcar visualmente los campos opcionales.
nombresOpcionales.forEach(nombre => {
    formulario_registro
        .querySelectorAll(`[name="${nombre}"]`)
        .forEach(campo => {
            campo.required = false;

            const etiqueta = campo.id
                ? formulario_registro.querySelector(
                    `label[for="${campo.id}"]`
                )
                : null;

            if (
                etiqueta &&
                !/opcional/i.test(etiqueta.textContent)
            ) {
                const marca = document.createElement("small");
                marca.textContent = " ";
                marca.className = "etiqueta-opcional";
                etiqueta.appendChild(marca);
            }
        });
});

// ==========================================================
// DISCAPACIDAD: CARNET Y REGISTRO MÉDICO CONDICIONAL
// ==========================================================

const selectorCarnetDiscapacidad = document.getElementById(
    "codigo_carnet_dispacidad"
);

const numeroRegistroMedico = document.getElementById(
    "nro_registro_medico"
);

function actualizarValidacionDiscapacidad() {
    if (!selectorCarnetDiscapacidad) return;

    const poseeCarnet = selectorCarnetDiscapacidad.value === "Si";
    const camposCondicionales = [
        numeroRegistroMedico,
        document.getElementById("tipos_discapacidad"),
        document.getElementById("grado_discapacidad"),
        document.getElementById("causa_discapacidad")
    ].filter(Boolean);

    // Con "Sí", todos los datos de discapacidad son obligatorios.
    // Con "No" (o mientras no se seleccione una respuesta), son opcionales.
    camposCondicionales.forEach(campo => {
        campo.required = poseeCarnet;
        if (!poseeCarnet) campo.setCustomValidity("");
    });

    if (numeroRegistroMedico) {
        const valorRegistro = numeroRegistroMedico.value.trim();
        numeroRegistroMedico.setCustomValidity(
            !valorRegistro || /^[A-Z]-\d{6}$/.test(valorRegistro)
                ? ""
                : "Utilice el formato de una letra, un guion y seis números. Ejemplo: D-123456."
        );
    }

    // Actualiza los indicadores visuales de obligatoriedad.
    document.dispatchEvent(new CustomEvent("casrce:discapacidad-actualizada"));
}

if (selectorCarnetDiscapacidad && numeroRegistroMedico) {
    selectorCarnetDiscapacidad.addEventListener(
        "change",
        actualizarValidacionDiscapacidad
    );

    numeroRegistroMedico.addEventListener("input", () => {
        const valor = numeroRegistroMedico.value.toUpperCase();
        const primeraLetra = valor.charAt(0);

        if (/^[A-Z]$/.test(primeraLetra)) {
            const digitos = valor.slice(1).replace(/\D/g, "").slice(0, 6);
            numeroRegistroMedico.value = `${primeraLetra}-${digitos}`;
        } else {
            numeroRegistroMedico.value = valor
                .replace(/[^A-Z0-9-]/g, "")
                .slice(0, 8);
        }

        actualizarValidacionDiscapacidad();
    });

    actualizarValidacionDiscapacidad();
}

// ==========================================================
// SECUNDARIA: MÁXIMO DOS DÍGITOS EN EL NOMBRE DEL LICEO
// ==========================================================

const nombreLiceo = document.getElementById("nombre_secundaria");

if (nombreLiceo) {
    nombreLiceo.addEventListener("input", () => {
        let digitosPermitidos = 0;

        nombreLiceo.value = nombreLiceo.value.replace(/\d/g, digito => {
            digitosPermitidos += 1;
            return digitosPermitidos <= 2 ? digito : "";
        });
    });
}

// ==========================================================
// DOCUMENTOS: VISTA PREVIA LOCAL DE ARCHIVOS
// ==========================================================

const documentosConVistaPrevia = [
    { inputId: "documentoCI_estudiante", previewId: "vista_previa_documentoCI_estudiante" },
    { inputId: "documentoTB_estudiante", previewId: "vista_previa_documentoTB_estudiante" },
    { inputId: "documentoSN_estudiante", previewId: "vista_previa_documentoSN_estudiante" },
    { inputId: "documentoOPSU_estudiante", previewId: "vista_previa_documentoOPSU_estudiante" }
];

function formatoTamanoArchivo(bytes) {
    if (bytes < 1024 * 1024) {
        return `${(bytes / 1024).toFixed(1)} KB`;
    }
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

documentosConVistaPrevia.forEach(({ inputId, previewId }) => {
    const inputArchivo = document.getElementById(inputId);
    const contenedorVistaPrevia = document.getElementById(previewId);

    if (!inputArchivo || !contenedorVistaPrevia) return;

    let urlTemporal = null;

    inputArchivo.addEventListener("change", () => {
        if (urlTemporal) {
            URL.revokeObjectURL(urlTemporal);
            urlTemporal = null;
        }

        contenedorVistaPrevia.replaceChildren();
        contenedorVistaPrevia.classList.remove("tiene-archivo");

        const archivo = inputArchivo.files && inputArchivo.files[0];

        if (!archivo) {
            const vacio = document.createElement("span");
            vacio.className = "vista-previa-vacio";
            vacio.textContent = "Aún no se ha seleccionado un archivo.";
            contenedorVistaPrevia.appendChild(vacio);
            return;
        }

        contenedorVistaPrevia.classList.add("tiene-archivo");

        const informacion = document.createElement("div");
        informacion.className = "vista-previa-archivo-info";

        const nombre = document.createElement("strong");
        nombre.textContent = archivo.name;

        const tamano = document.createElement("small");
        tamano.textContent = formatoTamanoArchivo(archivo.size);

        informacion.append(nombre, tamano);
        contenedorVistaPrevia.appendChild(informacion);

        urlTemporal = URL.createObjectURL(archivo);

        if (archivo.type.startsWith("image/")) {
            const imagen = document.createElement("img");
            imagen.className = "vista-previa-imagen";
            imagen.src = urlTemporal;
            imagen.alt = `Vista previa de ${archivo.name}`;
            contenedorVistaPrevia.appendChild(imagen);
        } else if (
            archivo.type === "application/pdf" ||
            archivo.name.toLowerCase().endsWith(".pdf")
        ) {
            const visor = document.createElement("iframe");
            visor.className = "vista-previa-pdf";
            visor.src = urlTemporal;
            visor.title = `Vista previa de ${archivo.name}`;
            visor.loading = "lazy";
            contenedorVistaPrevia.appendChild(visor);
        } else {
            const nota = document.createElement("small");
            nota.className = "vista-previa-no-disponible";
            nota.textContent =
                "La vista previa de este formato no está disponible en el navegador.";
            contenedorVistaPrevia.appendChild(nota);
        }

        const quitar = document.createElement("button");
        quitar.type = "button";
        quitar.className = "vista-previa-quitar";
        quitar.textContent = "Quitar archivo";
        quitar.addEventListener("click", () => {
            inputArchivo.value = "";
            inputArchivo.dispatchEvent(new Event("change", { bubbles: true }));
        });
        contenedorVistaPrevia.appendChild(quitar);
    });
});

// Estilos de los campos pendientes y de la lista de errores.
const estilosValidacion = document.createElement("style");

estilosValidacion.textContent = `
    #formulario_registro .campo-error {
        border: 1px solid #dc2626 !important;
        box-shadow: 0 0 0 2px rgba(220, 38, 38, .12) !important;
    }

    #formulario_registro .mensaje-validacion-paso {
        margin: 0 0 16px;
        padding: 14px 16px;
        border: 1px solid #fecaca;
        border-radius: 10px;
        background: #fef2f2;
        color: #991b1b;
    }

    #formulario_registro .mensaje-validacion-paso strong {
        display: block;
        margin-bottom: 8px;
    }

    #formulario_registro .mensaje-validacion-paso ul {
        margin: 0 0 0 20px;
    }

    #formulario_registro .mensaje-validacion-paso li {
        margin-top: 5px;
    }

    #formulario_registro .etiqueta-opcional {
        color: #64748b;
        font-size: .82em;
        font-weight: normal;
    }
`;

document.head.appendChild(estilosValidacion);

// Encuentra el paso que se encuentra visible.
function obtenerPasoVisible() {
    return pasosFormulario.find(paso => {
        const estilo = window.getComputedStyle(paso);

        return (
            estilo.display !== "none" &&
            estilo.visibility !== "hidden"
        );
    });
}

// Comprueba si un campo está oculto o desactivado.
function campoNoVisible(campo) {
    if (
        campo.disabled ||
        campo.type === "hidden" ||
        campo.closest("[hidden]")
    ) {
        return true;
    }

    const estilo = window.getComputedStyle(campo);

    if (
        estilo.display === "none" ||
        estilo.visibility === "hidden"
    ) {
        return true;
    }

    const paso = campo.closest(".paso_formulario");

    if (paso) {
        const estiloPaso = window.getComputedStyle(paso);

        if (
            estiloPaso.display === "none" ||
            estiloPaso.visibility === "hidden"
        ) {
            return true;
        }
    }

    return false;
}

// Obtiene el nombre legible del campo.
function obtenerNombreCampo(campo) {

    const etiqueta = campo.id
        ? formulario_registro.querySelector(`label[for="${campo.id}"]`)
        : campo.closest("label");

    if (etiqueta) {
        return etiqueta.textContent.trim();
    }

    if (campo.type === "file") {
        return "Documento: " + campo.name.replaceAll("_", " ");
    }

    return campo.name.replaceAll("_", " ");
}

// Comprueba si un campo obligatorio tiene valor.
function campoVacio(campo) {
    if (campo.type === "checkbox" || campo.type === "radio") {
        return !campo.checked;
    }

    if (campo.type === "file") {
        return !campo.files || campo.files.length === 0;
    }

    return !String(campo.value || "").trim();
}

// Obtiene todos los campos pendientes del paso actual.
function obtenerCamposPendientes(paso) {

    const pendientes = [];

    const campos = paso.querySelectorAll(
        "input[required], select[required], textarea[required]"
    );

    campos.forEach(campo => {

        if (["correo_secundario", "dominio_secundario"].includes(campo.id)) {
            return;
        }

        if (campoNoVisible(campo)) {
            return;
        }

        // Validar los grupos de radio como una sola selección.
        if (campo.type === "radio") {

            const grupo = Array.from(
                paso.querySelectorAll('input[type="radio"]')
            ).filter(radio =>
                radio.name === campo.name &&
                !campoNoVisible(radio)
            );

            // Evitar validar varias veces el mismo grupo.
            if (grupo[0] !== campo) {
                return;
            }

            const seleccionado = grupo.some(radio => radio.checked);

            if (!seleccionado) {
                pendientes.push({
                    campo: campo,
                    nombre: obtenerNombreCampo(campo)
                });
            }

            return;
        }

        // No repetir campos con el mismo nombre.
        if (
            pendientes.some(item => item.campo.name === campo.name) &&
            campo.type !== "checkbox"
        ) {
            return;
        }

        if (campoVacio(campo)) {

            pendientes.push({
                campo: campo,
                nombre: obtenerNombreCampo(campo)
            });

        } else if (
            typeof campo.checkValidity === "function" &&
            !campo.checkValidity()
        ) {

            pendientes.push({
                campo: campo,
                nombre: obtenerNombreCampo(campo)
            });

        }

    });

    if (paso.id === "contenedor_pnfs_cursar") {
        const nucleoSeleccionado = paso.querySelector(
            'input[name="nucleo_seleccionado"]:checked'
        );

        if (nucleoSeleccionado) {
            const contenedorActivo = document.getElementById(
                `contenedor_pnfs_${nucleoSeleccionado.value}`
            );
            const opcionesPNF = contenedorActivo
                ? Array.from(contenedorActivo.querySelectorAll(
                    'input[type="radio"][name="pnf_seleccionado"]'
                ))
                : [];

            const pnfSeleccionado = opcionesPNF.some(opcion => opcion.checked);

            const yaReportado = pendientes.some(
                item => item.campo.name === "pnf_seleccionado"
            );

            if (!pnfSeleccionado && !yaReportado) {
                pendientes.push({
                    campo: opcionesPNF[0] || nucleoSeleccionado,
                    nombre: "Seleccione un Programa Nacional de Formación (PNF)"
                });
            }
        }
    }

    return pendientes;
}

// Muestra una lista de los campos que faltan.
function mostrarCamposPendientes(paso, pendientes) {
    let aviso = paso.querySelector(".mensaje-validacion-paso");

    if (!aviso) {
        aviso = document.createElement("div");
        aviso.className = "mensaje-validacion-paso";
        aviso.setAttribute("role", "alert");

        const encabezado = paso.querySelector(
            ".registro-completo-paso-encabezado"
        );

        if (encabezado) {
            encabezado.insertAdjacentElement("afterend", aviso);
        } else {
            paso.prepend(aviso);
        }
    }

    aviso.replaceChildren();

    const titulo = document.createElement("strong");
    titulo.textContent =
        "Completa los siguientes campos para continuar:";

    aviso.appendChild(titulo);

    const lista = document.createElement("ul");

    pendientes.forEach(({ campo, nombre }) => {
        const elemento = document.createElement("li");
        elemento.textContent = nombre;
        lista.appendChild(elemento);

        campo.classList.add("campo-error");
    });

    aviso.appendChild(lista);
}

// Borra los avisos cuando el usuario corrige los campos.
function limpiarErroresPaso(paso) {
    paso.querySelectorAll(".mensaje-validacion-paso")
        .forEach(aviso => aviso.remove());

    paso.querySelectorAll(".campo-error")
        .forEach(campo => campo.classList.remove("campo-error"));
}

// Valida un paso completo.
function validarPasoActual(paso) {
    if (!paso) {
        return true;
    }

    limpiarErroresPaso(paso);

    const pendientes = obtenerCamposPendientes(paso);

    if (pendientes.length > 0) {
        mostrarCamposPendientes(paso, pendientes);

        const primerCampo = pendientes[0].campo;

        if (primerCampo) {
            primerCampo.focus({ preventScroll: false });
        }

        return false;
    }

    return true;
}

// Evita que el navegador valide campos que están en pasos ocultos.
// La validación se realiza paso por paso.
formulario_registro.noValidate = true;

// Validar antes de que se ejecute la navegación existente.
if (btnSiguiente) {
    btnSiguiente.addEventListener("click", evento => {
        const paso = obtenerPasoVisible();

        if (!validarPasoActual(paso)) {
            evento.preventDefault();
            evento.stopImmediatePropagation();
        }
    }, true);
}

// Limpiar los errores al volver al paso anterior.
if (btnAnterior) {
    btnAnterior.addEventListener("click", () => {
        const paso = obtenerPasoVisible();

        if (paso) {
            limpiarErroresPaso(paso);
        }
    }, true);
}

// Actualizar los errores cuando se editen los campos.
formulario_registro
    .querySelectorAll("input, select, textarea")
    .forEach(campo => {
        campo.addEventListener("input", () => {
            campo.classList.remove("campo-error");

            const paso = campo.closest(".paso_formulario");

            if (
                paso &&
                paso.querySelector(".mensaje-validacion-paso")
            ) {
                const pendientes = obtenerCamposPendientes(paso);

                if (pendientes.length === 0) {
                    limpiarErroresPaso(paso);
                } else {
                    mostrarCamposPendientes(paso, pendientes);
                }
            }
        });

        campo.addEventListener("change", () => {
            campo.classList.remove("campo-error");
        });
    });

    // ==========================================================
    // CONTADORES DE CARACTERES DE LAS DIRECCIONES
    // ==========================================================
    const camposDireccion = [
        {
            campo: document.getElementById("direccion_nacimiento"),
            contador: document.getElementById("contador_direccion_nacimiento")
        },
        {
            campo: document.getElementById("direccion_domicilio"),
            contador: document.getElementById("contador_direccion")
        }
    ];

    const limite_direccion = 100;

    camposDireccion.forEach(({ campo, contador }) => {

        if (!campo || !contador) return;

        // Establecer el límite desde JavaScript también.
        campo.maxLength = limite_direccion;

        function actualizarContador() {
            const caracteres = campo.value.length;

            contador.textContent =
                `${caracteres} / ${limite_direccion}`;

            contador.classList.toggle(
                "contador-direccion-cerca",
                caracteres >= 80 && caracteres < limite_direccion
            );

            contador.classList.toggle(
                "contador-direccion-limite",
                caracteres >= limite_direccion
            );
        }

        campo.addEventListener("input", actualizarContador);

        // Mostrar el conteo inicial.
        actualizarContador();
    });