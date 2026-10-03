# কুরআন ওয়েব — অসম্পূর্ণ, যাচাইাধীন

**এটি সম্পূর্ণ ১১৪ সূরার রূপান্তর নয়। ব্যবহারকারীর ১০০% নির্ভুলতার শর্ত পূরণ হয়নি; প্রকাশযোগ্য সংস্করণ নয়।**

ওয়েব ইন্টারফেসটি Flutter প্রজেক্টের বাইরে তৈরি। Flutter-এর কোড, assets বা configuration এই কাজে পরিবর্তন করা হয়নি। মূল PDF ও পূর্বের পর্যালোচনার ফাইলও অপরিবর্তিত আছে।

## চালানো

এই ফোল্ডারে `npm start`, তারপর <http://127.0.0.1:4173> খুলুন। Node dependency বা build প্রয়োজন নেই; Python 3 static server চালায়। `file://` থেকে খুললে JSON fetch কাজ করে না।

## যা আছে

- বাংলা ইন্টারফেস, ১১৪ সূরার নেভিগেশন তালিকা ও নাম/নম্বর অনুসন্ধান।
- সংরক্ষিত উৎস-পৃষ্ঠা ও সেই সূরার উপলব্ধ আয়াতের উল্লেখ অনুযায়ী নেভিগেশন। এই সংস্করণে ফাতিহার বিসমিল্লাহ আলাদা, নম্বরবিহীন; মূলের আয়াত নম্বর অপরিবর্তিত।
- মোবাইল layout, আরবি ফন্ট ২৬–৫৬ px, নির্বাচিত আকারের device-local সংরক্ষণ।
- Real HTML text, স্থানীয় সংকুচিত WOFF2 ফন্ট, প্রতি পৃষ্ঠার JSON প্রয়োজনমতো fetch; cache সর্বোচ্চ তিনটি পৃষ্ঠা। কোনো Quran API, PDF viewer, scan, canvas বা ছবিভিত্তিক পাঠ নেই।
- পূর্বে সংরক্ষিত সাতটি পৃষ্ঠার খসড়া হুবহু JSON import; নতুন প্রতিলিপি বা স্বয়ংক্রিয় অনুমোদন নয়। মূল ডেটার ৫৭ সারি, ৪৯৭ word record এবং ৭০০ annotation record সংরক্ষিত। পৃষ্ঠা ৬ মাত্র তিন সারি।
- ১১৪টি সূরা ও ৭৬০টি physical PDF পৃষ্ঠার persistent progress। অজানা পাঠ তৈরি করা হয়নি।

## শর্ত পূরণে যা বাকি

পূর্ণ যাচাইকৃত পৃষ্ঠা **০**, সূরা **০**, অক্ষরভিত্তিক অনুমোদিত annotation anchor **০/৭০০**। সাতটি পৃষ্ঠার বাইরে ৭৫৩টি physical page-এর প্রতিলিপি নেই; সব physical page কুরআনের স্বতন্ত্র পাঠ নয়। উৎসে duplicate scan ও পরিশিষ্ট আছে। দুই পৃষ্ঠার পুরোনো body review নতুন ওয়েবের shape/position অনুমোদন নয়।

বর্তমান source annotation-এ word ID ও আনুমানিক horizontal fraction আছে। সেগুলোকে letter ID বানিয়ে নেওয়া হয়নি। UI-তে এগুলো স্পষ্টভাবে আনুমানিক খসড়া; পরস্পরের ওপর পড়ে যাওয়া চিহ্নের ভাসমান অবস্থান না দেখিয়ে খোলা তথ্যতালিকায় পাঠ রাখা হয়; অক্ষর-সংযুক্ত render হিসেবে গ্রহণযোগ্য নয়। ৩ অক্টোবরের সংশোধনে ৫৫টি `?`-এর source shape উদ্ধার করে native custom font-এ দেখানো হয়েছে; আরও ৪২টি শর্তসাপেক্ষ চিহ্ন মূলের shape template ব্যবহার করে। একটি ক্ষতিগ্রস্ত চিহ্নে স্পষ্ট `অস্পষ্ট` অবস্থা দেখানো হয়। মূল observed shape ও uncertainty JSON-এ থাকে। তিনটি তীরের stop/verse boundary উৎস থেকে নতুন করে যাচাই করে display target দেওয়া হয়েছে; এটি letter-level anchor approval নয়।

