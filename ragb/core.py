"""Credential-independent answer validation and persistent conversation storage."""
import json
import sqlite3

MISSING = "I don't have an answer to this in the knowledge base."

def supported_answer(raw, documents):
    data = json.loads(raw)
    refs = data.get('sources', [])
    if data.get('supported') is not True or not isinstance(data.get('answer'), str) or not data['answer'].strip():
        return None
    if not refs or any(type(i) is not int or i < 1 or i > len(documents) for i in refs):
        return None
    sources = []
    for i in dict.fromkeys(refs):
        meta = documents[i-1].get('metadata') or {}
        sources.append(str(meta.get('filename', 'Knowledge base document')).replace('@', '＠'))
    return data['answer'].strip() + '\n\nSources: ' + ', '.join(dict.fromkeys(sources))

def split_message(text, limit=1900):
    return [text[i:i+limit] for i in range(0, len(text), limit)] or ['']

class Memory:
    def __init__(self, path):
        self.db = sqlite3.connect(path)
        self.db.execute('CREATE TABLE IF NOT EXISTS messages (session TEXT, role TEXT, content TEXT, created REAL DEFAULT (unixepoch()))')
        self.db.commit()
    def history(self, session):
        rows = self.db.execute('SELECT role, content FROM messages WHERE session=? AND created > unixepoch()-3600 ORDER BY rowid DESC LIMIT 10', (session,)).fetchall()
        return list(reversed(rows))
    def add(self, session, question, answer):
        self.db.executemany('INSERT INTO messages(session,role,content) VALUES(?,?,?)', [(session,'user',question),(session,'assistant',answer)])
        self.db.execute('DELETE FROM messages WHERE created < unixepoch()-604800')
        self.db.commit()
