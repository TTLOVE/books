#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import os
import json
from aiClient import get_ai_response
import asyncio
from concurrent.futures import ThreadPoolExecutor

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
    chapter_index = 0
    current_chapter_index = 0
    current_page = 0
    content = ""
    
    # Store the tasks to be run concurrently
    ai_tasks = []
    
    for i, chapter in enumerate(chapters, 1):
        if chapter['title'] == "":
            continue

        title, page = get_title_and_page(chapter['title'])
        if title not in group_chapters:
            chapter_index += 1
            group_chapters[title] = {
                "title":  f"第 {chapter_index} 章: {title}",
            }

        if page > 0:
            current_page = page
        else:
            current_page = current_page + 2

        title = group_chapters[title]
        print(title['title'], current_page)

        # 章变化,则先将AI任务添加到列表,然后清空内容
        if current_chapter_index != chapter_index and current_chapter_index != 0:
            print(f"章变化,准备发送内容到AI: {current_page}")
            if current_page >= 95:
                ai_tasks.append((chapter_index - 1, content))
            content = chapter['content']
        else:
            content = content + chapter['content']

        current_chapter_index = chapter_index
    
    # Add the last content if there's any
    if content and current_chapter_index > 0:
        print(f"准备发送最后一部分内容到AI: {current_page}")
        if current_page >= 95:
            ai_tasks.append((current_chapter_index, content))
    
    # Execute all AI tasks concurrently
    if ai_tasks:
        print(f"🚀 开始并发处理 {len(ai_tasks)} 个AI任务...")
        with ThreadPoolExecutor() as executor:
            # Submit all tasks
            futures = [executor.submit(get_ai_response_and_insert_data, chapter_idx, cont) 
                      for chapter_idx, cont in ai_tasks]
            
            # Wait for all tasks to complete
            for future in futures:
                future.result()  # This ensures any exceptions are raised
        print("✅ 所有AI任务完成")

    
    # 输出统计信息
    print(f"\n📊 总计: {len(chapters)} 个章节")
    total_chars = sum(len(ch['content']) for ch in chapters)
    print(f"总内容字符数: {total_chars}")
    
    # print("\n—" * 80)
    # print("所有章节标题列表:")
    # print("—" * 80)
    # for i, chapter in enumerate(chapters, 1):
    #     print(f"{i:3d}. {chapter['title']}")

def get_ai_response_and_insert_data(captcher: int, content):
    try:
        result_data = get_ai_response(captcher, content)
        if len(result_data) == 0:
            print("result_data is empty")
            return

        # print("解释后的数据:", result_data)
        batch_data = []
        
        # """ {
        #     "knowledge_id": "K_ATT_1_0-72月_045",
        #     "relevant_age_group": ["0-3月", "3-6月", "6-9月", "9-12月", "12-15月", "15-18月", "18-24月", "24-30月", "30-36月", "36-48月", "48-60月", "60-72月"],
        #     "original_text_segment": "对于一个幼儿或者成人来说，他是处于一种安全状态、焦虑状态还是忧郁状态，很大程度上是取决于他的首要依恋对象是否是可接近的、可到达的和有反应的。",
        #     "text_location": "第1章第24页第2段",
        #     "extraction_context": "论述依恋对象可接近性对情绪状态的核心影响",
        #     "inference_level": "理论推论",
        #     "extraction_basis": "从理论论述中推理出依恋对象可接近性和反应性是决定幼儿情绪状态的关键因素，适用于整个儿童期",
        #     "confidence_level": "高置信度",
        #     "original_age_reference": "幼儿或成人",
        #     "content_summary": "依恋对象可接近性和反应性是决定幼儿情绪状态（安全、焦虑、忧郁）的关键因素",
        #     "source_document": "依恋三部曲・第二卷分离",
        #     "development_aspect": ["行为表现", "影响因素"],
        #     "domain_category": ["社会行为"],
        #     "sensitive_period": {
        #     "category": "人际",
        #     "manifestation": "对依恋对象可接近性敏感，影响整体情绪健康"
        #     },
        #     "intelligence_development": {
        #     "category": "内省",
        #     "manifestation": "能感知依恋对象可用性并调节情绪"
        #     },
        #     "evidence_quality": "强证据",
        #     "extraction_notes": "基于理论总结，年龄范围从幼儿期扩展到整个儿童期"
        # }"""

        # Process the new response format: result_data is a list of objects
        for item in result_data:
            relevant_age_group = item.get("relevant_age_group", "")
            original_text_segment = item.get("original_text_segment", "")
            text_location = item.get("text_location", "")
            extraction_context = item.get("extraction_context", "")
            inference_level = item.get("inference_level", "")
            extraction_basis = item.get("extraction_basis", "")
            confidence_level = item.get("confidence_level", "")
            original_age_reference = item.get("original_age_reference", "")
            content_summary = item.get("content_summary", "")
            source_document = item.get("source_document", "")
            development_aspect = item.get("development_aspect", [])
            domain_category = item.get("domain_category", [])
            sensitive_period = item.get("sensitive_period", {})
            intelligence_development = item.get("intelligence_development", {})
            evidence_quality = item.get("evidence_quality", "")
            extraction_notes = item.get("extraction_notes", "")

            # Convert single values to lists if needed
            if isinstance(relevant_age_group, str):
                relevant_age_group = (
                    [relevant_age_group] if relevant_age_group else []
                )
            if isinstance(development_aspect, str):
                development_aspect = [development_aspect] if development_aspect else []
            if isinstance(domain_category, str):
                domain_category = [domain_category] if domain_category else []
            if isinstance(sensitive_period, str):
                sensitive_period = [sensitive_period] if sensitive_period else []
            if isinstance(intelligence_development, str):
                intelligence_development = [intelligence_development] if intelligence_development else []

            relevant_age_group = json.dumps(relevant_age_group, ensure_ascii=False)
            development_aspect = json.dumps(development_aspect, ensure_ascii=False)
            domain_category = json.dumps(domain_category, ensure_ascii=False)
            sensitive_period = json.dumps(sensitive_period, ensure_ascii=False)
            intelligence_development = json.dumps(intelligence_development, ensure_ascii=False)

            # Add data to batch list instead of inserting individually
            batch_data.append(
                (
                    relevant_age_group,
                    original_text_segment,
                    text_location,
                    extraction_context,
                    inference_level,
                    extraction_basis,
                    confidence_level,
                    original_age_reference,
                    content_summary,
                    source_document,
                    development_aspect,
                    domain_category,
                    sensitive_period,
                    intelligence_development,
                    evidence_quality,
                    extraction_notes,
                )
            )

    except json.JSONDecodeError as e:
        print(f"❌ JSON 解析错误 for chapter: {e}")
        print(f"AI response was: {result_data}")
        return
    except Exception as e:
        print(f"❌ 处理章节 {captcher} 时发生错误: {e}")
        return

    # Perform batch insertion
    if batch_data:
        from bookModel import batch_insert_knowledge

        # print("batch_data: ", batch_data)
        success = batch_insert_knowledge(batch_data)
        if success:
            print(f"✅ 批量插入 {len(batch_data)} 条记录成功")
        else:
            print("❌ 批量插入失败")
    else:
        print("⚠️ 没有有效数据需要插入")


if __name__ == "__main__":
    process_yilian_docx()