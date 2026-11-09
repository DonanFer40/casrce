document.addEventListener("DOMContentLoaded", () => {
    const botonCerrar = document.querySelector(".navegacion-autenticada-carsce-cerrar");

    if (botonCerrar) {
        botonCerrar.addEventListener("click", (e) => {
            e.preventDefault(); 
            NotificacionesCASRCE.cargar("Cerrando sesión...");
            const urlDestino = botonCerrar.href;
            setTimeout(() => {
                window.CASRCE_TAB_NAVIGATE(urlDestino);
            }, 1200);
        });
    }
});