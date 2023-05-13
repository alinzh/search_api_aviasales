import sqlite3
import pandas as pd

def create_table_in_database():
    # Создание подключения к базе данных
    conn = sqlite3.connect('mydatabase.db')
    # Создание курсора для работы с базой данных
    cursor = conn.cursor()
    # Создание таблицы users
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT NOT NULL,
        full_name TEXT NOT NULL
    )
''')
# Закрытие курсора и сохранение изменений
    cursor.close()
    conn.commit()
    conn.close()



def add_users_to_sql(new_users):
    '''
    users is list with thensor
    :return: bool
    '''
    conn = sqlite3.connect('mydatabase.db')
    cursor = conn.cursor()
    for user in new_users:
    # Проверка, существует ли пользователь с таким же id в базе данных
        cursor.execute('SELECT * FROM users WHERE user_id=?', (user[0],))
        existing_user = cursor.fetchone()

        if existing_user is None:
        # Добавление нового пользователя, если его еще нет в базе данных
            cursor.execute('INSERT INTO users (user_id, username, full_name) VALUES (?, ?, ?)', user)
            print(f'Added user {user[0]}')
        else:
            print(f'User {user[0]} already exists')
# Закрытие курсора и сохранение изменений
    cursor.close()
    conn.commit()
    conn.close()

def show_users_from_table():
    '''
    return list with * from table
    '''
    conn = sqlite3.connect('mydatabase.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")

    answer = cursor.fetchall()
    # Выводим результат на экран
    date_from_table = []
    for row in answer:
        date_from_table.append(row)
    # Закрываем соединение с базой данных
    conn.close()
    return date_from_table

def convert_to_excel():
    conn = sqlite3.connect('mydatabase.db')
    df = pd.read_sql('SELECT * FROM users', conn)
    df.to_excel(r'result.xlsx', index=False)
    document = open('result.xlsx', 'rb')
    return document