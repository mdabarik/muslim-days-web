/** Unicode offsets are codepoints in JSON; DOM Range offsets are UTF-16. */
export function utf16Offset(text, codepoint) { return [...text].slice(0, codepoint).join('').length; }
export function measureGrapheme(textElement, grapheme) {
  const text = textElement.textContent;
  if ([...text].slice(grapheme.startCodepoint, grapheme.endCodepoint).join('') !== grapheme.text) throw new Error('Grapheme text mismatch');
  const node = textElement.firstChild;
  if (!node || node.nodeType !== Node.TEXT_NODE) throw new Error('Expected intact shaping text node');
  const range = document.createRange();
  range.setStart(node, utf16Offset(text, grapheme.startCodepoint));
  range.setEnd(node, utf16Offset(text, grapheme.endCodepoint));
  const rect = range.getBoundingClientRect();
  if (rect.width <= 0 || rect.height <= 0) throw new Error('Unmeasurable grapheme');
  return rect;
}
/** Infrastructure only. Current source data has no approved character anchors.
 * Preserve Arabic in one text node. Never split ligatures into independent boxes.
 * Shaping-cluster ambiguity still needs font-specific source verification.
 */
export function placeVerifiedAnchor(wrapper, textElement, mark, annotation, graphemes) {
  if (!annotation.verified || !annotation.targetGraphemeId) throw new Error('Unverified anchor');
  const grapheme = graphemes.find(g => g.id === annotation.targetGraphemeId);
  if (!grapheme?.verified || !grapheme.sourceBox) throw new Error('Unverified source grapheme');
  const box = measureGrapheme(textElement, grapheme), parent = wrapper.getBoundingClientRect();
  mark.style.right = 'auto'; mark.style.left = `${box.left + box.width / 2 - parent.left}px`;
  mark.style.transform = 'translateX(-50%)';
  mark.dataset.targetGrapheme = grapheme.id;
}
