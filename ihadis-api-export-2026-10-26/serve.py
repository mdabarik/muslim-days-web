#!/usr/bin/env python3
"""Small dependency-free read-only API. Put an HTTPS reverse proxy in front for hosting."""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import sqlite3
from urllib.parse import parse_qs, unquote, urlparse


class Handler(BaseHTTPRequestHandler):
    def respond(self, value, status=200):
        body = json.dumps(value, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'public, max-age=3600' if status == 200 else 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        url = urlparse(self.path)
        path = [unquote(p) for p in url.path.strip('/').split('/')]
        q = parse_qs(url.query)
        try:
            with sqlite3.connect(f'file:{self.server.database}?mode=ro', uri=True) as db:
                if url.path == '/health':
                    db.execute('SELECT 1 FROM books LIMIT 1').fetchone()
                    return self.respond({'ok': True})
                if url.path == '/api/v1/trpc/hadith.byId':
                    args = json.loads(q.get('input', ['{}'])[0]).get('json', {})
                    if args.get('languageId', 'bn') != 'bn':
                        return self.respond({'error': 'Only bn is included'}, 400)
                    h = db.execute('SELECT data FROM hadiths WHERE book_id=? AND id=?',
                                   (int(args['bookId']), str(args['hadithId']))).fetchone()
                    if not h:
                        return self.respond({'error': 'Hadith not found'}, 404)
                    return self.respond({'result': {'data': {'json': json.loads(h[0])}}})
                if path == ['books']:
                    return self.respond([json.loads(r[0]) for r in db.execute('SELECT data FROM books ORDER BY id')])
                if len(path) >= 2 and path[0] == 'books':
                    book = db.execute('SELECT id,data FROM books WHERE slug=?', (path[1],)).fetchone()
                    if not book:
                        return self.respond({'error': 'Book not found'}, 404)
                    if len(path) == 2:
                        return self.respond(json.loads(book[1]))
                    if path[2:] == ['chapters']:
                        return self.respond([json.loads(r[0]) for r in db.execute(
                            'SELECT data FROM chapters WHERE book_id=? ORDER BY id', (book[0],))])
                    if len(path) == 4 and path[2] == 'hadiths':
                        h = db.execute('SELECT data FROM hadiths WHERE book_id=? AND id=?', (book[0], path[3])).fetchone()
                        return self.respond(json.loads(h[0]) if h else {'error': 'Hadith not found'}, 200 if h else 404)
                    if len(path) == 5 and path[2] == 'chapters' and path[4] == 'hadiths':
                        chapter_id = int(path[3])
                        if not db.execute('SELECT 1 FROM chapters WHERE book_id=? AND id=?', (book[0], chapter_id)).fetchone():
                            return self.respond({'error': 'Chapter not found'}, 404)
                        limit = min(250, max(1, int(q.get('limit', ['100'])[0])))
                        offset = max(0, int(q.get('offset', ['0'])[0]))
                        rows = db.execute('SELECT data FROM hadiths WHERE book_id=? AND chapter_id=? ORDER BY position LIMIT ? OFFSET ?',
                                          (book[0], chapter_id, limit, offset)).fetchall()
                        total = db.execute('SELECT count(*) FROM hadiths WHERE book_id=? AND chapter_id=?', (book[0], chapter_id)).fetchone()[0]
                        return self.respond({'total': total, 'offset': offset, 'limit': limit,
                                             'nextOffset': offset + limit if offset + limit < total else None,
                                             'hadiths': [json.loads(r[0]) for r in rows]})
                return self.respond({'error': 'Not found'}, 404)
        except (ValueError, KeyError, TypeError, AttributeError):
            return self.respond({'error': 'Invalid request parameters'}, 400)
        except sqlite3.Error:
            return self.respond({'error': 'Database unavailable'}, 503)


if __name__ == '__main__':
    here = Path(__file__).resolve().parent
    default_db = here / 'hadith.sqlite'
    if not default_db.exists():
        default_db = here / 'hosting' / 'hadith.sqlite'
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', type=Path, default=default_db)
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8080)
    args = parser.parse_args()
    if not args.db.is_file():
        parser.error(f'Database missing: {args.db}')
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    server.database = args.db.resolve()
    print(f'Listening at http://{args.host}:{args.port}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()
