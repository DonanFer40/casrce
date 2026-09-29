document.addEventListener("DOMContentLoaded", () => {

    async function calcular_promedios_finales() {
        console.log("Ejecutando cálculo de promedios");
        try {
            const respuesta = await fetch("/notas_academicas/calc_prom_est/");
            const resultado = await respuesta.json();
            console.log(resultado);

            Swal.fire({
                title: resultado.title,
                text: resultado.descripcion,
                icon: resultado.icon
            });
        } catch (error) {
            console.error(error);
        }
    }

    async function actualizar_promedio_reparacion() {
        console.log("Ejecutando actualizar promedios reparación a promedios finales");
        try {
            const respuesta = await fetch("/notas_academicas/act_prom_rep/");
            const resultado = await respuesta.json();
            console.log(resultado);

            Swal.fire({
                title: resultado.title,
                text: resultado.descripcion,
                icon: resultado.icon
            });
        } catch (error) {
            console.error(error);
        }
    }

    async function actualizar_trayectos() {
        console.log("Ejecutando actualización de trayectos");

        try {
            const respuesta = await fetch("/notas_academicas/act_tray_est/");
            const resultado = await respuesta.json();
            console.log(resultado);

            Swal.fire({
                title: resultado.title,
                text: resultado.descripcion,
                icon: resultado.icon
            });
        } catch (error) {
            console.error(error);
        }
    }

    // actualizar_trayectos();

    // actualizar_promedio_reparacion();

    // calcular_promedios_finales();
});