# Existing Quran data export

This is a byte-identical snapshot of the website's existing JSON and fonts, not a new transcription. `data/manifest.json` is the entry point; resolve its `data/pages/...` paths against this folder. Keep `fonts/` with the metadata because private-use shapes require their matching font. Read `DATA_FORMAT.md`, `SYMBOLS.md` and `data.schema.json`.

Seven draft pages, 57 rows, 497 words and 700 annotations are present. Page 6 is partial. The 114-surah directory does not imply complete text. All full-release and letter-anchor verification limitations remain in force.

The live website reads `web-views/dist/data/`, not this export. Refresh this export deliberately after future reviewed changes. No Flutter implementation is included or changed.
