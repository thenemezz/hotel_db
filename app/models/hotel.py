from app.utils.db import execute_query


class Hotel:
    @staticmethod
    def get_all():
        """Получение всех отелей"""
        query = """
            SELECT h.*, 
                  (SELECT COUNT(*) FROM room r WHERE r.hotel_id = h.id) as rooms_count
            FROM hotel h
            ORDER BY h.rating DESC, h.name
        """
        return execute_query(query)

    @staticmethod
    def get_by_id(hotel_id):
        """Получение отеля по ID"""
        query = """
            SELECT h.*, 
                  (SELECT COUNT(*) FROM room r WHERE r.hotel_id = h.id) as rooms_count
            FROM hotel h
            WHERE h.id = %s
        """
        return execute_query(query, (hotel_id,), fetchone=True)

    @staticmethod
    def create(name, rating, address=None, phone=None, has_pool=False, has_sauna=False,
               has_restaurant=False, has_cleaning=True, has_laundry=False, has_spa=False):
        """Создание нового отеля"""
        query = """
            INSERT INTO hotel 
            (name, rating, address, phone, has_pool, has_sauna, has_restaurant, 
             has_cleaning, has_laundry, has_spa)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        params = (name, rating, address, phone, has_pool, has_sauna, has_restaurant,
                 has_cleaning, has_laundry, has_spa)
        return execute_query(query, params, commit=True, fetchone=True)

    @staticmethod
    def update(hotel_id, name, rating, address=None, phone=None, has_pool=False, has_sauna=False,
               has_restaurant=False, has_cleaning=True, has_laundry=False, has_spa=False):
        """Обновление данных отеля"""
        query = """
            UPDATE hotel 
            SET name = %s, rating = %s, address = %s, phone = %s, 
                has_pool = %s, has_sauna = %s, has_restaurant = %s, 
                has_cleaning = %s, has_laundry = %s, has_spa = %s
            WHERE id = %s
            RETURNING id
        """
        params = (name, rating, address, phone, has_pool, has_sauna, has_restaurant,
                 has_cleaning, has_laundry, has_spa, hotel_id)
        return execute_query(query, params, commit=True, fetchone=True)

    @staticmethod
    def delete(hotel_id):
        """Удаление отеля"""
        query = "DELETE FROM hotel WHERE id = %s RETURNING id"
        return execute_query(query, (hotel_id,), commit=True, fetchone=True)

    @staticmethod
    def get_rooms(hotel_id):
        """Получение всех номеров отеля"""
        query = """
            SELECT r.*, 
                  (SELECT COUNT(*) 
                   FROM booking_room br 
                   JOIN booking b ON br.booking_id = b.id 
                   WHERE br.room_id = r.id 
                   AND b.status = 'Активно') as is_occupied
            FROM room r
            WHERE r.hotel_id = %s
            ORDER BY r.room_number
        """
        return execute_query(query, (hotel_id,))

    @staticmethod
    def get_available_rooms(hotel_id):
        """Получение свободных номеров отеля"""
        query = """
            SELECT r.*
            FROM room r
            WHERE r.hotel_id = %s
            AND r.id NOT IN (
                SELECT br.room_id
                FROM booking_room br
                JOIN booking b ON br.booking_id = b.id
                WHERE b.status = 'Активно'
            )
            ORDER BY r.room_number
        """
        return execute_query(query, (hotel_id,))

    @staticmethod
    def get_hotel_stats():
        """Получение статистики по отелям"""
        query = """
            SELECT h.id, h.name, h.rating,
                  (SELECT COUNT(*) FROM room r WHERE r.hotel_id = h.id) as total_rooms,
                  (SELECT COUNT(*) 
                   FROM room r 
                   WHERE r.hotel_id = h.id 
                   AND r.id NOT IN (
                       SELECT br.room_id
                       FROM booking_room br
                       JOIN booking b ON br.booking_id = b.id
                       WHERE b.status = 'Активно'
                   )) as available_rooms
            FROM hotel h
            ORDER BY h.rating DESC, h.name
        """
        return execute_query(query)