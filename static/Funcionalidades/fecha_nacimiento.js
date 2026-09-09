document.addEventListener("DOMContentLoaded", () => {
    const fechaNacimiento = document.getElementById("fecha_nacimiento");

    if (!fechaNacimiento) return;

    const anio = new Date().getFullYear() - 18;

    fechaNacimiento.max = `${anio}-12-31`;

    fechaNacimiento.addEventListener("keydown", e => e.preventDefault());
    fechaNacimiento.addEventListener("paste", e => e.preventDefault());
});