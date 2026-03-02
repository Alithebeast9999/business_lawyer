# bot_app.py
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from core import cfg, DB
from features import list_templates, render_template, get_disclaimer, is_rate_limited
from typing import Dict, Any

logger = logging.getLogger(__name__)

class BotApp:
    def __init__(self, token: str, db_url: str):
        self.bot = Bot(token=token)
        self.dp = Dispatcher()
        self.db = DB(db_url)
        self._active = {}
        self._register_handlers()

    async def init_app_for_runtime(self, app=None):
        logger.info('Init DB')
        await self.db.init()

    async def close_db(self):
        logger.info('Closing DB and bot session')
        await self.db.close()
        await self.bot.session.close()

    def get_dispatcher(self) -> Dispatcher:
        return self.dp

    def _main_menu_keyboard(self) -> ReplyKeyboardMarkup:
        kb = ReplyKeyboardMarkup(keyboard=[
            [KeyboardButton(text='📄 Получить шаблон'), KeyboardButton(text='📂 Мои запросы')],
            [KeyboardButton(text='📞 Связаться с юристом'), KeyboardButton(text='ℹ️ О боте')],
        ], resize_keyboard=True)
        return kb

    def _templates_keyboard(self) -> InlineKeyboardMarkup:
        kb = InlineKeyboardMarkup(row_width=2)
        for key in list_templates():
            kb.insert(InlineKeyboardButton(text=key.replace('_',' ').title(), callback_data=f"tpl:{key}"))
        return kb

    def _register_handlers(self):
        # Команда /start
        @self.dp.message(Command(commands=['start']))
        async def cmd_start(message: Message):
            await message.answer(
                f"Привет, {message.from_user.first_name or 'друг'}!\n\n"
                "Я — юридический бот для бизнеса. Могу сгенерировать шаблон договора и помочь с рутиной.\n\n"
                + get_disclaimer(),
                reply_markup=self._main_menu_keyboard()
            )

        # Кнопка "📄 Получить шаблон"
        @self.dp.message(F.text == '📄 Получить шаблон')
        async def menu_get_template(message: Message):
            if is_rate_limited(message.from_user.id, 'menu'):
                await message.answer('Пожалуйста, подождите пару секунд перед следующей операцией.')
                return
            kb = self._templates_keyboard()
            if not list_templates():
                await message.answer('Сейчас шаблонов нет.')
                return
            await message.answer('Выберите шаблон:', reply_markup=kb)

        # Кнопка "ℹ️ О боте"
        @self.dp.message(F.text == 'ℹ️ О боте')
        async def about_bot(message: Message):
            await message.answer(get_disclaimer())

        # Кнопка "📂 Мои запросы"
        @self.dp.message(F.text == '📂 Мои запросы')
        async def my_requests(message: Message):
            await message.answer("Функция в разработке.")

        # Кнопка "📞 Связаться с юристом"
        @self.dp.message(F.text == '📞 Связаться с юристом')
        async def contact_lawyer(message: Message):
            await message.answer("Для связи с юристом напишите на email: lawyer@example.com")

        # Обработка инлайн-кнопок выбора шаблона
        @self.dp.callback_query(F.data.startswith('tpl:'))
        async def on_template_selected(query: CallbackQuery):
            await query.answer()
            if is_rate_limited(query.from_user.id, 'get_template', cooldown_seconds=5):
                await query.message.answer('Вы слишком часто запрашиваете шаблоны. Подождите немного.')
                return
            key = query.data.split(':',1)[1]
            context: Dict[str,Any] = {
                'party_a':'Компания A',
                'party_b':'Компания B',
                'client_name': query.from_user.full_name or query.from_user.username or str(query.from_user.id)
            }
            bio = render_template(key, context)
            if bio:
                await self.bot.send_document(chat_id=query.from_user.id, document=bio, caption=f'Шаблон: {key}')
            else:
                await query.message.answer('Не удалось отрендерить шаблон.')

        # Команда /get_template
        @self.dp.message(Command(commands=['get_template']))
        async def cmd_get_template(message: Message):
            args = message.text.split(maxsplit=1)
            if len(args) < 2:
                await message.answer('Использование: /get_template <key>\nНапример: /get_template nda')
                return
            key = args[1].strip().lower()
            bio = render_template(key, {'party_a': 'Компания A', 'party_b': 'Компания B'})
            if bio:
                await message.answer_document(document=bio, caption=f'Шаблон: {key}')
            else:
                await message.answer('Шаблон не найден. Используйте кнопку "Получить шаблон".')

        # Обработчик всех остальных текстовых сообщений
        @self.dp.message(F.text)
        async def fallback(message: Message):
            await message.answer('Не понял. Выберите пункт меню или используйте /start.', reply_markup=self._main_menu_keyboard())

# Экземпляр приложения для импорта в main.py
bot_app = BotApp(token=cfg.BOT_TOKEN, db_url=cfg.DATABASE_URL)
