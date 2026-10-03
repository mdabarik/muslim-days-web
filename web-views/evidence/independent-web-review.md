# Independent web visual and acceptance review

Date: 2026-10-02. Reviewer: separate `visual_review` agent. Scope: local `quran-web` draft; no Flutter changes or publishing reviewed.

**Verdict: user acceptance fails.** The site is a legible, explicitly incomplete draft reader, not a completed conversion of the 114 surahs. No page or letter anchor receives 100% fidelity approval in this report.

## Evidence and method

Read `dist/app.js`, `style.css`, `anchors.js`, `evidence/source-audit.json`, `typography-audit.md`, and `scripts/browser_check.cjs`. Inspected desktop and complex-page mobile screenshots and a fresh 390 × 844 viewport of PDF page 3, rows 3–5. Compared the available source crop `muslim_days/tool/quran_fidelity/full_quran/content/page-003/crops-codex/row0.png`; this is a representative comparison, not a fresh full-page transcription audit. Source hash: `73fab89e61dda144b8c4b2d16239a756564303847917f1f0a69fdd283c3f6640`.

Fresh browser checks loaded PDF pages 1, 3, and 6 at 390 px width and Arabic font sizes 26, 34, 56. Each reported document scroll width 390 px. Bounding-box intersections were measured for rendered annotation spans, then a real viewport was inspected to distinguish layout from full-page screenshot scaling artifacts.

Reviewed implementation hashes:

- app.js: `c3238b109696d8af84b7fd97628ee3cb0a97dc38e8b25d5fbbcd5b743a2b7faf`
- style.css: `8de15e23f090b6472e45d92afd8c11e65e505ba26bc74f0c74d1bdba4f740e78`
- anchors.js: `a5430048bc6ade21d9f2e600e2e6a629f7980513f2f9f838d08321b7d19b564e`
- manifest.json: `9dcd3619388ae11634b4879dd03c5352c94508c44c38f81ee744d1051b60c095`

## Positive observations within draft scope

The restrained green, cream and gold layout is readable on desktop and mobile. Arabic and Bengali body content are actual text. Mobile wraps words without horizontal page overflow at the tested settings. The notice, per-row evidence disclosure, page issues, empty-surah states and progress dialog repeatedly disclose incomplete transcription, unverified shape and unverified letter attachment. The application does not claim that the list of 114 surahs represents 114 converted surahs. The site retains local source-derived candidates instead of substituting another Quran edition.

The existing browser report is appropriately limited to UI mechanics; text equality, selectable DOM content and no-overflow checks do not constitute source fidelity approval. The synthetic Range fixture is clearly marked synthetic and must remain excluded from source verification counts.

## Actionable findings

1. **Blocking — whole-source completion and exact anchors are absent.** Seven page files (one partial) cover 57 rows; 753 source pages have no transcription. Zero of 700 annotation objects has a verified letter anchor. Amiri is visibly different from the printed source. Word-relative percentages cannot retain source-letter positions after replacing the source glyph geometry. Keep release blocked and completion counts zero until independent source, font and anchor evidence exists.

2. **High — annotation boxes collide.** At mobile width 390 and default size 34, page 1 has a collision between `r2-a9` and `r2-a10`; page 3 has eight colliding pairs, including `r2-a5/r2-a6`, `r3-a2/r3-a3`, `r3-a3/r3-a4`, `r3-a11/r3-a12`, `r4-a4/r4-a5`, `r4-a12/r4-a13`, `r6-a8/r6-a9`, and `r6-a14/r6-a15`. Page 6 has four pairs (`r1-a6/r1-a7`, `r1-a8/r1-a9`, `r1-a15/r1-a14`, `r2-a4/r2-a5`). Counts at sizes 26/34/56 are page 1: 2/1/1, page 3: 10/8/9, page 6: 5/4/4. The fresh viewport shows contiguous crowded sign badges over page 3 row 4. Do not repair by horizontally shifting signs and treating the result as exact. A provisional draft may reserve additional annotation lanes while explicitly disclosing their changed vertical geometry; exact mode needs source-compatible geometry and reviewed letter targets.

3. **High — already-transcribed source furniture is not visible.** `render()` ignores `surah_header` and `page_furniture`. This omits source title information, para and manzil labels, and useful instructional text. Examples include page 3 `mandatory_stop_note` (মীম ওয়াক্ফি লাজীম...), page 4 `footer_legend`, and page 5 duration legends. These are retained in JSON but unavailable to ordinary readers. Render a separately labeled source-details section, keep uncertainty status, and distinguish source labels from navigation metadata. Do not silently promote provisional readings.

4. **High — non-word annotation targets are excluded from the Arabic line.** Filtering only `attachment.target === word.id` leaves page 3 `r4-a15` (marker target `r4-marker8`) and page 6 `r1-a16` (unknown target) in evidence details only. Explicitly state that these signs have no rendered source position, or support the reviewed non-word target. Unknown targets must stay unplaced rather than being assigned to a convenient nearby word.

5. **Medium — body word checks miss required content classes.** Current mechanical preservation assertions cover page 1 `.word` text. They cannot detect omitted furniture, omitted non-word marks, distorted enclosures, wrong annotation Unicode or lost stops. Add explicit counts/disclosures for these source object classes and meaningful collision checks. Keep any future expanded check report scoped to what it actually proves.

