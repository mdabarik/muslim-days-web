#!/usr/bin/env python3
"""Resume a public Bengali iHadis snapshot, preserving the original API responses."""
import concurrent.futures
import hashlib
import json
import re
from pathlib import Path
import subprocess
import threading
import time
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent
BASE = 'https://ihadis.com/api/v1/trpc/'
LOCK = threading.Lock()
LAST_REQUEST = 0.0
STOP = threading.Event()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    tmp.replace(path)


def fetch(procedure, args):
    global LAST_REQUEST
    key = hashlib.sha256(json.dumps([procedure, args], sort_keys=True).encode()).hexdigest()
    path = ROOT / 'raw' / procedure / (key + '.json')
    if path.exists():
        return json.loads(path.read_text())['response']['result']['data']['json']
    url = BASE + procedure + '?input=' + quote(json.dumps({'json': args}, separators=(',', ':')))
    for attempt in range(6):
        if STOP.is_set():
            raise RuntimeError('Download stopped after access/rate-limit error')
        with LOCK:
            time.sleep(max(0, LAST_REQUEST + 0.25 - time.monotonic()))
            LAST_REQUEST = time.monotonic()
        result = subprocess.run(['curl', '-sS', '--max-time', '60', '--compressed',
                                 '-w', '\n%{http_code}', url], capture_output=True)
        body, _, status = result.stdout.rpartition(b'\n')
        code = int(status) if status.isdigit() else 0
        if code in (401, 403):
            STOP.set()
            raise RuntimeError(f'Access denied: HTTP {code} {procedure}')
        if result.returncode == 0 and code == 200:
            response = json.loads(body)
            if 'result' not in response:
                raise RuntimeError(str(response)[:500])
            write_json(path, {'procedure': procedure, 'input': args, 'url': url,
                             'fetchedAt': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                             'response': response})
            return response['result']['data']['json']
        if code == 429:
            STOP.set()
            raise RuntimeError('HTTP 429: stop and resume later; cache has been saved')
        if code and code < 500:
            raise RuntimeError(f'HTTP {code}: {body.decode(errors="replace")[:500]}')
        time.sleep(min(30, 2 ** attempt))
    raise RuntimeError(f'Retry limit: {procedure} {args}')


def download_chapter(book, chapter):
    cursor, seen, records, sections = 1, set(), [], {}
    detail = None
    while cursor is not None:
        if cursor in seen:
            raise ValueError('Repeated cursor')
        seen.add(cursor)
        data = fetch('hadith.chapterHadithsPaginated', {
            'bookId': book['id'], 'chapterId': chapter['id'], 'languageId': 'bn',
            'limit': 100, 'cursor': cursor})
        if detail is None:
            assert data['book']['id'] == book['id']
            assert data['chapter']['id'] == chapter['id']
            detail = data['chapter']
            total = data['total']
        for section in data['sections']:
            previous = sections.get(str(section['id']))
            if previous is not None and previous != section:
                raise ValueError('Section changed between pages')
            sections[str(section['id'])] = section
        records.extend(data['hadiths'])
        cursor = data['nextCursor']
    # The chapter endpoint omits canonical aliases. Its first-page total includes them.
    # Fetch those explicitly through byId, using the published chapter range.
    span = re.fullmatch(r'(\d+)\s*-\s*(\d+)', chapter['range'])
    if not span:
        raise ValueError(f'Unsupported chapter range: {chapter["range"]}')
    first, last = map(int, span.groups())
    if len(records) != total and last - first + 1 != total:
        raise ValueError(f'Range and total disagree: {book["slug"]}/{chapter["id"]}')
    present = {str(h['id']) for h in records}
    prefixes = {re.fullmatch(r'(.*?)(\d+)', value).group(1) for value in present}
    if len(prefixes) != 1:
        raise ValueError(f'Ambiguous ID prefix: {book["slug"]}/{chapter["id"]}')
    prefix = prefixes.pop()
    for number in (range(first, last + 1) if len(records) < total else []):
        hadith_id = prefix + str(number)
        if hadith_id not in present:
            h = fetch('hadith.byId', {'bookId': book['id'], 'hadithId': hadith_id, 'languageId': 'bn'})
            assert h['id'] == hadith_id and h['bookId'] == book['id']
            assert h['chapterId'] == chapter['id']
            section = h['section']
            if section is not None:
                sections[str(section['id'])] = section
            records.append({**h, 'sectionId': section['id'] if section else -1})
    records.sort(key=lambda h: int(h['id'][len(prefix):]))
    ids = [str(h['id']) for h in records]
    if len(ids) != len(set(ids)) or len(ids) != total:
        raise ValueError(f'Chapter count mismatch: {book["slug"]}/{chapter["id"]}: {len(ids)}/{total}')
    for h in records:
        assert h['bookId'] == book['id']
        if str(h['sectionId']) not in sections:
            original = fetch('hadith.byId', {'bookId': book['id'], 'hadithId': h['id'], 'languageId': 'bn'})
            if original['section'] is None:
                assert h['sectionId'] == -1
                h['section'] = None
            else:
                sections[str(original['section']['id'])] = original['section']
                assert h['sectionId'] == original['section']['id']
    output = {'book': book, 'chapter': {**chapter, **detail},
              'sections': list(sections.values()), 'hadiths': records, 'count': len(records)}
    write_json(ROOT / 'chapters' / book['slug'] / f'{chapter["id"]:04d}.json', output)
    return len(records)


def main():
    books = fetch('book.list', {'languageId': 'bn'})
    write_json(ROOT / 'catalog-source.json', books)
    tasks = []
    for book in books:
        chapters = fetch('chapter.list', {'bookId': book['id'], 'languageId': 'bn'})
        if len(chapters) != book['chapterCount']:
            raise ValueError('Catalog chapter count mismatch')
        write_json(ROOT / 'chapters' / book['slug'] / 'index.json', chapters)
        tasks.extend((book, chapter) for chapter in chapters)
    print(f'Start: {len(books)} books, {len(tasks)} chapters, {sum(b["hadithCount"] for b in books)} advertised records', flush=True)
    count = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(download_chapter, b, c): (b, c) for b, c in tasks}
        for done, future in enumerate(concurrent.futures.as_completed(futures), 1):
            try:
                count += future.result()
            except Exception:
                STOP.set()
                for pending in futures:
                    pending.cancel()
                raise
            if done % 20 == 0 or done == len(tasks):
                print(f'{done}/{len(tasks)} chapters; {count} records', flush=True)
    write_json(ROOT / 'download-status.json', {'complete': True, 'books': len(books),
               'chapters': len(tasks), 'records': count})
    print('Download finished. Run package.py to validate and build the hosting files.', flush=True)


if __name__ == '__main__':
    main()
