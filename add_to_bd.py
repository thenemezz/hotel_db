import psycopg2
from datetime import date, timedelta
import random


def seed_database():
    """Заполняет базу данных hotel_complex тестовыми данными"""

    # Параметры подключения к базе данных hotel_complex
    conn_params = {
        'host': 'localhost',
        'user': 'postgres',
        'password': '0911',  # Используем ваш пароль из предыдущего кода
        'database': 'hotel_complex'
    }

    conn = None
    try:
        # Подключение к базе данных
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor()

        # Очистка существующих данных (опционально)
        clear_tables(cursor)

        # Заполнение таблицы hotel
        insert_hotels(cursor)

        # Заполнение таблицы room
        insert_rooms(cursor)

        # Заполнение таблицы firm
        insert_firms(cursor)

        # Заполнение таблицы contract
        insert_contracts(cursor)

        # Заполнение таблицы guest
        insert_guests(cursor)

        # Заполнение таблицы booking
        insert_bookings(cursor)

        # Заполнение таблицы booking_room
        insert_booking_rooms(cursor)

        # Заполнение таблицы service_type
        insert_service_types(cursor)

        # Заполнение таблицы service_usage
        insert_service_usages(cursor)

        # Заполнение таблицы complaint
        insert_complaints(cursor)

        # Фиксация изменений
        conn.commit()
        print("База данных успешно заполнена тестовыми данными.")

    except Exception as e:
        print(f"Ошибка при заполнении базы данных: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def clear_tables(cursor):
    """Очищает все таблицы перед заполнением"""
    tables = [
        'complaint',
        'service_usage',
        'booking_room',
        'service_type',
        'booking',
        'guest',
        'contract',
        'firm',
        'room',
        'hotel'
    ]

    for table in tables:
        try:
            cursor.execute(f"TRUNCATE TABLE {table} CASCADE")
            print(f"Таблица {table} очищена.")
        except Exception as e:
            print(f"Ошибка при очистке таблицы {table}: {e}")


def insert_hotels(cursor):
    """Заполняет таблицу hotel"""
    hotels = [
        ('Гранд Отель', 5, 10, 200, True, True, True, True, True, True, True),
        ('Бизнес Плаза', 4, 8, 150, True, True, True, True, True, False, False),
        ('Туристический Хостел', 3, 4, 50, True, False, False, True, False, False, False)
    ]

    for hotel in hotels:
        cursor.execute("""
            INSERT INTO hotel (name, rating, floors, room_count, has_housekeeping, has_laundry, 
                              has_dry_cleaning, has_restaurant, has_bar, has_pool_sauna, has_billiards)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, hotel)

    print("Отели добавлены.")


def insert_rooms(cursor):
    """Заполняет таблицу room"""
    # Получаем id отелей
    cursor.execute("SELECT id FROM hotel")
    hotel_ids = [row[0] for row in cursor.fetchall()]

    rooms = []
    # Для каждого отеля добавляем комнаты
    for hotel_id in hotel_ids:
        # Определяем количество этажей для отеля
        cursor.execute("SELECT floors FROM hotel WHERE id = %s", (hotel_id,))
        floors = cursor.fetchone()[0]

        # Добавляем комнаты для каждого этажа
        for floor in range(1, floors + 1):
            # На каждом этаже от 5 до 10 комнат
            room_count = random.randint(5, 10)
            for room_num in range(1, room_count + 1):
                room_number = f"{floor}{room_num:02d}"
                capacity = random.choice([1, 2, 2, 3, 4])
                base_rate = round(2000 + (capacity * 1000) + (hotel_id * 500), 2)
                is_available = random.choice([True, True, True, False])  # 75% комнат доступны

                rooms.append((hotel_id, floor, room_number, capacity, base_rate, is_available))

    for room in rooms:
        cursor.execute("""
            INSERT INTO room (hotel_id, floor_number, room_number, room_capacity, base_rate, is_available)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, room)

    print(f"{len(rooms)} комнат добавлено.")


def insert_firms(cursor):
    """Заполняет таблицу firm"""
    firms = [
        ('ТурКомпания "Горизонт"', 'Туристическое агентство', 'г. Москва, ул. Тверская, 15', '+7(495)123-45-67', True),
        ('ООО "Бизнес-Тревел"', 'Корпоративное агентство', 'г. Санкт-Петербург, Невский пр-т, 78', '+7(812)987-65-43',
         True),
        ('АО "Конференц-Сервис"', 'Организация мероприятий', 'г. Казань, ул. Баумана, 32', '+7(843)456-78-90', True),
        ('ИП Иванов Т.К.', 'Частный предприниматель', 'г. Новосибирск, ул. Ленина, 12', '+7(383)111-22-33', False)
    ]

    for firm in firms:
        cursor.execute("""
            INSERT INTO firm (name, firm_type, address, phone, is_active)
            VALUES (%s, %s, %s, %s, %s)
        """, firm)

    print("Компании добавлены.")


def insert_contracts(cursor):
    """Заполняет таблицу contract"""
    # Получаем id компаний
    cursor.execute("SELECT id FROM firm WHERE is_active = TRUE")
    firm_ids = [row[0] for row in cursor.fetchall()]

    contracts = []
    today = date.today()

    for firm_id in firm_ids:
        # Создаем контракт на текущий год
        start_date = date(today.year, random.randint(1, 6), random.randint(1, 28))
        end_date = date(today.year + 1, random.randint(1, 12), random.randint(1, 28))
        discount = random.randint(5, 20)

        contracts.append((firm_id, start_date, end_date, discount))

    for contract in contracts:
        cursor.execute("""
            INSERT INTO contract (firm_id, contract_start_date, contract_end_date, discount_rate)
            VALUES (%s, %s, %s, %s)
        """, contract)

    print(f"{len(contracts)} контрактов добавлено.")


def insert_guests(cursor):
    """Заполняет таблицу guest"""
    guests = [
        ('Иванов', 'Иван', 'Иванович', '4510', '123456', '+7(916)123-45-67', 'ivanov@mail.ru'),
        ('Петров', 'Петр', 'Петрович', '4511', '234567', '+7(917)234-56-78', 'petrov@gmail.com'),
        ('Сидорова', 'Анна', 'Сергеевна', '4512', '345678', '+7(918)345-67-89', 'sidorova@yandex.ru'),
        ('Козлов', 'Дмитрий', 'Александрович', '4513', '456789', '+7(919)456-78-90', 'kozlov@mail.ru'),
        ('Смирнова', 'Елена', 'Владимировна', '4514', '567890', '+7(920)567-89-01', 'smirnova@gmail.com'),
        ('Новиков', 'Алексей', 'Дмитриевич', '4515', '678901', '+7(921)678-90-12', 'novikov@mail.ru'),
        ('Морозова', 'Ольга', 'Андреевна', '4516', '789012', '+7(922)789-01-23', 'morozova@yandex.ru')
    ]

    for guest in guests:
        cursor.execute("""
            INSERT INTO guest (last_name, first_name, middle_name, passport_series, passport_number, phone, email)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, guest)

    print(f"{len(guests)} гостей добавлено.")


def insert_bookings(cursor):
    """Заполняет таблицу booking"""
    # Получаем id компаний и гостей
    cursor.execute("SELECT id FROM firm")
    firm_ids = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT id FROM guest")
    guest_ids = [row[0] for row in cursor.fetchall()]

    bookings = []
    today = date.today()

    # Создаем бронирования для компаний (корпоративные клиенты)
    for _ in range(3):
        firm_id = random.choice(firm_ids)
        check_in = today + timedelta(days=random.randint(1, 30))
        check_out = check_in + timedelta(days=random.randint(1, 7))
        total_rooms = random.randint(2, 5)
        total_persons = total_rooms * random.randint(1, 3)
        booking_date = today - timedelta(days=random.randint(1, 14))
        status = random.choice(['Забронировано', 'Забронировано', 'Отменено'])

        bookings.append((firm_id, None, total_rooms, total_persons, check_in, check_out, booking_date, status))

    # Создаем бронирования для индивидуальных гостей
    for _ in range(5):
        guest_id = random.choice(guest_ids)
        check_in = today + timedelta(days=random.randint(1, 60))
        check_out = check_in + timedelta(days=random.randint(1, 10))
        total_rooms = random.randint(1, 3)
        total_persons = total_rooms * random.randint(1, 2)
        booking_date = today - timedelta(days=random.randint(1, 30))
        status = random.choice(['Забронировано', 'Забронировано', 'Отменено', 'Завершено'])

        bookings.append((None, guest_id, total_rooms, total_persons, check_in, check_out, booking_date, status))

    # Создаем несколько прошедших бронирований
    for _ in range(2):
        guest_id = random.choice(guest_ids)
        check_in = today - timedelta(days=random.randint(20, 40))
        check_out = check_in + timedelta(days=random.randint(1, 7))
        total_rooms = random.randint(1, 2)
        total_persons = total_rooms * random.randint(1, 2)
        booking_date = check_in - timedelta(days=random.randint(10, 30))
        status = 'Завершено'

        bookings.append((None, guest_id, total_rooms, total_persons, check_in, check_out, booking_date, status))

    for booking in bookings:
        cursor.execute("""
            INSERT INTO booking (firm_id, guest_id, total_rooms, total_persons, check_in_date, check_out_date, booking_date, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, booking)

    print(f"{len(bookings)} бронирований добавлено.")


def insert_booking_rooms(cursor):
    """Заполняет таблицу booking_room"""
    # Получаем id бронирований со статусом "Забронировано" или "Завершено"
    cursor.execute("SELECT id, total_rooms FROM booking WHERE status IN ('Забронировано', 'Завершено')")
    bookings = cursor.fetchall()

    # Получаем доступные комнаты
    cursor.execute("SELECT id FROM room WHERE is_available = TRUE")
    available_room_ids = [row[0] for row in cursor.fetchall()]

    if not available_room_ids:
        print("Нет доступных комнат для бронирования.")
        return

    booking_rooms = []
    used_room_ids = set()  # Чтобы не использовать одну комнату несколько раз

    for booking_id, total_rooms in bookings:
        rooms_for_booking = []

        # Выбираем случайные доступные комнаты для этого бронирования
        for _ in range(total_rooms):
            # Отфильтруем комнаты, которые уже использованы
            available = [r for r in available_room_ids if r not in used_room_ids]
            if not available:
                break

            room_id = random.choice(available)
            used_room_ids.add(room_id)
            rooms_for_booking.append((booking_id, room_id))

        booking_rooms.extend(rooms_for_booking)

    for booking_room in booking_rooms:
        try:
            cursor.execute("""
                INSERT INTO booking_room (booking_id, room_id)
                VALUES (%s, %s)
            """, booking_room)
        except psycopg2.Error as e:
            print(f"Ошибка при добавлении связи бронирование-комната {booking_room}: {e}")

    print(f"{len(booking_rooms)} связей бронирование-комната добавлено.")


def insert_service_types(cursor):
    """Заполняет таблицу service_type"""
    services = [
        ('Завтрак', 500.00, True),
        ('Полупансион', 1200.00, True),
        ('Полный пансион', 2000.00, True),
        ('Мини-бар', 300.00, True),
        ('Спа-процедуры', 2500.00, True),
        ('Трансфер', 1500.00, True),
        ('Химчистка', 800.00, True),
        ('Прачечная', 500.00, True),
        ('Аренда конференц-зала', 5000.00, True),
        ('Экскурсия', 1800.00, False)
    ]

    for service in services:
        cursor.execute("""
            INSERT INTO service_type (name, base_price, is_active)
            VALUES (%s, %s, %s)
        """, service)

    print(f"{len(services)} типов услуг добавлено.")


def insert_service_usages(cursor):
    """Заполняет таблицу service_usage"""
    # Получаем id бронирований, комнат, гостей и услуг
    cursor.execute("""
        SELECT b.id, br.room_id, b.guest_id 
        FROM booking b 
        JOIN booking_room br ON b.id = br.booking_id 
        WHERE b.status IN ('Забронировано', 'Завершено')
    """)
    booking_data = cursor.fetchall()

    cursor.execute("SELECT id, base_price FROM service_type WHERE is_active = TRUE")
    services = cursor.fetchall()

    service_usages = []

    for booking_id, room_id, guest_id in booking_data:
        # Для каждого бронирования добавляем случайное количество услуг
        service_count = random.randint(1, 4)

        cursor.execute("SELECT check_in_date, check_out_date FROM booking WHERE id = %s", (booking_id,))
        check_in, check_out = cursor.fetchone()

        for _ in range(service_count):
            service_id, base_price = random.choice(services)

            # Дата использования услуги должна быть в пределах дат бронирования
            if check_in <= date.today() <= check_out:
                usage_date = date.today() - timedelta(days=random.randint(0, (date.today() - check_in).days))
            elif date.today() > check_out:
                usage_date = check_in + timedelta(days=random.randint(0, (check_out - check_in).days))
            else:  # Будущее бронирование
                continue  # Пропускаем создание услуги для будущего бронирования

            # Случайная корректировка стоимости
            # Преобразуем Decimal в float перед умножением
            cost = round(float(base_price) * random.uniform(0.9, 1.1), 2)
            paid = random.choice([True, False])

            service_usages.append((guest_id, booking_id, room_id, service_id, usage_date, cost, paid))

    for usage in service_usages:
        cursor.execute("""
            INSERT INTO service_usage (guest_id, booking_id, room_id, service_type_id, usage_date, cost, paid)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, usage)

    print(f"{len(service_usages)} использований услуг добавлено.")


def insert_complaints(cursor):
    """Заполняет таблицу complaint"""
    # Получаем id гостей
    cursor.execute("SELECT id FROM guest")
    guest_ids = [row[0] for row in cursor.fetchall()]

    complaints = [
        (random.choice(guest_ids), date.today() - timedelta(days=random.randint(1, 30)),
         "Шумные соседи в соседнем номере не давали спать всю ночь", True,
         date.today() - timedelta(days=random.randint(1, 5)),
         "Принесены извинения, гостям предложен комплимент от отеля и перемещение в другой номер."),

        (random.choice(guest_ids), date.today() - timedelta(days=random.randint(1, 20)),
         "Не работал кондиционер в комнате, было очень жарко.", True,
         date.today() - timedelta(days=random.randint(1, 3)),
         "Кондиционер был отремонтирован в течение часа после жалобы."),

        (random.choice(guest_ids), date.today() - timedelta(days=random.randint(1, 10)),
         "Очень медленное обслуживание в ресторане отеля, ждали заказ более часа.", False, None, None)
    ]

    for complaint in complaints:
        cursor.execute("""
            INSERT INTO complaint (guest_id, complaint_date, description, resolved, resolution_date, resolution_details)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, complaint)

    print(f"{len(complaints)} жалоб добавлено.")


import psycopg2


def add_users():
    """Добавляет пользователей с разными уровнями доступа в базу данных"""

    # Параметры подключения к базе данных hotel_complex
    conn_params = {
        'host': 'localhost',
        'user': 'postgres',
        'password': '0911',  # Используем ваш пароль из предыдущего кода
        'database': 'hotel_complex'
    }

    # Список пользователей для добавления
    users = [
        ('admin', 'admin_password', 'admin'),  # Администратор (Full CRUD для всех сущностей)
        ('service', 'service_password', 'service')  # Сервисная служба (ограниченный доступ)
    ]

    conn = None
    try:
        # Подключение к базе данных
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor()

        # Проверяем наличие таблицы пользователей
        cursor.execute("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'users')")
        table_exists = cursor.fetchone()[0]

        if not table_exists:
            print("Таблица пользователей не существует. Создайте её с помощью database_setup.py")
            return False

        # Добавляем пользователей
        for username, password, role in users:
            # Проверяем, существует ли уже пользователь с таким именем
            cursor.execute("SELECT 1 FROM users WHERE username = %s", (username,))
            if cursor.fetchone():
                print(f"Пользователь '{username}' уже существует. Пропускаем.")
                continue

            # Добавляем нового пользователя
            cursor.execute("""
                INSERT INTO users (username, password, role)
                VALUES (%s, %s, %s)
            """, (username, password, role))

            print(f"Пользователь '{username}' с ролью '{role}' успешно добавлен.")

        # Фиксация изменений
        conn.commit()
        print("Все пользователи успешно добавлены.")

    except Exception as e:
        print(f"Ошибка при добавлении пользователей: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return True


if __name__ == "__main__":
    add_users()

# if __name__ == "__main__":
#     seed_database()