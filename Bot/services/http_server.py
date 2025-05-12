import asyncio
from aiohttp import web
from aiogram import Bot
import logging

logger = logging.getLogger(__name__)

async def handle_notify(request: web.Request) -> web.Response:
    bot = request.app['bot']
    try:
        data = await request.json()
        user_ids = data.get('user_ids')
        url = data.get('url')
        contract_name = data.get('contract_name')

        if not user_ids or not isinstance(user_ids, list) or not url or not contract_name:
            logger.error(f"Некорректные данные в запросе: {data}")
            return web.json_response({'status': 'error', 'message': 'Некорректные данные'}, status=400)

        message_text_template = f"🔔 Новое изменение в контракте {contract_name}!\n<code>{{url}}</code>"

        for user_id in user_ids:
            try:
                await bot.send_message(chat_id=user_id, text=message_text_template.format(url=url))
                logger.info(f"Уведомление отправлено пользователю {user_id}")
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Ошибка отправки сообщения пользователю {user_id}: {e}")
        
        return web.json_response({'status': 'success', 'message': 'Уведомления обработаны'})
    except Exception as e:
        logger.error(f"Ошибка обработки /bot/notify: {e}")
        return web.json_response({'status': 'error', 'message': 'Внутренняя ошибка сервера'}, status=500)

async def start_http_server(bot: Bot, host: str, port: int):
    app = web.Application()
    app['bot'] = bot
    app.router.add_post('/bot/notify', handle_notify)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    logger.info(f"Запуск HTTP сервера для бота на {host}:{port}")
    await site.start()
    try:
        while True:
            await asyncio.sleep(3600)
    except asyncio.CancelledError:
        logger.info("HTTP сервер останавливается.")
        await runner.cleanup()
        logger.info("HTTP сервер остановлен.") 