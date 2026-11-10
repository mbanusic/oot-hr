#!/usr/bin/env python3
"""Apply the review fixes in tr/fix/*.json to tr/out/*.json.

Each fix must keep every placeholder of the entry exactly once; fixes that do not are reported and skipped.
Run rewrap.py and `chunks.py merge` (on a fresh export of hr.po) afterwards.
"""
import json, re
from pathlib import Path
T = Path(__file__).resolve().parent
mp = json.loads((T / 'map.json').read_text(encoding='utf-8'))
fixes = {}
for f in sorted((T / 'fix').glob('*.json')):
    try: d = json.loads(f.read_text(encoding='utf-8'))
    except Exception as e: print(f'{f.name}: invalid JSON: {e}'); continue
    print(f'{f.name}: {len(d)} fixes'); fixes.update(d)
applied, bad = 0, []
for f in sorted((T / 'out').glob('*.json')):
    got = json.loads(f.read_text(encoding='utf-8')); dirty = False
    for i in got:
        if i not in fixes: continue
        s = fixes[i]; n = len(mp[i]['codes'])
        found = sorted(int(x) for x in re.findall(r'\{(\d+)\}', s))
        if not isinstance(s, str) or not s.strip() or found != list(range(1, n + 1)) or re.search('[Ѐ-ӿ]', s):
            bad.append((i, found, n)); continue
        if got[i] != s: got[i] = s; dirty = True; applied += 1
    if dirty: f.write_text(json.dumps(got, ensure_ascii=False, indent=1), encoding='utf-8')
print(f'{applied} fixes applied; {len(bad)} rejected {bad[:20]}')
