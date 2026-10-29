// sb-lowfi-figma renderer: Figma 파일의 '컴포넌트' 페이지 텍스트 노드에 저장해 두고 호출마다 실행한다.
// 실행: const f = new AsyncFunction('D', 'figma', SRC); return await f(D, figma);
// D = { op:'screen'|'flow'|'index', ... } (build_payloads.py가 생성)
const FONT = 'Noto Sans KR';
await Promise.all(['Regular', 'Medium', 'Bold'].map(s => figma.loadFontAsync({ family: FONT, style: s })));
const hex = h => { const n = parseInt(h.slice(1), 16); return { r: ((n >> 16) & 255) / 255, g: ((n >> 8) & 255) / 255, b: (n & 255) / 255 }; };
const solid = h => [{ type: 'SOLID', color: hex(h) }];
const C = { ink: '#222222', gray: '#6b6b73', line: '#c8c8cd', hdr: '#404040', light: '#f4f4f5', orange: '#e8590c', white: '#ffffff', canvas: '#fafafa', blue: '#2A4DA0' };
const created = [];
const txt = (s, size, color, style = 'Regular', w = null) => {
  const t = figma.createText(); t.fontName = { family: FONT, style }; t.characters = String(s); t.fontSize = size; t.fills = solid(color);
  if (w) { t.textAutoResize = 'HEIGHT'; t.resize(w, t.height); } else t.textAutoResize = 'WIDTH_AND_HEIGHT';
  return t;
};
const page = await figma.getNodeByIdAsync(D.pageId);
await figma.setCurrentPageAsync(page);

