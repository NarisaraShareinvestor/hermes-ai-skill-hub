#!/usr/bin/env bash
# ติดตั้ง Docling tool (ครั้งเดียว). รันครั้งแรกจะดาวน์โหลด layout model ~ลง ~/.cache/huggingface
set -e
cd "$(dirname "$0")"
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo "เสร็จ. ใช้งาน: source tools/docling/.venv/bin/activate && python tools/docling/docling_convert.py FILE.pdf"
