import argparse
import base64
import json
import os
import sys
import datetime as _dt

if getattr(sys, 'frozen', False):
    # Frozen
    BASE_RESOURCE_DIR = sys._MEIPASS
    APP_DIR = os.path.dirname(sys.executable)
    DEFAULT_TEMPLATE = os.path.join(BASE_RESOURCE_DIR, "template.html")
    DEFAULT_OUT_DIR = os.path.join(APP_DIR, "output_HTML")
else:
    # Dev
    DEFAULT_TEMPLATE = os.path.join(os.path.dirname(__file__), "template.html")
    DEFAULT_OUT_DIR = os.path.join(os.path.dirname(__file__), "output_HTML")

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_template(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def get_image_tag(image_path):
    # This logic matches the new template structure (div with class/style)
    # The new template has a container:
    # <div class="mb-8 w-full h-40 bg-gray-100 border border-gray-300 flex items-center justify-center overflow-hidden">
    #    <span class="text-gray-400 text-xs">无照片</span>
    # </div>
    # We want to replace the inner content with the image, OR replace the whole div.
    # The template has <!-- AVATAR_PLACEHOLDER --> before the div.
    
    if not image_path or not os.path.exists(image_path):
        # Return the default placeholder div (as string) or just empty if we don't replace
        return None 
    
    try:
        with open(image_path, "rb") as f:
            data = f.read()
            b64 = base64.b64encode(data).decode("utf-8")
            ext = os.path.splitext(image_path)[1].lower()
            mime = "image/jpeg"
            if ext == ".png":
                mime = "image/png"
            elif ext == ".gif":
                mime = "image/gif"
            
            # Return an img tag with class that fits the container
            return f'<img src="data:{mime};base64,{b64}" class="w-full h-full object-cover">'
    except Exception as e:
        print(f"Error loading image: {e}")
        return None

def safe_filename(s):
    keep = ("-", "_", ".")
    return "".join(c if c.isalnum() or c in keep else "_" for c in s).strip()

def generate_html(json_path, out_path=None, template_path=DEFAULT_TEMPLATE):
    data = load_json(json_path)
    template = load_template(template_path)
    
    # 1. Fill standard fields
    keys = [
        "姓名", "人称代词", "机构头衔", "机构评级", "异常体", 
        "现实", "职能", "现实触发器", "过载解除", "首要指令",
        "许可行为1", "许可行为2", "许可行为3", "许可行为4",
        "问题0A", "问题0B", "问题1", "问题2", "问题3", "问题4", "问题5", "问题6", "问题7", "补充说明",
        "专注MAX", "欺瞒MAX", "活力MAX", "共情MAX", "主动MAX",
        "坚毅MAX", "气场MAX", "专业MAX", "诡秘MAX",
    ]
    
    content = template
    for k in keys:
        val = str(data.get(k, ""))
        content = content.replace(f"{{{{{k}}}}}", val)
    
    # 2. Handle Image
    img_path = data.get("图片路径", "")
    img_tag = get_image_tag(img_path)
    
    # We look for <!-- AVATAR_PLACEHOLDER --> and optionally the "No Photo" text
    # The updated template.html uses "角色头像" as the placeholder text.
    placeholder = '<!-- AVATAR_PLACEHOLDER -->'
    no_photo_text = '<span class="text-xs">角色头像</span>'

    if img_tag:
        # If image exists, replace placeholder with image tag
        if placeholder in content:
            content = content.replace(placeholder, img_tag)
        
        # And remove the "No Photo" text if it exists (to avoid overlap)
        if no_photo_text in content:
            content = content.replace(no_photo_text, "")
    else:
        # If no image, we can leave the placeholder and text as is, 
        # or just remove the placeholder comment.
        pass

    # 3. Handle Page 3 Abilities
    abilities = data.get("abilities", [])
    if abilities and isinstance(abilities, list):
        # We need to replace the ability cards in the template.
        # The template has 3 static ability cards. We should ideally have a placeholder or logic to replace them.
        # Currently, the template has:
        # <!-- 循环 3 次生成能力卡片 (静态写死或之后用脚本) -->
        # <div class="ability-card">...</div> ... <div class="ability-card">...</div>
        
        # We will construct the HTML for the abilities and replace the entire block.
        # But first we need to identify the block in the template.
        # A simple way is to use a marker comment if it exists, or regex replace.
        # The template has comments: <!-- 循环 3 次生成能力卡片 (静态写死或之后用脚本) -->
        
        start_marker = '<!-- 循环 3 次生成能力卡片 (静态写死或之后用脚本) -->'
        end_marker = '<!-- 第四页: 角色关系网 -->' # The next section starts here, but page-3 ends with </div></div>
        
        # Ideally, we should look for the container content of page-3.
        # Let's find the start marker and replace until the end of the 3 cards.
        # Since we don't have an explicit end marker for the cards, we can replace the content 
        # inside <div class="page-wrapper page-3 ..."> ... </div>
        # But replacing by string search is safer if we add a placeholder.
        # Let's construct the HTML first.
        
        abilities_html = []
        for i, ab in enumerate(abilities):
            if i >= 3: break # Only 3 cards fit
            
            title = ab.get("title", "")
            trigger = ab.get("trigger", "")
            # Split description/trigger if needed? 
            # In Anomaly.json: "description": "text... and roll Stat."
            # We put the whole description in trigger for now.
            
            success = ab.get("success", "")
            failure = ab.get("failure", "")
            special = ab.get("special", "")
            question = ab.get("question", "")
            options = ab.get("options", [])
            
            stat = ab.get("stat", "资质")
            
            # Format Options HTML
            options_html = ""
            for opt in options:
                ans = opt.get("answer", "")
                code = opt.get("code", "")
                options_html += f'''
                            <div class="qa-row">
                                答: <input type="text" value="{ans}" readonly style="background:transparent;"> ➔ <div class="square"></div> <div class="square"></div> <div class="square"></div>
                                <span style="margin-left:5px; font-size:10px; color:#999;">({code})</span>
                            </div>'''

            card_html = f'''
            <div class="ability-card">
                <div class="card-header">
                    <div>{title}</div>
                    <div style="font-size: 10px; font-weight: normal; overflow: hidden; white-space: nowrap; text-overflow: ellipsis;" title="{trigger}"></div>
                    <div style="text-align:right">{stat}</div>
                </div>
                <div class="card-body">
                    <div class="success-side">
                        <div class="success-title">▲ 成功时， <div style="flex-grow:1; border-bottom:1px solid var(--primary-blue); margin-left:10px;"></div></div>
                        <div class="input-line" style="height:auto; min-height:25px; font-size:11px;">{success}</div>
                        
                        <div style="display:flex; align-items:center; margin-top:20px;">
                            <span class="icon-star">★</span> 
                            <div style="background:#e2e8f0; width:80px; height:18px; border-radius:10px; margin-right:10px;"></div>,
                            <div style="flex-grow:1; border-bottom:1px solid var(--primary-blue); font-size:11px;">{special}</div>
                        </div>
                    </div>
                    
                    <div class="fail-side">
                        <div class="fail-title">✘ 失败时， <div style="flex-grow:1; border-bottom:1px solid var(--fail-red); margin-left:10px;"></div></div>
                        <div class="fail-line" style="height:auto; min-height:25px; font-size:11px;">{failure}</div>
                        
                        <div class="qa-section">
                            <div class="qa-row">
                                问: <input type="text" value="{question}" readonly style="background:transparent;"> 
                                <div class="checkbox-group">已练习? <div class="square"></div></div>
                            </div>
                            <div style="text-align:right; font-size:11px; margin-bottom:5px;">页码 # ________</div>
                            {options_html}
                        </div>
                    </div>
                </div>
            </div>'''
            abilities_html.append(card_html)
            
        full_abilities_html = "\n".join(abilities_html)
        
        # Replace in template
        # We need to find where to insert. 
        # In template.html: 
        # <!-- 循环 3 次生成能力卡片 (静态写死或之后用脚本) -->
        # ... (3 cards) ...
        # </div>
        # </div>
        # <!-- 第四页: ... -->
        
        # Let's replace the whole marker and following content until the closing div of container?
        # A better way is to define a replacement range in the template using a new marker.
        # But we can't edit template.html easily from here without rewriting it.
        # So we'll use string finding logic.
        
        if start_marker in content:
            # Find the end of the cards section.
            # The cards are inside <div class="container"> which is inside <div class="page-wrapper page-3 ...">
            # The next page starts with <!-- 第四页
            
            next_page_idx = content.find('<!-- 第四页')
            if next_page_idx == -1:
                next_page_idx = len(content)
                
            # Find the last closing div before the next page?
            # Actually, we can just replace the marker and assume the static cards follow it.
            # But we need to remove the static cards.
            # The static cards start after the marker.
            # We can use regex or just finding known strings.
            
            # Simple approach: Replace the marker + known static content if it matches.
            # Or, we can just replace everything between the marker and the closing </div> of the container.
            # The container closes before page-3 wrapper closes.
            
            # Let's try to find the start marker index
            start_idx = content.find(start_marker)
            
            # Find the end of the container div. 
            # The structure is:
            # <div class="page-wrapper page-3 ...">
            #   <div class="container">
            #      <div class="header">...</div>
            #      <!-- Marker -->
            #      <div class="ability-card">...</div>
            #      ...
            #   </div>
            # </div>
            
            # So we look for the next "</div>\n    </div>" sequence after start_idx?
            # That's risky.
            
            # Alternative: Since we control the template, let's assume the user hasn't modified it manually too much.
            # We will replace the static content by looking for the first <div class="ability-card"> and the last </div> of the last card.
            
            # Let's just insert the new HTML after the marker, and if we can, remove the old cards.
            # To remove old cards, we can regex replace `<div class="ability-card">.*?</div>\s*</div>\s*</div>` (non-greedy?)
            # No, nested divs make regex hard.
            
            # BEST APPROACH: Use a unique placeholder in template.html.
            # Since we can't edit template.html right now in this function (it's read only), 
            # we rely on what's there.
            # The marker is unique.
            
            # Let's try to match the exact string of the first static card start?
            card_start = '<div class="ability-card">'
            
            # We construct a replacement string that includes the marker (to keep it?) or just replaces it.
            # Let's replace the marker with the new content.
            # And we need to consume the existing cards.
            # Since we are generating the file, maybe we can just overwrite the whole section if we knew the bounds.
            
            # Hacky but effective: 
            # Find start_marker.
            # Find the start of "<!-- 第四页"
            # The content between them contains the 3 static cards AND the closing divs for container and page-wrapper.
            # Wait, page-wrapper closes BEFORE "<!-- 第四页".
            
            # content[start_idx : next_page_idx] contains:
            # <!-- Marker -->
            # (Static Cards)
            # </div> (container)
            # </div> (page-wrapper)
            
            # We want to replace (Static Cards) with full_abilities_html.
            # So we keep the closing divs.
            
            # Let's find the position of the last "</div>" before "<!-- 第四页"
            # And the one before that.
            
            segment = content[start_idx : next_page_idx]
            # segment ends with closing divs.
            # We want to replace everything from start of marker to the start of the closing divs.
            
            # How many closing divs? 
            # <div class="container"> ... </div>
            # <div class="page-wrapper ..."> ... </div>
            # So 2 closing divs at the end of segment.
            
            r_idx = segment.rfind('</div>')
            r_idx = segment.rfind('</div>', 0, r_idx) 
            # This should be the start of the </div> for container.
            
            if r_idx != -1:
                # We replace content[start_idx : start_idx + r_idx] with full_abilities_html
                # But we need to be careful about whitespace.
                
                # Let's just use the marker.
                # We will replace the marker with full_abilities_html.
                # AND we will try to remove the static cards.
                # If we just prepend, we have 6 cards.
                
                # Let's assume the static cards are exactly as in the template file we read.
                # If we read the template file fresh, we know its content.
                # We can try to identify the block of static cards in the template string.
                pass
                
            # Let's try to be robust. 
            # We will use regex to remove all <div class="ability-card">...</div> blocks? 
            # No, regex is bad for HTML.
            
            # Let's just use the marker and cut until the known footer of the page container.
            # The container ends with:
            #         </div>
            #     </div>
            # 
            #     <!-- 第四页
            
            end_of_cards_idx = content.rfind('</div>', 0, next_page_idx) # page-wrapper end
            end_of_cards_idx = content.rfind('</div>', 0, end_of_cards_idx) # container end
            
            if start_idx != -1 and end_of_cards_idx != -1:
                # Replace everything between marker and container end
                prefix = content[:start_idx]
                suffix = content[end_of_cards_idx:]
                content = prefix + full_abilities_html + "\n" + suffix

    # Output path
    if not out_path:
        os.makedirs(DEFAULT_OUT_DIR, exist_ok=True)
        name = safe_filename(data.get("姓名", "unknown"))
        ts_file = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{name}_{ts_file}.html"
        out_path = os.path.join(DEFAULT_OUT_DIR, filename)
    else:
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)
        
    print(f"HTML Generated: {out_path}")
    return out_path

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", required=True, help="Path to JSON data file")
    parser.add_argument("--out", help="Path to output HTML file")
    parser.add_argument("--template", default=DEFAULT_TEMPLATE, help="Path to HTML template")
    args = parser.parse_args()
    
    generate_html(args.json, args.out, args.template)