// ---------- 화면 섹션 ----------
async function screen() {
  const marker = await figma.getNodeByIdAsync(D.markerId);
  const mkKey = Object.keys(marker.componentPropertyDefinitions).find(k => k.startsWith('n'));
  // 같은 레인의 마지막 섹션 아래에 배치
  let y = D.startY;
  for (const n of page.children) if (n.type === 'SECTION' && n.name.startsWith(D.laneTag + ' ')) y = Math.max(y, n.y + n.height + D.gap);
  const old = page.children.find(n => n.type === 'SECTION' && n.name === D.secName);
  if (old) { y = old.y; old.remove(); }   // 재실행 시 같은 화면은 교체
  const sec = figma.createSection(); sec.name = D.secName; sec.x = D.laneX; sec.y = y; sec.fills = solid('#ffffff');
  created.push(sec.id);
  const P = 48;
  // 1) 메타 표
  const meta = figma.createAutoLayout('VERTICAL', { name: '메타 정보', itemSpacing: 0 });
  meta.strokes = solid(C.line); meta.strokeWeight = 1; meta.fills = solid(C.white);
  sec.appendChild(meta); meta.x = P; meta.y = P;
  for (const [k, v] of D.meta) {
    const row = figma.createAutoLayout('HORIZONTAL', { name: k, itemSpacing: 0 });
    meta.appendChild(row); row.layoutSizingHorizontal = 'FILL';
    const lc = figma.createAutoLayout('HORIZONTAL', { paddingLeft: 12, paddingRight: 12, paddingTop: 8, paddingBottom: 8 }); lc.fills = solid(C.hdr);
    row.appendChild(lc); lc.resize(150, lc.height); lc.layoutSizingHorizontal = 'FIXED'; lc.layoutSizingVertical = 'FILL';
    lc.appendChild(txt(k, 13, C.white, 'Bold'));
    const vc = figma.createAutoLayout('HORIZONTAL', { paddingLeft: 12, paddingRight: 12, paddingTop: 8, paddingBottom: 8 }); vc.fills = solid(C.white);
    vc.strokes = solid(C.line); vc.strokeWeight = 1; vc.strokeTopWeight = 0; vc.strokeRightWeight = 0; vc.strokeLeftWeight = 0;
    row.appendChild(vc); vc.layoutSizingHorizontal = 'FILL';
    const vt = txt(v, 13, C.ink, 'Regular', 100); vc.appendChild(vt); vt.layoutSizingHorizontal = 'FILL';
  }
  // 메타 표 폭을 먼저 확정해야 높이가 맞게 계산된다
  const TW = D.frames.reduce((a, f) => a + f.w + 80, 0) + 460 + 32 + 520;
  meta.resize(TW, meta.height); meta.layoutSizingHorizontal = 'FIXED';
  // 2) 와이어프레임 (1:1 고정 크기)
  let x = P; const top = P + 40 + 0;   // 메타 표 높이는 나중에 반영
  const frameNodes = [];
  for (const f of D.frames) {
    const cap = txt(f.cap, 15, C.gray, 'Bold'); sec.appendChild(cap); cap.x = x; created.push(cap.id);
    const fr = figma.createFrame(); fr.name = f.cap; fr.resize(f.w, f.h); fr.fills = solid(C.white); fr.clipsContent = true;
    fr.strokes = solid('#9a9aa2'); fr.strokeWeight = 1; fr.cornerRadius = f.kind === 'mo' ? 20 : 8;
    sec.appendChild(fr); fr.x = x; created.push(fr.id);
    for (const it of f.items) {
      if (it[0] === 'b') {
        const [, bx, by, bw, bh, fill, stroke, sw, dashed, rad, oval] = it;
        const r = oval ? figma.createEllipse() : figma.createRectangle();
        r.resize(Math.max(bw, 0.5), Math.max(bh, 0.5)); r.x = bx; r.y = by;
        r.fills = fill ? solid(fill) : [];
        if (stroke) { r.strokes = solid(stroke); r.strokeWeight = sw; if (dashed) r.dashPattern = [4, 3]; } else r.strokes = [];
        if (!oval && rad) r.cornerRadius = rad;
        fr.appendChild(r);
      } else if (it[0] === 'l') {   // 한쪽 테두리: 얇은 사각형
        const [, lx, ly, lw, lh, col] = it;
        const r = figma.createRectangle(); r.resize(Math.max(lw, 0.5), Math.max(lh, 0.5)); r.x = lx; r.y = ly; r.fills = solid(col); fr.appendChild(r);
      } else if (it[0] === 't') {
        const [, tx, ty, tw, th, s, size, col, bold, align, single, ul, lines] = it;
        const t = txt(s, size, col, bold ? 'Bold' : 'Regular', single ? null : Math.ceil(tw * 1.04) + 2);
        t.lineHeight = { unit: 'PIXELS', value: single ? th : th / Math.max(1, lines) };
        if (ul) t.textDecoration = 'UNDERLINE';
        if (!single && align !== 'left') t.textAlignHorizontal = align === 'center' ? 'CENTER' : 'RIGHT';
        fr.appendChild(t);
        t.y = ty;
        if (single && align === 'center') t.x = tx + tw / 2 - t.width / 2;
        else if (single && align === 'right') t.x = tx + tw - t.width;
        else t.x = tx;
      }
    }
    frameNodes.push({ fr, cap, f });
    x += f.w + 80;
  }
  // 3) 화면 설명 열
  const colW = 460;
  const desc = figma.createAutoLayout('VERTICAL', { name: '화면 설명', itemSpacing: 10, paddingLeft: 16, paddingRight: 16, paddingTop: 0, paddingBottom: 16 });
  desc.strokes = solid(C.line); desc.strokeWeight = 1; desc.fills = solid(C.white);
  sec.appendChild(desc); desc.x = x; desc.resize(colW, 100); desc.layoutSizingHorizontal = 'FIXED';
  const head = (parent, title) => {
    const h = figma.createAutoLayout('HORIZONTAL', { paddingTop: 10, paddingBottom: 10, paddingLeft: 16, paddingRight: 16, primaryAxisAlignItems: 'CENTER' });
    h.fills = solid(C.hdr); parent.appendChild(h); h.layoutSizingHorizontal = 'FILL';
    h.appendChild(txt(title, 15, C.white, 'Bold'));
    return h;
  };
  const sub = (parent, title) => {
    const h = figma.createAutoLayout('HORIZONTAL', { paddingTop: 6, paddingBottom: 6, paddingLeft: 10, paddingRight: 10 });
    h.fills = solid(C.light); parent.appendChild(h); h.layoutSizingHorizontal = 'FILL';
    h.appendChild(txt(title, 14, C.ink, 'Bold'));
  };
  const hd = head(desc, '화면 설명'); hd.layoutPositioning = 'AUTO';
  desc.paddingLeft = 0; desc.paddingRight = 0;
  const body = figma.createAutoLayout('VERTICAL', { itemSpacing: 10, paddingLeft: 16, paddingRight: 16 });
  desc.appendChild(body); body.layoutSizingHorizontal = 'FILL';
  sub(body, '화면 구성 요소');
  for (const [n, name, d] of D.desc) {
    const row = figma.createAutoLayout('HORIZONTAL', { itemSpacing: 10, counterAxisAlignItems: 'MIN' });
    body.appendChild(row); row.layoutSizingHorizontal = 'FILL';
    if (/^\d{1,2}$/.test(n)) { const m = marker.createInstance(); m.setProperties({ [mkKey]: n }); row.appendChild(m); }
    else row.appendChild(txt(n, 12, C.orange, 'Bold'));
    const t = figma.createText(); t.fontName = { family: FONT, style: 'Regular' }; t.characters = name + '  ' + d; t.fontSize = 13; t.fills = solid(C.ink);
    t.setRangeFontName(0, name.length, { family: FONT, style: 'Bold' });
    t.lineHeight = { unit: 'PERCENT', value: 145 };
    row.appendChild(t); t.textAutoResize = 'HEIGHT'; t.layoutSizingHorizontal = 'FILL';
  }
  if (!D.desc.length) body.appendChild(txt('이 화면에는 번호가 붙은 구성 요소가 없습니다.', 13, C.gray, 'Regular', colW - 32));
  // 4) 규칙·부연 설명 열
  const rules = figma.createAutoLayout('VERTICAL', { name: '규칙·부연 설명', itemSpacing: 10, paddingBottom: 16 });
  rules.strokes = solid(C.line); rules.strokeWeight = 1; rules.fills = solid(C.white);
  sec.appendChild(rules); rules.x = x + colW + 32; rules.resize(520, 100); rules.layoutSizingHorizontal = 'FIXED';
  head(rules, '상태·규칙·부연 설명');
  const rb = figma.createAutoLayout('VERTICAL', { itemSpacing: 8, paddingLeft: 16, paddingRight: 16 });
  rules.appendChild(rb); rb.layoutSizingHorizontal = 'FILL';
  const para = (s, boldLen = 0, color = C.ink) => {
    const t = figma.createText(); t.fontName = { family: FONT, style: 'Regular' }; t.characters = s; t.fontSize = 13; t.fills = solid(color);
    if (boldLen) t.setRangeFontName(0, boldLen, { family: FONT, style: 'Bold' });
    t.lineHeight = { unit: 'PERCENT', value: 145 };
    rb.appendChild(t); t.textAutoResize = 'HEIGHT'; t.layoutSizingHorizontal = 'FILL'; return t;
  };
  if (D.states.length) { sub(rb, '상태별 화면'); for (const [s, c, d] of D.states) { const line = `${s}  ·  ${c}  →  ${d}`; const t = para(line, s.length); t.setRangeFills(s.length, s.length + 5 + c.length, solid(C.gray)); } }
  if (D.rules.length) { sub(rb, '처리 규칙'); for (const r of D.rules) para('- ' + r); }
  if (D.notes.length) { sub(rb, '부연 설명'); for (const r of D.notes) para('- ' + r, 0, C.gray); }
  // 5) 세로 위치 확정
  const yFr = meta.y + meta.height + 40;
  for (const { fr, cap } of frameNodes) { cap.y = yFr; fr.y = yFr + 30; }
  desc.y = yFr + 30; rules.y = yFr + 30;
  // 6) 마커 (와이어프레임 위 레이어, 겹침 회피 좌표는 미리 계산됨)
  frameNodes.forEach(({ fr, f }) => {
    for (const [n, cx, cy] of f.marks) {
      const m = marker.createInstance(); m.setProperties({ [mkKey]: String(n) });
      sec.appendChild(m); m.x = fr.x + cx - m.width / 2; m.y = fr.y + cy - m.height / 2;
    }
  });
  // 7) 섹션 크기
  const right = Math.max(rules.x + rules.width, ...frameNodes.map(o => o.fr.x + o.fr.width));
  const bottom = Math.max(desc.y + desc.height, rules.y + rules.height, ...frameNodes.map(o => o.fr.y + o.fr.height));
  sec.resizeWithoutConstraints(right + P, bottom + P);
  return { sectionId: sec.id, name: sec.name, x: sec.x, y: sec.y, w: sec.width, h: sec.height, frames: frameNodes.length, markers: D.frames.reduce((a, f) => a + f.marks.length, 0) };
}

