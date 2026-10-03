# Existing state — 3 October 2026

## Locations

- Handoff project root on this Mac: `/Users/barik/Desktop/muslims-days`.
- Original source workspace: `/Users/barik/Desktop/Life & Love/PlayStore/Muslim Days`.
- Old `/Users/barik/Desktop/PlayStore/Muslim Days` no longer exists. Set the real working directory explicitly.
- Handoff website: `web-views/`, with `dist/` as the server document root.
- Original working copy: `quran-web/`. The existing port 4173 preview may still serve this original copy.
- Export: `output-json/data/`, `output-json/fonts/`, schema and format documentation. Runtime uses `web-views/dist/data/`; the export is a snapshot, not a second live source.
- Original PDF: `/Users/barik/Downloads/oct 1 bin/CamScanner 09-20-2026 01.00.pdf`.
- PDF SHA256: `73fab89e61dda144b8c4b2d16239a756564303847917f1f0a69fdd283c3f6640`.
- Source tooling and original candidate JSON: `muslim_days/tool/quran_fidelity/`; these existing files remain in place.

The 1.19 GB PDF is not duplicated. The served `dist/` is independently runnable with a static HTTP server. Source imports/font rebuilds additionally need the existing sibling source-tooling tree; importing also reads `muslim_days/lib/data/surah_data.dart` for directory metadata only. If moving to another machine, retain those dependencies and the original PDF before attempting source work.

## Honest coverage

760 physical PDF pages; scanned image content with no usable Arabic/Bengali text layer. Only seven candidate pages are integrated: 57 rows, 497 word records, 700 annotation records. Page 6 has only three rows. Another 753 physical pages have no transcription. Physical pages include repeated scans and appendices; do not infer a verse map from page count.

114 navigation entries do not mean 114 transcribed surahs. Entirely verified surahs/pages: zero. Verified individual-letter annotation anchors: zero. Existing word-relative coordinates and historical body reviews do not approve the whole web rendering. One damaged PDF3 annotation, r0-a8, remains explicitly unresolved. `releaseReady` is false and the release check is intentionally blocked.

## Implemented rendering

- Lazy page JSON loading, mobile directory/search, page/ayah navigation, font sizes 26–56, local font assets.
- Qarian Symbols font: 52 enclosed wedges, 3 arrows and 42 conditional signs displayed through source-backed bindings; a damaged sign stays labelled unclear. The original candidate remains intact.
- First printed Fatiha ayah: four exact Unicode word contexts, 18 embedded harakat, five native upper signs and native stop/verse ending. This font cannot shape arbitrary Quran words.
- Ordinary verse sukun: QuranWedgeArabic changes only two glyph outlines, keeping text and shaping/positioning metrics. Do not apply it to basmala/header calligraphy.
- Verse numbering: 38 reusable ornament frames with real Bengali numeral text; original first-ayah marker preserved, 39 existing markers total. Three-digit support was tested with a fixture, not invented source content.
- First Fatiha row: ordinary body words and their ending raised by .35em to align the visible writing line with the scoped source font. Upper marks and the four source words keep their geometry.
- First two Fatiha ayahs: all 10 upper signs visible and uniformly black/transparent. Two were previously falsely hidden because advance boxes included blank font side bearings. Their actual ink does not overlap; sizes and x positions remain unchanged. Genuine collisions are still withheld.

## Main files

- `web-views/dist/app.js`: rendering, navigation, collision handling.
- `style.css`: mobile layout and scoped baseline/color rules.
- `opening.js` + `data/opening-typography.json`: four-context first-ayah font/layout.
- `symbols.js` + `data/symbol-catalog.json`: source-shape symbols and bindings.
- `verse-markers.js` + `data/verse-frame.json`: ornament plus native numerals.
- `anchors.js`: experimental verified-grapheme infrastructure; current data does not have approved letter targets.
- `data/sukun-font.json`: derivative-font provenance and scope.
- `DATA_FORMAT.md`, `SYMBOLS.md`, `data.schema.json`: reusable data contracts.

## Evidence routing

Read the report appropriate to the change, not every screenshot:

- `evidence/symbol-fix-2026-10-03/`: legend analysis, known symbol recovery and damaged-sign uncertainty.
- `evidence/fatiha-opening-2026-10-03/`: source-shaped first ayah and nonbreaking ending.
- `evidence/sukun-fix-2026-10-03/`: body sukun vs basmala, unchanged annotation/font evidence.
- `evidence/verse-numbering-2026-10-03/`: true numeral preservation and ornament tests.
- `evidence/alignment-2026-10-03/`: first-row baseline correction.
- `evidence/first-two-annotations-2026-10-03/`: latest first-row color/visibility review.

Each pass has a limited scope. Earlier reports identify the hashes they reviewed and are historical, not blanket approval of every later edit. The original README contains earlier-state descriptions as well as later additions; use these current-state notes and the latest relevant report to disambiguate.

## Desktop relocation

The handoff is now directly on Desktop. Original transcription/rebuild inputs remain in the original source workspace above. The website itself runs independently from `web-views/dist`. Existing import/font-build scripts expect those source dependencies beside their project; run rebuilds in the original source workspace and copy reviewed outputs, or explicitly configure dependencies before rebuilding here. Do not interpret missing local source inputs as permission to reconstruct or guess content.
