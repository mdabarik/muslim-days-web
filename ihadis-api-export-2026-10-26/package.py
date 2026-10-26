#!/usr/bin/env python3
"""Validate all chapters, then build 250-record JSON volumes and a SQLite API store."""
import hashlib
import json
import re
from pathlib import Path
import sqlite3
import zipfile
from download import ROOT, write_json


def dump(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(',', ':'))


def main():
    status = json.loads((ROOT / 'download-status.json').read_text())
    assert status['complete']
    books = json.loads((ROOT / 'catalog-source.json').read_text())
    out = ROOT / 'hosting'
    out.mkdir(exist_ok=True)
    dbpath = out / 'hadith.sqlite.tmp'
    if dbpath.exists():
        dbpath.unlink()
    db = sqlite3.connect(dbpath)
    db.executescript('''
        CREATE TABLE books (id INTEGER PRIMARY KEY, slug TEXT UNIQUE NOT NULL, data TEXT NOT NULL);
        CREATE TABLE chapters (book_id INTEGER, id INTEGER, data TEXT NOT NULL, PRIMARY KEY(book_id,id));
        CREATE TABLE sections (book_id INTEGER, chapter_id INTEGER, id INTEGER, data TEXT NOT NULL,
                               PRIMARY KEY(book_id,chapter_id,id));
        CREATE TABLE hadiths (book_id INTEGER, id TEXT, chapter_id INTEGER, section_id INTEGER,
                              position INTEGER, data TEXT NOT NULL, PRIMARY KEY(book_id,id));
        CREATE INDEX hadith_chapter ON hadiths(book_id,chapter_id,position);
    ''')
    catalog, count_issues, source_notes = [], [], []
    for book in books:
        folder = ROOT / 'chapters' / book['slug']
        chapters = json.loads((folder / 'index.json').read_text())
        records, chapter_index, section_count = [], [], 0
        for chapter in chapters:
            source = json.loads((folder / f'{chapter["id"]:04d}.json').read_text())
            assert source['count'] == len(source['hadiths'])
            section_map = {s['id']: s for s in source['sections']}
            detail = source['chapter']
            span = re.fullmatch(r'(\d+)\s*-\s*(\d+)', detail['range'])
            if span and int(span[2]) - int(span[1]) + 1 != len(source['hadiths']):
                source_notes.append({'book': book['slug'], 'chapterId': chapter['id'],
                                     'type': 'source_range_is_not_a_contiguous_id_count',
                                     'sourceRange': detail['range'], 'actualCount': len(source['hadiths'])})
            db.execute('INSERT INTO chapters VALUES (?,?,?)', (book['id'], chapter['id'], dump(detail)))
            for section in source['sections']:
                db.execute('INSERT INTO sections VALUES (?,?,?,?)',
                           (book['id'], chapter['id'], section['id'], dump(section)))
            section_count += len(section_map)
            chapter_index.append({**detail, 'count': len(source['hadiths']), 'sectionCount': len(section_map)})
            for h in source['hadiths']:
                records.append({**h, 'languageId': 'bn', 'chapterId': chapter['id'],
                                'section': section_map.get(h['sectionId']),
                                'chapter': {k: detail[k] for k in ('id', 'title', 'contents', 'arabicTitle') if k in detail},
                                'book': {k: book[k] for k in ('id', 'slug', 'title')}})
        for i, h in enumerate(records):
            if h['section'] is None:
                source_notes.append({'book': book['slug'], 'hadithId': h['id'],
                                     'type': 'source_section_is_null'})
            h['siblings'] = {'prev': records[i-1]['id'] if i and records[i-1]['chapterId'] == h['chapterId'] else None,
                             'next': records[i+1]['id'] if i+1 < len(records) and records[i+1]['chapterId'] == h['chapterId'] else None}
            db.execute('INSERT INTO hadiths VALUES (?,?,?,?,?,?)',
                       (book['id'], h['id'], h['chapterId'], h['sectionId'], i, dump(h)))
        if len(records) != book['hadithCount']:
            raise ValueError(f'Incomplete book: {book["slug"]}: {len(records)}/{book["hadithCount"]}')
        parts = []
        for start in range(0, len(records), 250):
            subset = records[start:start+250]
            part = start // 250 + 1
            path = out / 'books' / book['slug'] / f'part-{part:03d}.json'
            write_json(path, {'schemaVersion': 1, 'languageId': 'bn', 'book': book,
                             'part': part, 'count': len(subset), 'hadiths': subset})
            parts.append({'part': part, 'file': str(path.relative_to(out)), 'count': len(subset),
                          'firstId': subset[0]['id'], 'lastId': subset[-1]['id'],
                          'bytes': path.stat().st_size,
                          'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
        entry = {**book, 'downloadedCount': len(records), 'downloadedSectionCount': section_count,
                 'parts': parts, 'chaptersFile': f'books/{book["slug"]}/chapters.json'}
        write_json(out / 'books' / book['slug'] / 'index.json', entry)
        write_json(out / entry['chaptersFile'], chapter_index)
        db.execute('INSERT INTO books VALUES (?,?,?)', (book['id'], book['slug'], dump(entry)))
        catalog.append(entry)
        for field, actual in [('hadithCount', len(records)), ('chapterCount', len(chapters)), ('sectionCount', section_count)]:
            if book[field] != actual:
                count_issues.append({'book': book['slug'], 'field': field, 'advertised': book[field], 'actual': actual})
    assert db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
    db.commit()
    db.close()
    dbpath.replace(out / 'hadith.sqlite')
    manifest = {'schemaVersion': 1, 'source': 'https://ihadis.com/api/v1/trpc', 'languageId': 'bn',
                'snapshotDate': '2026-10-26', 'books': len(books), 'chapters': status['chapters'],
                'hadiths': sum(b['downloadedCount'] for b in catalog),
                'advertisedHadiths': sum(b['hadithCount'] for b in books),
                'parts': sum(len(b['parts']) for b in catalog), 'chunkSize': 250,
                'countDiscrepancies': count_issues,
                'scope': 'All Bengali catalog books, with Arabic text. Digital parts are not printed volumes. Separate wordByWord data is not included.'}
    write_json(out / 'catalog.json', catalog)
    write_json(out / 'manifest.json', manifest)
    write_json(out / 'source-notes.json', source_notes)
    checksums = {str(p.relative_to(out)): hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in sorted(out.rglob('*')) if p.is_file() and p.name != 'checksums.json'}
    write_json(out / 'checksums.json', checksums)
    archive = ROOT.parent / 'ihadis-bn-hosting-2026-10-26.zip'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for p in sorted(out.rglob('*')):
            if p.is_file():
                z.write(p, 'ihadis-bn/' + str(p.relative_to(out)))
        for name in ('README-bn.md', 'serve.py', 'download.py', 'package.py', 'verify.py', 'build_database.py'):
            z.write(ROOT / name, 'ihadis-bn/' + name)
        for name in ('verification.json', 'server-verification.json'):
            if (ROOT / name).exists():
                z.write(ROOT / name, 'ihadis-bn/' + name)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    print(f'Hosting archive: {archive} ({archive.stat().st_size:,} bytes)')


if __name__ == '__main__':
    main()
