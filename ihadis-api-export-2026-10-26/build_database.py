#!/usr/bin/env python3
"""Build the API SQLite database offline from the committed JSON parts."""
import hashlib
import json
from pathlib import Path
import sqlite3


def main():
    root = Path(__file__).resolve().parent
    folder = root / 'hosting' if (root / 'hosting').exists() else root
    read = lambda path: json.loads(path.read_text(encoding='utf-8'))
    dump = lambda value: json.dumps(value, ensure_ascii=False, separators=(',', ':'))
    catalog = read(folder / 'catalog.json')
    checksums = read(folder / 'checksums.json')
    for name, expected in checksums.items():
        if name.endswith('.json'):
            assert hashlib.sha256((folder / name).read_bytes()).hexdigest() == expected, name
    temporary = folder / 'hadith.sqlite.tmp'
    temporary.unlink(missing_ok=True)
    db = sqlite3.connect(temporary)
    db.executescript('''
        CREATE TABLE books (id INTEGER PRIMARY KEY, slug TEXT UNIQUE NOT NULL, data TEXT NOT NULL);
        CREATE TABLE chapters (book_id INTEGER, id INTEGER, data TEXT NOT NULL, PRIMARY KEY(book_id,id));
        CREATE TABLE sections (book_id INTEGER, chapter_id INTEGER, id INTEGER, data TEXT NOT NULL,
                               PRIMARY KEY(book_id,chapter_id,id));
        CREATE TABLE hadiths (book_id INTEGER, id TEXT, chapter_id INTEGER, section_id INTEGER,
                              position INTEGER, data TEXT NOT NULL, PRIMARY KEY(book_id,id));
        CREATE INDEX hadith_chapter ON hadiths(book_id,chapter_id,position);
    ''')
    total = 0
    for book in catalog:
        db.execute('INSERT INTO books VALUES (?,?,?)', (book['id'], book['slug'], dump(book)))
        for chapter in read(folder / book['chaptersFile']):
            db.execute('INSERT INTO chapters VALUES (?,?,?)', (book['id'], chapter['id'], dump(chapter)))
        position = 0
        sections = {}
        for part in book['parts']:
            payload = read(folder / part['file'])
            assert payload['count'] == part['count'] == len(payload['hadiths'])
            for h in payload['hadiths']:
                assert h['bookId'] == book['id']
                db.execute('INSERT INTO hadiths VALUES (?,?,?,?,?,?)',
                           (book['id'], h['id'], h['chapterId'], h['sectionId'], position, dump(h)))
                if h['section'] is not None:
                    key = (book['id'], h['chapterId'], h['sectionId'])
                    if key in sections:
                        assert sections[key] == h['section']
                    sections[key] = h['section']
                position += 1
        for key, section in sections.items():
            db.execute('INSERT INTO sections VALUES (?,?,?,?)', (*key, dump(section)))
        assert position == book['downloadedCount'] == book['hadithCount']
        total += position
    assert total == read(folder / 'manifest.json')['hadiths']
    assert db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
    db.commit()
    db.close()
    temporary.replace(folder / 'hadith.sqlite')
    # The rebuilt database is logically equivalent, but SQLite bytes can differ.
    checksums['hadith.sqlite'] = hashlib.sha256((folder / 'hadith.sqlite').read_bytes()).hexdigest()
    (folder / 'checksums.json').write_text(json.dumps(checksums, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Built {total:,} records: {folder / "hadith.sqlite"}')


if __name__ == '__main__':
    main()