// ---------- 흐름도 + 섹션 사이 화살표 ----------
async function flow() {
  const secs = page.children.filter(n => n.type === 'SECTION');
  const byId = {}; for (const s of secs) { const m = s.name.match(/SCR-\d{3}/); if (m) byId[m[0]] = s; }
  const old = page.children.filter(n => n.name === '화면 흐름도' || n.name.startsWith('흐름 화살표'));
  old.forEach(n => n.remove());
  // 레인 안 순서대로 아래 방향 화살표
  for (const lane of D.lanes) {
    const list = lane.order.map(id => byId[id]).filter(Boolean);
    for (let i = 0; i + 1 < list.length; i++) {
      const a = list[i], b = list[i + 1];
      const v = figma.createNodeFromSvg(`<svg width="24" height="${Math.max(30, b.y - (a.y + a.height))}" viewBox="0 0 24 ${Math.max(30, b.y - (a.y + a.height))}" xmlns="http://www.w3.org/2000/svg"><path d="M12 0 V${Math.max(30, b.y - (a.y + a.height)) - 10}" stroke="#2A4DA0" stroke-width="3"/><path d="M4 ${Math.max(30, b.y - (a.y + a.height)) - 12} L12 ${Math.max(30, b.y - (a.y + a.height))} L20 ${Math.max(30, b.y - (a.y + a.height)) - 12}" fill="none" stroke="#2A4DA0" stroke-width="3"/></svg>`);
      v.name = `흐름 화살표 ${lane.order[i]}→${lane.order[i + 1]}`; page.appendChild(v);
      v.x = a.x + 120; v.y = a.y + a.height; created.push(v.id);
    }
  }
  // 상단 흐름도
  const fd = figma.createAutoLayout('VERTICAL', { name: '화면 흐름도', itemSpacing: 28, paddingLeft: 48, paddingRight: 48, paddingTop: 40, paddingBottom: 40 });
  fd.fills = solid('#ffffff'); fd.strokes = solid(C.line); fd.strokeWeight = 1; page.appendChild(fd); created.push(fd.id);
  fd.appendChild(txt(D.title, 32, C.ink, 'Bold'));
  fd.appendChild(txt(D.subtitle, 16, C.gray, 'Regular'));
  for (const lane of D.lanes) {
    const box = figma.createAutoLayout('VERTICAL', { itemSpacing: 12 }); fd.appendChild(box);
    box.appendChild(txt(lane.title, 20, C.blue, 'Bold'));
    for (const chain of lane.chains) {
      const row = figma.createAutoLayout('HORIZONTAL', { itemSpacing: 10, counterAxisAlignItems: 'CENTER' }); box.appendChild(row);
      chain.ids.forEach((id, i) => {
        if (i) row.appendChild(txt('→', 20, C.blue, 'Bold'));
        const c = figma.createAutoLayout('VERTICAL', { paddingLeft: 14, paddingRight: 14, paddingTop: 10, paddingBottom: 10, itemSpacing: 2 });
        c.fills = solid(byId[id] ? '#ffffff' : C.light); c.strokes = solid(byId[id] ? C.hdr : C.line); c.strokeWeight = 1.5; c.cornerRadius = 8;
        row.appendChild(c);
        const a = txt(id, 12, C.orange, 'Bold'); c.appendChild(a);
        const nm = txt(D.names[id] || '', 14, C.ink, 'Bold'); c.appendChild(nm);
        if (byId[id]) { nm.hyperlink = { type: 'NODE', value: byId[id].id }; a.hyperlink = { type: 'NODE', value: byId[id].id }; }
      });
      if (chain.note) row.appendChild(txt(chain.note, 13, C.gray, 'Regular'));
    }
  }
  fd.x = D.flowX; fd.y = D.startY - fd.height - 200;
  return { flowId: fd.id, w: fd.width, h: fd.height, arrows: created.length - 1 };
}

if (D.op === 'screen') return Object.assign(await screen(), { created: created.length });
if (D.op === 'flow') return await flow();
throw new Error('unknown op ' + D.op);
