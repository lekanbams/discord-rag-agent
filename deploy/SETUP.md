# RAG-B v2 setup

This branch replaces n8n with a Python service. Discord and optional Telegram use outbound connections, so no public HTTP port or domain is needed. Supabase and Gemini remain external services. No credentials are included.

## Before starting

1. Provide VPS OS/RAM/CPU details. Install Docker Engine and Compose using the official instructions for that OS.
2. Run `sql/v2.sql` in Supabase SQL Editor after reviewing it. This creates a separate v2 table and restricted retrieval function. It does not migrate or alter v1 documents. Re-upload demo documents unless the previous embedding model is verified compatible.
3. Copy `env.example` to `.env`, fill values locally and run `chmod 600 .env`. Never commit this file. Verify Gemini model access. The chosen embedding model must support 768 dimensions and retrieval task types.
4. Enable Discord Message Content Intent. Invite the bot with View Channels, Send Messages and Read Message History permissions. Give it access to the admin-only channel and permission to mention the chosen admin role. Keep the admin role mentionable or grant the bot the appropriate mention permission. Review channel overrides for all member roles, not only @everyone.
5. Optional Telegram: set bot token and comma-separated admin user IDs. Remove any old Telegram webhook before using long polling. Only approved admins in private chats can upload. Accepted formats: PDF, DOCX, TXT, MD and CSV, maximum 5 MB. Scanned PDFs need OCR elsewhere.

## Run on VPS

Clone this repository and check out `v2`. From the repository directory:

```sh
docker compose up -d --build
docker compose logs --tail=100
```

Persistent chat history is in the named Docker volume. Do not run two instances of the same Discord/Telegram bot. Restart policy handles process failure and server restart when Docker starts at boot. No port is published. Keep VPS SSH access restricted and back up the data volume and Supabase documents.

## Live verification required

- Upload a small FAQ document and confirm indexed chunks.
- Ask a supported question using `!ask` or a mention. Check answer and filename citation.
- Ask a follow-up and check retrieval uses context.
- Ask something outside the FAQ. Confirm the private admin alert contains question, user and message link, and the public reply confirms notification.
- Temporarily remove admin send permission. Confirm the public reply says notification failed.
- Test database/API failure separately. It must not claim missing context.
- Check regular members cannot see the admin channel.
- Restart the container and confirm reconnection and memory persistence.
- Test unauthorized Telegram upload and duplicate file upload.

The retrieval threshold 0.65 is an initial configuration, not a calibrated guarantee. Tune it using supported, paraphrased and unrelated demo questions. Model evidence checks reduce guessing but cannot guarantee factual accuracy. Model and database calls are live-test blockers until credentials exist.

## Demo recording, 60-90 seconds

1. Show RAG-B online in your personal Discord server.
2. Show Telegram FAQ upload and success confirmation.
3. Ask a question covered by the FAQ. Show answer and source.
4. Ask a relevant follow-up.
5. Ask a clearly absent question. Show the missing-answer reply.
6. Switch to the private admin channel and show the real alert.
7. Explain that an admin takes over manually. Automatic tickets are a later feature.

Record only after live verification. Hide tokens, user IDs and unrelated conversations. Do not portray a simulated interaction as a live demonstration.

## Current scope and limits

SQLite replaces the n8n Postgres memory node for a single VPS instance. Sessions separate server/channel/user, retain a one-hour context window and prune stored messages older than seven days on writes. Uploads are single-document atomic database writes. Duplicate bytes are upserted, changed documents coexist until removed manually. There is no automatic ticket creation, OCR, automatic document replacement, dashboard or distributed deployment. Detailed alerts are stored in Discord. Admin-only delivery depends on correct server permissions. Model failures return a temporary-error reply. Malformed model output is treated as an error, not a missing-answer handoff.
