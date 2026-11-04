# Validation, 2026-11-04

- All 15 existing application unit tests passed in an isolated Python 3.12 environment with the repository requirements installed.
- Supabase SQL and env.example recovery copies match their original source bytes.
- Source hashes match manifest.json.
- SQLite reference schema created a working in-memory database.
- Exporter was tested with mocked paginated responses and issued GET requests only.
- No live API calls, Supabase export, server inspection, credential verification or end-to-end restore were performed.
