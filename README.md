# Discord RAG Agent

An intelligent Discord bot powered by RAG (Retrieval-Augmented Generation) that can answer questions based on documents you provide. Upload PDFs, Word docs, or text files via Telegram, and the bot automatically indexes them into a vector database. Users can then query this knowledge base through Discord, with AI-powered responses that cite relevant information.

## 📊 Overview

This automation creates a knowledge base chatbot that:
- Accepts documents via Telegram for easy knowledge base updates
- Stores document embeddings in Supabase vector database
- Answers Discord user questions using retrieved context
- Maintains conversation memory per user (PostgreSQL)
- Provides properly formatted Discord markdown responses
- Supports concurrent users with isolated conversation histories

## ✨ Key Features

- **Document Ingestion**: Upload any document via Telegram (PDF, DOCX, TXT, etc.)
- **Vector Search**: Semantic search through your knowledge base
- **RAG Architecture**: Combines retrieval with AI generation for accurate answers
- **Per-User Memory**: Each Discord user has their own conversation context
- **Discord-Optimized**: Proper markdown formatting for Discord
- **Multi-Channel**: Can be deployed across multiple Discord servers
- **Real-Time Updates**: New documents instantly available to the bot
- **Scalable**: Handles unlimited documents and concurrent users

## 🏗️ Workflow Architecture

### Two Main Paths:

#### **Path 1: Vector Store Update** (Telegram)
```
Telegram Trigger (Document Upload)
    ↓
Get File from Telegram
    ↓
Default Data Loader (Parse Document)
    ↓
Embeddings Google Gemini (Convert to Vectors)
    ↓
Supabase Vector Store (Store in Database)
    ↓
Send Update Confirmation
```

#### **Path 2: RAG-B Query Handler** (Discord)
```
Webhook (Discord Question)
    ↓
Get Question (Parse Request)
    ↓
AI Agent (Process Query)
    ├── Google Gemini Chat Model (Generate Response)
    ├── Supabase Vector Store Tool (Search Knowledge)
    └── Postgres Chat Memory (Conversation Context)
    ↓
Answer (Format Response)
    ↓
Respond to Webhook (Send to Discord)
```

## 📋 Prerequisites

### Required Accounts & Credentials

