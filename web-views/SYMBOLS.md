# কারিয়ানা চিহ্ন সংশোধন — ৩ অক্টোবর ২০২৬

মূল PDF-এর ৪ ও ৫ নম্বর physical পৃষ্ঠার নির্দেশনা নতুন করে পড়ে সংরক্ষিত সাতটি পৃষ্ঠার বিশেষ চিহ্নগুলো মিলিয়ে দেখা হয়েছে। এগুলো কেবল character code খালি থাকার জন্য আগে `?` হিসেবে দেখানো হচ্ছিল।

| মূলের চিহ্ন | উৎসে পাওয়া পরিচিতি/ব্যাখ্যা | বর্তমান ব্যবস্থা |
|---|---|---|
| ডিম্বাকার ঘেরের মধ্যে ∧-আকৃতি | আরবী সাকিন — PDF৪ | ৫২টি ব্যবহারে source-derived ফন্ট-গ্লিফ |
| নিচমুখী মোটা তীর | ওয়াক্‌ফ/আয়াত-সীমানার ওপর দেখা যায়; PDF৪–৫-এ আলাদা অর্থ নেই | ৩টি ব্যবহারে ফন্ট-গ্লিফ, source-observed boundary target |
| বাটি, ভেতরের বাঁকানো রেখা ও ডান লোববিশিষ্ট বিশেষ চিহ্ন | দম ফেলিলে তিন / না ফেলিলে এক — PDF৫ | ৪২টি ব্যবহারে সাধারণ `৬`-এর বদলে মূল-আকৃতির ফন্ট-গ্লিফ; standard Unicode identity দাবি নেই |
| ঘেরযুক্ত ১ / ২ | দম ফেলিলে এক আলিফ / দম ফেলিলে দুই আলিফ — PDF৫ | আটটি source occurrence-এ একটিই ঘের দেখা গেছে; দ্বিতীয় ঘের যোগ করা হয়নি |
| ক / শ / গ / ম | ক্বলক্বলাহ / শিষ / গুন্নাহ / মোটা — PDF৪ | আগের পাঠ সংরক্ষিত; নির্দেশনার ঘের দেখে সব running mark-এ ঘের যোগ করা হয়নি |
| source ইখফা-চিহ্ন | ইখফা — PDF৪ | family meaning নথিভুক্ত; standard Unicode digit identity এই সংশোধনে প্রতিষ্ঠিত হয়নি |

পৃষ্ঠা ৩-এর `r0-a8` চিহ্ন ক্ষতিগ্রস্ত। আগে `শ` ছিল provisional candidate; এখন সেটিকে নিশ্চিত অক্ষর হিসেবে না দেখিয়ে **অস্পষ্ট** অবস্থা ও কারণ দেখানো হয়। মূল candidate/evidence বাদ দেওয়া হয়নি।

## Native text

`dist/fonts/QarianSymbols.woff2` মাত্র ৯৬০ বাইটের outline font; এতে bitmap বা SVG font table নেই। দৃশ্যমান চিহ্নগুলো HTML text span-এর private-use Unicode character। ছবির ওপর hidden text নয়। চিহ্ন নির্বাচন ও copy করা যায়; একই আকৃতি অন্য অ্যাপে দেখাতে এই ফন্ট ও JSON symbol ID দরকার।

| Symbol ID | প্রকল্পের codepoint |
|---|---|
| `ringed-wedge` | U+E000 |
| `bare-wedge` | U+E001; catalogue-এ আছে, এই সংশোধনে Arabic body-তে প্রয়োগ হয়নি |
| `solid-down-arrow` | U+E002 |
| `conditional-three-or-one` | U+E003 |

এই codepoint-গুলো নতুন standard Unicode identity দাবি করে না। Shape template এসেছে source contour থেকে; source resolution, threshold ও outline approximation-এর সীমা `dist/data/symbol-catalog.json`-এ আছে। প্রতিটি occurrence-এর ঠিক একই pixel outline বা letter anchor অনুমোদিত নয়।

## ডেটার পৃথক স্তর

`originalCandidate` ও `annotations[].text` অপরিবর্তিত। নতুন `display`-এ reviewed source-shape ID, PUA character, font/review hashes এবং verification scope থাকে। ক্ষতিগ্রস্ত চিহ্নের `display.status` হলো `unresolved_identity`। তিনটি তীরের `displayAttachment`-এ word-এর বদলে source-observed stop/verse boundary থাকে। এগুলো letter-level anchor দাবি নয়।

`bind_symbols.py` কেবল occurrence ID ও SHA256-bound independent source finding থেকে mapping করে। শুধু সব খালি string খুঁজে একই চিহ্ন বসানো হয় না। উৎস বা finding বদলালে binding/validation ব্যর্থ হয়।

## পরীক্ষা ও সীমা

সাতটি পৃষ্ঠার ৫২ সাকিন, ৩ তীর, ৪২ বিশেষ মাত্রাচিহ্ন এবং আটটি ঘেরযুক্ত অঙ্ক নতুন source crops-এ পর্যালোচিত। মোট **৫৫টি আগের question-mark occurrence** বদলেছে, **৯৭টি custom-glyph occurrence** আছে। পৃষ্ঠা ৩-এর একটি ক্ষতিগ্রস্ত পরিচয় এখনো অমীমাংসিত।

Browser test সব সাত পৃষ্ঠায় ৩২০/৩৯০/১২০০ px ও ২৬/৩৪/৫৬ font size-এ glyph availability, text preservation, complete mark inventory, single enclosure, boundary placement, native selection এবং overflow পরীক্ষা করে। Structural tests ভুল glyph binding, wrong boundary target, dropped haraka ও damaged-character promotion প্রত্যাখ্যান করে।

এটি পুরো ১১৪ সূরার রূপান্তর বা নির্ভুলতার অনুমোদন নয়। বাকি ৭৫৩ physical পৃষ্ঠায় structured transcription নেই; বর্তমান সাত পৃষ্ঠারও exact letter geometry/full-page acceptance বাকি। একই catalogue ভবিষ্যৎ পৃষ্ঠায় ব্যবহার করা যাবে **সেই occurrence যাচাই হওয়ার পরে**। Flutter-এর কোনো ফাইল পরিবর্তন করা হয়নি।

## প্রমাণ ও পুনরুৎপাদন

- `evidence/symbol-fix-2026-10-03/source-legend-audit.json`: source findings, per-occurrence hashes ও uncertainty।
- `evidence/symbol-fix-2026-10-03/independent-review-baseline.json`: implementation দেখার আগে স্বাধীন baseline।
- `evidence/symbol-fix-2026-10-03/browser-check.json`: interface checks, source-accuracy approval নয়।
- `evidence/symbol-fix-2026-10-03/integration.json`: নতুন mapping counts/hashes।
- `scripts/build_symbol_font.py`: ফন্ট পুনর্নির্মাণ; fonttools, brotli ও Pillow দরকার।
- `scripts/bind_symbols.py`: source-reviewed mapping পুনরায় প্রয়োগ। `npm run import` শেষে এটিও চলে।
