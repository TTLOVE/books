import mysql.connector

# Connect to MySQL database
connection = mysql.connector.connect(
    # host="192.168.31.147",
    host="192.168.5.111",
    database="books",  # Replace with your database name
    user="root",  # Replace with your MySQL username
    password="qt123",  # Replace with your MySQL password
)


def insert_data(book_name, title, summary, content, tags, categories, ages):
    if connection.is_connected():
        cursor = connection.cursor()
        insert_query = """
        INSERT INTO seperate_books (book_name, title, summary, content, tags, categories, ages)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(
            insert_query, (book_name, title, summary, content, tags, categories, ages)
        )
        connection.commit()
        print(f"Data inserted successfully for chapter: {title}")
        return True
    else:
        print("Failed to connect to MySQL")
        return False


def batch_insert_data(data_list):
    if connection.is_connected():
        cursor = connection.cursor()
        cursor.executemany(
            "INSERT INTO seperate_books (book_name, title, summary, content, tags, categories, ages, page) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            data_list,
        )
        connection.commit()
        print(f"Data inserted successfully for {len(data_list)} chapters")
        return True
    else:
        print("Failed to connect to MySQL")
        return False


def batch_insert_knowledge(data_list):
    if connection.is_connected():
        cursor = connection.cursor()
        cursor.executemany(
            "INSERT INTO knowledges (relevant_age_group, original_text_segment, text_location, extraction_context, inference_level, extraction_basis, confidence_level, original_age_reference, content_summary, source_document, development_aspect, domain_category, sensitive_period, intelligence_development, evidence_quality, extraction_notes) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            data_list,
        )
        connection.commit()
        print(f"Data inserted successfully for {len(data_list)} knowledge")
        return True
    else:
        print("Failed to connect to MySQL")
        return False


if __name__ == "__main__":
    data_list = [
        (
            '["18-24月"]',
            "在观察中的两周里，敌对行为虽然不常出现，却有增加的迹象。并且常常表现为咬别的小朋友，或者虐待从家里带来的小客体。",
            "第1章第10页第3段",
            "描述分离期间幼儿敌对行为的发展",
            "直接描述",
            "直接观察分离压力导致幼儿敌对行为增加",
            "高置信度",
            "15-30个月（研究样本年龄范围）",
            "分离压力导致幼儿敌对行为增加，表现为咬人和虐待客体",
            "依恋三部曲・第二卷分离",
            '["行为表现"]',
            '["社会行为", "适应能力"]',
            '{"category": ["人际"], "manifestation": "对挫折敏感，通过攻击行为表达情绪"}',
            '{"category": ["身体动觉"], "manifestation": "通过身体动作表达愤怒情绪"}',
            "强证据",
            "显示分离压力对攻击行为的影响",
        )
    ]
    batch_insert_knowledge(data_list)
