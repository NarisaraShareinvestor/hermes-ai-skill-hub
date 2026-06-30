#!/usr/bin/env python3
"""docling_figures.py — ดึง bounding box ของ 'รูป/กราฟ/ตาราง' ทุกหน้าจาก PDF ด้วย Docling layout model
แล้วคืนเป็น dict (พิกัด normalize 0..1, origin มุมซ้ายบน) ให้ backend เอาไป crop ด้วย pymupdf.

ใช้สำหรับหน้าที่ heuristic เชิงเรขาคณิต (การ์ดขาว/cluster) แยกกราฟไม่ได้ — เช่นหน้า dashboard
ที่กราฟหลายอันวางบนพื้นหลังเดียวกันโดยไม่มีการ์ด (Docling เห็น layout จึงแยก Picture/Table ได้แม่น)

ใช้เป็น lib (extract_figures) จาก docling_server.py หรือเป็น CLI:
  tools/docling/.venv/bin/python tools/docling/docling_figures.py FILE.pdf [--pages 1-50]
output (stdout): {"page_count":N,"pages":{"6":[{"type":"picture","box":[x0,y0,x1,y1]},...]}}
"""
import sys
import json
import argparse

_CONVERTER = None


def _get_converter():
    """สร้าง DocumentConverter ครั้งเดียว (โหลด layout model ครั้งเดียว) — ปิด OCR + table-structure
    เพราะเราต้องการแค่ bbox ของ figure/table ไม่ต้องอ่าน OCR/โครงสร้างตาราง → เร็วขึ้น เบาขึ้นมาก"""
    global _CONVERTER
    if _CONVERTER is not None:
        return _CONVERTER
    from docling.document_converter import DocumentConverter, PdfFormatOption
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    opts = PdfPipelineOptions()
    opts.do_ocr = False             # PDF มี text layer อยู่แล้ว ไม่ต้อง OCR
    opts.do_table_structure = False  # ต้องการแค่ bbox ของตาราง ไม่ต้องแกะ cell
    _CONVERTER = DocumentConverter(
        format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=opts)})
    return _CONVERTER


def extract_figures(pdf_path, p0=1, p1=10 ** 9, min_frac=0.01):
    """คืน {"page_count":N, "pages":{pageno(str): [{type,box[x0,y0,x1,y1] normalize 0..1}]}}"""
    res = _get_converter().convert(pdf_path, page_range=(p0, p1))
    doc = res.document
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
            if "BOTTOMLEFT" in str(bb.coord_origin).upper():
                y0, y1 = H - t, H - b
            else:
                y0, y1 = t, b
            x0, x1 = min(l, r), max(l, r)
            y0, y1 = min(y0, y1), max(y0, y1)
            if (x1 - x0) * (y1 - y0) < min_frac * W * H:
                continue
            box = [round(x0 / W, 4), round(y0 / H, 4), round(x1 / W, 4), round(y1 / H, 4)]
            pages.setdefault(str(pno), []).append({"type": kind, "box": box})

    for pic in doc.pictures:
        add("picture", pic.prov)
    for tbl in doc.tables:
        add("table", tbl.prov)
    return {"page_count": len(sizes), "pages": pages}


def _parse_pages(spec):
    if not spec:
        return (1, 10 ** 9)
    if "-" in spec:
        a, b = spec.split("-", 1)
        return (int(a), int(b))
    n = int(spec)
    return (n, n)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--pages", default="", help="เช่น 1-50 หรือ 6 (ว่าง=ทั้งไฟล์)")
    ap.add_argument("--min-frac", type=float, default=0.01)
    args = ap.parse_args()
    import warnings
    warnings.filterwarnings("ignore")
    p0, p1 = _parse_pages(args.pages)
    out = extract_figures(args.pdf, p0, p1, args.min_frac)
    json.dump(out, sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()
