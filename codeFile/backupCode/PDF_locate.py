import argparse
import json
import os
import tempfile
from io import BytesIO


PDF_PATH_DEFAULT = r"e:\三角Allin\角色卡文档-无水印无加密版.pdf"


def load_json_dict(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        obj = json.load(f)
    if not isinstance(obj, dict):
        raise ValueError("JSON内容必须是对象(dict)。")
    return obj


def save_json_dict(path: str, obj: dict):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def parse_keys_arg(keys: str | None) -> list[str]:
    if keys:
        return [k.strip() for k in keys.split(",") if k.strip()]
    return [
        "姓名",
        "机构头衔",
        "机构评级",
        "异常体",
        "现实",
        "职能",
        "现实触发器",
        "过载解除",
        "首要指令",
    ]


def align_positions_x_by_groups(positions: dict[str, list], groups: list[list[str]]):
    for group in groups:
        if not group:
            continue
        base_key = group[0]
        base_val = positions.get(base_key)
        if not isinstance(base_val, list) or len(base_val) < 2:
            continue
        base_x = float(base_val[0])
        for key in group[1:]:
            val = positions.get(key)
            if not isinstance(val, list) or len(val) < 2:
                continue
            val[0] = round(base_x, 2)


def build_grid_overlay_page(width: float, height: float, step: int) -> BytesIO:
    from reportlab.pdfgen import canvas

    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=(width, height))

    c.setLineWidth(0.5)
    c.setStrokeColorRGB(0.85, 0.85, 0.85)
    c.setFont("Helvetica", 6)

    x = 0
    while x <= width:
        c.line(x, 0, x, height)
        c.setFillColorRGB(0.4, 0.4, 0.4)
        c.drawString(x + 1, height - 8, str(int(x)))
        x += step

    y = 0
    while y <= height:
        c.line(0, y, width, y)
        c.setFillColorRGB(0.4, 0.4, 0.4)
        c.drawString(2, y + 1, str(int(y)))
        y += step

    c.setFillColorRGB(0.2, 0.2, 0.2)
    c.setFont("Helvetica", 8)
    c.drawString(6, height - 18, f"size: {int(width)} x {int(height)}  step: {step}")

    c.showPage()
    c.save()
    buf.seek(0)
    return buf


def export_grid_pdf(pdf_path: str, out_path: str, step: int):
    from pypdf import PdfReader, PdfWriter

    reader = PdfReader(pdf_path)
    page0 = reader.pages[0]
    width = float(page0.mediabox.width)
    height = float(page0.mediabox.height)

    overlay_pdf = build_grid_overlay_page(width, height, int(step))
    overlay_reader = PdfReader(overlay_pdf)
    overlay_page = overlay_reader.pages[0]
    page0.merge_page(overlay_page)

    writer = PdfWriter()
    writer.add_page(page0)
    for i in range(1, len(reader.pages)):
        writer.add_page(reader.pages[i])

    with open(out_path, "wb") as f:
        writer.write(f)


