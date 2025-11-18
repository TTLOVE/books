"""
依恋三部曲•第二卷分离 文档高级分块处理
根据指定策略进行语义完整性、案例独立性、实验数据完整性、理论论述连贯性的分块
"""
import re
import json
from aiClient import get_ai_response
from bookModel import insert_data

def preprocess_yilian_textile(textile_src: str) -> str:
    """
    预处理 Textile 源码 → 干净的文本内容
    修复：跨行标题、h1./h2. 标记、无空格问题
    """
    # 移除 Textile 行内标记（calibre2, alt 等无用属性）
    text = re.sub(r'\(calibre\d+\)', '', textile_src)
    text = re.sub(r'\(alt\)', '', text)
    
    # 处理 h1/h2/h3 标签中的 title# 属性
    def remove_title_attr(match):
        h_part = match.group(1)      # h1, h2, 或 h3
        content = match.group(2)     # 括号内的完整内容
        # 移除 title# 属性部分: title#...)
        clean_content = re.sub(r'title#[^)]*\)', '', content)
        return f'{h_part}({clean_content})'

    # 应用标题属性移除
    text = re.sub(r'(h[1-3])\(([^)]*)\)', remove_title_attr, text)

    # 合并跨行标题
    text = re.sub(
        r'(h[1-3]\([^)]*\)\.\s*[^\n]+)\n([^\n]+)',
        lambda m: m.group(1) + ' ' + m.group(2) if not re.match(r'(h[1-3]|div|images|---)', m.group(2).strip()) else m.group(0),
        text
    )

    # 将 h1./h2. → 模拟"章""节"格式
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
        
        # 普通标题：补"章"字
        if level == "1":
            return f"章节 {content}"
        else:
            return f"节 {content}"

    text = re.sub(r'h([1-3])\([^)]*\)\.\s*(.+?)(?=\n|\Z)', fix_heading, text, flags=re.DOTALL)

    # 确保"章""节"后有空格
    text = re.sub(r'([章节])([^章\n\s])', r'\1 \2', text)

    return text


