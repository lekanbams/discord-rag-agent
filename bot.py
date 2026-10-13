"""RAG-B v2: Discord support + restricted Telegram document ingestion."""
import asyncio
import logging
import os
import re
import httpx
import time
from pathlib import Path
import discord
from dotenv import load_dotenv
from ragb.core import Memory, MISSING, split_message
from ragb.services import Services

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
log=logging.getLogger('ragb')
REQUIRED=['DISCORD_BOT_TOKEN','OPENAI_API_KEY','SUPABASE_URL','SUPABASE_SERVICE_ROLE_KEY','EMBEDDING_MODEL','CHAT_MODEL','DISCORD_GUILD_ID','ADMIN_CHANNEL_ID','ADMIN_ROLE_ID']

def safe_http_error(error):
    # Never log request URLs, headers, full bodies or exception strings.
    status = error.response.status_code
    detail = ''
    if error.request.url.host == 'api.telegram.org':
        try:
            detail = str(error.response.json().get('description', ''))
        except (ValueError, AttributeError):
            pass
        for key in ('TELEGRAM_BOT_TOKEN', 'DISCORD_BOT_TOKEN', 'OPENAI_API_KEY', 'SUPABASE_SERVICE_ROLE_KEY'):
            value = os.getenv(key)
            if value: detail = detail.replace(value, '[REDACTED]')
        detail = re.sub(r'https?://\S+', '[URL]', detail).replace('\n', ' ')[:250]
    return f'HTTP {status}' + (f': {detail}' if detail else '')

