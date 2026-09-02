# ==== BEGIN migrate_rst.py ==== copy from this line to the END line only
#!/usr/bin/env pypy3
"""
migrate_rst.py -- one-shot migration of the hash-attacks .rst to the new
Markdown format.  Usage: pypy3 migrate_rst.py hashes.rst

DESIGN: the document is an ordered list of segments, each tagged 'src'
(rST text that passes may still rewrite) or 'lit' (finalized Markdown
that no pass may ever touch). Generated output enters as 'lit', so it
can structurally never be re-consumed as input by a later pass.

TRANSIT ARMOR: this file must survive copy-paste through markdown/LaTeX
pipelines. Therefore it contains (a) no backslash-bracket regex escapes
(brackets via the LBe/RBe constants), (b) no literal triple-backtick
sequences (see FENCE), and (c) a self-integrity check that refuses to
run a mangled copy. Do not "simplify" these back.

BACKSLASH GOTCHA (the other one): every re.sub replacement is a lambda
or function, because replacement strings get escape processing.
"""
import re, sys, pathlib

# ---- transit-armor constants ----------------------------------------
LB, RB = chr(0x5B), chr(0x5D)        # '[' and ']'
LBe, RBe = re.escape(LB), re.escape(RB)
BSLASH = chr(92)
FENCE = chr(96) * 3                  # triple backtick
BT = chr(96)                         # single backtick
Q = chr(34)                          # double quote
BADDOLLAR = chr(36) * 2              # two adjacent dollar signs
BADPROT = '__PROT' + 'ECTED'

# ---- self-integrity check: refuse to run if transit mangled us ------
_me = pathlib.Path(__file__).read_text(encoding='utf-8')
assert BADDOLLAR not in _me, 'CORRUPT COPY: double-dollar (latex-mangled)'
assert BADPROT not in _me, 'CORRUPT COPY: contains placeholder tokens'
assert '==== END migrate_rst.py ====' in _me, 'CORRUPT COPY: truncated'

WARN = []
def warn(msg): WARN.append(msg)

NOTE_IDS = {'†': 'dagger', '§': 'sect', '*': 'star', '‡': 'ddagger'}

# ---------------------------------------------------------------- data
# TIMELINE: color transitions per hash, canonical (carries editorial
# judgment: MD2->red 2010 via Bitcoin hashrate; SHA-0->yellow 1994 per
# RFC 6194, ref 54 -- which exists only in the hand-edited bibliography,
# so that link dangles in this script's output by design).
# Transition = (color, year, ref); color in y/o/r; ref '' if none.
# Empty list = green since design year. Do NOT regenerate mechanically.
TL_ROWS = [
    ('MD2',            1989, '128', '638', [('y',1989,'21'),('r',2010,'45')], []),
    ('Snefru-2',       1990, '128', '?',   [('y',1990,'3'),('r',1991,'19')], [('r',1991,'19')]),
    ('MD4',            1990, '128', '4.0', [('y',1990,'22'),('r',1995,'20')], []),
    ('RIPEMD',         1990, '128', '?',   [('y',1990,'23'),('r',2004,'7')], []),
    ('MD5',            1992, '128', '5.1', [('y',1992,'24'),('r',2004,'7')], []),
    ('HAVAL-256-3',    1992, '256', '?',   [('r',2003,'11')], []),
    ('SHA-0',          1993, '160', '?',   [('y',1994,'54'),('r',2005,'27')], []),
    ('GOST',           1994, '256', '?',   [('y',2008,'14')], []),
    ('SHA-1',          1995, '160', '18',  [('r',2005,'15')], []),
    ('RIPEMD-160',     1996, '160', '17',  [('o',2010,'47')], []),
    ('Tiger',          1996, '192', '6.2', [], []),
    ('Panama',         1998, '512', '2.5', [('y',2002,'34'),('r',2007,'35')], []),
    ('Whirlpool',      2000, '512', '50',  [], []),
    ('SHA-256',        2001, '256', '19',  [], []),
    ('RadioGatún',     2006, '256', '?',   [], []),
    ('Skein',          2008, '256', '8.7', [], []),
    ('Blake',          2008, '256', '17',  [], []),
    ('Grøstl',         2008, '256', '24',  [], []),
    ('Keccak (SHA-3)', 2008, '256', '16',  [], []),
    ('JH',             2008, '256', '20',  [], []),
    ('BLAKE2',         2012, '256', '5.7', [], []),
]

TIMELINE_CAPTION = ("*Figures 1 & 2: safety history of each hash function "
    "against collision and (second-)pre-image attacks. Each cell lists "
    "the color transitions from the design year onward (🟢 from design; "
    "🟡 theoretical attack or distrust; 🟠 brute force becoming feasible; "
    "🔴 practically broken). A cell containing only 🟢 means no transition "
    "has ever occurred. The interactive view renders this as a "
    "year-by-year timeline.*\n\n")

