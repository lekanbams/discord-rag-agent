# RAG-B v2 recovery record

Prepared 2026-11-04 from the repository and recovered deployment conversation.

## What this preserves

- Original v2 application source at commit `485177996d6ab835a85694383c55840bcc83a75b`.
- `supabase-schema.sql`: byte-for-byte copy of that commit's `sql/v2.sql`.
- `env.example`: byte-for-byte copy of that commit's environment template, without credentials.
- Dockerfile, compose.yaml, requirements.txt and application source remain at the repository root.
- `configuration.md`: model settings, database contract, storage behavior and known limitations.
- `RESTORE.md`: steps for rebuilding the application and checking it works.
- `export_supabase.py`: optional read-only exporter for existing v2 knowledge-base rows.
- `sqlite-schema.sql`: the local conversation schema reproduced from `ragb/core.py`.
- `manifest.json`: source identity and file hashes.

This is a rebuild package, not a snapshot of the running server or a live Supabase database dump. No live credentials, numeric Discord/Telegram IDs, Supabase project URL, original uploaded documents, database rows or conversation history have been captured. Repository branch head is known; the exact commit running on Zeabur has not been independently checked. Earlier screenshots show matching file structure and bot code.

## Confirmed history

The October 13 deployment conversation recorded OpenAI chat model `gpt-4.1-mini`, embedding model `text-embedding-3-small` with 768 dimensions, and a successful Telegram response: `Knowledge base updated: 10 chunks indexed.` The same Supabase project used by v1 was reused with a separate v2 table. Actual project URL and IDs were not recovered.

## What can be recreated

The application automatically creates `/app/data/memory.sqlite` when it starts. An empty replacement loses previous conversation context, but does not remove Supabase documents or Discord messages. Local history is limited to ten recent messages within one hour per session; messages older than seven days are pruned on writes.

Telegram document bytes are downloaded into memory and parsed directly. This code does not keep the original uploaded files on disk. Existing chunks/embeddings are in Supabase. Preserve that project or export its rows. To rebuild an empty database, obtain the original documents and upload them again.

The source code can recreate the Supabase table and RPC, but cannot recreate missing document contents, credentials or account IDs.

## Before turning off Zeabur

1. Save actual environment values privately, including tokens, Supabase URL and Discord/Telegram IDs. Do not commit them to this public repository.
2. Keep the existing Supabase project, or export its v2 documents separately. Zeabur's service backup does not capture external Supabase data.
3. If old conversation history matters, take a consistent SQLite backup before suspending the container. Otherwise accept that a new deployment starts with empty chat history.
4. Do not delete the Zeabur service, volume or server until required private values and data have been secured. Suspending is reversible but is not a durable off-platform backup.

No deployment was stopped or modified while preparing this record.
