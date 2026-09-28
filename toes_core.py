
# ==========================================================
# Файл: toes_core.py
# Проект: TOES 112
# Версия: 0.7 от 27.09.26
# Назначение:
# Голосовой тренажёр оператора 112.
#
# Контур:
# микрофон → Whisper → ScenarioEngine
#                     ↓
#              GigaChat (опционально)
#                     ↓
#                    TTS
#
# ScenarioEngine является источником фактов.
# GigaChat только добавляет эмоциональность.
#
# ВАЖНО:
# GigaChat не имеет права изменять фактический ответ.
# Если исходный ответ изменён — используется оригинал.
# ==========================================================

import os
import re
import time

import sounddevice as sd
from scipy.io.wavfile import write
from faster_whisper import WhisperModel
import pyttsx3

from gigachat_client import GigaChatClient
from scenario_engine import ScenarioEngine


SAMPLE_RATE = 16000
DURATION = 3

# True  — использовать GigaChat для эмоциональной речи
# False — говорить непосредственно ответ ScenarioEngine
GIGACHAT_EMOTION = True


SCENARIO_FILE = os.path.join(
    "scenarios",
    "training",
    "fire_apartment.txt"
)


if not os.path.exists(SCENARIO_FILE):

    print("ОШИБКА:")
    print("Файл сценария не найден:")
    print(SCENARIO_FILE)

    raise SystemExit(1)


print("Загрузка Whisper...")


model = WhisperModel(
    "base",
    compute_type="int8"
)


engine = pyttsx3.init()
engine.setProperty("rate", 190)


scenario_engine = ScenarioEngine()


if GIGACHAT_EMOTION:
    ai = GigaChatClient()
else:
    ai = None


def clean(text):

    text = text.lower().strip()

    return re.sub(
        r"[^a-zа-яё0-9 ]",
        "",
        text
    )


def speak(text):

    print()
    print("TOES:", text)
    print()

    engine.say(text)
    engine.runAndWait()

    time.sleep(0.4)


def show_hint():

    hint = scenario_engine.get_hint()

    if hint is None:
        return

    print()
    print("ПОДСКАЗКА:", hint)
    print()

    speak(
        "Подсказка. " + hint
    )


def is_stop_command(text):

    """
    Устойчивое распознавание команды завершения.

    Например:

    стоп
    стоп стоп
    пожалуйста стоп
    выход
    выход выход
    """

    words = text.lower().split()

    if "стоп" in words:
        return True

    if "выход" in words:
        return True

    return False


def is_call_acceptance(text):

    """
    Распознавание принятия входящего вызова.

    Основная фраза оператора:
    «Служба 112 слушаю».

    Также принимается естественный вариант:
    «Слушаю службу 112».

    Проверка выполняется после clean(), поэтому регистр
    и знаки препинания значения не имеют.
    """

    normalized = clean(text)

    accepted_phrases = (
        "служба 112 слушаю",
        "слушаю службу 112",
    )

    return any(phrase in normalized for phrase in accepted_phrases)


