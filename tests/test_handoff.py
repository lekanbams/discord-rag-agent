import asyncio
import os
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import discord
from bot import Bot
from ragb.core import MISSING

class HandoffTests(unittest.IsolatedAsyncioTestCase):
    async def run_case(self, alert_fails=False, service_fails=False):
        with patch.dict(os.environ,{'DISCORD_GUILD_ID':'1','ADMIN_CHANNEL_ID':'2','ADMIN_ROLE_ID':'3'}):
            bot=Bot(intents=discord.Intents.default())
            bot.config_ready=True
            bot._connection.user=MagicMock(id=99)
            bot.services=MagicMock(); bot.services.answer=AsyncMock(return_value=None)
            if service_fails: bot.services.answer.side_effect=RuntimeError('offline')
            bot.memory=MagicMock(); bot.memory.history.return_value=[]
            bot.locks={}; bot.cooldowns={}; bot.slots=asyncio.Semaphore(3)
            message=MagicMock(); message.author.bot=False; message.author.id=5; message.author.mention='<@5>'
            message.guild.id=1; message.channel.id=4; message.content='!ask Unknown question'; message.mentions=[]
            message.jump_url='https://discord.com/channels/1/4/6'
            message.reply=AsyncMock()
            role=MagicMock(); role.mention='<@&3>'; message.guild.get_role.return_value=role
            channel=MagicMock(); channel.permissions_for.return_value.view_channel=False
            channel.send=AsyncMock()
            if alert_fails: channel.send.side_effect=RuntimeError('forbidden')
            bot.get_channel=MagicMock(return_value=channel)
            await bot.on_message(message)
            return message.reply.call_args.args[0], channel.send
    async def test_missing_answer_routes(self):
        reply,send=await self.run_case()
        self.assertEqual(reply,MISSING)
        self.assertIn('Unknown question',send.call_args.args[0])
        self.assertIn('<@5>',send.call_args.args[0])
        self.assertFalse(send.call_args.kwargs['allowed_mentions'].everyone)
    async def test_failed_alert_is_not_confirmed(self):
        reply,_=await self.run_case(alert_fails=True)
        self.assertEqual(reply,MISSING)
        self.assertNotIn("I've notified",reply)
    async def test_database_error_not_missing_context(self):
        reply,send=await self.run_case(service_fails=True)
        self.assertIn("couldn't check",reply)
        send.assert_not_called()

    async def test_close_before_setup(self):
        bot=Bot(intents=discord.Intents.default())
        await bot.close()
        self.assertTrue(bot.is_closed())
