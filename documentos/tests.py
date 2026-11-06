import unittest
from io import BytesIO

from PIL import Image

from documentos.services.generador_qr import generar_qr_png


class GeneradorQRTests(unittest.TestCase):
    def test_genera_png_valido(self):
        contenido = generar_qr_png("https://example.org/documento/abc")
        imagen = Image.open(BytesIO(contenido))
        self.assertEqual(imagen.format, "PNG")
        self.assertGreater(imagen.width, 0)

    def test_rechaza_contenido_vacio(self):
        with self.assertRaises(ValueError):
            generar_qr_png("")
