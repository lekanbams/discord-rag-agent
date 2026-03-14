import discord
import requests
import os
import re
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
N8N_WEBHOOK_URL = os.getenv('N8N_WEBHOOK_URL')

# Verify we have the required credentials
if not DISCORD_BOT_TOKEN:
    print("ERROR: DISCORD_BOT_TOKEN not found in .env file!")
    exit(1)
if not N8N_WEBHOOK_URL:
    print("ERROR: N8N_WEBHOOK_URL not found in .env file!")
    exit(1)

# Set up Discord client
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    """Called when bot connects to Discord"""
    print('=' * 50)
    print(f'✅ Bot is online!')
    print(f'Bot name: {client.user.name}')
    print(f'Bot ID: {client.user.id}')
    print(f'Connected to {len(client.guilds)} server(s)')
    print('=' * 50)
    print('Ready to answer questions!')
    print('Users can ask questions by:')
    print(f'  - Mentioning the bot: @{client.user.name} your question')
    print('  - Using command: !ask your question')
    print('=' * 50)

def clean_markdown_for_discord(text):
    """Convert incompatible markdown to Discord-compatible format"""
    text = re.sub(r'####\s+(.+?)(\n|$)', r'**\1**\2', text)
    text = re.sub(r'###\s+(.+?)(\n|$)', r'**\1**\2', text)
    text = re.sub(r'##\s+(.+?)(\n|$)', r'**\1**\2', text)
    text = re.sub(r'#\s+(.+?)(\n|$)', r'**\1**\2', text)
    return text

def split_message_smart(text, max_length=1900):
    """Split text at natural boundaries while respecting markdown structure"""
    if len(text) <= max_length:
        return [text]

    chunks = []
    current_chunk = ""
    paragraphs = text.split('\n\n')

    for paragraph in paragraphs:
        if len(current_chunk) + len(paragraph) + 2 > max_length:
            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = paragraph + '\n\n'
            else:
                sentences = []
                temp = ""
                for char in paragraph:
                    temp += char
                    if char in '.!?' and len(temp) > 1:
                        sentences.append(temp)
                        temp = ""
                if temp:
                    sentences.append(temp)

                for sentence in sentences:
                    if len(current_chunk) + len(sentence) > max_length:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                        current_chunk = sentence
                    else:
                        current_chunk += sentence
                current_chunk += '\n\n'
        else:
            current_chunk += paragraph + '\n\n'

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks

@client.event
async def on_message(message):
    """Called when a message is sent in any channel the bot can see"""

    if message.author == client.user:
        return

    should_respond = (
        client.user.mentioned_in(message) or
        message.content.startswith('!ask')
    )

    if should_respond:
        question = message.content
        question = question.replace(f'<@{client.user.id}>', '').strip()
        question = question.replace('!ask', '').strip()

        if not question:
            await message.channel.send(
                "❓ Please ask me a question!\n"
                f"Examples:\n"
                f"• `!ask What is machine learning?`\n"
                f"• `@{client.user.name} Explain neural networks`"
            )
            return

        print(f"\n📩 Question from {message.author.name}: {question}")

        async with message.channel.typing():
            try:
                payload = {
                    'question': question,
                    'user_id': str(message.author.id),
                    'username': message.author.name,
                    'channel_id': str(message.channel.id)
                }

                print(f"🔄 Sending to n8n...")
                response = requests.post(
                    N8N_WEBHOOK_URL,
                    json=payload,
                    timeout=30
                )

                response.raise_for_status()

                try:
                    response_data = response.json()
                    if isinstance(response_data, list) and len(response_data) > 0:
                        answer = response_data[0].get('answer') or response_data[0].get('content', 'Sorry, I could not generate an answer.')
                    else:
                        answer = response_data.get('answer') or response_data.get('content', 'Sorry, I could not generate an answer.')
                except ValueError:
                    answer = response.text or 'Sorry, I could not generate an answer.'

                answer = clean_markdown_for_discord(answer)

                print(f"✅ Received answer ({len(answer)} characters)")

                if len(answer) > 1900:
                    chunks = split_message_smart(answer, max_length=1900)
                    print(f"📝 Splitting into {len(chunks)} parts")
                    for chunk in chunks:
                        await message.channel.send(chunk)
                else:
                    await message.channel.send(answer)

                print(f"✅ Answer sent successfully\n")

            except requests.exceptions.Timeout:
                await message.channel.send("⏱️ The request took too long. Please try again.")
                print(f"❌ Timeout error\n")

            except requests.exceptions.HTTPError as e:
                await message.channel.send("❌ Sorry, there was an error processing your request.")
                print(f"❌ HTTP Error: {e}\n")

            except requests.exceptions.RequestException as e:
                await message.channel.send("❌ Could not connect to the knowledge base.")
                print(f"❌ Request Error: {e}\n")

            except KeyError as e:
                await message.channel.send("❌ Received invalid response format from n8n.")
                print(f"❌ KeyError: {e}\n")

            except Exception as e:
                await message.channel.send("❌ An unexpected error occurred.")
                print(f"❌ Unexpected error: {e}\n")

print("Starting Discord bot...")
print("Press Ctrl+C to stop\n")

try:
    client.run(DISCORD_BOT_TOKEN)
except discord.LoginFailure:
    print("\n❌ ERROR: Invalid Discord token!")
    print("Please check your DISCORD_BOT_TOKEN in the .env file")
except KeyboardInterrupt:
    print("\n👋 Bot stopped by user")
except Exception as e:
    print(f"\n❌ Error starting bot: {e}")
