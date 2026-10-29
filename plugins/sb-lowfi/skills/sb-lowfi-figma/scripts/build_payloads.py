"""sb-lowfi-figma: geo.json(+ md + flows.json) -> Figma use_figma 호출용 페이로드(JS) 파일들

사용:
  build_payloads.py --geo geo.json --flows flows.json --out <폴더> --pc-page 1:2 --mo-page 1:3 --marker 1:10 --renderer 1:11
                    [--md 화면설계서.md] [--date YYYY-MM-DD] [--version v1.0]
출력: <폴더>/NN_<kind>_<SCR>.js (화면 하나당 한 호출), <폴더>/ZZ_<kind>_flow.js (흐름도), manifest.json
각 JS는 '컴포넌트' 페이지에 저장된 렌더러(텍스트 노드)를 불러 실행하므로 데이터만 담는다.
"""
import json, re, os, math, argparse, datetime

ap = argparse.ArgumentParser()
ap.add_argument('--geo', required=True); ap.add_argument('--flows', required=True); ap.add_argument('--out', required=True)
ap.add_argument('--pc-page', required=True); ap.add_argument('--mo-page', required=True)
ap.add_argument('--marker', required=True, help='마커 컴포넌트 노드 id'); ap.add_argument('--renderer', required=True, help='렌더러 소스 텍스트 노드 id')
ap.add_argument('--md', default=None); ap.add_argument('--date', default=datetime.date.today().isoformat()); ap.add_argument('--version', default='v1.0')
A = ap.parse_args()
geo = json.load(open(A.geo, encoding='utf-8')); flows = json.load(open(A.flows, encoding='utf-8'))
md = open(A.md, encoding='utf-8').read() if A.md else ''
os.makedirs(A.out, exist_ok=True)
MK = 22                     # Figma 마커 지름(px)
P, GAP_F, COL1, COL2, GAPC = 48, 80, 460, 520, 32
SEC_GAP, LANE_GAP, START_Y = 220, 400, 0

# ---------- md 메타 ----------
meta, blocks_md = {}, (re.split(r'\n(?=### SCR-)', md) if md else [])
for blk in blocks_md:
    m = re.match(r'### (SCR-\d{3})\. (.+)', blk)
    if not m: continue
    d = {'name': m.group(2).strip()}
    for k in ['URL', '플랫폼', '접근 권한', '관련 기능', '관련 API']:
        r = re.search(r'^\| %s \| (.+?) \|\s*$' % re.escape(k), blk, re.M); d[k] = r.group(1).strip() if r else '-'
    d['blk'] = blk; meta[m.group(1)] = d
prio = {m.group(1): m.group(2) for m in re.finditer(r'^\| (SCR-\d{3}) \|.*?\| (P\d) \|', md, re.M)}
for s in geo:
    S = s['sid'].upper()
    if S not in meta:
        parts = [p.strip() for p in s.get('meta', '').split('·')]
        meta[S] = {'name': re.sub(r'^SCR-\d+\s*', '', s['h2']), 'URL': parts[0] if parts else '-', '플랫폼': parts[1] if len(parts) > 1 else '-',
                   '접근 권한': parts[2] if len(parts) > 2 else '-', '관련 기능': parts[3] if len(parts) > 3 else '-', '관련 API': ' · '.join(parts[4:]) or '-', 'blk': ''}

def md_states(S):
    blk = meta[S].get('blk', '')
    st, rl = [], []
    m = re.search(r'\*\*상태별 화면\*\*\s*\n((?:\|.*\n?)+)', blk)
    if m:
        rows = [[c.strip() for c in l.strip().strip('|').split('|')] for l in m.group(1).strip().split('\n') if not re.match(r'^\|[-\s|]+\|$', l.strip())]
        st = [r for r in rows[1:] if len(r) >= 3]
    r = re.search(r'\*\*처리 규칙\*\*\s*\n((?:\s*[-*] .*\n?)+)', blk)
    if r: rl = [re.sub(r'^\s*[-*] ', '', x).strip() for x in r.group(1).strip().split('\n') if x.strip()]
    return st, rl

# ---------- 변환 유틸 ----------
def hexc(c):
    m = re.findall(r'[\d.]+', c); r, g, b = [float(x) for x in m[:3]]; a = float(m[3]) if len(m) > 3 else 1
    if a < 1: r, g, b = [255 * (1 - a) + v * a for v in (r, g, b)]
    return '#%02x%02x%02x' % (int(r), int(g), int(b))
R1 = lambda v: round(v, 1)
def wch(t): return sum(1.0 if ord(c) > 0x2E80 else 0.56 for c in t)
def rng(s):
    nums = set()
    for a in re.findall(r'\d+(?:\s*[~-]\s*\d+)?', s):
        p = re.split(r'\s*[~-]\s*', a); nums |= set(range(int(p[0]), int(p[1]) + 1)) if len(p) == 2 else {int(p[0])}
    return nums
def overlap(a, b, pad=0):
    return not (a[0] + a[2] <= b[0] - pad or b[0] + b[2] <= a[0] - pad or a[1] + a[3] <= b[1] - pad or b[1] + b[3] <= a[1] - pad)

