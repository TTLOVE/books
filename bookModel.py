import mysql.connector

# Connect to MySQL database
connection = mysql.connector.connect(
    host="192.168.31.147",
    # host="192.168.5.105",
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
        cursor.executemany("INSERT INTO seperate_books (book_name, title, summary, content, tags, categories, ages, page) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", data_list)
        connection.commit()
        print(f"Data inserted successfully for {len(data_list)} chapters")
        return True
    else:
        print("Failed to connect to MySQL")
        return False   
