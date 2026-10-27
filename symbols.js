/** Project PUA glyphs reproduce observed shapes; they do not assert Unicode identity.
 * Annotation anchors and whole-page acceptance remain independent requirements.
 */
let catalog = new Map(), fontAvailable = false;
export function configureSymbols(data, ready) {
  catalog = new Map(data.symbols.map(g => [g.id, g]));
  fontAvailable = ready;
}
export function symbolDescriptor(annotation, original) {
  const display = annotation?.display;
  if (display?.status === 'unresolved_identity') return {text:'অস্পষ্ট', label:'মূলের ক্ষতিগ্রস্ত চিহ্ন; পরিচয় অমীমাংসিত', unresolved:true};
  if (display?.symbolId) {
    const glyph = catalog.get(display.symbolId);
    if (!glyph || glyph.text !== display.character) return {text:'অস্পষ্ট', label:'চিহ্নের তথ্য মিলছে না', unresolved:true};
    if (!fontAvailable) return {text:'ফন্ট অনুপস্থিত', label:'চিহ্নের ফন্ট লোড হয়নি; আবার পৃষ্ঠা লোড করুন', unresolved:true};
    return {text:glyph.text, label:display.labelBn || glyph.labelBn || original.legend_bengali || 'মূলের চিহ্ন', glyph, custom:true};
  }
  if (original.printed) return {text:original.printed,label:original.legend_bengali || original.shape_description || 'চিহ্ন'};
  return {text:'অস্পষ্ট',label:'চিহ্নের পরিচয় এখনো যাচাই হয়নি',unresolved:true};
}
export function symbolNode(annotation, original, className = '') {
  const value = symbolDescriptor(annotation, original);
  const node = document.createElement('span');
  node.className = className;
  node.textContent = value.text;
  node.dir = 'ltr';
  node.lang = value.custom ? 'und' : 'bn';
  node.setAttribute('aria-label', value.label);
  node.title = value.label;
  if (value.custom) {
    node.classList.add('source-symbol');
    node.dataset.symbolId = value.glyph.id;
    node.dataset.intrinsicEnclosure = String(!!value.glyph.intrinsicRing);
  }
  if (value.unresolved) node.classList.add('source-uncertain');
  return node;
}
