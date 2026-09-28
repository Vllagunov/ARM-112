# ==========================================================
# Файл: scenario_engine.py
# Проект: TOES 112
# Версия: 0.5 от 27.09.26
# Назначение:
# Движок сценария. Определяет действие оператора,
# управляет контрольными точками и возвращает
# фактический ответ из данных сценария.
#
# Версия 0.5:
# Добавлена передача событий и фактов для АРМ 112.
# ==========================================================

from scenarios.training.fire_apartment_data import SCENARIO_DATA


class ScenarioEngine:

    def __init__(self):
        self.current_step = 0

        self.steps = [
            {
                "id": "incident",
                "hint": "Уточните, что произошло.",
                "patterns": [
                    "что произошло",
                    "что случилось",
                    "что у вас случилось",
                    "что у вас произошло",
                    "расскажите что произошло",
                ],
                "answer": self._incident_answer,
            },
            {
                "id": "address",
                "hint": "Уточните адрес происшествия.",
                "patterns": [
                    "адрес",
                    "где это произошло",
                    "назовите адрес",
                    "какой адрес",
                    "по какому адресу",
                ],
                "answer": self._address_answer,
            },
            {
                "id": "people",
                "hint": "Уточните, есть ли люди внутри.",
                "patterns": [
                    "есть ли люди",
                    "кто-нибудь есть",
                    "кто там",
                    "кто находится",
                    "кто в квартире",
                    "кто внутри",
                ],
                "answer": self._people_answer,
            },
            {
                "id": "victims",
                "hint": "Уточните, есть ли пострадавшие.",
                "patterns": [
                    "есть ли пострадавшие",
                    "кто-нибудь пострадал",
                    "есть пострадавшие",
                    "есть раненые",
                    "кто пострадал",
                ],
                "answer": self._victims_answer,
            },
            {
                "id": "fire_location",
                "hint": "Уточните, где находится очаг пожара.",
                "patterns": [
                    "где горит",
                    "где пожар",
                    "где находится пожар",
                    "где очаг",
                    "где находится очаг",
                ],
                "answer": self._fire_location_answer,
            },
            {
                "id": "smoke",
                "hint": "Уточните степень задымления.",
                "patterns": [
                    "есть ли дым",
                    "есть дым",
                    "сильный дым",
                    "задымление",
                    "степень задымления",
                    "насколько сильный дым",
                ],
                "answer": self._smoke_answer,
            },
        ]

        self.results = []

    def get_hint(self):
        if self.current_step >= len(self.steps):
            return None

        return self.steps[self.current_step]["hint"]

    def process(self, operator_text):
        text = operator_text.lower().strip()

        if self.current_step >= len(self.steps):
            return {
                "success": False,
                "done": True,
                "step": None,
                "answer": None,
                "event": "SCENARIO_COMPLETE",
                "facts": {},
            }

        step = self.steps[self.current_step]

        success = False

        # ----------------------------------------------
        # Обычное распознавание
        # ----------------------------------------------

        for pattern in step["patterns"]:
            if pattern in text:
                success = True
                break

        # ----------------------------------------------
        # Устойчивое распознавание этапа задымления
        # ----------------------------------------------

        if step["id"] == "smoke" and not success:

            smoke_markers = [
                "дым",
                "дымл",
                "задым",
                "задим",
                "задум",
                "задем",
                "дымлен",
                "дымление",
                "степень",
            ]

            for marker in smoke_markers:
                if marker in text:
                    success = True
                    break

        # ----------------------------------------------
        # УСПЕШНОЕ РАСПОЗНАВАНИЕ
        # ----------------------------------------------

        if success:

            answer = step["answer"]()

            event, facts = self._build_event(step["id"])

            self.results.append({
                "step": step["id"],
                "success": True,
                "event": event,
                "facts": facts,
            })

            self.current_step += 1

            return {
                "success": True,
                "done": self.current_step >= len(self.steps),
                "step": step["id"],
                "answer": answer,
                "event": event,
                "facts": facts,
            }

        # ----------------------------------------------
        # НЕУСПЕШНОЕ РАСПОЗНАВАНИЕ
        # ----------------------------------------------

        self.results.append({
            "step": step["id"],
            "success": False,
        })

        return {
            "success": False,
            "done": False,
            "step": step["id"],
            "answer": None,
            "event": None,
            "facts": {},
        }

    # ======================================================
    # СОБЫТИЯ И ФАКТЫ ДЛЯ АРМ
    # ======================================================

    def _build_event(self, step_id):

        if step_id == "incident":

            data = SCENARIO_DATA["incident"]

            facts = {
                "incident": "пожар" if data["fire"] else "неизвестно",
                "location": data["location"],
                "smoke": data["smoke"],
                "fire_spreading": data["fire_spreading"],
            }

            return "INCIDENT_CONFIRMED", facts

        if step_id == "address":

            data = SCENARIO_DATA["address"]

            facts = {
                "city": data["city"],
                "street": data["street"],
                "house": data["house"],
                "building": data["building"],
                "apartment": data["apartment"],
                "floor": data["floor"],
            }

            return "ADDRESS_CONFIRMED", facts

        if step_id == "people":

            data = SCENARIO_DATA["people"]

            facts = {
                "people_inside": data["possible_person_inside"],
                "person": data["person"],
            }

            return "PEOPLE_CONFIRMED", facts

        if step_id == "victims":

            data = SCENARIO_DATA["victims"]

            facts = {
                "victims_known": data["known"],
                "victims": data["known"],
            }

            return "VICTIMS_CONFIRMED", facts

        if step_id == "fire_location":

            data = SCENARIO_DATA["incident"]

            facts = {
                "fire_location": data["location"],
            }

            return "FIRE_LOCATION_CONFIRMED", facts

        if step_id == "smoke":

            data = SCENARIO_DATA["smoke"]

            facts = {
                "smoke_apartment": data["apartment"],
                "smoke_entrance": data["entrance"],
            }

            return "SMOKE_CONFIRMED", facts

        return None, {}

    # ======================================================
    # ФАКТИЧЕСКИЕ ОТВЕТЫ СЦЕНАРИЯ
    # ======================================================

    def _incident_answer(self):
        data = SCENARIO_DATA["incident"]

        location = data["location"]

        if location == "кухня":
            location_text = "на кухне"
        else:
            location_text = f"в районе {location}"

        return (
            f"Пожар начался {location_text}. "
            f"{data['smoke'].capitalize()}."
        )

    def _address_answer(self):
        data = SCENARIO_DATA["address"]

        return (
            f"{data['city']}, улица {data['street']}, "
            f"дом {data['house']}, корпус {data['building']}, "
            f"квартира {data['apartment']}."
        )

    def _people_answer(self):
        data = SCENARIO_DATA["people"]

        if data["possible_person_inside"]:
            return f"Возможно, внутри находится {data['person']}."

        return "Людей внутри нет."

    def _victims_answer(self):
        data = SCENARIO_DATA["victims"]

        if data["known"]:
            return "Есть пострадавшие."

        return "Информации о пострадавших пока нет."

    def _fire_location_answer(self):
        data = SCENARIO_DATA["incident"]

        location = data["location"]

        if location == "кухня":
            return "Пожар находится на кухне."

        return f"Пожар находится в районе {location}."

    def _smoke_answer(self):
        data = SCENARIO_DATA["smoke"]

        if data["apartment"] and data["entrance"]:
            return (
                "В квартире сильное задымление. "
                "Дым также заполняет подъезд."
            )

        if data["apartment"]:
            return "В квартире сильное задымление."

        return "Задымления нет."

    def get_results(self):
        return self.results


if __name__ == "__main__":

    engine = ScenarioEngine()

    test_questions = [
        "Что произошло?",
        "Назовите адрес.",
        "Есть ли люди внутри?",
        "Есть ли пострадавшие?",
        "Где пожар?",
        "Есть ли сильный дым?",
    ]

    for question in test_questions:

        result = engine.process(question)

        print()
        print("ВОПРОС:", question)
        print("РЕЗУЛЬТАТ:", result)