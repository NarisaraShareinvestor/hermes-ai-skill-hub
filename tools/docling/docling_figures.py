#!/usr/bin/env python3
"""docling_figures.py — ดึง bounding box ของ 'รูป/กราฟ/ตาราง' ทุกหน้าจาก PDF ด้วย Docling layout model
แล้วพ่นออกเป็น JSON (พิกัด normalize 0..1, origin มุมซ้ายบน) ให้ backend เอาไป crop ด้วย pymupdf.

ใช้สำหรับหน้าที่ heuristic เชิงเรขาคณิต (การ์ดขาว/cluster) แยกกราฟไม่ได้ — เช่นหน้า dashboard
ที่กราฟหลายอันวางบนพื้นหลังเดียวกันโดยไม่มีการ์ด (Docling เห็น layout จึงแยก Picture/Table ได้แม่น)

วิธีใช้:
  tools/docling/.venv/bin/python tools/docling/docling_figures.py FILE.pdf [--pages 1-50] [--min-frac 0.01]
output (stdout): {"page_count":N,"pages":{"6":[{"type":"picture","box":[x0,y0,x1,y1]},...]}}
  box = normalize 0..1, origin มุมซ้ายบน (x0,y0=ซ้ายบน)
"""
import sys
import json
import argparse


def _parse_pages(spec, total):
    if not spec:
        return (1, total)
    if "-" in spec:
        a, b = spec.split("-", 1)
        return (int(a), int(b))
    n = int(spec)
    return (n, n)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--pages", default="", help="เช่น 1-50 หรือ 6 (ว่าง=ทั้งไฟล์)")
    ap.add_argument("--min-frac", type=float, default=0.01,
                    help="ทิ้ง box ที่เล็กกว่าสัดส่วนนี้ของหน้า (กันไอคอน/โลโก้)")
    args = ap.parse_args()

    import warnings
    warnings.filterwarnings("ignore")
    from docling.document_converter import DocumentConverter

    # หาจำนวนหน้าก่อน (Docling เปิดอ่าน metadata ไม่ได้ตรงๆ → ใช้ pypdf ถ้ามี ไม่งั้นปล่อยช่วงกว้าง)
    total = 10 ** 9
    try:
        from pypdf import PdfReader
        total = len(PdfReader(args.pdf).pages)
    except Exception:
        pass
    p0, p1 = _parse_pages(args.pages, total)

    conv = DocumentConverter()
    res = conv.convert(args.pdf, page_range=(p0, min(p1, total)))
    doc = res.document

    # ขนาดหน้า (ใช้ flip พิกัด + normalize)
    sizes = {}
    for pno, pg in doc.pages.items():
        try:
            sizes[int(pno)] = (float(pg.size.width), float(pg.size.height))
        except Exception:
            pass

    pages = {}

    def add(kind, prov_list):
        for pr in prov_list:
            pno = int(pr.page_no)
            wh = sizes.get(pno)
            if not wh:
                continue
            W, H = wh
            if W <= 0 or H <= 0:
                continue
            bb = pr.bbox
            l, t, r, b = float(bb.l), float(bb.t), float(bb.r), float(bb.b)
            # Docling อาจเป็น BOTTOMLEFT → flip เป็น top-left
            if "BOTTOMLEFT" in str(bb.coord_origin).upper():
                y0, y1 = H - t, H - b
            else:
                y0, y1 = t, b
            x0, x1 = min(l, r), max(l, r)
            y0, y1 = min(y0, y1), max(y0, y1)
            if (x1 - x0) * (y1 - y0) < args.min_frac * W * H:
                continue
            box = [round(x0 / W, 4), round(y0 / H, 4), round(x1 / W, 4), round(y1 / H, 4)]
            pages.setdefault(str(pno), []).append({"type": kind, "box": box})

    for pic in doc.pictures:
        add("picture", pic.prov)
    for tbl in doc.tables:
        add("table", tbl.prov)

    json.dump({"page_count": len(sizes), "pages": pages}, sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()
