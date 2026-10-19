
document.addEventListener("DOMContentLoaded", () => {
    // =====================================================
    // ELEMENTOS PRINCIPALES
    // =====================================================

    const botonHamburguesa = document.getElementById("hamburger-btn");

    const menuPublico = document.getElementById("menu-contenedor");

    const menuAutenticado = document.getElementById(
        "menu-contenedor-logueado"
    );

    const barraLateral = document.getElementById(
        "barra-lateral-carsce"
    );

    if (!botonHamburguesa) {
        console.error("CARSCE: no se encontró hamburger-btn.");
        return;
    }

    /*
     * Si existe la barra lateral, la hamburguesa la controla.
     * De lo contrario, controla la navegación pública.
     *
     * El menú superior autenticado no se utiliza como panel
     * móvil cuando existe la barra lateral.
     */

    const modoAutenticado = Boolean(barraLateral);

    const menuActual = modoAutenticado
        ? barraLateral
        : menuPublico || menuAutenticado;

    if (!menuActual) {
        console.error("CARSCE: no se encontró un menú disponible.");
        return;
    }

    const icono = botonHamburguesa.querySelector("i");

    // Clases CSS utilizadas por la barra lateral.
    const CLASE_BARRA_ABIERTA =
        "barra-lateral-carsce-movil-abierta";

    const CLASE_FONDO_ACTIVO =
        "barra-lateral-carsce-fondo-activo";

    const CLASE_MENU_PUBLICO_ABIERTO =
        "menu-movil-abierto";

    // =====================================================
    // ESTADO DEL BOTÓN HAMBURGUESA
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
    // COMPROBAR SI EL MENÚ ESTÁ ABIERTO
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
    // ABRIR MENÚ
    // =====================================================

    function abrirMenu() {
        if (modoAutenticado) {
            barraLateral.classList.add(CLASE_BARRA_ABIERTA);

            document.body.classList.add(CLASE_FONDO_ACTIVO);
        } else {
            menuActual.classList.add(
                CLASE_MENU_PUBLICO_ABIERTO
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
                CLASE_FONDO_ACTIVO
            );
        } else {
            menuActual.classList.remove(
                CLASE_MENU_PUBLICO_ABIERTO
            );

            // Restablecer los submenús públicos.
            menuActual
                .querySelectorAll(".submenu-abierto")
                .forEach((elemento) => {
                    elemento.classList.remove(
                        "submenu-abierto"
                    );
                });
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
            "CARSCE: menú",
            menuEstaAbierto() ? "abierto" : "cerrado"
        );
    });

    // =====================================================
    // SUBMENÚS DE LA NAVEGACIÓN PÚBLICA
    // =====================================================

    if (!modoAutenticado && menuPublico) {
        const botonesSubmenu = menuPublico.querySelectorAll(
            ".navegacion-publica-carsce-toggle"
        );

        botonesSubmenu.forEach((enlace) => {
            enlace.addEventListener("click", (evento) => {
                if (window.innerWidth < 1360) {
                    evento.preventDefault();

                    const elementoPadre = enlace.closest(
                        ".navegacion-publica-carsce-dropdown"
                    );

                    if (elementoPadre) {
                        elementoPadre.classList.toggle(
                            "submenu-abierto"
                        );
                    }
                }
            });
        });
    }

    // =====================================================
    // CERRAR AL SELECCIONAR UN ENLACE
    // =====================================================

    /*
     * En la barra lateral se conservan los <details> y sus
     * acordeones. Los enlaces mantienen sus URL de Django.
     */

    menuActual.querySelectorAll("a[href]").forEach((enlace) => {
        enlace.addEventListener("click", () => {
            if (window.innerWidth < 1360) {
                cerrarMenu();
            }
        });
    });

    // =====================================================
    // CERRAR AL HACER CLIC FUERA
    // =====================================================

    document.addEventListener("click", (evento) => {
        if (!menuEstaAbierto()) {
            return;
        }

        // El clic sobre la hamburguesa ya tiene su propio evento.
        if (botonHamburguesa.contains(evento.target)) {
            return;
        }

        // No cerrar al interactuar dentro del menú.
        if (menuActual.contains(evento.target)) {
            return;
        }

        cerrarMenu();
    });

    // =====================================================
    // CERRAR CON ESCAPE
    // =====================================================

    document.addEventListener("keydown", (evento) => {
        if (evento.key === "Escape" && menuEstaAbierto()) {
            cerrarMenu();
            botonHamburguesa.focus();
        }
    });

    // =====================================================
    // RESTABLECER AL REGRESAR AL ESCRITORIO
    // =====================================================

    window.addEventListener("resize", () => {
        if (window.innerWidth >= 1360) {
            cerrarMenu();
        }
    });

    // =====================================================
    // ESTADO INICIAL
    // =====================================================

    cerrarMenu();

    console.log(
        "CARSCE: navegación preparada:",
        modoAutenticado
            ? "barra lateral del usuario autenticado"
            : "menú público"
    );
});