def split_by_advanced_strategy(text: str, max_chunk_size: int = 900):
    """
    根据高级策略对文本进行分块：
    - 语义完整性分块: 保证发展描述的完整上下文
    - 案例独立分块: 儿童个案描述单独成块
    - 实验数据完整分块: 实验设计-过程-结果保持一体
    - 理论论述连贯分块: 理论推导保持逻辑连贯
    - 最大长度: 800-1000 tokens
    """
    # 识别案例研究标记 - 更精确的案例识别
    case_study_keywords = [
        '案例', '个案', '病例', '患者', '儿童', '小孩', '小男孩', '小女孩', 
        '孩子', '来访者', '病患', '研究对象', '实验对象', '观察对象', 
        '记录显示', '观察结果', '临床表现', '表现', '行为', '反应',
        '托尼', '吉姆', '雪莉', '雷吉'  # 具体案例名称
    ]
    
    # 识别章节标题
    chapter_pattern = re.compile(
        r'^\s*(?:章节|节|第[零一二三四五六七八九十\d]+[章节])\s+.+$',
        re.MULTILINE | re.UNICODE
    )
    
    # 识别理论论述段落
    theory_keywords = [
        '理论', '论述', '推导', '假设', '模型', '框架', '概念', '定义', 
        '观点', '认为', '提出', '发展', '研究表明', '研究指出', '指出',
        '依恋理论', '分离焦虑', '安全依恋', '焦虑型依恋'
    ]
    
    # 识别实验相关部分
    experiment_keywords = [
        '实验', '研究', '观察', '数据', '结果', '方法', '过程', '设计', 
        '调查', '分析', '记录', '测量', '测试', '评估', '实验结果', 
        '研究结果', '观察研究', '临床观察', '数据分析'
    ]
    
    # 按段落分割
    paragraphs = text.split('\n\n')
    
    chunks = []
    current_chunk = ""
    
    # 遍历所有段落
    i = 0
    while i < len(paragraphs):
        paragraph = paragraphs[i].strip()
        if not paragraph:
            i += 1
            continue
        
        # 检查是否是新章节开始
        if chapter_pattern.match(paragraph):
            if current_chunk.strip():
                if len(current_chunk) > 50:  # 避免过小的块
                    chunks.append(current_chunk.strip())
                current_chunk = ""
            current_chunk += paragraph + "\n\n"
            i += 1
            continue
        
        # 检测是否包含案例内容
        is_case_study = any(keyword in paragraph for keyword in case_study_keywords)
        
        # 案例独立分块：儿童个案描述单独成块
        if is_case_study:
            # 收集完整的案例描述（可能跨越多个段落）
            case_chunk = paragraph
            j = i + 1
            
            # 查找案例的边界 - 直到遇到新主题或章节
            while j < len(paragraphs):
                next_para = paragraphs[j].strip()
                if not next_para:
                    j += 1
                    continue
                
                # 检查下一个段落是否仍属于同一案例
                next_is_case = any(keyword in next_para for keyword in case_study_keywords)
                next_is_chapter = chapter_pattern.match(next_para)
                
                # 检查是否是案例的延续（有案例相关关键词或与案例相关的描述）
                is_case_continuation = (
                    next_is_case or 
                    any(keyword in next_para for keyword in ['他', '她', '这个孩子', '该案例', '该个案', '在这种情况'])
                )
                
                # 如果是新章节或明显非案例内容，则停止添加到当前案例
                if next_is_chapter or (not is_case_continuation and 
                                      all(kw not in next_para for kw in case_study_keywords + ['他', '她', '这个孩子', '该案例', '该个案', '在这种情况']) and
                                      len(next_para) > 100 and  # 长段落更可能是新主题
                                      any(keyword in next_para for keyword in ['理论', '研究表明', '总结', '结论', '分析'])):
                    break
                
                # 添加到案例块中
                case_chunk += "\n\n" + next_para
                j += 1
            
            # 保存案例块
            if len(case_chunk) > 50:
                chunks.append(case_chunk.strip())
            
            # 跳转到下一个非案例段落
            i = j
            continue
        
        # 非案例内容处理
        paragraph_size = len(paragraph)
        current_size = len(current_chunk)
        
        # 检查是否是实验相关
        is_experiment = any(keyword in paragraph for keyword in experiment_keywords)
        
        # 检查是否是理论相关
        is_theory = any(keyword in paragraph for keyword in theory_keywords)
        
        # 语义完整性：检测发展描述的上下文
        is_development_context = any(keyword in paragraph for keyword in 
                                   ['发展', '过程', '阶段', '演变', '演进', '成长', 
                                    '变化', '进展', '影响', '作用', '效应', '关系',
                                    '依恋', '母婴', '分离', '焦虑', '恐惧', '安全'])
        
        # 实验数据完整分块：保持实验设计-过程-结果保持一体
        if is_experiment:
            # 检查是否应该开始新的实验块
            has_experiment_content = any(keyword in current_chunk for keyword in experiment_keywords)
            
            # 如果当前块包含非实验内容，先保存当前块，然后开始新实验块
            if current_chunk.strip() and not has_experiment_content:
                chunks.append(current_chunk.strip())
                current_chunk = paragraph + "\n\n"
            # 如果当前块已经在包含实验内容，继续添加
            elif current_chunk.strip() and has_experiment_content:
                # 检查当前实验块是否过大
                if current_size + paragraph_size > max_chunk_size:
                    # 如果实验相关的段落，即使超过长度也尽量保持在一起
                    if any(keyword in paragraph for keyword in ['方法', '结果', '数据', '观察']):
                        current_chunk += paragraph + "\n\n"
                    else:
                        chunks.append(current_chunk.strip())
                        current_chunk = paragraph + "\n\n"
                else:
                    current_chunk += paragraph + "\n\n"
            # 如果没有当前块，开始新的实验块
            else:
                current_chunk = paragraph + "\n\n"
        
        # 理论论述连贯分块：保持逻辑推导连贯
        elif is_theory or is_development_context:
            # 检查当前块是否包含理论或发展内容
            has_theory_content = any(keyword in current_chunk for keyword in theory_keywords)
            has_dev_content = any(keyword in current_chunk for keyword in 
                                 ['发展', '过程', '阶段', '演变', '演进', '成长', 
                                  '变化', '进展', '影响', '作用', '效应', '关系',
                                  '依恋', '母婴', '分离', '焦虑', '恐惧', '安全'])
            
            should_continue_theory = has_theory_content or has_dev_content
            
            # 如果当前块包含非理论/非发展内容，先保存当前块，然后开始新理论块
            if current_chunk.strip() and not should_continue_theory:
                chunks.append(current_chunk.strip())
                current_chunk = paragraph + "\n\n"
            # 如果当前块已经在包含理论/发展内容，继续添加
            elif current_chunk.strip() and should_continue_theory:
                # 对于理论内容，即使略微超过长度限制也尽量保持逻辑连贯
                if current_size + paragraph_size > max_chunk_size:
                    # 检查是否是理论的重要组成部分，保持连贯性
                    if any(keyword in paragraph for keyword in ['因此', '所以', '由此', '这表明', '可以看出', '基于']):
                        current_chunk += paragraph + "\n\n"
                    else:
                        chunks.append(current_chunk.strip())
                        current_chunk = paragraph + "\n\n"
                else:
                    current_chunk += paragraph + "\n\n"
            # 如果没有当前块，开始新的理论块
            else:
                current_chunk = paragraph + "\n\n"
        
        # 普通内容处理：按长度控制分块
        else:
            if current_size + paragraph_size > max_chunk_size:
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                current_chunk = paragraph + "\n\n"
            else:
                current_chunk += paragraph + "\n\n"
        
        i += 1
    
    # 添加最后一块
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    # 进一步拆分过长的块，但要保持语义完整性
    final_chunks = []
    for chunk in chunks:
        if len(chunk) > max_chunk_size:
            # 识别块的主要类型以决定如何拆分
            is_case_chunk = any(keyword in chunk for keyword in case_study_keywords)
            is_exp_chunk = any(keyword in chunk for keyword in experiment_keywords)
            is_theory_chunk = any(keyword in chunk for keyword in theory_keywords)
            is_dev_chunk = any(keyword in chunk for keyword in 
                              ['发展', '过程', '阶段', '演变', '演进', '成长', 
                               '变化', '进展', '影响', '作用', '效应', '关系'])
            
            if is_case_chunk or is_exp_chunk:
                # 案例或实验块通常不拆分，因为它们需要保持完整性
                # 但如果是特别长的案例/实验，可以适当拆分
                if len(chunk) > max_chunk_size * 2:  # 如果是两倍长度以上
                    sentences = re.split(r'[.!?。！？]\s*', chunk)
                    temp_chunk = ""
                    
                    for sentence in sentences:
                        sentence = sentence.strip()
                        if not sentence:
                            continue
                        
                        # 对于案例和实验，即使是长块也要在合适的地方拆分
                        if len(temp_chunk + sentence) <= max_chunk_size:
                            temp_chunk += sentence + ". "
                        else:
                            if temp_chunk.strip():
                                final_chunks.append(temp_chunk.strip())
                            temp_chunk = sentence + ". "
                    
                    if temp_chunk.strip():
                        final_chunks.append(temp_chunk.strip())
                else:
                    # 普通长度的案例/实验块保持完整
                    final_chunks.append(chunk)
            else:
                # 对于非案例/非实验块，按句子拆分但保持最大长度
                sentences = re.split(r'[.!?。！？]\s*', chunk)
                temp_chunk = ""
                
                for sentence in sentences:
                    sentence = sentence.strip()
                    if not sentence:
                        continue
                    
                    if len(temp_chunk + sentence) <= max_chunk_size:
                        temp_chunk += sentence + ". "
                    else:
                        if temp_chunk.strip():
                            final_chunks.append(temp_chunk.strip())
                        temp_chunk = sentence + ". "
                
                if temp_chunk.strip():
                    final_chunks.append(temp_chunk.strip())
        else:
            final_chunks.append(chunk)
    
    # 过滤掉太小的块
    final_chunks = [chunk for chunk in final_chunks if len(chunk.strip()) > 50]
    
    return final_chunks


