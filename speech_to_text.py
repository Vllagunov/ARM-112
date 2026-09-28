# ==========================================================
# Файл: speech_to_text.py
# Проект: TOES 112 / AELIN
# Версия: 2.0
# Дата: 27.09.2026
#
# Назначение:
# Запись речи с микрофона и распознавание
# через OpenAI Whisper.
# ==========================================================

import os
import tempfile

import sounddevice as sd
import soundfile as sf
import whisper


class SpeechToText:

    def __init__(self):

        print("=" * 60)
        print("Загрузка Whisper...")
        print("=" * 60)

        self.model = whisper.load_model("base")

        print("Whisper готов.")
        print("=" * 60)

    # ------------------------------------------------------

    def record(self, seconds=5):

        samplerate = 16000

        print()
        print("Говорите...")
        print()

        audio = sd.rec(
            int(seconds * samplerate),
            samplerate=samplerate,
            channels=1,
            dtype="float32"
        )

        sd.wait()

        filename = tempfile.mktemp(".wav")

        sf.write(
            filename,
            audio,
            samplerate
        )

        return filename

    # ------------------------------------------------------

    def recognize(self, filename):

        result = self.model.transcribe(
            filename,
            language="ru"
        )

        try:
            os.remove(filename)
        except:
            pass

        return result["text"].strip()

    # ------------------------------------------------------

    def listen(self, seconds=5):

        filename = self.record(seconds)

        return self.recognize(filename)


# ==========================================================

if __name__ == "__main__":

    stt = SpeechToText()

    text = stt.listen(5)

    print()
    print("=" * 60)
    print("Распознано:")
    print(text)
    print("=" * 60)