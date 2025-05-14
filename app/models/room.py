from app.utils.db import execute_query
from datetime import date


class Room:
    @staticmethod
    def get_all():
        """Получение всех номеров"""
        query = """
            SELECT r.*, h.name as hotel_name 
            FROM room r
            JOIN hotel h ON r.hotel_id = h.id
            ORDER BY h.name, r.floor_number, r.room_number
        """
        return execute_query(query)

    @staticmethod
    def get_by_id(room_id):
        """Получение номера по ID"""
        query = """
            SELECT r.*, h.name as hotel_name 
            FROM room r
            JOIN hotel h ON r.hotel_id = h.id
            WHERE r.id = %s
        """
        return execute_query(query, (room_id,), fetchone=True)

    @staticmethod
    def create(hotel_id, floor_number, room_number, room_capacity, base_rate, is_available=True):
        """Создание нового номера"""
        query = """
            INSERT INTO room 
            (hotel_id, floor_number, room_number, room_capacity, base_rate, is_available)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        params = (hotel_id, floor_number, room_number, room_capacity, base_rate, is_available)
        return execute_query(query, params, commit=True, fetchone=True)

    @staticmethod
    def update(room_id, hotel_id, floor_number, room_number, room_capacity, base_rate, is_available=True):
        """Обновление данных номера"""
        query = """
            UPDATE room 
            SET hotel_id = %s, floor_number = %s, room_number = %s, 
                room_capacity = %s, base_rate = %s, is_available = %s
            WHERE id = %s
            RETURNING id
        """
        params = (hotel_id, floor_number, room_number, room_capacity, base_rate, is_available, room_id)
        return execute_query(query, params, commit=True, fetchone=True)

    @staticmethod
    def delete(room_id):
        """Удаление номера"""
        query = "DELETE FROM room WHERE id = %s RETURNING id"
        return execute_query(query, (room_id,), commit=True, fetchone=True)

    @staticmethod
    def get_available_rooms(check_in_date=None, check_out_date=None, capacity=None, hotel_id=None):
        """
        Получение доступных номеров с учетом дат и параметров

        Args:
            check_in_date (date, optional): Дата заезда
            check_out_date (date, optional): Дата выезда
            capacity (int, optional): Вместимость номера
            hotel_id (int, optional): ID отеля

        Returns:
            list: Список доступных номеров
        """
        params = []
        conditions = ["r.is_available = TRUE"]

        # Базовый запрос
        query = """
            SELECT r.*, h.name as hotel_name, h.rating as hotel_rating
            FROM room r
            JOIN hotel h ON r.hotel_id = h.id
        """

        # Если указаны даты заезда и выезда, проверяем на пересечение с существующими бронированиями
        if check_in_date and check_out_date:
            query += """
                WHERE r.id NOT IN (
                    SELECT br.room_id
                    FROM booking_room br
                    JOIN booking b ON br.booking_id = b.id
                    WHERE b.status = 'Забронировано'
                    AND NOT (b.check_out_date <= %s OR b.check_in_date >= %s)
                )
            """
            params.extend([check_in_date, check_out_date])
        else:
            query += " WHERE "

        # Добавляем условие по вместимости номера
        if capacity:
            conditions.append("r.room_capacity >= %s")
            params.append(capacity)

        # Добавляем условие по ID отеля
        if hotel_id:
            conditions.append("r.hotel_id = %s")
            params.append(hotel_id)

        # Объединяем все условия
        if conditions:
            if check_in_date and check_out_date:
                query += " AND " + " AND ".join(conditions)
            else:
                query += " AND ".join(conditions)

        query += " ORDER BY h.name, r.floor_number, r.room_number"

        return execute_query(query, tuple(params))

    @staticmethod
    def get_rooms_available_by_date(target_date):
        """
        Получить список номеров, которые будут доступны к указанной дате

        Args:
            target_date (date): Целевая дата

        Returns:
            list: Список номеров
        """
        query = """
            SELECT r.*, h.name as hotel_name,
                  (SELECT MIN(b.check_out_date)
                   FROM booking b
                   JOIN booking_room br ON b.id = br.booking_id
                   WHERE br.room_id = r.id AND b.status = 'Забронировано' AND b.check_out_date > CURRENT_DATE
                  ) as next_available_date
            FROM room r
            JOIN hotel h ON r.hotel_id = h.id
            WHERE r.id IN (
                SELECT br.room_id
                FROM booking_room br
                JOIN booking b ON br.booking_id = b.id
                WHERE b.status = 'Забронировано'
                AND b.check_out_date <= %s
                AND r.id NOT IN (
                    SELECT br2.room_id
                    FROM booking_room br2
                    JOIN booking b2 ON br2.booking_id = b2.id
                    WHERE b2.status = 'Забронировано'
                    AND b2.check_out_date > %s
                    AND b2.check_in_date <= %s
                )
            )
            ORDER BY next_available_date, h.name, r.floor_number, r.room_number
        """
        return execute_query(query, (target_date, target_date, target_date))

    @staticmethod
    def get_room_availability_details(room_id):
        """
        Получить детальную информацию о доступности конкретного номера

        Args:
            room_id (int): ID номера

        Returns:
            dict: Информация о номере и его бронированиях
        """
        # Получаем информацию о номере
        room_info = Room.get_by_id(room_id)

        if not room_info:
            return None

        # Получаем текущие и будущие бронирования для этого номера
        bookings_query = """
            SELECT b.id, b.check_in_date, b.check_out_date, b.status,
                  COALESCE(g.last_name || ' ' || g.first_name, f.name) as booked_by
            FROM booking b
            JOIN booking_room br ON b.id = br.booking_id
            LEFT JOIN guest g ON b.guest_id = g.id
            LEFT JOIN firm f ON b.firm_id = f.id
            WHERE br.room_id = %s
            AND b.status = 'Забронировано'
            AND b.check_out_date >= CURRENT_DATE
            ORDER BY b.check_in_date
        """
        bookings = execute_query(bookings_query, (room_id,))

        # Добавляем бронирования к информации о номере
        room_info['bookings'] = bookings

        return room_info