def split_chapters_robust(text: str):
    """增强版章节分割函数"""
    lines = text.splitlines()
    chapters = []
    current_title = ""
    current_content_lines = []

    # 允许的标题模式
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
            # 新章节
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


def chunk_yilian_advanced():
    """
    对依恋三部曲•第二卷分离进行高级分块处理
    """
    # 读取 textile 文件
    with open("./textiles/依恋三部曲•第二卷分离.textile", encoding="utf-8") as f:
        textile_src = f.read()

    # 预处理 + 切分章节
    clean_text = preprocess_yilian_textile(textile_src)
    chapters = split_chapters_robust(clean_text)

    print(f"✅ 成功切分 {len(chapters)} 章")
    
    all_chunks_with_titles = []
    
    for i, ch in enumerate(chapters, 1):
        print(f"[{i}] {ch['title']}... {len(ch['content'])}字")
        
        # 对每章内容进行高级策略分块
        chunks = split_by_advanced_strategy(ch['content'])
        
        print(f"  └── 分割为 {len(chunks)} 个语义块")
        
        # 为每个块创建标题（包含章节信息）
        for j, chunk in enumerate(chunks):
            chunk_title = f"{ch['title']} - 第{j+1}块"
            all_chunks_with_titles.append({
                "title": chunk_title,
                "content": chunk,
                "original_chapter": ch['title']
            })
    
    print(f"📦 总共生成 {len(all_chunks_with_titles)} 个语义块")
    
    # 处理每个块，获取AI响应并插入数据库
    for idx, chunk_data in enumerate(all_chunks_with_titles, 1):
        print(f"\n处理块 {idx}/{len(all_chunks_with_titles)}: {chunk_data['title'][:50]}...")
        
        try:
            result_data = get_ai_response(chunk_data["content"])
            if len(result_data) == 0:
                print("  ⚠️ result_data is empty")
                continue

            batch_data = []
            if isinstance(result_data, list):
                # 新响应格式
                for item in result_data:
                    content = item.get('content', '')
                    relevant_age_group = item.get('relevant_age_group', '')
                    relevant_domain = item.get('relevant_domain', '其他')
                    tags = item.get('tags', [])
                    
                    # 转换为列表格式
                    if isinstance(relevant_age_group, str):
                        relevant_age_group = [relevant_age_group] if relevant_age_group else []
                    if isinstance(relevant_domain, str):
                        relevant_domain = [relevant_domain] if relevant_domain else []
                    
                    tags_json = json.dumps(tags, ensure_ascii=False)                                                 
                    categories_json = json.dumps(relevant_domain, ensure_ascii=False)                                         
                    ages_json = json.dumps(relevant_age_group, ensure_ascii=False)                                                     
                    summary = content
                    
                    batch_data.append(("依恋三部曲•第二卷分离", chunk_data["title"], summary, 
                                     chunk_data["original_chapter"], tags_json, categories_json, ages_json))
            else:
                # 兼容旧格式
                tags_json = json.dumps(result_data.get('points', []), ensure_ascii=False)                                                 
                categories_json = json.dumps(result_data.get('categories', []), ensure_ascii=False)                                         
                ages_json = json.dumps(result_data.get('ages', []), ensure_ascii=False)                                                     
                summary = result_data.get('summary', '')                                                                
                batch_data.append(("依恋三部曲•第二卷分离", chunk_data["title"], summary, 
                                 chunk_data["original_chapter"], tags_json, categories_json, ages_json))

        except json.JSONDecodeError as e:
            print(f"  ❌ JSON 解析错误: {e}")
            continue
        except Exception as e:
            print(f"  ❌ 处理块 {idx} 时发生错误: {e}")
            continue

        # 批量插入数据
        if batch_data:
            from bookModel import batch_insert_data
            success = batch_insert_data(batch_data)
            if success:
                print(f"  ✅ 批量插入 {len(batch_data)} 条记录成功")
            else:
                print("  ❌ 批量插入失败")
        else:
            print("  ⚠️ 没有有效数据需要插入")


def yilian_simple_chunk():
    """
    简单分块版本，用于测试
    """
    # 读取 textile 文件
    with open("./textiles/依恋三部曲•第二卷分离.textile", encoding="utf-8") as f:
        textile_src = f.read()

    # 预处理 + 切分章节
    clean_text = preprocess_yilian_textile(textile_src)
    chapters = split_chapters_robust(clean_text)

    print(f"✅ 成功切分 {len(chapters)} 章")
    
    for i, ch in enumerate(chapters, 1):
        print(f"[{i}] {ch['title']}... {len(ch['content'])}字")
        
        # 使用高级策略分块
        chunks = split_by_advanced_strategy(ch['content'])
        
        print(f"  └── 分割为 {len(chunks)} 个语义块")
        
        for j, chunk in enumerate(chunks):
            print(f"    块 {j+1}: {len(chunk)} 字符")
            
            # 在实际应用中，这里会调用AI处理和数据库插入
            # result_data = get_ai_response(chunk_content)
            # insert_data("依恋三部曲•第二卷分离", f"{ch['title']}-块{j+1}", ...)


if __name__ == "__main__":
    print("开始处理 依恋三部曲•第二卷分离 的高级分块...")
    chunk_yilian_advanced()