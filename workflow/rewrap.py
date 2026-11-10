#!/usr/bin/env python3
"""Re-break the lines of the Croatian translations so they fit the game's text boxes.

  rewrap.py            rewrite tr/out/*.json in place; print what still does not fit (tr/overflow.json)
  rewrap.py --dry      only report

The width limit of an entry is the widest English line in it, at least MIN_W. Each box (the text between
two {{0.4}} page breaks) is re-broken only when one of its lines is over the limit; it then gets the fewest
lines that fit, balanced so they have similar widths. Boxes that need more lines than English allows
(MAX_LINES for dialogue) are listed in tr/overflow.json for shortening.
"""
import json, re, sys
from pathlib import Path
T = Path(__file__).resolve().parent
MIN_W = 52           # dialogue lines up to this width are fine even when the English line is shorter
VALUE_W = 6          # width counted for an inserted value (number, name)
PAGE = '{{0.4}}'
MAX_LINES = {'EventFlowMsg': 3, 'StaticMsg': 3, 'ActorMsg': 4, 'ChallengeMsg': 99}   # ChallengeMsg: the story log scrolls

mp = json.loads((T / 'map.json').read_text(encoding='utf-8'))

def width(s, codes):
    w = 0
    for part in re.split(r'(\{\d+\})', s):
        m = re.fullmatch(r'\{(\d+)\}', part)
        if m: w += VALUE_W if codes[int(m.group(1)) - 1].startswith('{{2.') else 0
        else: w += len(part)
    return w

def boxes(s, codes):
    """Split at page breaks, keeping the break placeholder at the end of its box."""
    out, cur = [], ''
    for part in re.split(r'(\{\d+\})', s):
        cur += part
        m = re.fullmatch(r'\{(\d+)\}', part)
        if m and codes[int(m.group(1)) - 1] == PAGE: out.append(cur); cur = ''
    out.append(cur)
    return out

def wrap(words, codes, limit):
    """Greedy wrap at `limit`; returns the lines."""
    lines, cur = [], ''
    for w in words:
        cand = w if not cur else cur + ' ' + w
        if cur and width(cand, codes) > limit: lines.append(cur); cur = w
        else: cur = cand
    lines.append(cur)
    return lines

def rebreak(box, codes, limit):
    if '\n\n' in box: return '\n\n'.join(rebreak(p, codes, limit) for p in box.split('\n\n'))
    words = box.replace('\n', ' ').split(' ')
    words = [w for w in words if w != ''] if box.strip() else words
    lead = re.match(r'^\s*', box.replace('\n', ' ')).group(0)
    n = len(wrap(words, codes, limit))
    lo, hi = 1, limit                # smallest width that still gives n lines -> balanced lines
    while lo < hi:
        mid = (lo + hi) // 2
        if len(wrap(words, codes, mid)) <= n: hi = mid
        else: lo = mid + 1
    return lead + '\n'.join(wrap(words, codes, lo))

def main(dry):
    where = {}
    for f in sorted((T / 'in').glob('*.json')):
        for e in json.loads(f.read_text(encoding='utf-8')): where[e['id']] = e['where']
    changed, overflow = 0, []
    for f in sorted((T / 'out').glob('*.json')):
        got = json.loads(f.read_text(encoding='utf-8')); dirty = False
        for i, hr in got.items():
            cat = where[i].split('/')[0]
            if cat not in MAX_LINES: continue
            codes, src = mp[i]['codes'], mp[i]['src']
            # widest English line, measured on the source text without codes
            en_plain = re.sub(r'\{\{[^}]*\}\}', lambda m: '\n' if m.group(0) == PAGE else ('x' * VALUE_W if m.group(0).startswith('{{2.') else ''), src)
            en_w = max(len(l) for l in en_plain.split('\n'))
            limit = max(en_w, MIN_W)
            maxl = MAX_LINES[cat] if '\n' in src or cat == 'EventFlowMsg' else 1
            new = []
            for b in boxes(hr, codes):
                if any(width(l, codes) > limit for l in b.split('\n')):
                    b = rebreak(b, codes, limit)
                if b.count('\n') + 1 > maxl: overflow.append({'id': i, 'chunk': f.stem, 'where': where[i], 'limit': limit, 'lines': b.count('\n') + 1, 'max': maxl, 'box': b})
                new.append(b)
            s = ''.join(new)
            if s != hr: got[i] = s; dirty = True; changed += 1
        if dirty and not dry: f.write_text(json.dumps(got, ensure_ascii=False, indent=1), encoding='utf-8')
    (T / 'overflow.json').write_text(json.dumps(overflow, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'{changed} entries re-broken{" (dry run)" if dry else ""}; {len(overflow)} boxes still need more lines than English allows (tr/overflow.json)')

main('--dry' in sys.argv)
