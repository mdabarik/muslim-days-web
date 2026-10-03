# Arabic body sukun shape correction

The user identified circular Arabic vowel marks where the supplied PDF's ordinary verse text uses an open wedge. This concerns U+0652 ARABIC SUKUN (jazm), not the separately rendered instructional annotation band.

The correction is limited to ordinary Arabic word rendering. It preserves Unicode U+0652 and uses font shaping to keep the mark attached to its base letter. Do not replace it with an ASCII caret, split Arabic words into letters, position a floating overlay, or change the annotation catalogue. The already reviewed four-context first-ayah font remains separate.

Source review identified loop/teardrop-like sukuns in the ornate basmala. Its existing typeface must remain unchanged; a global sukun replacement would misrepresent that source style.

Current data includes 406 sukun codepoints in verse words and six in two basmalas. This inventory is of the seven available draft pages, not an audit of all 760 source pages. This correction does not certify all content, all positions, or full Quran completion.
