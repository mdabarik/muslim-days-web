# Typography and letter anchoring audit

Date: 2026-10-02. Scope: read-only inspection of existing local source inventories, fonts, builders and review records. No Flutter code or frozen evidence changed. This is an engineering audit, not a new independent transcription or visual acceptance of the PDF.

## Finding

The available data and fonts cannot satisfy the requested 100% whole-Quran text, mark and letter-position fidelity. A working selectable reader can be built, but its current source-derived text must be explicitly labeled **draft**. Whole-word annotation percentages are not verified letter anchors. Prior functional/pilot passes must not be imported as full-source acceptance.

The seven current `full_quran/content/page-NNN/page-NNN.json` files contain 57 rows, 497 Arabic word records and 700 annotation-band glyph records. Page 6 has only three rows. None of these 700 annotation attachments contains a grapheme or letter ID. They use word IDs (or other object targets) plus `offset_in_word`, and describe their relationship as horizontal projection. These counts were recomputed from the files; they are not a completeness census against the source.

## Existing work that works, and its limits

| Artifact | Demonstrated mechanism | Scope limitation |
|---|---|---|
| `runs/fatihah-001/source-font-vowelled-feasibility/FatihahSourcePilot.ttf` and `browser-check.json` | Real Unicode Arabic in SVG text, GSUB substitution into traced whole-word outlines; direct selection retains all reported letters and harakat | Four exact vowelled word contexts only. Unsupported contexts show placeholder boxes. Threshold contours approximate scan ink. No reusable complete Quran font |
| `runs/fatihah-001/round-05/visual-review.json` | Prior reviewer accepted first printed ayah's visual structure at available scan resolution | Explicitly excludes original Bengali typeface, all instruction Unicode identities and whole-Quran approval. Seven outer signs are SVG paths and are not part of text selection |
| `scripts/renderer.js` in source-font mode | Source-positioned word occurrences retain internal letter/mark shape under a common SVG scale | Fixed composition, not a demonstrated general reflow engine. Upper signs are positioned by source boxes and merely carry anchor metadata; an anchor label alone does not bind rendering to a reshaped glyph |
| `scripts/renderer.js` with Amiri | Connected browser-shaped real text; measured whole-word box fitting | Same outer box does not preserve internal letter locations. Existing typography and review evidence documents this failure |
| `full_quran/page-001-native/scripts/native_occurrences.py` | Audited component catalog to a distinct real-Unicode font per occurrence, preventing identical text from selecting the wrong source outline | Tooling only: readiness report says zero page fonts built, zero verified pages; no full-page shaping/selection/reflow/scalability checks. It handles Arabic letter/mark Unicode, not the complete Bengali instruction sign inventory |
| `full_quran/content/check/codex-render-review.json` | Prior Flutter functional layout review | The review explicitly says collision spreading changes annotation centers and exact letter attachment is inferred. Amiri sukun/type proportions differ from the source. Do not port this as an exact renderer |

The source-font build scripts do not recover the publisher's original font. They turn reviewed source contours into native outline font glyphs. That can preserve source-specific geometry while providing visible selectable Unicode text, but only when the text-to-contour mapping itself has independent source evidence. It does not make OCR recognition correct.

`full_quran/annotation-errata-2026-09-26.json` supersedes an earlier sign interpretation: first-ayah a4 is not ordinary Bengali ৩ / unconditional তিন আলিফ. Its Unicode remains unverified. Existing `printed` candidate strings must not automatically become verified copy text.

## Implementable native text contract

The practical source-preserving unit is a complete connected word/cluster with immutable internal geometry. It can reflow as one inline box and scale with font size; it must not reshape into a different font while retaining old offsets. Every external sign is a child of that box with a separate, reviewed reference to its actual source letter or sign target.

For each occurrence store:

- Stable IDs for page, row, word and each source letter/haraka. Preserve original code-point sequence; any canonical normalization must have an explicit offset map so IDs never silently move.
- `textCandidate`, `textVerified` (null until accepted), source bbox/polygon and coordinate frame, exact source hash, and independent review evidence.
- For each grapheme, the source letter identity, code-point interval, source ink region and its physical anchor point inside the source-preserving word. Do not infer a grapheme by dividing word width evenly. Connected ligatures require explicit source subregions.
- For every annotation, separate observed shape, Unicode candidate, verified Unicode, legend text, target type, verified `targetGraphemeId` or explicit stop/marker/span target, source geometry, and uncertainty. Some existing arrows target stop signs; do not force those onto a letter.
- For each shape, its immutable source outline/font binding and hash. All visible required signs must themselves be text glyphs to meet the user's all-text requirement. SVG paths plus hidden copy text would not establish that requirement. Unknown Unicode identities stay unresolved; PUA glyphs would require a documented custom-codepoint contract and cannot be silently presented as recovered Unicode.

