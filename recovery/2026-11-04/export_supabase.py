"""Read-only export of RAG-B v2 rows. Credentials come from the environment.

Run with no concurrent document uploads. Output contains private document text.
Store it outside the public repository. This is not a full Supabase project dump.
"""
import argparse
import datetime
import json
import os
from pathlib import Path
import tempfile
import urllib.error
import urllib.parse
import urllib.request


def export_rows(base, key):
    rows = []
    offset = 0
    while True:
        query = urllib.parse.urlencode({
            'select': 'id,chunk_key,content,metadata,embedding',
            'order': 'id.asc', 'limit': 500, 'offset': offset,
        })
        request = urllib.request.Request(
            base + '/rest/v1/ragb_documents_v2?' + query,
            headers={'apikey': key, 'Authorization': 'Bearer ' + key},
        )
        with urllib.request.urlopen(request, timeout=60) as response:
            batch = json.load(response)
        if not isinstance(batch, list):
            raise ValueError('Expected a list of document rows')
        if not batch:
            break
        rows.extend(batch)
        offset += len(batch)
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path, help='New private JSON file outside any Git checkout')
    args = parser.parse_args()
    output = args.output.expanduser().resolve()
    if output.exists():
        parser.error('Output already exists; choose a new filename')
    if any((parent / '.git').exists() for parent in [output.parent, *output.parent.parents]):
        parser.error('Choose an output location outside Git to avoid publishing documents')
    base = os.environ.get('SUPABASE_URL', '').rstrip('/')
    key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY', '')
    parsed = urllib.parse.urlparse(base)
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password or parsed.path not in ('', '/') or parsed.query or parsed.fragment:
        parser.error('SUPABASE_URL must be an HTTPS project origin without credentials, path, query or fragment')
    if not key:
        parser.error('Set SUPABASE_SERVICE_ROLE_KEY privately in the environment')
    try:
        rows = export_rows(base, key)
        payload = {
            'format': 'ragb-v2-document-export-v1',
            'created_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'table': 'public.ragb_documents_v2', 'row_count': len(rows), 'rows': rows,
            'scope': 'Document rows only. No schema, other tables, auth or Storage objects.',
        }
        output.parent.mkdir(parents=True, exist_ok=True)
        # Fetch all pages first, then publish the complete private file atomically.
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=output.parent,
                                             prefix='.ragb-export-', delete=False) as handle:
                temporary = Path(handle.name)
                json.dump(payload, handle, ensure_ascii=False, indent=2)
                handle.write('\n')
            os.chmod(temporary, 0o600)
            os.link(temporary, output)  # Never overwrite an existing destination.
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
        print(f'Exported {len(rows)} rows to {output}. Keep this file private.')
    except urllib.error.HTTPError as error:
        raise SystemExit(f'Export failed: HTTP {error.code}. No complete output was saved.') from None
    except (urllib.error.URLError, ValueError, OSError):
        raise SystemExit('Export failed. Check connection, credentials and output path. No complete output is confirmed.') from None


if __name__ == '__main__':
    main()
