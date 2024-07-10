from aiohttp import web
import os
import ssl
import telebot
import asyncio
from bot.common import check_new_entries

# Load environment variables from the .env file
BOT_TOKEN = os.getenv('bot_token')
TIMER = int(os.getenv('timer'))
SSL_CERT = os.getenv('ssl_sert')
SSL_PRIVKEY = os.getenv('ssl_privkey')

def setup_web_app(bot_instance, config_dict, limiter_obj):
    global bot, config, limiter
    bot = bot_instance
    config = config_dict
    limiter = limiter_obj


    WEBHOOK_SSL_CERT = SSL_CERT
    WEBHOOK_SSL_PRIV = SSL_PRIVKEY

    app = web.Application()
    app.router.add_post("/{token}/", handle)

    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    context.load_cert_chain(WEBHOOK_SSL_CERT, WEBHOOK_SSL_PRIV)

    app.on_startup.append(start_background_tasks)
    app.on_cleanup.append(cleanup_background_tasks)

    return app, context

# Process requests with correct bot token
async def handle(request):
    if request.match_info.get("token") == BOT_TOKEN:
        request_body_dict = await request.json()
        update = telebot.types.Update.de_json(request_body_dict)
        bot.process_new_updates([update])
        return web.Response()
    else:
        return web.Response(status=403)

# Update nws in background
async def check_site_for_updates():
    while True:
        check_new_entries(config, bot, limiter)
        await asyncio.sleep(TIMER * 3600)

async def start_background_tasks(app):
    app['check_site_for_updates'] = asyncio.create_task(check_site_for_updates())

async def cleanup_background_tasks(app):
    app['check_site_for_updates'].cancel()
    await app['check_site_for_updates']