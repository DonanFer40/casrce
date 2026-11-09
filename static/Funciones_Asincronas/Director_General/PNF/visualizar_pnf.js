document.addEventListener("DOMContentLoaded", () => {

    const tbody = document.getElementById("pnfs_registrados");

    // =========================================
    // CARGAR PNFS
    // =========================================

    async function cargarPNFs() {

        try {

            const respuesta = await fetch("/pnfs_reg/");
            const resultado = await respuesta.json();

            tbody.innerHTML = "";

            if (resultado.estado !== "exito") {

                tbody.innerHTML = `
                    <tr>
                        <td colspan="4">
                            No fue posible cargar los programas.
                        </td>
                    </tr>
                `;

                return;

            }

            if (!resultado.nucleos || resultado.nucleos.length === 0) {

                tbody.innerHTML = `
                    <tr>
                        <td colspan="4">
                            No hay PNFs registrados.
                        </td>
                    </tr>
                `;

                return;

            }

            const nucleo = resultado.nucleos[0];

            if (!nucleo.pnfs || nucleo.pnfs.length === 0) {

                tbody.innerHTML = `
                    <tr>
                        <td colspan="4">
                            No hay PNFs registrados.
                        </td>
                    </tr>
                `;

                return;

            }

            nucleo.pnfs.forEach((pnf, index) => {

                const fila = document.createElement("tr");

                fila.dataset.idNucleo = nucleo.id_nucleo;
                fila.dataset.idPnf = pnf.id_pnf;
                fila.dataset.codigo = pnf.codigo;

                fila.classList.add(
                    "director-pnf-gestion-carsce-fila-seleccionable"
                );

                const valores = [
                    index + 1,
                    pnf.pnf,
                    pnf.codigo,
                    pnf.periodo_academico
                ];

                valores.forEach(valor => {

                    const celda = document.createElement("td");

                    celda.textContent = valor;

                    fila.appendChild(celda);

                });

                fila.addEventListener("click", async () => {

                    document.querySelectorAll(
                        ".director-pnf-gestion-carsce-fila-seleccionable"
                    ).forEach(fila => {
                        fila.classList.remove("fila-seleccionada");
                    });

                    fila.classList.add("fila-seleccionada");

                    if (typeof window.seleccionarPNF === "function") {
                        await window.seleccionarPNF(pnf.codigo);
                    }

                });

                tbody.appendChild(fila);

            });

        } catch (error) {

            console.error("Error cargando PNFs:", error);

            tbody.innerHTML = `
                <tr>
                    <td colspan="4">
                        Error al consultar los programas registrados.
                    </td>
                </tr>
            `;

        }

    }

    // =========================================
    // EXPONER FUNCIÓN PARA ACTUALIZAR LA TABLA
    // =========================================

    window.cargarPNFs = cargarPNFs;

    cargarPNFs();

});