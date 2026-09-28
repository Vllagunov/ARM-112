

# ==========================================================
# Файл: gigachat_client.py
# Проект: TOES 112 / AELIN
# Версия: 0.4 от 27.09.26
# Назначение:
# Клиент GigaChat с сохранением контекста сценария и диалога.
# ==========================================================

from gigachat import GigaChat
from gigachat.models import Chat, Messages


class GigaChatClient:

    def __init__(self, system_prompt=""):

        self.credentials = "MmI2MzZhZDktZDc0OC00NjNiLWI4NjgtYjBhZDc5MWFkYmI0Ojg4Yjc0MTgyLTI1MWItNDI4NC1hOTg0LTE5NWQ0YTc3Mjk5Zg=="
        self.scope = "GIGACHAT_API_PERS"

        self.system_prompt = system_prompt
        self.history = []

        if self.system_prompt:
            self.history.append(
                Messages(
                    role="system",
                    content=self.system_prompt
                )
            )

    def check_connection(self):
        """Проверяет доступность GigaChat API без отправки пользовательского запроса."""
        with GigaChat(
            credentials=self.credentials,
            scope=self.scope,
            verify_ssl_certs=False
        ) as giga:
            giga.get_models()
        return True

    def ask(self, text):

        self.history.append(
            Messages(
                role="user",
                content=text
            )
        )

        chat = Chat(
            messages=self.history
        )

        with GigaChat(
            credentials=self.credentials,
            scope=self.scope,
            verify_ssl_certs=False
        ) as giga:

            response = giga.chat(chat)

        answer = response.choices[0].message.content

        self.history.append(
            Messages(
                role="assistant",
                content=answer
            )
        )

        return answer


if __name__ == "__main__":

    ai = GigaChatClient()

    while True:

        text = input("Вы > ")

        if text.lower() in ("выход", "exit", "quit"):
            break

        print()
        print(ai.ask(text))
        print()


       