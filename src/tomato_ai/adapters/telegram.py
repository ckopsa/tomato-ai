import telegram
from tomato_ai.config import settings


from telegram import InlineKeyboardMarkup


class TelegramNotifier:
    def __init__(self, token: str):
        self.bot = telegram.Bot(token=token)

    async def send_message(self, chat_id: str, message: str, reply_markup: InlineKeyboardMarkup | None = None):
        await self.bot.send_message(chat_id=chat_id, text=message, reply_markup=reply_markup)


def get_telegram_notifier() -> TelegramNotifier | None:
    if settings.TELEGRAM_BOT_TOKEN:
        return TelegramNotifier(token=settings.TELEGRAM_BOT_TOKEN)
    return None
