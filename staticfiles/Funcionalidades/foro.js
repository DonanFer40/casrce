document.addEventListener("DOMContentLoaded", () => {

    /* =====================================================
       ELEMENTOS
    ====================================================== */

    const carrusel = document.querySelector(".carrusel");
    const slides = document.querySelectorAll(".carrusel-slide");
    const indicadores = document.querySelectorAll(".indicador");

    const botonAnterior = document.querySelector(".carrusel-anterior");
    const botonSiguiente = document.querySelector(".carrusel-siguiente");

    const selectorNucleo = document.getElementById("selectorNucleo");
    const noticiasGrid = document.getElementById("noticiasGrid");
    const estadoNoticias = document.getElementById("estadoNoticias");
    const tituloNoticias = document.getElementById("tituloNoticias");

    const configuracion = document.getElementById("foro-config");

    const urlNoticias = configuracion
        ? configuracion.dataset.urlNoticias
        : "";

    let indiceActual = 0;
    let intervaloCarrusel = null;
    let noticiasActuales = [];


    /* =====================================================
       CARRUSEL
    ====================================================== */

    function mostrarSlide(indice) {

        if (!slides.length) {
            return;
        }

        if (indice >= slides.length) {
            indice = 0;
        }

        if (indice < 0) {
            indice = slides.length - 1;
        }

        indiceActual = indice;

        slides.forEach((slide, index) => {
            slide.classList.toggle(
                "activo",
                index === indiceActual
            );
        });

        indicadores.forEach((indicador, index) => {
            indicador.classList.toggle(
                "activo",
                index === indiceActual
            );
        });
    }


    function siguienteSlide() {
        mostrarSlide(indiceActual + 1);
    }


    function anteriorSlide() {
        mostrarSlide(indiceActual - 1);
    }


    function iniciarCarrusel() {

        detenerCarrusel();

        intervaloCarrusel = setInterval(() => {
            siguienteSlide();
        }, 5000);
    }


    function detenerCarrusel() {

        if (intervaloCarrusel) {
            clearInterval(intervaloCarrusel);
            intervaloCarrusel = null;
        }
    }


    function reiniciarCarrusel() {
        detenerCarrusel();
        iniciarCarrusel();
    }


    if (botonSiguiente) {
        botonSiguiente.addEventListener(
            "click",
            () => {
                siguienteSlide();
                reiniciarCarrusel();
            }
        );
    }


    if (botonAnterior) {
        botonAnterior.addEventListener(
            "click",
            () => {
                anteriorSlide();
                reiniciarCarrusel();
            }
        );
    }


    indicadores.forEach((indicador, index) => {

        indicador.addEventListener(
            "click",
            () => {
                mostrarSlide(index);
                reiniciarCarrusel();
            }
        );

    });


    if (carrusel) {

        carrusel.addEventListener(
            "mouseenter",
            detenerCarrusel
        );

        carrusel.addEventListener(
            "mouseleave",
            iniciarCarrusel
        );

    }


    mostrarSlide(0);
    iniciarCarrusel();


    /* =====================================================
       SELECTOR DE SEDE
    ====================================================== */

    if (selectorNucleo) {

        selectorNucleo.addEventListener(
            "change",
            () => {

                const nucleo = selectorNucleo.value;

                if (!nucleo) {
                    limpiarNoticias();
                    return;
                }

                cargarNoticias(nucleo);
            }
        );

    }


    /* =====================================================
       CARGAR NOTICIAS
    ====================================================== */

    async function cargarNoticias(nucleo) {

        mostrarCargando();

        try {

            if (!urlNoticias) {
                throw new Error(
                    "No se encontró la URL de noticias."
                );
            }

            const url = `${urlNoticias}?nucleo=${encodeURIComponent(nucleo)}`;

            const respuesta = await fetch(url, {
                method: "GET",
                headers: {
                    "X-Requested-With": "XMLHttpRequest"
                }
            });

            let datos;

            try {
                datos = await respuesta.json();
            } catch (error) {
                throw new Error(
                    "El servidor devolvió una respuesta inválida."
                );
            }

            if (!respuesta.ok) {
                throw new Error(
                    datos.error ||
                    "No fue posible cargar las noticias."
                );
            }

            mostrarNoticias(
                datos.nucleo,
                datos.noticias || []
            );

        } catch (error) {

            console.error(
                "Error al cargar noticias:",
                error
            );

            mostrarError(
                error.message ||
                "No fue posible cargar las noticias."
            );
        }

    }


    /* =====================================================
       MOSTRAR NOTICIAS
    ====================================================== */

    function mostrarNoticias(nucleo, noticias) {

        noticiasActuales = noticias;

        estadoNoticias.style.display = "none";

        noticiasGrid.innerHTML = "";

        tituloNoticias.textContent =
            `Noticias de ${nucleo}`;


        if (!noticias.length) {

            noticiasGrid.innerHTML = `
                <div class="estado-cargando">
                    <i class="fa-regular fa-newspaper"></i>
                    <p>
                        No hay noticias disponibles para esta sede.
                    </p>
                </div>
            `;

            return;
        }


        noticias.forEach((noticia, indice) => {

            const elemento = crearNoticia(
                noticia,
                indice === 0
            );

            noticiasGrid.appendChild(elemento);

        });

    }


    /* =====================================================
       CREAR NOTICIA
    ====================================================== */

    function crearNoticia(noticia, destacada = false) {

        const article = document.createElement("article");

        article.className = destacada
            ? "noticia-destacada"
            : "noticia-card";


        const imagen = noticia.imagen
            ? `
                <div class="noticia-imagen">
                    <img
                        src="${escapeAttribute(noticia.imagen)}"
                        alt="${escapeAttribute(noticia.titulo)}"
                        loading="lazy"
                    >
                </div>
            `
            : `
                <div class="noticia-imagen">
                    <i class="fa-regular fa-image"></i>
                </div>
            `;


        const informacion = document.createElement("div");

        informacion.className = "noticia-info";

        informacion.innerHTML = `
            <span class="noticia-fecha">
                ${escapeHTML(noticia.fecha || "")}
            </span>

            <h3 class="noticia-titulo">
                ${escapeHTML(noticia.titulo || "")}
            </h3>

            <p class="noticia-descripcion">
                ${escapeHTML(noticia.descripcion || "")}
            </p>

            <button
                type="button"
                class="btn-leer"
                data-id="${escapeAttribute(String(noticia.id))}"
            >
                Leer noticia
                <i class="fa-solid fa-arrow-right"></i>
            </button>
        `;


        article.innerHTML = imagen;

        article.appendChild(informacion);

        return article;
    }


    /* =====================================================
       CARGANDO
    ====================================================== */

    function mostrarCargando() {

        estadoNoticias.style.display = "none";

        tituloNoticias.textContent =
            "Cargando noticias...";

        noticiasGrid.innerHTML = `
            <div class="estado-cargando">
                <i class="fa-solid fa-spinner fa-spin"></i>
                <p>
                    Cargando información institucional...
                </p>
            </div>
        `;

    }


    /* =====================================================
       ERROR
    ====================================================== */

    function mostrarError(mensaje) {

        estadoNoticias.style.display = "none";

        tituloNoticias.textContent =
            "Noticias institucionales";

        noticiasGrid.innerHTML = `
            <div class="estado-error">
                <i class="fa-solid fa-triangle-exclamation"></i>
                <p>
                    ${escapeHTML(mensaje)}
                </p>
            </div>
        `;

    }


    /* =====================================================
       LIMPIAR NOTICIAS
    ====================================================== */

    function limpiarNoticias() {

        noticiasActuales = [];

        noticiasGrid.innerHTML = "";

        tituloNoticias.textContent =
            "Noticias institucionales";

        estadoNoticias.innerHTML = `
            <div class="estado-icono">
                <i class="fa-regular fa-newspaper"></i>
            </div>

            <h2>
                Seleccione una sede
            </h2>

            <p>
                Seleccione una de las sedes disponibles para
                visualizar sus noticias.
            </p>
        `;

        estadoNoticias.style.display = "";

    }


    /* =====================================================
       EVENTOS DE NOTICIAS
    ====================================================== */

    noticiasGrid.addEventListener(
        "click",
        (evento) => {

            const boton =
                evento.target.closest(".btn-leer");

            if (!boton) {
                return;
            }

            const id = boton.dataset.id;

            const noticia =
                buscarNoticiaPorId(id);

            if (noticia) {
                abrirNoticia(noticia);
            }

        }
    );


    function buscarNoticiaPorId(id) {

        return noticiasActuales.find(
            noticia => String(noticia.id) === String(id)
        );

    }


    /* =====================================================
       MODAL
    ====================================================== */

    function abrirNoticia(noticia) {

        cerrarModal();

        const modal =
            document.createElement("div");

        modal.className = "modal-noticia activo";

        modal.innerHTML = `

            <div class="modal-contenido">

                <button
                    type="button"
                    class="modal-cerrar"
                    aria-label="Cerrar noticia"
                >
                    <i class="fa-solid fa-xmark"></i>
                </button>

                ${
                    noticia.imagen
                    ? `
                        <img
                            class="modal-imagen"
                            src="${escapeAttribute(noticia.imagen)}"
                            alt="${escapeAttribute(noticia.titulo)}"
                        >
                    `
                    : ""
                }

                <div class="modal-texto">

                    <span class="modal-fecha">
                        ${escapeHTML(noticia.fecha || "")}
                    </span>

                    <h2>
                        ${escapeHTML(noticia.titulo || "")}
                    </h2>

                    <p>
                        ${escapeHTML(noticia.contenido || "")}
                    </p>

                </div>

            </div>
        `;


        document.body.appendChild(modal);


        const botonCerrar =
            modal.querySelector(".modal-cerrar");


        botonCerrar.addEventListener(
            "click",
            cerrarModal
        );


        modal.addEventListener(
            "click",
            (evento) => {

                if (
                    evento.target === modal
                ) {
                    cerrarModal();
                }

            }
        );

    }


    function cerrarModal() {

        const modal =
            document.querySelector(".modal-noticia");

        if (modal) {
            modal.remove();
        }

    }


    /* =====================================================
       ESCAPE
    ====================================================== */

    document.addEventListener(
        "keydown",
        (evento) => {

            if (evento.key === "Escape") {
                cerrarModal();
            }

        }
    );


    /* =====================================================
       SEGURIDAD
    ====================================================== */

    function escapeHTML(valor) {

        return String(valor)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");

    }


    function escapeAttribute(valor) {

        return escapeHTML(valor);

    }

});