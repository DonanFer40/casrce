import re

from django.contrib.staticfiles import finders
from premailer import transform


# =========================================================
# COLORES PARA COMPATIBILIDAD CON CLIENTES DE CORREO
# =========================================================

COLORES_EMAIL = {
    "--color-azul-profundo": "#0F172A",
    "--color-azul-card": "#1E293B",
    "--color-azul-hover": "#2563EB",
    "--color-amarillo-accion": "#F59E0B",
    "--color-amarillo-hover": "#D97706",
    "--color-rojo-acento": "#DC2626",
    "--color-rojo-soft": "#FEF2F2",
    "--color-blanco": "#FFFFFF",
    "--color-fondo-pagina": "#F8FAFC",
    "--color-borde-fino": "#E2E8F0",
    "--color-borde-oscuro": "rgba(255, 255, 255, 0.1)",
    "--texto-principal": "#0F172A",
    "--texto-secundario": "#64748B",
    "--texto-claro": "#F8FAFC",
    "--texto-mutado": "#94A3B8",
    "--sombra-card": (
        "0 1px 3px rgba(0, 0, 0, 0.05), "
        "0 1px 2px rgba(0, 0, 0, 0.08)"
    ),
    "--sombra-elevada": (
        "0 10px 25px -5px rgba(15, 23, 42, 0.12), "
        "0 8px 10px -6px rgba(15, 23, 42, 0.08)"
    ),
    "--sombra-hover": "0 12px 20px -3px rgba(15, 23, 42, 0.15)",
    "--radio-card": "12px",
}


# =========================================================
# PROCESAMIENTO DEL HTML DEL CORREO
# =========================================================

def procesar_html_correo(html, css_especifico):
    """
    Incorpora al HTML las reglas CSS de la plantilla base
    y de la plantilla específica del correo.
    """

    rutas_css = [
        "Estilos/Email/base_email.css",
        css_especifico,
    ]

    reglas_css = []

    for ruta_css in rutas_css:
        archivo_css = finders.find(ruta_css)

        if not archivo_css:
            raise FileNotFoundError(
                f"No se encontró el archivo CSS: {ruta_css}"
            )

        with open(archivo_css, "r", encoding="utf-8") as archivo:
            reglas_css.append(archivo.read())

    css_completo = "\n".join(reglas_css)

    # Sustituir las variables CSS por valores concretos.
    for variable, valor in COLORES_EMAIL.items():
        css_completo = re.sub(
            re.escape(f"var({variable})"),
            lambda _: valor,
            css_completo,
        )

    # Los enlaces CSS sirven para la vista previa web,
    # pero no deben depender de ellos los estilos del correo.
    html = re.sub(
        r"<link\b(?=[^>]*\bhref\s*=\s*['\"][^'\"]*Estilos/Email/)"
        r"[^>]*>",
        "",
        html,
        flags=re.IGNORECASE,
    )

    # Incorporar las reglas CSS a los elementos HTML.
    return transform(
        html,
        css_text=css_completo,
        remove_classes=False,
        strip_important=False,
        keep_style_tags=True,
    )
