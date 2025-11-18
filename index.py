import re
import json
import re
from typing import List, Dict, Any
from aiClient import get_ai_response
from bookModel import insert_data

def split_chapters(text):
    # ✅ 严格匹配：以任意字符开头，但必须包含「章 」或「节 」（中文空格或英文空格均可）
    # 且「章」「节」字后面必须紧跟一个空白字符（空格/全角空格/\t），再跟标题文字
    # 正则说明：
    #   ^\s*              行首可有空白
    #   .*?               非贪婪匹配前缀（如“第1”、“第三”、“2.3”等）
    #   [章节]            必须是“章”或“节”
    #   [\s\u3000]+       后跟至少一个空白（\s=英文空格/t/n/r/f，\u3000=中文全角空格）
    #   .+?               标题正文（非贪婪）
    #   $                 行尾结束（确保整行为标题）
    title_pattern = re.compile(
        r'^\s*.*?[章节][\s\u3000]+.+?$',
        re.MULTILINE | re.UNICODE
    )
    
    lines = text.splitlines()
    chapters = []
    current_title = ""
    current_content_lines = []

    for line in lines:
        stripped_line = line.rstrip()  # 仅去除右侧空格（保留缩进风格）
        # 严格检查：是否含「章 」或「节 」+ 至少一个空格
        if title_pattern.match(line):
            # 保存上一章
            if current_title or current_content_lines:
                chapters.append({
                    "title": current_title,
                    "content": "\n".join(current_content_lines).strip()
                })
            # 开启新章节
            current_title = stripped_line
            current_content_lines = []
        else:
            current_content_lines.append(line)

    # 保存最后一章
    if current_title or current_content_lines:
        chapters.append({
            "title": current_title,
            "content": "\n".join(current_content_lines).strip()
        })

    return chapters


# ====== 配置你的分类体系（与你提供的一致）======
TAGS = [
    "敏感期-秩序", "敏感期-语言", "敏感期-动作", "敏感期-感官",
    "敏感期-细小事物", "敏感期-社会规范",
    "多元智能-语言", "多元智能-逻辑数学", "多元智能-空间",
    "多元智能-身体动觉", "多元智能-音乐", "多元智能-人际",
    "多元智能-内省", "多元智能-自然观察"
]

CATEGORIES = [
    "大运动", "精细动作", "语言", "适应能力", "社会行为", "健康", "科学", "艺术", "其他"
]

AGES = [
    "0-3月", "3-6月", "6-9月", "9-12月", "12-15月", "15-18月",
    "18-24月", "24-30月", "30-36月", "36-48月", "48-60月", "60-72月"
]

# # ———— 固定部分：System Message ————
# SYSTEM_PROMPT = f"""你是一位专业的儿童发展分析师，专注于0-6岁儿童的敏感期与多元智能发展评估。

# ### 分类体系（必须严格从以下列表中选择，禁止新增、缩写或改写）：
# 1. **标签（tags）**：
# {json.dumps(TAGS, ensure_ascii=False)}

# 2. **类别（categories）**：
# {json.dumps(CATEGORIES, ensure_ascii=False)}

# 3. **月龄阶段（ages）**：
# {json.dumps(AGES, ensure_ascii=False)}

# ### 输出规则：
# - 仅输出一个 JSON 对象，字段为：{{"tags": [...], "categories": [...], "ages": [...], "summary":...}}  
# - 所有值必须是上述列表中的字符串，支持多选，无匹配时返回空数组 `[]`  
# - 仅当文本**明确描述行为、能力或年龄特征**时才标注（例如：“排列积木”→秩序；“说双词句”→18-24月）  
# - 禁止编造、推测或补充列表外内容。"""


def handle_txt():
    # 使用示例
    with open("book.txt", "r", encoding="utf-8") as f:
        text = f.read()

    chapters = split_chapters(text)
    for i, ch in enumerate(chapters, 1):
        if ch['title'] == '':
            continue

        print(f"--- {ch['title']} ---")

        result_data = get_ai_response(ch["content"])
        print(result_data)

        tags_json = json.dumps(result_data.get('points', []), ensure_ascii=False)                                                 
        categories_json = json.dumps(result_data.get('categories', []), ensure_ascii=False)                                         
        ages_json = json.dumps(result_data.get('ages', []), ensure_ascii=False)                                                     
        summary = result_data.get('summary', '')                                                                
        insert_data("我们如何思维", ch["title"], summary, ch["content"], tags_json, categories_json, ages_json)


if __name__ == "__main__":
    handle_txt()