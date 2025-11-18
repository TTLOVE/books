#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import os
import json
from aiClient import get_ai_response

def split_chapters_by_pattern(text):
    """
    根据"第一章\n人类悲伤的原型"格式切分章节
    章节编号和章节名称分别在不同行
    """
    lines = text.splitlines()
    chapters = []
    current_title = ""
    current_content_lines = []

    # 匹配章节编号格式，如"第一章"、"第二章"等（单独一行）
    chapter_number_pattern = re.compile(
        r'^\s*第[零一二三四五六七八九十百千万\d]+[章节]\s*$',
        re.UNICODE
    )

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        if chapter_number_pattern.match(line):
            # 检查下一行是否为章节标题
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                # 如果下一行非空且不是另一个章节编号，则认为是章节标题
                if next_line and not chapter_number_pattern.match(next_line):
                    # 保存上一章节（如果有内容）
                    if current_title or current_content_lines:
                        chapters.append({
                            "title": current_title,
                            "content": "\n".join(current_content_lines).strip()
                        })
                    
                    # 设置新章节标题，跳过章节编号和标题两行
                    current_title = next_line
                    i += 2  # 跳过章节编号行和标题行
                    current_content_lines = []
                    continue
                else:
                    # 如果下一行是另一个章节编号或为空，则当前行可能只是普通内容
                    current_content_lines.append(lines[i])
            else:
                # 如果当前行是最后一条且没有下一行标题，则可能只是普通内容
                current_content_lines.append(lines[i])
            i += 1
        else:
            # 不是章节编号行，添加到当前内容
            current_content_lines.append(lines[i])
            i += 1

    # 添加最后一章节
    if current_title or current_content_lines:
        chapters.append({
            "title": current_title or "前言",
            "content": "\n".join(current_content_lines).strip()
        })

    return chapters


def extract_text_from_docx(file_path):
    """
    从 DOCX 文件中提取文本内容
    """
    try:
        import zipfile
        import xml.etree.ElementTree as ET
        
        with zipfile.ZipFile(file_path, 'r') as docx_zip:
            # 读取主文档内容
            content_xml = docx_zip.read('word/document.xml')
            tree = ET.fromstring(content_xml)
            
            # 定义命名空间
            namespaces = {
                'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
            }
            
            # 提取所有段落文本
            paragraphs = []
            for paragraph in tree.iterfind('.//w:p', namespaces):
                texts = []
                for text_elem in paragraph.iterfind('.//w:t', namespaces):
                    if text_elem is not None and text_elem.text:
                        texts.append(text_elem.text)
                if texts:
                    paragraphs.append(''.join(texts))
            
            return '\n'.join(paragraphs)
    except Exception as e:
        print(f"❌ 无法从 DOCX 文件提取文本: {e}")
        return None

def get_title_and_page(title):
    """
    获取标题和页数
    """
    page = 0
    # 匹配标题名称和页数信息,标题可能为：人类悲伤的原型   003，需要获取标题名称和页数信息
    parts = re.split(r'\s+', title.strip(), maxsplit=1)
    if len(parts) > 1:
        title = parts[0]
        page = parts[1]
        page = page.replace('.', '').replace('/', '1')

        # 判断是否存在数字
        if re.search(r'\d', page):
            page = int(page)
        else:
            title = title + " " + page
            page = 0
    else:
        title = re.sub(r'\d+', '', title)

    return title, page

def process_yilian_docx():
    """
    处理依恋三部曲•第二卷分离.docx 文件并输出切分信息
    """
    docx_path = "./依恋三部曲•第二卷分离.docx"
    
    print(f"📖 正在处理文件: {docx_path}")
    
    # 检查文件是否存在
    if not os.path.exists(docx_path):
        print(f"❌ 文件不存在: {docx_path}")
        return
    
    # 从 DOCX 文件提取文本
    print("📖 正在从 DOCX 文件中提取文本...")
    text_content = extract_text_from_docx(docx_path)
    
    if text_content is None:
        print("❌ 无法提取 DOCX 文件内容")
        return
    
    print(f"✅ 成功提取文本，共 {len(text_content)} 个字符")
    
    # 按章节模式切分文档
    print("✂️ 正在按'第一章\\n人类悲伤的原型'格式切分章节...")
    chapters = split_chapters_by_pattern(text_content)

    print(f"✅ 成功识别出 {len(chapters)} 个章节")
    print("=" * 80)
    print("📋 章节切分结果:")
    print("=" * 80)
    
    group_chapters = {}
    index = 0
    current_page = 0
    for i, chapter in enumerate(chapters, 1):
        if chapter['title'] == "":
            continue

        title, page = get_title_and_page(chapter['title'])
        if title not in group_chapters:
            index += 1
            group_chapters[title] = {
                "title":  f"第 {index} 章: {title}",
            }

        if page > 0:
            current_page = page
        else:
            current_page = current_page + 2

        title = group_chapters[title]
        print(title['title'], current_page)
        get_ai_response_and_insert_data(title['title'], chapter['content'], current_page)

    
    # 输出统计信息
    print(f"\n📊 总计: {len(chapters)} 个章节")
    total_chars = sum(len(ch['content']) for ch in chapters)
    print(f"总内容字符数: {total_chars}")
    
    # print("\n—" * 80)
    # print("所有章节标题列表:")
    # print("—" * 80)
    # for i, chapter in enumerate(chapters, 1):
    #     print(f"{i:3d}. {chapter['title']}")

def get_ai_response_and_insert_data(title, content, page):
    try:
        result_data = get_ai_response(content)
        if len(result_data) == 0:
            print("result_data is empty")
            return

        # print(result_data)
        batch_data = []
        # Process the new response format: result_data is a list of objects
        for item in result_data:
            content = item.get("content", "")
            relevant_age_group = item.get("relevant_age_group", "")
            relevant_domain = item.get("relevant_domain", "其他")
            tags = item.get("tags", [])

            # Convert single values to lists if needed
            if isinstance(relevant_age_group, str):
                relevant_age_group = (
                    [relevant_age_group] if relevant_age_group else []
                )
            if isinstance(relevant_domain, str):
                relevant_domain = [relevant_domain] if relevant_domain else []

            tags_json = json.dumps(tags, ensure_ascii=False)
            categories_json = json.dumps(relevant_domain, ensure_ascii=False)
            ages_json = json.dumps(relevant_age_group, ensure_ascii=False)
            summary = content  # Use the content as summary since that's where the main text is

            # Add data to batch list instead of inserting individually
            batch_data.append(
                (
                    "依恋三部曲•第二卷分离",
                    title,
                    summary,
                    "",
                    tags_json,
                    categories_json,
                    ages_json,
                    page,
                )
            )

    except json.JSONDecodeError as e:
        print(f"❌ JSON 解析错误 for chapter {i}: {e}")
        print(f"AI response was: {result_data}")
        return
    except Exception as e:
        print(f"❌ 处理章节 {title} 时发生错误: {e}")
        return

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


if __name__ == "__main__":
    process_yilian_docx()