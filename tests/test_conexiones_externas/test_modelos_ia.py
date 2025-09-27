
import unittest, os
from codigo.conexiones_externas.modelos_ia import ModelosIa

class TestModelosIa(unittest.TestCase):

    def setUp(self):
        self.modelos_ia = ModelosIa()
        self.archivo_audio = os.environ["TEMPORAL_PATH"] + "test_a1.mp3"

    def test_a1_generar_audio(self):
        salida_modelo = self.modelos_ia.tts.llamar("Hola, mucho gusto",self.archivo_audio,"es")
        self.assertIsInstance(salida_modelo, dict)
        self.assertEqual(salida_modelo["status"],200,str(salida_modelo))

    def test_a2_trasncribir_audio_archivo(self):
        salida_modelo = self.modelos_ia.asr.llamar(self.archivo_audio)
        self.assertIsInstance(salida_modelo, dict)
        self.assertEqual(salida_modelo["status"],200,str(salida_modelo))

    def test_a3_trasncribir_audio_binario(self):
        with open(self.archivo_audio, "rb") as f:
            archivo_binario = f.read()
        salida_modelo = self.modelos_ia.asr.llamar(archivo_binario,True)
        self.assertIsInstance(salida_modelo, dict)
        self.assertEqual(salida_modelo["status"],200,str(salida_modelo))


    def test_a4_traducir_texto(self):
        salida_modelo = self.modelos_ia.llm.manejar_chat("Eres un traductor a ingles",[],"me llamo carlos")
        self.assertIsInstance(salida_modelo, dict)
        self.assertEqual(salida_modelo["status"],200,str(salida_modelo))
        
if __name__ == '__main__':
    unittest.main()