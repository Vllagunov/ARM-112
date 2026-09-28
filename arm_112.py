# ==========================================================
# Файл: arm_112.py
# Проект: TOES 112
# Версия: 0.5 от 27.09.26
# Назначение: АРМ оператора 112
#
# ГОВОРИТЬ -> Whisper -> ScenarioEngine -> АРМ
# ==========================================================

import tkinter as tk
from datetime import datetime
import threading
import os
import re

from speech_to_text import SpeechToText
from scenario_engine import ScenarioEngine
from text_to_speech import TextToSpeech
from gigachat_client import GigaChatClient


class ARM112(tk.Tk):

    def __init__(self):
        super().__init__()

        self.title("АРМ ОПЕРАТОРА 112 — TOES 112")
        self.geometry("1400x850")
        self.minsize(1100, 700)
        self.configure(bg="#e9edf2")

        self.call_state = tk.StringVar(value="ОЖИДАНИЕ")
        self.system_state = tk.StringVar(value="НОРМА")
        self.ai_state = tk.StringVar(value="ИИ: ГОТОВ")
        self.gigachat_state = tk.StringVar(value="GigaChat: НЕ ПРОВЕРЕН")
        self.call_timer = tk.StringVar(value="00:00")

        self.incident = tk.StringVar(value="—")
        self.address = tk.StringVar(value="—")
        self.people = tk.StringVar(value="—")
        self.threat = tk.StringVar(value="—")

        self.applicant_name = tk.StringVar(value="—")
        self.applicant_phone = tk.StringVar(value="—")

        self.hint_text = tk.StringVar(
            value="Ожидание входящего вызова."
        )

        self.questions = [
            "Что произошло?",
            "Где произошло?",
            "Есть ли люди внутри?",
            "Есть ли пострадавшие?",
            "Где находится очаг пожара?",
            "Какова степень задымления?",
        ]

        self.question_labels = []
        self.current_question = 0

        self.call_active = False
        self.call_seconds = 0
        self.listening = False
        self.speaking = False
        self.tts_lock = threading.Lock()
        self.ringing = False
        self.tts = None
        self.gigachat = None
        self.call_greeting_accepted = False

        self.log_dir = os.path.join(os.path.dirname(__file__), "logs")
        os.makedirs(self.log_dir, exist_ok=True)
        self.log_file = os.path.join(self.log_dir, "arm_112.log")

        self.engine = None
        self.stt = None

        self.build_interface()
        self.update_clock()

        # Имитация поступления вызова после запуска АРМ.
        self.after(1200, self.simulate_incoming_call)

    # ======================================================
    # ИНТЕРФЕЙС
    # ======================================================

    def build_interface(self):

        top = tk.Frame(
            self,
            bg="#263238",
            height=58
        )
        top.pack(fill="x")
        top.pack_propagate(False)

        tk.Label(
            top,
            text="АРМ ОПЕРАТОРА 112",
            font=("Arial", 20, "bold"),
            fg="white",
            bg="#263238"
        ).pack(side="left", padx=18)

        tk.Label(
            top,
            text="ВЫЗОВ №0001",
            font=("Arial", 12),
            fg="white",
            bg="#263238"
        ).pack(side="left", padx=30)

        tk.Label(
            top,
            textvariable=self.system_state,
            font=("Arial", 12, "bold"),
            fg="white",
            bg="#263238"
        ).pack(side="right", padx=20)

        self.clock_label = tk.Label(
            top,
            font=("Arial", 12),
            fg="white",
            bg="#263238"
        )
        self.clock_label.pack(side="right", padx=10)

        main = tk.Frame(
            self,
            bg="#e9edf2"
        )
        main.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=10
        )

        left = tk.Frame(
            main,
            bg="#e9edf2",
            width=360
        )
        left.pack(
            side="left",
            fill="y",
            padx=(0, 8)
        )
        left.pack_propagate(False)

        self.make_call_panel(left)
        self.make_applicant_panel(left)
        self.make_questions_panel(left)
        self.make_hint_panel(left)

        right = tk.Frame(
            main,
            bg="#e9edf2"
        )
        right.pack(
            side="left",
            fill="both",
            expand=True
        )

        self.make_incident_panel(right)
        self.make_map_panel(right)
        self.make_journal_panel(right)

        status = tk.Frame(
            self,
            bg="#cfd8dc",
            height=34
        )
        status.pack(fill="x")
        status.pack_propagate(False)

        tk.Label(
            status,
            textvariable=self.ai_state,
            font=("Arial", 10, "bold"),
            bg="#cfd8dc"
        ).pack(side="left", padx=15)

        tk.Label(
            status,
            textvariable=self.gigachat_state,
            font=("Arial", 10, "bold"),
            bg="#cfd8dc"
        ).pack(side="left", padx=15)

        self.whisper_status = tk.Label(
            status,
            text="Whisper: READY",
            font=("Arial", 10),
            bg="#cfd8dc"
        )
        self.whisper_status.pack(side="left", padx=15)

        tk.Label(
            status,
            text="Audio: READY",
            font=("Arial", 10),
            bg="#cfd8dc"
        ).pack(side="left", padx=15)

        tk.Label(
            status,
            text="ScenarioEngine: READY",
            font=("Arial", 10),
            bg="#cfd8dc"
        ).pack(side="left", padx=15)

    # ======================================================
    # ЗАГОЛОВОК ПАНЕЛИ
    # ======================================================

    def panel_title(self, parent, text):

        tk.Label(
            parent,
            text=text,
            font=("Arial", 13, "bold"),
            bg="white",
            anchor="w",
            padx=10,
            pady=7
        ).pack(fill="x")

    # ======================================================
    # ВЫЗОВ
    # ======================================================

    def make_call_panel(self, parent):

        frame = tk.Frame(
            parent,
            bg="white",
            bd=1,
            relief="solid"
        )
        frame.pack(
            fill="x",
            pady=(0, 8)
        )

        self.panel_title(
            frame,
            "ВХОДЯЩИЙ ВЫЗОВ"
        )

        tk.Label(
            frame,
            textvariable=self.call_state,
            font=("Arial", 18, "bold"),
            bg="white",
            pady=8
        ).pack()

        tk.Label(
            frame,
            textvariable=self.call_timer,
            font=("Arial", 24),
            bg="white"
        ).pack(pady=3)

        buttons = tk.Frame(
            frame,
            bg="white"
        )
        buttons.pack(pady=10)

        tk.Button(
            buttons,
            text="ПРИНЯТЬ ВЫЗОВ",
            font=("Arial", 11, "bold"),
            command=self.accept_call,
            width=16
        ).pack(side="left", padx=5)

        tk.Button(
            buttons,
            text="ЗАВЕРШИТЬ",
            font=("Arial", 11),
            command=self.end_call,
            width=12
        ).pack(side="left", padx=5)

        self.speak_button = tk.Button(
            frame,
            text="🎙 ГОВОРИТЬ",
            font=("Arial", 12, "bold"),
            command=self.start_listening,
            width=20,
            height=2
        )
        self.speak_button.pack(pady=(0, 8))

        tk.Button(
            frame,
            text="▶ ТЕСТ СЦЕНАРИЯ",
            font=("Arial", 10, "bold"),
            command=self.run_test_scenario
        ).pack(pady=(0, 10))

    # ======================================================
    # ЗАЯВИТЕЛЬ
    # ======================================================

    def make_applicant_panel(self, parent):

        frame = tk.Frame(
            parent,
            bg="white",
            bd=1,
            relief="solid"
        )
        frame.pack(
            fill="x",
            pady=(0, 8)
        )

        self.panel_title(
            frame,
            "ЗАЯВИТЕЛЬ"
        )

        data = tk.Frame(
            frame,
            bg="white"
        )
        data.pack(
            fill="x",
            padx=10,
            pady=8
        )

        tk.Label(
            data,
            text="Имя:",
            bg="white"
        ).grid(row=0, column=0, sticky="w")

        tk.Label(
            data,
            textvariable=self.applicant_name,
            bg="white"
        ).grid(row=0, column=1, sticky="w")

        tk.Label(
            data,
            text="Телефон:",
            bg="white"
        ).grid(row=1, column=0, sticky="w")

        tk.Label(
            data,
            textvariable=self.applicant_phone,
            bg="white"
        ).grid(row=1, column=1, sticky="w")

    # ======================================================
    # ВОПРОСЫ
    # ======================================================

    def make_questions_panel(self, parent):

        frame = tk.Frame(
            parent,
            bg="white",
            bd=1,
            relief="solid"
        )
        frame.pack(
            fill="both",
            expand=True,
            pady=(0, 8)
        )

        self.panel_title(
            frame,
            "КОНТРОЛЬНЫЕ ВОПРОСЫ"
        )

        for question in self.questions:

            label = tk.Label(
                frame,
                text="□ " + question,
                font=("Arial", 11),
                bg="white",
                anchor="w",
                padx=12,
                pady=6
            )

            label.pack(fill="x")
            self.question_labels.append(label)

    # ======================================================
    # ПОДСКАЗКА
    # ======================================================

    def make_hint_panel(self, parent):

        frame = tk.Frame(
            parent,
            bg="#fff8e1",
            bd=1,
            relief="solid"
        )
        frame.pack(fill="x")

        tk.Label(
            frame,
            text="ПОДСКАЗКА ОПЕРАТОРУ",
            font=("Arial", 11, "bold"),
            bg="#fff8e1",
            anchor="w",
            padx=10,
            pady=6
        ).pack(fill="x")

        tk.Label(
            frame,
            textvariable=self.hint_text,
            font=("Arial", 11),
            bg="#fff8e1",
            wraplength=320,
            justify="left",
            anchor="w",
            padx=10,
            pady=10
        ).pack(fill="x")

    # ======================================================
    # КАРТОЧКА ПРОИСШЕСТВИЯ
    # ======================================================

    def make_incident_panel(self, parent):

        frame = tk.Frame(
            parent,
            bg="white",
            bd=1,
            relief="solid"
        )
        frame.pack(
            fill="x",
            pady=(0, 8)
        )

        self.panel_title(
            frame,
            "КАРТОЧКА ПРОИСШЕСТВИЯ"
        )

        data = tk.Frame(
            frame,
            bg="white"
        )
        data.pack(
            fill="x",
            padx=12,
            pady=10
        )

        rows = [
            ("Тип происшествия:", self.incident),
            ("Адрес:", self.address),
            ("Люди внутри:", self.people),
            ("Угроза:", self.threat),
        ]

        for row, (title, variable) in enumerate(rows):

            tk.Label(
                data,
                text=title,
                font=("Arial", 11, "bold"),
                bg="white",
                anchor="nw"
            ).grid(
                row=row,
                column=0,
                sticky="nw",
                padx=(0, 10),
                pady=3
            )

            tk.Label(
                data,
                textvariable=variable,
                font=("Arial", 11),
                bg="white",
                anchor="nw",
                justify="left",
                wraplength=650
            ).grid(
                row=row,
                column=1,
                sticky="nw",
                pady=3
            )

    # ======================================================
    # КАРТА
    # ======================================================

    def make_map_panel(self, parent):

        frame = tk.Frame(
            parent,
            bg="white",
            bd=1,
            relief="solid"
        )
        frame.pack(
            fill="both",
            expand=True,
            pady=(0, 8)
        )

        self.panel_title(
            frame,
            "КАРТА"
        )

        self.map_area = tk.Frame(
            frame,
            bg="#dfe5e8"
        )
        self.map_area.pack(
            fill="both",
            expand=True,
            padx=8,
            pady=8
        )

        self.map_label = tk.Label(
            self.map_area,
            text="ОЖИДАНИЕ АДРЕСА",
            font=("Arial", 18, "bold"),
            bg="#dfe5e8",
            fg="#607d8b"
        )
        self.map_label.place(
            relx=0.5,
            rely=0.5,
            anchor="center"
        )
    # ======================================================
    # ЖУРНАЛ
    # ======================================================

    def make_journal_panel(self, parent):

        frame = tk.Frame(
            parent,
            bg="white",
            bd=1,
            relief="solid"
        )
        frame.pack(fill="x")

        self.panel_title(frame, "ЖУРНАЛ СОБЫТИЙ")

        self.journal = tk.Text(
            frame,
            height=8,
            font=("Consolas", 10),
            bg="#fafafa",
            wrap="word"
        )
        self.journal.pack(
            fill="both",
            expand=True,
            padx=8,
            pady=8
        )

        self.journal.configure(state="disabled")

    # ======================================================
    # ЖУРНАЛИРОВАНИЕ
    # ======================================================

    def log(self, message):

        timestamp = datetime.now().strftime("%H:%M:%S")
        line = f"[{timestamp}] {message}"
        print(line, flush=True)

        self.journal.configure(state="normal")
        self.journal.insert("end", line + "\n")
        self.journal.see("end")
        self.journal.configure(state="disabled")

        try:
            with open(self.log_file, "a", encoding="utf-8") as file:
                file.write(line + "\n")
        except Exception as error:
            print(f"[LOG] Ошибка записи журнала: {error}", flush=True)

    # ======================================================
    # ЗВУКОВОЙ СИГНАЛ ВХОДЯЩЕГО ВЫЗОВА
    # ======================================================

    def play_ring(self):

        try:
            import winsound

            winsound.Beep(1000, 500)
            winsound.Beep(700, 500)

        except Exception:
            self.bell()

    def simulate_incoming_call(self):

        if self.call_active:
            return

        self.ringing = True
        self.call_state.set("ВХОДЯЩИЙ ВЫЗОВ")
        self.system_state.set("ВЫЗОВ ПОСТУПИЛ")
        self.hint_text.set(
            "Поступил входящий вызов. Нажмите «ПРИНЯТЬ ВЫЗОВ»."
        )

        self.log("[CALL] Входящий вызов 112.")

        self.ring_loop()

    def ring_loop(self):

        if not self.ringing:
            return

        self.play_ring()

        if self.ringing:
            self.after(1100, self.ring_loop)

    # ======================================================
    # ПРИНЯТИЕ ВЫЗОВА
    # ======================================================

    def accept_call(self):

        if self.call_active:
            return

        self.ringing = False
        self.call_active = True
        self.call_seconds = 0

        self.call_state.set("ВЫЗОВ ПРИНЯТ")
        self.system_state.set("ОПЕРАТОР НА ЛИНИИ")
        self.hint_text.set(
            "Соединение установлено. Говорит оператор."
        )

        self.log("[CALL] Вызов принят.")
        self.initialize_modules()

        # Сначала оператор должен принять вызов и произнести
        # установленную фразу. До этого сценарий и заявитель не запускаются.
        self.call_greeting_accepted = False
        self.speak_async(
            'Примите звонок и скажите: «Служба 112 слушаю».',
            on_done=self.start_listening
        )
        self.update_call_timer()

    def play_initial_applicant_reply(self):

        if not self.call_active or self.engine is None:
            return

        # Первый шаг сценария ещё НЕ выполняем: оператор должен сам
        # услышать инициативную реплику заявителя и спросить о происшествии.
        self.log("[CALLER] Заявитель начинает разговор.")

        base_text = (
            "Пожар в квартире. Начался пожар на кухне, сильное задымление."
        )

        self.generate_applicant_phrase(
            context=(
                "Это первая реплика заявителя при звонке 112. "
                "Он сам сообщает о пожаре до первого вопроса оператора. "
                "Факты сценария: пожар в квартире, очаг на кухне, "
                "сильное задымление. Нельзя добавлять другие факты."
            ),
            base_text=base_text,
            on_done=self.after_initial_applicant_reply
        )

    def after_initial_applicant_reply(self):
        if not self.call_active:
            return

        hint = self.engine.get_hint() if self.engine is not None else None
        if hint:
            self.hint_text.set("Подсказка: " + hint)
            self.log(f"[HINT] Голосовая подсказка: {hint}")
            self.speak_async(
                "Подсказка. " + hint,
                on_done=self.start_listening
            )
        else:
            self.start_listening()

    def generate_applicant_phrase(self, context, base_text, on_done):
        """Формирует реплику заявителя через GigaChat, не меняя факты сценария."""
        if self.gigachat is None:
            self.gigachat_state.set("GigaChat: НЕДОСТУПЕН")
            self.log("[GIGACHAT] Клиент отсутствует. Используется сценарная реплика.")
            self.speak_async(base_text, on_done=on_done)
            return

        def worker():
            try:
                prompt = (
                    "Ты играешь обычного заявителя, который звонит в службу 112. "
                    "Не являйся оператором, диспетчером или помощником. "
                    "Сформулируй короткую естественную устную реплику заявителя. "
                    "Не задавай вопросов оператору. Не давай советы. "
                    "Не добавляй ни одного факта, которого нет в исходной реплике. "
                    "Если исходная реплика содержит факты — сохрани их. "
                    "Ответ только одной репликой заявителя, без кавычек и пояснений.\n\n"
                    f"Контекст: {context}\n"
                    f"Фактическая основа: {base_text}"
                )

                self.after(0, lambda: self.gigachat_state.set("GigaChat: ЗАПРОС..."))
                self.after(0, lambda: self.log("[GIGACHAT] Запрос отправляется: формирование реплики заявителя."))
                answer = self.gigachat.ask(prompt)
                self.after(0, lambda: self.gigachat_state.set("GigaChat: ОТВЕТ ПОЛУЧЕН"))
                self.after(0, lambda: self.log("[GIGACHAT] API вернул ответ."))
                answer = str(answer or "").strip()

                if not answer:
                    answer = base_text
                    self.after(0, lambda: self.log("[GIGACHAT] Пустой ответ. Использована сценарная реплика."))
                else:
                    required_keywords = self._get_required_keywords(base_text)
                    normalized_answer = answer.lower().replace("ё", "е")
                    found_keywords = [
                        keyword for keyword in required_keywords
                        if keyword in normalized_answer
                    ]
                    missing_keywords = [
                        keyword for keyword in required_keywords
                        if keyword not in normalized_answer
                    ]

                    if missing_keywords:
                        self.after(0, lambda text=answer, missing=missing_keywords: self.log(
                            f"[GIGACHAT] ОТКЛОНЁН — не найдены ключевые слова: {missing}. "
                            f"Ответ: {text}"
                        ))
                        answer = base_text
                    else:
                        self.after(0, lambda text=answer, found=found_keywords: self.log(
                            f"[GIGACHAT] ПРИНЯТ — ключевые слова найдены: {found}. "
                            f"Ответ: {text}"
                        ))

                

                self.after(0, lambda text=answer: self._speak_generated_applicant(text, on_done))

            except Exception as error:
                error_text = f"{type(error).__name__}: {error}"
                self.after(0, lambda: self.gigachat_state.set("GigaChat: ОШИБКА ЗАПРОСА"))
                self.after(0, lambda message=error_text: self.log(f"[GIGACHAT] ОШИБКА запроса: {message}"))
                self.after(0, lambda: self._speak_generated_applicant(base_text, on_done))

        threading.Thread(target=worker, daemon=True).start()

    def _get_required_keywords(self, base_text):
        """Возвращает обязательные ключевые слова для фактов текущей реплики."""
        text = base_text.lower().replace("ё", "е")

        if "пожар начался" in text:
            return ["пожар", "кухн", "задым"]

        if "улица первомайская" in text:
            return ["москва", "первомайская", "15", "2", "48"]

        if "возможно, внутри находится" in text:
            return ["внутри", "пожил", "женщ"]

        if "информации о пострадавших" in text:
            return ["пострадав"]

        if "пожар находится" in text:
            return ["пожар", "кухн"]

        if "сильное задымление" in text:
            return ["квартир", "задым", "дым", "подъезд"]

        # Запасной вариант: требуем содержимое исходной реплики
        # только для коротких неизвестных реплик.
        return [word for word in text.split() if len(word.strip(".,!?;:")) >= 5]

    def _speak_generated_applicant(self, text, on_done):
        if not self.call_active:
            return
        self.log(f"[CALL] Заявитель: {text}")
        self.hint_text.set("Заявитель говорит...")
        self.speak_async(text, on_done=on_done)

    # ======================================================
    # ПОДКЛЮЧЕНИЕ МОДУЛЕЙ
    # ======================================================

    def initialize_modules(self):

        if self.tts is None:
            try:
                self.tts = TextToSpeech()
                self.log("[TTS] Модуль подключён.")
            except Exception as error:
                self.log(
                    f"[TTS] ОШИБКА подключения: {error}"
                )

        if self.engine is None:
            try:
                self.engine = ScenarioEngine()
                self.log("[SCENARIO] Модуль подключён.")
            except Exception as error:
                self.log(
                    f"[SCENARIO] ОШИБКА запуска: {error}"
                )

        if self.gigachat is None:
            try:
                self.gigachat = GigaChatClient(
                    system_prompt=(
                        "Ты — заявитель в учебном тренажёре 112. "
                        "Говори только от лица заявителя. "
                        "Не являйся оператором и не управляй вызовом. "
                        "Не выдумывай факты сценария. "
                        "Отвечай естественно и коротко."
                    )
                )
                self.log("[GIGACHAT] Клиент создан; доступность API ещё не проверена.")
                self.gigachat_state.set("GigaChat: КЛИЕНТ СОЗДАН")
            except Exception as error:
                self.gigachat_state.set("GigaChat: ОШИБКА ИНИЦИАЛИЗАЦИИ")
                self.log(f"[GIGACHAT] ОШИБКА инициализации: {type(error).__name__}: {error}")

        if self.stt is None:
            try:
                self.stt = SpeechToText()
                self.log("[WHISPER] Модуль подключён.")
            except Exception as error:
                self.log(
                    f"[WHISPER] ОШИБКА запуска: {error}"
                )

    # ======================================================
    # ОЗВУЧИВАНИЕ
    # ======================================================

    def speak_async(self, text, on_done=None):

        if not text:
            if on_done is not None:
                self.after(0, on_done)
            return

        if self.tts is None:
            self.log("[TTS] ОШИБКА: модуль недоступен.")
            if on_done is not None:
                self.after(0, on_done)
            return

        def worker():

            with self.tts_lock:
                self.speaking = True

                self.after(
                    0,
                    lambda: self.log(f"[TTS] Начало озвучки: {text}")
                )

                try:
                    self.tts.say(text)

                    self.after(
                        0,
                        lambda: self.log("[TTS] Озвучка завершена.")
                    )

                except Exception as error:
                    error_text = str(error)

                    self.after(
                        0,
                        lambda message=error_text: self.log(
                            f"[TTS] ОШИБКА: {message}"
                        )
                    )

                finally:
                    self.speaking = False

            # Переход к следующему состоянию выполняется даже после
            # ошибки TTS. Ошибка озвучивания не должна оставлять
            # вызов в зависшем состоянии.
            if on_done is not None and self.call_active:
                self.after(0, on_done)

        threading.Thread(
            target=worker,
            daemon=True
        ).start()

    # ======================================================
    # ТАЙМЕР ВЫЗОВА
    # ======================================================

    def update_call_timer(self):

        if not self.call_active:
            return

        minutes = self.call_seconds // 60
        seconds = self.call_seconds % 60

        self.call_timer.set(
            f"{minutes:02d}:{seconds:02d}"
        )

        self.call_seconds += 1

        self.after(1000, self.update_call_timer)

    # ======================================================
    # РАСПОЗНАВАНИЕ РЕЧИ
    # ======================================================

    def start_listening(self):

        if not self.call_active:
            self.log(
                "Сначала примите входящий вызов."
            )
            return

        # Во время реплики заявителя микрофон оператора не запускаем.
        if self.speaking:
            self.log("Сейчас говорит заявитель. Дождитесь окончания реплики.")
            return

        if self.listening:
            return

        if self.stt is None:
            self.initialize_modules()

        if self.stt is None:
            self.log(
                "Распознавание речи недоступно."
            )
            return

        self.listening = True
        self.ai_state.set("ИИ: СЛУШАЕТ")
        self.hint_text.set(
            "Говорите — сейчас распознаётся речь ОПЕРАТОРА."
        )

        self.log("[AUDIO] Запуск записи речи оператора.")
        self.log("[WHISPER] Ожидание результата распознавания.")

        threading.Thread(
            target=self.listen_worker,
            daemon=True
        ).start()

    def listen_worker(self):
        """Записывает одну реплику оператора и передаёт её в UI-поток."""
        try:
            self.after(0, lambda: self.log("[AUDIO] Запись начата."))

            recognized_text = self.stt.listen()

            self.after(0, lambda: self.log("[AUDIO] Запись завершена."))

            if isinstance(recognized_text, dict):
                recognized_text = (
                    recognized_text.get("text")
                    or recognized_text.get("transcription")
                    or ""
                )

            recognized_text = str(recognized_text or "").strip()

            self.after(
                0,
                lambda text=recognized_text:
                    self._finish_listening(text, None)
            )

        except Exception as error:
            error_text = str(error)

            self.after(
                0,
                lambda message=error_text:
                    self._finish_listening("", message)
            )

    def _finish_listening(self, text, error):
        """Сбрасывает флаг прослушивания и обрабатывает результат в UI-потоке."""
        self.listening = False
        if not self.call_active:
            return
        self.ai_state.set("ИИ: ГОТОВ")
        if error:
            self.log(f"[WHISPER] ОШИБКА: {error}")
            self.hint_text.set("Ошибка микрофона. Нажмите «ГОВОРИТЬ» для повтора.")
            return
        self.log(f"[WHISPER] Результат: {text if text else "[пусто]"}")
        self.process_recognized_text(text)

    # ======================================================
    # ОБРАБОТКА РАСПОЗНАННОГО ТЕКСТА
    # ======================================================

    def is_call_greeting(self, text):
        """Устойчиво распознаёт приветствие оператора по результату Whisper."""
        normalized = re.sub(r"[^а-яё0-9 ]", " ", str(text).lower())
        normalized = re.sub(r"\s+", " ", normalized).strip()
        words = normalized.split()

        # Whisper часто заменяет «слушаю» на «слушает/слушает» и
        # ошибается в написании номера. Достаточно услышать службу,
        # номер 112 (цифрами или словами) и близкую форму «слушаю».
        has_service = any(w.startswith(("служб", "сложб", "служив")) for w in words)
        has_listen = any(w.startswith(("слуш", "слуша", "слушае")) for w in words)
        number_forms = {"112", "сто", "двенадцать", "двенадцатый", "один", "одиннадцать"}
        has_number = any(w in number_forms for w in words)

        if has_service and has_listen and has_number:
            return True

        # Короткий ответ «Служба 112» тоже принимаем: оператор уже
        # ответил на вызов, а не должен бесконечно повторять приветствие.
        if has_service and has_number and len(words) <= 4:
            return True

        return normalized in (
            "слушаю службу",
            "слушаю",
            "служба слушаю",
            "служба слушает",
        )

    def process_recognized_text(self, text):

        if not text.strip():
            self.log("[WHISPER] Результат пустой.")
            self.hint_text.set(
                "Речь не распознана. Повторите вопрос оператору."
            )
            self.speak_async(
                "Речь не распознана. Повторите вопрос.",
                on_done=self.start_listening
            )
            return

        # Микрофон принадлежит оператору.
        self.log(f"[CALL] Оператор: {text}")

        # Первый этап: принятие вызова. До правильной фразы сценарий
        # не запускается и заявитель не начинает говорить.
        if not self.call_greeting_accepted:
            if self.is_call_greeting(text):
                self.call_greeting_accepted = True
                self.log('[CALL] Фраза «Служба 112 слушаю» распознана. Вызов принят оператором.')
                self.hint_text.set('Вызов принят. Заявитель говорит...')
                self.speak_async(
                    'Вызов принят.',
                    on_done=self.play_initial_applicant_reply
                )
            else:
                self.log('[CALL] Фраза принятия вызова не распознана.')
                self.hint_text.set(
                    'Примите звонок и скажите: «Служба 112 слушаю».'
                )
                self.speak_async(
                    'Примите звонок и скажите: «Служба 112 слушаю».',
                    on_done=self.start_listening
                )
            return

        if self.engine is None:
            self.initialize_modules()

        if self.engine is None:
            self.log("Сценарий недоступен.")
            return

        try:
            result = self.engine.process(text)
            if isinstance(result, dict):
                self.log(
                    f"[SCENARIO] Результат: success={result.get('success')}, "
                    f"step={result.get('step')}, done={result.get('done')}"
                )

            if not isinstance(result, dict):
                self.log(
                    "Сценарий вернул неожиданный результат."
                )
                return

            # Если вопрос не соответствует текущему этапу сценария,
            # заявитель не должен отвечать случайной репликой.
            if not result.get("success", False):
                hint = self.engine.get_hint()

                self.log(
                    "[SCENARIO] Вопрос не распознан или не соответствует "
                    "текущему этапу."
                )

                self.hint_text.set(
                    "Вопрос не распознан или не подходит. Повторите вопрос."
                )

                if hint:
                    self.speak_async(
                        "Вопрос не распознан или не подходит. "
                        "Повторите вопрос. Подсказка. " + hint,
                        on_done=self.start_listening
                    )
                else:
                    self.speak_async(
                        "Вопрос не распознан или не подходит. "
                        "Повторите вопрос.",
                        on_done=self.start_listening
                    )

                return

            # ScenarioEngine возвращает здесь именно ответ заявителя.
            answer = result.get("answer", "")

            if answer:
                self.generate_applicant_phrase(
                    context=(
                        f"Оператор спросил: {text}. "
                        f"Текущий этап сценария: {result.get('step')}. "
                        "Сформулируй ответ заявителя только на этот вопрос. "
                        "Не добавляй новые сведения сверх фактического ответа сценария."
                    ),
                    base_text=answer,
                    on_done=self.after_applicant_reply
                )

            else:
                hint = self.engine.get_hint()

                if hint:
                    self.hint_text.set(
                        "Подсказка: " + hint
                    )
                    self.log(f"[HINT] Голосовая подсказка: {hint}")

                    self.speak_async(
                        "Подсказка. " + hint,
                        on_done=self.start_listening
                    )
                else:
                    self.hint_text.set(
                        "Ответ заявителя не сформирован. Говорите дальше."
                    )
                    self.after(200, self.start_listening)

            facts = result.get("facts", {})

            if isinstance(facts, dict):
                self.update_incident(facts)

            if result.get("done"):
                self.hint_text.set(
                    "Сценарий завершён. Можно завершить вызов."
                )
                self.log("[SCENARIO] Сценарий завершён.")

        except Exception as e:
            self.log(
                f"[SCENARIO] ОШИБКА: {e}"
            )

    def after_applicant_reply(self):
        """После ответа заявителя озвучивает голосовую подсказку тренировки."""
        if not self.call_active:
            return

        if self.engine is not None and self.engine.current_step >= len(self.engine.steps):
            self.hint_text.set("Сценарий завершён.")
            self.log("[SCENARIO] Сценарий завершён.")
            self.speak_async(
                "Диалог завершён. Сцена окончена.",
                on_done=None
            )
            return

        hint = self.engine.get_hint() if self.engine is not None else None

        if hint:
            self.hint_text.set(
                "Подсказка: " + hint
            )
            self.log(f"[HINT] Голосовая подсказка: {hint}")

            self.speak_async(
                "Подсказка. " + hint,
                on_done=self.start_listening
            )
        else:
            self.hint_text.set(
                "Ваша очередь говорить. Задайте следующий вопрос заявителю."
            )
            self.start_listening()

    # ======================================================
    # ОБНОВЛЕНИЕ КАРТОЧКИ
    # ======================================================

    def update_incident(self, facts):

        mapping = {
            "incident": self.incident,
            "address": self.address,
            "people": self.people,
            "threat": self.threat,
            "name": self.applicant_name,
            "phone": self.applicant_phone,
        }

        for key, variable in mapping.items():
            value = facts.get(key)

            if value:
                variable.set(str(value))

    # ======================================================
    # ТЕСТ СЦЕНАРИЯ
    # ======================================================

    def run_test_scenario(self):

        if not self.call_active:
            self.log(
                "Для теста сначала примите вызов."
            )
            return

        self.log("Запуск тестового сценария.")

        self.hint_text.set(
            "Тестовый режим. Говорите в микрофон."
        )

        self.start_listening()

    # ======================================================
    # ЗАВЕРШЕНИЕ ВЫЗОВА
    # ======================================================

    def end_call(self):

        self.ringing = False
        self.call_active = False
        self.listening = False
        self.speaking = False
        self.call_greeting_accepted = False

        self.call_state.set("ВЫЗОВ ЗАВЕРШЁН")
        self.system_state.set("ОЖИДАНИЕ")
        self.ai_state.set("ИИ: ГОТОВ")

        self.hint_text.set(
            "Вызов завершён. Можно ожидать следующий."
        )

        self.log("[CALL] Вызов завершён оператором.")

        self.call_timer.set("00:00")

        self.incident.set("—")
        self.address.set("—")
        self.people.set("—")
        self.threat.set("—")
        self.applicant_name.set("—")
        self.applicant_phone.set("—")

        self.current_question = 0

        for label, question in zip(
            self.question_labels,
            self.questions
        ):
            label.configure(
                text="□ " + question
            )

        self.after(
            3000,
            self.simulate_incoming_call
        )

    # ======================================================
    # ЧАСЫ
    # ======================================================

    def update_clock(self):

        now = datetime.now().strftime(
            "%d.%m.%Y  %H:%M:%S"
        )

        self.clock_label.configure(text=now)

        self.after(
            1000,
            self.update_clock
        )


# ==========================================================
# ЗАПУСК ПРОГРАММЫ
# ==========================================================

if __name__ == "__main__":
    app = ARM112()
    app.mainloop()
