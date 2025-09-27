from app import app


import unittest
import os


class TestApi(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        self.archivo_audio = os.environ["TEMPORAL_PATH"] + "test_a1.mp3"

    def test_a1_recibir_mensaje_audio(self):
        with open(self.archivo_audio, 'rb') as audio_file:
            response = self.app.post('/audio',
                                     data={
                                         'audio': (audio_file, 'test_a1.mp3')},
                                     content_type='multipart/form-data',
                                     headers={
                                         "id-usuario": "sada",
                                         "canal": "web"
                                     })
        self.assertEqual(response.status_code,200)


if __name__ == '__main__':
    unittest.main()
