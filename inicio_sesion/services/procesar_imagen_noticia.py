from io import BytesIO
from pathlib import Path

from PIL import Image, ImageOps
from django.core.files.base import ContentFile


ANCHO_NOTICIA = 1080
ALTO_NOTICIA = 1350
CALIDAD_JPEG = 85


def procesar_imagen_noticia(imagen):
    """
    Procesa una imagen para las noticias de CARSCE.

    - Corrige la orientación EXIF.
    - Recorta proporcionalmente a formato 4:5.
    - Redimensiona a 1080x1350 px.
    - Convierte a JPEG.
    - Comprime con calidad 85.
    - No deforma la imagen original.
    """

    imagen_original = Image.open(imagen)

    # Corregir orientación de fotografías tomadas desde móviles
    imagen_original = ImageOps.exif_transpose(imagen_original)

    # Convertir a RGB para poder guardar correctamente como JPEG
    if imagen_original.mode != "RGB":
        fondo = Image.new(
            "RGB",
            imagen_original.size,
            (255, 255, 255)
        )

        if "A" in imagen_original.getbands():
            fondo.paste(
                imagen_original,
                mask=imagen_original.getchannel("A")
            )
        else:
            fondo.paste(imagen_original)

        imagen_original = fondo

    ancho_original, alto_original = imagen_original.size

    proporcion_objetivo = ANCHO_NOTICIA / ALTO_NOTICIA
    proporcion_original = ancho_original / alto_original

    # =====================================================
    # RECORTE CENTRAL 4:5
    # =====================================================

    if proporcion_original > proporcion_objetivo:
        # La imagen es demasiado horizontal.
        # Se recortan los laterales.

        nuevo_ancho = int(
            alto_original * proporcion_objetivo
        )

        izquierda = (
            ancho_original - nuevo_ancho
        ) // 2

        derecha = izquierda + nuevo_ancho

        imagen_original = imagen_original.crop(
            (
                izquierda,
                0,
                derecha,
                alto_original
            )
        )

    elif proporcion_original < proporcion_objetivo:
        # La imagen es demasiado vertical.
        # Se recorta la parte superior/inferior.

        nuevo_alto = int(
            ancho_original / proporcion_objetivo
        )

        arriba = (
            alto_original - nuevo_alto
        ) // 2

        abajo = arriba + nuevo_alto

        imagen_original = imagen_original.crop(
            (
                0,
                arriba,
                ancho_original,
                abajo
            )
        )

    # =====================================================
    # REDIMENSIONAMIENTO
    # =====================================================

    imagen_final = imagen_original.resize(
        (
            ANCHO_NOTICIA,
            ALTO_NOTICIA
        ),
        Image.Resampling.LANCZOS
    )

    # =====================================================
    # GUARDAR COMO JPEG
    # =====================================================

    archivo = BytesIO()

    imagen_final.save(
        archivo,
        format="JPEG",
        quality=CALIDAD_JPEG,
        optimize=True,
        progressive=True
    )

    archivo.seek(0)

    nombre_original = Path(imagen.name).stem

    nombre_final = f"{nombre_original}.jpg"

    return ContentFile(
        archivo.read(),
        name=nombre_final
    )   