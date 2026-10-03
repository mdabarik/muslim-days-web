# Ayah view — 3 October 2026

Scope: a new default reader view that regroups the existing source segments into one section per `ayah_ref`. The source-row view remains available (`view=rows`). No data, font or annotation geometry changed.

- `browser-check.json`: `scripts/check_ayah_view.cjs` result (base `http://127.0.0.1:4180`). It compares each ayah's words and Bengali text with the raw candidates, checks that all 700 marks appear, that gaps (2:28–30, 2:37–286) and partial ayahs (2:27, 2:31) are flagged, that the three boundary arrows stay on their stop/verse targets, that the ten first-row Fatiha signs stay visible and black, that the view switch keeps the selected ayah, and that nothing overflows at 1360/390/320 px with font sizes 26/34/56.
- Regression: `browser_check`, `check_opening`, `check_symbols`, `check_verse_numbers`, `check_alignment` and `check_first_two_annotations` were run unchanged except for their URL (`view=rows`, port 4180), from a temporary copy so frozen evidence was not overwritten. All passed: 27, 46, 273, 87, 48 and 53 checks.
- Screenshots: `fatiha-ayah4-mobile.png` (ayah spanning two rows), `cross-page-2-26-mobile.png` (ayah spanning PDF pages 5–6), `gap-28-30-mobile.png`.

Known difference: collision withholding depends on line wrapping, so 152 marks are withheld in ayah view and 154 in row view at 1100 px. No mark is moved to make it fit.

This is display mechanics only. It does not verify the source text, glyph shapes or letter anchors.