6. **Open typography limitation — Range center is not source anchor geometry.** `placeVerifiedAnchor` uses the center of a browser selection rectangle and does not apply a source offset from a particular source-letter point. A ligature or combining-mark selection rectangle may not describe the source glyph ink. Marking JSON `verified: true` would not itself establish correct placement; exact support requires the source geometry and font evidence described in `typography-audit.md`.

## Acceptance boundary

Useful as an incomplete local development/review artifact. Not accepted as the requested full Quran website, publication-ready source edition, or exact letter-anchored renderer. The above findings were sent to the coordinator before final reporting; subsequent changes require a new hash-bound recheck. No content or implementation files were edited by this reviewer.


## Recheck after draft UI repairs — 2026-10-03

The coordinator requested a recheck of collision withholding, source-furniture rendering and WOFF2 loading. This section supersedes initial findings 2–4 only to the limited extent stated below. **The complete-source and exact-letter acceptance verdict remains fail.**

Fresh browser checks exercised 30 combinations: desktop width 1360 and mobile width 390; PDF pages 1, 3, 4, 5 and 6; Arabic sizes 26, 34 and 56. All 30 had zero intersections between *visible* annotation badge rectangles, zero horizontal document overflow and no rows with withheld badges hidden behind a closed disclosure. No page runtime errors were observed. Real viewport screenshots were inspected for page 3 mobile body/disclosure/furniture and page 4 desktop furniture. The mobile reading line is clearer than in the initial build. Known source title fields, the mandatory-stop Bengali note and footer legend entries are now visibly selectable text.

At default size 34 the numbers of collision-withheld badges were desktop pages 1/3/4/5/6: 4/17/42/45/9, and mobile: 4/21/48/49/9. This is a transparent incomplete-placement fallback, **not a fidelity fix**. Their textual records remain in automatically opened lists with a prominent placement explanation. The original per-word percentages are not shifted to create a misleading appearance of accurate attachment. Non-word targets also produce a visible unresolved-placement note and opened evidence details. The two non-word annotations remain unplaced, as their evidence requires.

Source furniture now visibly discloses unresolved text rather than promoting `provisional_text`. Page 6 correctly has no furniture block because its partial candidate has no furniture entries. Page 1 metadata and page 4/5 legend readings are present. Original source geometry, full title mark fidelity and all annotation targets remain unverified.

Residual limitations in this revision:

- `renderFurniture` emits known `text` and legend `entries`, but not separate `symbol` fields: page 3 mandatory-stop Arabic `م` is still absent from that source-furniture block. Its observed component arrays are likewise not shown. Thus “all source furniture reproduced” would still be false.
- Withheld annotation lists preserve candidate text and meanings, but do not reproduce their enclosure geometry or source position. Null printed values remain explicitly unresolved. This is acceptable disclosure for a review artifact only.
- Source uncertainty messages include raw English diagnostic text and internal word IDs. These are readable review aids, but the page remains a development/review interface rather than a finished general reading edition.
- The original blocking coverage/anchor deficits and browser Range source-geometry limitations are unchanged. Neither WOFF2 conversion nor this UI recheck verifies the original font shapes, Unicode identities, all harakat or any letter-level anchor.

Rechecked artifact hashes:

- dist/app.js: `7efe119cd14a57ddc804cd731066580630230937f22c9ab0ffcb9a1a66223756`
- dist/style.css: `3f562f7de13c4d90c00abc26fce4629e2858ed916cf4743939fcf1ce4e74b7e8`
- dist/anchors.js: `a5430048bc6ade21d9f2e600e2e6a629f7980513f2f9f838d08321b7d19b564e`
- dist/data/manifest.json: `9dcd3619388ae11634b4879dd03c5352c94508c44c38f81ee744d1051b60c095`
- dist/fonts/Amiri-Regular.woff2: `083b22369749e48712b4d6da6c4a13279d62efd17cba60a9fae9f9ecec82c29f`
- dist/fonts/NotoSansBengali-VF.woff2: `350c086f3e760a0ca48906534307b097d81ca510b0a892d3c5d17593e6e76ab3`

Draft UI findings: mitigated as described. Full user acceptance: **not met**. No code or source-data edits were made by this reviewer.


## Final narrow recheck — 2026-10-03

The source-furniture symbol/component omission recorded in the preceding recheck is now resolved for the implemented data fields. A fresh 390 px browser visit to PDF page 3 confirmed Arabic `م` in `.furniture-symbol`, the observed `ع` and Bengali numerals/ruku text, and explicitly bracketed Bengali descriptions for uncertain vertical/horizontal strokes. These editorial shape descriptions are distinguished from source text; this does not establish their original Unicode identity or geometry.

The ayah selector now includes all available candidate references for the selected surah. Selecting `2:1` from PDF page 3 navigated to PDF page 2 and highlighted its `2:1` row. The selector appropriately skips untranscribed references rather than manufacturing their text. This was an additive narrow regression check; the preceding full matrix was not repeated.

Latest hashes:

- app.js: `31246bfa25adfc9db4c72c06ed37e58dbd0c1267148223e09d5af97482c39488`
- style.css: `336071c690604653e019abde5edf209e65b699de4ad5548288d30d77d458bf67`

The complete-source/100%-fidelity acceptance verdict remains **fail**; these repairs improve the disclosed local draft only. No implementation changes were made by this reviewer.
