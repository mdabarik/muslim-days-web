# Source-derived Qarian glyph templates

`QarianSymbols.woff2` is a 960-byte TrueType-outline WOFF2 font. It contains selectable private-use characters, not embedded scans, SVG, raster glyphs or canvas drawing. The reader must keep the symbol ID/catalogue with PUA text: these characters have no portable Unicode identity.

| ID | Codepoint | Source template |
| --- | --- | --- |
| ringed-wedge | U+E000 | PDF1 first printed ayah, `round-05/mark-vectors.json` trace `a5`; oval is intrinsic |
| bare-wedge | U+E001 | Same source, trace `w1-m2` |
| solid-down-arrow | U+E002 | Fresh PDF3 300dpi crop, native 190×250; largest dark component inside inspected arrow box |
| conditional-three-or-one | U+E003 | PDF1 first printed ayah, trace `a4`; compound bowl/stem/lobe preserved |

The source reader independently confirms PDF5's conditional-mark legend says “দম ফেলিলে তিন; না ফেলিলে এক”. This does not make the graphic Unicode Bengali digit 6. The rule and glyph encoding are separately documented in the catalogue. `intrinsicRing` refers to a distinct external enclosing oval; the conditional glyph's bowl is its own skeleton, not an extra ring.

## Reproduce

From repository root:

```sh
PYTHONPATH=/tmp/quran-web-tools python3 quran-web/scripts/build_symbol_font.py
```

Requires Pillow, fonttools and brotli. The script pins the source-vector, source-image and native-arrow crop hashes; it fails if a source input changes. It generates `dist/fonts/QarianSymbols.woff2`, `dist/data/symbol-catalog.json`, `glyph-outlines.json`, and `font-build-report.json`. Two successive builds produced the identical font SHA-256 `b143435ef0a9e71c4a9e002b7404bc73a7a9dcd642d48cb9e4803e71204a7473`.

Native arrow provenance: original PDF SHA-256 `73fab89e61dda144b8c4b2d16239a756564303847917f1f0a69fdd283c3f6640`, physical page 3, pypdfium2 render at 300dpi (2480×3509), crop XYXY `(430,1160,620,1410)`, no resizing. Trace threshold is grayscale <128. Selection box inside crop `(55,68,95,118)` contains the arrow away from its boundaries; smaller disconnected noise is excluded. No ideal geometric arrow or generic Unicode arrow was substituted.

## Verification and limits

- TrueType cmap resolves all four PUA entries. Font tables contain no SVG or bitmap data.
- `glyph-comparison.png` is an evidence-only comparison viewed by the builder: original crop above, actual FreeType rendering below. It is not shipped in the reader. `QarianSymbols-proof.ttf` is an evidence-only decompression for that rendering.
- Oval, asymmetric wedge, solid arrow silhouette and conditional bowl/stem/lobe remain visible. Contours are intentionally unsmoothed; scan resolution and threshold are material limits.
- Normalizing template ink height to 780/1000 em preserves each template's aspect ratio, but does not establish original relative sizes, word positions or letter anchors.
- These are family templates from specific source occurrences. Reusing them on 52 wedge occurrences, three arrows or 42 conditional marks does not certify that each scan has identical geometry. No full-page or Quran-wide accuracy claim follows from this font.
- Damaged PDF3 row0-a8 is omitted. The available crop does not support confident character recovery or clean separation of the intended mark from scan damage.
