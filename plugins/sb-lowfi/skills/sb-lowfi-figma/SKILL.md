---
name: sb-lowfi-figma
description: sb-lowfi-pptx로 만든 low-fi 와이어프레임 HTML을 Figma 화면설계서로 옮깁니다. PC 시나리오 페이지와 Mobile 시나리오 페이지를 나누고(관리자 같은 PC 전용 화면은 PC 시나리오에만), 화면마다 Section 하나에 메타 표 + 1:1 고정 크기 와이어프레임 + "화면 설명" 열 + "상태·규칙·부연 설명" 열을 두며, 페이지 상단 화면 흐름도(화면 링크)와 레인별 화살표로 흐름을 보여 줍니다. 사용 트리거 - "low-fi를 figma로", "화면설계서 피그마로", "와이어프레임 figma", "figma 화면설계서", "html to figma 화면설계서".
type: skill
---

# SB Low-fi Figma (low-fi HTML → Figma 화면설계서)

`sb-lowfi-pptx`의 low-fi HTML(마커 `data-n` 포함)을 그대로 Figma 네이티브 도형·텍스트·컴포넌트 인스턴스로 옮깁니다. PPTX와 달리 Figma는 캔버스가 넓으므로 화면을 자르지 않고 1:1 크기로 둡니다.

## 산출물 형식

| 영역 | 규칙 |
|------|------|
| 페이지 | `표지·화면 목록` / `PC 시나리오` / `Mobile 시나리오` / `컴포넌트`(마커 컴포넌트 + 렌더러 소스). PC면 PC 프레임만, Mobile이면 Mobile 프레임만. PC 전용 화면(관리자 등)은 PC 시나리오에만 |
| 레인 | 시나리오 페이지 안에서 사용자 그룹별 세로 열(예: 사용자 / 관리자). 같은 레인 안의 화면은 `flows.json`의 `order` 순서로 위에서 아래로 쌓이고, 연속된 화면 사이에 아래 방향 화살표 |
| 화면 Section | 이름 `[레인] SCR-NNN 화면명`. 같은 이름이 있으면 지우고 같은 자리에 다시 만든다(재실행 안전) |
| 메타 표 | Screen ID, 화면명, Platform, Screen Path, 접근 권한, 관련 기능, 관련 API, Date / Version. 화면설계서.md 메타 원문 그대로(축약 금지). 표 폭 = 섹션 내용 폭 |
| 와이어프레임 | 1:1 고정 크기(PC 1000px, Mobile 375px). 프레임마다 위에 캡션. 한 화면의 여러 상태 프레임은 가로로 나란히 |
| 화면 설명 열 (460px) | 그 화면에 실제로 찍힌 마커 번호의 구성 요소만. 마커 인스턴스 + 굵은 이름 + 설명 |
| 상태·규칙·부연 설명 열 (520px) | 상태별 화면(md 표) / 처리 규칙(md 목록) / 부연 설명(프레임 목록, 마커 안내, 원본 표기) |
| 마커 | `컴포넌트` 페이지의 `Marker` 컴포넌트 인스턴스(22px 주황 원, 텍스트 속성 n). 위치는 build_payloads.py가 글자·다른 마커와 겹치지 않는 자리로 미리 계산 |
| 화면 흐름도 | 페이지 맨 위. 레인별 제목 + 체인(화면 박스 → 화면 박스 + 설명). 박스를 누르면 해당 Section으로 이동(하이퍼링크). 이 페이지에 없는 화면은 회색 박스 |

## 준비물

1. low-fi HTML: `sb-lowfi-pptx` 워크플로우 2~4단계로 만든 `화면설계서_lowfi_YYYYMMDD_HHMM.html`
2. geo.json: `<sb-lowfi-pptx 스킬 폴더>/scripts/extract_geo.py <lowfi.html> geo.json` (헤드리스 Chrome으로 좌표 추출, 마커 자동 이식 포함)
3. 화면설계서.md (메타 표·상태별 화면·처리 규칙 원문)
4. flows.json: 레인과 흐름 정의. 형식은 `references/flows_example.json` 참고
   - `pc` / `mo` 각각 `lanes: [{tag, title, order: [SCR...], chains: [{ids: [SCR...], note}]}]`
   - `exclude: ["SCR-002:mo"]` 처럼 특정 화면·플랫폼 조합 제외 가능
   - 사용자가 주지 않았으면 화면설계서.md(화면 목록, 접근 권한, 화면 간 이동)를 보고 초안을 만들어 레인·순서를 확인받은 뒤 쓴다
   - 프로젝트 산출물 폴더에 `화면흐름_figma.json` 같은 이름으로 저장해 두면 재생성 때 그대로 씀
5. Figma 파일: `create_new_file` 또는 사용자가 준 파일. 페이지 4개(표지·화면 목록, PC 시나리오, Mobile 시나리오, 컴포넌트)를 만들고 id를 기록

## 워크플로우

`use_figma`를 호출하기 전에 반드시 `figma-use` 스킬(또는 MCP 리소스)을 로드하고, 호출마다 `skillNames: "resource:figma-use,resource:figma-generate-design"`을 붙인다.

1. **설치 (파일당 1회)**: `make_setup.py`로 setup.js를 만들어 use_figma 코드로 보낸다. 반환된 `markerId`, `rendererId`를 기록한다.
   - 렌더러만 고쳤을 때: `make_setup.py --renderer-only --renderer-id <id>` (마커 인스턴스 유지)
