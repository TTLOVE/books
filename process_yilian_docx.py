#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import os
import zipfile
import xml.etree.ElementTree as ET

def split_chapters_robust(text):
    """
    根据"第一章\n人类悲伤的原型"格式切分章节
    章节编号和章节名称分别在不同行
    """
    lines = text.splitlines()
    chapters = []
    current_title = ""
    current_content_lines = []

    # 匹配章节编号格式，如"第一章"、"第二章"、"第X章"等
    chapter_number_pattern = re.compile(r'^\s*第[零一二三四五六七八九十百千万\d]+[章节]\s*$')

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # 检查是否是章节编号行
        if chapter_number_pattern.match(stripped):
            # 检查下一行是否为标题内容
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                # 如果下一行非空且不是另一个章节编号，则将其作为章节标题
                if next_line and not chapter_number_pattern.match(next_line):
                    # 保存上一章节（如果有内容）
                    if current_title or current_content_lines:
                        chapters.append({
                            "title": current_title,
                            "content": "\n".join(current_content_lines).strip()
                        })
                    
                    # 设置新章节标题，跳过编号和标题两行
                    current_title = next_line
                    i += 2  # 跳过章节编号行和标题行
                    current_content_lines = []
                    continue
        
        # 添加当前行到章节内容（如果不是章节编号行）
        current_content_lines.append(line)
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
    DOCX 实际上是 ZIP 格式的压缩包，包含 XML 文件
    """
    try:
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

def process_yilian_docx():
    """
    处理依恋三部曲•第二卷分离.docx 文件
    """
    docx_path = "./依恋三部曲•第二卷分离.docx"
    
    print(f"📖 正在从 DOCX 文件中提取文本: {docx_path}")
    
    # 检查文件是否存在
    if not os.path.exists(docx_path):
        print(f"❌ 文件不存在: {docx_path}")
        return
    
    # 从 DOCX 文件提取文本
    text_content = extract_text_from_docx(docx_path)
    
    if text_content is None:
        print("❌ 无法提取 DOCX 文件内容")
        return
    
    print(f"✅ 成功提取文本，共 {len(text_content)} 个字符")
    
    # 按章节模式切分文档
    print("✂️ 正在按'第一章\\n人类悲伤的原型'格式切分章节...")
    chapters = split_chapters_robust(text_content)

    print(f"✅ 成功识别出 {len(chapters)} 个章节")
    print("=" * 80)
    print("📋 章节切分结果:")
    print("=" * 80)
    
    for i, chapter in enumerate(chapters, 1):
        title = chapter['title']
        content_length = len(chapter['content'])
        preview = chapter['content'][:100] + "..." if len(chapter['content']) > 100 else chapter['content']
        
        print(f"\n第 {i:2d} 章:")
        print(f"  标题: {title}")
        print(f"  内容长度: {content_length} 字符")
        print(f"  内容预览: {preview}")
        print("-" * 60)
    
    # 输出统计信息
    print(f"\n📊 总计: {len(chapters)} 个章节")
    total_chars = sum(len(ch['content']) for ch in chapters)
    print(f"总内容字符数: {total_chars}")
    
    print("\n—" * 80)
    print("所有章节标题列表:")
    print("—" * 80)
    for i, chapter in enumerate(chapters, 1):
        print(f"{i:3d}. {chapter['title']}")
    

if __name__ == "__main__":
    process_yilian_docx()