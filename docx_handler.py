#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import json
import os

# Import database functions but handle import error gracefully
try:
    from bookModel import insert_data, batch_insert_data
except ImportError:
    print("❌ 无法导入数据库模块，将跳过数据插入功能")
    insert_data = None
    batch_insert_data = None
except Exception as e:
    print(f"❌ 数据库连接错误: {e}")
    insert_data = None
    batch_insert_data = None

from aiClient import get_ai_response

def split_chapters_robust(text):
    """
    从文本中按章节切分内容
    适用于处理从 DOCX 文件提取的文本
    按照"第一章\n人类悲伤的原型"格式进行切分
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
            # 如果当前章节有内容，先保存当前章节
            if current_title or current_content_lines:
                chapters.append({
                    "title": current_title,
                    "content": "\n".join(current_content_lines).strip()
                })
            
            # 检查下一行是否为章节标题
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                # 如果下一行非空且不是另一个章节编号，则认为是章节标题
                if next_line and not chapter_number_pattern.match(next_line):
                    current_title = next_line
                    i += 2  # 跳过章节编号行和标题行
                    current_content_lines = []
                    continue
                else:
                    # 如果下一行是另一个章节编号或为空，则当前行可能是普通内容
                    current_content_lines.append(lines[i])
            else:
                # 如果当前行是最后一条且没有下一行标题，则可能只是普通内容
                current_content_lines.append(lines[i])
            i += 1
        else:
            # 不是章节编号行，添加到当前内容
            current_content_lines.append(lines[i])
            i += 1

    # 保存最后一章
    if current_title or current_content_lines:
        chapters.append({
            "title": current_title or "前言",
            "content": "\n".join(current_content_lines).strip()
        })

    return chapters


def extract_text_from_docx(file_path):
    """
    从 DOCX 文件中提取文本内容
    使用 zipfile 直接读取 DOCX 内容 (DOCX 实际上是 ZIP 格式的 XML 文档)
    """
    try:
        import zipfile
        import xml.etree.ElementTree as ET
        
        with zipfile.ZipFile(file_path, 'r') as docx_zip:
            # 读取文档内容
            content_xml = docx_zip.read('word/document.xml')
            tree = ET.fromstring(content_xml)
            
            # 定义命名空间
            namespaces = {
                'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
                'xml': 'http://www.w3.org/XML/1998/namespace'
            }
            
            # 提取段落文本
            paragraphs = []
            for para in tree.iterfind('.//w:p', namespaces):
                text_elements = para.iterfind('.//w:t', namespaces)
                para_text = ''.join([elem.text for elem in text_elements if elem.text])
                paragraphs.append(para_text)
            
            return '\n'.join(paragraphs)
    except ImportError:
        print("❌ 未安装 python-docx，请运行: pip install python-docx")
        print("📝 使用内置方法读取 DOCX 文件...")
        # 尝试直接方法
        return extract_text_from_docx_builtin(file_path)
    except Exception as e:
        print(f"❌ 读取 DOCX 文件时出错: {e}")
        return None


def extract_text_from_docx_builtin(file_path):
    """
    使用内置方法从 DOCX 文件中提取文本内容
    DOCX 文件是 ZIP 格式，包含 XML 文件
    """
    try:
        import zipfile
        import xml.etree.ElementTree as ET
        
        with zipfile.ZipFile(file_path, 'r') as docx_zip:
            # 读取文档内容
            content_xml = docx_zip.read('word/document.xml')
            tree = ET.fromstring(content_xml)
            
            # 定义命名空间
            namespaces = {
                'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
                'xml': 'http://www.w3.org/XML/1998/namespace'
            }
            
            # 提取段落文本
            paragraphs = []
            for para in tree.iterfind('.//w:p', namespaces):
                text_elements = para.iterfind('.//w:t', namespaces)
                para_text = ''.join([elem.text for elem in text_elements if elem.text])
                if para_text.strip():  # 只添加非空段落
                    paragraphs.append(para_text)
            
            return '\n'.join(paragraphs)
    except Exception as e:
        print(f"❌ 使用内置方法读取 DOCX 文件时出错: {e}")
        return None


def yilian_docx():
    """
    处理依恋三部曲•第二卷分离.docx 文件的主函数
    """
    docx_path = "./依恋三部曲•第二卷分离.docx"
    
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

    # 切分章节
    print("✂️  正在进行章节切分...")
    chapters = split_chapters_robust(text_content)

    print(f"✅ 成功切分 {len(chapters)} 个章节")
    for i, ch in enumerate(chapters, 1):
        print(f"[{i}] {ch['title']}... {len(ch['content'])} 字符")


if __name__ == "__main__":
    yilian_docx()