হাদিসের ডেটার মূল উৎস অনুসন্ধান — দ্বিতীয় তদন্ত

২৬ অক্টোবর ২০২৬। এটি আগের APK রিপোর্টের পরিপূরক। লক্ষ্য: অ্যাপ কোন domain থেকে data আনে তার বাইরে গিয়ে প্রকাশনী, অনুবাদক ও digital dataset-এর উৎস খোঁজা।

**ফলাফল**

সব হাদিস/অনুবাদ IRD নতুন করে লিখেছে—এমন প্রমাণ নেই; বরং বিভিন্ন প্রকাশিত সংস্করণ ব্যবহারের সুস্পষ্ট attribution আছে। তবে সব data একটি ready-made API/database থেকে নিয়েছে, কিংবা নিজে কোনো digitization করেনি—সেটিও প্রমাণিত নয়। প্রাপ্ত প্রমাণ published editions + পুরোনো digitization কাজ + shared digital text + নতুন structured feature—এই মিশ্র ব্যবস্থার সঙ্গে সামঞ্জস্যপূর্ণ। শেষ কথাটি প্রমাণগুলো মিলিয়ে করা ব্যাখ্যা, তাদের অপ্রকাশিত pipeline-এর বিবরণ নয়।

**বাংলা অনুবাদ ও গ্রন্থের নিশ্চিত attribution**

নিচের তথ্যগুলো iHadis-এর সংশ্লিষ্ট বাংলা বইয়ের description থেকে সরাসরি পড়া হয়েছে। ওয়েব সার্চের reader কিছু URL-এ ব্যর্থ হলেও একই public URL-এর HTML স্বাভাবিক HTTP GET-এ পাওয়া গেছে। এগুলো প্রকাশনীর attribution; publisher file সরাসরি পাওয়া, OCR করা কিংবা অন্য website থেকে import—কোন পথে এসেছে সেটি এই metadata বলে না।

