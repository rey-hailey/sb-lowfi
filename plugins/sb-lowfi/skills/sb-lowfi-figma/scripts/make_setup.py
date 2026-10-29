"""sb-lowfi-figma: Figma 파일 초기 설치용 use_figma 코드(setup.js) 생성

사용:
  make_setup.py --components-page 1:4 --out setup.js [--renderer renderer.js]
출력 setup.js를 use_figma 코드로 그대로 보낸다. 반환값의 markerId, rendererId를 build_payloads.py 인자로 쓴다.
- '컴포넌트' 페이지에 번호 마커 컴포넌트(Marker, 22px 주황 원, 텍스트 속성 n)를 만든다
- 같은 페이지에 렌더러 소스를 잠긴 텍스트 노드(renderer.js)로 저장한다 (이후 호출은 데이터만 보내면 됨)
- 다시 실행하면 기존 Marker / renderer.js 노드를 지우고 새로 만든다 (기존 화면의 마커 인스턴스는 끊기므로 렌더러만 바꿀 때는 --renderer-only)
"""
import argparse, json, os

ap = argparse.ArgumentParser()
ap.add_argument('--components-page', required=True, help="'컴포넌트' 페이지 노드 id")
ap.add_argument('--out', required=True)
ap.add_argument('--renderer', default=os.path.join(os.path.dirname(__file__), 'renderer.js'))
ap.add_argument('--renderer-id', default=None, help='--renderer-only일 때 교체할 텍스트 노드 id')
ap.add_argument('--renderer-only', action='store_true', help='마커는 두고 렌더러 소스만 교체')
A = ap.parse_args()
src = open(A.renderer, encoding='utf-8').read()

if A.renderer_only:
    if not A.renderer_id: raise SystemExit('--renderer-only에는 --renderer-id가 필요합니다')
    code = f"""const rt = await figma.getNodeByIdAsync({json.dumps(A.renderer_id)});
await figma.loadFontAsync(rt.fontName);
rt.locked = false; rt.characters = {json.dumps(src, ensure_ascii=False)}; rt.locked = true;
return {{ rendererId: rt.id, len: rt.characters.length }};
"""
else:
    code = f"""const page = await figma.getNodeByIdAsync({json.dumps(A.components_page)});
await figma.setCurrentPageAsync(page);
await Promise.all(['Regular', 'Bold'].map(s => figma.loadFontAsync({{ family: 'Noto Sans KR', style: s }})));
for (const n of [...page.children]) if (n.name === 'Marker' || n.name === 'renderer.js') n.remove();
const comp = figma.createComponent(); comp.name = 'Marker'; comp.resize(22, 22);
comp.layoutMode = 'HORIZONTAL'; comp.primaryAxisAlignItems = 'CENTER'; comp.counterAxisAlignItems = 'CENTER';
comp.primaryAxisSizingMode = 'FIXED'; comp.counterAxisSizingMode = 'FIXED';
comp.cornerRadius = 11; comp.fills = [{{ type: 'SOLID', color: {{ r: 0.91, g: 0.349, b: 0.047 }} }}];
const t = figma.createText(); t.fontName = {{ family: 'Noto Sans KR', style: 'Bold' }}; t.characters = '1'; t.fontSize = 12;
t.fills = [{{ type: 'SOLID', color: {{ r: 1, g: 1, b: 1 }} }}]; t.textAlignHorizontal = 'CENTER';
comp.appendChild(t);
const key = comp.addComponentProperty('n', 'TEXT', '1');
t.componentPropertyReferences = {{ characters: key }};
comp.description = '화면설계서 번호 마커. 속성 n에 화면 설명 번호를 넣는다.';
comp.x = 0; comp.y = 0;
const rt = figma.createText(); rt.name = 'renderer.js'; rt.fontName = {{ family: 'Noto Sans KR', style: 'Regular' }};
rt.characters = {json.dumps(src, ensure_ascii=False)};
rt.fontSize = 8; rt.x = 0; rt.y = 80; rt.locked = true;
return {{ markerId: comp.id, rendererId: rt.id, rendererLen: rt.characters.length }};
"""
open(A.out, 'w', encoding='utf-8').write(code)
print(A.out, len(code), 'chars')
