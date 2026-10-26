#!/usr/bin/env python3
"""Verify JSON/SQLite agreement, completeness, checksums and optional upstream samples."""
import argparse
import hashlib
import json
from pathlib import Path
import sqlite3


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-samples', action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    out = root if (root / 'catalog.json').exists() else root / 'hosting'
    load = lambda p: json.loads(p.read_text())
    catalog = load(out / 'catalog.json')
    manifest = load(out / 'manifest.json')
    db = sqlite3.connect(f'file:{out / "hadith.sqlite"}?mode=ro', uri=True)
    assert db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
    files_checked = 0
    for name, expected in load(out / 'checksums.json').items():
        assert hashlib.sha256((out / name).read_bytes()).hexdigest() == expected, name
        files_checked += 1
    total, parts_count, samples, comparisons = 0, 0, [], []
    for book in catalog:
        records = []
        for part in book['parts']:
            data = load(out / part['file'])
            assert data['count'] == part['count'] == len(data['hadiths']) <= 250
            assert data['book']['id'] == book['id']
            records.extend(data['hadiths'])
            parts_count += 1
        ids = [h['id'] for h in records]
        assert len(ids) == len(set(ids)) == book['hadithCount'] == book['downloadedCount']
        assert records == [json.loads(r[0]) for r in db.execute(
            'SELECT data FROM hadiths WHERE book_id=? ORDER BY position', (book['id'],))]
        chapters = load(out / book['chaptersFile'])
        assert len(chapters) == book['chapterCount']
        for chapter in chapters:
            assert sum(h['chapterId'] == chapter['id'] for h in records) == chapter['count']
        for i, h in enumerate(records):
            assert h['bookId'] == book['id'] and h['book']['id'] == book['id']
            assert h['chapterId'] == h['chapter']['id']
            assert h['sectionId'] == (h['section']['id'] if h['section'] else -1)
            assert h['siblings'] == {'prev': records[i-1]['id'] if i and records[i-1]['chapterId'] == h['chapterId'] else None,
                                     'next': records[i+1]['id'] if i+1 < len(records) and records[i+1]['chapterId'] == h['chapterId'] else None}
        total += len(records)
        selection = [records[0], records[len(records)//2], records[-1]]
        alias = next((h for h in records if h.get('canonical')), None)
        if alias:
            selection.append(alias)
        missing_section = next((h for h in records if h['section'] is None), None)
        if missing_section:
            selection.append(missing_section)
        samples.extend(selection)
    assert total == manifest['hadiths'] == manifest['advertisedHadiths']
    assert parts_count == manifest['parts']
    assert total == db.execute('SELECT count(*) FROM hadiths').fetchone()[0]
    if args.source_samples:
        from download import fetch
        for sample in samples:
            original = fetch('hadith.byId', {'bookId': sample['bookId'], 'hadithId': sample['id'], 'languageId': 'bn'})
            # Check every upstream field, including section, chapter, content and siblings.
            for field, value in original.items():
                assert sample.get(field) == value, (sample['bookId'], sample['id'], field)
            comparisons.append({'bookId': sample['bookId'], 'id': sample['id'], 'match': True})
    report = {'passed': True, 'books': len(catalog), 'hadiths': total, 'parts': parts_count,
              'checksummedFiles': files_checked, 'sourceSamples': comparisons,
              'checks': ['all advertised book/chapter counts', 'no duplicate book+id keys',
                         'section/chapter references', 'JSON and SQLite record equality',
                         'previous/next IDs', 'all SHA-256 checksums', 'SQLite integrity']}
    (root / 'verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({**report, 'sourceSamples': len(comparisons)}, indent=2))


if __name__ == '__main__':
    main()
