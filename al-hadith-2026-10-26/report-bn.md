পরবর্তী গভীর অনুসন্ধানে প্রকাশনী, ২০১৩ সালের digitization code এবং dataset comparison পাওয়া গেছে। [নতুন উৎস-অনুসন্ধান রিপোর্ট](source-tracing-bn.md) দেখুন।

আপনার দেওয়া Al Hadith APK: ডেটা, API, শব্দে-শব্দে ও অফলাইন ব্যবস্থা

পরীক্ষার তারিখ: ২৬ অক্টোবর ২০২৬। পরীক্ষা করা ফাইল: `/Users/bedata/Downloads/base.apk`।

**মূল ফলাফল**

এটি IRD Foundation-এর Al Hadith, package `com.ihadis.ihadis`, version **8.1.0**, versionCode **119**। অ্যাপটি Flutter ব্যবহার করে। নিজস্বভাবে সংগঠিত হাদিস ডেটা, অনলাইন API এবং অফলাইনের জন্য packaged data—তিনটিরই প্রমাণ পাওয়া গেছে। শব্দে-শব্দে তথ্যের জন্য আলাদা API আছে; একটি হাদিসের ক্ষেত্রে সেটি সরাসরি পরীক্ষা করে HTTP 200 পাওয়া গেছে। API-তে সাধারণ পাঠকের প্রবেশাধিকার থাকা, developer-দের জন্য আনুষ্ঠানিক public API থাকা এবং ডেটা পুনঃব্যবহারের অনুমতি থাকা আলাদা বিষয়।

**সুন্দর দেখায় কেন**

APK-র FontManifest-এ বাংলা Kalpurush, ইংরেজি Inter এবং আরবির জন্য Amiri, KFGQ ও Me_Quran আছে। Inter-এর একাধিক weight-ও আছে। SVG icons, আলাদা light/dark artwork, reading view ও word-by-word notice-এর asset পাওয়া গেছে। ফলে সুন্দর লেখা এবং layout তৈরির উপকরণ অ্যাপেই থাকে। API মূলত তথ্য দেয়; সেটি কীভাবে সাজিয়ে দেখানো হবে তা UI নির্ধারণ করে।

পরীক্ষা করা হাদিস API-তে `arabic`, `translation`, `narrator`, `note`, `chapter`, `section`, `book`, `grade` আলাদা field। `grade`-এর সঙ্গে display color-ও এসেছে। এই structured data থেকেই পৃথক আরবি অংশ, বাংলা অংশ, বর্ণনাকারী, হাদিসের মান ও reference সাজানো সম্ভব। APK-টি চালিয়ে তার সব screen মাপা হয়নি; exact spacing বা animation সম্পর্কে দাবি করা হচ্ছে না।

**কোন API পাওয়া গেছে**

ওয়েবসাইটের production client configuration-এ API base:

`https://ihadis.com/api/v1/trpc`

| Procedure | কাজ | পরীক্ষার ফল |
|---|---|---|
| `hadith.byId` | ভাষা, বই ও হাদিস নম্বর অনুযায়ী হাদিস | বাংলা বুখারী ১: HTTP 200 |
| `hadith.wordByWord` | নির্দিষ্ট হাদিসের শব্দ ও ভাষাগত তথ্য | বাংলা বুখারী ১: HTTP 200; ২৪টি entry |

দুটি request-এ login cookie বা API key পাঠানো হয়নি। একে documented, supported third-party API বলা যাচ্ছে না: পরীক্ষা করা অফিসিয়াল উৎসে সে ধরনের developer documentation বা ব্যবহার-অনুমতি পাওয়া যায়নি।

Android-এর `WidgetHadithRemote` class-ও `hadith.byId` call করে এবং `x-trpc-source: al-hadith-flutter` header দেয়। এটি অ্যাপের অন্তত widget অংশে tRPC API ব্যবহারের সরাসরি প্রমাণ। তবে ওই class-এ base URL বাইরে থেকে আসে; ওয়েবসাইটে পাওয়া host-ই APK-র প্রতিটি feature-এর host, এমন দাবি করা যায় না।

