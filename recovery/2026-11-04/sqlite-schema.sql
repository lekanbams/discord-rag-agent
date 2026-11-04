-- Reproduced from ragb/core.py. Automatically created by the application.
-- This is schema only, not existing conversation data.
CREATE TABLE IF NOT EXISTS messages (
    session TEXT,
    role TEXT,
    content TEXT,
    created REAL DEFAULT (unixepoch())
);