| বই | উল্লেখিত প্রকাশনী | বাড়তি তথ্য |
|---|---|---|
| [সহীহ বুখারী](https://ihadis.com/bukhari) | তাওহীদ পাবলিকেশন্স | আগের তদন্তেও নিশ্চিত |
| [সহীহ মুসলিম](https://ihadis.com/muslim) | হাদীস একাডেমী, ঢাকা | আগের তদন্তেও নিশ্চিত |
| [সুনানে আন-নাসায়ী](https://ihadis.com/nasai) | ইসলামিক ফাউন্ডেশন বাংলাদেশ | নতুনভাবে যাচাই |
| [সুনানে আবূ দাউদ](https://ihadis.com/abu-dawud) | তাওহীদ পাবলিকেশন্স | তাহকিক আলবানীর নামে |
| [জামে আত-তিরমিযী](https://ihadis.com/tirmidhi) | হুসাইন আল মাদানী প্রকাশনী | তাহকিক আলবানীর নামে |
| [সুনানে ইবনে মাজাহ](https://ihadis.com/ibn-majah) | হুসাইন আল মাদানী প্রকাশনী | একই description-এ অনুবাদ/সম্পাদনা তাওহীদ পাবলিকেশন্স অনুবাদ ও গবেষণা বিভাগের নামে |
| [রিয়াদুস সালেহীন](https://ihadis.com/riyadus-salihin) | তাওহীদ পাবলিকেশন্স | আগের তদন্তেও নিশ্চিত |
| [বুলুগুল মারাম](https://ihadis.com/bulugul-maram) | তাওহীদ পাবলিকেশন্স | নতুনভাবে যাচাই |
| [মিশকাতুল মাসাবীহ](https://ihadis.com/mishkatul-masabih) | হাদিস একাডেমী | তাহকিক আলবানীর নামে |
| [হাদীস সম্ভার](https://ihadis.com/hadis-somvar) | ওয়াহীদিয়া ইসলামিয়া লাইব্রেরী, রাজশাহী | সংকলক আব্দুল হামিদ ফাইযী আল-মাদানী |
| [সিলসিলা সহিহা](https://ihadis.com/silsila-sahiha) | আতিফা পাবলিকেশন্স | অনুবাদক হাফেজ মুফতি মোবারক সালমান |

ইবনে মাজাহর প্রকাশনী ও অনুবাদ/সম্পাদনার দুটি আলাদা প্রতিষ্ঠানের নাম সাইটে যেভাবে আছে সেভাবেই দেওয়া হয়েছে; স্বাধীনভাবে edition title page মিলিয়ে যাচাই করা হয়নি। Muatta-এর দৃশ্যমান description-এ publisher পাইনি, তাই অনুমান করে যোগ করা হয়নি।

**ইংরেজি লেখার নমুনা পরীক্ষা**

iHadis-এর API থেকে বুখারী ১, ২ ও ৫৪-এর ইংরেজি `translation` নিয়েছি। এগুলো `fawazahmed0/hadith-api`-র একই নম্বরের `eng-bukhari` text-এর সঙ্গে character-by-character তুলনা করেছি।

| হাদিস | ফল |
|---|---|
| বুখারী ১ | শেষের full stop ও quotation mark ছাড়া একই |
| বুখারী ২ | শেষের full stop ছাড়া একই |
| বুখারী ৫৪ | শেষের full stop ও quotation mark ছাড়া একই |

এই dataset-এর [editions metadata](https://raw.githubusercontent.com/fawazahmed0/hadith-api/1/editions.json) ইংরেজি বুখারীর author হিসেবে Muhsin Khan উল্লেখ করে। [Sunnah.com-এর বুখারী ১](https://sunnah.com/bukhari:1)-এও একই ইংরেজি অনুবাদের মূল পাঠ দেখা যায়।

এতে তিনটি নমুনার ইংরেজি text একই প্রচলিত অনুবাদের অন্তর্গত হওয়ার শক্ত প্রমাণ পাওয়া যায়। এতে IRD সরাসরি fawaz API থেকে নিয়েছে প্রমাণ হয় না। দুটো project একই অন্য উৎস ব্যবহার করতে পারে; একই বই থেকে digitize-ও করতে পারে। আরবি নমুনায়ও প্রচলিত পাঠের সঙ্গে যথেষ্ট মিল আছে, কিন্তু একই মূল হাদিসের আরবি হওয়ায় তা transfer direction নির্ণয়ের দুর্বল প্রমাণ।

বাংলা নমুনা raw character হিসাবে একই নয়। অন্য dataset-এ chapter text, narrator ও note যুক্ত থাকার মতো structural পার্থক্য আছে; তাই একটি raw similarity percentage-কে source শনাক্তকরণ হিসেবে ব্যবহার করা হয়নি।

[fawaz-এর References](https://github.com/fawazahmed0/hadith-api/blob/1/References.md)-এ Sunnah.com, HadithBD, alQuranBD/Bangla-Hadith-api, al-maktaba.org ইত্যাদি উল্লেখ আছে। এটি fawaz-এর source list, IRD-এর source list নয়। একই লেখা ওই জায়গাগুলোতে পাওয়া গেলেই IRD সেখান থেকে নিয়েছে বলা যাবে না।

**আরবি গবেষণাসংক্রান্ত যে সূত্রগুলো নিজেরাই credit দিয়েছে**

iHadis-এর [বাংলা Credits](https://ihadis.com/credit)-এ `الباحث الحديثي` এবং `تراث` আছে। এ দুই নাম অনুসরণ করে পাওয়া যায়:

- [Al-Bahith al-Hadithi / sunnah.one](https://nuqayah.com/projects/sunnah): Nuqayah-এর official description অনুযায়ী Dorar al-Saniyyah-এর hadith encyclopedia-তে search করে, বিভিন্ন বর্ণনা ও grading দেখায়। তাই acknowledged toolটির upstream হিসেবে Dorar নিশ্চিত।
- [Turath](https://nuqayah.com/projects/turath): Shamela-ভিত্তিক classical library পড়া/খোঁজার tool। [Nuqayah-এর নিজস্ব ঘোষণা](https://t.me/s/nuqayah?before=93)-তে Shamela থেকে বই পড়ার কথা আছে।

প্রমাণের সীমা: IRD ওই tools-কে credit দিয়েছে, tools নিজেদের উৎস জানিয়েছে। কিন্তু IRD-এর কোন নির্দিষ্ট table, কতটি hadith বা কোন grade ওই পথ ধরে এসেছে—তা প্রকাশ করা হয়নি। Credits-ও generic; ইংরেজি credits-এ Dua/Ruqyah-এর উল্লেখ দেখা গেছে। ফলে credits-কে field-by-field data provenance হিসেবে নেওয়া যাবে না। Sunnah.one এবং Sunnah.com আলাদা service।

**নিজেরা digitization করেছে কি না: নতুন ঐতিহাসিক প্রমাণ**

[ajaxray/iHadisDesktop](https://github.com/ajaxray/iHadisDesktop)-এর README নিজেকে iHadith Project-এর desktop application বলে এবং Arabic/Bangla/English hadith digitization-এর লক্ষ্য উল্লেখ করে। GitHub commit history সরাসরি পরীক্ষা করে প্রথম commit-এর তারিখ পেয়েছি **১৭ জুন ২০১৩**। Repository-তে database schema, book/chapter/hadith model এবং search-এর code আছে। এটি বর্তমান Android 8.1.0-এর source নয়, কিন্তু project-এর পুরোনো database/software কাজের সরাসরি ঐতিহাসিক প্রমাণ। [Commit history](https://github.com/ajaxray/iHadisDesktop/commits/master/)

আরও একটি সূত্র: [পুরোনো app description-এর mirror](https://www.androidblip.com/android-apps/com.ihadis.ihadis.html)-এ কয়েকটি হাদিসগ্রন্থ টাইপ করা এবং আরও টাইপ করার পরিকল্পনার কথা আছে। এটি third-party mirror-এ সংরক্ষিত পুরোনো দাবি, স্বাধীন audit নয়। ফলে এটিকে সহায়ক historical evidence হিসেবে ধরা হয়েছে। এটি আগের রিপোর্টের “টাইপ করার ইতিহাস পাওয়া যায়নি” বক্তব্যকে আংশিক সংশোধন করে।

উল্টো data flow-এর primary evidence-ও আছে: [rakibrahman/hadith-api](https://github.com/rakibrahman/hadith-api)-এর README iHadis-কে hadith দেওয়ার জন্য ধন্যবাদ দেয়। অর্থাৎ এই নির্দিষ্ট API নিজেই iHadis-কে upstream বলছে। Public GitHub-এ একই data দেখলেই সেটিকে IRD-এর upstream ভাবা যাবে না।

**শব্দে-শব্দে ও root data-র উৎস**

এখানে নির্দিষ্ট বাইরের উৎস এখনও শনাক্ত হয়নি। আগের যাচাই করা API-তে `wordId`, `position`, `meaning`, `transliteration`, `pos`, `root`, `lemma`, `relatedWords` আছে। কিন্তু publisher, dictionary title, translator বা provenance field নেই। Reader client শুধু সেই structured response দেখায়।

Public web search এবং GitHub repository search-এ hadith word-by-word-এর অন্য project পাওয়া গেছে। উদাহরণস্বরূপ [imkhan3/Populate-Contently](https://github.com/imkhan3/Populate-Contently) Sunnah.com Arabic থেকে word translation তৈরি করার কথা বলে; তার প্রকাশিত code-এ Google translation ব্যবহৃত। কিন্তু IRD-এর সঙ্গে কোনো প্রমাণিত সম্পর্ক বা একই data structure পাওয়া যায়নি। তাই এটিকে IRD-এর source বলা হয়নি। একইভাবে Quranic Arabic Corpus, Quran.com, Turath বা Dorar-কে IRD-এর বাংলা word-by-word data-র উৎস বলে চিহ্নিত করার প্রমাণ পাওয়া যায়নি।

অটোমেশন দিয়ে word mapping তৈরি করা প্রযুক্তিগতভাবে সম্ভব, কিন্তু এ থেকে IRD AI/Google Translate ব্যবহার করেছে বলা যায় না। তাদের notice featureটিকে পরীক্ষামূলক এবং scholarly checking অসম্পূর্ণ বলছে—এটুকুই নিশ্চিত। [পাঠক পেজ](https://ihadis.com/bukhari/hadith/1)

**কোন সিদ্ধান্ত কতটা নিশ্চিত**

| সিদ্ধান্ত | প্রমাণের অবস্থা |
|---|---|
| বাংলা content-এর গুরুত্বপূর্ণ অংশ আগে প্রকাশিত বই/অনুবাদের | শক্ত, বইয়ের description-এ attribution |
| ইংরেজি বুখারীর পরীক্ষিত তিনটি text প্রচলিত অন্য dataset-এর একই অনুবাদ | সরাসরি তুলনায় নিশ্চিত |
| iHadis-এর পুরোনো digitization/database কাজ ছিল | ২০১৩ GitHub code/history-তে প্রমাণ |
| কিছু অন্য API iHadis থেকে hadith নিয়েছে | সংশ্লিষ্ট README-তে সরাসরি credit |
| Dorar/Shamela-ভিত্তিক tools-কে IRD credit দেয় | credit এবং tool docs মিলিয়ে নিশ্চিত; data কতটা নিয়েছে অজানা |
| IRD পুরো dataset fawaz/Sunnah.com/HadithBD থেকে সরাসরি নিয়েছে | প্রমাণিত নয় |
| শব্দে-শব্দে অর্থ ও root data-র নির্দিষ্ট supplier | অজানা |
| IRD তা AI দিয়ে বানিয়েছে | প্রমাণিত নয় |

আরও নির্ভুল উৎস নির্ধারণের জন্য IRD-এর word-by-word source note, গবেষণা বিভাগের বিবৃতি বা upstream import/attribution manifest প্রয়োজন। বড় corpus দেখে প্রস্তুত অন্য database নেওয়া হয়েছে ধরে নেওয়া যথেষ্ট নয়; নমুনা মিল পেলেও direction ও agreement আলাদাভাবে যাচাই করতে হয়।

`source-tracing-evidence.json`-এ তিনটি ইংরেজি comparison-এর exact differences ও source URL রাখা আছে। দীর্ঘ হাদিসের অনুবাদ রিপোর্টে পুনঃপ্রকাশ করা হয়নি।
