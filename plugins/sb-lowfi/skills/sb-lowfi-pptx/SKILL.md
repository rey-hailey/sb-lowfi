---
name: sb-lowfi-pptx
description: 화면설계서(.md, ASCII 와이어프레임)를 실무형 low-fidelity 와이어프레임으로 만들어 HTML과 편집 가능한 PPTX 화면설계서로 출력합니다. PPTX는 상단 메타 표(Page Title, Screen ID, Date, Screen Path, Platform, 접근 권한, 관련 기능, 관련 API), 좌측 와이어프레임, 우측 Description(구성 요소 + 상태별 화면 + 처리 규칙)을 한 슬라이드에 담고 PC와 Mobile 슬라이드를 분리합니다. 사용 트리거 - "화면설계서 PPTX로", "low-fi 와이어프레임 만들어줘", "와이어프레임 pptx", "화면 기획서 PPT", "스토리보드 PPTX", "개발자 전달용 화면설계서".
type: skill
---

# SB Low-fi PPTX (화면설계서 → low-fi HTML → 실무형 PPTX)

ASCII 와이어프레임만으로는 개발자·디자이너에게 전달하기 어렵기 때문에, 박스·입력칸·버튼을 실제 도형으로 그린 low-fi 와이어프레임을 만들고 현업에서 쓰는 PPTX 화면설계서 형식으로 출력합니다.

## 산출물 형식 (현업 화면 기획서 레퍼런스 기준)

| 영역 | 규칙 |
|------|------|
| 순서 | 표지 → 화면 목록(PC·Mobile 페이지) → **[PC 화면] PC 시나리오 전체** → **[Mobile 화면] Mobile 시나리오 전체** |
| 상단 메타 표 | Page Title / Screen ID / Date, Screen Path / Platform, 접근 권한, 관련 기능, 관련 API (화면설계서.md 메타 표 원문 그대로, 축약 금지) |
| 와이어프레임 크기 | 플랫폼별 **고정 축척** (PC 1000px = 6.2in, Mobile 375px = 2.55in). 설명 양 때문에 크기가 바뀌지 않음. 고정 축척으로 한 장을 넘는 긴 화면만 글자가 없는 빈 줄에서 상단/하단으로 나눔 |
| 와이어프레임 배치 | PC는 좌측 한 열(짧은 프레임은 세로로 쌓음), Mobile은 한 장에 최대 3개 나란히. Description 위치도 플랫폼별로 고정 |
| Description | 그 슬라이드에 **실제로 보이는 마커 번호의 구성 요소만**. 마커 없는 상태 프레임만 있는 슬라이드는 "상태 화면" 안내 |
| 상태별 화면·처리 규칙 | 같은 화면 마지막 슬라이드의 Description에 들어가면 함께, 넘치면 **바로 다음 슬라이드**(같은 메타 표, 2단) |
| 마커 | 원래 위치가 글자·다른 마커와 겹치면 요소 바깥(왼쪽 → 위 → 오른쪽 → 가장자리 훑기) 빈자리로 자동 이동. 빌드 결과의 `marker collisions`가 0이어야 함 |
| 마커 자동 이식 | 마커가 없는 프레임(PC 변형, 상태 화면)에는 같은 화면의 다른 프레임에서 마커가 붙은 요소와 글자가 같은 요소를 찾아 같은 번호를 붙임 |
| 편집성 | 모든 박스·글자·마커·표가 PowerPoint 네이티브 도형/표 (이미지 아님) |

## 워크플로우

1. **입력 확인**: 화면설계서.md (`### SCR-NNN. 화면명` + 메타 표(URL/플랫폼/접근 권한/관련 기능/관련 API) + `**UI 컴포넌트**` 표 + `**상태별 화면**` 표 + `**처리 규칙**` 목록). 디자인 기준 문서(디자인스타일가이드 등)가 있으면 함께 읽는다.
2. **조각 HTML 작성**: 화면별 `<div id="scr-nnn" class="screen-section">` 조각을 `frag_*.html`로 작성한다. 규칙은 `references/fragment-spec.md`, 예시는 `assets/example_fragment.html`, 공통 CSS는 `assets/lowfi.css`(수정 금지). 화면이 많으면 4개씩 나눠 병렬 에이전트에 맡긴다(에이전트마다 자기 frag 파일만 쓰기). 대표 화면 2~3개로 먼저 시안을 보여주고 스타일 확정 후 나머지를 만든다.
3. **조립**: `assemble.py`로 하나의 HTML로 합친다.
4. **검증**: 화면별로 설명표 번호 집합과 `data-n` 마커 집합이 같은지, 이모지·`<style>` 태그가 없는지 점검하고, 헤드리스 Chrome 스크린샷으로 마커 겹침을 본다.
5. **PPTX 출력**: `make_pptx.sh`로 좌표 추출 + PPTX 생성. 출력의 `marker collisions`가 0인지 확인한다. 축척은 `--pc-scale`, `--mo-scale`로 바꿀 수 있다(바꾸면 모든 슬라이드에 똑같이 적용).
6. **렌더링 검수**: `preview.py`로 대표 슬라이드 몇 장을 PNG로 뽑아 확인한다(macOS Quick Look, 맑은 고딕 없으면 대체 글꼴로 보임).