An illustrative **schema shape**, not Quran content or an audited anchor:

```json
{
  "wordId": "page-N-row-N-word-N",
  "textCandidate": null,
  "textVerified": null,
  "fontBinding": null,
  "graphemes": [
    {
      "id": "page-N-row-N-word-N-letter-N",
      "codePointRange": null,
      "sourceInkRegion": null,
      "anchorInWord": null,
      "verification": "unresolved"
    }
  ],
  "annotations": [
    {
      "id": "page-N-row-N-sign-N",
      "unicodeCandidate": null,
      "unicodeVerified": null,
      "targetType": "letter",
      "targetGraphemeId": null,
      "sourceOffsetFromAnchor": null,
      "verification": "unresolved"
    }
  ]
}
```

Render the word as real text using its exact source-outline font and render known instruction glyphs as real text using audited custom font glyphs. Use a relative inline-block with a single shared scale for word, anchor points, annotations and reserved annotation headroom. Annotation x/y is the verified letter anchor plus its source offset, scaled identically to the word. Line wrapping moves the entire unit. Do not split Arabic into individually isolated characters, and do not move annotation x positions for collision avoidance. Reserve the necessary space or keep a larger connected unit instead; any collision repair that changes source geometry needs a new review.

Whole-word source fonts preserve a *physical* source letter anchor even though browser caret positions inside ligatures can be ambiguous. Stable grapheme IDs plus source regions establish the target; browser `Range` or SVG character extent rectangles by themselves do not prove exact letter ink. Selection/copy must be tested independently from visual identity.

For a lighter eventual implementation, group occurrence outlines into versioned per-page/per-surah WOFF2 subsets with explicit occurrence substitution selection. A separate font file/family for every word is the currently implemented safe experiment but not a demonstrated fast book-wide strategy. Page/subset font loads, memory reclamation, repeated identical-word variants and mobile browser limits require measurement before selecting the production design. No compactness claim is established yet.

## Acceptance gates before any page is called verified

1. Independently reconcile every source letter, haraka, sign, enclosure, stop, numeral and Bengali string; hash-bind the review to the exact data and font versions.
2. Require reviewed target grapheme IDs and source regions for every letter annotation. Preserve genuinely non-letter targets and unresolved cases explicitly.
3. Check actual font loading and shaping, missing glyphs, complete selection/copy and canonical-equivalent sequences. A DOM text match alone is insufficient if the wrong font outlines render.
4. Independently inspect final ink and annotation positions at desktop/mobile widths and multiple font sizes, including line breaks, complex ligatures, dense bands, stacked signs and internal stop signs.
5. Require zero unresolved in-scope content or geometry findings. Existing `blocking: false` values in older artifacts do not waive the user's current stricter criterion.

The old evidence provides useful mechanics and source candidates, but not these gates for all 760 pages. Only seven page files currently contain structured transcription, one of them partial; the existing local OCR benchmark records persistent Arabic/Bengali errors and missing fine marks. Scaling that OCR over every page would supply draft evidence, not verified text. All remaining transcription, source-letter inventories, annotation glyph mappings and independent page reviews are still required. It would be inaccurate to call a 114-item navigation list, 760 checkpoint records, or a selectable approximate font a completed full-Quran conversion.

## Evidence paths

All paths below are relative to `muslim_days/tool/quran_fidelity/`:

- `AGENTS.md`, `full_quran/AGENTS.md`
- `runs/fatihah-001/typography-plan.md`
- `scripts/renderer.js`, `scripts/build_source_font.py`, `scripts/verify_source_font.cjs`
- `runs/fatihah-001/source-font-vowelled-feasibility/browser-check.json`
- `runs/fatihah-001/round-05/visual-review.json`
- `full_quran/page-001-native/BUILDER-READINESS.md`, `builder-readiness.json`, `scripts/native_occurrences.py`
- `full_quran/content/page-001/page-001.json` through `page-007/page-007.json`
- `full_quran/content/check/codex-render-review.json`
- `full_quran/annotation-errata-2026-09-26.json`
- `full_quran/recheck-2026-09-26/decision.json`, `full_quran/README.md`
