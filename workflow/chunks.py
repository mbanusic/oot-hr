#!/usr/bin/env python3
"""Split the game's English text into translation chunks with short placeholders, and merge translations back into hr.po.

  chunks.py prepare [--size N]   hr.po -> tr/in/NNN.json  ([{"id", "where", "en"}]) and tr/map.json
  chunks.py merge                tr/out/NNN.json ({"id": "hr"}) -> hr.po msgstr; prints what failed the checks
  chunks.py status               which chunks are done, missing or bad

Each control code of an entry becomes {1}, {2}, … in order; merge puts the codes back and requires every
placeholder exactly once. Identical English texts are translated once.
"""
import json, re, sys
from pathlib import Path
T = Path(__file__).resolve().parent
ROOT = T.parent
sys.argv, args = sys.argv[:1], sys.argv[1:]
exec((ROOT / 'mals_po.py').read_text().split("if __name__")[0])

ARTICLES = {'the', 'a', 'an'}

def entries():
    out, cur = [], {}
    for k, v in po_parse(ROOT / 'hr.po').items(): out.append(k)
    return out

def po_entries():   # [(ctx, msgid, msgstr)] in file order
    text = (ROOT / 'hr.po').read_text(encoding='utf-8')
    res = []
    for blk in text.split('\n\n'):
        d = {}
        for m in re.finditer(r'^(msgctxt|msgid|msgstr) (".*")$', blk, re.M): d[m.group(1)] = po_u(m.group(2))
        if 'msgctxt' in d: res.append((d['msgctxt'], d['msgid'], d['msgstr']))
    return res

def mask(t):
    codes = []
    def rep(m):
        if m.group(0) in ('{{{{', '\\\\'): return m.group(0)
        codes.append(m.group(0)); return '{%d}' % len(codes)
    return TOKEN.sub(rep, t), codes

def unmask(s, codes):
    found = [int(x) for x in re.findall(r'\{(\d+)\}', s)]
    if sorted(found) != list(range(1, len(codes) + 1)): return None, f'placeholders {sorted(found)} != 1..{len(codes)}'
    return re.sub(r'\{(\d+)\}', lambda m: codes[int(m.group(1)) - 1], s), None

def prepare(size=200, chars=9000):
    seen, units = {}, []
    for ctx, en, _ in po_entries():
        masked, codes = mask(en)
        if not re.sub(r'\{\d+\}', '', masked).strip(): continue   # control codes only
        if en in seen: continue
        seen[en] = len(units)
        f, label = ctx.split('|', 1)
        units.append({'id': str(len(units)), 'where': f.replace('.msbt', '') + ' ' + label, 'en': masked, 'src': en, 'codes': codes})
    (T / 'in').mkdir(exist_ok=True); (T / 'out').mkdir(exist_ok=True)
    chunk, n, c = [], 0, 0
    def flush():
        nonlocal chunk, n, c
        if chunk: (T / 'in' / f'{n:03d}.json').write_text(json.dumps(chunk, ensure_ascii=False, indent=1), encoding='utf-8'); n += 1
        chunk, c = [], 0
    for u in units:
        if len(chunk) >= size or c + len(u['en']) > chars: flush()
        chunk.append({k: u[k] for k in ('id', 'where', 'en')}); c += len(u['en'])
    flush()
    (T / 'map.json').write_text(json.dumps({u['id']: {'src': u['src'], 'codes': u['codes']} for u in units}, ensure_ascii=False), encoding='utf-8')
    print(f'{len(units)} unique texts in {n} chunks under {T / "in"}')

def check(write):
    mp = json.loads((T / 'map.json').read_text(encoding='utf-8'))
    tr, bad, missing, wide = {}, [], [], []
    for f in sorted((T / 'in').glob('*.json')):
        ids = [e['id'] for e in json.loads(f.read_text(encoding='utf-8'))]
        o = T / 'out' / f.name
        if not o.exists(): missing.append(f.stem); continue
        try: got = json.loads(o.read_text(encoding='utf-8'))
        except Exception as e: bad.append((f.stem, '*', f'invalid JSON: {e}')); continue
        for i in ids:
            s, src = got.get(i), mp[i]['src']
            if TOKEN.sub('', src).strip().lower() in ARTICLES and isinstance(s, str) and not s.strip(): tr[src] = EMPTY; continue   # Croatian has no articles
            elif not isinstance(s, str) or not s.strip(): bad.append((f.stem, i, 'missing')); continue
            if re.search('[Ѐ-ӿ]', s): bad.append((f.stem, i, 'Cyrillic letter')); continue
            full, err = unmask(s, mp[i]['codes'])
            if err: bad.append((f.stem, i, err)); continue
            w = lambda t: max((len(re.sub(r'\{\d+\}', '', l)) for l in t.split('\n')), default=0)
            if w(s) > max(w(mask(src)[0]) * 1.25, w(mask(src)[0]) + 8): wide.append((f.stem, i, w(mask(src)[0]), w(s)))
            tr[src] = full
    if write:
        text = (ROOT / 'hr.po').read_text(encoding='utf-8')
        out, n = [], 0
        for blk in text.split('\n\n'):
            m = re.search(r'^msgid (".*")$', blk, re.M)
            if m and po_u(m.group(1)) in tr and re.search(r'^msgstr ""$', blk, re.M) and 'msgctxt' in blk:
                blk = re.sub(r'^msgstr ""$', lambda _: 'msgstr ' + po_q(tr[po_u(m.group(1))]), blk, flags=re.M); n += 1
            out.append(blk)
        (ROOT / 'hr.po').write_text('\n\n'.join(out), encoding='utf-8')
        print(f'{n} entries filled in hr.po')
    chunks = len(list((T / 'in').glob('*.json')))
    badchunks = sorted({b[0] for b in bad})
    print(f'chunks: {chunks}, missing {len(missing)} {missing[:20]}, with problems {len(badchunks)} {badchunks[:20]}; translated texts {len(tr)} / {len(mp)}')
    for b in bad[:30]: print('  ', *b)
    print(f'lines much wider than the English: {len(wide)} entries (tr/wide.json)')
    (T / 'redo.json').write_text(json.dumps({'missing': missing, 'bad': bad}, indent=1), encoding='utf-8')
    (T / 'wide.json').write_text(json.dumps(wide, indent=1), encoding='utf-8')

cmd = args[0] if args else 'status'
if cmd == 'prepare': prepare(int(args[2]) if len(args) > 2 and args[1] == '--size' else 200)
elif cmd == 'merge': check(True)
else: check(False)
