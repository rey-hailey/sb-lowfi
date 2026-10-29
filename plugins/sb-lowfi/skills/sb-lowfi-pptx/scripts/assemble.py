"""조각 HTML(frag_*.html, screen-section div 모음)을 하나의 low-fi 화면설계서 HTML로 조립
사용: assemble.py --frags <폴더> --out <화면설계서_lowfi_YYYYMMDD_HHMM.html> [--title 프로젝트명] [--css lowfi.css]
"""
import re, glob, os, argparse
here = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser()
ap.add_argument('--frags', required=True); ap.add_argument('--out', required=True)
ap.add_argument('--title', default='Project'); ap.add_argument('--css', default=os.path.join(here, '..', 'assets', 'lowfi.css'))
ap.add_argument('--version', default='v1.0')
a = ap.parse_args()
css = open(a.css, encoding='utf-8').read()
secs = {}
for f in sorted(glob.glob(os.path.join(a.frags, 'frag_*.html'))):
    t = open(f, encoding='utf-8').read()
    for m in re.finditer(r'<div id="(scr-\d+)" class="screen-section">.*?(?=<div id="scr-\d+" class="screen-section">|\Z)', t, re.S):
        secs[m.group(1)] = m.group(0)
order = sorted(secs)
nav = ''.join(f'<a href="#{k}">{k.upper()}</a>' for k in order)
html = f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{a.title} 화면설계서 Low-fi</title><style>{css}
.top{{flex-wrap:wrap}}.top .nav{{display:flex;gap:10px;flex-wrap:wrap}}</style></head><body>
<div class="top"><b>{a.title} 화면설계서 Low-fi</b><span>{len(order)}개 화면 / {a.version}</span><div class="nav">{nav}</div></div>
{''.join(secs[k] for k in order)}
</body></html>'''
open(a.out, 'w', encoding='utf-8').write(html)
print(len(order), 'screens ->', a.out)
