# Source legend audit — 2026-10-03

Fresh local renders of the original PDF confirm that the 55 empty `printed` fields in the seven existing content pages represent **52 oval-enclosed inverted-V wedges and 3 solid downward arrows**. These are observed printed symbols, not unknown question marks. Every occurrence and its source JSON hash is mapped in `source-legend-audit.json`.

The PDF4 footer labels the enclosed wedge **আরবী সাকিন**. It is not Bengali digit ৮ or ১, ASCII A, or a plain sukun glyph. A dedicated text-font glyph can preserve its observed graphical identity while keeping Unicode identity unspecified. Source rings vary naturally in the scan. Exact per-occurrence outline fidelity still needs rendered comparison.

PDF5 distinguishes ordinary ১ (এক আলিফ), ringed ১ (দম ফেলিলে এক আলিফ), ringed ২ (দম ফেলিলে দুই আলিফ), ৩ (তিন আলিফ), ৪ (চার আলিফ), and a hooked/lobed compound mark meaning **দম ফেলিলে তিন / না ফেলিলে এক**. The latter is a candidate ৬ shape, but its Unicode identity is not independently verified. Existing source errata correctly prohibit substituting ordinary ৩. Footer circles are also used as explanatory bullets: that does not license adding rings to every occurrence.

Fresh crops show the three arrows above stop boundaries: PDF3 `r4-a15` over ম / verse ৮; PDF6 `r1-a16` over ম following مَثَلًا; PDF7 `r10-a2` over ج following عَدُوٌّ. The PDF4/5 footer does not define their meaning. The PDF7 arrow should not be described as anchored to a known Arabic letter in `r10w2`.

The damaged PDF3 `r0-a8` remains **unresolved**. The legacy candidate শ is not confirmed by the source. A fresh enlarged crop shows ink loss/noise and cannot establish either শ or ১. Preserve this uncertainty and occurrence; do not turn a guess into verified content or silently remove it. A visible textual status can identify an unresolved source mark without printing a bogus Quran character.

Some legacy annotation bboxes truncate the mark; wider fresh crops were read to confirm the full enclosed-wedge shapes. The montage is evidence of classification, not approval of exact geometry. No letter-level anchoring or UI rendering is approved here. All760-page conversion and 114-surah verification remain incomplete; this report cannot support a Quran-wide completion claim.

## Expanded conditional and ring audit

All42 `printed:৬` / `conditional:true` occurrences were subsequently independently inspected in fresh original-PDF crops. All42 match the conditional hooked-bowl family illustrated by PDF5 (দম ফেলিলে তিন / না ফেলিলে এক). This supports a source-specific conditional glyph class for all42; Unicode6 identity remains unverified, and this does not establish exact outline/letter anchoring. Occurrence IDs and hashes are appended as `conditionalOccurrences`.

All8 explicitly ringed ১/২ records were also inspected. Each has one enclosing ring around the digit, not two. No enclosure corrections are required for those eight records. PDF5 explanatory outer bullet circles must not be added to ordinary in-text glyphs. This check did not search all unenclosed digit records for previously missed rings.
