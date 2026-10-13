import asyncio
import os
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import discord
from bot import Bot

class TelegramStartupTests(unittest.IsolatedAsyncioTestCase):
    async def test_webhook_removed_before_polling_preserves_queue(self):
        with patch.dict(os.environ,{'TELEGRAM_BOT_TOKEN':'test','TELEGRAM_ADMIN_IDS':'1'}):
            bot=Bot(intents=discord.Intents.default())
            calls=[]
            async def post(url,**kwargs):
                calls.append(('remove',kwargs['json']))
                response=MagicMock();response.json.return_value={'ok':True}
                return response
            async def get(url,**kwargs):
                calls.append(('poll',{}))
                raise asyncio.CancelledError()
            bot.services=MagicMock()
            bot.services.http.post=AsyncMock(side_effect=post)
            bot.services.http.get=AsyncMock(side_effect=get)
            with self.assertRaises(asyncio.CancelledError): await bot.telegram()
            self.assertEqual(calls,[('remove',{'drop_pending_updates':False}),('poll',{})])
