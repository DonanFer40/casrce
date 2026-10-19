document.addEventListener("DOMContentLoaded", function () {

    /* =====================================================
       CONTRASEÑA PRINCIPAL
    ===================================================== */

    const toggleCheck = document.getElementById("oculta_aparecer");
    const inputPassword = document.getElementById("password");
    const eyeOn = document.querySelector(".AccesoInstitucionalCASRCE-ojo-off");
    const eyeOff = document.querySelector(".AccesoInstitucionalCASRCE-ojo-on");

    /* =====================================================
       CONFIRMACIÓN DE CONTRASEÑA
    ===================================================== */
    
    const toggleCheckConfirm = document.getElementById("oculta_aparecer-confirm");
    const inputPasswordConfirm = document.getElementById("confirm-password");
    const eyeOnConfirm = document.querySelector(".AccesoInstitucionalCASRCE-ojo-off-confirm");
    const eyeOffConfirm = document.querySelector(".AccesoInstitucionalCASRCE-ojo-on-confirm");

    /* =====================================================
       MOSTRAR / OCULTAR CONTRASEÑA PRINCIPAL
    ===================================================== */

    function actualizarPassword() {
        if (!toggleCheck || !inputPassword || !eyeOn || !eyeOff) {
            return;
        }

        if (toggleCheck.checked) {
            inputPassword.type = "text";
            eyeOn.classList.add("ocultar");
            eyeOff.classList.remove("ocultar");
        } else {
            inputPassword.type = "password";
            eyeOn.classList.remove("ocultar");
            eyeOff.classList.add("ocultar");
        }
    }


    /* =====================================================
       MOSTRAR / OCULTAR CONFIRMACIÓN
    ===================================================== */

    function actualizarPasswordConfirm() {
        if (!toggleCheckConfirm || !inputPasswordConfirm || !eyeOnConfirm || !eyeOffConfirm) {
            return;
        }

        if (toggleCheckConfirm.checked) {
            inputPasswordConfirm.type = "text";
            eyeOnConfirm.classList.add("ocultar");
            eyeOffConfirm.classList.remove("ocultar");
        } else {
            inputPasswordConfirm.type = "password";
            eyeOnConfirm.classList.remove("ocultar");
            eyeOffConfirm.classList.add("ocultar");
        }
    }


    /* =====================================================
       EVENTOS
    ===================================================== */

    if (toggleCheck) {
        toggleCheck.addEventListener("change",actualizarPassword);
    }

    if (toggleCheckConfirm) {
        toggleCheckConfirm.addEventListener("change",actualizarPasswordConfirm);
    }

    /* =====================================================
       ESTADO INICIAL
    ===================================================== */

    actualizarPassword();
    actualizarPasswordConfirm();

});
