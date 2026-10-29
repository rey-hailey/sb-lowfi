"""low-fi HTML을 헤드리스 Chrome으로 렌더링해 프레임별 도형·텍스트·마커 좌표(geo.json)를 뽑는다
사용: extract_geo.py <lowfi.html> <geo.json>
"""
import sys, os, re, json, html, subprocess, tempfile, shutil
here = os.path.dirname(os.path.abspath(__file__))
src, out = sys.argv[1], sys.argv[2]


def _find_chrome():
    cands = [os.environ.get('CHROME'),
             '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
             '/Applications/Chromium.app/Contents/MacOS/Chromium',
             shutil.which('google-chrome'), shutil.which('google-chrome-stable'),
             shutil.which('chromium'), shutil.which('chromium-browser'), shutil.which('chrome')]
    for c in cands:
        if c and os.path.exists(c):
            return c
    sys.exit('Chrome/Chromium을 찾지 못했습니다. CHROME 환경변수로 실행 파일 경로를 지정하세요.')


CHROME = _find_chrome()
js = open(os.path.join(here, 'extract.js'), encoding='utf-8').read()
h = open(src, encoding='utf-8').read()
# sb-creator-pptx 등 다른 주입 스크립트가 있어도 무방. 추출 스크립트만 load 뒤에 실행
h = h.replace('</body>', '<script>window.addEventListener("load",function(){' + js + '});</script></body>')
d = tempfile.mkdtemp()
view = os.path.join(d, 'view.html'); open(view, 'w', encoding='utf-8').write(h)
r = subprocess.run([CHROME, '--headless=new', '--disable-gpu', '--window-size=1300,2000', '--virtual-time-budget=8000', '--dump-dom', 'file://' + view], capture_output=True, text=True, timeout=180)
m = re.search(r'<pre id="__out">(.*?)</pre>', r.stdout, re.S)
if not m: sys.exit('추출 실패: Chrome 출력에서 결과를 찾지 못함')
data = json.loads(html.unescape(m.group(1)))
json.dump(data, open(out, 'w', encoding='utf-8'), ensure_ascii=False)
pc = sum(1 for s in data for f in s['frames'] if f['kind'] == 'pc'); mo = sum(1 for s in data for f in s['frames'] if f['kind'] == 'mo')
print(f'{len(data)} screens, frames pc={pc} mo={mo} -> {out}')
