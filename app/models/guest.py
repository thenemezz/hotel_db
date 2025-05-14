from app.utils.db import execute_query


class Guest:
    @staticmethod
    def get_all():
        """Получение всех гостей"""
        query = """
            SELECT * FROM guest 
            ORDER BY last_name, first_name
        """
        return execute_query(query)

    @staticmethod
    def get_by_id(guest_id):
        """Получение гостя по ID"""
        query = "SELECT * FROM guest WHERE id = %s"
        return execute_query(query, (guest_id,), fetchone=True)

    @staticmethod
    def create(last_name, first_name, middle_name=None, passport_series=None,
               passport_number=None, phone=None, email=None):
        """Создание нового гостя"""
        query = """
            INSERT INTO guest 
            (last_name, first_name, middle_name, passport_series, passport_number, phone, email)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        params = (last_name, first_name, middle_name, passport_series,
                  passport_number, phone, email)
        return execute_query(query, params, commit=True, fetchone=True)

    @staticmethod
    def update(guest_id, last_name, first_name, middle_name=None, passport_series=None,
               passport_number=None, phone=None, email=None):
        """Обновление данных гостя"""
        query = """
            UPDATE guest 
            SET last_name = %s, first_name = %s, middle_name = %s, 
                passport_series = %s, passport_number = %s, phone = %s, email = %s
            WHERE id = %s
            RETURNING id
        """
        params = (last_name, first_name, middle_name, passport_series,
                  passport_number, phone, email, guest_id)
        return execute_query(query, params, commit=True, fetchone=True)

    @staticmethod
    def delete(guest_id):
        """Удаление гостя"""
        query = "DELETE FROM guest WHERE id = %s RETURNING id"
        return execute_query(query, (guest_id,), commit=True, fetchone=True)

    @staticmethod
    def search(search_term):
        """Поиск гостя по имени, фамилии, номеру телефона или email"""
        query = """
            SELECT * FROM guest 
            WHERE last_name ILIKE %s 
            OR first_name ILIKE %s 
            OR phone ILIKE %s 
            OR email ILIKE %s
            ORDER BY last_name, first_name
        """
        search_pattern = f"%{search_term}%"
        params = (search_pattern, search_pattern, search_pattern, search_pattern)
        return execute_query(query, params)

    @staticmethod
    def get_guest_history(guest_id):
        """Получение истории бронирований гостя"""
        query = """
            SELECT b.id, b.check_in_date, b.check_out_date, b.status, b.total_rooms, b.total_persons,
                  (SELECT COUNT(*) FROM service_usage su WHERE su.guest_id = %s AND su.booking_id = b.id) as services_count,
                  (SELECT SUM(su.cost) FROM service_usage su WHERE su.guest_id = %s AND su.booking_id = b.id) as services_cost,
                  (SELECT STRING_AGG(h.name, ', ') 
                   FROM booking_room br 
                   JOIN room r ON br.room_id = r.id 
                   JOIN hotel h ON r.hotel_id = h.id 
                   WHERE br.booking_id = b.id) as hotels
            FROM booking b
            WHERE b.guest_id = %s
            ORDER BY b.check_in_date DESC
        """
        return execute_query(query, (guest_id, guest_id, guest_id))

    @staticmethod
    def get_guests_by_room_types(room_capacity=None, hotel_rating=None, start_date=None, end_date=None):
        """
        Получение гостей, заселявшихся в номера с указанными характеристиками
        за определенный период

        Args:
            room_capacity (int, optional): Вместимость номера
            hotel_rating (int, optional): Рейтинг отеля
            start_date (date, optional): Начальная дата периода
            end_date (date, optional): Конечная дата периода

        Returns:
            list: Список гостей
        """
        params = []
        conditions = []

        base_query = """
            SELECT DISTINCT g.*,
                   COUNT(DISTINCT b.id) as bookings_count
            FROM guest g
            JOIN booking b ON g.id = b.guest_id
            JOIN booking_room br ON b.id = br.booking_id
            JOIN room r ON br.room_id = r.id
            JOIN hotel h ON r.hotel_id = h.id
            WHERE b.status != 'Отменено'
        """

        if room_capacity:
            conditions.append("r.room_capacity = %s")
            params.append(room_capacity)

        if hotel_rating:
            conditions.append("h.rating = %s")
            params.append(hotel_rating)

        if start_date:
            conditions.append("b.check_in_date >= %s")
            params.append(start_date)

        if end_date:
            conditions.append("b.check_out_date <= %s")
            params.append(end_date)

        if conditions:
            base_query += " AND " + " AND ".join(conditions)

        base_query += """
            GROUP BY g.id
            ORDER BY bookings_count DESC, g.last_name, g.first_name
        """

        return execute_query(base_query, tuple(params))