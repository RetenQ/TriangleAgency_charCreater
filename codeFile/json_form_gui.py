import json
import os
import sys
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox, filedialog
import subprocess

try:
    import json_to_html
except ImportError:
    sys.path.append(os.path.dirname(__file__))
    import json_to_html

CARDS_DIR = r"e:\三角Allin\codeFile\cards"
EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

# Determine paths based on run environment (Frozen/Dev)
if getattr(sys, 'frozen', False):
    # Running as compiled exe
    APP_DIR = os.path.dirname(sys.executable)
    BASE_RESOURCE_DIR = sys._MEIPASS
    
    # Resources bundled in EXE
    ANOMALY_PATH = os.path.join(BASE_RESOURCE_DIR, "ARC_setting", "Anomaly.json")
    COMPETENCY_PATH = os.path.join(BASE_RESOURCE_DIR, "ARC_setting", "Competency.json")
    REALITY_PATH = os.path.join(BASE_RESOURCE_DIR, "ARC_setting", "Reality.json")
    
    # Output directory relative to EXE
    CARDS_DIR = os.path.join(APP_DIR, "cards")
else:
    # Running as script
    # e:\三角Allin\TrianglgAgency_charCreater\codeFile
    BASE_DIR = os.path.dirname(os.path.abspath(__file__)) 
    # e:\三角Allin\TrianglgAgency_charCreater
    PROJECT_ROOT = os.path.dirname(BASE_DIR) 
    
    ANOMALY_PATH = os.path.join(PROJECT_ROOT, "ARC_setting", "Anomaly.json")
    COMPETENCY_PATH = os.path.join(PROJECT_ROOT, "ARC_setting", "Competency.json")
    REALITY_PATH = os.path.join(PROJECT_ROOT, "ARC_setting", "Reality.json")
    CARDS_DIR = os.path.join(BASE_DIR, "cards")


def safe_filename_part(value: str, fallback: str, max_len: int = 50) -> str:
    v = (value or "").strip() or fallback
    v = "".join("_" if (c in '<>:"/\\|?*' or ord(c) < 32) else c for c in v)
    v = "_".join(v.split())
    v = v.strip("._ ")
    if not v:
        v = fallback
    return v[:max_len]

