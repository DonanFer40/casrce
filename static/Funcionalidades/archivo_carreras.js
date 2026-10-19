
document.addEventListener("DOMContentLoaded", () => {

    /* =====================================================
       1. INFORMACIÓN ACADÉMICA DE LOS NÚCLEOS
    ===================================================== */

    const carreras_sedes = {
        "Barinas": {
            direccion: "Barinas, Estado Barinas, Venezuela",
            coordenadas: [8.6226, -70.2075],
            carreras: [
                "Ingeniería en Sistemas e Informática",
                "Ingeniería Electrónica",
                "Medicina Veterinaria",
                "Nutrición y Dietética"
            ],
            tipos_grados: [
                "TSU - Ingeniería",
                "TSU - Ingeniería",
                "Licenciatura",
                "Licenciatura"
            ],
            duracion: [
                "4 años",
                "4 años",
                "5 años",
                "5 años"
            ]
        },

        "Barinitas": {
            direccion: "Barinitas, Municipio Bolívar, Estado Barinas, Venezuela",
            coordenadas: [8.7617, -70.4117],
            carreras: [
                "Ingeniería en Electricidad",
                "Ingeniería en Mecánica",
                "Ingeniería en Agroalimentación",
                "Ingeniería en Construcción Civil",
                "Ingeniería Industrial",
                "Ingeniería en Sistemas e Informática",
                "Medicina Veterinaria"
            ],
            tipos_grados: [
                "TSU - Ingeniería",
                "TSU - Ingeniería",
                "TSU - Ingeniería",
                "TSU - Ingeniería",
                "TSU - Ingeniería",
                "TSU - Ingeniería",
                "Licenciatura"
            ],
            duracion: [
                "4 años",
                "4 años",
                "4 años",
                "4 años",
                "4 años",
                "4 años",
                "5 años"
            ]
        },

        "Socopo": {
            direccion: "Socopó, Municipio Antonio José de Sucre, Estado Barinas, Venezuela",
            coordenadas: [8.2297, -70.8228],
            carreras: [
                "Ingeniería en Electricidad",
                "Ingeniería en Agroalimentación",
                "Ingeniería en Construcción Civil",
                "Ingeniería en Sistemas e Informática",
                "Medicina Veterinaria"
            ],
            tipos_grados: [
                "TSU - Ingeniería",
                "TSU - Ingeniería",
                "TSU - Ingeniería",
                "TSU - Ingeniería",
                "Licenciatura"
            ],
            duracion: [
                "4 años",
                "4 años",
                "4 años",
                "4 años",
                "5 años"
            ]
        },

        "Pedraza": {
            direccion: "Municipio Pedraza, Estado Barinas, Venezuela",
            coordenadas: [8.3306, -70.5856],
            carreras: [
                "Ingeniería en Agroalimentación",
                "Medicina Veterinaria"
            ],
            tipos_grados: [
                "TSU - Ingeniería",
                "Licenciatura"
            ],
            duracion: [
                "4 años",
                "5 años"
            ]
        }
    };


    /* =====================================================
       2. REFERENCIAS AL HTML
    ===================================================== */

    const contenedor = document.getElementById(
        "OfertaAcademica-contenedor-carrera"
    );

    const titulo = document.getElementById(
        "OfertaAcademica-info-sedes"
    );

    const nombre_sede = document.getElementById(
        "OfertaAcademica-nombre-sede"
    );

    const direccion_sede = document.getElementById(
        "OfertaAcademica-direccion-texto"
    );

    const enlace_maps = document.getElementById(
        "OfertaAcademica-maps-enlace"
    );

    const total_carreras = document.getElementById(
        "OfertaAcademica-total-carreras"
    );

    const indicador_numero = document.getElementById(
        "OfertaAcademica-indicador-numero"
    );

    const indicador_nombre = document.getElementById(
        "OfertaAcademica-indicador-nombre"
    );

    const btn_avanzar = document.getElementById(
        "OfertaAcademica-avanzar"
    );

    const btn_retroceder = document.getElementById(
        "OfertaAcademica-retroceder"
    );

    const mapa_contenedor = document.getElementById(
        "OfertaAcademica-mapa-interactivo"
    );


    /* =====================================================
       3. COMPROBAR ELEMENTOS NECESARIOS
    ===================================================== */

    const elementos_obligatorios = {
        contenedor,
        titulo,
        nombre_sede,
        direccion_sede,
        enlace_maps,
        total_carreras,
        indicador_numero,
        indicador_nombre,
        btn_avanzar,
        btn_retroceder
    };

    const elementos_faltantes = Object.entries(
        elementos_obligatorios
    )
        .filter(([, elemento]) => !elemento)
        .map(([nombre]) => nombre);

    if (elementos_faltantes.length > 0) {
        console.error(
            "Oferta Académica: faltan elementos HTML:",
            elementos_faltantes
        );
        return;
    }


    /* =====================================================
       4. ESTADO DE NAVEGACIÓN
    ===================================================== */

    const sedes = Object.keys(carreras_sedes);

    let sedeIndex = 0;

    let mapa = null;
    let marcador = null;


    /* =====================================================
       5. INICIALIZAR MAPA
    ===================================================== */

    function inicializarMapa() {

        if (!mapa_contenedor) {
            console.warn("No se encontró el contenedor del mapa.");
            return;
        }

        if (typeof L === "undefined") {
            console.warn(
                "Leaflet no está disponible. Se omitirá el mapa."
            );
            return;
        }

        const sede_inicial = carreras_sedes[sedes[sedeIndex]];

        mapa = L.map(mapa_contenedor).setView(
            sede_inicial.coordenadas,
            12
        );

        L.tileLayer(
            "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
            {
                attribution:
                    '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
                maxZoom: 19,
                referrerPolicy: "strict-origin-when-cross-origin"
            }
        ).addTo(mapa);

        marcador = L.marker(
            sede_inicial.coordenadas
        ).addTo(mapa);

        marcador.bindPopup(
            `<strong>${sedes[sedeIndex]}</strong>`
        );

        setTimeout(() => {
            mapa.invalidateSize();
        }, 200);
    }


    /* =====================================================
       6. ACTUALIZAR MAPA SEGÚN EL NÚCLEO
    ===================================================== */

    function actualizarMapa(sedeActual, data) {

        if (!mapa || !marcador) {
            return;
        }

        marcador.setLatLng(data.coordenadas);

        marcador.bindPopup(
            `<strong>${sedeActual}</strong>`
        );

        mapa.setView(data.coordenadas, 12, {
            animate: true
        });
    }


    /* =====================================================
       7. MOSTRAR INFORMACIÓN DEL NÚCLEO
    ===================================================== */

    function mostrar() {

        const sedeActual = sedes[sedeIndex];
        const data = carreras_sedes[sedeActual];

        if (!data) {
            console.error(
                "No existe información para el núcleo:",
                sedeActual
            );
            return;
        }

        // Encabezado y ubicación.
        titulo.textContent =
            `Carreras impartidas en la sede ${sedeActual}`;

        nombre_sede.textContent = sedeActual;

        direccion_sede.textContent = data.direccion;

        // Enlace para buscar el núcleo en Google Maps.
        enlace_maps.href =
            `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(
                `${sedeActual}, ${data.direccion}`
            )}`;

        // Limpiar tabla anterior.
        contenedor.replaceChildren();

        // Generar las filas de carreras.
        data.carreras.forEach((carrera, i) => {

            const fila = document.createElement("tr");

            const celda_carrera = document.createElement("td");
            const celda_grado = document.createElement("td");
            const celda_duracion = document.createElement("td");

            celda_carrera.textContent = carrera;
            celda_grado.textContent = data.tipos_grados[i];
            celda_duracion.textContent = data.duracion[i];

            fila.append(
                celda_carrera,
                celda_grado,
                celda_duracion
            );

            contenedor.appendChild(fila);
        });

        // Total de carreras del núcleo.
        const cantidad = data.carreras.length;

        total_carreras.textContent =
            `${cantidad} ${cantidad === 1 ? "carrera" : "carreras"}`;

        // Indicador de posición.
        indicador_numero.textContent =
            `${sedeIndex + 1} / ${sedes.length}`;

        indicador_nombre.textContent = sedeActual;

        // Estado de los botones.
        btn_retroceder.disabled = sedeIndex === 0;

        btn_avanzar.disabled =
            sedeIndex === sedes.length - 1;

        // Actualizar mapa.
        actualizarMapa(sedeActual, data);
    }


    /* =====================================================
       8. AVANZAR AL SIGUIENTE NÚCLEO
    ===================================================== */

    btn_avanzar.addEventListener("click", () => {

        if (sedeIndex < sedes.length - 1) {
            sedeIndex++;
            mostrar();
        }

    });


    /* =====================================================
       9. REGRESAR AL NÚCLEO ANTERIOR
    ===================================================== */

    btn_retroceder.addEventListener("click", () => {

        if (sedeIndex > 0) {
            sedeIndex--;
            mostrar();
        }

    });


    /* =====================================================
       10. INICIAR LA PÁGINA
    ===================================================== */

    mostrar();
    inicializarMapa();

});