def place_marks(marks, texts, fw, fh):
    placed, d, g = [], MK, 4
    for m in sorted(marks, key=lambda m: (m['y'], m['x'])):
        ex, ey, ew, eh = m.get('ex', m['x'] + 8), m.get('ey', m['y'] + 8), m.get('ew', 20), m.get('eh', 20)
        orig = (m['x'] + m['w'] / 2, m['y'] + m['h'] / 2)
        c = [orig, (ex - d / 2 - g, ey + min(eh, d) / 2), (ex - d / 2 - g, ey + eh / 2), (ex + d / 2, ey - d / 2 - g),
             (ex + ew + d / 2 + g, ey + min(eh, d) / 2), (ex + ew - d / 2, ey - d / 2 - g), (ex + d / 2 + g, ey + d / 2 + g), (ex + ew - d / 2 - g, ey + d / 2 + g)]
        for st in range(1, 7):
            c += [(ex - d / 2 - g - st * (d + g), ey + min(eh, d) / 2), (ex + d / 2 + st * (d + g), ey - d / 2 - g)]
        n = max(1, int(ew / (d / 2)))
        for i in range(n + 1):
            cx = ex + d / 2 + i * (ew - d) / n
            c += [(cx, cy) for cy in (ey + eh / 2, ey + d / 2 + g, ey + eh - d / 2 - g, ey - d / 2 - g, ey + eh + d / 2 + g)]
        best = None
        for cx, cy in c:
            r = (cx - d / 2, cy - d / 2, d, d)
            if r[0] < -26 or r[0] + d > fw + 26 or r[1] < -26 or r[1] + d > fh + 10: continue
            if any(overlap(r, t, 2) for t in texts): continue
            if any(overlap(r, (px - d / 2, py - d / 2, d, d), g) for _, px, py in placed): continue
            best = (cx, cy); break
        placed.append((m['n'], *(best or orig)))
    return [[n, R1(x), R1(y)] for n, x, y in placed]

def conv_frame(f):
    items, texts, marks = [], [], []
    for it in f['items']:
        t = it['t']
        if t == 'box':
            if abs(it['x']) < 1 and abs(it['y']) < 1 and abs(it['w'] - f['w']) < 2 and abs(it['h'] - f['h']) < 2: continue   # 프레임 자체
            bw = it['bw']; allsame = len(set(bw)) == 1 and bw[0] > 0
            rad = it['rad']; mn = min(it['w'], it['h'])
            if it['pct']: rad = mn * rad / 100
            oval = 1 if (rad >= mn / 2 - 0.5 and rad > 0 and abs(it['w'] - it['h']) < 2) else 0
            if it['bg'] or allsame:
                items.append(['b', R1(it['x']), R1(it['y']), R1(it['w']), R1(it['h']), hexc(it['bg']) if it['bg'] else 0,
                              hexc(it['bc'][0]) if allsame else 0, R1(bw[0]) if allsame else 0, 1 if (allsame and it['bs'] == 'dashed') else 0, R1(min(rad, mn / 2)), oval])
            if not allsame:
                for i, b in enumerate(bw):
                    if b <= 0: continue
                    x, y, w, h = it['x'], it['y'], it['w'], it['h']
                    seg = [(x, y, w, b), (x + w - b, y, b, h), (x, y + h - b, w, b), (x, y, b, h)][i]
                    items.append(['l', *[R1(v) for v in seg], hexc(it['bc'][i])])
        elif t == 'text':
            single = 1 if (it['lines'] <= 1 or it['h'] < it['size'] * 1.9) else 0
            al = it['align'] if it['align'] in ('center', 'right') else 'left'
            items.append(['t', R1(it['x']), R1(it['y']), R1(it['w']), R1(it['h']), it['text'], R1(it['size']), hexc(it['color']), 1 if it['bold'] else 0, al, single, 1 if it['ul'] else 0, it['lines']])
            tw = max(it['w'] * 1.06, wch(it['text']) * it['size'] * 0.98 if single else 0)
            tx = it['x'] - (tw - it['w']) / 2 if al == 'center' else (it['x'] - (tw - it['w']) if al == 'right' else it['x'])
            texts.append((tx, it['y'], tw, it['h']))
        elif t == 'mark':
            marks.append(it)
    return items, place_marks(marks, texts, f['w'], f['h'])

# ---------- 레이아웃 계산 ----------
excl = set(flows.get('exclude', []))
by_sid = {s['sid'].upper(): s for s in geo}
def frames_of(S, kind):
    if f'{S}:{kind}' in excl or S not in by_sid: return []
    return [f for f in by_sid[S]['frames'] if f['kind'] == kind]
def sec_width(fr): return P + sum(f['w'] + GAP_F for f in fr) + COL1 + GAPC + COL2 + P

