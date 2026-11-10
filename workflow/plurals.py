#!/usr/bin/env python3
"""Put Croatian plural forms into the {{201.6}} codes of hr.po (run after `chunks.py merge`).

A {{201.6}} parameter is a list of forms, each a u16 byte length and UTF-8 text. English gives
[one, other, ""]; Polish, which like Croatian has three forms, gives [one, many, few] with no end mark.
The game picks the form by the plural rule of its language (en-US here: 1 -> the first, else the second),
so the first two forms carry the Croatian accusative singular and genitive plural, and the third is "few".
"""
import re
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
FORMS = {   # English forms -> Croatian [one, many, few], as used after "za"/"skupio" (accusative)
    ('rupee', 'rupees'): ['rupiju', 'rupija', 'rupije'],
    ('token', 'tokens'): ['žeton', 'žetona', 'žetona'],
    (' token', ' tokens'): [' žeton', ' žetona', ' žetona'],
    ('fence', 'fences'): ['ogradu', 'ograda', 'ograde'],
    (' monster statue', ' monster statues'): [' kip čudovišta', ' kipova čudovišta', ' kipa čudovišta'],
    (' monster', ' monsters'): [' čudovište', ' čudovišta', ' čudovišta'],
}
def parse(h):
    b, out, p = bytes.fromhex(h), [], 0
    while p + 2 <= len(b):
        n = int.from_bytes(b[p:p + 2], 'little'); p += 2
        out.append(b[p:p + n].decode()); p += n
    return out
def enc(forms): return b''.join(len(f.encode()).to_bytes(2, 'little') + f.encode() for f in forms).hex()
p = ROOT / 'hr.po'; text = p.read_text(encoding='utf-8'); n = 0
def rep(blk):
    global n
    if '\nmsgstr ' not in blk or 'msgstr ""' in blk or '{{201.6:' not in blk.split('msgstr', 1)[1]: return blk
    head, tail = blk.split('\nmsgstr ', 1)
    def code(m):
        global n
        f = parse(m.group(1))
        key = (f[0], f[1]) if len(f) >= 2 else None
        if key in FORMS: n += 1; return '{{201.6:' + enc(FORMS[key]) + '}}'
        return m.group(0)
    return head + '\nmsgstr ' + re.sub(r'\{\{201\.6:([0-9a-f]+)\}\}', code, tail)
text = '\n\n'.join(rep(b) for b in text.split('\n\n'))
p.write_text(text, encoding='utf-8'); print(f'{n} plural codes made Croatian')
