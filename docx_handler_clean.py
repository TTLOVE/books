#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import os

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
        line = lines[i].strip()
        
        # 检查是否是章节编号行
        if chapter_number_pattern.match(line):
            # 检查下一行是否为标题内容
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                # 如果下一行非空且不是另一个章节编号，则将其作为章节标题
                if next_line and not chapter_number_pattern.match(next_line):
                    # 保存上一章节
                    if current_title or current_content_lines:
                        chapters.append({
                            "title": current_title,
                            "content": "\n".join(current_content_lines).strip()
                        })
                    
                    # 设置新章节标题，跳过编号和标题两行
                    current_title = next_line
                    i += 2
                    current_content_lines = []
                    continue
        
        # 添加当前行到章节内容
        current_content_lines.append(lines[i])
        i += 1

    # 添加最后一章节
    if current_title or current_content_lines:
        chapters.append({
            "title": current_title or "前言",
            "content": "\n".join(current_content_lines).strip()
        })

    return chapters

def process_docx_file(file_path):
    """
    处理DOCX文件并输出切分信息
    """
    print(f"正在处理文件: {file_path}")
    
    # 检查文件是否存在
    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        return
    
    # 读取文件内容
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 切分章节
    chapters = split_chapters_robust(content)
    
    # 输出结果
    print(f"✅ 成功识别 {len(chapters)} 个章节")
    print("=" * 60)
    print("切分结果:")
    for i, chapter in enumerate(chapters, 1):
        title = chapter['title']
        content_preview = chapter['content'][:100] + "..." if len(chapter['content']) > 100 else chapter['content']
        print(f"\n第{i}章:")
        print(f"  标题: {title}")
        print(f"  内容预览: {content_preview}")
        print(f"  内容长度: {len(chapter['content'])} 字符")
    
    print("\n" + "=" * 60)
    print("所有章节标题:")
    for i, chapter in enumerate(chapters, 1):
        print(f"  {i:3d}. {chapter['title']}")

def main():
    docx_path = "./依恋三部曲•第二卷分离.docx"
    process_docx_file(docx_path)

if __name__ == "__main__":
    main()