# iHadis বাংলা ডেটা — ডাউনলোড ও হোস্টিং প্যাক

উৎস: https://ihadis.com/api/v1/trpc — সংগ্রহের তারিখ: ২৬ অক্টোবর ২০২৬।

এই snapshot-এ **২৫টি বই, ৬৫৪টি অধ্যায়, ৫২,৮৫৬টি রেকর্ড এবং ২২৭টি JSON খণ্ড**।
বই, অধ্যায়, অনুচ্ছেদ ও রেকর্ডের ক্যাটালগ সংখ্যার সঙ্গে কোনো অমিল নেই। সব JSON
রেকর্ড SQLite-এর সঙ্গে মিলেছে। মূল `hadith.byId`-এর ৮০টি নমুনার সব field মিলেছে;
স্থানীয় API-র ১৮টি HTTP পরীক্ষাও পাস করেছে। বিস্তারিত `verification.json` এবং
`server-verification.json`-এ আছে।

বাংলা ক্যাটালগের সব ২৫টি বইয়ের আরবি মূল, বাংলা অনুবাদ, বর্ণনাকারী, মান,
টীকা, উপলব্ধ ব্যাখ্যা, অধ্যায় ও অনুচ্ছেদ সংগ্রহ করা হয়েছে। চূড়ান্ত রেকর্ড সংখ্যা,
ক্যাটালগের সঙ্গে অমিল থাকলে তার বিবরণ এবং খণ্ডসংখ্যা `manifest.json`-এ আছে।
এটি বাংলা (`bn`) সংগ্রহ। অন্য ভাষা এবং পৃথক `hadith.wordByWord` API-র ডেটা এতে নেই।

## খণ্ড ও ফাইল

- `catalog.json`: সব বই, প্রকাশনী, সংখ্যা এবং খণ্ডের ফাইলের তালিকা।
- `books/<slug>/index.json`: একটি বইয়ের তথ্য ও সব খণ্ডের তালিকা।
- `books/<slug>/chapters.json`: মূল অধ্যায়ের ক্রম ও নাম।
- `books/<slug>/part-001.json`: সর্বোচ্চ ২৫০টি হাদিসের একটি JSON খণ্ড।
- `hadith.sqlite`: পুনরায় API হোস্ট করার জন্য SQLite ডেটাবেস।
- `checksums.json`: ফাইল ঠিক আছে কি না যাচাই করার SHA-256।
- `source-notes.json`: উৎসের অনুচ্ছেদহীন রেকর্ড ও range-এর ব্যতিক্রমের তালিকা।

**খণ্ডগুলো ডাউনলোড/হোস্টিংয়ের সুবিধার জন্য বানানো ডিজিটাল ভাগ; মুদ্রিত বইয়ের
মূল খণ্ড নম্বর নয়।** API-তে পাওয়া মূল অধ্যায়, অনুচ্ছেদ, প্রকাশনী ও হাদিস ID
অক্ষুণ্ণ রাখা হয়েছে। ID string হিসেবে রাখুন; ভবিষ্যতে অক্ষরযুক্ত ID-ও থাকতে পারে।
একটি হাদিসের পরিচয় `(languageId, bookId, id)`। ভিন্ন বইয়ে একই ID থাকতে পারে।
মুসলিমের ভূমিকার ID `intro-1`-এর মতো। উৎসে অনুচ্ছেদ অনুপস্থিত থাকলে
`section: null`, `sectionId: -1` রাখা হয়েছে; কৃত্রিম অনুচ্ছেদ বানানো হয়নি।
একাধিক বইয়ে একই বর্ণনা থাকলে সেগুলো আলাদা রেকর্ড; অর্থগতভাবে অনন্য হাদিসের সংখ্যা নয়।

## শুধু JSON হোস্ট করতে

ZIP খুলে `catalog.json`, `manifest.json`, `checksums.json` এবং `books/` নিজের
static hosting / object storage-এ রাখুন। `catalog.json` থেকে খণ্ডের path পাওয়া যাবে।
এই path-গুলো ওই catalog-এর directory-র relative path। বাংলা/আরবি UTF-8 অক্ষুণ্ণ রাখুন।
নিজের host অনুযায়ী CORS ও JSON Content-Type কনফিগার করুন।

