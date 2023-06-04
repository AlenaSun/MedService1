import sqlite3

def create_connection():
    conn = sqlite3.connect('ad.db')
    cursor = conn.cursor()
    return conn, cursor

def close_connection(conn):
    conn.commit()
    conn.close()

def create_table(city):
    conn, cursor = create_connection()
    create_table_query = f'''
    CREATE TABLE IF NOT EXISTS users_info_{city} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name TEXT,
        phone TEXT,
        email TEXT,
        date TEXT,
        time TEXT
    );
    '''
    cursor.execute(create_table_query)
    print(f"Таблица users_info_{city} была успешно создана")
    close_connection(conn)

def insert_user_info(city, user_id, name, phone, email, date, time):
    conn, cursor = create_connection()
    cursor.execute(f"INSERT INTO users_info_{city} (user_id, name, phone, email, date, time) VALUES (?, ?, ?, ?, ?, ?)", (user_id, name, phone, email, date, time))
    conn.commit()
    close_connection(conn)

    # Создание таблицы при запуске для каждого города
    create_table('kogalym')
    create_table('uray')
    create_table('tumen')
