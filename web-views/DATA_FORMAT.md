# JSON contract 2.0.0-draft

UTF-8 JSON; source strings are preserved **without Unicode normalization**. No guessed text or standard-edition replacements. This is a draft evidence contract, not an approved whole-Quran dataset. UI code resides separately in `dist/app.js`, `style.css` and `anchors.js`.

## `dist/data/manifest.json`

- `source`: PDF filename, SHA256, 760 physical pages. The supplied moved PDF matches historical evidence byte-for-byte.
- `releaseReady`: false. Never derive release readiness from directory length, OCR confidence or file count.
- `surahs`: 114 navigation records. `nameBn/nameAr` are existing app directory labels, **not source-transcribed titles**. `pages` and `draftAyahs` come only from candidate `ayah_ref`; a reference can be a fragment, not a complete ayah. `verifiedAyahs` remains empty. `sourcePageMappingComplete` remains false.
- `pages`: all 760 physical pages. `file` exists only when a structured candidate exists. No generated Quran content for absent pages. `fullyVerified` is false, even for a legacy body-only acceptance.
- `summary`: counts of actual records, not a source completeness census.
- `blockingIssues`: declared blockers; per-page source uncertainties remain in each page file.

## `dist/data/pages/NNN.json`

- `source`, `candidateSha256`: source identity and SHA256 of the **original candidate file bytes**, not of a rewritten/minified object. Original files remain in the sibling Flutter repository's tooling directory and are read only.
- `originalCandidate`: complete existing source candidate, retaining rows, Arabic/Bengali segments, source boxes, upper bands, stop signs, verse markers, header/footer data, provenance and historical uncertainty. Observations and interpretations are not collapsed.
- `legacyReview`: available old review retained as evidence only. Its body/partial scope cannot approve this renderer.
- `graphemes`: map keyed by original word ID. Each cluster has a stable page/word/cluster ID, exact `text`, and half-open `startCodepoint/endCodepoint` range in the original word. Combining marks stay with the preceding base. This deterministic text clustering is **not** verified source-letter recognition. `sourceBox:null`, `verified:false` make this explicit.
- `annotations`: one record per original band glyph, in source row order. Stable `id`, original `sourceId`, row, candidate `text` or null, observed `sourceBox`, and `draftWordAttachment` preserved verbatim. `targetGraphemeId:null`, `verified:false` and reasons in `unresolved` prevent a source word fraction being promoted into an exact letter identity.

Coordinates inherit each page's `source.coordinate_system` and are `[x,y,width,height]`, top-left origin. Page scales differ; never compare raw coordinates between pages. Original `offset_in_word` is measured from the **right** of the recorded word box, not from the start of a JavaScript string or from uniform character slots.

Use codepoint ranges in portable data, not UTF-16 indices. JS `Range` needs a conversion; Dart strings also need rune/grapheme-aware handling. The browser mechanism converts to UTF-16 only at measurement time and does not insert isolated letter boxes that would break Arabic shaping.

Unknown `text:null` is not an empty confirmed glyph. Reviewed source-shape mappings now carry `display.symbolId`, `character` (PUA), `fontSha256`, `reviewSha256`, `shapeFamilyConfirmed:true` and `exactOccurrenceOutlineVerified:false`. The original `text:null` remains unchanged: a project PUA mapping does not establish standard Unicode identity. A damaged mark uses `display.status:unresolved_identity` and a visible Bengali editorial status, not a guessed character. Three reviewed arrows now use `displayAttachment` with a source-observed stop/verse marker ID, row and segment index. The legacy attachment remains intact. Do not force boundary signs into a grapheme relationship. Per-page `symbolCatalogue` hashes bind the displayed PUA contract to font bytes; `symbolProgress` and manifest per-surah progress separate symbol repairs from whole-Quran completion.

## Verification and future completion

A full acceptance must independently bind exact candidate data, grapheme source geometry, font assets and web renderer hashes. It must cover every Arabic letter/haraka, Bengali text, band sign/outline/enclosure, stop, numeral, source-relative anchor and page furniture required by scope. Record reviewer scope and unresolved items. Required independent acceptance must not be created by the importer or UI.

The current `fullAcceptance` fields are absent and all releases are blocked. `validate.py` distinguishes structural integrity from release readiness. Before adding approved content, extend and independently review the final source-font/anchor schema and gate; the draft Range mechanism alone cannot establish exact ink fidelity. See typography audit for a source-preserving connected-word font design.

Cross-page fragments, duplicate scans (known PDF384/385 and704/705), mixed appendix page753 and non-ayah pages754–760 must be audited before claiming complete surahs. These are known boundary observations, not a complete continuity proof.

See `SYMBOLS.md` and `dist/data/symbol-catalog.json` for U+E000–U+E003 mappings. Copying PUA text outside this font does not carry visual identity; portable clients must preserve the symbol ID, catalogue and font together.

### First printed Fatiha ayah: source typography

`data/opening-typography.json` separately documents the four exact Arabic word contexts, their source outline font and per-word source geometry. `opening.js` uses it only for PDF page 1, row 0, words `r0w1`–`r0w4`, with the original PDF/candidate hashes and exact Unicode text matched. The raw page JSON is unchanged. The visible body text keeps its Arabic Unicode; 18 Arabic harakat are included in the word outlines, never overlaid a second time. Seven native PUA glyphs preserve the five instructional signs, stop sign and first verse rosette. Preserve this JSON and `fonts/FatihahOpening.woff2` together for future reuse. Browser CSS uses the alias `Fatihah Opening` for the catalogue font.

`sourcePixelsPerEm`, each word's origin/advance/baseline and each glyph's `leftEm`/`topEm` define observed relative positions. The HTML wrapper and all its children scale together. Whole-word ligatures do not establish individual-letter caret geometry, so `letterAnchorVerified` remains false. Scope is only these four occurrences; other identical strings must not automatically use the font. The new browser review is separate from the historical round-05 SVG-text review. See `evidence/fatiha-opening-2026-10-03/`.

### Body sukun typography

The ordinary Arabic body uses a derived outline font for the scanned edition's open wedge form of U+0652. The raw Arabic codepoints remain unchanged. Font shaping, not an overlay or ASCII caret, attaches the sukun to the Arabic letters. The basmala and title retain their separate font, since source samples show a different calligraphic sukun shape. The first four source-outline words retain their existing scoped font. Annotation data, Qarian symbol fonts and their geometry are unaffected. Source and font-diff evidence is in `evidence/sukun-fix-2026-10-03/`. This is a display convention for the available body text, not a new per-occurrence source accuracy approval.

### Decorative verse numbers

`data/verse-frame.json` documents a reusable empty ornament traced from the first Fatiha verse marker. Only the original inner digit contour is removed. `fonts/VerseFrame.woff2` maps the eight preserved ornament contours to U+E200. `verse-markers.js` displays this frame in a separate, accessible-hidden native font span and the unchanged `numeral_bn` in a selectable Bengali text span. One-, two- and three-digit values use smaller digit sizes inside the same frame. The already source-shaped first Fatiha marker is preserved. This reuses the source's ornament as a display style; it does not assert that every source marker has identical geometry. The Arabic words, harakat, instructional annotation fonts and raw source data are unchanged. Flutter can use the same frame font plus native numeral text.
