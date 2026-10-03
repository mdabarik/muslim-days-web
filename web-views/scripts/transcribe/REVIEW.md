# Second reading of a transcribed page

You check another agent's transcription of one PDF page against the scan, and correct it. Read `SPEC.md` (same folder) for the format, conventions and tools. You did not write this page, so do not trust it. The scan is the only authority.

## Procedure

1. Open `web-views/source/pages/page-NNN.json` and the page `overview`. Confirm the page kind, headers, row count and furniture.
2. For **every row**, make the strip (`strip N Y0 Y1 3`) and compare it with the file, item by item:
   - **Arabic.** Check every word, right to left: the letters, every haraka, shadda, sukun, tanwin, standing alif/kasra, inverted damma, madd and small meem, as printed. Use `crop … 3` on each word whose diacritics are not perfectly clear at strip resolution. Expect several crops per row; this is the core of the job. Check segment splits, stop signs (including stacked pairs) and the rosette numbers.
   - **Marks.** Check that the count and order are right, that each sign is the right character or shape, that each target word is right, and that offsets are roughly right (±0.15 is fine). Missing or extra signs are errors.
   - **Bengali.** Check the text character by character (spelling, vowel signs, punctuation `।`, quotes), the splits at ayah numbers, and the numerals.
3. Fix every error directly in the file. Record each change in the review file. Add an `uncertain` entry to the page file for anything you cannot decide.
4. Run `python3 qtools.py check N` and resolve every ERROR. Re-inspect each `DIFFERENT`.
5. Write `web-views/source/pages/page-NNN.review.json`:

```json
{
  "page": 8,
  "reviewer": "review agent <batch name>",
  "scope": "Second reading of every row (Arabic incl. harakat, marks, Bengali) and the furniture against the 300 dpi scan",
  "verdict": "accept",                     // "accept" if the file now matches the scan apart from listed uncertain items, else "needs_attention"
  "rows_checked": 11,
  "words_checked": 102,
  "marks_checked": 98,
  "changes": [ {"where": "row 2 word 4", "before": "…", "after": "…", "reason": "kasra, not fatha, under ب (crop x1300-1420 y760-900)"} ],
  "remaining_uncertain": ["row 6 word 3: …"],
  "check_output": "<last lines of qtools check>"
}
```

Report briefly: the verdict, the number of changes by type (Arabic letter, haraka, mark, Bengali, structure), and the remaining uncertain items.
