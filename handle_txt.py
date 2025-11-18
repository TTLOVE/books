import re
import json
import os
from aiClient import get_ai_response
from bookModel import insert_data


def yilian():
    # 读取txt文件夹下的多个文件
    for file in os.listdir("./txt"):
        with open(f"./txt/{file}", encoding="utf-8") as f:
            text = f.read()

            print(f"✅ 成功读取文件 {file}")

            try:
                result_data = get_ai_response(text)
                if len(result_data) == 0:
                    print("result_data is empty")
                    continue

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
                            file,
                            summary,
                            "",
                            tags_json,
                            categories_json,
                            ages_json,
                        )
                    )

            except json.JSONDecodeError as e:
                print(f"❌ JSON 解析错误 for chapter {i}: {e}")
                print(f"AI response was: {result_data}")
                continue
            except Exception as e:
                print(f"❌ 处理文件 {file} 时发生错误: {e}")
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


if __name__ == "__main__":
    yilian()