2. **페이로드 생성**: `build_payloads.py`가 화면별 데이터를 22,000자 이하 묶음(`batch_NN_pc.js`, `batch_NN_mo.js`)으로 만들고 `manifest.json`을 쓴다. 흐름도는 시나리오별 마지막 묶음.
3. **전송**: 묶음 파일을 Read로 읽어 내용을 그대로 use_figma `code`에 넣는다(파일 끝에 렌더러 실행 래퍼가 이미 있음). PC 묶음을 모두 보낸 뒤 PC 흐름도, 그다음 Mobile 묶음과 Mobile 흐름도. 흐름도는 화면 Section 위치를 읽어 화살표를 그리므로 반드시 그 시나리오의 화면을 다 보낸 뒤에 보낸다.
   - 작은 묶음 두 개는 `DS` 배열을 합쳐 한 번에 보내도 된다(50,000자 한도).
   - 실패하면 같은 묶음을 다시 보내면 된다(같은 이름 Section은 교체됨).
4. **검수**: `get_screenshot`으로 흐름도 노드와 대표 Section 2~3개를 본다. 마커가 글자를 덮는지, 메타 표와 프레임 사이 빈 공간, 열 넘침을 확인하고 필요하면 build_payloads.py나 renderer.js를 고친 뒤 해당 묶음만 다시 보낸다.
5. **보고**: Figma 파일 URL과 페이지별 화면 수, 회색(해당 페이지에 없는) 화면을 알린다.

## 명령

```bash
# SK = 이 스킬 폴더. 스킬을 불러올 때 표시되는 "Base directory" 경로를 그대로 쓴다
SK=<이 스킬 폴더>
PP=$SK/../sb-lowfi-pptx   # 같은 플러그인의 sb-lowfi-pptx (venv는 make_pptx.sh 첫 실행 때 생김)
# 1. 설치 코드 생성 (컴포넌트 페이지 id)
python3 $SK/scripts/make_setup.py --components-page 1:4 --out <작업폴더>/setup.js
# 2. 좌표 추출 + 페이로드
$PP/.venv/bin/python $PP/scripts/extract_geo.py 화면설계서_lowfi_YYYYMMDD_HHMM.html <작업폴더>/geo.json
python3 $SK/scripts/build_payloads.py --geo <작업폴더>/geo.json --flows 화면흐름_figma.json --out <작업폴더>/fig \
  --pc-page 1:2 --mo-page 1:3 --marker <markerId> --renderer <rendererId> --md 화면설계서.md --date YYYY-MM-DD --version v1.0
```

작업폴더는 세션 스크래치패드를 쓴다. 묶음 JS는 재생성 가능한 중간 산출물이라 프로젝트에 저장하지 않는다.

## 렌더러 호출 규약

묶음 파일 구조:

```js
const DS = [{ op: 'screen', pageId, markerId, laneTag, laneX, startY, gap, secName, meta, frames, desc, states, rules, notes }, ...,
            { op: 'flow', pageId, title, subtitle, lanes, names, flowX, startY }];
const src = (await figma.getNodeByIdAsync('<rendererId>')).characters;
const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor;
const run = new AsyncFunction('D', 'figma', src);
const out = []; for (const D of DS) out.push(await run(D, figma)); return out;
```

- 프레임 items: `['b',x,y,w,h,fill,stroke,sw,dashed,radius,oval]` 박스, `['l',x,y,w,h,color]` 선, `['t',x,y,w,h,text,size,color,bold,align,single,underline,lines]` 글자. marks: `[n, cx, cy]` (섹션 기준 계산 전 프레임 좌표)
- 레인 x 위치는 build_payloads.py가 레인의 최대 섹션 폭 + 400으로 정한다. 섹션은 레인 안에서 기존 섹션 아래 220px 간격으로 붙는다.
- 글꼴: Noto Sans KR (Regular, Medium, Bold). 이모지 금지.

## 주의

| 항목 | 내용 |
|------|------|
| 계정 | Starter/View 좌석은 호출 수 제한이 낮다. 화면 30개 기준 약 25회 호출이 필요하므로 교육용·유료 좌석 권장 |
| 순서 | 레인 안 섹션 순서 = 보낸 순서. 순서를 바꾸려면 해당 레인 섹션을 지우고 order대로 다시 보낸다 |
| 흐름도 재실행 | 기존 `화면 흐름도`와 `흐름 화살표*` 노드를 지우고 다시 그린다 |
| 메타 표 폭 | 렌더러가 표 폭을 먼저 확정한 뒤 높이를 잰다(폭을 나중에 바꾸면 줄바꿈 높이가 틀어져 빈 공간이 생김) |
| PC 시나리오의 모바일 전용 화면 | low-fi HTML에 PC 프레임이 없는 화면은 PC 페이지에 Section이 없고 흐름도에서 회색 박스로 남는다. 필요하면 low-fi HTML에 PC 프레임을 추가한 뒤 다시 생성 |

## 파일 구조

```
sb-lowfi-figma/
├── SKILL.md
├── references/
│   └── flows_example.json   # flows.json 예시 (스터디룸 예약 예시, PC 2레인 / Mobile 1레인)
└── scripts/
    ├── make_setup.py        # 마커 컴포넌트 + 렌더러 소스 설치 코드 생성
    ├── renderer.js          # Figma 안에서 실행되는 렌더러 (op: screen, flow)
    └── build_payloads.py    # geo.json + md + flows.json -> batch_NN_*.js, manifest.json
```
