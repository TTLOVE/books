import re
import json
from aiClient import get_ai_response
from bookModel import insert_data

def preprocess_textile(textile_src: str) -> str:
    """
    将 Textile 源码 → 干净标题行（符合“章/节 + 空格”规则）
    修复：跨行标题、h1./h2. 标记、无空格问题
    """
    # Step 1: 移除 Textile 行内标记（calibre2, alt 等无用属性）
    # 但要小心处理 h1/h2/h3 标签的属性部分
    text = re.sub(r'\(calibre\d+\)', '', textile_src)
    text = re.sub(r'\(alt\)', '', text)
    
    # 处理 h1/h2/h3 标签中的 title# 属性 - 移除它们但保持标签结构
    def remove_title_attr(match):
        h_part = match.group(1)      # h1, h2, 或 h3
        content = match.group(2)     # 括号内的完整内容
        # 移除 title# 属性部分: title#...)
        clean_content = re.sub(r'title#[^)]*\)', '', content)
        return f'{h_part}({clean_content})'

    # 应用标题属性移除
    text = re.sub(r'(h[1-3])\(([^)]*)\)', remove_title_attr, text)

    # Step 2: 合并跨行标题（h1. 标题\n副标题 → h1. 标题 副标题）
    # 匹配：h[1-3](...)标题\n（非空、非h开头、非div/images/---开头的行）
    text = re.sub(
        r'(h[1-3]\([^)]*\)\.\s*[^\n]+)\n([^\n]+)',
        lambda m: m.group(1) + ' ' + m.group(2) if not re.match(r'(h[1-3]|div|images|---)', m.group(2).strip()) else m.group(0),
        text
    )

    # Step 3: 将 h1./h2. → 模拟“章”“节”格式（适配您的切分器）
    # PART X → “第X章”；中文标题保留；罗马数字 → “第Y节”
    def fix_heading(match):
        level = match.group(1)
        content = match.group(2).strip()
        
        # 尝试提取 PART 数字
        part_match = re.search(r'PART\s+(\d+)', content, re.IGNORECASE)
        if part_match:
            num = part_match.group(1)
            return f"第{num}章 {content.replace('PART '+num, '').strip()}"
        
        # 尝试罗马数字 → 节
        if re.match(r'^[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]+$', content):
            roman_map = {"Ⅰ":"一", "Ⅱ":"二", "Ⅲ":"三", "Ⅳ":"四", "Ⅴ":"五",
                         "Ⅵ":"六", "Ⅶ":"七", "Ⅷ":"八", "Ⅸ":"九", "Ⅹ":"十"}
            cn_num = ''.join(roman_map.get(c, c) for c in content)
            return f"第{cn_num}节 {content}"
        
        # 普通标题：补“章”字（如“中文版序” → “前言章 中文版序”）
        if level == "1":
            return f"章节 {content}"  # 用“章节”兼容您的“章 空格”规则
        else:
            return f"节 {content}"    # 用“节 ”开头，确保有空格

    text = re.sub(r'h([1-3])\([^)]*\)\.\s*(.+?)(?=\n|\Z)', fix_heading, text, flags=re.DOTALL)

    # Step 4: 确保“章”“节”后有空格（最终兜底）
    text = re.sub(r'([章节])([^章\n\s])', r'\1 \2', text)

    return text

def split_chapters_robust(text: str):
    lines = text.splitlines()
    chapters = []
    current_title = ""
    current_content_lines = []

    # 允许： "章节 "、"节 "、"第X章 "、"第X节 "
    title_pattern = re.compile(
        r'^\s*(?:章节|节|第[零一二三四五六七八九十\d]+[章节])\s+.+$',
        re.UNICODE
    )

    for line in lines:
        stripped = line.strip()
        if not stripped:
            current_content_lines.append(line)
            continue

        if title_pattern.match(line):
            # 保存上一章
            if current_title or current_content_lines:
                chapters.append({
                    "title": current_title,
                    "content": "\n".join(current_content_lines).strip()
                })
            # 新章节（去除前缀“章节”/“节”，仅留真实标题）
            clean_title = re.sub(r'^\s*(?:章节|节)\s*', '', stripped)
            clean_title = re.sub(r'^第[零一二三四五六七八九十\d]+[章节]\s*', '', clean_title)
            current_title = clean_title.strip()
            current_content_lines = []
        else:
            current_content_lines.append(line)

    # 保存最后一章
    if current_title or current_content_lines:
        chapters.append({
            "title": current_title or "前言",
            "content": "\n".join(current_content_lines).strip()
        })

    return chapters