def listen_and_recognize():

    """Записать короткую реплику и вернуть распознанный текст."""

    audio = sd.rec(
        int(DURATION * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="int16"
    )

    sd.wait()

    write(
        "temp.wav",
        SAMPLE_RATE,
        audio
    )

    segments, _ = model.transcribe(
        "temp.wav",
        language="ru"
    )

    return clean(
        " ".join(
            s.text for s in segments
        )
    )


def wait_for_call_acceptance():

    """
    Ожидать принятия входящего вызова оператором.

    Сценарий не начинается, пока оператор не произнесёт
    фразу принятия вызова.
    """

    prompt = (
        'Примите звонок и скажите: «Служба 112 слушаю».'
    )

    speak(prompt)

    while True:

        print()
        print("Ожидание принятия вызова...")
        print()

        text = listen_and_recognize()

        print(
            "Оператор:",
            text
        )

        if text == "":
            speak(prompt)
            continue

        if is_stop_command(text):

            speak(
                "Работа завершена."
            )

            return False

        if is_call_acceptance(text):

            speak(
                "Вызов принят."
            )

            return True

        speak(prompt)


def make_emotional_answer(answer):

    """
    GigaChat может сделать реплику более естественной,
    но исходный фактический ответ должен сохраниться
    ДОСЛОВНО.

    Пример:

    Исходный ответ:
    "Возможно, внутри находится пожилая женщина."

    Допустимо:
    "Помогите, пожалуйста! Возможно, внутри находится
    пожилая женщина."

    Недопустимо:
    "Там застряла бабушка, ей нужна помощь."

    Если GigaChat изменил исходный ответ,
    функция возвращает исходный ответ без изменений.
    """

    prompt = f"""
Ты помогаешь озвучивать реплику заявителя
в тренировочном сценарии оператора 112.

ИСХОДНЫЙ ОТВЕТ СИСТЕМЫ:

{answer}

ТВОЯ ЗАДАЧА:

Сделать реплику немного более естественной
и эмоциональной.

КРИТИЧЕСКОЕ ПРАВИЛО:

Исходный ответ должен присутствовать
в твоём ответе ДОСЛОВНО, без единого изменения.

Нельзя:
- менять слова;
- менять порядок слов внутри исходного ответа;
- менять числа;
- менять адрес;
- менять степень уверенности;
- добавлять новые факты;
- добавлять новых людей;
- добавлять пострадавших;
- добавлять новые события;
- добавлять новые места;
- усиливать или ослаблять утверждение.

Разрешено только:

- добавить короткую эмоциональную фразу ДО исходного ответа;
- добавить короткую эмоциональную фразу ПОСЛЕ исходного ответа.

Например:

"Помогите, пожалуйста! {answer}"

или:

"{answer} Помогите скорее!"

Но {answer} должен остаться
АБСОЛЮТНО БЕЗ ИЗМЕНЕНИЙ.

Ответ должен быть одной короткой репликой.
"""

    try:

        result = ai.ask(prompt)

        if not result:
            return answer

        result = result.strip()

        # --------------------------------------------------
        # ЗАЩИТА ОТ ИЗМЕНЕНИЯ ФАКТОВ
        #
        # Если исходный ответ не содержится в ответе
        # GigaChat ДОСЛОВНО — результат отбрасывается.
        # --------------------------------------------------

        if answer not in result:

            print()
            print(
                "GigaChat изменил фактический ответ."
            )
            print(
                "Используется исходный ответ ScenarioEngine."
            )
            print()

            return answer

        # --------------------------------------------------
        # Дополнительная проверка:
        # исходный ответ должен встречаться ровно один раз.
        # --------------------------------------------------

        if result.count(answer) != 1:

            print()
            print(
                "GigaChat некорректно повторил ответ."
            )
            print(
                "Используется исходный ответ ScenarioEngine."
            )
            print()

            return answer

        return result

    except Exception as error:

        print()
        print("Ошибка GigaChat:")
        print(error)
        print()

        return answer


print("=" * 60)
print("TOES 112")
print("РЕЖИМ: ТРЕНИРОВКА")
print("СЦЕНАРИЙ: ПОЖАР В КВАРТИРЕ")
print("=" * 60)


if GIGACHAT_EMOTION:

    print(
        "ЭМОЦИОНАЛЬНЫЙ РЕЖИМ: ВКЛ"
    )

else:

    print(
        "ЭМОЦИОНАЛЬНЫЙ РЕЖИМ: ВЫКЛ"
    )


speak(
    "Система готова."
)


# --------------------------------------------------
# ПРИЁМ ВХОДЯЩЕГО ВЫЗОВА
# До принятия вызова сценарий не начинается.
# --------------------------------------------------

if not wait_for_call_acceptance():
    raise SystemExit(0)


show_hint()


while True:

    print()
    print("Слушаю...")
    print()

    text = listen_and_recognize()


    print(
        "Оператор:",
        text
    )


    if text == "":
        continue


    # --------------------------------------------------
    # Команда остановки проверяется ДО ScenarioEngine.
    # --------------------------------------------------

    if is_stop_command(text):

        speak(
            "Работа завершена."
        )

        break


    result = scenario_engine.process(text)


    if not result["success"]:

        speak(
            "Действие не определено."
        )

        show_hint()

        continue


    speak(
        "Действие принято."
    )


    answer = result["answer"]


    if answer:

        if GIGACHAT_EMOTION:

            answer = make_emotional_answer(
                answer
            )

        speak(answer)


    if result["done"]:

        speak(
            "Сценарий завершён."
        )

        break


    show_hint()

