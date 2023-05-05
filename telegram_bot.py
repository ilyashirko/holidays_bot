

from textwrap import dedent
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update

from telegram.ext import Updater, ConversationHandler, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler
import sqlite3
import telegram_calendar as tg_calendar



class TelegramBot:
    title = 'Holidays BOT'
    select_date_callback = {
        'text': '📅 Выбрать дату 📅',
        'callback_data': 'select_date'
    }
    select_date_inline = InlineKeyboardMarkup([[InlineKeyboardButton(**select_date_callback)]])

    class Holiday:
        def __init__(self, holiday_meta: set):
            self.id = holiday_meta[0]
            self.title = holiday_meta[1]
            self.day = holiday_meta[2]
            self.month = holiday_meta[3]
            self.image_url = holiday_meta[4]
            self.description = holiday_meta[5]

    def __init__(self,
                 telegram_bot_token: str,
                 db_path: str,
                 admin_telegram_id: str):
        self.db = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.db.cursor()
        
        self.admin_telegram_id = admin_telegram_id

        self.telegram_bot_token = telegram_bot_token
        self.updater = Updater(token=self.telegram_bot_token, use_context=True)
        self.updater.bot.send_message(self.admin_telegram_id, 'init bot')

    def run_bot(self):
        self.updater.dispatcher.add_handler(CommandHandler(command='start', callback=self.start))
        

        self.updater.dispatcher.add_handler(ConversationHandler(
            entry_points=[
                CallbackQueryHandler(callback=tg_calendar.create_date,
                                     pattern=self.select_date_callback['callback_data'])],
            states={
                'DATE_PROCESSING': [
                    CallbackQueryHandler(callback=self.display_holidays,
                                         pattern=tg_calendar.CONFIRM_DATE_CALLBACK),
                    CallbackQueryHandler(callback=tg_calendar.correct_date)
                ]
            },
            fallbacks=[],
        ))

        self.updater.bot.send_message(self.admin_telegram_id, f'{self.title} start polling')
        self.updater.start_polling()
        self.updater.idle()


    def start(self, update: Update, callback: CallbackContext):
        update.message.reply_text(dedent(
                f'''
                Привет 👋
                Наверняка у тебя бывали моменты когда хочется праздника, но праздновать нечего.

                А ты знаешь что каждый день в мире отмечаются много праздников?
                Я знаю и с удовольствием поделюсь радостью 👍

                Помогу тебе найти:
                ✅ повод;
                ✅ новые знания;
                ✅ убедительную отмазку.

                Жми "{self.select_date_callback['text']}", выбирай дату и я расскажу какие праздники празднует мир в этот день.
                '''
            ),
            reply_markup=self.select_date_inline
        )

    def display_holidays(self, update: Update, context: CallbackContext):
        date = tg_calendar.get_current_calendar(update=update, context=context).dt
        holidays = self.get_holidays(day=date.day, month=date.month)
        return ConversationHandler.END

    def get_holidays(self, day: int, month: int):
        holidays = self.cursor.execute('SELECT * FROM holidays WHERE day = ? AND month = ?',
                                       (day, month)).fetchall()
        return [self.Holiday(holiday_meta) for holiday_meta in holidays]
