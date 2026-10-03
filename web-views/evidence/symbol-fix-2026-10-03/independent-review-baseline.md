# Independent source baseline — 2026-10-03

Scope: known missing-symbol rendering in seven existing page drafts. This is not whole-Quran verification.

I inspected source crops before reading any implementation conclusions, then independently rendered PDF pages 4 and 5 footer regions directly from the original 760-page PDF using Poppler at 150 dpi. The fresh renders agree with the provided larger crops.

- PDF4 legend: a closed oval containing a Λ-like wedge, labelled **আরবী সাকিন**. Representative page1/2/3 crops share this morphology. Do not replace with `?`, an empty circle, or a standard Unicode character claimed to be authoritative. If the font glyph includes the enclosure, CSS must not enclose it again.
- PDF5 legend: visible Bengali number distinctions and different ring counts remain meaningful; global circle normalization would erase content.
- PDF3/6/7 arrows: three heavy filled downward arrows, separately printed next to neighboring circled signs. An arrow must not be discarded simply because it lacks the usual word target.
- PDF3 r0-a8: damaged far-left mark remains unreadable. The existing provisional **শ** is not independently validated. Its source identity uncertainty must remain visible in the data and UI.
- All 55 cells in supplied empty-mark sheets were inspected as baseline; partial edge crops require larger source contexts for individual conclusions. The page3 damaged oval remains morphology-visible despite damage; the different damaged far-left r0-a8 is not resolved by this comparison.

Final approval requires frozen app/font/catalog/data hashes, real desktop/mobile renders, native PUA selectable text with loaded font and no tofu, no double enclosure, retained arrows, and truthful unresolved/coverage disclosure. A visual repair does not validate any character-level anchor.
