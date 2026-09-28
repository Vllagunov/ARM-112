# ==========================================================
# Файл: text_to_speech.py
# Проект: TOES 112 / AELIN
# Версия: 1.1
# Дата: 26.09.2026
#
# Назначение:
# Озвучивание текста через pyttsx3.
#
# Важно:
# Движок pyttsx3 создаётся и используется в одном и том же
# потоке. Это устраняет зависание SAPI5 при вызове из
# фонового потока ARM112.
# ==========================================================

import pyttsx3


class TextToSpeech:

    def __init__(self):
        # Не создаём pyttsx3 здесь.
        # Движок должен быть создан в том потоке, где он работает.
        self.rate = 180
        self.volume = 1.0

    # =====================================================

    def say(self, text):

        if not text:
            return

        print("Озвучивание:", text, flush=True)

        engine = None

        try:
            # Создание и использование SAPI5 в одном потоке.
            engine = pyttsx3.init()

            engine.setProperty("rate", self.rate)
            engine.setProperty("volume", self.volume)

            engine.say(text)
            engine.runAndWait()

            print("Озвучивание завершено.", flush=True)

        finally:
            if engine is not None:
                try:
                    engine.stop()
                except Exception:
                    pass


# =========================================================

if __name__ == "__main__":

    tts = TextToSpeech()

    tts.say(
        "Здравствуйте. Проверка модуля озвучивания "
        "завершена успешно."
    )
