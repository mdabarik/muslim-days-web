# কুরআন ওয়েব প্রজেক্ট — AI agent handoff

অবস্থান: `/Users/barik/Desktop/muslims-days`।

আগের তৈরি কাজটি এখানে গুছিয়ে রাখা হয়েছে। এই প্যাকেজিংয়ে ওয়েবসাইটের নতুন ফিচার বা Flutter পরিবর্তন করা হয়নি।

- `skills/quran-web-handoff/SKILL.md` — অন্য AI agent-এর কাজ বোঝার মূল নির্দেশনা।
- `web-views/` — পুরো বর্তমান HTML/CSS/JavaScript প্রজেক্ট, ফন্ট, JSON, scripts ও review evidence; মূল `quran-web/` থেকে হুবহু কপি।
- `output-json/` — আলাদা JSON export, প্রয়োজনীয় ফন্ট, schema ও format documentation।
- `QURAN-WEB-HANDOFF.json` — ফাইলের SHA256, মূল PDF-এর পরিচয়, অবস্থান ও প্রকৃত অগ্রগতি।

## অন্য AI agent-কে এই কথাটি দিন

> এই প্রজেক্টের `skills/quran-web-handoff/SKILL.md` এবং তার current-state reference পড়ো। `web-views`-এ আগের কুরআন ওয়েবসাইট আছে; `output-json`-এ তার ডেটা ও ফন্ট export। বর্তমান কাজ বুঝে আমার পরবর্তী নির্দেশ অনুযায়ী কাজ করবে। মূল PDF ছাড়া অন্য সংস্করণের পাঠ বসাবে না, অসম্পূর্ণ কাজকে সম্পূর্ণ বলবে না, এবং আলাদা অনুমতি ছাড়া Flutter বদলাবে না।

## চালানো

প্রজেক্ট root থেকে:

```sh
cd web-views
python3 -m http.server 4180 --bind 127.0.0.1 --directory dist
```

তারপর `http://127.0.0.1:4180/#surah=1` খুলুন। Build বা npm install লাগে না। আগের 4173 preview মূল `quran-web/` কপির হতে পারে; দুই কপি গুলিয়ে ফেলবেন না।

**পূর্ণ ওয়েব প্রজেক্ট রাখা হয়েছে, কিন্তু কুরআনের কনটেন্ট সম্পূর্ণ নয়:** ১১৪ সূরার তালিকা আছে, সাত পৃষ্ঠার খসড়া আছে; পৃষ্ঠা ৬ আংশিক। পুরো ১১৪ সূরার হুবহু রূপান্তর ও অক্ষরভিত্তিক যাচাই বাকি। মূল PDF বড় হওয়ায় আরেকটি কপি করা হয়নি; তার আসল path ও hash JSON/skill-এ আছে। Source import/font rebuild-এর বিদ্যমান sibling source dependencies-ও সেখানে লেখা আছে।