def html_to_pdf(html_path: str, pdf_path: str):
    """
    Convert HTML to PDF using Microsoft Edge in headless mode.
    """
    if not os.path.exists(EDGE_PATH):
        raise FileNotFoundError(f"Microsoft Edge not found at: {EDGE_PATH}")

    # Edge arguments for headless printing
    # Note: Paths must be absolute.
    cmd = [
        EDGE_PATH,
        "--headless",
        "--disable-gpu",
        f"--print-to-pdf={pdf_path}",
        html_path
    ]
    
    # Run the command
    try:
        # Edge might print logs to stderr/stdout, we capture them to keep console clean
        subprocess.run(cmd, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        print(f"Edge PDF conversion failed: {e.stderr.decode()}")
        raise e

def main():
    # Setup main window
    root = tk.Tk()
    root.title("角色卡编辑器 (JSON/HTML/PDF)")
    
    # Use a wider window
    root.geometry("900x700")

    try:
        with open(ANOMALY_PATH, "r", encoding="utf-8") as f:
            anomaly_data = json.load(f)
        anomaly_titles: list[str] = []
        for key, value in anomaly_data.items():
            if isinstance(value, list):
                anomaly_titles.append(str(key))
    except Exception:
        anomaly_titles = []

    try:
        with open(COMPETENCY_PATH, "r", encoding="utf-8") as f:
            reality_raw = json.load(f)
        reality_roles: dict[str, dict] = {}
        for name, arr in reality_raw.items():
            if isinstance(arr, list) and arr:
                first = arr[0]
                if not isinstance(first, dict):
                    continue
                main = first.get("MAIN") or ""
                main_desc = first.get("MAIN_description") or ""
                pa = first.get("permitted_actions")
                permitted: list[str] = []
                if isinstance(pa, dict):
                    lst = pa.get("list")
                    if isinstance(lst, list):
                        for item in lst:
                            if isinstance(item, str) and item:
                                permitted.append(item)
                reality_roles[str(name)] = {
                    "main": str(main),
                    "main_desc": str(main_desc),
                    "permitted": permitted,
                }
        reality_names = list(reality_roles.keys())
    except Exception:
        reality_roles = {}
        reality_names: list[str] = []

    try:
        with open(REALITY_PATH, "r", encoding="utf-8") as f:
            competency_data = json.load(f)
        competency_types: dict[str, list[str]] = {}
        for name, cfg in competency_data.items():
            if isinstance(cfg, dict):
                types = cfg.get("类型")
                if isinstance(types, list) and types:
                    competency_types[str(name)] = [str(t) for t in types if t]
        competency_names = list(competency_types.keys())
    except Exception:
        competency_types = {}
        competency_names: list[str] = []

    container = tk.Frame(root)
    container.pack(fill="both", expand=True)

    notebook = ttk.Notebook(container)
    notebook.pack(fill="both", expand=True, padx=10, pady=10)

    # Helper for scrollable tabs
    def create_tab(title):
        tab = tk.Frame(notebook)
        notebook.add(tab, text=title)
        
        # Scrollbar logic
        canvas = tk.Canvas(tab)
        vbar = tk.Scrollbar(tab, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas)
        
        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )
        
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=vbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        vbar.pack(side="right", fill="y")
        
        # Mousewheel support
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            
        def _bind_mousewheel(event):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
        def _unbind_mousewheel(event):
            canvas.unbind_all("<MouseWheel>")
            
        canvas.bind("<Enter>", _bind_mousewheel)
        canvas.bind("<Leave>", _unbind_mousewheel)
        
        return scroll_frame

    tab1 = create_tab("基础属性内容")
    tab2 = create_tab("角色详细内容")
    
    pages = [tab1, tab2]

    STAT_MAX_FIELDS = [
        "专注MAX",
        "欺瞒MAX",
        "活力MAX",
        "共情MAX",
        "主动MAX",
        "坚毅MAX",
        "气场MAX",
        "专业MAX",
        "诡秘MAX",
    ]

    STAT_NAMES = ["专注", "欺瞒", "活力", "共情", "主动", "坚毅", "气场", "专业", "诡秘"]

    form_config = [
        # (Key, Label, Type, PageIndex)
        ("姓名", "姓名", "entry", 0),
        ("人称代词", "人称代词", "entry", 0),
        ("机构头衔", "机构头衔", "entry", 0),
        ("机构评级", "机构评级", "entry", 0),
        ("异常体", "异常体", "entry", 0),
        ("现实", "现实", "entry", 0),
        ("职能", "职能", "entry", 0),
        ("专注MAX", "专注MAX", "entry", 0),
        ("欺瞒MAX", "欺瞒MAX", "entry", 0),
        ("活力MAX", "活力MAX", "entry", 0),
        ("共情MAX", "共情MAX", "entry", 0),
        ("主动MAX", "主动MAX", "entry", 0),
        ("坚毅MAX", "坚毅MAX", "entry", 0),
        ("气场MAX", "气场MAX", "entry", 0),
        ("专业MAX", "专业MAX", "entry", 0),
        ("诡秘MAX", "诡秘MAX", "entry", 0),
        ("问题0A", "0.A 描述你的外貌", "text", 0),
        ("问题0B", "0.B 描述你的性格", "text", 0),
        
        ("现实触发器", "现实触发器", "text", 1),
        ("过载解除", "过载解除", "text", 1),
        ("首要指令", "首要指令", "text", 1),
        ("许可行为1", "许可行为1", "entry", 1),
        ("许可行为2", "许可行为2", "entry", 1),
        ("许可行为3", "许可行为3", "entry", 1),
        ("许可行为4", "许可行为4", "entry", 1),
        ("问题1", "1 你是如何与你的异常体接触的？", "text", 1),
        ("问题2", "2 机构是如何找到你的？", "text", 1),
        ("问题3", "3 你的能力有独特的外在视觉表现吗？", "text", 1),
        ("问题4", "4 你喝咖啡有什么偏好？", "text", 1),
        ("问题5", "5 请描述你过往的工作经历。", "text", 1),
        ("问题6", "6 你对办公套件的熟悉程度？", "text", 1),
        ("问题7", "7 协作中你能做出什么贡献？", "text", 1),
        ("补充说明", "补充说明", "text", 1),

        ("能力1资质", "能力1资质", "stat_select", 0),
        ("能力2资质", "能力2资质", "stat_select", 0),
        ("能力3资质", "能力3资质", "stat_select", 0),
    ]
    
    # Generate legacy fields list for compatibility if needed, 
    # but we will switch loop to use form_config.
    # We'll use form_config in the loop.

    widgets: dict[str, object] = {}
    setting_from_data = False

    # ... (helper functions fill_reality_details_from_competency, fill_role_details_from_reality unchanged) ...

    def fill_reality_details_from_competency(name: str):
        cfg = competency_data.get(name)
        if not isinstance(cfg, dict):
            return
        triggers_text = ""
        overload_text = ""
        triggers = cfg.get("现实触发器")
        if isinstance(triggers, list):
            parts = []
            for item in triggers:
                if not isinstance(item, dict):
                    continue
                lines = []
                title = item.get("title")
                if isinstance(title, str) and title:
                    lines.append(title)
                desc = item.get("description")
                if isinstance(desc, str) and desc:
                    lines.append(desc)
                mech = item.get("mechanics")
                if isinstance(mech, str) and mech:
                    lines.append(mech)
                if lines:
                    parts.append("\n".join(lines))
            triggers_text = "\n\n".join(parts)
        overloads = cfg.get("过载解除")
        if isinstance(overloads, list):
            parts = []
            for item in overloads:
                if not isinstance(item, dict):
                    continue
                lines = []
                title = item.get("title")
                if isinstance(title, str) and title:
                    lines.append(title)
                desc = item.get("description")
                if isinstance(desc, str) and desc:
                    lines.append(desc)
                if lines:
                    parts.append("\n".join(lines))
            overload_text = "\n\n".join(parts)
        trig_widget = widgets.get("现实触发器")
        if isinstance(trig_widget, tk.Text):
            trig_widget.delete("1.0", "end")
            trig_widget.insert("1.0", triggers_text)
        overload_widget = widgets.get("过载解除")
        if isinstance(overload_widget, tk.Text):
            overload_widget.delete("1.0", "end")
            overload_widget.insert("1.0", overload_text)

    def fill_role_details_from_reality(name: str):
        cfg = reality_roles.get(name)
        if not isinstance(cfg, dict):
            return
        main = cfg.get("main", "") or ""
        main_desc = cfg.get("main_desc", "") or ""
        if main and main_desc:
            main_text = f"{main}：{main_desc}"
        else:
            main_text = main or main_desc
        main_widget = widgets.get("首要指令")
        if isinstance(main_widget, tk.Text):
            main_widget.delete("1.0", "end")
            main_widget.insert("1.0", main_text)
        permitted = cfg.get("permitted") or []
        if not isinstance(permitted, list):
            permitted = []
        for i in range(4):
            label = f"许可行为{i+1}"
            w = widgets.get(label)
            value = permitted[i] if i < len(permitted) else ""
            if isinstance(w, tk.Entry):
                w.delete(0, "end")
                if value:
                    w.insert(0, value)

    def fill_anomaly_abilities(anomaly_key: str):
        # anomaly_data = { "Category": [ {ability1}, {ability2}, ... ], ... }
        # anomaly_titles was flattened keys? No, anomaly_titles = keys of anomaly_data (e.g. "缺位", "低语"...)
        # We need to find the list of abilities for the selected category.
        
        abilities = anomaly_data.get(anomaly_key)
        if not isinstance(abilities, list):
            return

        # Prepare data structure for abilities
        # We need to store this data so gather_data can pick it up.
        # Since the UI doesn't have explicit fields for abilities, we'll store them in a hidden way
        # or we should probably add them to the data dict directly in gather_data.
        # But wait, gather_data reads from widgets.
        # So we need to store the abilities data somewhere accessible.
        # Let's attach it to the root or a global variable.
        # Better yet, let's update a global 'current_abilities_data' variable.
        
        nonlocal current_abilities_data
        current_abilities_data = []

        for item in abilities:
            if not isinstance(item, dict):
                continue
            
            ability_info = {
                "title": item.get("title", ""),
                "trigger": item.get("description", ""), # Trigger is the description usually? Or part of it. The JSON has description which seems to be the trigger text.
                # Actually, looking at template.html, card 3 has:
                # <div>能力</div> (Title)
                # <div>触发器</div> (Trigger)
                # <div>资质</div> (Stat/Dice?)
                
                # In JSON: "description": "他们似乎永远不知道你在哪里... 并掷欺瞒。"
                # The description includes the trigger and the dice roll.
                
                "success": item.get("outcomes", {}).get("success", ""),
                "failure": item.get("outcomes", {}).get("failure", ""),
                "special": item.get("outcomes", {}).get("specially", ""),
                
                "question": item.get("interactions", {}).get("question", ""),
                "options": []
            }
            
            opts = item.get("interactions", {}).get("options", [])
            for opt in opts:
                ability_info["options"].append({
                    "answer": opt.get("answer", ""),
                    "code": opt.get("code", "")
                })
                
            current_abilities_data.append(ability_info)

    # Global variable to hold current abilities data
    current_abilities_data = []

    # --- UI Layout ---

    # 1. Image Selection
    img_row = 0
    tk.Label(tab1, text="角色照片", anchor="w").grid(row=img_row, column=0, sticky="nw", padx=10, pady=6)
    
    img_frame = tk.Frame(tab1)
    img_frame.grid(row=img_row, column=1, sticky="nw", padx=10, pady=6)
    
    img_entry = tk.Entry(img_frame, width=50)
    img_entry.pack(side="left")
    
    def pick_image():
        path = filedialog.askopenfilename(
            title="选择图片",
            filetypes=[("Images", "*.png;*.jpg;*.jpeg;*.gif"), ("All Files", "*.*")]
        )
        if path:
            img_entry.delete(0, "end")
            img_entry.insert(0, path)
            
    tk.Button(img_frame, text="浏览...", command=pick_image).pack(side="left", padx=5)

    # Track row indices for each tab
    row_indices = [1, 0] # Tab 1 starts at 1 (after image), others at 0

    for i, (key, label, kind, page_idx) in enumerate(form_config):
        # Determine parent frame
        parent = pages[page_idx] if page_idx < len(pages) else pages[0]
        row = row_indices[page_idx]
        row_indices[page_idx] += 1

        tk.Label(parent, text=label, anchor="w").grid(row=row, column=0, sticky="nw", padx=10, pady=6)
        if key == "异常体":
            var = tk.StringVar(parent)
            if anomaly_titles:
                var.set(anomaly_titles[0])
            option = tk.OptionMenu(parent, var, *anomaly_titles) if anomaly_titles else tk.OptionMenu(parent, var, "")
            option.grid(row=row, column=1, sticky="nw", padx=10, pady=6)
            
            def on_anomaly_change(*_):
                fill_anomaly_abilities(var.get())
            
            var.trace_add("write", on_anomaly_change)
            widgets[key] = var
        elif key == "现实":
            comp_frame = tk.Frame(parent)
            comp_frame.grid(row=row, column=1, sticky="nw", padx=10, pady=6)

            name_var = tk.StringVar(parent)
            type_var = tk.StringVar(parent)

            if competency_names:
                name_var.set(competency_names[0])
            else:
                name_var.set("")

            name_option = tk.OptionMenu(comp_frame, name_var, *(competency_names if competency_names else [""]))
            name_option.pack(side="left")

            type_option = tk.OptionMenu(comp_frame, type_var, "")
            type_option.pack(side="left", padx=5)

            def update_type_menu():
                types = competency_types.get(name_var.get(), [])
                menu = type_option["menu"]
                menu.delete(0, "end")
                if types:
                    for t in types:
                        menu.add_command(label=t, command=lambda v=t: type_var.set(v))
                    type_var.set(types[0])
                else:
                    type_var.set("")

            def on_name_change(*_):
                update_type_menu()
                fill_reality_details_from_competency(name_var.get())

            name_var.trace_add("write", on_name_change)
            update_type_menu()

            widgets[key] = {
                "name_var": name_var,
                "type_var": type_var,
                "type_menu": type_option,
                "name_menu": name_option,
            }
        elif key == "职能":
            job_var = tk.StringVar(parent)
            if reality_names:
                job_var.set(reality_names[0])
            else:
                job_var.set("")
            job_option = tk.OptionMenu(parent, job_var, *(reality_names if reality_names else [""]))
            job_option.grid(row=row, column=1, sticky="nw", padx=10, pady=6)

            def on_job_change(*_):
                if setting_from_data:
                    return
                fill_role_details_from_reality(job_var.get())

            job_var.trace_add("write", on_job_change)
            widgets[key] = job_var
        elif kind == "stat_select":
            stat_var = tk.StringVar(parent)
            stat_var.set(STAT_NAMES[0] if STAT_NAMES else "")
            stat_option = tk.OptionMenu(parent, stat_var, *STAT_NAMES) if STAT_NAMES else tk.OptionMenu(parent, stat_var, "")
            stat_option.grid(row=row, column=1, sticky="nw", padx=10, pady=6)
            widgets[key] = stat_var
        elif kind == "entry":
            e = tk.Entry(parent, width=60)
            e.grid(row=row, column=1, sticky="nw", padx=10, pady=6)
            if key in STAT_MAX_FIELDS:
                e.insert(0, "0")
            widgets[key] = e
        else:
            t = tk.Text(parent, width=60, height=4)
            t.grid(row=row, column=1, sticky="nw", padx=10, pady=6)
            widgets[key] = t

    if anomaly_titles:
        fill_anomaly_abilities(anomaly_titles[0])
    if competency_names:
        fill_reality_details_from_competency(competency_names[0])
    if reality_names:
        fill_role_details_from_reality(reality_names[0])

    # --- Logic Functions ---

    def gather_data() -> dict:
        data: dict[str, str] = {}
        # Image
        img_path = img_entry.get().strip()
        if img_path:
            data["图片路径"] = img_path
            
        for key, label, kind in form_config:
            w = widgets[key]
            if key == "异常体":
                if isinstance(w, tk.StringVar):
                    value = w.get().strip()
                else:
                    value = str(w.get()).strip()
            elif key == "现实":
                comp = widgets["现实"]
                name_val = comp["name_var"].get().strip()
                type_val = comp["type_var"].get().strip()
                value = f"{name_val}-{type_val}" if name_val and type_val else ""
            elif key == "职能":
                if isinstance(w, tk.StringVar):
                    value = w.get().strip()
                else:
                    value = str(w.get()).strip()
            elif kind == "stat_select":
                if isinstance(w, tk.StringVar):
                    value = w.get().strip()
                else:
                    value = str(w.get()).strip()
            elif kind == "entry":
                value = w.get().strip()
            else:
                value = w.get("1.0", "end").strip()
            if value != "":
                data[key] = value
        
        # Add current abilities data
        if current_abilities_data:
            # Inject selected stats into abilities
            output_abilities = []
            for i, ab in enumerate(current_abilities_data):
                new_ab = ab.copy()
                stat_key = f"能力{i+1}资质"
                if stat_key in data:
                    new_ab["stat"] = data[stat_key]
                output_abilities.append(new_ab)
            data["abilities"] = output_abilities
            
        return data

    def set_fields(data: dict):
        nonlocal setting_from_data
        img_entry.delete(0, "end")
        img_entry.insert(0, data.get("图片路径", ""))
        
        setting_from_data = True
        try:
            for key, label, kind in form_config:
                w = widgets[key]
                val = data.get(key, "")
                if key == "异常体":
                    if isinstance(w, tk.StringVar):
                        if val:
                            w.set(val)
                            # Also trigger fill_anomaly_abilities?
                            # The trace on 'w' should handle it if we set it.
                            # But wait, trace fires on set()
                        elif anomaly_titles:
                            w.set(anomaly_titles[0])
                elif key == "现实":
                    comp = widgets["现实"]
                    name_var = comp["name_var"]
                    type_var = comp["type_var"]
                    type_menu = comp["type_menu"]

                    if isinstance(val, str) and "-" in val:
                        cname, ctype = val.split("-", 1)
                    else:
                        cname, ctype = val, ""

                    if cname:
                        name_var.set(cname)
                    else:
                        if competency_names:
                            name_var.set(competency_names[0])

                    types = competency_types.get(name_var.get(), [])
                    menu = type_menu["menu"]
                    menu.delete(0, "end")
                    if types:
                        for t in types:
                            menu.add_command(label=t, command=lambda v=t: type_var.set(v))
                        if ctype and ctype in types:
                            type_var.set(ctype)
                        else:
                            type_var.set(types[0])
                    else:
                        type_var.set("")
                elif key == "职能":
                    if isinstance(w, tk.StringVar):
                        if val:
                            w.set(val)
                        elif reality_names:
                            w.set(reality_names[0])
                elif kind == "entry":
                    w.delete(0, "end")
                    w.insert(0, val)
                else:
                    w.delete("1.0", "end")
                    w.insert("1.0", val)
        finally:
            setting_from_data = False

    def validate_data(data):
        if not data.get("姓名"):
            messagebox.showwarning("缺少字段", "请填写：姓名")
            return False
        if not data.get("异常体"):
            messagebox.showwarning("缺少字段", "请填写：异常体")
            return False
        return True

    def save_and_generate():
        data = gather_data()
        if not validate_data(data):
            return

        # Determine file name and directory
        name = safe_filename_part(data.get("姓名", ""), "Unnamed")
        
        # Structure: cards/<Name>/<Name>.[json|html|pdf]
        card_dir = os.path.join(CARDS_DIR, name)
        os.makedirs(card_dir, exist_ok=True)
        
        base_path = os.path.join(card_dir, name)
        json_path = base_path + ".json"
        html_path = base_path + ".html"
        pdf_path = base_path + ".pdf"

        try:
            # 1. Save JSON
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            # 2. Generate HTML (using imported module)
            # Assuming json_to_html.generate_html(json_path, out_path, template_path)
            # We use the default template path from the module
            json_to_html.generate_html(json_path, html_path)
            
            # 3. Generate PDF
            html_to_pdf(html_path, pdf_path)
            
            messagebox.showinfo("成功", f"已更新所有文件：\nDirectory: {card_dir}\n\n[OK] JSON\n[OK] HTML\n[OK] PDF")
            
        except Exception as e:
            messagebox.showerror("错误", f"处理失败：\n{str(e)}")

    def load_card():
        path = filedialog.askopenfilename(
            title="打开角色卡 JSON",
            initialdir=CARDS_DIR,
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
        )
        if not path:
            return
            
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            set_fields(data)
            # Update window title or status?
            root.title(f"角色卡编辑器 - {os.path.basename(path)}")
        except Exception as e:
            messagebox.showerror("读取失败", f"无法读取文件：\n{str(e)}")

    # --- Buttons ---
    btn_frame = tk.Frame(container)
    btn_frame.pack(side="bottom", fill="x", pady=10, padx=10)
    
    tk.Button(btn_frame, text="📂 打开 (Load)", command=load_card, width=15, height=2).pack(side="left", padx=10)
    tk.Button(btn_frame, text="💾 保存并生成 (Save & Sync)", command=save_and_generate, width=25, height=2, bg="#dddddd").pack(side="left", padx=10)
    tk.Button(btn_frame, text="退出 (Exit)", command=root.destroy, width=15, height=2).pack(side="left", padx=10)

    root.mainloop()

if __name__ == "__main__":
    main()
