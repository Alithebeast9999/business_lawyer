from dataclasses import dataclass
import os
import aiosqlite
from typing import Optional

@dataclass
class Config:
    BOT_TOKEN: str = os.getenv('BOT_TOKEN', '')
    WEBHOOK_HOST: str = os.getenv('WEBHOOK_HOST', '')  # e.g. https://your-app.onrender.com
    WEBHOOK_PATH: str = os.getenv('WEBHOOK_PATH', '/webhook')
    DATABASE_URL: str = os.getenv('DATABASE_URL', 'sqlite:///./bot_db.sqlite')
    ADMIN_USER_IDS: str = os.getenv('ADMIN_USER_IDS', '')  # comma-separated

    def __post_init__(self):
        if self.WEBHOOK_HOST:
            self.WEBHOOK_URL = f"{self.WEBHOOK_HOST.rstrip('/')}{self.WEBHOOK_PATH}"
        else:
            self.WEBHOOK_URL = ''

cfg = Config()

class DB:
    """Light aiosqlite wrapper."""
    def __init__(self, database_url: str):
        if database_url.startswith('sqlite:///'):
            self.path = database_url.replace('sqlite:///', '')
        else:
            self.path = database_url
        self._conn: Optional[aiosqlite.Connection] = None

    async def init(self):
        self._conn = await aiosqlite.connect(self.path)
        await self._conn.execute("PRAGMA foreign_keys = ON;")
        await self._create_tables()
        await self._conn.commit()

    async def _create_tables(self):
        await self._conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE,
            name TEXT,
            role TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        await self._conn.execute("""
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER,
            request_type TEXT,
            payload TEXT,
            status TEXT DEFAULT 'new',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

    async def close(self):
        if self._conn:
            await self._conn.close()
            self._conn = None

    async def execute(self, sql: str, params: tuple = ()):
        cur = await self._conn.execute(sql, params)
        await self._conn.commit()
        return cur

    async def fetchone(self, sql: str, params: tuple = ()):
        cur = await self._conn.execute(sql, params)
        row = await cur.fetchone()
        return row

    async def fetchall(self, sql: str, params: tuple = ()):
        cur = await self._conn.execute(sql, params)
        rows = await cur.fetchall()
        return rows
