# 角色卡 PDF 工具（JSON 填写 / 坐标锚定 / HTML 档案）

本目录提供一套工具，用于生成“三角Allin”风格的角色卡，支持 PDF 填空和 HTML 档案生成。

## 目录结构

- `json_form_gui.py`：**（推荐）** GUI 界面，用于填写信息、选择头像，并生成 JSON 或 HTML 档案。
- `json_to_html.py`：后端脚本，读取 JSON 生成 HTML 档案。
- `template.html`：HTML 档案的样式模板（已更新为 ARC 2026 风格）。
- `PDF_locate.py`：用于 PDF 锚点定位（高级用法）。
- `get_char_fromJSON.py`：用于 PDF 填空（基于锚点）。

## 依赖安装

```powershell
pip install pypdf reportlab pymupdf
```

## 快速开始：生成 HTML 档案（推荐）

这是生成带有头像、自动排版的角色档案的最佳方式。

1. 运行 GUI：
   ```powershell
   python e:\三角Allin\codeFile\json_form_gui.py
   ```
2. 填写字段信息（支持新版字段：人称代词、许可行为、过载解除等）。
3. （可选）点击“浏览...”选择一张角色照片（注意：当前 ARC 2026 模板暂未启用照片显示，主要用于记录）。
4. 点击 **“生成 HTML 档案”**。
5. 生成的 HTML 文件位于 `e:\三角Allin\codeFile\output_HTML\`，可以直接用浏览器打开，并使用浏览器的“打印 -> 另存为 PDF”功能保存为 PDF。

## 高级用法：PDF 填空（旧版）

如果你需要直接在原版 PDF 背景图上填空，请使用以下流程：

### 1. 生成坐标网格（可选）

```powershell
python e:\三角Allin\codeFile\PDF_locate.py --grid-out e:\三角Allin\codeFile\角色卡_坐标网格.pdf --grid-step 100
```

### 2. 点击选点生成 positions.json

```powershell
python e:\三角Allin\codeFile\PDF_locate.py --pick-positions e:\三角Allin\codeFile\positions.json
```

### 3. 从 JSON 生成 PDF

```powershell
python e:\三角Allin\codeFile\get_char_fromJSON.py --data e:\三角Allin\codeFile\data_test.json --positions e:\三角Allin\codeFile\positions.json
```

默认输出到 `e:\三角Allin\codeFile\output_CARD\`。

## 自定义 HTML 模板

你可以直接编辑 `e:\三角Allin\codeFile\template.html` 来修改档案的样式、布局或配色。
当前模板使用了 Tailwind CSS，你可以参考 `card.html` 进行修改。