## API চালাতে

বড় SQLite-এর gzip কপি ও ZIP ফাইল Git LFS-এ রাখা হয়েছে। Git LFS install করে
clone করার পর `git lfs pull` চালান। SQLite খুলতে এই directory-তে
`gzip -dk hosting/hadith.sqlite.gz` চালান। Download cache Git-এ রাখা নেই; সব হাদিস
`hosting/books/`-এর JSON-এও আছে। LFS ছাড়াও এই directory-তে নিচের command
চালিয়ে সম্পূর্ণ offline-এ ডেটাবেস তৈরি ও যাচাই করতে পারবেন:

```sh
python3 build_database.py
python3 verify.py
python3 serve.py --host 127.0.0.1 --port 8080
```

ডেটাবেস পুনর্নির্মাণে তার binary checksum বদলাতে পারে; `build_database.py`
সেই checksum হালনাগাদ করে। মূল JSON-গুলোর checksum আগে যাচাই করে নেওয়া হয়।

ZIP খুলে `ihadis-bn` directory-তে:

```sh
python3 serve.py --host 127.0.0.1 --port 8080
```

Python 3 ছাড়া আলাদা package লাগে না। VPS-এ process supervisor এবং HTTPS reverse
proxy (যেমন Nginx/Caddy)-র পেছনে এই read-only server চালান।

```text
GET /health
GET /books
GET /books/bukhari
GET /books/bukhari/chapters
GET /books/bukhari/hadiths/1
GET /books/bukhari/chapters/1/hadiths?limit=100&offset=0
```

মূল URL-এর single-request response shape-এও পড়া যাবে:

```sh
curl --get 'http://127.0.0.1:8080/api/v1/trpc/hadith.byId' \
  --data-urlencode 'input={"json":{"bookId":1,"hadithId":"1","languageId":"bn"}}'
```

এটি সম্পূর্ণ tRPC server নয়: batching, অন্যান্য procedure বা mutation বাস্তবায়িত নেই।
অনুপস্থিত রেকর্ডে 404 এবং ভুল input-এ 400 পাওয়া যাবে। `siblings` একই অধ্যায়ের
রেকর্ডের ক্রম থেকে তৈরি; অধ্যায়ের প্রথম/শেষে যথাক্রমে prev/next null। অন্যান্য
content মূল API থেকে নেওয়া। উৎসে অধ্যায়ের range-এর সঙ্গে প্রকৃত ID-র ব্যতিক্রম
থাকলে মূল রেকর্ডের chapter assignment-ই রাখা হয়েছে।

## সংগ্রহ পুনরায় চালাতে

```sh
python3 download.py
python3 package.py
python3 verify.py
```

ডাউনলোডারের `raw/` cache থাকলে সফল request আবার করতে হবে না। নতুন snapshot নিতে
scripts একটি নতুন directory-তে চালান। প্রতি সেকেন্ডে সর্বোচ্চ প্রায় ৪টি request,
সর্বোচ্চ ৩টি একসঙ্গে; network/5xx-এ সীমিত retry আছে। 401/403/429 পেলে থামে।
`raw/`-এ request input, timestamp ও মূল API response থাকে। `chapters/`-এ অধ্যায়ভিত্তিক
উৎস কপি থাকে। বড় এই intermediate ফাইলগুলো hosting ZIP-এ দেওয়া হয়নি; workspace-এ আছে।

`python3 verify.py` চালিয়ে JSON খণ্ড বনাম SQLite-এর সব রেকর্ড, সংখ্যা, ID,
অনুচ্ছেদ ও checksum যাচাই করা যায়। `--source-samples` যোগ করলে প্রতিটি বই থেকে
কয়েকটি রেকর্ড সরাসরি `hadith.byId`-এর সঙ্গে সব field মিলিয়ে দেখে।

প্রতি অধ্যায়ের API total, duplicate ID, অনুচ্ছেদ link এবং বইয়ের ক্যাটালগ সংখ্যা
যাচাই করে export তৈরি হয়। উৎসের ব্যাখ্যা/অনুবাদের বিষয়বস্তুর নতুন সম্পাদনা বা ধর্মীয়
যাচাই করা হয়নি। Download/validation log এবং source metadata workspace-এ সংরক্ষিত।
