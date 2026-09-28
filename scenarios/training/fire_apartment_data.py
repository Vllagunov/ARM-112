
# ==========================================================
# Файл: fire_apartment_data.py
# Проект: TOES 112
# Версия: 0.1
# Назначение:
# Факты тренировочного сценария «Пожар в квартире».
#
# Эти данные являются источником истины.
# GigaChat не имеет права изменять их.
# ==========================================================

SCENARIO_DATA = {

    "incident": {
        "fire": True,
        "location": "кухня",
        "smoke": "сильное задымление",
        "fire_spreading": True,
    },

    "address": {
        "city": "Москва",
        "street": "Первомайская",
        "house": "15",
        "building": "2",
        "apartment": "48",
        "floor": "5",
    },

    "applicant": {
        "name": "Иван",
        "age": 35,
        "phone": "+7 999 123-45-67",
    },

    "people": {
        "possible_person_inside": True,
        "person": "пожилая женщина",
    },

    "victims": {
        "known": False,
    },

    "smoke": {
        "apartment": True,
        "entrance": True,
    },
}

