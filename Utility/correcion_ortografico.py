
from pathlib import Path
from spylls.hunspell import Dictionary


# Ruta del diccionario español
RUTA_DICCIONARIO = (
    Path(__file__).resolve().parent.parent
    / "Diccionarios"
    / "es_ES"
)

# Cargar el diccionario una sola vez
corrector = Dictionary.from_files(str(RUTA_DICCIONARIO))


def palabra_correcta(palabra):
    """
    Comprueba si una palabra está correctamente escrita.
    """
    return corrector.lookup(palabra)


def obtener_sugerencias(palabra):
    """
    Devuelve posibles correcciones para una palabra.
    """
    return corrector.suggest(palabra)
