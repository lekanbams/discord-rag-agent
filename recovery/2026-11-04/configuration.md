# Recovered configuration

## Supabase database contract

Source: `sql/v2.sql` and `ragb/services.py` at the recorded source commit. This describes the repository's expected schema, not an inspection of live Supabase.

- Extension: `vector` in schema `extensions`.
- Table: `public.ragb_documents_v2`.
- Columns: `id` bigint generated identity primary key; `chunk_key` unique required text; `content` required text; `metadata` required jsonb; `embedding` required `extensions.vector(768)`.
- RPC: `public.ragb_match_documents_v2(query_embedding, match_threshold, match_count, model_name)`.
- Search: cosine similarity, restricted to metadata embedding_model matching model_name; result limit is at most 10. Application requests 4 matches.
- RLS enabled. SQL grants table/sequence access and RPC execution to `service_role`, and revokes RPC access from PUBLIC, anon and authenticated. No client-facing RLS policies or additional vector index are defined in this SQL.
- v1 tables are left untouched.
- Embeddings are normalized by the application after OpenAI returns 768 dimensions.
- Document metadata: filename, SHA-256 hash of original file bytes, chunk number and embedding_model.
- Ingestion: 1,200-character chunks starting every 1,000 characters, upserted by chunk_key. Changed file contents coexist until manually removed.

## Environment variables

| Variable | Value or recovery source |
| --- | --- |
| CHAT_MODEL | gpt-4.1-mini, recorded in successful setup |
| EMBEDDING_MODEL | text-embedding-3-small, recorded in successful setup |
| MATCH_THRESHOLD | 0.65 in repository template and code default; actual live override unknown |
| DISCORD_BOT_TOKEN | Private token, recover from existing variables or Discord Developer Portal |
| DISCORD_GUILD_ID | Personal Discord server ID, actual number not recovered |
| ADMIN_CHANNEL_ID | Private unanswered-alert channel ID, actual number not recovered |
| ADMIN_ROLE_ID | Admin role ID, actual number not recovered |
| OPENAI_API_KEY | Private API key, recover securely or issue a replacement |
| SUPABASE_URL | Existing v1/v2 project's URL, actual value not recovered |
| SUPABASE_SERVICE_ROLE_KEY | Private backend key, recover from project settings |
| TELEGRAM_BOT_TOKEN | Optional private bot token |
| TELEGRAM_ADMIN_IDS | Optional comma-separated numeric Telegram user IDs, actual numbers not recovered |

Required at startup: all of the above except MATCH_THRESHOLD and both Telegram variables. For Telegram ingestion, provide both Telegram variables.

## Runtime and storage

- Docker base: python:3.12-slim; working directory `/app`; command `python bot.py`.
- Container user: `ragb`, UID 10001. Mounted `/app/data` must be writable by that user.
- Repository Compose volume: `ragb-data:/app/data`. The actual Zeabur mount was not verified.
- SQLite file: `/app/data/memory.sqlite`. Stores conversation messages only, with session, role, content and creation time.
- Discord and Telegram use outbound connections; no public HTTP port is required by this application.
- Run one active copy for a given bot token. A second Telegram poller can cause HTTP 409 conflicts.
- Telegram webhook removal on startup preserves queued updates. Do not start a second production bot just to test a restore.
- Requirements specify version ranges, not an exact installed dependency lock. Rebuilding may resolve newer versions within those ranges. No running-container package inventory was obtained.

## Behaviour preserved in source

No public source lines in answers. Insufficient evidence triggers a private admin alert. The bot confirms admin notification only if sending succeeds. The approved missing-answer wording is preserved in `ragb/core.py`.

## Original setup notes

`deploy/SETUP.md` is retained as historical setup guidance. Its mentions of public filename citations and pending live verification predate later changes and the successful October 13 upload. Use current code and this recovery record for those points.
