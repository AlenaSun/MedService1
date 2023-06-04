import sqlite3

def create_connection():
    conn = sqlite3.connect('admin.db')
    cursor = conn.cursor()
    return conn, cursor

def close_connection(conn):
    conn.commit()
    conn.close()

def create_table(city, type):
    conn, cursor = create_connection()
    create_table_query = f'''
    CREATE TABLE IF NOT EXISTS users_info_{city}_{type} (
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
    print(f"Таблица users_info_{city}_{type} была успешно создана")
    close_connection(conn)

def insert_user_info(city, user_id, name, phone, email, date, time, type):
    conn, cursor = create_connection()
    cursor.execute(f"INSERT INTO users_info_{city}_{type} (user_id, name, phone, email, date, time) VALUES (?, ?, ?, ?, ?, ?)", (user_id, name, phone, email, date, time))
    conn.commit()
    close_connection(conn)

    # Создание таблицы при запуске для каждого города
    create_table('kogalym', 'dentist3')
    create_table('kogalym', 'dentist4')
    create_table('uray', 'dentist5')
    create_table('uray', 'orthopedic2')
    create_table('tumen', 'dentist1')
    create_table('tumen', 'orthopedic1')
    create_table('tumen', 'dentist2')
