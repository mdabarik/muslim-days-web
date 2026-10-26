"""Export readable structured data from the user-supplied APK, without running it."""
import base64
import hashlib
import json
import sqlite3
import tempfile
import zipfile
from pathlib import Path

APK = Path('/Users/bedata/Downloads/base.apk')
OUT = Path(__file__).parent / 'apk-json-export'
OUT.mkdir(exist_ok=True)


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def sha(data):
    return hashlib.sha256(data).hexdigest()


manifest = {
    'source': str(APK),
    'source_sha256': sha(APK.read_bytes()),
    'scope': 'Readable SQLite tables and JSON assets physically present in the supplied base.apk',
    'contains_complete_hadith_collection': False,
    'contains_online_downloads': False,
    'exports': [],
    'unconverted': [],
}

with zipfile.ZipFile(APK) as apk:
    inventory = []
    for entry in apk.infolist():
        if not entry.filename.startswith('assets/') or entry.is_dir():
            continue
        data = apk.read(entry)
        inventory.append({'path': entry.filename, 'bytes': len(data), 'sha256': sha(data)})
        if entry.filename.endswith('.json'):
            value = json.loads(data)
            relative = Path('assets') / Path(entry.filename).name
            write_json(OUT / relative, value)
            assert json.loads((OUT / relative).read_text()) == value
            manifest['exports'].append({
                'source': entry.filename, 'file': str(relative),
                'kind': 'original_json',
                'top_level_count': len(value) if isinstance(value, (list, dict)) else None,
            })
        elif entry.filename.endswith('.db') and data.startswith(b'SQLite format 3\0'):
            with tempfile.TemporaryDirectory() as temporary:
                db = Path(temporary) / 'source.db'
                db.write_bytes(data)
                con = sqlite3.connect(f'file:{db}?mode=ro', uri=True)
                con.row_factory = sqlite3.Row
                assert con.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
                tables = con.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name").fetchall()
                for table in tables:
                    name = table['name']
                    quoted = '"' + name.replace('"', '""') + '"'
                    rows = [dict(row) for row in con.execute('SELECT * FROM ' + quoted)]
                    for row in rows:
                        for key, value in row.items():
                            if isinstance(value, bytes):
                                row[key] = {'encoding': 'base64', 'data': base64.b64encode(value).decode()}
                    relative = Path(Path(entry.filename).stem) / (name + '.json')
                    write_json(OUT / relative, rows)
                    assert json.loads((OUT / relative).read_text()) == rows
                    manifest['exports'].append({
                        'source': entry.filename, 'table': name, 'file': str(relative),
                        'kind': 'sqlite_table', 'rows': len(rows), 'schema': table['sql'],
                    })
                con.close()
        elif entry.filename.endswith('.ihdb'):
            relative = Path('unconverted') / Path(entry.filename).name
            (OUT / relative).parent.mkdir(exist_ok=True)
            (OUT / relative).write_bytes(data)
            manifest['unconverted'].append({
                'source': entry.filename, 'file': str(relative), 'bytes': len(data),
                'sha256': sha(data), 'status': 'encrypted_not_decoded',
                'reason': 'IHDB encrypted package; decryption key unavailable in supplied base.apk.',
            })

write_json(OUT / 'apk-assets-inventory.json', inventory)
manifest['unavailable_content'] = [
    {'content': 'Full hadith texts and translations', 'status': 'not_exported'},
    {'content': 'Word-by-word hadith dataset', 'status': 'not_exported'},
    {'content': 'Full text of the 25 general books', 'status': 'not_in_catalog_database'},
    {'content': 'Server-only and previously downloaded application data', 'status': 'not_present_in_supplied_apk'},
]
write_json(OUT / 'manifest.json', manifest)
(OUT / 'README-bn.md').write_text('''# APK থেকে JSON রপ্তানি

এটি ব্যবহারকারীর দেওয়া `base.apk`-এর পাঠযোগ্য ডেটার রপ্তানি। অ্যাপের সম্পূর্ণ অনলাইন হাদিস বা বইয়ের সংগ্রহ নয়।

- `general_books/general_books.json`: ২৫টি সাধারণ বইয়ের নাম, লেখক ও অন্যান্য ক্যাটালগ তথ্য। বইয়ের মূল লেখা নেই।
- `prayer_locations/locations.json`: ৬৯,৪৫৬টি লোকেশনের তথ্য।
- `prayer_locations/countries.json`: ২৪৫টি দেশের রেকর্ড।
- `prayer_locations/timezones.json`: ৩৭১টি টাইমজোনের রেকর্ড।
- `assets/`: APK-তে থাকা তিনটি JSON ফাইল, মূল ডেটা অপরিবর্তিত রেখে ফরম্যাট করা।
- `apk-assets-inventory.json`: সব assets ফাইলের পথ, আকার ও SHA-256।
- `manifest.json`: প্রতিটি রপ্তানির উৎস, রেকর্ড সংখ্যা, SQLite schema ও অনুপস্থিত কনটেন্টের তালিকা।
- `unconverted/hadith.ihdb`: APK-তে থাকা এনক্রিপ্টেড মূল ফাইল; এটি JSON নয়, এর ভেতরের রেকর্ড যাচাই করা হয়নি।

দুটি SQLite ডেটাবেসের integrity check পাস করেছে। প্রতিটি রপ্তানি করা JSON পুনরায় পড়ে মূল ডেটার সঙ্গে মিলিয়ে যাচাই করা হয়েছে। কোনো দূরবর্তী হাদিস সংগ্রহকে এই APK-এর ডেটা বলে যুক্ত করা হয়নি।
''', encoding='utf-8')

archive = OUT.parent / 'al-hadith-apk-json-export.zip'
with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as bundle:
    for path in sorted(OUT.rglob('*')):
        if path.is_file():
            bundle.write(path, str(Path(OUT.name) / path.relative_to(OUT)))
with zipfile.ZipFile(archive) as bundle:
    assert bundle.testzip() is None
print(json.dumps({'archive': str(archive), 'archive_bytes': archive.stat().st_size,
                  'exports': manifest['exports'], 'assets_count': len(inventory)}, ensure_ascii=False, indent=2))
