document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("formulario_registrar");
    const trayectoSelect = document.getElementById("trayectos_registrados");
    const aulaSelect = document.getElementById("aulas_registrados");
    const periodoSelect = document.getElementById("periodos_academicas_registrados");
    const tableBody = document.getElementById("contenedor_horario");
    const submitButton = document.getElementById("generar_pdf");
    const message = document.getElementById("horario_mensaje");
    const csrfToken = form.querySelector("[name=csrfmiddlewaretoken]").value;

    async function request(url, options = {}) {
        const response = await fetch(url, options);
        const result = await response.json();
        if (!response.ok) {
            throw new Error(result.mensaje || result.descripcion || "No fue posible cargar el horario.");
        }
        return result;
    }

    function clearGrid() {
        tableBody.querySelectorAll("select").forEach((select) => {
            select.innerHTML = '<option value="">Libre</option>';
            select.disabled = true;
        });
        submitButton.disabled = true;
    }

    function postForm(data) {
        const {url, ...fields} = data;
        const body = new FormData();
        Object.entries(fields).forEach(([key, value]) => body.append(key, value));
        return request(url, {
            method: "POST",
            headers: {"X-CSRFToken": csrfToken},
            body,
        });
    }

    async function loadTrayectosAndAulas() {
        try {
            const [trayectosResult, aulasResult] = await Promise.all([
                request("/trayecto_hor/"),
                request("/aulas_hor/"),
            ]);

            trayectosResult.trayectos.forEach((trayecto) => {
                trayectoSelect.add(new Option(trayecto.nombre, trayecto.id_periodo_academico));
            });
            aulasResult.aulas.forEach((aula) => {
                aulaSelect.add(new Option(aula.nombre_aula, aula.id_aula));
            });
        } catch (error) {
            message.textContent = error.message;
        }
    }

    async function loadPeriods() {
        periodoSelect.innerHTML = '<option value="">Selecciona un período</option>';
        clearGrid();
        const trayecto = trayectoSelect.value;
        const aula = aulaSelect.value;
        if (!trayecto || !aula) {
            message.textContent = "Selecciona un trayecto y un aula.";
            return;
        }

        try {
            const result = await postForm({
                url: "/periodo_academico_hor/",
                trayecto,
                aula,
            });
            result.periodos_academicos.forEach((periodo) => {
                periodoSelect.add(new Option(periodo.nombre, periodo.id));
            });
            message.textContent = result.periodos_academicos.length
                ? "Selecciona un período para consultar o editar su horario."
                : "No hay períodos disponibles para este trayecto y aula.";
        } catch (error) {
            message.textContent = error.message;
        }
    }

    async function loadSchedule() {
        clearGrid();
        const trayecto = trayectoSelect.value;
        const aula = aulaSelect.value;
        const periodo = periodoSelect.value;
        if (!trayecto || !aula || !periodo) {
            message.textContent = "Selecciona un trayecto, aula y período.";
            return;
        }

        try {
            const materiasResult = await postForm({
                url: "/asig_mat_reg/",
                trayecto,
                aula,
                periodo_academico: periodo,
            });

            const selects = [...tableBody.querySelectorAll("select")];
            selects.forEach((select) => {
                materiasResult.materias.forEach((asignacion) => {
                    select.add(new Option(
                        asignacion.materia.nombre,
                        asignacion.id_materia_asignada,
                    ));
                });
                select.disabled = materiasResult.materias.length === 0;
            });

            if (!materiasResult.materias.length) {
                message.textContent = "No hay materias activas asociadas a este período.";
                return;
            }

            const params = new URLSearchParams({trayecto, aula, periodo});
            const existente = await request(`/horario_existente/?${params}`);
            existente.horarios.forEach((horario) => {
                if (horario.franja === null) {
                    return;
                }
                const select = tableBody.querySelector(
                    `select[data-franja="${horario.franja}"][data-dia="${horario.dia}"]`,
                );
                if (select) {
                    select.value = horario.materia;
                }
            });

            submitButton.disabled = false;
            message.textContent = existente.horarios.length
                ? "Horario existente cargado. Modifica las celdas y guarda para reemplazarlo."
                : "Completa las celdas necesarias y guarda el nuevo horario.";
        } catch (error) {
            message.textContent = error.message;
        }
    }

    trayectoSelect.addEventListener("change", loadPeriods);
    aulaSelect.addEventListener("change", loadPeriods);
    periodoSelect.addEventListener("change", loadSchedule);

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        submitButton.disabled = true;
        try {
            const result = await request("/reg_hor/", {
                method: "POST",
                headers: {"X-CSRFToken": csrfToken},
                body: new FormData(form),
            });
            message.textContent = result.descripcion;
            await NotificacionesCASRCE.mostrar({
                title: result.title || "Horario guardado",
                text: result.descripcion,
                icon: result.icon || "success",
                allowOutsideClick: false,
                allowEscapeKey: false,
            });
            if (result.url_descarga) {
                window.open(result.url_descarga, "_blank", "noopener");
            }
        } catch (error) {
            message.textContent = error.message;
            await NotificacionesCASRCE.mostrar({
                title: "No se pudo guardar",
                text: error.message,
                icon: "error",
            });
        } finally {
            submitButton.disabled = false;
        }
    });

    loadTrayectosAndAulas();
});
