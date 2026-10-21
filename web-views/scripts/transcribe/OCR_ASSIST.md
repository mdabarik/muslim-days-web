# OCR assistance for the scanned source

`ocr_assist.py` and `batch_ocr.py` record **unreviewed suggestions only**. They never write `source/pages/` or `dist/data/`. Arabic harakat, Bengali spelling, Qarian signs, verse boundaries and letter anchors must still be read from the original PDF and reviewed separately. A word from another Quran edition must never replace an unclear source word.

The source is `/Users/barik/Downloads/oct 1 bin/CamScanner 09-20-2026 01.00.pdf`, SHA-256 `73fab89e61dda144b8c4b2d16239a756564303847917f1f0a69fdd283c3f6640`. `batch_ocr.py` checks that hash before reading. Its eleven 300 dpi row crops are **approximate** and can be wrong on title and appendix pages; output JSON records the crop geometry and is never an accepted transcription. It saves after each physical page, so an interrupted run can resume by rerunning the same range.

The local models used in the October 2026 pilot are `ara.traineddata` and `ben.traineddata` from the [official Tesseract best-model repository](https://github.com/tesseract-ocr/tessdata_best). Store them outside the website, for example under `/tmp/quran-ocr-tessdata/`; they are tools, not Quran source content. `pypdfium2` and Pillow are available in the bundled Codex Python runtime. Tesseract is installed at `/opt/homebrew/bin/tesseract` on this Mac.

Example from `web-views/`:

```sh
/Users/barik/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 scripts/transcribe/batch_ocr.py \
  --pdf '/Users/barik/Downloads/oct 1 bin/CamScanner 09-20-2026 01.00.pdf' \
  --model-dir /tmp/quran-ocr-tessdata \
  --output-dir evidence/resume-2026-10-16/ocr-queue \
  --start 51 --end 100
```

Before moving a suggestion to `source/pages/page-NNN.json`, inspect the corresponding original PDF row, write all Arabic letters and harakat, Bengali text and every annotation as structured fields, document any uncertainty, then have a different reviewer compare the authored JSON with the source. The website release gate stays blocked until every page and each letter anchor have independent source and browser acceptance.