**শব্দে-শব্দে অর্থ আসলে কীভাবে আসে**

ওয়েব client-এ word-by-word mode চালু হলে `hadith.wordByWord` query হয়। Request-এ `bookSlug`, `hadithId`, `languageId` যায়। Response-এর প্রতি entry-তে নিচের তথ্য থাকে:

| Field | অর্থ |
|---|---|
| `position` | শব্দের ক্রম |
| `wordId` | শব্দের পরিচয় |
| `arabic`, `arabicClean` | আরবি এবং পরিষ্কার করা আরবি রূপ |
| `transliteration` | নির্বাচিত ভাষায় উচ্চারণ |
| `meaning` | অর্থ |
| `pos` | noun/verb/particle ইত্যাদি পদের ধরন |
| `root` | মূল অক্ষর, lemma, সাধারণ অর্থ ও সংশ্লিষ্ট শব্দ |

পরীক্ষায় `الأَعْمَالُ` শব্দের অর্থ এসেছে “আমলসমূহ”, পদ `noun`, root `ع-م-ل`, lemma `عَمَل`। অর্থাৎ পূর্ণ অনুবাদকে শুধু ফাঁক দিয়ে ভাগ করে দেখানো নয়; শব্দ ও মূল শব্দের মধ্যে structured mapping সরবরাহ করা হচ্ছে। বুখারী ১-এর ২৪টি entry পূর্ণ isnad-সহ আরবি লেখার প্রতিটি শব্দকে cover করে না; সব হাদিসে সমান coverage ধরে নেওয়া যাবে না।

এই endpoint নির্দিষ্ট কোন dictionary, গবেষক বা AI model থেকে তৈরি—response-এ সেই provenance নেই। তাই এটি AI-generated বা সম্পূর্ণ মানুষ-অনূদিত—কোনোটিই নিশ্চিত করা যাচ্ছে না।

