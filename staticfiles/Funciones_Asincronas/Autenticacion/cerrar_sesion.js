document.addEventListener("DOMContentLoaded", () => {
    const botonCerrar = document.querySelector(".navegacion-autenticada-carsce-cerrar");

    if (botonCerrar) {
        botonCerrar.addEventListener("click", (e) => {
            e.preventDefault(); 
            NotificacionesCASRCE.cargar("Cerrando sesión...");
            const urlDestino = botonCerrar.href;
            setTimeout(() => {
                window.location.href = urlDestino;
            }, 1200);
        });
    }
});