from datetime import date, datetime, timedelta
from itertools import chain

from more_itertools import chunked
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext
from contextlib  import suppress
from telegram.error import BadRequest
import re

CONFIRM_DATE_BUTTON = '✅ Готово ✅'

CONFIRM_DATE_CALLBACK = 'confirm_date'

def create_date(update: Update, context: CallbackContext):
    dt = Calendar()
    context.bot.send_message(
        update.effective_chat.id,
        dt.display_date(),
        reply_markup=dt.generate_keyboard()
    )
    return 'DATE_PROCESSING'

def correct_date(update: Update, context: CallbackContext, message: str = None):
    callback = update.callback_query.data
    inline_keyboard = update.callback_query.message.reply_markup.inline_keyboard
    if re.match(r'\d+', callback):
        dt = Calendar(new_day=int(callback), inline_keyboard=inline_keyboard)
    else:
        dt = Calendar(callback=callback, inline_keyboard=inline_keyboard)
    message = message or dt.display_date()
    with suppress(BadRequest):
        context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=update.callback_query.message.message_id,
            text=message,
            reply_markup=dt.generate_keyboard()
        )
    return 'DATE_PROCESSING'

def get_current_calendar(update: Update, context: CallbackContext):
    inline_keyboard = update.callback_query.message.reply_markup.inline_keyboard
    return Calendar(inline_keyboard=inline_keyboard)


class Calendar:
    WEEKDAYS = {
        0: ("ПН", "Понедельник"),
        1: ("ВТ", "Вторник"),
        2: ("СР", "Среда"),
        3: ("ЧТ", "Четверг"),
        4: ("ПТ", "Пятница"),
        5: ("СБ", "Суббота"),
        6: ("ВС", "Воскресенье"),
    }
    MONTHS = {
        1: {
            "nominative": "январь",
            "genitive": "января"
        },
        2: {
            "nominative": "февраль",
            "genitive": "февраля"
        },
        3: {
            "nominative": "март",
            "genitive": "марта"
        },
        4: {
            "nominative": "апрель",
            "genitive": "апреля"
        },
        5: {
            "nominative": "май",
            "genitive": "мая"
        },
        6: {
            "nominative": "июнь",
            "genitive": "июня"
        },
        7: {
            "nominative": "июль",
            "genitive": "июля"
        },
        8: {
            "nominative": "август",
            "genitive": "августа"
        },
        9: {
            "nominative": "сентябрь",
            "genitive": "сентября"
        },
        10: {
            "nominative": "октябрь",
            "genitive": "октября"
        },
        11: {
            "nominative": "ноябрь",
            "genitive": "ноября"
        },
        12: {
            "nominative": "декарь",
            "genitive": "декабря"
        },
    }
    
    dt = None
    
    def __init__(self, *args, **kwargs):
        current_inline = kwargs.get('inline_keyboard', None)
        if current_inline:
            year = int(current_inline[0][2].text)
            month = int(current_inline[1][1].callback_data.split(':::')[1])
            day = kwargs.get('new_day', self._find_current_date(current_inline))
            self.dt = date(year, month, day)
            self.callback = kwargs.get('callback')
            if self.callback:
                self.change_date()
        self.dt = self.dt or kwargs.get('input_dt', date.today())

    def __str__(self):
        return self.dt.strftime(r'%Y-%m-%d')
    
    def change_date(self):
        year = self.dt.year
        month = self.dt.month
        if self.callback == 'increase_year':
            year += 1
        elif self.callback == 'ten_increase_year':
            year += 10
        elif self.callback == 'reduce_year':
            year -= 1
        elif self.callback == 'ten_reduce_year':
            year -= 10
        elif self.callback == 'increase_month':
            if month == 12:
                month = 1
                year += 1
            else:
                month += 1
        elif self.callback == 'reduce_month':
            if month == 1:
                month = 12
                year -= 1
            else:
                month -= 1
            
        try:
            self.dt = self.dt.replace(year=year, month=month)
        except ValueError:
            max_day = self.get_last_month_day(
                date(year=year, month=month, day=1)
            ).day
            self.dt = self.dt.replace(year=year, month=month, day=max_day)
        
        return
    
    def _find_current_date(self, buttons: list[list[InlineKeyboardButton]]):
        buttons = list(chain(*buttons))
        for button in buttons:
            if 'current_day' in button.callback_data:
                return int(button.callback_data.split(':::')[1])

    def display_date(self):
        return f"{self.dt.day} {self.MONTHS[self.dt.month]['genitive']} {self.dt.year} г."

    def get_last_month_day(self, date = None):
        dt = date or self.dt
        next_month = dt.replace(day=28) + timedelta(days=4)
        return next_month - timedelta(days=next_month.day)

    def generate_days_keyboard(self):
        first_month_day = self.dt.replace(day=1)
        last_month_day = self.get_last_month_day()
        add_before = datetime.weekday(first_month_day)
        add_after = datetime.weekday(last_month_day)
        days = list(range(1, last_month_day.day + 1))
        if add_before:
            buttons = [None for _ in range(add_before)] + days
        else:
            buttons = days
        if add_after < 6:
            buttons += [None for _ in range(6 - add_after)]
        return buttons
    
    def weekdays_buttons(self):
        return [
            InlineKeyboardButton(text=self.WEEKDAYS[num][0], callback_data='none')
            for num in range(7)
        ]

    def generate_keyboard(self):
        days_buttons = list()
        for day in self.generate_days_keyboard():
            if day == self.dt.day:
                days_buttons.append(InlineKeyboardButton(text=f'- {day} -', callback_data=f'current_day:::{day}'))
            elif day:
                days_buttons.append(InlineKeyboardButton(text=day, callback_data=day))
            else:
                days_buttons.append(InlineKeyboardButton(text=' ', callback_data=f'none'))
            
        buttons = [
                [
                    InlineKeyboardButton(text='<<<', callback_data='ten_reduce_year'),
                    InlineKeyboardButton(text='<-', callback_data='reduce_year'),
                    InlineKeyboardButton(text=self.dt.year, callback_data='year'),
                    InlineKeyboardButton(text='->', callback_data='increase_year'),
                    InlineKeyboardButton(text='>>>', callback_data='ten_increase_year'),
                ],
                [
                    InlineKeyboardButton(text='<-', callback_data='reduce_month'),
                    InlineKeyboardButton(text=self.MONTHS[self.dt.month]['nominative'], callback_data=f'month:::{self.dt.month}'),
                    InlineKeyboardButton(text='->', callback_data='increase_month'),
                ],
                self.weekdays_buttons()
            ]
        buttons += list(chunked(days_buttons, 7))
        buttons.append([InlineKeyboardButton(
            text=f"✅ {self.display_date()} ✅",
            callback_data=f'{CONFIRM_DATE_CALLBACK}:::{self.__str__()}'
        )])
        return InlineKeyboardMarkup(buttons)

