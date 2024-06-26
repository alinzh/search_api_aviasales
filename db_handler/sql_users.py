import sqlite3

import pandas as pd


def create_table_in_database():
    conn = sqlite3.connect("mydatabase.db")
    cursor = conn.cursor()
    # Создание таблицы users
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT ,
        full_name TEXT ,
        states INT NOT NULL,
        start_date TEXT NOT NULL,
        end_date TEXT NOT NULL,
        start_period TEXT NOT NULL,
        end_period TEXT NOT NULL,
        home TEXT NOT NULL,
        finish TEXT NOT NULL,
        hate_airl TEXT NOT NULL
        
    )
        """
    )
    cursor.close()
    conn.commit()
    conn.close()


def add_users_to_sql(new_users):
    """
    users is list with thensor
    :return: bool
    """
    conn = sqlite3.connect("mydatabase.db")
    cursor = conn.cursor()
    for user in new_users:
        # Проверка, существует ли пользователь с таким же id в базе
        cursor.execute("SELECT * FROM users WHERE user_id=?", (user[0],))
        existing_user = cursor.fetchone()

        if existing_user is None:
            # Добавление нового пользователя, если его еще нет в базе
            cursor.execute(
                "INSERT INTO users (user_id, username, full_name, states, start_date, end_date, start_period, end_period, home, finish, hate_airl) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                user,
            )
            print(f"Added user {user[0]}")
        else:
            print(f"User {user[0]} already exists")
    # Закрытие курсора и сохранение изменений
    cursor.close()
    conn.commit()
    conn.close()


def show_users_from_table():
    """
    return list with * from table
    """
    conn = sqlite3.connect("mydatabase.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")

    answer = cursor.fetchall()
    # Выводим результат
    date_from_table = []
    for row in answer:
        date_from_table.append(row)
    # Закрываем соединение с базой
    conn.close()
    return date_from_table


def convert_to_excel():
    conn = sqlite3.connect("mydatabase.db")
    df = pd.read_sql("SELECT * FROM users", conn)
    df.to_excel(r"result.xlsx", index=False)
    document = open("result.xlsx", "rb")
    return document


def update_user_state(user_id, new_state):
    conn = sqlite3.connect("mydatabase.db")
    cursor = conn.cursor()
    # Проверяем, существует ли пользователь с указанным user_id в базе данных
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    existing_user = cursor.fetchone()

    if existing_user is not None:
        # Обновляем состояние пользователя
        cursor.execute(
            "UPDATE users SET states=? WHERE user_id=?", (int(new_state), user_id)
        )
        print(f"Updated state for user {user_id}")
    else:
        print(f"User {user_id} does not exist")
    conn.commit()
    conn.close()


def users_all_the_time(user_id, username, full_name):
    conn = sqlite3.connect("mydatabase.db")
    cursor = conn.cursor()

    # Проверяем, существует ли таблица users_all_the_time
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='users_all_the_time'"
    )
    table_exists = cursor.fetchone()

    if not table_exists:
        # Создаем таблицу users_all_the_time, если она не существует
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users_all_the_time (
                user_id INTEGER,
                username TEXT,
                full_name TEXT
            )
        """
        )
        conn.commit()

    cursor.execute("SELECT * FROM users_all_the_time WHERE user_id=?", (user_id,))
    existing_entry = cursor.fetchone()

    if not existing_entry:
        # Добавляем новую запись в таблицу users_all_the_time
        cursor.execute(
            "INSERT INTO users_all_the_time (user_id, username, full_name) VALUES (?, ?, ?)",
            (user_id, username, full_name),
        )
        conn.commit()
        print(f"Added user {user_id}, username {username}")
    else:
        print(f"Already added")

    # Закрытие соединения с базой данных
    cursor.close()
    conn.close()


