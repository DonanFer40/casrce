from django.core.exceptions import ValidationError


PASSWORD_POLICY_MESSAGE = (
    "La contraseña debe tener al menos 8 caracteres e incluir una mayúscula, "
    "una minúscula, un número y un símbolo."
)


def validar_contrasenia_segura(contrasenia):
    if (
        len(contrasenia) < 8
        or not any(caracter.isupper() for caracter in contrasenia)
        or not any(caracter.islower() for caracter in contrasenia)
        or not any(caracter.isdecimal() for caracter in contrasenia)
        or not any(
            not caracter.isalnum() and not caracter.isspace()
            for caracter in contrasenia
        )
    ):
        raise ValidationError(PASSWORD_POLICY_MESSAGE)
    return contrasenia