FIG0_HEADER = ["digital signature type", "today", "quantum computer",
               "asymmetric crypto breakthrough", "hash collisions",
               "hash preimages"]
FIG3_HEADER = ["hash", "year", "bits", "cpb",
               "coll. safe?", "comp", "mem", "ref",
               "preimg. safe?", "comp", "mem", "ref"]

FOOTER = ('\n<!-- rendering machinery: everything below this line is not '
    'content -->\n<!-- Markdeep: --><script src="markdeep.min.js" '
    'charset="utf-8"></script><script src="viewer.js"></script>\n')

EMOJI = {'r': '🔴', 'y': '🟡', 'g': '🟢', 'o': '🟠'}

# ------------------------------------------------------------- helpers
def parse_grid_body(block):
    """Rows below the +===+ line of an rST grid table. Multi-line cells
    merged with spaces. Assumes no '|' inside cell text (true here)."""
    lines = block.splitlines()
    for i, ln in enumerate(lines):
        if ln.startswith('+='):
            lines = lines[i + 1:]
            break
    rows, cur = [], None
    for ln in lines:
        if ln.startswith('+'):
            if cur: rows.append(cur)
            cur = None
        else:
            cells = [c.strip() for c in ln.strip().strip('|').split('|')]
            if cur is None:
                cur = cells
            else:
                for i, c in enumerate(cells):
                    if i < len(cur): cur[i] = (cur[i] + ' ' + c).strip()
                    else: cur.append(c)
    if cur: rows.append(cur)
    return rows

def md_table(header, rows):
    out = ['| ' + ' | '.join(header) + ' |', '|' + '---|' * len(header)]
    out += ['| ' + ' | '.join(r) + ' |' for r in rows]
    return '\n'.join(out) + '\n'

def tl_cell(transitions):
    if not transitions:
        return EMOJI['g']
    parts = []
    for color, year, ref in transitions:
        t = EMOJI[color] + ' ' + str(year)
        if ref:
            t += ' ' + LB + LB + ref + RB + RB + '(#ref-' + ref + ')'
        parts.append(t)
    return ' → '.join(parts)

TIMELINE = md_table(
    ['hash', 'designed', 'bits', 'cpb', 'collisions',
     '(second-)pre-images'],
    [[h, str(d), b, c, tl_cell(ct), tl_cell(pt)]
     for (h, d, b, c, ct, pt) in TL_ROWS])

ANON_ANCHOR = re.compile(r'\.\. _' + LBe + '(.)' + RBe + r':\s*')

def convert_anon_footnotes(s):
    """Line-based: '.. _(X):' anchor (optional) + '.. (*)' body ->
    anchored blockquote note. Runs BEFORE target grabbing so the
    grabber can never eat the anchors."""
    lines, out = s.split('\n'), []
    fallback = iter(['*', '‡'])
    pending, i = None, 0
    star = '.. ' + LB + '*' + RB
    while i < len(lines):
        m = ANON_ANCHOR.fullmatch(lines[i])
        if m:
            pending = m.group(1); i += 1
            continue
        if lines[i].startswith(star):
            body = [lines[i][len(star):].strip()]; i += 1
            while i < len(lines):
                if not lines[i].strip():
                    j = i
                    while j < len(lines) and not lines[j].strip(): j += 1
                    if j < len(lines) and lines[j].startswith('   '):
                        i = j; continue
                    break
                if lines[i].startswith('   '):
                    body.append(lines[i].strip()); i += 1
                else:
                    break
            lbl = pending or next(fallback)
            if pending is None:
                warn('anonymous footnote assigned label ' + LB + lbl + RB
                     + ' -- verify')
            pending = None
            nid = NOTE_IDS.get(lbl, lbl)
            out.append('> <a id="note-' + nid + '"></a>**Note ' + LB + lbl
                       + RB + ':** ' + ' '.join(body))
            out.append('')
            continue
        out.append(lines[i]); i += 1
    return '\n'.join(out)

def fix_headings(s):
    lines, out, i = s.split('\n'), [], 0
    while i < len(lines):
        ln = lines[i]
        nxt = lines[i + 1] if i + 1 < len(lines) else ''
        if re.fullmatch(r'={3,}', ln) and i + 2 < len(lines) \
                and re.fullmatch(r'={3,}', lines[i + 2]):
            out.append('# ' + lines[i + 1].strip()); i += 3; continue
        if ln.strip() and not ln[0] in ' +|.>' \
                and re.fullmatch(r'={3,}', nxt):
            out.append('## ' + ln.strip()); i += 2; continue
        if ln.strip() and not ln[0] in ' +|.>' \
                and re.fullmatch(r'-{3,}', nxt):
            out.append('### ' + ln.strip()); i += 2; continue
        out.append(ln); i += 1
    return '\n'.join(out)