manifest = []
seq = 0
for kind, page in (('pc', A.pc_page), ('mo', A.mo_page)):
    cfg = flows[kind]; lane_x = 0; lanes_out = []
    for lane in cfg['lanes']:
        ws = [sec_width(frames_of(S, kind)) for S in lane['order'] if frames_of(S, kind)]
        if not ws: continue
        for S in lane['order']:
            fr = frames_of(S, kind)
            if not fr: continue
            scr = by_sid[S]; m = meta[S]
            frames = []; shown = set()
            for f in fr:
                items, mk = conv_frame(f); frames.append({'cap': f['cap'] or ('PC' if kind == 'pc' else 'Mobile'), 'w': R1(f['w']), 'h': R1(f['h']), 'kind': kind, 'items': items, 'marks': mk})
                shown |= {int(x[0]) for x in mk}
            desc = [[r[0], re.sub(r'\s+', ' ', r[1]), re.sub(r'\s+', ' ', r[2] if len(r) > 2 else '')] for r in scr['spec'] if rng(r[0]) & shown]
            st, rl = md_states(S)
            if not st:
                for t in scr['stbls']:
                    if t['rows']: st = [r for r in t['rows'][1:] if len(r) >= 3]
            if not rl:
                for t in scr['stbls']:
                    if t['items']: rl = t['items']
            caps = [f['cap'] for f in frames]
            notes = [f'이 시나리오의 프레임 {len(caps)}개: ' + ' / '.join(caps),
                     '번호 마커(주황 원)는 왼쪽 "화면 설명"의 번호와 같습니다. 상태 화면에서 번호가 없는 요소는 기본 화면의 같은 요소와 같습니다.',
                     f'원본: 화면설계서 {S} ({A.version}, {A.date})']
            view = 'PC 시나리오' if kind == 'pc' else 'Mobile 시나리오'
            D = {'op': 'screen', 'pageId': page, 'markerId': A.marker, 'laneTag': lane['tag'], 'laneX': lane_x, 'startY': START_Y, 'gap': SEC_GAP,
                 'secName': f"{lane['tag']} {S} {m['name']}",
                 'meta': [['Screen ID', S], ['화면명', m['name']], ['Platform', f"{m['플랫폼']} / {prio.get(S, 'P0')}  ({view})"], ['Screen Path', m['URL']],
                          ['접근 권한', m['접근 권한']], ['관련 기능', m['관련 기능']], ['관련 API', m['관련 API']], ['Date / Version', f'{A.date} / {A.version}']],
                 'frames': frames, 'desc': desc, 'states': st, 'rules': rl, 'notes': notes}
            seq += 1
            fn = os.path.join(A.out, f'{seq:02d}_{kind}_{S}.js')
            body = 'const D = ' + json.dumps(D, ensure_ascii=False, separators=(',', ':')) + ';\n'
            open(fn, 'w', encoding='utf-8').write(body)
            manifest.append({'file': fn, 'kind': kind, 'sid': S, 'chars': len(body)})
        lanes_out.append({'tag': lane['tag'], 'title': lane['title'], 'order': lane['order'], 'chains': lane['chains']})
        lane_x += max(ws) + LANE_GAP
    names = {S: meta[S]['name'] for S in meta}
    D = {'op': 'flow', 'pageId': page, 'title': cfg['title'], 'subtitle': cfg['subtitle'], 'lanes': lanes_out, 'names': names, 'flowX': 0, 'startY': START_Y}
    fn = os.path.join(A.out, f'ZZ_{kind}_flow.js')
    body = 'const D = ' + json.dumps(D, ensure_ascii=False, separators=(',', ':')) + ';\n'
    open(fn, 'w', encoding='utf-8').write(body); manifest.append({'file': fn, 'kind': kind, 'sid': 'flow', 'chars': len(body)})

# 호출 묶음: 같은 페이지의 화면을 45k자 이하로 묶고, 렌더러 소스를 텍스트 노드에서 읽어 순서대로 실행
WRAP = ("const src = (await figma.getNodeByIdAsync('%s')).characters;\n"
        "const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor;\n"
        "const run = new AsyncFunction('D', 'figma', src);\n"
        "const out = [];\nfor (const D of DS) out.push(await run(D, figma));\nreturn out;\n") % A.renderer
batches, cur, size = [], [], 0
for m in manifest:
    body = open(m['file'], encoding='utf-8').read()[len('const D = '):].rstrip().rstrip(';')
    os.remove(m['file'])
    if cur and (size + len(body) > 22000 or cur[-1]['kind'] != m['kind'] or m['sid'] == 'flow'):
        batches.append(cur); cur, size = [], 0
    cur.append(dict(m, body=body)); size += len(body)
if cur: batches.append(cur)
out = []
for i, b in enumerate(batches, 1):
    code = 'const DS = [' + ',\n'.join(x['body'] for x in b) + '];\n' + WRAP
    fn = os.path.join(A.out, f'batch_{i:02d}_{b[0]["kind"]}.js')
    open(fn, 'w', encoding='utf-8').write(code)
    out.append({'file': fn, 'kind': b[0]['kind'], 'screens': [x['sid'] for x in b], 'chars': len(code)})
json.dump(out, open(os.path.join(A.out, 'manifest.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(len(out), 'batches; max chars', max(x['chars'] for x in out))
for x in out: print(os.path.basename(x['file']), x['chars'], x['screens'])