def append_airports(user_id, airports):
    conn = sqlite3.connect("mydatabase.db")
    cursor = conn.cursor()

    # Проверяем, существует ли таблица user_airports
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='user_airports'"
    )
    table_exists = cursor.fetchone()

    if not table_exists:
        # Создаем таблицу user_airports, если она не существует
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS user_airports (
                user_id INTEGER,
                airport TEXT,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """
        )
        conn.commit()

    # Проверяем, существует ли пользователь с указанным user_id в таблице users
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    existing_user = cursor.fetchone()

    if existing_user:
        cursor.execute(
            "SELECT * FROM user_airports WHERE user_id=? AND airport=?",
            (user_id, airports),
        )
        existing_entry = cursor.fetchone()

        if not existing_entry:
            # Добавляем новую запись в таблицу user_airports
            cursor.execute(
                "INSERT INTO user_airports (user_id, airport) VALUES (?, ?)",
                (user_id, airports),
            )
            conn.commit()
            print(f"Added airport {airports} for user {user_id}")
        else:
            print(f"Airport {airports} already exists for user {user_id}")
    else:
        print(f"User {user_id} does not exist")

    # Закрытие соединения с базой данных
    cursor.close()
    conn.close()


def append_start_date(user_id, start_date):
    conn = sqlite3.connect("mydatabase.db")
    cursor = conn.cursor()
    # Проверяем, существует ли пользователь с указанным user_id в базе данных
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    existing_user = cursor.fetchone()

    if existing_user is not None:
        # Обновляем состояние пользователя
        cursor.execute(
            "UPDATE users SET start_date=? WHERE user_id=?", (str(start_date), user_id)
        )
        print(f"Updated state for user {user_id}")
    else:
        print(f"User {user_id} does not exist")
    conn.commit()
    conn.close()


def append_end_date(user_id, end_date):
    conn = sqlite3.connect("mydatabase.db")
    cursor = conn.cursor()
    # Проверяем, существует ли пользователь с указанным user_id в базе данных
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    existing_user = cursor.fetchone()

    if existing_user is not None:
        # Обновляем состояние пользователя
        cursor.execute(
            "UPDATE users SET end_date=? WHERE user_id=?", (str(end_date), user_id)
        )
        print(f"Updated state for user {user_id}")
    else:
        print(f"User {user_id} does not exist")
    conn.commit()
    conn.close()


def append_start_period(user_id, start_period):
    conn = sqlite3.connect("mydatabase.db")
    cursor = conn.cursor()
    # Проверяем, существует ли пользователь с указанным user_id в базе данных
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    existing_user = cursor.fetchone()

    if existing_user is not None:
        # Обновляем состояние пользователя
        cursor.execute(
            "UPDATE users SET start_period=? WHERE user_id=?",
            (str(start_period), user_id),
        )
        print(f"Updated state for user {user_id}")
    else:
        print(f"User {user_id} does not exist")
    conn.commit()
    conn.close()


def append_end_period(user_id, end_period):
    conn = sqlite3.connect("mydatabase.db")
    cursor = conn.cursor()
    # Проверяем, существует ли пользователь с указанным user_id в базе данных
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    existing_user = cursor.fetchone()

    if existing_user is not None:
        # Обновляем состояние пользователя
        cursor.execute(
            "UPDATE users SET end_period=? WHERE user_id=?", (str(end_period), user_id)
        )
        print(f"Updated state for user {user_id}")
    else:
        print(f"User {user_id} does not exist")
    conn.commit()
    conn.close()


def append_home(user_id, home):
    conn = sqlite3.connect("mydatabase.db")
    cursor = conn.cursor()
    # Проверяем, существует ли пользователь с указанным user_id в базе данных
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    existing_user = cursor.fetchone()

    if existing_user is not None:
        # Обновляем состояние пользователя
        cursor.execute("UPDATE users SET home=? WHERE user_id=?", (home, user_id))
        print(f"Updated state for user {user_id}")
    else:
        print(f"User {user_id} does not exist")
    conn.commit()
    conn.close()


def append_tranzit(user_id, tranzit):
    conn = sqlite3.connect("mydatabase.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='users_tranzit'"
    )
    table_exists = cursor.fetchone()

    if not table_exists:
        cursor.execute(
            """
                CREATE TABLE IF NOT EXISTS users_tranzit (
                    user_id INTEGER,
                    airport TEXT,
                    duration TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """
        )
        conn.commit()
    airport = tranzit[0]
    duration = tranzit[1]

    # Проверяем, существует ли пользователь с указанным user_id в таблице users
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    existing_user = cursor.fetchone()

    if existing_user:
        cursor.execute(
            "SELECT * FROM users_tranzit WHERE user_id=? AND airport=? AND duration=?",
            (user_id, airport, duration),
        )
        existing_entry = cursor.fetchone()

        if not existing_entry:
            # Добавляем новую запись в таблицу users_tranzit
            cursor.execute(
                "INSERT INTO users_tranzit (user_id, airport, duration) VALUES (?, ?, ?)",
                (user_id, airport, duration),
            )
            conn.commit()
            print(
                f"Added tranzit in airport {airport}, duration for tranzit is {duration}min for user {user_id}"
            )
        else:
            print(
                f"Added tranzit in airport {airport}, duration for tranzit is {duration}min for user {user_id}"
            )
    else:
        print(f"User {user_id} does not exist")

    # Закрытие соединения с базой данных
    cursor.close()
    conn.close()


def append_finish(user_id, finish):
    conn = sqlite3.connect("mydatabase.db")
    cursor = conn.cursor()
    # Проверяем, существует ли пользователь с указанным user_id в базе данных
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    existing_user = cursor.fetchone()

    if existing_user is not None:
        # Обновляем состояние пользователя
        cursor.execute("UPDATE users SET finish=? WHERE user_id=?", (finish, user_id))
        print(f"Updated state for user {user_id}")
    else:
        print(f"User {user_id} does not exist")
    conn.commit()
    conn.close()


def append_hate_airl(user_id, hate_air):
    conn = sqlite3.connect("mydatabase.db")
    cursor = conn.cursor()
    # Проверяем, существует ли пользователь с указанным user_id в базе данных
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    existing_user = cursor.fetchone()

    if existing_user is not None:
        # Обновляем состояние пользователя
        cursor.execute(
            "UPDATE users SET hate_airl=? WHERE user_id=?", (str(hate_air), user_id)
        )
        print(f"Updated state for user {user_id}")
    else:
        print(f"User {user_id} does not exist")
    conn.commit()
    conn.close()


def get_user_state(user_id):
    conn = sqlite3.connect("mydatabase.db")
    cursor = conn.cursor()

    # SQL-запрос для получения состояния пользователя по его идентификатору
    cursor.execute("SELECT states FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()

    if result:
        user_state = result[0]
    else:
        user_state = None

    cursor.close()
    conn.close()

    return int(user_state)


def check_user_in_table(user_id):
    conn = sqlite3.connect("mydatabase.db")
    cursor = conn.cursor()

    # Проверяем наличие пользователя в таблице по его идентификатору
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()

    cursor.close()
    conn.close()

    # Если результат не равен None, значит, пользователь существует
    if result is not None:
        return True
    else:
        return False


def get_all_data_from_table():
    conn = sqlite3.connect("mydatabase.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users")
    result = cursor.fetchall()

    cursor.close()
    conn.close()

    return result


def get_all_data_from_users_airport():
    conn = sqlite3.connect("mydatabase.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM user_airports")
    result = cursor.fetchall()

    cursor.close()
    conn.close()
    return result


def get_all_data_from_users_tranzit():
    conn = sqlite3.connect("mydatabase.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users_tranzit")
    result = cursor.fetchall()

    cursor.close()
    conn.close()
    return result


def delete_airports(user_id):
    conn = sqlite3.connect("mydatabase.db")
    cursor = conn.cursor()

    cursor.execute("DELETE FROM user_airports WHERE user_id=?", (user_id,))
    conn.commit()

    cursor.close()
    conn.close()


def delete_tranzit(user_id):
    conn = sqlite3.connect("mydatabase.db")
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM users_tranzit WHERE user_id=?", (user_id,))
        conn.commit()
    except:
        pass

    cursor.close()
    conn.close()


def delete_user(user_id):
    conn = sqlite3.connect("mydatabase.db")
    cursor = conn.cursor()

    cursor.execute("DELETE FROM users WHERE user_id=?", (user_id,))
    conn.commit()

    cursor.close()
    conn.close()
