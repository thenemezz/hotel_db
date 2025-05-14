from app.utils.db import execute_query


class Firm:
    @staticmethod
    def get_all():
        """Получение всех фирм"""
        query = """
            SELECT * FROM firm 
            ORDER BY name
        """
        return execute_query(query)

    @staticmethod
    def get_by_id(firm_id):
        """Получение фирмы по ID"""
        query = "SELECT * FROM firm WHERE id = %s"
        return execute_query(query, (firm_id,), fetchone=True)

    @staticmethod
    def create(name, firm_type=None, address=None, phone=None, is_active=True):
        """Создание новой фирмы"""
        query = """
            INSERT INTO firm 
            (name, firm_type, address, phone, is_active)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """
        params = (name, firm_type, address, phone, is_active)
        return execute_query(query, params, commit=True, fetchone=True)

    @staticmethod
    def update(firm_id, name, firm_type=None, address=None, phone=None, is_active=True):
        """Обновление данных фирмы"""
        query = """
            UPDATE firm 
            SET name = %s, firm_type = %s, address = %s, phone = %s, is_active = %s
            WHERE id = %s
            RETURNING id
        """
        params = (name, firm_type, address, phone, is_active, firm_id)
        return execute_query(query, params, commit=True, fetchone=True)

    @staticmethod
    def delete(firm_id):
        """Удаление фирмы"""
        query = "DELETE FROM firm WHERE id = %s RETURNING id"
        return execute_query(query, (firm_id,), commit=True, fetchone=True)

    @staticmethod
    def get_contracts(firm_id):
        """Получение всех контрактов фирмы"""
        query = """
            SELECT * FROM contract 
            WHERE firm_id = %s
            ORDER BY contract_start_date DESC
        """
        return execute_query(query, (firm_id,))

    @staticmethod
    def add_contract(firm_id, contract_start_date, contract_end_date, discount_rate):
        """Добавление нового контракта для фирмы"""
        query = """
            INSERT INTO contract 
            (firm_id, contract_start_date, contract_end_date, discount_rate)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """
        params = (firm_id, contract_start_date, contract_end_date, discount_rate)
        return execute_query(query, params, commit=True, fetchone=True)

    @staticmethod
    def get_firms_with_bookings(min_rooms=None, start_date=None, end_date=None):
        """
        Получение фирм, забронировавших места в объеме не менее указанного
        за весь период сотрудничества или за конкретный период

        Args:
            min_rooms (int, optional): Минимальное кол-во забронированных комнат
            start_date (date, optional): Начальная дата периода
            end_date (date, optional): Конечная дата периода

        Returns:
            list: Список фирм
        """
        params = []
        conditions = ["b.firm_id IS NOT NULL"]  # Убедимся, что бронирования связаны с фирмами

        base_query = """
            SELECT f.*, 
                  COUNT(DISTINCT b.id) as bookings_count,
                  SUM(b.total_rooms) as total_rooms_booked,
                  SUM(b.total_persons) as total_persons_booked,
                  (SELECT MAX(c.discount_rate) FROM contract c WHERE c.firm_id = f.id) as max_discount
            FROM firm f
            JOIN booking b ON f.id = b.firm_id
        """

        if start_date:
            conditions.append("b.booking_date >= %s")
            params.append(start_date)

        if end_date:
            conditions.append("b.booking_date <= %s")
            params.append(end_date)

        base_query += " WHERE " + " AND ".join(conditions)

        base_query += """
            GROUP BY f.id
        """

        if min_rooms:
            base_query += " HAVING SUM(b.total_rooms) >= %s"
            params.append(min_rooms)

        base_query += """
            ORDER BY total_rooms_booked DESC, f.name
        """

        return execute_query(base_query, tuple(params))

    @staticmethod
    def get_booking_preferences(firm_id, start_date=None, end_date=None):
        """
        Получение данных о предпочтениях фирмы при бронировании

        Args:
            firm_id (int): ID фирмы
            start_date (date, optional): Начальная дата периода
            end_date (date, optional): Конечная дата периода

        Returns:
            dict: Данные о предпочтениях
        """
        params = [firm_id]
        conditions = ["b.firm_id = %s"]

        # Запрос для общего объема бронирования
        bookings_query = """
            SELECT COUNT(DISTINCT b.id) as bookings_count,
                  SUM(b.total_rooms) as total_rooms,
                  SUM(b.total_persons) as total_persons,
                  AVG(EXTRACT(DAY FROM (b.check_out_date - b.check_in_date))) as avg_stay_duration,
                  COUNT(DISTINCT r.hotel_id) as different_hotels_count
            FROM booking b
            JOIN booking_room br ON b.id = br.booking_id
            JOIN room r ON br.room_id = r.id
        """

        if start_date:
            conditions.append("b.booking_date >= %s")
            params.append(start_date)

        if end_date:
            conditions.append("b.booking_date <= %s")
            params.append(end_date)

        bookings_query += " WHERE " + " AND ".join(conditions)

        bookings_summary = execute_query(bookings_query, tuple(params), fetchone=True)

        # Запрос для предпочитаемых отелей
        hotels_query = """
            SELECT h.id, h.name, h.rating,
                  COUNT(DISTINCT b.id) as bookings_count,
                  SUM(b.total_rooms) as total_rooms
            FROM booking b
            JOIN booking_room br ON b.id = br.booking_id
            JOIN room r ON br.room_id = r.id
            JOIN hotel h ON r.hotel_id = h.id
            WHERE b.firm_id = %s
        """

        if start_date:
            hotels_query += " AND b.booking_date >= %s"

        if end_date:
            hotels_query += " AND b.booking_date <= %s"

        hotels_query += """
            GROUP BY h.id, h.name, h.rating
            ORDER BY total_rooms DESC
            LIMIT 5
        """

        preferred_hotels = execute_query(hotels_query, tuple(params))

        # Запрос для предпочитаемых типов номеров
        rooms_query = """
            SELECT r.room_capacity,
                  COUNT(DISTINCT br.room_id) as rooms_count
            FROM booking b
            JOIN booking_room br ON b.id = br.booking_id
            JOIN room r ON br.room_id = r.id
            WHERE b.firm_id = %s
        """

        if start_date:
            rooms_query += " AND b.booking_date >= %s"

        if end_date:
            rooms_query += " AND b.booking_date <= %s"

        rooms_query += """
            GROUP BY r.room_capacity
            ORDER BY rooms_count DESC
        """

        preferred_room_types = execute_query(rooms_query, tuple(params))

        # Объединяем все данные
        result = {
            'bookings_summary': bookings_summary,
            'preferred_hotels': preferred_hotels,
            'preferred_room_types': preferred_room_types
        }

        return result
    