"""Transcription helpers for the scanned edition. The PDF is the only text source.

  python3 qtools.py overview N            page overview with y ticks (300 dpi coordinates)
  python3 qtools.py strip N Y0 Y1 [K]     horizontal strip at full 300 dpi, split into K overlapping parts with x ticks
  python3 qtools.py crop N X0 Y0 X1 Y1 [ZOOM]   zoomed detail crop
  python3 qtools.py ref 2:37-2:44         reference rasm (consonant skeleton) for a checker only; never copy its text
  python3 qtools.py check N               validate a candidate in source/pages and compare its rasm with the reference

Rendered images go to QURAN_CACHE (default: a scratch directory); nothing here is shipped.
"""
import json, os, re, subprocess, sys, unicodedata
from pathlib import Path

PDF = Path(os.environ.get('QURAN_PDF', '/Users/barik/Downloads/oct 1 bin/CamScanner 09-20-2026 01.00.pdf'))
CACHE = Path(os.environ.get('QURAN_CACHE', '/private/tmp/claude-501/-Users-barik-Desktop-muslims-days/a087df49-3801-4c24-a277-d42d460ea54d/scratchpad/pages'))
MORPH = Path(os.environ.get('QURAN_REFERENCE', '/Users/barik/Desktop/Life & Love/PlayStore/Muslim Days/muslim_days/assets/quran/morphology'))
ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'source/pages'
DPI = 300


def page_png(n):
    CACHE.mkdir(parents=True, exist_ok=True)
    out = CACHE / f'p{n:03}.png'
    if not out.exists():
        prefix = CACHE / f'tmp-{n:03}'
        subprocess.run(['pdftoppm', '-f', str(n), '-l', str(n), '-r', str(DPI), '-png', '-singlefile', str(PDF), str(prefix)], check=True)
        Path(str(prefix) + '.png').replace(out)
    return out


def _font(size):
    from PIL import ImageFont
    for f in ['/System/Library/Fonts/Supplemental/Arial.ttf', '/System/Library/Fonts/Helvetica.ttc']:
        if os.path.exists(f):
            return ImageFont.truetype(f, size)
    return ImageFont.load_default()


def overview(n):
    from PIL import Image, ImageDraw
    im = Image.open(page_png(n)).convert('RGB')
    scale = 0.5
    small = im.resize((int(im.width * scale), int(im.height * scale)))
    canvas = Image.new('RGB', (small.width + 70, small.height), 'white')
    canvas.paste(small, (70, 0))
    d = ImageDraw.Draw(canvas)
    f = _font(14)
    for y in range(0, im.height, 100):
        sy = int(y * scale)
        d.line([(55, sy), (70, sy)], fill='red', width=1)
        d.text((2, sy - 7), str(y), fill='red', font=f)
    out = CACHE / f'p{n:03}-overview.png'
    canvas.save(out)
    print(out, f'(source size {im.width}x{im.height}; tick labels are 300 dpi y coordinates)')


