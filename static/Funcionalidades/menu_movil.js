
document.addEventListener("DOMContentLoaded", () => {

    // =====================================================
    // ELEMENTOS PRINCIPALES
    // =====================================================

    const botonHamburguesa = document.getElementById("hamburger-btn");
    const menuPublico = document.getElementById("menu-contenedor");
    const menuAutenticado = document.getElementById("menu-contenedor-logueado");
    const barraLateral = document.getElementById("barra-lateral-carsce");

    if (!botonHamburguesa) {
        console.error("CASRCE: no se encontró hamburger-btn.");
        return;
    }

    // =====================================================
    // DETECCIÓN DEL TIPO DE NAVEGACIÓN
    // =====================================================

    const modoAutenticado = Boolean(barraLateral);

    const menuActual = modoAutenticado
        ? barraLateral
        : menuPublico || menuAutenticado;

    if (!menuActual) {
        console.error("CASRCE: no se encontró un menú disponible.");
        return;
    }

    const icono = botonHamburguesa.querySelector("i");

    // =====================================================
    // CLASES DE ESTADO
    // =====================================================

    const CLASE_BARRA_ABIERTA =
        "barra-lateral-carsce-movil-abierta";

    const CLASE_FONDO_AUTENTICADO =
        "barra-lateral-carsce-fondo-activo";

    const CLASE_MENU_PUBLICO_ABIERTO =
        "menu-movil-abierto";

    const CLASE_FONDO_PUBLICO =
        "menu-publico-fondo-activo";

    const ANCHO_ESCRITORIO = 1360;

    // =====================================================
    // ESTADO DEL MENÚ
    // =====================================================

    function menuEstaAbierto() {

        if (modoAutenticado) {
            return barraLateral.classList.contains(
                CLASE_BARRA_ABIERTA
            );
        }

        return menuActual.classList.contains(
            CLASE_MENU_PUBLICO_ABIERTO
        );
    }

    // =====================================================
    // ACTUALIZAR BOTÓN HAMBURGUESA
    // =====================================================

    function actualizarBoton(abierto) {

        botonHamburguesa.setAttribute(
            "aria-expanded",
            String(abierto)
        );

        botonHamburguesa.setAttribute(
            "aria-label",
            abierto ? "Cerrar menú" : "Abrir menú"
        );

        if (icono) {

            icono.classList.toggle("fa-bars", !abierto);
            icono.classList.toggle("fa-xmark", abierto);

        }
    }

    // =====================================================
    // RESTABLECER SUBMENÚS PÚBLICOS
    // =====================================================

    function restablecerSubmenusPublicos() {

        if (!menuPublico) {
            return;
        }

        menuPublico
            .querySelectorAll(".submenu-abierto")
            .forEach((elemento) => {

                elemento.classList.remove(
                    "submenu-abierto"
                );

            });
    }

    // =====================================================
    // ABRIR MENÚ
    // =====================================================

    function abrirMenu() {

        if (modoAutenticado) {

            barraLateral.classList.add(
                CLASE_BARRA_ABIERTA
            );

            document.body.classList.add(
                CLASE_FONDO_AUTENTICADO
            );

        } else {

            menuActual.classList.add(
                CLASE_MENU_PUBLICO_ABIERTO
            );

            document.body.classList.add(
                CLASE_FONDO_PUBLICO
            );

        }

        actualizarBoton(true);
    }

    // =====================================================
    // CERRAR MENÚ
    // =====================================================

    function cerrarMenu() {

        if (modoAutenticado) {

            barraLateral.classList.remove(
                CLASE_BARRA_ABIERTA
            );

            document.body.classList.remove(
                CLASE_FONDO_AUTENTICADO
            );

        } else {

            menuActual.classList.remove(
                CLASE_MENU_PUBLICO_ABIERTO
            );

            document.body.classList.remove(
                CLASE_FONDO_PUBLICO
            );

            restablecerSubmenusPublicos();

        }

        actualizarBoton(false);
    }

    // =====================================================
    // BOTÓN HAMBURGUESA
    // =====================================================

    botonHamburguesa.addEventListener("click", (evento) => {

        evento.preventDefault();
        evento.stopPropagation();

        if (menuEstaAbierto()) {

            cerrarMenu();

        } else {

            abrirMenu();

        }

        console.log(
            "CASRCE: menú",
            menuEstaAbierto() ? "abierto" : "cerrado"
        );

    });

    // =====================================================
    // SUBMENÚS PÚBLICOS
    // =====================================================

    if (!modoAutenticado && menuPublico) {

        const botonesSubmenu = menuPublico.querySelectorAll(
            ".navegacion-publica-carsce-toggle"
        );

        botonesSubmenu.forEach((enlace) => {

            enlace.addEventListener("click", (evento) => {

                if (window.innerWidth >= ANCHO_ESCRITORIO) {
                    return;
                }

                evento.preventDefault();
                evento.stopPropagation();

                const elementoPadre = enlace.closest(
                    ".navegacion-publica-carsce-dropdown"
                );

                if (!elementoPadre) {
                    return;
                }

                elementoPadre.classList.toggle(
                    "submenu-abierto"
                );

            });

        });

    }

    // =====================================================
    // CERRAR AL SELECCIONAR UN ENLACE
    // =====================================================

    menuActual.querySelectorAll("a[href]").forEach((enlace) => {

        enlace.addEventListener("click", () => {

            if (window.innerWidth >= ANCHO_ESCRITORIO) {
                return;
            }

            // No cerrar al desplegar un submenú público.
            if (
                !modoAutenticado &&
                enlace.classList.contains(
                    "navegacion-publica-carsce-toggle"
                )
            ) {
                return;
            }

            cerrarMenu();

        });

    });

    // =====================================================
    // CERRAR AL HACER CLIC FUERA DEL MENÚ
    // =====================================================

    document.addEventListener("click", (evento) => {

        if (!menuEstaAbierto()) {
            return;
        }

        // Mantener abierto al pulsar la hamburguesa.
        if (botonHamburguesa.contains(evento.target)) {
            return;
        }

        // Mantener abierto al interactuar dentro del panel.
        if (menuActual.contains(evento.target)) {
            return;
        }

        cerrarMenu();

    });

    // =====================================================
    // PERFIL DEL USUARIO AUTENTICADO
    // =====================================================

    const perfil = modoAutenticado
        ? barraLateral.querySelector(
            ".navegacion-autenticada-carsce-dropdown"
        )
        : null;

    // =====================================================
    // CERRAR CON ESCAPE
    // =====================================================

    document.addEventListener("keydown", (evento) => {

        if (evento.key !== "Escape") {
            return;
        }

        if (menuEstaAbierto()) {

            cerrarMenu();

            botonHamburguesa.focus();

        }

        if (perfil && perfil.open) {

            perfil.open = false;

        }

    });

    // =====================================================
    // CERRAR PERFIL AL HACER CLIC FUERA
    // =====================================================

    if (perfil) {

        document.addEventListener("click", (evento) => {

            if (!perfil.open) {
                return;
            }

            if (perfil.contains(evento.target)) {
                return;
            }

            perfil.open = false;

        });

    }

    // =====================================================
    // RESTABLECER AL REGRESAR A ESCRITORIO
    // =====================================================

    window.addEventListener("resize", () => {

        if (window.innerWidth >= ANCHO_ESCRITORIO) {

            cerrarMenu();

        }

    });

    // =====================================================
    // ESTADO INICIAL
    // =====================================================

    cerrarMenu();

    console.log(
        "CASRCE: navegación preparada:",
        modoAutenticado
            ? "barra lateral autenticada"
            : "menú público"
    );

});
