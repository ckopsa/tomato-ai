import telegram
from tomato_ai.config import settings


class TelegramNotifier:
    def __init__(self, token: str):
        self.bot = telegram.Bot(token=token)

    async def send_message(self, chat_id: str, message: str):
        await self.bot.send_message(chat_id=chat_id, text=message)


def get_telegram_notifier() -> TelegramNotifier | None:
    if settings.TELEGRAM_BOT_TOKEN:
        return TelegramNotifier(token=settings.TELEGRAM_BOT_TOKEN)
    return None