class Bot(discord.Client):
    async def setup_hook(self):
        self.config_ready=False
        self.services=Services()
        Path('data').mkdir(exist_ok=True)
        self.memory=Memory('data/memory.sqlite')
        self.locks={}
        self.cooldowns={}
        self.slots=asyncio.Semaphore(3)
        self.telegram_task=asyncio.create_task(self.telegram()) if os.getenv('TELEGRAM_BOT_TOKEN') else None
    async def close(self):
        task = getattr(self, 'telegram_task', None)
        try:
            if task:
                task.cancel()
                await asyncio.gather(task, return_exceptions=True)
            services = getattr(self, 'services', None)
            if services:
                await services.http.aclose()
        finally:
            await super().close()
    async def on_ready(self):
        log.info('RAG-B connected as %s',self.user)
        channel=self.get_channel(int(os.environ['ADMIN_CHANNEL_ID']))
        guild=self.get_guild(int(os.environ['DISCORD_GUILD_ID']))
        if not guild or not channel or channel.guild.id != guild.id:
            log.error('Admin channel/server configuration invalid'); return
        if channel.permissions_for(guild.default_role).view_channel:
            log.error('Admin channel must be private to @everyone'); return
        if not guild.get_role(int(os.environ['ADMIN_ROLE_ID'])):
            log.error('Admin role not found'); return
        self.config_ready=True
    async def on_message(self,message):
        if message.author.bot or not message.guild or message.guild.id != int(os.environ['DISCORD_GUILD_ID']): return
        if message.channel.id == int(os.environ['ADMIN_CHANNEL_ID']): return
        prefix=message.content.startswith('!ask ')
        mentioned=self.user in message.mentions
        if not (prefix or mentioned): return
        if not self.config_ready:
            await message.reply('RAG-B setup is incomplete. Please contact a moderator.',mention_author=False); return
        question=message.content[5:] if prefix else message.content
        for tag in (f'<@{self.user.id}>',f'<@!{self.user.id}>'): question=question.replace(tag,'')
        question=question.strip()
        if not question or len(question)>4000:
            await message.reply('Please ask a question under 4,000 characters.',mention_author=False); return
        session=f'{message.guild.id}:{message.channel.id}:{message.author.id}'
        now=time.monotonic()
        if now-self.cooldowns.get(session,0)<5:
            await message.reply('Please wait a few seconds before asking again.',mention_author=False); return
        self.cooldowns[session]=now
        async with self.locks.setdefault(session,asyncio.Lock()), self.slots, message.channel.typing():
            try:
                answer=await self.services.answer(question,self.memory.history(session))
                if answer is None:
                    try:
                        channel=self.get_channel(int(os.environ['ADMIN_CHANNEL_ID']))
                        role=message.guild.get_role(int(os.environ['ADMIN_ROLE_ID']))
                        if not channel or channel.permissions_for(message.guild.default_role).view_channel or not role: raise RuntimeError('Invalid private admin destination')
                        # Only the configured admin role may ping. User/question mentions cannot ping.
                        alert=f'{role.mention} Unanswered question from {message.author.mention}\nQuestion: {question}\nOriginal message: {message.jump_url}'
                        await channel.send(alert,allowed_mentions=discord.AllowedMentions(roles=[role],users=False,everyone=False))
                        answer=MISSING
                    except Exception:
                        log.warning('Admin routing failed')
                        answer=MISSING
                for chunk in split_message(answer):
                    await message.reply(chunk,mention_author=False,allowed_mentions=discord.AllowedMentions.none())
                self.memory.add(session,question,answer)
            except Exception as error:
                log.warning('Question failed: %s',type(error).__name__)
                await message.reply('I couldn\'t check the knowledge base right now. Please try again shortly.',mention_author=False)
    async def telegram(self):
        token=os.environ['TELEGRAM_BOT_TOKEN']
        base=f'https://api.telegram.org/bot{token}'
        admins={int(x) for x in os.getenv('TELEGRAM_ADMIN_IDS','').split(',') if x.strip()}
        if not admins: log.warning('Telegram uploads disabled: no admin IDs'); return
        offset=0
        webhook_removed=False
        while True:
            try:
                if not webhook_removed:
                    removed = await self.services.http.post(base+'/deleteWebhook', json={'drop_pending_updates':False})
                    removed.raise_for_status()
                    if removed.json().get('ok') is not True:
                        raise RuntimeError('Telegram webhook removal failed')
                    webhook_removed=True
                    log.info('Telegram webhook removed; queued updates retained; polling started')
                r=await self.services.http.get(base+'/getUpdates',params={'offset':offset,'timeout':25},timeout=35)
                r.raise_for_status()
                data=r.json()
                if not data.get('ok'): raise RuntimeError('Telegram polling failed')
                for update in data['result']:
                    offset=update['update_id']+1
                    msg=update.get('message',{})
                    if msg.get('from',{}).get('id') not in admins or msg.get('chat',{}).get('type')!='private': continue
                    doc=msg.get('document')
                    if not doc: continue
                    try:
                        if doc.get('file_size',0)>5*1024*1024: raise ValueError('Upload limit is 5 MB')
                        f=await self.services.http.get(base+'/getFile',params={'file_id':doc['file_id']})
                        f.raise_for_status()
                        file_path=f.json()['result']['file_path']
                        payload=await self.services.http.get(f'https://api.telegram.org/file/bot{token}/{file_path}')
                        payload.raise_for_status()
                        if len(payload.content)>5*1024*1024: raise ValueError('Upload limit is 5 MB')
                        count=await self.services.ingest(doc['file_name'],payload.content)
                        reply=f'Knowledge base updated: {count} chunks indexed.'
                    except ValueError as e: reply=str(e)
                    except httpx.HTTPStatusError as e:
                        log.warning('Upload HTTP failure: %s', safe_http_error(e))
                        reply='Upload failed. Please try again. No success is confirmed.'
                    except Exception as e:
                        log.warning('Upload failed: %s', type(e).__name__)
                        reply='Upload failed. Please try again. No success is confirmed.'
                    sent = await self.services.http.post(base+'/sendMessage',json={'chat_id':msg['chat']['id'],'text':reply})
                    sent.raise_for_status()
            except httpx.HTTPStatusError as e:
                log.warning('Telegram operation failed: %s', safe_http_error(e))
                await asyncio.sleep(15)
            except Exception as e:
                log.warning('Telegram operation failed: %s',type(e).__name__)
                await asyncio.sleep(5)

if __name__=='__main__':
    missing=[key for key in REQUIRED if not os.getenv(key)]
    if missing: raise SystemExit('Missing configuration: '+', '.join(missing))
    # Avoid httpx INFO request logs, which would expose Telegram tokens in URLs.
    logging.getLogger('httpx').setLevel(logging.WARNING)
    intents=discord.Intents.default(); intents.message_content=True
    Bot(intents=intents).run(os.environ['DISCORD_BOT_TOKEN'])