ওয়েবসাইটের নিজস্ব word-by-word notice এটিকে পরীক্ষামূলক বলে এবং জানায় যে আলেমদের যাচাই সম্পূর্ণ হয়নি। এটি ডেটার বর্তমান যাচাই-অবস্থা সম্পর্কে তাদের নিজের বক্তব্য। [হাদিসের পাঠক পেজ](https://ihadis.com/bukhari/hadith/1)

**এত বই কোথা থেকে এসেছে**

তাদের About Us পেজ অনুযায়ী শুরুর প্রকল্পই ছিল হাদিসের database তৈরি করা। অর্থাৎ বিভিন্ন গ্রন্থ ও সংস্করণের তথ্য ডিজিটালভাবে সংগঠিত করা তাদের প্রকল্পের অংশ। কোন বই হাতে টাইপ করা, কোনটি OCR করা বা অন্য প্রতিষ্ঠানের data থেকে নেওয়া—সেই পূর্ণ production history প্রকাশিত পেজ থেকে জানা যায়নি। [তাদের পরিচিতি](https://ihadis.com/about-us)

কিছু বইয়ের বাংলা সংস্করণের প্রকাশনী সরাসরি যাচাই করা গেছে:

| বই | ওয়েবসাইটে উল্লিখিত প্রকাশনী/সংস্করণ |
|---|---|
| [সহীহ বুখারী](https://ihadis.com/bukhari) | তাওহীদ পাবলিকেশন্স |
| [সহীহ মুসলিম](https://ihadis.com/muslim) | হাদীস একাডেমী, ঢাকা |
| [সুনানে আবূ দাউদ](https://ihadis.com/abu-dawud) | তাওহীদ পাবলিকেশন্স |
| [রিয়াদুস সালেহীন](https://ihadis.com/riyadus-salihin) | তাওহীদ পাবলিকেশন্স |

প্রকাশনীর নাম পাওয়া মানে digitization agreement বা নির্দিষ্ট অনুবাদকের সম্পূর্ণ তথ্য পাওয়া নয়। এগুলো যাচাই করা edition attribution। বুখারী ১-এর note-এ আধুনিক প্রকাশনী ও ইসলামিক ফাউন্ডেশনের numbering reference-ও আছে; reference থাকা মানেই অনুবাদ ওই প্রকাশনী থেকে নেওয়া নয়।

Credits-এ বিভিন্ন মূল গ্রন্থের পাশাপাশি `الباحث الحديثي` ও `تراث` অ্যাপকে সাহায্যকারী উৎস হিসেবে উল্লেখ করেছে। তাদের API সরাসরি ব্যবহার করে কি না বা সেখান থেকে কতটুকু নিয়েছে, এ তালিকা সেটি বলে না। [অফিসিয়াল ক্রেডিট](https://ihadis.com/credit)

Play listing-এ ২৫টি হাদিস collection এবং বাংলা database-এ ৫২,৮৫৬ entry উল্লেখ আছে; marketing text-এ ৪৯,০০০+ কথাও আছে। এগুলো listing-এর দাবি, এই encrypted APK database খুলে গোনা সংখ্যা নয়। Collection-গুলোর মধ্যে পুনরাবৃত্ত বর্ণনা থাকতে পারে, তাই entry count-কে সবগুলো আলাদা অর্থের হাদিস বলা ঠিক হবে না। [অফিসিয়াল Play listing](https://play.google.com/store/apps/details?id=com.ihadis.ihadis&hl=en_CA)

**অফলাইনে কী থাকে**

APK-তে সরাসরি পাওয়া তিনটি data asset:

| Asset | Uncompressed size | যা নিশ্চিত হয়েছে |
|---|---:|---|
| `assets/flutter_assets/assets/databases/hadith.ihdb` | 967,823 bytes | IHDB custom encrypted package |
| `assets/flutter_assets/assets/databases/general_books.db` | 24,576 bytes | SQLite; ২৫টি সাধারণ বইয়ের catalogue |
| `assets/flutter_assets/assets/databases/prayer_locations.db` | 6,987,776 bytes | SQLite; দেশ, timezone, location ও coordinates |

`DatabasePackageCipher` code-এ IHDB header, ৩২-byte key এবং `AES/GCM/NoPadding` পাওয়া গেছে। তাই `hadith.ihdb` সাধারণ SQLite viewer-এ সরাসরি পড়ার ফাইল নয়। এখানে encryption খুলে payload পরীক্ষা করা হয়নি। ভেতরে সব হাদিস আছে, শুধু metadata আছে, নাকি প্রাথমিক কিছু content আছে—নিশ্চিত নয়।

`general_books.db`-তে একটি `general_books` table আছে। এতে title, writer, slug এবং chapter/section/page count আছে; বইয়ের পূর্ণ text table নেই। অর্থাৎ ২৫টি catalogue row মানে এই ছোট ফাইলের ভেতর ২৫টি সম্পূর্ণ বই রাখা নেই। এর বইগুলো নিয়মিত হাদিসের ২৫ collection-এর আলাদা তালিকা। সম্পূর্ণ catalogue নিচে এবং পাশের JSON ফাইলে আছে।

Play listing ডাউনলোড করে offline পড়া এবং collection আগে download না করেও online পড়া—দুটি ব্যবস্থার কথাই বলে। সুতরাং ব্যবহারকারীর কাছে দেখা বড় library আর initial APK-তে থাকা data একই জিনিস নয়। Offline-এ ঠিক কোন বই আছে তা ঐ device-এ কী download করা হয়েছে তার ওপরও নির্ভর করে। শব্দে-শব্দে অংশের app-side offline download/cache এই base APK থেকে নিশ্চিত হয়নি। [অফিসিয়াল feature description](https://play.google.com/store/apps/details?id=com.ihadis.ihadis&hl=en_AU)

**কোথায় host করা**

| অংশ | পাওয়া ঠিকানা/প্রমাণ | সীমা |
|---|---|---|
| ওয়েবসাইট | `ihadis.com` | কার্যকর reader ও বইয়ের পেজ পরীক্ষা করা হয়েছে |
| ওয়েব হাদিস API | `ihadis.com/api/v1/trpc` | দুটি read-only procedure HTTP 200 |
| বাইরের delivery/cache layer | HTTP header-এ Cloudflare | origin server-এর company/location বোঝা যায় না |
| ওয়েব framework | Next.js response header ও client bundles | physical database host বোঝা যায় না |
| Source service configuration | `https://source.ummah.one` | client schema-তে default; APK download host হিসেবে প্রমাণিত নয় |
| CMS configuration | `https://dev.irdfoundation.com` | client schema-তে default; সব হাদিস এখানে থাকে এমন প্রমাণ নেই |
| Report service configuration | `https://report.irdfoundation.com` | রিপোর্ট জমা দেওয়ার configuration; কোনো report পাঠানো হয়নি |

AWS, DigitalOcean, Hetzner বা অন্য কোনো origin provider-এর নাম নিশ্চিত করা যায়নি। Cloudflare ব্যবহার করা আর মূল database Cloudflare-এ রাখা এক কথা নয়। একইভাবে listing-এর Firebase/Firestore sync হলো bookmark, note ও reading activity-র জন্য; তা থেকে মূল হাদিস corpus Firestore-এ আছে বলা যায় না।

**নিজের অ্যাপে ব্যবহার করতে চাইলে**

এ UI-র ধরনের reading experience বানানো সম্ভব: structured hadith data, পরিষ্কার font/layout, আলাদা word mapping এবং offline download ব্যবস্থা লাগবে। কিন্তু iHadis-এর dataset/API নিজের অ্যাপের স্থায়ী dependency বানানোর আগে তাদের dataset/API access ও পুনঃব্যবহারের শর্ত জানতে হবে। তাদের প্রকাশিত terms বড় পরিসরে content পুনঃপ্রকাশ বা বাণিজ্যিক ব্যবহারের আগে সংশ্লিষ্ট অধিকারীর অনুমতি চায়। [তাদের শর্তাবলি](https://ihadis.com/terms-and-conditions)

অন্য documented source হিসেবে [Sunnah.com developer API](https://sunnah.com/developers) আছে—key চাইতে হয় এবং তারা dataset-এর একটি অংশ দেয়। [fawazahmed0/hadith-api](https://github.com/fawazahmed0/hadith-api) একাধিক ভাষার JSON dataset/API প্রকাশ করে। কোনোটিতেই iHadis-এর একই বাংলা অনুবাদ ও একই word-by-word dataset পাওয়া যাবে বলে এই তদন্তে নিশ্চিত করা হয়নি।

**যা এখনও অজানা**

১. অ্যাপের মূল Flutter native code-এর API configuration; এই base APK-তে `libapp.so`/native library নেই।
২. বই download করার exact URL, package contents, update manifest ও version policy।
৩. শব্দে-শব্দে data-র মূল dictionary, প্রস্তুতকারী, review process ও reuse licence।
৪. actual origin/database server provider।
৫. IRD তৃতীয় পক্ষকে supported API বা licensed dataset দেয় কি না।

পরবর্তী নির্ভুল app-side তদন্তের জন্য একই installation-এর architecture split APK-সহ পূর্ণ APK set/APKS/XAPK অথবা চলমান অ্যাপের network observation প্রয়োজন। এই রিপোর্টে অ্যাপ run, user account access বা encrypted payload extraction করা হয়নি।

**APK-তে পাওয়া সাধারণ বইয়ের catalogue**

এগুলো হাদিসবিজ্ঞান, ইতিহাস, ব্যাখ্যা ও সংশ্লিষ্ট বই; মূল হাদিস collection-এর তালিকা নয়। Writer field ফাঁকা থাকলে “উল্লেখ নেই” লেখা হয়েছে। `pages_count` database-এর field; physical printed page count হিসেবে যাচাই করা হয়নি।

| # | বই | catalogue-এ লেখক/সংকলক |
|---|---|---|
| 1 | উসূলে হাদীস | মাওলানা মুহাম্মাদ আমীন আসারী (মূল লেখক) |
| 2 | হাদীস সংকলনের ইতিহাস | শায়খ ড. মুস্তাফা আল-আযামী |
| 3 | তারীখে ইলমে হাদীস | উল্লেখ নেই |
| 4 | ইসলামে হাদীসের মর্যাদা | ড. আবু বকর মুহাম্মাদ যাকারিয়া |
| 5 | হাদীসের পরিচয় | জিলহজ আলী |
| 6 | হাদীসের পরিভাষা | ড. মুহাম্মদ আত্ব-তাহ্হান (মূল লেখক) |
| 7 | হাদীস শাস্ত্রের পরিভাষা | সানাউল্লাহ নজীর আহমদ |
| 8 | হাদীস শাস্ত্রের পারিভাষিক জ্ঞান | শায়খ আবদুল হামীদ ফাইযী মাদানী (সংকলক) |
| 9 | মুসতালাহুল হাদীস | উল্লেখ নেই |
| 10 | সহীহ মুসলিমের মুকাদ্দিমা | ইমাম আবুল হুসাইন মুসলিম ইবনুল হাজ্জাজ |
| 11 | এহইয়াউস সুনান | ড. খোন্দকার আব্দুল্লাহ জাহাঙ্গীর |
| 12 | বুস্তানুল মুহাদ্দিসীন | শাহ আবদুল আযীয মুহাদ্দিস দেহলভী |
| 13 | হাদীসের নামে জালিয়াতি — ১ম খণ্ড | ড. খোন্দকার আব্দুল্লাহ জাহাঙ্গীর |
| 14 | হাদীসের নামে জালিয়াতি — ২য় খণ্ড | ড. খোন্দকার আব্দুল্লাহ জাহাঙ্গীর |
| 15 | প্রচলিত জাল হাদীস | উল্লেখ নেই |
| 16 | জাল ও যঈফ হাদীস বর্জনের মূলনীতি | মুযাফফর বিন মুহসিন |
| 17 | হাদীস কেন মানতে হবে | কামাল আহমাদ |
| 18 | আমরা হাদীস মানতে বাধ্য | আবদুল্লাহ বিন আবদুর রাযযাক |
| 19 | হাদীস অস্বীকারকারীদের সংশয় নিরসন | ড. আহমাদ আবদুল্লাহ সাকিব |
| 20 | হাদীস আকীদা ও ফিকহের দলীল | মুহাম্মাদ নাসিরুদ্দীন আলবানী (মূল লেখক) |
| 21 | প্রজ্ঞার খনি: ৪০ হাদীস | শায়খ আবদুল জাব্বার |
| 22 | হাদীসে বর্ণিত দু'আ ও তার ব্যাখ্যা | উল্লেখ নেই |
| 23 | ঐতিহাসিক ঘটনাবহুল শিক্ষামূলক হাদীস — ১ম খণ্ড | ড. মুহাম্মাদ শওকত আলী (সংকলক) |
| 24 | এসো হাদীসের গল্প শুনি | শায়খ আবু মালেক মুহাম্মাদ বিন হামেদ (মূল লেখক) |
| 25 | হাদীসের গল্প | গবেষণা বিভাগ, হাদীছ ফাউন্ডেশন বাংলাদেশ (সংকলক) |

**পুনরায় যাচাই করার লিংক ও প্রমাণ**

- [hadith.byId: পরীক্ষিত request](https://ihadis.com/api/v1/trpc/hadith.byId?input=%7B%22json%22%3A%7B%22bookId%22%3A1%2C%22hadithId%22%3A%221%22%2C%22languageId%22%3A%22bn%22%7D%7D)
- [hadith.wordByWord: পরীক্ষিত request](https://ihadis.com/api/v1/trpc/hadith.wordByWord?input=%7B%22json%22%3A%7B%22bookSlug%22%3A%22bukhari%22%2C%22hadithId%22%3A%221%22%2C%22languageId%22%3A%22bn%22%7D%7D)
- [ওয়েবের API configuration bundle](https://ihadis.com/_next/static/chunks/72b9a843b4b4bdd3.js)
- [ওয়েবের শব্দে-শব্দে component bundle](https://ihadis.com/_next/static/chunks/420d49956d1bc882.js)
- `evidence.json`: APK hash, file sizes, fonts, API ফলাফল, এক শব্দের sample এবং তদন্তের সীমা।
- `general-books-catalog.json`: SQLite থেকে পাওয়া ২৫টি বইয়ের metadata।