1. **n8n Instance** (Cloud or Self-hosted)
   - [Get started with n8n](https://n8n.io/)

2. **Telegram Bot** (Free)
   - Create bot via [@BotFather](https://t.me/botfather)
   - Get bot token
   - Enable file uploads

3. **Discord Bot** (Free)
   - Create application in [Discord Developer Portal](https://discord.com/developers/applications)
   - Get bot token
   - Create webhook URL for your channel
   - Grant necessary permissions

4. **Google Gemini API** (Free tier available)
   - Sign up at [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Generate API key
   - Free tier: 60 requests/minute

5. **Supabase** (Free tier available)
   - Create account at [Supabase](https://supabase.com/)
   - Create new project
   - Enable pgvector extension
   - Get API URL and anon/public key
   - Free tier: 500 MB database, 2 GB bandwidth

6. **PostgreSQL Database** (For chat memory)
   - Use Supabase's built-in PostgreSQL
   - Or external: Railway, Render, AWS RDS
   - Need connection string

### Technical Requirements

- n8n version 1.0.0 or higher with LangChain support
- pgvector extension enabled in PostgreSQL/Supabase
- Internet connection for API calls
- Webhook-capable Discord bot integration

## 🚀 Installation

### Step 1: Set Up Supabase Vector Database

1. **Create Supabase Project**:
   - Go to [Supabase Dashboard](https://app.supabase.com/)
   - Click "New Project"
   - Choose organization and name
   - Select region (choose closest to users)
   - Wait for project creation (~2 minutes)

2. **Enable pgvector Extension**:
   ```sql
   -- Run in SQL Editor
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

3. **Create Documents Table**:
   ```sql
   CREATE TABLE documents (
     id BIGSERIAL PRIMARY KEY,
     content TEXT,
     metadata JSONB,
     embedding VECTOR(768)
   );
   
   -- Create index for vector similarity search
   CREATE INDEX documents_embedding_idx 
   ON documents 
   USING ivfflat (embedding vector_cosine_ops)
   WITH (lists = 100);
   ```

4. **Get Credentials**:
   - Go to Settings → API
   - Copy:
     - Project URL
     - Anon/public key
     - Service role key (for n8n)

### Step 2: Set Up Telegram Bot

1. **Create Bot**:
   - Open Telegram, search for [@BotFather](https://t.me/botfather)
   - Send `/newbot`
   - Choose name and username
   - Copy the bot token (looks like: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)

2. **Configure Bot**:
   - Send `/setprivacy` to BotFather
   - Select your bot
   - Choose "Disable" (allows bot to receive all messages)
   - Send `/setcommands` (optional) and add:
     ```
     help - Show bot commands
     status - Check bot status
     ```

3. **Start Bot**:
   - Search for your bot in Telegram
   - Send `/start` to initialize

### Step 3: Set Up Discord Bot & Webhook

1. **Create Discord Application**:
   - Go to [Discord Developer Portal](https://discord.com/developers/applications)
   - Click "New Application"
   - Name your bot

2. **Create Bot**:
   - Go to "Bot" tab
   - Click "Add Bot"
   - **Important Settings**:
     - Enable "Message Content Intent"
     - Enable "Server Members Intent"
   - Copy bot token (keep secure!)

3. **Create Webhook**:
   - Open Discord server
   - Right-click your target channel → "Edit Channel"
   - Go to "Integrations" → "Webhooks"
   - Click "New Webhook"
   - Copy webhook URL (e.g., `https://discord.com/api/webhooks/...`)

4. **Invite Bot to Server**:
   - Go to OAuth2 → URL Generator in Developer Portal
   - Select scopes: `bot`, `applications.commands`
   - Select permissions: `Send Messages`, `Read Message History`
   - Copy generated URL and open in browser
   - Select server and authorize

### Step 4: Set Up PostgreSQL for Chat Memory

**Option A: Use Supabase's PostgreSQL** (Recommended)
   - Use the same Supabase project
   - Connection string format:
     ```
     postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
     ```
   - Get password from Supabase Dashboard → Settings → Database

**Option B: External PostgreSQL**
   - Use Railway, Render, or any PostgreSQL provider
   - Create database
   - Get connection string

### Step 5: Import n8n Workflow

1. Download `Discord_RAG_Agent.json`
2. Open n8n instance
3. Click **Workflows** → **Import from File**
4. Select the JSON file
5. Click **Import**

### Step 6: Configure Credentials

#### A. Telegram API

1. Click **"Telegram Trigger"** node
2. Click **Credentials** → **Create New**
3. Select **Telegram API**
4. Enter your bot token
5. Test connection
6. Save

Repeat for **"Get a file"** and **"Send Update Confirmation"** nodes.

#### B. Google Gemini API

1. Click **"Embeddings Google Gemini"** node
2. Click **Credentials** → **Create New**
3. Select **Google PaLM/Gemini API**
4. Enter your API key
5. Save

Use the same credential for **"Google Gemini Chat Model"** node.

#### C. Supabase API

1. Click **"Supabase Vector Store (Main)"** node
2. Click **Credentials** → **Create New**
3. Select **Supabase API**
4. Enter:
   - **Host**: Your project URL (e.g., `https://abc123.supabase.co`)
   - **Service Role Key**: From Supabase dashboard
5. Save

Use the same credential for **"Supabase Vector Store (Tool)"** node.

Configure table name: `documents` (in both Supabase nodes)

#### D. PostgreSQL

1. Click **"Postgres Chat Memory"** node
2. Click **Credentials** → **Create New**
3. Select **PostgreSQL**
4. Enter connection details:
   - **Host**: Database host
   - **Database**: Database name
   - **User**: Username
   - **Password**: Password
   - **Port**: 5432 (default)
   - **SSL**: Enable if using cloud provider
5. Test connection
6. Save

### Step 7: Configure Discord Webhook

You need to integrate with Discord separately since n8n receives webhook requests.

**Create Discord Bot Script** (Python example):
```python
import discord
import requests

WEBHOOK_URL = "https://your-n8n-instance.com/webhook/discord-rag"
DISCORD_BOT_TOKEN = "your-discord-bot-token"

client = discord.Client(intents=discord.Intents.default())

@client.event
async def on_message(message):
    # Ignore bot's own messages
    if message.author == client.user:
        return
    
    # Send to n8n webhook
    response = requests.post(WEBHOOK_URL, json={
        "question": message.content,
        "user_id": str(message.author.id),
        "username": message.author.name,
        "channel_id": str(message.channel.id)
    })
    
    # Send n8n response back to Discord
    if response.ok:
        answer = response.json().get('answer', 'No response')
        await message.channel.send(answer)

client.run(DISCORD_BOT_TOKEN)
```

Deploy this script to:
- Heroku (free tier)
- Railway
- Your own server
- Replit

### Step 8: Test the Workflow

#### Test Document Upload:
1. Open your Telegram bot
2. Send a PDF or text file
3. Wait for confirmation message: "Vector store successfully updated ✅"

#### Test Discord Query:
1. Go to your Discord server
2. Ask a question related to your uploaded documents
3. Bot should respond with relevant answer

### Step 9: Activate Workflow

1. Click the **Active** toggle in top-right corner
2. Workflow is now live!

## 📝 Usage Guide

### Uploading Documents

1. **Supported Formats**:
   - PDF (.pdf)
   - Word documents (.docx, .doc)
   - Text files (.txt)
   - Markdown (.md)
   - CSV (.csv)

2. **How to Upload**:
   - Open Telegram bot
   - Send document as file (not as photo)
   - Wait for confirmation
   - Document is now searchable

3. **Best Practices**:
   - Upload clear, well-structured documents
   - Avoid scanned images (use OCR first)
   - Break large documents into chapters
   - Name files descriptively

### Asking Questions in Discord

1. **Question Format**:
   - Ask naturally: "What is machine learning?"
   - Be specific: "How do I implement RAG in Python?"
   - Reference concepts: "Explain the vector embedding from chapter 3"

2. **Follow-Up Questions**:
   - Bot remembers context per user
   - You can ask: "Can you explain that in simpler terms?"
   - Reference previous answers: "What was that formula you mentioned?"

3. **Best Practices**:
   - Ask one question at a time
   - Be specific rather than vague
   - If answer is wrong, rephrase question
   - Provide context if needed

## ⚙️ Configuration Options

### Customize AI Behavior

Edit the **"AI Agent"** system message:

```
When formatting responses:
- Use **bold text** for headings instead of # markdown headers
- Keep numbered list items together (number + content on same line)
- Use proper Discord markdown:
  * **bold** for emphasis
  * *italic* for secondary emphasis
  * `code` for technical terms
  * ```code blocks``` for multi-line code
- Avoid using #### headers as they don't render in Discord

Additional instructions:
- Always cite sources when available
- If unsure, say "I don't have that information"
- Keep responses under 2000 characters (Discord limit)
- Use bullet points for lists
```

### Adjust Vector Search Relevance

In **"Supabase Vector Store (Tool)"** node:
- **Top K**: Number of relevant chunks to retrieve (default: 4)
- **Tool Description**: Customize to guide AI on when to search

Example:
```
"Call this tool to look up information about [YOUR TOPIC]. 
Use this when the user asks questions related to [SPECIFIC AREA]."
```

### Change Embedding Model

Currently uses Google Gemini embeddings (768 dimensions).

To switch to OpenAI:
1. Replace **"Embeddings Google Gemini"** node
2. Add **"Embeddings OpenAI"** node
3. Update vector dimensions in Supabase table (1536 for OpenAI)

### Modify Chat Memory Window

In **"Postgres Chat Memory"** node:
- **Context Window Size**: Number of previous messages to remember
- Default: Last 10 messages
- Increase for longer context, decrease for performance

## 🔧 Advanced Customization

### Multi-Language Support

Add language detection and translation:

```python
# In AI Agent system message
"Detect the language of the question and respond in the same language.
Supported languages: English, Spanish, French, German, Japanese"
```

### Add Command Handling

Modify Discord bot script to handle commands:

```python
@client.event
async def on_message(message):
    if message.content.startswith('!help'):
        await message.channel.send("Available commands: !ask, !clear, !status")
    elif message.content.startswith('!clear'):
        # Clear user's conversation history
        # Implement memory reset
    elif message.content.startswith('!ask'):
        question = message.content[5:]  # Remove '!ask '
        # Send to n8n...
```

### Add Multiple Knowledge Bases

Create separate tables for different topics:

```sql
CREATE TABLE tech_docs (id BIGSERIAL PRIMARY KEY, content TEXT, embedding VECTOR(768));
CREATE TABLE company_policies (id BIGSERIAL PRIMARY KEY, content TEXT, embedding VECTOR(768));
```

Use conditional logic in n8n to route to different tables based on channel or command.

### Implement Access Control

Add user role checking in Discord bot:

```python
async def check_permissions(message):
    member = message.author
    # Only allow users with specific role
    if "Premium" in [role.name for role in member.roles]:
        return True
    return False
```

## 📊 Understanding the Technology

### What is RAG?

RAG (Retrieval-Augmented Generation) combines:
1. **Retrieval**: Semantic search through document embeddings
2. **Augmentation**: Adding relevant context to the prompt
3. **Generation**: AI creates answer using both context and its training

**Benefits**:
- More accurate than pure AI generation
- Sources can be updated without retraining
- Reduces hallucinations
- Can cite specific sources

### How Vector Embeddings Work

1. **Text Chunking**: Documents split into smaller pieces
2. **Embedding**: Each chunk converted to 768-dimensional vector
3. **Storage**: Vectors stored in Supabase with pgvector
4. **Search**: User question converted to vector, similar vectors retrieved
5. **Response**: AI generates answer using retrieved chunks

### Memory Architecture

- **Per-User Sessions**: Each Discord user ID = unique session
- **PostgreSQL Storage**: Conversation history stored in database
- **Context Window**: Last N messages used for context
- **Automatic Pruning**: Old conversations can be archived/deleted

## ⚠️ Important Notes

### API Rate Limits

**Google Gemini**:
- Free tier: 60 requests/minute
- Each query uses 1 request
- Embedding: 1 request per document chunk
- Monitor at [Google AI Studio](https://makersuite.google.com/app/apikey)

**Supabase**:
- Free tier: 500 MB database
- 2 GB bandwidth/month
- 50,000 monthly active users
- Upgrade if exceeding

**Discord**:
- 2000 character limit per message
- Rate limits: 5 messages/5 seconds per channel
- Bot must have proper permissions

### Data Privacy

**Sensitive Information**:
- Don't upload confidential documents to public bots
- User questions and conversation history stored in database
- Consider encryption for sensitive data
- Implement data retention policies

**GDPR Compliance**:
- Allow users to request data deletion
- Provide privacy policy
- Log data access
- Implement user consent mechanisms

### Performance Considerations

**Document Size**:
- Large PDFs take longer to process
- Consider splitting documents >100 pages
- Use batching for bulk uploads

**Concurrent Users**:
- PostgreSQL handles multiple connections
- Supabase auto-scales
- Monitor resource usage

**Response Time**:
- Typical: 2-5 seconds per query
- Factors: Vector search time, AI generation, network latency
- Optimize by caching common queries

## 🐛 Troubleshooting

### Documents Not Uploading

**Symptom**: Telegram bot receives file but no confirmation

**Solutions**:
1. Check Supabase credentials are correct
2. Verify pgvector extension is enabled
3. Check table exists and schema matches
4. Review n8n execution logs
5. Test with small text file first

### Bot Not Responding in Discord

**Symptom**: Questions sent but no replies

**Solutions**:
1. Verify Discord bot script is running
2. Check webhook URL is correct
3. Confirm n8n webhook node is active
4. Test webhook directly with curl:
   ```bash
   curl -X POST https://your-n8n-instance.com/webhook/discord-rag \
   -H "Content-Type: application/json" \
   -d '{"question":"test","user_id":"123","username":"test","channel_id":"456"}'
   ```
5. Check Discord bot has message permissions

### Incorrect or Irrelevant Answers

**Symptom**: Bot responds but answers are wrong

**Solutions**:
1. **Improve Document Quality**:
   - Upload more comprehensive documents
   - Ensure documents are text-searchable (not scans)
   - Remove duplicate or conflicting information

2. **Adjust Retrieval**:
   - Increase "Top K" in vector store (retrieve more chunks)
   - Modify tool description to be more specific
   - Check embedding quality

3. **Improve Prompting**:
   - Update system message to be more specific
   - Add examples of good responses
   - Instruct to cite sources

### Memory Not Working

**Symptom**: Bot doesn't remember previous conversation

**Solutions**:
1. Check PostgreSQL connection is active
2. Verify session key is using correct user ID
3. Check chat memory table exists
4. Test with fresh conversation
5. Review memory window size setting

### Rate Limit Errors

**Symptom**: "429 Too Many Requests" or similar errors

**Solutions**:
1. **Google Gemini**: Add delay between requests
2. **Discord**: Implement message queuing
3. **Supabase**: Upgrade plan or optimize queries
4. Add retry logic with exponential backoff

## 🔒 Security Best Practices

- **Never commit credentials** to repositories
- **Use environment variables** for all secrets
- **Enable SSL** for database connections
- **Rotate API keys** every 90 days
- **Implement rate limiting** on webhook endpoint
- **Validate webhook signatures** (Discord webhooks)
- **Sanitize user input** to prevent injection
- **Monitor usage** for unusual activity
- **Set up alerts** for errors or suspicious activity

## 💡 Pro Tips

1. **Organize Documents**: Upload related documents in batches, use consistent naming
2. **Test Queries**: Keep a list of test questions to verify bot quality
3. **User Feedback**: Add reaction buttons in Discord to rate answers
4. **Analytics**: Track most common questions to improve knowledge base
5. **Regular Updates**: Periodically update documents to keep information current
6. **Backup Database**: Export Supabase data regularly
7. **Monitor Costs**: Set up billing alerts in Supabase and Google Cloud
8. **Version Documents**: Track document versions in metadata
9. **Use Tags**: Add tags to documents for better organization
10. **Create FAQ**: Based on common questions, create dedicated FAQ document

## 📈 Scaling Considerations

### For High Volume (100+ users):

1. **Database Optimization**:
   - Upgrade Supabase plan
   - Add more indexes
   - Implement caching layer (Redis)

2. **Multiple Bot Instances**:
   - Deploy Discord bot replicas
   - Load balance across instances
   - Use message queue (RabbitMQ)

3. **Dedicated Infrastructure**:
   - Self-host PostgreSQL
   - Use dedicated vector database (Pinecone, Weaviate)
   - Deploy n8n on own infrastructure

### For Enterprise:

1. **Enhanced Security**:
   - Implement SSO
   - Add audit logging
   - Use private network
   - Encrypt at rest and in transit

2. **Advanced Features**:
   - Multi-tenancy support
   - Custom embedding models
   - Advanced analytics
   - Integration with enterprise tools

## 🤝 Contributing

Ideas for improvements:
- Add support for more document types (Excel, PPT)
- Implement semantic caching for faster responses
- Add source citation with page numbers
- Create admin dashboard for monitoring
- Add multi-modal support (images, audio)
- Implement federated search across multiple sources
- Add confidenc
