# Independent body-sukun baseline

Direct local 300dpi crops from original PDF pages1–7 were inspected before implementation. In the representative running-body rows, sukun is an open-bottom **Λ-like wedge**, without an enclosing ring. This is distinct from the circled wedge in the upper instruction band, which must stay untouched.

**Important exception:** the purple decorative basmala on both PDF1 and PDF2 uses hooked/loop-like sukun shapes, not the running body's plain wedge. Restrict a body-font U+0652 change to running words; retain the basmala's separate typography. A blanket page-wide change would introduce a new source mismatch.

Damma is a loop-and-tail/waw-like mark and must not be changed because it looks round. Keep shadda, fatha/kasra, dagger alif, tanwin, end signs and instruction annotations unchanged. Preserve source Unicode U+0652 and only change its body-font rendering.

The JSON baseline includes original hashes of annotation files, opening-font assets, seven page datasets and Amiri. This representative review does not verify all760pages or exact positions of all marks.
