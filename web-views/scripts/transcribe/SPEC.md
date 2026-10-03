# Transcribing one PDF page

You are transcribing pages of a scanned Bengali *Qariana* Quran (Indo-Pak script) into structured JSON for a web reader. The scan is the **only** text source. The result must say exactly what is printed, nothing more.

## Hard rules

1. Write only what you can see in the scan. Never fill text from memory, another edition or the reference skeleton. If you cannot read something, write your best reading **and** add an `uncertain` entry for it. Never silently skip a word or mark.
2. Do not edit files other than your own `source/pages/page-NNN.json`, and do not touch `dist/`, git or other agents' pages.
3. Tools (run from `web-views/scripts/transcribe/`):
   - `python3 qtools.py overview N`: page overview image with y-axis ticks (300 dpi coordinates). Look at it first.
   - `python3 qtools.py strip N Y0 Y1 3`: a horizontal strip at full resolution, cut into 3 overlapping parts (part 1 = right end). Use one strip per printed row, starting a little above the small mark band and ending below the Bengali translation line.
   - `python3 qtools.py crop N X0 Y0 X1 Y1 3`: zoomed detail. **Use it for every word whose harakat you are not certain of, and for every small sign.**
   - `python3 qtools.py ref 2:37-2:44`: the consonant skeleton of a *different* (Madani) printing. Use it only to know which ayahs to expect and to notice a skipped or misread word. **Never copy from it.** Its spelling differs from this book.
   - `python3 qtools.py check N`: validates your file and compares each ayah's consonant skeleton with the reference. `spelling variant only` (an extra/missing ا و ي) is normal for this script. Every `DIFFERENT` must be re-examined in a zoomed crop. Keep the scan's reading if it really is printed that way, and add an `uncertain` note saying so.
   - View images with the Read tool.

## Page layout

A normal page has a header strip (para name box at top left, running title in the centre, para number at top right), about 11 *rows*, and a footer. The footer has the surah name at the left, the folio number in the centre, manzil at the right, and a legend strip. Each row is three lines, top to bottom:

1. **Mark band.** Small Bengali instruction signs over the words of the Arabic line just below them.
2. **Arabic line.** Read right to left.
3. **Bengali translation line.** Read left to right. It contains Bengali ayah numbers (e.g. `৩৭`) where a new ayah's translation begins.

Some pages start a surah: an ornamented title box (Arabic name, Bengali name in a pill, badges `সূরা নং-…`, `মাক্কী/মাদানী সূরা`, `রুকু-…`, `আয়াত-…`), then the basmala and its Bengali line. Late in the book one page can hold several surahs. Pages may also be duplicate scans, appendix or index pages, or blank.

## Output: `web-views/source/pages/page-NNN.json` (NNN = 3-digit PDF page)

```json
{
  "page": 8,
  "kind": "quran",                       // or "duplicate" (+ "duplicate_of": <page>), "non_quran", "blank"
  "printed_page": "৯",                   // folio printed in the footer, Bengali digits, or null
  "surah_headers": [                     // one per surah title box on this page; [] if none
    {"surah": 2, "before_row": 0, "arabic": "سورة البقرة", "bengali": "সূরা বাক্বারহ্",
     "surah_number_bn": "২", "revelation_bn": "মাদানী সূরা", "ruku_bn": "৪০", "ayah_count_bn": "২৮৬",
     "basmala": {"arabic": "بِسْمِ اللّٰهِ الرَّحْمٰنِ الرَّحِيْمِ", "bengali": "পরম করুণাময় ও অসীম দয়ালু আল্লাহর নামে শুরু করছি ।"}}
  ],
  "rows": [ /* printed rows in order, see below */ ],
  "furniture": [
    {"kind": "para_name", "text": "আলিফ লাম মীম"},
    {"kind": "running_title", "text": "ক্বারীয়ানা কুরআনুল কারীম"},
    {"kind": "para_number", "text": "পারা-১"},
    {"kind": "surah_label", "text": "২ সূরা বাক্বারহ্"},
    {"kind": "folio", "text": "৯"},
    {"kind": "manzil", "text": "মানযিল-১"},
    {"kind": "ruku_margin", "text": "রুকু ৪ / ৫ / ৪", "note": "boxed ع with numbers in the left margin beside row 5"},
    {"kind": "legend", "text": "ক ক্বলক্বলাহ; শ শিষ; গ গুন্নাহ; ম মোটা; ৭ ইখফা; ringed wedge আরবী সাকিন"}
  ],
  "uncertain": [ {"where": "row 3 word 5", "question": "kasra or fatha under the second letter? crop is noisy"} ],
  "extracted_by": "transcription agent <your batch name>"
}
```

`before_row` is the index of the first row that comes after that header. A header with `before_row: 0` is at the top of the page.

### A row

Below is a real example: PDF page 7, row 1, as previously transcribed.

