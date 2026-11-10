#!/usr/bin/env python3
"""Ocarina of Time (Switch 2) message text <-> gettext .po, for a fan translation delivered as a RomFS overlay (DM_ROMFS_OVERLAY).

  export <game RomFS dir or orig dir> <lang> <out.po> [--ref LANG] [--tr hr.json]
      Mals/<lang>.Product.*.sarc.zs -> one .po: msgctxt "<file>|<label>", msgid the source text, msgstr empty
      (--ref LANG adds that language's text as a translator comment, e.g. EUde or EUpl;
      --tr fills msgstr from a translation file, so it can be edited in a .po editor such as Poedit).
  tojson <in.po> <out.json>
      Saves the translated entries of a .po as a translation file ({"<file>|<label>": text}, no source text).
  build <orig dir> <base lang> <hr.json or in.po> <overlay dir> [--as LANG ...]
      Rebuilds the base language's archive with every non-empty msgstr put in, and writes it into the overlay
      as Mals/<LANG>.Product.*.sarc.zs for each --as (default: the base language). Untranslated entries keep the base text.
  selftest <orig dir> <lang>
      Unpacks and repacks the archive and checks the result is byte-identical.

<orig dir> holds Pack/ZsDic.pack.zs and Mals/ as in the game's RomFS. Control codes in the text are written as
{{g.t:hex}} (tag with parameters), {{g.t}} (tag without), {{/g.t}} (closing tag): keep them as they are, move
them with the words they belong to. A msgstr of {{empty}} makes the text empty (English articles, which Croatian does not have). Needs Python 3.14 (compression.zstd), or 3.13 with backports.zstd.
"""
import argparse, re, struct, sys
from pathlib import Path
try: from compression import zstd   # Python 3.14
except ImportError: from backports import zstd   # 3.13 with backports.zstd, as NX2Apple bundles it

# ---------- SARC ----------
def sarc_read(b):
    assert b[:4] == b'SARC', 'not a SARC'
    hl, bom = struct.unpack_from('<HH', b, 4)
    assert bom == 0xFEFF, 'big-endian SARC'
    data_off = struct.unpack_from('<I', b, 0xC)[0]
    sh, n, mult = struct.unpack_from('<HHI', b, hl + 4)
    nodes = [struct.unpack_from('<IIII', b, hl + 12 + i * 16) for i in range(n)]
    q = hl + 12 + n * 16
    names = q + 8
    files = []
    for h, attr, s, t in nodes:
        name = b[names + (attr & 0xFFFF) * 4:].split(b'\0', 1)[0].decode()
        files.append((name, b[data_off + s:data_off + t]))
    return files, mult, data_off

def sarc_hash(name, mult):
    h = 0
    for c in name.encode(): h = (h * mult + (c if c < 128 else c - 256)) & 0xFFFFFFFF
    return h