def strip(n, y0, y1, k=3):
    from PIL import Image, ImageDraw
    im = Image.open(page_png(n)).convert('RGB')
    y0, y1, k = int(y0), int(y1), int(k)
    width = im.width
    part = width / k
    overlap = 120
    outs = []
    for i in range(k):
        x0 = max(0, int(width - (i + 1) * part - overlap))  # right to left, matching Arabic reading order
        x1 = min(width, int(width - i * part + overlap))
        c = im.crop((x0, y0, x1, y1))
        canvas = Image.new('RGB', (c.width, c.height + 26), 'white')
        canvas.paste(c, (0, 26))
        d = ImageDraw.Draw(canvas)
        f = _font(16)
        for x in range((x0 // 50 + 1) * 50, x1, 50):
            d.line([(x - x0, 18), (x - x0, 26)], fill='red')
            if x % 100 == 0:
                d.text((x - x0 - 14, 0), str(x), fill='red', font=f)
        out = CACHE / f'p{n:03}-y{y0}-{y1}-part{i + 1}of{k}.png'
        canvas.save(out)
        outs.append(str(out))
    print('\n'.join(outs))
    print(f'parts run right-to-left; red ticks are 300 dpi x coordinates; each part overlaps its neighbour by {overlap}px')


def crop(n, x0, y0, x1, y1, zoom=2):
    from PIL import Image
    im = Image.open(page_png(n)).convert('RGB')
    c = im.crop((int(x0), int(y0), int(x1), int(y1)))
    z = float(zoom)
    c = c.resize((int(c.width * z), int(c.height * z)), Image.LANCZOS)
    out = CACHE / f'p{n:03}-x{x0}-{x1}-y{y0}-{y1}-z{zoom}.png'
    c.save(out)
    print(out)


# ---------------- reference skeleton (checker only) ----------------
STRIP_CATS = {'Mn', 'Me', 'Cf'}
FOLD = {'ٱ': 'ا', 'أ': 'ا', 'إ': 'ا', 'آ': 'ا', 'ٲ': 'ا', 'ٳ': 'ا', 'ى': 'ي', 'ی': 'ي', 'ې': 'ي', 'ئ': 'ي', 'ؤ': 'و', 'ۥ': '', 'ۦ': '', 'ـ': '', 'ء': '', 'ۭ': '', 'ٰ': ''}


def rasm(text):
    out = []
    for ch in unicodedata.normalize('NFD', text):
        if unicodedata.category(ch) in STRIP_CATS or ch.isspace():
            continue
        ch = FOLD.get(ch, ch)
        if ch:
            out.append(ch)
    return ''.join(out)


_ref = None


def reference():
    global _ref
    if _ref is None:
        words = {}
        for f in sorted(MORPH.glob('[0-9][0-9][0-9].txt')):
            for line in f.read_text(encoding='utf-8').splitlines():
                if not line.strip():
                    continue
                loc, form = line.split('\t')[:2]
                s, a, w, _ = map(int, loc.split(':'))
                words.setdefault((s, a), {}).setdefault(w, []).append(form)
        _ref = {k: [''.join(v[w]) for w in sorted(v)] for k, v in words.items()}
    return _ref


def parse_range(spec):
    a, _, b = spec.partition('-')
    s1, a1 = map(int, a.split(':'))
    if b:
        s2, a2 = map(int, b.split(':')) if ':' in b else (s1, int(b))
    else:
        s2, a2 = s1, a1
    ref = reference()
    keys = sorted(k for k in ref if (s1, a1) <= k <= (s2, a2))
    return keys


def ref_cmd(spec):
    ref = reference()
    for k in parse_range(spec):
        print(f'{k[0]}:{k[1]}  words={len(ref[k])}  rasm={" ".join(rasm(w) for w in ref[k])}')
    print('Checker only: this is a different (Madani) orthography. Never copy it; transcribe the scan.')


# ---------------- candidate check ----------------
MARKS = {'১', '২', '৩', '৪', '৬', '৭', 'ম', 'শ', 'গ', 'ক'}
SHAPES = {'ringed-wedge', 'solid-down-arrow', 'conditional-three-or-one'}
ALLOWED_AR = set('ءآأؤإئابةتثجحخدذرزسشصضطظعغفقكلمنهوىي') | {chr(c) for c in range(0x064B, 0x0658)} | {'ٰ', 'ۢ', 'ۤ', 'ۦ', 'ۭ', '۟', '۪', '۫', '۬', 'ۨ', 'ۥ', 'ٓ', 'ٔ', 'ٕ'}


def check(n):
    path = SOURCE / f'page-{n:03}.json'
    d = json.loads(path.read_text(encoding='utf-8'))
    errors, warnings = [], []
    if d.get('page') != n:
        errors.append('page number mismatch')
    ayah_words = {}
    ayah_order = []
    for ri, row in enumerate(d.get('rows', [])):
        words = []
        for si, seg in enumerate(row.get('arabic', [])):
            ref = seg.get('ayah')
            if not re.fullmatch(r'\d{1,3}:\d{1,3}', ref or ''):
                errors.append(f'r{ri} s{si}: bad ayah ref {ref!r}')
                continue
            if ref not in ayah_words:
                ayah_words[ref] = []
                ayah_order.append(ref)
            for w in seg.get('words', []):
                bad = sorted({c for c in w if c not in ALLOWED_AR})
                if bad:
                    errors.append(f'r{ri} {ref}: unexpected characters {[f"U+{ord(c):04X}" for c in bad]} in {w}')
                if unicodedata.normalize('NFC', w) != w and False:
                    pass
                words.append(w)
                ayah_words[ref].append(w)
            if seg.get('end_marker') and not re.fullmatch(r'[০-৯]{1,3}', seg['end_marker']):
                errors.append(f'r{ri} {ref}: end_marker must be Bengali digits')
        for mi, m in enumerate(row.get('marks', [])):
            p, shape = m.get('printed'), m.get('shape')
            if shape and shape not in SHAPES:
                errors.append(f'r{ri} mark {mi}: unknown shape {shape}')
            if not shape and p not in MARKS:
                warnings.append(f'r{ri} mark {mi}: printed {p!r} outside the known legend; keep only if the scan shows it')
            t = m.get('target')
            if isinstance(t, int):
                if not 1 <= t <= len(words):
                    errors.append(f'r{ri} mark {mi}: target word {t} not in row (1..{len(words)})')
                off = m.get('offset')
                if not isinstance(off, (int, float)) or not 0 <= off <= 1:
                    errors.append(f'r{ri} mark {mi}: offset must be 0..1 from the word\'s right edge')
            elif not (isinstance(t, str) and re.fullmatch(r'(stop|marker):\d+', t)):
                errors.append(f'r{ri} mark {mi}: target must be a word number or "stop:<segment>"/"marker:<segment>"')
        for b in row.get('bengali', []):
            if not b.get('text'):
                errors.append(f'r{ri}: empty Bengali segment')
    ref = reference()
    report = []
    for i, a in enumerate(ayah_order):
        s, v = map(int, a.split(':'))
        if s == 1:
            report.append(f'{a}: {len(ayah_words[a])} words; Fatiha uses this edition\'s own numbering (basmala unnumbered) — not compared')
            continue
        if (s, v) not in ref:
            errors.append(f'{a}: not an ayah in the reference numbering')
            continue
        mine = rasm(''.join(ayah_words[a]))
        theirs = rasm(''.join(ref[(s, v)]))
        if mine == theirs:
            status = 'match'
        elif i == 0 and theirs.endswith(mine):
            status = 'match (continues from previous page)'
        elif i == len(ayah_order) - 1 and theirs.startswith(mine):
            status = 'match (continues on next page)'
        elif i == 0 and i == len(ayah_order) - 1 and mine in theirs:
            status = 'match (fragment)'
        else:
            import difflib
            sm = difflib.SequenceMatcher(None, theirs, mine, autojunk=False)
            raw = [(tag, theirs[i1:i2], mine[j1:j2]) for tag, i1, i2, j1, j2 in sm.get_opcodes() if tag != 'equal']
            ops = '; '.join(f'{tag} ref={x!r} scan={y!r}' for tag, x, y in raw[:8])
            # Indo-Pak spelling writes some long vowels in full where the Madani reference uses a small/dagger letter.
            if all(tag in ('insert', 'delete') and set(x + y) <= set('اوي') for tag, x, y in raw):
                status = f'spelling variant only ({ops})'
            else:
                status = f'DIFFERENT: {ops}'
                warnings.append(f'{a}: skeleton differs from reference — re-inspect the scan; keep the scan reading if it is really printed that way')
        report.append(f'{a}: {len(ayah_words[a])} words; {status}')
    print('\n'.join(report))
    for e in errors:
        print('ERROR', e)
    for w in warnings:
        print('WARN', w)
    print('OK' if not errors else f'{len(errors)} errors')
    return not errors


if __name__ == '__main__':
    cmd, *args = sys.argv[1:] or ['help']
    if cmd == 'overview': overview(int(args[0]))
    elif cmd == 'strip': strip(int(args[0]), *args[1:])
    elif cmd == 'crop': crop(int(args[0]), *args[1:])
    elif cmd == 'ref': ref_cmd(args[0])
    elif cmd == 'check': sys.exit(0 if check(int(args[0])) else 1)
    else: print(__doc__)
