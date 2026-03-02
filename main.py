# main.py (заменить файл полностью)
import logging
import os
from aiohttp import web
from aiogram.webhook.aiohttp_server import SimpleRequestHandler
from core import cfg
from bot_app import bot_app

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

WEBHOOK_PATH = cfg.WEBHOOK_PATH
WEBHOOK_URL = cfg.WEBHOOK_URL or None

async def on_startup(app: web.Application):
    await bot_app.init_app_for_runtime(app)
    if WEBHOOK_URL:
        try:
            logger.info(f'Setting webhook: {WEBHOOK_URL}')
            await bot_app.bot.set_webhook(WEBHOOK_URL)
            logger.info('Webhook set successfully.')
        except Exception as e:
            logger.exception('Failed to set webhook: %s', e)
    else:
        logger.warning('WEBHOOK_HOST not configured; running without setting webhook.')

async def on_shutdown(app: web.Application):
    logger.info('Shutting down: deleting webhook and closing DB')
    try:
        await bot_app.bot.delete_webhook()
    except Exception as e:
        logger.exception('Error deleting webhook: %s', e)
    await bot_app.close_db()

async def healthz(request):
    return web.Response(text='OK')

async def debug(request):
    return web.json_response({'status': 'ok'})

# simple root so GET / returns friendly 200
async def index(request):
    return web.Response(text='Business-Lawyer Bot is running. Use /healthz for health checks.')

def create_app():
    app = web.Application()
    handler = SimpleRequestHandler(bot_app.get_dispatcher(), bot=bot_app.bot)
    # webhook endpoint
    app.router.add_post(WEBHOOK_PATH, handler.handle)
    app.router.add_get('/', index)
    app.router.add_get('/healthz', healthz)
    app.router.add_get('/debug', debug)
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    return app

if __name__ == '__main__':
    # Use PORT provided by host (Render). Fallback to 8000 locally.
    port = int(os.environ.get('PORT', 8000))
    app = create_app()
    web.run_app(app, host='0.0.0.0', port=port)
