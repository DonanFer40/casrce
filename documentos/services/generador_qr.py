"""Utilidades centralizadas para códigos QR de documentos CASRCE."""
from io import BytesIO

import qrcode
from qrcode.constants import ERROR_CORRECT_M

def generar_qr_png(datos, *, box_size=8, border=2):
    """Devuelve el QR como bytes PNG, listo para incrustar en un PDF."""
    if not datos:
        raise ValueError("Se requiere un contenido para generar el código QR.")

    qr = qrcode.QRCode(
        version=None,
        error_correction=ERROR_CORRECT_M,
        box_size=box_size,
        border=border,
    )
    qr.add_data(str(datos))
    qr.make(fit=True)

    imagen = qr.make_image(fill_color="#0F172A", back_color="#FFFFFF")
    buffer = BytesIO()
    imagen.save(buffer, format="PNG")
    return buffer.getvalue()