def bib_item(m):
    body = m.group(2).strip().replace(' .. ', ' ')
    parts = body.split(None, 1)
    if parts and parts[0].startswith('http'):
        body = ('<' + parts[0] + '>'
                + ((' ' + parts[1]) if len(parts) > 1 else ''))
    return ('- <a id=' + Q + 'ref-' + m.group(1) + Q + '></a>' + LB
            + m.group(1) + RB + ' ' + body)

targets = {}
def grab_target(m):
    name = m.group(1).strip().strip(BT)
    rest = m.group(2).strip()
    if rest and ' ' in rest:
        warn('target "' + name + '": trailing description dropped: '
             + repr(rest))
    targets[name] = rest.split()[0] if rest else ''
    return ''

grids = [FIG0_HEADER, FIG3_HEADER]
def grid_repl(m):
    return md_table(grids.pop(0), parse_grid_body(m.group(0)))

leftovers = []
def sweep(m):
    leftovers.append(m.group(0).rstrip('\n'))
    return ''

NOTE_XREF = re.compile(LBe + '(.)' + RBe)
def named_ref(m):
    name = m.group(1)
    mm = NOTE_XREF.fullmatch(name)
    if mm:
        nid = NOTE_IDS.get(mm.group(1), mm.group(1))
        return LB + LB + mm.group(1) + RB + RB + '(#note-' + nid + ')'
    if targets.get(name):
        return LB + name + RB + '(' + targets[name] + ')'
    warn('unresolved reference "' + name + '" left as plain text')
    return name

# ---------------------------------------------- segment machinery
segs = None   # list of ['src'|'lit', text]

def sub_src(pat, repl):
    for seg in segs:
        if seg[0] == 'src':
            seg[1] = re.sub(pat, repl, seg[1])

def map_src(fn):
    for seg in segs:
        if seg[0] == 'src':
            seg[1] = fn(seg[1])

def splice_lit(pat, lit):
    """Replace the first match of pat (in source order) with a finalized
    literal segment that later passes can never touch."""
    for i in range(len(segs)):
        kind, text = segs[i]
        if kind != 'src':
            continue
        m = re.search(pat, text)
        if m:
            segs[i:i + 1] = [['src', text[:m.start()]], ['lit', lit],
                             ['src', text[m.end():]]]
            return
    raise AssertionError('splice pattern matched nothing')

# ---------------------------------------------------------------- main
src = pathlib.Path(sys.argv[1])
segs = [['src', src.read_text(encoding='utf-8-sig')]]

# 0. drop the emacs modeline
sub_src(r'(?m)\A\.\. -\*-.*\n', lambda m: '')

# 1. Figure 1 csv-table -> finalized timeline table; Figure 2 -> gone
splice_lit(r'(?ms)^\.\. csv-table:: Figure 1.*?\n(?=\S)',
           TIMELINE_CAPTION + TIMELINE + '\n')
sub_src(r'(?ms)^\.\. csv-table:: Figure 2.*?\n(?=\S)', lambda m: '')

# 2. anonymous footnotes (BEFORE targets -- see helper docstring)
map_src(convert_anon_footnotes)

# 3. numbered footnotes -> anchored bibliography items
sub_src(r'(?m)^\.\. ' + LBe + r'(\d+)' + RBe + r'\s+(.*)', bib_item)

# 4. collect & remove hyperlink targets; guard refuses bracket names
sub_src(r'(?m)^\.\. _(?!' + LBe + r')(' + BT + r'.+?' + BT
        + r'|.+?):\s*(.*)\n', grab_target)

# 5. drop role definitions
sub_src(r'(?m)^\.\. role:: .*\n', lambda m: '')

# 6. headings
map_src(fix_headings)

# 7. grid tables (Figure 0 then Figure 3). A real rST grid table begins
#    with a '+---' border line, which a Markdown pipe table never has --
#    and the timeline is a lit segment anyway, structurally unreachable.
sub_src(r'(?m)(?:^\+.*\n)(?:^[+|].*\n)+', grid_repl)
assert not grids, 'expected exactly two grid tables'

# 8. definition-list color keys -> bullet lists
sub_src(r'(?m)^:(.):' + BT + r'(.+?)' + BT + r'\n((?:[ ]{3,}.*\n)+)',
        lambda m: '- ' + EMOJI.get(m.group(1), '') + ' **' + m.group(2)
                  + '** — '
                  + ' '.join(x.strip() for x in m.group(3).splitlines())
                  + '\n')