def pick_positions_gui(
    pdf_path: str,
    out_positions_path: str,
    keys: list[str],
    default_font_size: int,
    render_scale: float,
):
    import fitz
    import tkinter as tk

    doc = fitz.open(pdf_path)
    page = doc[0]
    width = float(page.rect.width)
    height = float(page.rect.height)

    matrix = fitz.Matrix(render_scale, render_scale)
    pix = page.get_pixmap(matrix=matrix, alpha=False)

    # Use PPM format to avoid libpng warnings (iCCP profile) and dependency issues
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".ppm")
    tmp_path = tmp.name
    tmp.close()
    pix.save(tmp_path)

    scale = pix.width / width

    positions: dict[str, list[float | int]] = {}
    cursor = {"i": 0}
    align_groups = [
        ["姓名", "机构头衔", "机构评级"],
        ["异常体", "现实", "职能"],
        ["现实触发器", "过载解除", "首要指令"],
    ]

    root = tk.Tk()
    root.title(f"选点：{keys[cursor['i']]}（点击放置位置）")
    img = tk.PhotoImage(file=tmp_path)
    screen_w = int(root.winfo_screenwidth())
    screen_h = int(root.winfo_screenheight())
    view_w = min(int(img.width()), max(600, screen_w - 120))
    view_h = min(int(img.height()), max(600, screen_h - 220))

    frame = tk.Frame(root)
    frame.pack(fill="both", expand=True)

    canvas = tk.Canvas(frame, width=view_w, height=view_h)
    vbar = tk.Scrollbar(frame, orient="vertical", command=canvas.yview)
    hbar = tk.Scrollbar(frame, orient="horizontal", command=canvas.xview)
    canvas.configure(yscrollcommand=vbar.set, xscrollcommand=hbar.set)

    canvas.grid(row=0, column=0, sticky="nsew")
    vbar.grid(row=0, column=1, sticky="ns")
    hbar.grid(row=1, column=0, sticky="ew")
    frame.grid_rowconfigure(0, weight=1)
    frame.grid_columnconfigure(0, weight=1)

    canvas.create_image(0, 0, anchor="nw", image=img)
    canvas.configure(scrollregion=(0, 0, int(img.width()), int(img.height())))

    hint = tk.StringVar()
    hint.set(f"当前字段：{keys[cursor['i']]}  |  左键选点  |  右键撤销  |  鼠标滚轮滚动  |  中键拖拽  |  Esc退出")
    label = tk.Label(root, textvariable=hint)
    label.pack()

    coord = tk.StringVar()
    coord.set("坐标：x=0.00, y=0.00")
    coord_label = tk.Label(root, textvariable=coord)
    coord_label.pack()

    def cleanup():
        try:
            os.remove(tmp_path)
        except Exception:
            pass

    grid_ids: list[int] = []
    crosshair = {"v": None, "h": None}

    def draw_grid():
        nonlocal grid_ids
        for gid in grid_ids:
            try:
                canvas.delete(gid)
            except Exception:
                pass
        grid_ids = []

        grid_step_pdf = 25.0
        major_step_pdf = 100.0
        grid_step_px = grid_step_pdf * scale
        major_step_px = major_step_pdf * scale

        w_px = float(img.width())
        h_px = float(img.height())

        x = 0.0
        while x <= w_px + 0.1:
            is_major = abs((x / major_step_px) - round(x / major_step_px)) < 1e-6 if major_step_px > 0 else False
            color = "#B0B0B0" if is_major else "#D9D9D9"
            width_px = 1.2 if is_major else 0.8
            grid_ids.append(canvas.create_line(x, 0, x, h_px, fill=color, width=width_px))
            if is_major and x > 0:
                x_pdf = x / scale
                grid_ids.append(
                    canvas.create_text(x + 2, 2, anchor="nw", fill="#666666", text=str(int(round(x_pdf))), font=("Helvetica", 8))
                )
            x += grid_step_px

        y = 0.0
        while y <= h_px + 0.1:
            is_major = abs((y / major_step_px) - round(y / major_step_px)) < 1e-6 if major_step_px > 0 else False
            color = "#B0B0B0" if is_major else "#D9D9D9"
            width_px = 1.2 if is_major else 0.8
            grid_ids.append(canvas.create_line(0, y, w_px, y, fill=color, width=width_px))
            if is_major and y > 0:
                y_pdf = height - (y / scale)
                grid_ids.append(
                    canvas.create_text(2, y + 2, anchor="nw", fill="#666666", text=str(int(round(y_pdf))), font=("Helvetica", 8))
                )
            y += grid_step_px

        grid_ids.append(canvas.create_rectangle(0, 0, w_px, h_px, outline="#909090", width=1.5))

    draw_grid()

    def set_title():
        if cursor["i"] < len(keys):
            root.title(f"选点：{keys[cursor['i']]}（点击放置位置）")
            hint.set(f"当前字段：{keys[cursor['i']]}  |  左键选点  |  右键撤销  |  鼠标滚轮滚动  |  中键拖拽  |  Esc退出")
        else:
            root.title("选点完成")
            hint.set("选点完成，窗口可关闭。")

    def on_left_click(event):
        if cursor["i"] >= len(keys):
            return
        key = keys[cursor["i"]]
        cx = float(canvas.canvasx(event.x))
        cy = float(canvas.canvasy(event.y))
        x_pdf = cx / scale
        y_pdf = height - cy / scale
        positions[key] = [round(x_pdf, 2), round(y_pdf, 2), int(default_font_size)]
        r = 5
        canvas.create_oval(cx - r, cy - r, cx + r, cy + r, outline="red", width=2)
        canvas.create_text(cx + 8, cy, anchor="w", fill="red", text=key, font=("Helvetica", 10, "bold"))
        cursor["i"] += 1
        set_title()
        if cursor["i"] >= len(keys):
            align_positions_x_by_groups(positions, align_groups)
            save_json_dict(out_positions_path, positions)

    def on_right_click(event):
        if cursor["i"] <= 0:
            return
        cursor["i"] -= 1
        key = keys[cursor["i"]]
        positions.pop(key, None)
        canvas.delete("all")
        canvas.create_image(0, 0, anchor="nw", image=img)
        canvas.configure(scrollregion=(0, 0, int(img.width()), int(img.height())))
        draw_grid()
        for k, (x_pdf, y_pdf, _) in positions.items():
            x = int(round(x_pdf * scale))
            y = int(round((height - y_pdf) * scale))
            r = 5
            canvas.create_oval(x - r, y - r, x + r, y + r, outline="red", width=2)
            canvas.create_text(x + 8, y, anchor="w", fill="red", text=k, font=("Helvetica", 10, "bold"))
        set_title()

    def on_mousewheel(event):
        units = int(-1 * (event.delta / 120))
        if event.state & 0x0001:
            canvas.xview_scroll(units, "units")
        else:
            canvas.yview_scroll(units, "units")

    def on_motion(event):
        cx = float(canvas.canvasx(event.x))
        cy = float(canvas.canvasy(event.y))
        x_pdf = cx / scale
        y_pdf = height - cy / scale
        if 0 <= x_pdf <= width and 0 <= y_pdf <= height:
            coord.set(f"坐标：x={x_pdf:.2f}, y={y_pdf:.2f}")
        else:
            coord.set("坐标：x=—, y=—")

        if crosshair["v"] is None:
            crosshair["v"] = canvas.create_line(cx, 0, cx, float(img.height()), fill="#7A7A7A", width=1)
            crosshair["h"] = canvas.create_line(0, cy, float(img.width()), cy, fill="#7A7A7A", width=1)
        else:
            canvas.coords(crosshair["v"], cx, 0, cx, float(img.height()))
            canvas.coords(crosshair["h"], 0, cy, float(img.width()), cy)

    def on_middle_down(event):
        canvas.scan_mark(event.x, event.y)

    def on_middle_drag(event):
        canvas.scan_dragto(event.x, event.y, gain=1)

    def on_escape(event):
        if positions:
            align_positions_x_by_groups(positions, align_groups)
            save_json_dict(out_positions_path, positions)
        cleanup()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_escape)
    root.bind("<Escape>", on_escape)
    canvas.bind("<Button-1>", on_left_click)
    canvas.bind("<Button-3>", on_right_click)
    canvas.bind("<MouseWheel>", on_mousewheel)
    canvas.bind("<Motion>", on_motion)
    canvas.bind("<Button-2>", on_middle_down)
    canvas.bind("<B2-Motion>", on_middle_drag)

    root.mainloop()
    cleanup()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", default=PDF_PATH_DEFAULT, help="源PDF路径")
    ap.add_argument("--keys", default=None, help="字段列表(逗号分隔)")
    ap.add_argument("--pick-positions", default=None, help="打开选点窗口并输出positions.json")
    ap.add_argument("--pick-font-size", type=int, default=12, help="选点输出的默认字体大小")
    ap.add_argument("--pick-scale", type=float, default=2.0, help="选点渲染倍率(越大越清晰)")
    ap.add_argument("--grid-out", default=None, help="生成坐标网格PDF并退出")
    ap.add_argument("--grid-step", type=int, default=50, help="网格间距(point)")
    args = ap.parse_args()

    if not os.path.exists(args.pdf):
        raise FileNotFoundError(f"找不到PDF文件：{args.pdf}")

    keys = parse_keys_arg(args.keys)

    if args.grid_out:
        export_grid_pdf(args.pdf, args.grid_out, int(args.grid_step))
        print(f"\n已生成：{args.grid_out}")
        return

    if args.pick_positions:
        pick_positions_gui(
            pdf_path=args.pdf,
            out_positions_path=args.pick_positions,
            keys=keys,
            default_font_size=int(args.pick_font_size),
            render_scale=float(args.pick_scale),
        )
        print(f"\n已生成：{args.pick_positions}")
        return

    raise SystemExit("需要提供 --grid-out 或 --pick-positions")


if __name__ == "__main__":
    main()
