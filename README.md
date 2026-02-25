Telegram Legal Bot — compact & improved

Коротко: я упростил и улучшил код (маленькие оптимизации, кеш шаблонов, простая защита от спама).
В проекте:
- main.py      -- входной сервер (aiohttp + aiogram webhook)
- bot_app.py   -- логика бота, меню, рендер шаблонов, кеш
- core.py      -- конфиг + лёгкая DB-обёртка (aiosqlite)
- features.py  -- шаблоны, рендер, кеш, дисклеймер
- templates/   -- jinja2 шаблоны
- .env.sample  -- пример переменных окружения
- requirements.txt, render.yaml, Dockerfile

Запуск локально:
1) Создай .env с BOT_TOKEN.
2) pip install -r requirements.txt
3) python main.py
