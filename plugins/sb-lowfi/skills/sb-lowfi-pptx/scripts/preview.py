"""PPTX의 특정 슬라이드를 PNG로 렌더링(macOS Quick Look). 검수용
사용: preview.py <pptx> <출력폴더> <슬라이드 번호(0부터)> [...]
"""
import sys, os, subprocess
from pptx import Presentation
src, outdir, idxs = sys.argv[1], sys.argv[2], [int(x) for x in sys.argv[3:]]
os.makedirs(outdir, exist_ok=True); files = []
for idx in idxs:
    p = Presentation(src); ids = p.slides._sldIdLst
    for i, sid in reversed(list(enumerate(list(ids)))):
        if i != idx: ids.remove(sid)
    f = os.path.join(outdir, f's{idx}.pptx'); p.save(f); files.append(f)
subprocess.run(['qlmanage', '-t', '-s', '1600', '-o', outdir] + files, capture_output=True, timeout=300)
for f in files: print(f + '.png')
