import io
import unittest
import wave

import numpy as np

from voice.stt import wav_a_muestras


def hacer_wav(muestras_int16, frecuencia=16000, canales=1):
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(canales)
        wav.setsampwidth(2)
        wav.setframerate(frecuencia)
        wav.writeframes(np.asarray(muestras_int16, dtype=np.int16).tobytes())
    return buffer.getvalue()


class TestWavAMuestras(unittest.TestCase):

    def test_wav_16k_mono_se_convierte_directo(self):
        muestras = wav_a_muestras(hacer_wav([0, 16384, -32768, 32767]))
        self.assertEqual(muestras.dtype, np.float32)
        np.testing.assert_allclose(muestras, [0.0, 0.5, -1.0, 32767 / 32768], rtol=1e-6)

    def test_otros_formatos_van_al_decodificador(self):
        self.assertIsNone(wav_a_muestras(hacer_wav([0] * 10, frecuencia=48000)))
        self.assertIsNone(wav_a_muestras(hacer_wav([0] * 10, canales=2)))
        self.assertIsNone(wav_a_muestras(b"\x1aE\xdf\xa3webm..."))
        self.assertIsNone(wav_a_muestras(b"RIFF basura"))


if __name__ == "__main__":
    unittest.main()