def mengtai():
    # 读取您上传的文本（已复制到变量）
    with open("./textiles/蒙台梭利早期教育法.textile", encoding="utf-8") as f:
        textile_src = f.read()

    # 预处理 + 切分
    clean_text = preprocess_textile(textile_src)
    chapters = split_chapters_robust(clean_text)

    print(f"✅ 成功切分 {len(chapters)} 章")
    for i, ch in enumerate(chapters, 1):
        print(f"[{i}] {ch['title']}... {len(ch['content'])}字")
        result_data = get_ai_response(ch["content"])
        print(result_data)
        if len(result_data) == 0:
            continue

        tags_json = json.dumps(result_data.get('points', []), ensure_ascii=False)                                                 
        categories_json = json.dumps(result_data.get('categories', []), ensure_ascii=False)                                         
        ages_json = json.dumps(result_data.get('ages', []), ensure_ascii=False)                                                     
        summary = result_data.get('summary', '')                                                                
        insert_data("蒙台梭利早期教育法", ch["title"], summary, "", tags_json, categories_json, ages_json)

def mengtai_new():
    # 读取您上传的文本（已复制到变量）
    with open("./textiles/蒙台梭利早期教育法.textile", encoding="utf-8") as f:
        textile_src = f.read()

    # 预处理 + 切分
    clean_text = preprocess_textile(textile_src)
    chapters = split_chapters_robust(clean_text)

    print(f"✅ 成功切分 {len(chapters)} 章")
    
    # Collect data for batch insertion
    
    for i, ch in enumerate(chapters, 1):
        print(f"[{i}] {ch['title']}... {len(ch['content'])}字")
        try:
            result_data = get_ai_response(ch["content"])
            if len(result_data) == 0:
                print("result_data is empty")
                continue

            batch_data = []
            # Process the new response format: result_data is a list of objects
            for item in result_data:
                content = item.get('content', '')
                relevant_age_group = item.get('relevant_age_group', '')
                relevant_domain = item.get('relevant_domain', '其他')
                tags = item.get('tags', [])
                
                # Convert single values to lists if needed
                if isinstance(relevant_age_group, str):
                    relevant_age_group = [relevant_age_group] if relevant_age_group else []
                if isinstance(relevant_domain, str):
                    relevant_domain = [relevant_domain] if relevant_domain else []
                
                tags_json = json.dumps(tags, ensure_ascii=False)                                                 
                categories_json = json.dumps(relevant_domain, ensure_ascii=False)                                         
                ages_json = json.dumps(relevant_age_group, ensure_ascii=False)                                                     
                summary = content  # Use the content as summary since that's where the main text is
                
                # Add data to batch list instead of inserting individually
                batch_data.append(("蒙台梭利早期教育法", ch["title"], summary, "", tags_json, categories_json, ages_json))

        except json.JSONDecodeError as e:
            print(f"JSON 解析错误 for chapter {i}: {e}")
            print(f"AI response was: {result_data}")
            continue
        except Exception as e:
            print(f"处理章节 {i} 时发生错误: {e}")
            continue

        # Perform batch insertion
        if batch_data:
            from bookModel import batch_insert_data
            success = batch_insert_data(batch_data)
            if success:
                print(f"✅ 批量插入 {len(batch_data)} 条记录成功")
            else:
                print("❌ 批量插入失败")
        else:
            print("⚠️ 没有有效数据需要插入")




def yilian():
    # 读取依恋三部曲•第二卷分离.textile文件
    with open("./textiles/依恋三部曲•第二卷分离.textile", encoding="utf-8") as f:
        textile_src = f.read()

    # 预处理 + 切分
    clean_text = preprocess_textile(textile_src)
    chapters = split_chapters_robust(clean_text)

    print(f"✅ 成功切分 {len(chapters)} 章")
    for i, ch in enumerate(chapters, 1):
        print(f"[{i}] {ch['title']}... {len(ch['content'])}字")
        # result_data = get_ai_response(ch["content"])
        # print(result_data)

        # tags_json = json.dumps(result_data.get('points', []), ensure_ascii=False)                                                 
        # categories_json = json.dumps(result_data.get('categories', []), ensure_ascii=False)                                         
        # ages_json = json.dumps(result_data.get('ages', []), ensure_ascii=False)                                                     
        # summary = result_data.get('summary', '')                                                                
        # insert_data("依恋三部曲•第二卷分离", ch["title"], summary, "", tags_json, categories_json, ages_json)


if __name__ == "__main__":
    mengtai_new()