```json
{
  "marks": [
    {"printed": "গ", "target": 1, "offset": 0.26},
    {"printed": "১", "target": 1, "offset": 0.69},
    {"printed": "শ", "target": 2, "offset": 0.42},
    {"printed": "৪", "target": 2, "offset": 0.75},
    {"printed": "৭", "target": 4, "offset": 0.78},
    {"shape": "conditional-three-or-one", "target": 6, "offset": 0.65},
    {"shape": "ringed-wedge", "target": 6, "offset": 0.91}
  ],
  "arabic": [
    {"ayah": "2:31", "words": ["اَنْبِئُوْنِيْ", "بِاَسْمَآءِ", "هٰٓؤُلَآءِ", "اِنْ", "كُنْتُمْ", "صٰدِقِيْنَ"], "end_marker": "৩১"},
    {"ayah": "2:32", "words": ["قَالُوْا", "سُبْحٰنَكَ", "لَا", "عِلْمَ"]}
  ],
  "bengali": [
    {"ayah": "2:31", "numeral": "", "text": "‘তোমরা আমাকে এগুলোর নাম জানাও, যদি তোমরা সত্যবাদী হও’ ।"},
    {"ayah": "2:32", "numeral": "৩২", "text": "তারা বলল, ‘আপনি পবিত্র মহান । আপনি"}
  ]
}
```

**Arabic segments.** Split the line into segments. A segment ends at a printed stop sign, at an ayah-end rosette, or at the end of the line. Each segment has:
- `ayah`: `"surah:ayah"`, using this book's own numbering (the number printed in the rosette that ends it).
- `words`: the printed words, right to left, one string per word.
- `stop` (optional): the waqf sign printed at the segment's end, e.g. `لا` `ط` `ج` `ص` `م` `ق` `ز` `ع` `صلى`. Write a stacked pair top to bottom with a newline, e.g. `"لا\nق"`. Write `ع` when the ruku sign is printed above an ayah end.
- `end_marker` (optional): the Bengali numeral inside the ayah-end rosette, e.g. `"৩৭"`.

The words of a row are numbered 1, 2, 3 … right to left **across the whole row**, continuing through all its segments. Marks refer to these numbers.

**Marks.** List every sign in the mark band, right to left. Each sign targets the word it stands over (`target`, a word number), with `offset`: 0.0 = over the word's right edge, 1.0 = over its left edge. Estimate the offset from where the sign's centre falls over that word. Vocabulary:

| looks like | write |
|---|---|
| Bengali ১ ৩ ৪ ম শ গ ক | `"printed": "১"` etc. |
| small hook like the footer legend's ইখফা sign | `"printed": "৭"` |
| ১ or ২ inside a thin circle | `"printed": "১", "enclosure": "circle"` |
| inverted V (∧) inside an oval (আরবী সাকিন) | `"shape": "ringed-wedge"` |
| ৬-like sign with a right lobe (দম ফেলিলে তিন / না ফেলিলে এক) | `"shape": "conditional-three-or-one"` |
| solid downward arrow above a stop sign or rosette | `"shape": "solid-down-arrow", "target": "stop:<segment index>"` or `"marker:<segment index>"` (0-based segment index in this row) |

Anything else: write the closest printed character, and add an `uncertain` entry describing the shape.

**Bengali.** Split the translation line at the printed ayah numbers. Text before the first number continues the previous ayah (`"numeral": ""`, `ayah` = that ayah). Copy spelling and punctuation exactly, including `।`, quotes and spacing. Do not include the leading numeral in `text`.

## Arabic character conventions (match the earlier pages)

| printed | Unicode |
|---|---|
| fatha / kasra / damma | U+064E / U+0650 / U+064F |
| sukun, printed as an open wedge ∧ | U+0652 `ْ` |
| shadda | U+0651 (write it before the vowel: `رَّ` = ر + ّ + َ) |
| tanwin | U+064B ً / U+064D ٍ / U+064C ٌ |
| standing fatha (khara zabar) | U+0670 `ٰ` |
| standing kasra | U+0656 `ٖ` (e.g. `بِهٖ`) |
| inverted damma (ulta pesh) | U+0657 `ٗ` (e.g. `اِنَّهٗ`) |
| madd sign | U+0653 `ٓ` (e.g. `جَآءَ`, `اُولٰٓئِكَ`) |
| small meem (iqlab) | U+06E2 `ۢ` |
| initial hamzated alif | plain alif + vowel: `اَ` `اِ` `اُ` (not أ إ) |
| lone hamza | U+0621 ء; hamza on carriers ئ ؤ as printed |
| final dotless ya | ى U+0649; dotted or medial ya | ي U+064A |
| Allah | `اللّٰهُ` / `لِلّٰهِ` (alif lam lam + shadda + superscript alef + ha) |

Write each printed vowel sign you see, and do not add any that are not printed. In this script a noon or tanwin before an assimilating letter may carry no sukun. Write it that way if the scan shows that. Long vowels are written as printed: `قَالُوْا`, `فِيْهِ`. No tatweel (ـ), no spaces inside a word, and a single space between words.

## Procedure

1. `overview`: decide the kind, and find the header, rows and footer y-ranges. For a duplicate scan, compare with the neighbouring page.
2. `ref` for the expected ayah range: the previous page ended at the ayah given in your batch instructions.
3. For each row: `strip`, then read the mark band, the Arabic and the Bengali. `crop` (zoom 3) any word or sign you are not sure of. **Save the file after every row** so partial work survives.
4. `check`, and fix every ERROR. Look at each `DIFFERENT` again in a zoomed crop.
5. Final self-review: count words and marks per row against the strip images.
6. Report: rows, words, marks, ayah range, your uncertain items, and any check warnings you kept.
