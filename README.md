# RAG-B v2

A VPS-ready Discord knowledge-base bot with Gemini, Supabase and optional admin-only Telegram document uploads. This branch replaces the n8n runtime. The `main` branch preserves v1.

When documents do not support an answer, RAG-B alerts a configured private admin channel with the question, user and original message link. It confirms notification only after the alert succeeds. Admins handle tickets manually.

See [setup and live verification](deploy/SETUP.md) for credentials, database SQL, Discord permissions, VPS instructions, limits and the demo recording outline. No credentials are included. Live verification and recording are pending.

```sh
python -m unittest discover -s tests -v
cp env.example .env
# Fill credentials and apply sql/v2.sql, then:
docker compose up -d --build
```

[Original v1 documentation](deploy/V1-README.md) and `Discord_RAG_Agent.json` are kept for reference only. They are not used by v2.
