import argparse
import datetime as _dt
import json
import os
from io import BytesIO


PDF_PATH_DEFAULT = r"e:\三角Allin\角色卡文档-无水印无加密版.pdf"
OUTPUT_DIR_DEFAULT = r"e:\三角Allin\codeFile\output_CARD"


def load_json_dict(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        obj = json.load(f)
    if not isinstance(obj, dict):
        raise ValueError("JSON内容必须是对象(dict)。")
    return obj


def normalize_positions(raw_positions: dict) -> dict[str, tuple[float, float, int]]:
    normalized: dict[str, tuple[float, float, int]] = {}
    for k, v in raw_positions.items():
        if isinstance(v, (list, tuple)) and len(v) >= 3:
            x, y, size = v[0], v[1], v[2]
        elif isinstance(v, dict) and {"x", "y"} <= set(v.keys()):
            x, y = v["x"], v["y"]
            size = v.get("size", 12)
        else:
            raise ValueError(f"positions里字段 {k} 的格式不正确：{v}")
        normalized[str(k)] = (float(x), float(y), int(size))
    return normalized


def _safe_filename_part(value: str, fallback: str, max_len: int = 50) -> str:
    v = (value or "").strip() or fallback
    v = "".join("_" if (c in '<>:"/\\|?*' or ord(c) < 32) else c for c in v)
    v = "_".join(v.split())
    v = v.strip("._ ")
    if not v:
        v = fallback
    return v[:max_len]


def build_default_output_path(data: dict) -> str:
    os.makedirs(OUTPUT_DIR_DEFAULT, exist_ok=True)
    name = _safe_filename_part(str(data.get("姓名", "")), "未知姓名")
    anomaly = _safe_filename_part(str(data.get("异常体", "")), "未知异常体")
    duty = _safe_filename_part(str(data.get("职能", "")), "未知职能")
    ts = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{name}_{anomaly}_{duty}_{ts}.PDF"
    return os.path.join(OUTPUT_DIR_DEFAULT, filename)


def build_overlay_page(width: float, height: float, items: list[tuple[str, float, float, int]]) -> BytesIO:
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    from reportlab.pdfgen import canvas

    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=(width, height))

    font_name = "Helvetica"
    try:
        pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
        font_name = "STSong-Light"
    except Exception:
        pass

    for text, x, y, font_size in items:
        if not text:
            continue
        c.setFont(font_name, font_size)
        c.drawString(x, y, text)

    c.showPage()
    c.save()
    buf.seek(0)
    return buf


def fill_first_page_overlay(pdf_path: str, out_path: str, data: dict, positions: dict[str, tuple[float, float, int]]):
    from pypdf import PdfReader, PdfWriter

    reader = PdfReader(pdf_path)
    page0 = reader.pages[0]
    width = float(page0.mediabox.width)
    height = float(page0.mediabox.height)

    overlay_items = []
    for key, (x, y, size) in positions.items():
        v = str(data.get(key, "")).strip()
        overlay_items.append((v, x, y, size))

    overlay_pdf = build_overlay_page(width, height, overlay_items)
    overlay_reader = PdfReader(overlay_pdf)
    overlay_page = overlay_reader.pages[0]

    page0.merge_page(overlay_page)

    writer = PdfWriter()
    writer.add_page(page0)
    for i in range(1, len(reader.pages)):
        writer.add_page(reader.pages[i])

    with open(out_path, "wb") as f:
        writer.write(f)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", default=PDF_PATH_DEFAULT, help="源PDF路径")
    ap.add_argument("--data", required=True, help="填写数据JSON文件路径(对象：字段名->值)")
    ap.add_argument("--positions", required=True, help="坐标JSON文件路径(对象：字段名->[x,y,size])")
    ap.add_argument("--out", default=None, help="输出PDF路径")
    args = ap.parse_args()

    if not os.path.exists(args.pdf):
        raise FileNotFoundError(f"找不到PDF文件：{args.pdf}")
    if not os.path.exists(args.data):
        raise FileNotFoundError(f"找不到数据JSON：{args.data}")
    if not os.path.exists(args.positions):
        raise FileNotFoundError(f"找不到坐标JSON：{args.positions}")

    data = load_json_dict(args.data)
    positions = normalize_positions(load_json_dict(args.positions))
    out_path = args.out or build_default_output_path(data)

    fill_first_page_overlay(args.pdf, out_path, data, positions)
    print(f"\n已生成：{out_path}")


if __name__ == "__main__":
    main()