Amiri ও Noto Sans Bengali মূল প্রকাশনার হুবহু font নয়। আরবি shaping বজায় রাখতে প্রতিটি শব্দ এক text node। বর্তমান draft glyph shape, harakat, ring/rosette এবং source offsets চূড়ান্তভাবে যাচাই হয়নি। সংরক্ষিত পরিচিত header ও footer/প্রান্তলেখার পাঠ আলাদা source-details অংশে দেখানো হয়; null বা সম্ভাব্য পাঠকে নিশ্চিত পাঠ করা হয়নি। সব decorated title ও মূল বিন্যাস পুনর্নির্মাণ হয়নি।

`dist/anchors.js`-এ verified grapheme target-এর জন্য DOM Range পরীক্ষামূলক ব্যবস্থা আছে। **এটি exact-source-font সমাধান নয়।** Ligature-এর caret rectangle অক্ষরের প্রকৃত ink geometry-এর প্রমাণ নয়। সব বর্তমান target null রাখা হয়েছে। সঠিক source-compatible font, grapheme ink region ও independent review ছাড়া এটিকে production acceptance দেওয়া যাবে না। বিস্তারিত `evidence/typography-audit.md`।

## ডেটা এবং Flutter-এর জন্য চুক্তি

`DATA_FORMAT.md` ও `data.schema.json` পড়ুন। UI-independent JSON-এ মূল Unicode, source SHA256, physical page, candidate hash, original candidate, grapheme IDs, annotation evidence ও unresolved fields আছে। কোনো Dart-specific type নেই। ভবিষ্যৎ Flutter integration এখন করা হয়নি।

## পুনরুৎপাদন ও পরীক্ষা

- `npm run import`: মূল candidate file ও current progress hash মিলিয়ে সাতটি draft ও পুরো progress index তৈরি করে; পুরোনো উৎস বদলায় না।
- `npm run check`: Unicode loss, source hash, marker inventory, false verification এবং data integrity পরীক্ষা।
- `npm run release:check`: একই পরীক্ষা এবং পূর্ণ acceptance gate; বর্তমানে exit code **2** প্রত্যাশিত, কারণ বই অসম্পূর্ণ।
- `scripts/browser_check.cjs`: local Chrome/Playwright দিয়ে 320/390/1360 px, font 26/34/56, navigation, selection, local requests, lazy loading, incomplete states পরীক্ষা। `NODE_PATH`-এ Playwright দিন।

`evidence/browser-check.json` কেবল interface mechanics-এর প্রমাণ; PDF accuracy নয়। `evidence/source-audit.json`-এ নতুন করে সব ৭৬০ পৃষ্ঠার text-layer audit আছে। `evidence/progress.json` ও `evidence/validation.json` পরের কাজে checkpoint। কোনো background conversion চলছে বলে দাবি করা হচ্ছে না।

পূর্ণ বইয়ের পাঠ উদ্ধার, ক্ষতিগ্রস্ত অংশের নির্ভরযোগ্য পাঠ, source-compatible glyph ও letter anchor mapping, এবং প্রতিটি পৃষ্ঠার স্বাধীন content+web rendering review ছাড়া চূড়ান্ত করা সম্ভব নয়। পূর্ণতার gate ব্যর্থ হওয়ায় এই খসড়া অনলাইনে প্রকাশ করা হয়নি।

বিশেষ চিহ্নের নতুন উৎসবিশ্লেষণ, font contract, scope ও প্রমাণ: [SYMBOLS.md](SYMBOLS.md)।

The first printed Fatiha ayah now uses a scoped source-outline font for four audited word contexts, with native upper signs and the stop/verse ending. Rebuild with `PYTHONPATH=/tmp/quran-web-tools python3 scripts/build_opening_typography.py`; run `scripts/check_opening.cjs` with the bundled Node/Playwright runtime. The source heading is before the separate basmala. This is a limited typography correction, not full Fatiha or full Quran fidelity approval; remaining words use the existing fallback font.

Ordinary Arabic verse words use `fonts/QuranWedgeArabic.woff2`, a renamed Amiri derivative with only the two sukun glyph outlines changed to a source-traced open wedge. Unicode, shaping, anchor tables and metrics remain intact. The separate basmala/header style and all instructional annotations retain their previous fonts. Rebuild with `PYTHONPATH=/tmp/quran-web-tools python3 scripts/build_sukun_font.py`; provenance and licensing are recorded in `dist/data/sukun-font.json`. The seven-page `scripts/check_sukun.cjs` comparison verifies unchanged Arabic text/word widths and unchanged annotation text, font, geometry and visibility against the saved baseline. It does not approve complete source fidelity.
