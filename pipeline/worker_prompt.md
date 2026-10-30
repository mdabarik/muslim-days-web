# Transcribe physical page {PAGE} of the scanned Bengali Qariyana Quran

You are one worker in a page-by-page pipeline. Your job: read page {PAGE} of the scan and write
`transcripts/{PAGE3}.json`. The scan is the only source of truth. The old data for this page
(`data/pages/{PAGE3}.json`) is broken OCR. Do not read it or copy from it.

## Tools (run from the repository root)

- `.venv/bin/python pipeline/prepare.py {PAGE}` extracts the page (2480x3509 px) and writes an
  820 px overview with red ticks every 100 source px down both sides (labels = source y).
  Read the overview once to find every line's y range.
- `.venv/bin/python pipeline/crop.py {PAGE} X Y W H NAME [--zoom Z] [--ruler]` crops
  full-resolution pixels to `work/crops/{PAGE3}/NAME.png`. Then Read that file. Output is capped at
  1500 px wide. `--ruler` adds a strip of source x coordinates on top. Use it to line a band
  sign up with the letter under it.
- `.venv/bin/python pipeline/check.py {PAGE}` validates the transcript and prints every word
  split into numbered letter clusters, with the annotations attached to each. It must print `OK`
  before you finish.

Use only these commands. Don't edit any other file.

## Page layout

Each Quran line on the page has three parts, top to bottom:
1. **Annotation band**: a thin strip (about 40 px) of small Bengali signs just above the Arabic line.
2. **Arabic line** (about 120–160 px tall): the Quran text, with harakat and small signs printed on it.
3. **Bengali translation line** under it.

A page can also have surah header boxes (সূরা-N, রুকু, আয়াত-N, মাক্কী/মাদানী, the surah's
Bengali name and the basmala), a page number, a para name, QR codes beside the first line of a
surah (ignore them), and a legend strip at the bottom. Some pages have non-Quran content (du'a,
index, publisher pages). Put a one-line note about it in `non_quran`, and only transcribe the
Quran lines into `rows`.

## What to write

Follow the format in the docstring of `pipeline/transcript.py`. Set a header's `arabic` to null
if the box prints no Arabic name. For each Quran line, add one entry in `rows`:

- `segments`: split the line by ayah. Each segment has:
  - `ayah_ref`: "surah:ayah", in this edition's numbering.
  - `words`: in reading order.
  - `verse_number_bn`: the Bengali number in the ayah-end circle (such as "৫") when the ayah ends
    on this line, otherwise `null`.

  Use the header, the verse numbers and your knowledge of the Quran to fix the refs. An ayah that
  continues from the previous page starts the first row.
- `words`: copy each Arabic word exactly as printed, in Unicode, with every haraka on the scan.
  - Write fatha, kasra, damma, sukun, shadda, tanween, superscript alif U+0670 and maddah U+0653
    as they are printed.
  - This edition uses Indo-Pak style spelling (for example `اَعُوْذُ`, `اللّٰهِ`, `يٰۤاَيُّهَا`). Your memory of the
    Quran helps you read the words, but the printed spelling and vowels win.
  - **This edition prints sukun as a small ∧.** Write it as the normal sukun U+0652 in the word. Do
    not add it as an annotation. The web font draws U+0652 as the ∧.
  - A small waqf sign printed over the end of a word or over the ayah circle goes at the end of
    the ayah's last word, as Unicode: ۙ (small لا), ۚ (ج), ۗ (قلے), ۖ (صلے), ۛ (three dots),
    ۘ (small meem), ۜ (small seen), ؕ (small ط). For any other sign, use the closest one and
    note it in `unresolved`.
  - Skip the ruku sign ع beside verse circles. Never put the ayah circle itself in the words.
- `annotations`: **every** sign in the annotation band. For each one:
  - `glyph`: the Bengali character as printed: `১`, `২`, `৩`, `৪`, `৬`, `শ`, `ম`, `গ`, `ক` ...
    Two characters printed together, such as `শ১`, are two annotations.
  - `enclosure`: `"circle"` only if the band digit itself is printed inside a circle, else `"none"`.
    Band digits are usually printed without one, even though the legend circles them.
  - `label_bn`: its meaning, from the legend strip at the bottom of the page:
    - ১ এক আলিফ
    - ১ with a double ring: দম ফেলিলে এক আলিফ
    - ২ দম ফেলিলে দুই আলিফ
    - ৩ তিন আলিফ
    - ৪ চার আলিফ
    - ৬ দম ফেলিলে তিন / না ফেলিলে এক

    Letters: শ = শীষ, ম = মোটা (পুর), গ = গুন্নাহ, ক = কলকলাহ. If the page's legend differs, use the legend.
  - The band also has an oval with a ∧ inside, usually beside ক or শ over the last letter of an
    ayah. It is **not** a circled ৪. Record it with `"symbol": "ringed-wedge"`, no `glyph`,
    `"enclosure": "none"`, `"label_bn": "আরবী সাকিন (থামলে সাকিন পড়ুন)"`.
  - `layer`: always `"band"`. Use `"arabic"` only for a solid down arrow printed on the Arabic
    line (`"symbol": "solid-down-arrow"`).
  - `word` and `letter`: the letter the sign stands over. Take the sign's x from a `--ruler` crop of
    the band, then find which word and which letter cluster sit at that x in the Arabic line
    below. `word` counts across the whole row (1 = rightmost word). `letter` is the cluster number
    `check.py` prints.
- `bengali`: the translation line, split at the verse numbers. Each part has `ayah_ref`,
  `numeral_bn` (the number printed before that ayah's translation, or "" for a continuation) and `text`.
- `surah_headers`: one entry per header box on the page. `before_row` is the index of the first
  row of that surah on this page.
- `unresolved`: list anything you could not read with confidence. Never guess silently.

## How to work (keep it efficient: about 4 crops per line is enough)

1. Run prepare and read the overview. Write down each line's band y, Arabic y and Bengali y.
2. For each line, make two crops (right half x 1240–2400, left half x 80–1300) covering band, Arabic
   and Bengali, with `--ruler` (about y_band-10 to y_bengali+50). Read the words and the Bengali.
   Zoom (`--zoom 2`, about 600 px wide) only where a sign or haraka is unclear. Count the band signs
   and count them again. A band often has 10–20 signs, and missing signs was the main failure of the
   old data.
3. Write the transcript, run `check.py`, and compare its table with your crops: each sign must sit
   over the right letter. Fix and rerun until it prints `OK`.
4. Finish with one line: `PAGE {PAGE} DONE rows=N annotations=M`. If the page has no Quran lines,
   finish with `PAGE {PAGE} DONE non-quran`.
