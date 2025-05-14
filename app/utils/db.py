import psycopg2
import psycopg2.extras
from contextlib import contextmanager
from flask import current_app, g


def get_db():
    """Получение соединения с базой данных"""
    if 'db' not in g:
        g.db = psycopg2.connect(
            host=current_app.config['DB_HOST'],
            port=current_app.config['DB_PORT'],
            user=current_app.config['DB_USER'],
            password=current_app.config['DB_PASSWORD'],
            database=current_app.config['DB_NAME']
        )
        # Автоматическое преобразование результатов запросов в словари
        g.db.cursor_factory = psycopg2.extras.RealDictCursor
    return g.db


def close_db(e=None):
    """Закрытие соединения с базой данных"""
    db = g.pop('db', None)
    if db is not None:
        db.close()


@contextmanager
def get_db_cursor(commit=False):
    """Контекстный менеджер для работы с курсором базы данных"""
    conn = get_db()
    cursor = conn.cursor()
    try:
        yield cursor
        if commit:
            conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()


def init_app(app):
    """Инициализация функций работы с БД в приложении"""
    app.teardown_appcontext(close_db)


def execute_query(query, params=None, fetch=True, commit=False, fetchone=False):
    """
    Выполнение SQL-запроса к базе данных

    Args:
        query (str): SQL-запрос
        params (tuple|dict, optional): Параметры для запроса
        fetch (bool, optional): Нужно ли получать результат запроса
        commit (bool, optional): Нужно ли применять изменения в БД
        fetchone (bool, optional): Нужно ли получить только одну запись

    Returns:
        dict|list|None: Результат запроса или None
    """
    with get_db_cursor(commit=commit) as cursor:
        cursor.execute(query, params)

        if fetch:
            if fetchone:
                return cursor.fetchone()
            return cursor.fetchall()

        if cursor.rowcount > 0 and not fetch:
            return cursor.rowcount

        return None