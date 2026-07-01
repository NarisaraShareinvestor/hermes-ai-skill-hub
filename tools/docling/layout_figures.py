#!/usr/bin/env python3
"""layout_figures.py — ดึง bounding box ของ 'รูป/กราฟ/ตาราง' ทุกหน้าจาก PDF ด้วย DocLayout-YOLO
(YOLOv10 ที่เทรนบน DocStructBench — เร็ว + มี class 'figure'/'table' โดยตรง แม่นเรื่องกราฟ/ชาร์ต).

ใช้กับหน้า dashboard ที่กราฟหลายอันวางบนพื้นหลังเดียวกันโดยไม่มีการ์ด — heuristic เชิงเรขาคณิต
(การ์ดขาว/cluster) แยกไม่ได้ แต่ YOLO เห็น layout จึงตัด Figure แต่ละอันได้แม่น (เช่นหน้า Financial
Highlights แยกโดนัท Sales / Net Income / bar chart; หน้า 18 แยก Figure 5/6/7 ครบ).

หมายเหตุ: YOLO เก่งเฉพาะ 'กราฟ/ตาราง/รูปถ่ายชัดๆ' — หน้า infographic ดีไซน์เต็มหน้า/กล่อง vision
มันจะไม่คืน figure (ปล่อยให้ backend fallback ไป heuristic เดิมรายหน้า).

output: {"page_count":N,"pages":{"6":[{"type":"figure","box":[x0,y0,x1,y1],"conf":0.93},...]}}
  box = normalize 0..1, origin มุมซ้ายบน
"""
import os

_MODEL = None
_RENDER_DPI = int(os.getenv("LAYOUT_RENDER_DPI", "150"))
_IMGSZ = int(os.getenv("LAYOUT_IMGSZ", "1024"))
_CONF = float(os.getenv("LAYOUT_CONF", "0.3"))
_MIN_FRAC = float(os.getenv("LAYOUT_MIN_FRAC", "0.05"))   # ตัด figure เล็ก (ไอคอน/โลโก้) — กราฟจริงมัก >=7%
_NMS_IOU = float(os.getenv("LAYOUT_NMS_IOU", "0.3"))
_KEEP = {"figure", "table"}   # เก็บเฉพาะ figure/table (ไม่เอา text/title/caption)


def _get_model():
    global _MODEL
    if _MODEL is not None:
        return _MODEL
    from huggingface_hub import hf_hub_download
    from doclayout_yolo import YOLOv10
    repo = os.getenv("LAYOUT_MODEL_REPO", "juliozhao/DocLayout-YOLO-DocStructBench")
    fn = os.getenv("LAYOUT_MODEL_FILE", "doclayout_yolo_docstructbench_imgsz1024.pt")
    _MODEL = YOLOv10(hf_hub_download(repo_id=repo, filename=fn))
    return _MODEL


def _iou(a, b):
    ix0, iy0 = max(a[0], b[0]), max(a[1], b[1])
    ix1, iy1 = min(a[2], b[2]), min(a[3], b[3])
    inter = max(0, ix1 - ix0) * max(0, iy1 - iy0)
    ua = (a[2]-a[0])*(a[3]-a[1]) + (b[2]-b[0])*(b[3]-b[1]) - inter
    return inter / ua if ua > 0 else 0


def extract_figures(pdf_path, p0=1, p1=10 ** 9, min_frac=None):
    """คืน {"page_count":N,"pages":{pageno(str):[{type,box,conf}]}} — box normalize 0..1 มุมซ้ายบน"""
    import pymupdf
    min_frac = _MIN_FRAC if min_frac is None else min_frac
    model = _get_model()
    doc = pymupdf.open(str(pdf_path))
    n = len(doc)
    lo, hi = max(1, p0), min(n, p1)
    s = _RENDER_DPI / 72.0
    pages = {}
    import tempfile
    for pno in range(lo, hi + 1):
        page = doc[pno - 1]
        PR = page.rect
        PA = PR.get_area() or 1
        with tempfile.NamedTemporaryFile(suffix=".png") as tf:
            page.get_pixmap(dpi=_RENDER_DPI).save(tf.name)
            det = model.predict(tf.name, imgsz=_IMGSZ, conf=0.2, device="cpu", verbose=False)[0]
        names = det.names
        cands = []
        for box, cls, cf in zip(det.boxes.xyxy.tolist(), det.boxes.cls.tolist(), det.boxes.conf.tolist()):
            kind = names[int(cls)]
            if kind not in _KEEP or cf < _CONF:
                continue
            r = [box[0]/s, box[1]/s, box[2]/s, box[3]/s]          # pixel → point
            r = [max(0, r[0]), max(0, r[1]), min(PR.width, r[2]), min(PR.height, r[3])]
            if (r[2]-r[0]) * (r[3]-r[1]) < min_frac * PA:
                continue
            cands.append((cf, kind, r))
        cands.sort(reverse=True, key=lambda x: x[0])
        kept = []
        for cf, kind, r in cands:                                 # NMS
            if any(_iou(r, k[2]) > _NMS_IOU for k in kept):
                continue
            kept.append((cf, kind, r))
        if kept:
            pages[str(pno)] = [{"type": k, "conf": round(cf, 3),
                                "box": [round(r[0]/PR.width, 4), round(r[1]/PR.height, 4),
                                        round(r[2]/PR.width, 4), round(r[3]/PR.height, 4)]}
                               for cf, k, r in kept]
    return {"page_count": n, "pages": pages}


def _parse_pages(spec):
    if not spec:
        return (1, 10 ** 9)
    if "-" in spec:
        a, b = spec.split("-", 1)
        return (int(a), int(b))
    return (int(spec), int(spec))


def main():
    import argparse, json, sys, warnings
    warnings.filterwarnings("ignore")
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--pages", default="")
    args = ap.parse_args()
    p0, p1 = _parse_pages(args.pages)
    json.dump(extract_figures(args.pdf, p0, p1), sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()
