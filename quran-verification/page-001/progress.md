# Page 001 extraction/correction progress

- Scope: physical PDF page 1, Surah Al-Fatiha only.
- Source: `source-pdf/Quran - Qariyana Quranul Karim.pdf`.
- Candidate: `muslim_days/assets/quran/printed/page-001.json`.
- Status: extraction/correction pass complete; ready for independent review.
- 600 dpi source render completed (4959 × 7017 px).
- Existing JSON loaded and checked against the scan item by item.
- Checked 5 Quranic-body rows, 9 Arabic segments, 9 Bengali segments, 7 printed ayah markers, and 36 tajweed instruction signs.
- Corrected the Surah 1 basmala/API offset: the unnumbered basmala is API 1:1, while printed ayahs ১–৭ map to API 1:2–1:7.
- Corrected the stored source PDF SHA-256 to match the specified PDF.
- No definite Arabic-letter/haraka, Bengali-text, printed-marker, tajweed-sign identity, target, or offset defect was found in this pass after the reference correction.
- Decorated Arabic title harakat remain unresolved as page furniture; this does not block Quranic-body review.
- Candidate verdict: READY_FOR_INDEPENDENT_REVIEW.
- Independent verification is outside this agent's scope.

## Agent 2 independent verification

- Started independent verification of physical PDF page 1.
- Initial verifier record saved to `agent-2-verify.json` before row review.
- Prior-agent conclusions are excluded from evidentiary reasoning; the source raster is the authority.
- Row 0 saved: PASS. Verified both Arabic segments and harakat, Bengali segments, printed markers ১–২, both `لا` signs, and all 10 instruction signs including the two oval Arabic-sakin enclosures and two conditional `৬` signs.
- Row 1 saved: PASS. Verified Arabic and Bengali continuation structure, marker ৩ and `ط`, and all 5 instruction signs including conditional/enclosed identities.
- Row 2 saved: PASS. Verified Arabic/harakat, Bengali continuation, markers ৪–৫ with `ط`/`لا`, and all 10 signs including three `শ`, two conditional `৬`, and two oval Arabic-sakin enclosures.
- Row 3 saved: PASS. Verified Arabic/harakat, Bengali text, stacked marker ৬ and `لا`, and all 7 signs with exact word targets.
- Row 4 saved: PASS. Verified final Arabic/Bengali continuation, marker ৭ and ruku `ع`, and all 4 signs including `৪`, conditional `৬`, and the oval enclosure.
- Basmala/global checks saved: PASS. Confirmed the unnumbered printed basmala, API 1:1 / printed-body ১–৭ offset to API 1:2–1:7, and `اللّٰهِ` with U+0651 shadda plus U+0670 dagger alif.
- Recomputed totals: 5 rows, 9 Arabic segments, 9 Bengali segments, 7 printed ayah markers, and exactly 36 instruction signs.
- Page furniture: non-blocking uncertainty remains in decorated Arabic title marks and normalized Bengali header spelling (`মাক্কী সূরা` versus visibly printed `মক্কী সুরা`-style furniture).
- Agent 2 final status: complete.
- Agent 2 verdict: **ACCEPT**. No Quranic-body defects found.

