# Run, inspect and continue existing work

## Preview

From the project root:

```sh
cd web-views
python3 -m http.server 4180 --bind 127.0.0.1 --directory dist
```

Open `http://127.0.0.1:4180/#surah=1`. Port 4180 avoids the existing original-copy preview on 4173. No npm install/build is needed. `npm start` uses the existing 4173 command if that port is free. `file://` does not support the JSON fetch workflow.

## Data integrity

From `web-views/`:

```sh
python3 scripts/validate.py
python3 scripts/validate.py --release
```

Structural checks should pass. The second command currently exits 2 because full-source acceptance is unmet; do not weaken the gate or label that expected result a successful release.

`python3 scripts/import_source.py` recreates the data from hash-bound sibling candidates. This is a data-writing command; use it when importing source changes, not merely to preview. It does not OCR the missing pages. After a requested accepted data change, refresh the export deliberately and record its hashes; it is not automatically synchronized.

## Browser checks

Scripts use Playwright/Chromium and currently target `http://127.0.0.1:4173`. When checking this handoff copy on 4180, explicitly point the test at the intended server in a temporary test copy; do not accidentally validate the older working copy.

The default view is now ayah-by-ayah. Row-layout scripts must open URLs with `view=rows` (e.g. `#view=rows&surah=1`).

Relevant scripts:

- `check_ayah_view.cjs`: ayah grouping against raw candidates, gaps, partial ayahs, view switch. Honors `BASE`.

- `browser_check.cjs`: UI navigation, local requests, copy, mobile overflow.
- `check_opening.cjs`: four-word font, first-ayah signs and ending reflow.
- `check_symbols.cjs`: mapped source glyphs, unresolved mark and arrow targets.
- `check_verse_numbers.cjs`: all existing numeral strings plus one/two/three-digit fixture.
- `check_alignment.cjs`: scoped baseline correction and stationary upper band.
- `check_first_two_annotations.cjs`: 10 visible signs, consistent color, stationary geometry, and a forced true-collision case.

`check_sukun.cjs` includes a historical before/after snapshot comparison made before later verse-frame and annotation-style changes. It is not a current whole-suite gate. Understand a historical mismatch rather than overwriting evidence or reverting later approved work. Review any test's snapshot assumptions before rerunning it. Tests write evidence; preserve a frozen reviewed report when a new round is needed.

Local runtime paths, if still present:

- Node: `/Users/barik/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node`
- `NODE_PATH`: `/Users/barik/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules`
- Chrome: `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`
- Font tools were installed under `/tmp/quran-web-tools`; that temporary dependency location may disappear. Font rebuild scripts need fontTools and brotli, and the symbol builder also uses Pillow. Running the website needs none of these.

## Typography and source work

Read the relevant source JSON, font metadata and reviewed evidence before changing mappings. The `build_*` scripts reproduce the existing fonts from their recorded source inputs. Fonts/metadata are already included, so routine UI work need not rebuild them.

Keep the body in intact shaping text nodes. U+0652 must remain U+0652; do not replace it with ASCII `^`. Do not globally apply the four-word source font. Do not apply the body-wedge font to the separate basmala. Do not duplicate harakat already embedded in the first-ayah glyphs.

For the first-row recovered pair, actual horizontal ink is measured on an unattached canvas solely for collision geometry. The reader remains selectable HTML text; no canvas is displayed. If fonts/metrics change, retest both the recovered pair and a deliberately forced real overlap.

New source transcription requires page-level evidence, literal text, explicit unresolved fields and independent content/visual verification. Follow the existing fidelity workspace's applicable AGENTS.md when doing that work. Do not claim future conversion is running, complete missing surahs from another edition, or grant exact letter-anchor approval from a word fraction.