def sarc_write(files, mult, align):
    """files: [(name, bytes)]; nodes sorted by hash as the game's packer does; each file aligned to `align`."""
    files = sorted(files, key=lambda f: sarc_hash(f[0], mult))
    pool, attrs = b'', []
    for name, _ in files:
        attrs.append(0x01000000 | len(pool) // 4)
        nb = name.encode() + b'\0'; pool += nb + b'\0' * (-len(nb) % 4)
    head = 0x14 + 0xC + 16 * len(files) + 8 + len(pool)
    data_off = (head + align - 1) // align * align
    data, nodes = b'', []
    for (name, v), a in zip(files, attrs):
        data += b'\0' * (-len(data) % align)
        nodes.append(struct.pack('<IIII', sarc_hash(name, mult), a, len(data), len(data) + len(v)))
        data += v
    out = struct.pack('<4sHHIIHH', b'SARC', 0x14, 0xFEFF, 0, data_off, 0x100, 0)
    out += struct.pack('<4sHHI', b'SFAT', 0xC, len(files), mult) + b''.join(nodes)
    out += struct.pack('<4sHH', b'SFNT', 8, 0) + pool
    out += b'\0' * (data_off - len(out)) + data
    return out[:8] + struct.pack('<I', len(out)) + out[12:]

# ---------- MSBT ----------
def msbt_read(b):
    """-> (encoding byte, [(label, text)], raw sections) with text as a str in the {{…}} notation"""
    assert b[:8] == b'MsgStdBn' and b[8:10] == b'\xff\xfe', 'not a little-endian MSBT'
    enc, nsec = b[0xC], struct.unpack_from('<H', b, 0xE)[0]
    assert enc in (0, 1), f'encoding {enc}'
    cw, fmt, codec = (1, '<B', 'utf-8') if enc == 0 else (2, '<H', 'utf-16-le')
    p, labels, texts, secs = 0x20, {}, [], []
    for _ in range(nsec):
        m, sz = b[p:p + 4], struct.unpack_from('<I', b, p + 4)[0]
        body = b[p + 16:p + 16 + sz]; secs.append((m, body))
        if m == b'LBL1':
            nslot = struct.unpack_from('<I', body)[0]
            for i in range(nslot):
                cnt, off = struct.unpack_from('<II', body, 4 + i * 8)
                for _ in range(cnt):
                    ln = body[off]; name = body[off + 1:off + 1 + ln].decode(); idx = struct.unpack_from('<I', body, off + 1 + ln)[0]
                    labels[idx] = name; off += 5 + ln
        elif m == b'TXT2':
            c = struct.unpack_from('<I', body)[0]; offs = struct.unpack_from(f'<{c}I', body, 4)
            for i, o in enumerate(offs):
                s = body[o:offs[i + 1] if i + 1 < c else sz]; q, out, run = 0, [], bytearray()
                def flush():
                    if run: out.append(run.decode(codec).replace('{{', '{{{{').replace('\\', '\\\\')); run.clear()
                while q < len(s):
                    ch = struct.unpack_from(fmt, s, q)[0]
                    if ch == 0xE:
                        flush(); g, t, l = struct.unpack_from('<HHH', s, q + cw)
                        prm = s[q + cw + 6:q + cw + 6 + l]
                        out.append(f'{{{{{g}.{t}:{prm.hex()}}}}}' if l else f'{{{{{g}.{t}}}}}'); q += cw + 6 + l
                    elif ch == 0xF:
                        flush(); g, t = struct.unpack_from('<HH', s, q + cw); out.append(f'{{{{/{g}.{t}}}}}'); q += cw + 4
                    elif ch == 0 and q + cw == len(s): q += cw   # the terminator
                    else: run += s[q:q + cw]; q += cw
                flush(); texts.append(''.join(out))
        p += 16 + sz; p = (p + 15) & ~15
    assert len(labels) == len(texts), 'labels and texts differ in number'
    return b, enc, [(labels[i], texts[i]) for i in range(len(texts))]

EMPTY = '{{empty}}'   # a msgstr that stands for an empty text (an empty msgstr means untranslated)
TOKEN = re.compile(r'\{\{\{\{|\\\\|\{\{(/?)(\d+)\.(\d+)(?::([0-9a-fA-F]*))?\}\}')
def encode_text(text, enc):
    codec, w = ('utf-8', 1) if enc == 0 else ('utf-16-le', 2)
    ch = lambda v: v.to_bytes(w, 'little')
    out, p = bytearray(), 0
    for m in TOKEN.finditer(text):
        out += text[p:m.start()].encode(codec); p = m.end()
        if m.group(0) == '{{{{': out += '{{'.encode(codec); continue
        if m.group(0) == '\\\\': out += '\\'.encode(codec); continue
        g, t = int(m.group(2)), int(m.group(3))
        if m.group(1): out += ch(0xF) + struct.pack('<HH', g, t)
        else:
            prm = bytes.fromhex(m.group(4) or ''); out += ch(0xE) + struct.pack('<HHH', g, t, len(prm)) + prm
    out += text[p:].encode(codec) + ch(0)
    return bytes(out)

def msbt_replace_texts(b, enc, new_texts):
    """Rebuilds the TXT2 section with new texts; every other section is kept as it is"""
    nsec = struct.unpack_from('<H', b, 0xE)[0]; p, out = 0x20, bytearray(b[:0x20])
    for _ in range(nsec):
        m, sz = b[p:p + 4], struct.unpack_from('<I', b, p + 4)[0]
        body = b[p + 16:p + 16 + sz]
        if m == b'TXT2':
            enc_t = [encode_text(t, enc) for t in new_texts]
            off, offs = 4 + 4 * len(enc_t), []
            for e in enc_t: offs.append(off); off += len(e)
            body = struct.pack(f'<I{len(offs)}I', len(offs), *offs) + b''.join(enc_t)
        out += m + struct.pack('<I', len(body)) + b[p + 8:p + 16] + body
        out += b'\xab' * (-len(out) % 16)
        p += 16 + sz; p = (p + 15) & ~15
    struct.pack_into('<I', out, 0x12, len(out))
    return bytes(out)

# ---------- archives ----------
def zsdic(orig):
    files, _, _ = sarc_read(zstd.decompress((orig / 'Pack/ZsDic.pack.zs').read_bytes()))
    return zstd.ZstdDict(dict(files)['zs.zsdic'])

def archive(orig, lang):
    found = sorted((orig / 'Mals').glob(f'{lang}.Product.*.sarc.zs'))
    if not found: sys.exit(f'no Mals/{lang}.Product.*.sarc.zs under {orig}')
    return found[-1]

def load(orig, lang, d):
    path = archive(orig, lang)
    raw = zstd.decompress(path.read_bytes(), zstd_dict=d)
    files, mult, data_off = sarc_read(raw)
    return path, raw, files, mult

def file_align(raw, files):   # the largest power of two every file offset in the original is a multiple of
    data_off = struct.unpack_from('<I', raw, 0xC)[0]
    hl = 0x14; n = struct.unpack_from('<H', raw, hl + 6)[0]
    starts = [data_off + struct.unpack_from('<I', raw, hl + 12 + i * 16 + 8)[0] for i in range(n)]
    a = 1
    while all(s % (a * 2) == 0 for s in starts) and a < 0x10000: a *= 2
    return a

# ---------- .po ----------
def po_q(s): return '"' + s.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\t', '\\t') + '"'
def po_u(s):
    out, i = [], 0
    s = s[1:-1]
    while i < len(s):
        if s[i] == '\\':
            out.append({'n': '\n', 't': '\t', '"': '"', '\\': '\\'}[s[i + 1]]); i += 2
        else: out.append(s[i]); i += 1
    return ''.join(out)

def po_parse(path):
    entries, cur, key = {}, {}, None
    def done():
        if 'msgctxt' in cur: entries[cur['msgctxt']] = cur.get('msgstr', '')
    for line in Path(path).read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            if not line and cur: done(); cur = {}
            continue
        m = re.match(r'(msgctxt|msgid|msgstr)\s+(".*")$', line)
        if m: key = m.group(1); cur[key] = po_u(m.group(2))
        elif line.startswith('"'): cur[key] += po_u(line)
    if cur: done()
    return entries

def load_tr(path):
    """A translation file: .json {"<file>|<label>": text} or a .po; -> only the translated entries."""
    if str(path).endswith('.json'):
        import json
        return {k: v for k, v in json.loads(Path(path).read_text(encoding='utf-8')).items() if v}
    return {k: v for k, v in po_parse(path).items() if v}

def cmd_tojson(a):
    import json
    tr = load_tr(a.po)
    Path(a.out).write_text(json.dumps(dict(sorted(tr.items())), ensure_ascii=False, indent=0) + '\n', encoding='utf-8')
    print(f'{len(tr)} translated entries -> {a.out}')

def cmd_export(a):
    orig = Path(a.orig); d = zsdic(orig)
    tr = load_tr(a.tr) if a.tr else {}
    _, _, files, _ = load(orig, a.lang, d)
    ref = {}
    if a.ref:
        for name, v in load(orig, a.ref, d)[2]:
            for lab, t in msbt_read(v)[2]: ref[f'{name}|{lab}'] = t
    with open(a.out, 'w', encoding='utf-8') as f:
        f.write('msgid ""\nmsgstr ""\n"Content-Type: text/plain; charset=UTF-8\\n"\n"Language: hr\\n"\n\n')
        n = 0
        for name, v in sorted(files):
            for lab, t in msbt_read(v)[2]:
                k = f'{name}|{lab}'
                if k in ref: f.write(f'#. {a.ref}: {ref[k]!r}\n')
                f.write(f'msgctxt {po_q(k)}\nmsgid {po_q(t)}\nmsgstr {po_q(tr.get(k, ""))}\n\n'); n += 1
    print(f'{n} entries from {len(files)} files -> {a.out}')

def check_tags(src, dst, key):
    tags = lambda s: sorted(m.group(0) for m in TOKEN.finditer(s) if m.group(0) not in ('{{{{', '\\\\'))
    if tags(src) != tags(dst): print(f'warning: {key}: control codes differ from the source ({tags(src)} vs {tags(dst)})')

def cmd_build(a):
    orig = Path(a.orig); d = zsdic(orig)
    path, raw, files, mult = load(orig, a.lang, d)
    tr = load_tr(a.po)
    used, out = 0, []
    for name, v in files:
        b, enc, items = msbt_read(v)
        texts = []
        for lab, t in items:
            k = f'{name}|{lab}'
            if k in tr and tr[k] == EMPTY: texts.append(''); used += 1
            elif k in tr: check_tags(t, tr[k], k); texts.append(tr[k]); used += 1
            else: texts.append(t)
        out.append((name, msbt_replace_texts(b, enc, texts) if any(f'{name}|{lab}' in tr for lab, _ in items) else v))
    new = sarc_write(out, mult, file_align(raw, files))
    comp = zstd.compress(new, level=19, zstd_dict=d)
    unknown = set(tr) - {f'{n}|{l}' for n, v in files for l, _ in msbt_read(v)[2]}
    if unknown: print(f'warning: {len(unknown)} translated keys not in the game, e.g. {sorted(unknown)[:3]}')
    suffix = path.name.split('.', 1)[1]
    for lang in a.as_ or [a.lang]:
        dst = Path(a.overlay) / 'Mals' / f'{lang}.{suffix}'; dst.parent.mkdir(parents=True, exist_ok=True); dst.write_bytes(comp)
        print(f'{used} translated entries -> {dst}')

def cmd_selftest(a):
    orig = Path(a.orig); d = zsdic(orig)
    path, raw, files, mult = load(orig, a.lang, d)
    bad = 0
    for name, v in files:
        b, enc, items = msbt_read(v)
        if msbt_replace_texts(b, enc, [t for _, t in items]) != v: bad += 1; print('msbt differs:', name)
    new = sarc_write(files, mult, file_align(raw, files))
    print(f'{len(files)} files, {bad} msbt differ; SARC identical: {new == raw} (align {file_align(raw, files)})')
    back = sarc_read(zstd.decompress(zstd.compress(new, zstd_dict=d), zstd_dict=d))[0]
    print('recompressed archive reads back:', sorted(back) == sorted(files))
    if bad or new != raw: sys.exit(1)

if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter); sp = ap.add_subparsers(dest='cmd', required=True)
    e = sp.add_parser('export'); e.add_argument('orig'); e.add_argument('lang'); e.add_argument('out'); e.add_argument('--ref'); e.add_argument('--tr')
    j = sp.add_parser('tojson'); j.add_argument('po'); j.add_argument('out')
    b = sp.add_parser('build'); b.add_argument('orig'); b.add_argument('lang'); b.add_argument('po'); b.add_argument('overlay'); b.add_argument('--as', dest='as_', action='append')
    s = sp.add_parser('selftest'); s.add_argument('orig'); s.add_argument('lang')
    a = ap.parse_args(); {'export': cmd_export, 'tojson': cmd_tojson, 'build': cmd_build, 'selftest': cmd_selftest}[a.cmd](a)