## 명령

```bash
# SK = 이 스킬 폴더. 스킬을 불러올 때 표시되는 "Base directory" 경로를 그대로 쓴다
SK=<이 스킬 폴더>
# 3. 조립 (조각 폴더 -> HTML). 파일명에는 타임스탬프를 붙여 덮어쓰기 방지
$SK/.venv/bin/python $SK/scripts/assemble.py --frags <조각폴더> --out 화면설계서_lowfi_YYYYMMDD_HHMM.html --title 프로젝트명 --version v1.0
# 5. PPTX (venv가 없으면 자동 생성: python-pptx, lxml)
$SK/scripts/make_pptx.sh 화면설계서_lowfi_YYYYMMDD_HHMM.html 화면설계서_YYYYMMDD_HHMM.pptx \
  --md 화면설계서.md --project 프로젝트명 --date YYYY-MM-DD --version v1.0 --note "원본 문서 표기"
# 6. 검수용 렌더링 (슬라이드 번호는 0부터)
$SK/.venv/bin/python $SK/scripts/preview.py 화면설계서_YYYYMMDD_HHMM.pptx <출력폴더> 2 3 10
```

## 파일 구조

```
sb-lowfi-pptx/
├── SKILL.md
├── assets/
│   ├── lowfi.css               # low-fi 공통 스타일 (프레임 .pc/.mo, 마커 [data-n], 버튼·입력·세그먼트·카드·표)
│   └── example_fragment.html   # 완성 예시 3화면 (로그인 PC+모바일, 목록 모바일, 관리자 PC)
├── references/
│   └── fragment-spec.md        # 조각 작성 규칙 (병렬 에이전트 프롬프트에 그대로 사용)
└── scripts/
    ├── assemble.py             # frag_*.html -> 단일 HTML
    ├── extract.js              # 브라우저에서 프레임별 도형·텍스트·마커 좌표 추출
    ├── extract_geo.py          # 헤드리스 Chrome 실행 -> geo.json
    ├── build_pptx.py           # geo.json (+ md) -> PPTX
    ├── make_pptx.sh            # extract_geo + build_pptx 한 번에
    └── preview.py              # 슬라이드 PNG 렌더링 (검수용)
```

## 주의

| 항목 | 내용 |
|------|------|
| 메타 정보 출처 | `--md`를 주면 화면설계서.md 메타 표를 원문 그대로 쓴다. 없으면 HTML의 `.meta` 줄(`URL · 플랫폼 · 권한 · 기능 · API`)을 나눠 쓴다 |
| 상태·규칙 출처 | HTML의 `.stbl` 표·목록을 우선 쓰고, 없으면 md의 `**상태별 화면**`·`**처리 규칙**`을 읽는다 |
| 글꼴 | 맑은 고딕(코드는 Consolas). Windows PowerPoint 기준으로 폭을 보정했다 |
| 세로로 긴 화면 | 고정 축척 높이(PC 약 860px, Mobile 약 780px)를 넘으면 자동으로 상단/하단 분할. 의미 단위로 나누고 싶으면 HTML에서 프레임을 미리 둘로 나눈다 |
| 기존 sb-creator-pptx와 차이 | sb-creator-pptx는 화면을 7.5in 단위로 잘라 붙이는 범용 변환기. 이 스킬은 프레임 단위로 한 장에 맞추고 현업 화면설계서 레이아웃을 따른다 |
| 의존성 | Google Chrome(헤드리스), Python 3 + python-pptx, lxml. 렌더링 검수(`preview.py`)는 macOS `qlmanage` 전용. 다른 OS에서는 PPTX를 직접 열어 확인한다 |
| 파일명 | HTML/PPTX 파일명에 `_YYYYMMDD_HHMM`을 붙여 기존 파일을 덮어쓰지 않는다 |
