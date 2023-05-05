from environs import Env
from telegram_bot import TelegramBot


if __name__ == '__main__':
    env = Env()
    env.read_env()

    bot = TelegramBot(telegram_bot_token=env.str('TELEGRAM_BOT_TOKEN'),
                      db_path=env.str('DATABASE_PATH'),
                      admin_telegram_id=env.str('ADMIN_TELEGRAM_ID'),)
    bot.run_bot()