# 9. drop the old raw-html/jQuery block (superseded by viewer.js)
sub_src(r'(?ms)^\.\. raw:: html.*?(?=^\S|\Z)', lambda m: '')

# 10. sweep remaining ".. " comment lines into a preserved appendix
sub_src(r'(?m)^\.\..*\n', sweep)
if leftovers:
    warn(str(len(leftovers)) + ' commented-out rST lines preserved in '
         'appendix at end of file -- review and delete')

# 11. inline conversions
sub_src(BT + LBe + '(.)' + RBe + BT + '_',
        lambda m: LB + LB + m.group(1) + RB + RB + '(#note-'
                  + NOTE_IDS.get(m.group(1), m.group(1)) + ')')
sub_src(BT + r'(.+?)' + BT + r'_', named_ref)
sub_src(r'(?<!\w)(?<!' + BT + r')(\w(?:\w|-|\+)*)_(?!\w)',
        lambda m: LB + m.group(1) + RB + '(' + targets[m.group(1)] + ')'
                  if targets.get(m.group(1)) else m.group(0))
sub_src(LBe + r'(\d+)' + RBe + '_',
        lambda m: LB + LB + m.group(1) + RB + RB
                  + '(#ref-' + m.group(1) + ')')
sub_src(r':(.):' + BT + r'(.*?)' + BT,
        lambda m: (EMOJI.get(m.group(1), '') + ' ' + m.group(2)).strip())
map_src(lambda t: t.replace(BSLASH + '?', '?'))
map_src(lambda t: t.replace(
    'cycles per byte ' + LB + '*' + RB,
    'cycles per byte ' + LB + LB + '*' + RB + RB + '(#note-star)'))

# 12. small fixups: legend syntax (rename BEFORE blank-line insertion),
#     star-list dedent, field list
sub_src(r'(?m)^\*legend:\*:', lambda m: '*Legend:*')
sub_src(r'(?m)^[ ]{3,}\* ', lambda m: '- ')
sub_src(r'(?m)^\*Legend:\*\n(?=- )', lambda m: '*Legend:*\n\n')
sub_src(r'(?m)^:(\w+):\s+(.*)$',
        lambda m: '- **' + m.group(1) + ':** ' + m.group(2))

# ---- all pattern-matching done: collapse to a single string ----------
s = ''.join(text for kind, text in segs)

# 12b. section headings (post-join is safe: index-based, no re-parse)
ref1 = '- <a id=' + Q + 'ref-1' + Q
i = s.find(ref1)
assert i >= 0, 'cannot locate first bibliography item'
s = s[:i] + '## References\n\n' + s[i:]
j = s.find('- **Author:**')
assert j >= 0, 'cannot locate Author field'
s = s[:j] + '## Metadata\n\n' + s[j:]

# 13. tidy blank runs
s = re.sub(r'\n{3,}', lambda m: '\n\n', s).strip() + '\n'

# --- POSTCONDITIONS: fail loudly, leave a corpse for forensics --------
def check(cond, msg):
    if not cond:
        dbg = src.with_suffix('.FAILED.md')
        dbg.write_text(s, encoding='utf-8')
        raise AssertionError(msg + ' -- partial output in ' + str(dbg))

check(not re.search(LBe + r'\d+' + RBe + '_', s), 'unconverted citations')
check(s.count('<a id=' + Q + 'ref-') >= 50, 'bibliography did not convert')
check('| hash | designed | bits | cpb | collisions' in s,
      'timeline table missing')
check(s.count(' → ') >= 7, 'timeline transitions missing')
check('| year | bits | cpb |' in s, 'Figure 3 did not convert')
check(s.count('**Note ' + LB) == 4, 'expected 4 anonymous footnotes')
check('4096-byte' in s and 'median measurement' in s, 'cpb note lost')
check('Bitcoin mining network' in s, 'MD2/Bitcoin note lost')
check('## References' in s, 'References heading missing')
check('## Metadata' in s, 'Metadata heading missing')
check(s.count('<http') >= 45, 'bibliography URLs not angle-bracketed')
check(' .. ' not in s, 'stray rST dots survived')  # appendix added below

if leftovers:
    s += ('\n<!-- appendix: content commented out in the old rST, '
          'preserved verbatim; delete when reviewed -->\n' + FENCE + '\n'
          + '\n'.join(leftovers) + '\n' + FENCE + '\n')
s += FOOTER

dst = src.with_suffix('.md')
dst.write_text(s, encoding='utf-8-sig')   # emit UTF-8 BOM at byte 0
print('wrote ' + str(dst))
print('\nMANUAL REVIEW CHECKLIST:')
for w in WARN:
    print('  -', w)
# ==== END migrate_rst.py ==== copy ends here, nothing below this line
