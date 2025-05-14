from app.utils.db import execute_query
from datetime import date


class Booking:
    @staticmethod
    def get_all():
        """Получение всех бронирований"""
        query = """
            SELECT b.*,
                  COALESCE(g.last_name || ' ' || g.first_name, f.name) as booked_by,
                  (SELECT STRING_AGG(r.room_number, ', ')
                   FROM booking_room br
                   JOIN room r ON br.room_id = r.id
                   WHERE br.booking_id = b.id) as room_numbers
            FROM booking b
            LEFT JOIN guest g ON b.guest_id = g.id
            LEFT JOIN firm f ON b.firm_id = f.id
            ORDER BY b.check_in_date DESC
        """
        return execute_query(query)

    @staticmethod
    def get_by_id(booking_id):
        """Получение бронирования по ID"""
        query = """
            SELECT b.*,
                  g.last_name, g.first_name, g.middle_name, g.phone as guest_phone,
                  f.name as firm_name, f.phone as firm_phone
            FROM booking b
            LEFT JOIN guest g ON b.guest_id = g.id
            LEFT JOIN firm f ON b.firm_id = f.id
            WHERE b.id = %s
        """
        booking = execute_query(query, (booking_id,), fetchone=True)

        if booking:
            # Получаем связанные номера
            rooms_query = """
                SELECT r.*, h.name as hotel_name, h.rating as hotel_rating
                FROM booking_room br
                JOIN room r ON br.room_id = r.id
                JOIN hotel h ON r.hotel_id = h.id
                WHERE br.booking_id = %s
            """
            rooms = execute_query(rooms_query, (booking_id,))
            booking['rooms'] = rooms

            # Получаем связанные услуги
            services_query = """
                SELECT su.*, st.name as service_name
                FROM service_usage su
                JOIN service_type st ON su.service_type_id = st.id
                WHERE su.booking_id = %s
                ORDER BY su.usage_date
            """
            services = execute_query(services_query, (booking_id,))
            booking['services'] = services

        return booking

    @staticmethod
    def create(firm_id=None, guest_id=None, total_rooms=0, total_persons=0,
               check_in_date=None, check_out_date=None, booking_date=None, status='Забронировано'):
        """Создание нового бронирования"""
        if not booking_date:
            booking_date = date.today()

        query = """
            INSERT INTO booking 
            (firm_id, guest_id, total_rooms, total_persons, check_in_date, check_out_date, booking_date, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        params = (firm_id, guest_id, total_rooms, total_persons,
                  check_in_date, check_out_date, booking_date, status)
        return execute_query(query, params, commit=True, fetchone=True)

    @staticmethod
    def update(booking_id, firm_id=None, guest_id=None, total_rooms=0, total_persons=0,
               check_in_date=None, check_out_date=None, booking_date=None, status='Забронировано'):
        """Обновление данных бронирования"""
        query = """
            UPDATE booking 
            SET firm_id = %s, guest_id = %s, total_rooms = %s, total_persons = %s,
                check_in_date = %s, check_out_date = %s, booking_date = %s, status = %s
            WHERE id = %s
            RETURNING id
        """
        params = (firm_id, guest_id, total_rooms, total_persons,
                  check_in_date, check_out_date, booking_date, status, booking_id)
        return execute_query(query, params, commit=True, fetchone=True)

    @staticmethod
    def delete(booking_id):
        """Удаление бронирования"""
        query = "DELETE FROM booking WHERE id = %s RETURNING id"
        return execute_query(query, (booking_id,), commit=True, fetchone=True)

    @staticmethod
    def add_room(booking_id, room_id):
        """Добавление номера к бронированию"""
        query = """
            INSERT INTO booking_room (booking_id, room_id)
            VALUES (%s, %s)
            ON CONFLICT (booking_id, room_id) DO NOTHING
            RETURNING booking_id
        """
        return execute_query(query, (booking_id, room_id), commit=True, fetchone=True)

    @staticmethod
    def remove_room(booking_id, room_id):
        """Удаление номера из бронирования"""
        query = """
            DELETE FROM booking_room 
            WHERE booking_id = %s AND room_id = %s
            RETURNING booking_id
        """
        return execute_query(query, (booking_id, room_id), commit=True, fetchone=True)

    @staticmethod
    def get_rooms(booking_id):
        """Получение всех номеров для бронирования"""
        query = """
            SELECT r.*, h.name as hotel_name, h.rating as hotel_rating
            FROM booking_room br
            JOIN room r ON br.room_id = r.id
            JOIN hotel h ON r.hotel_id = h.id
            WHERE br.booking_id = %s
            ORDER BY h.name, r.floor_number, r.room_number
        """
        return execute_query(query, (booking_id,))

    @staticmethod
    def update_status(booking_id, status):
        """Обновление статуса бронирования"""
        query = """
            UPDATE booking 
            SET status = %s
            WHERE id = %s
            RETURNING id
        """
        return execute_query(query, (status, booking_id), commit=True, fetchone=True)

    @staticmethod
    def get_active_bookings():
        """Получение активных бронирований (текущие и будущие)"""
        query = """
            SELECT b.*,
                  COALESCE(g.last_name || ' ' || g.first_name, f.name) as booked_by,
                  (SELECT STRING_AGG(h.name || ' №' || r.room_number, ', ')
                   FROM booking_room br
                   JOIN room r ON br.room_id = r.id
                   JOIN hotel h ON r.hotel_id = h.id
                   WHERE br.booking_id = b.id) as rooms
            FROM booking b
            LEFT JOIN guest g ON b.guest_id = g.id
            LEFT JOIN firm f ON b.firm_id = f.id
            WHERE b.status = 'Забронировано'
            AND b.check_out_date >= CURRENT_DATE
            ORDER BY b.check_in_date
        """
        return execute_query(query)

    @staticmethod
    def get_rooms_to_be_freed_by_date(target_date):
        """
        Получение списка занятых номеров, которые освободятся к указанному сроку

        Args:
            target_date (date): Целевая дата

        Returns:
            list: Список номеров с информацией о бронировании
        """
        query = """
            SELECT r.id as room_id, r.room_number, r.floor_number, 
                  r.room_capacity, r.base_rate,
                  h.id as hotel_id, h.name as hotel_name, h.rating,
                  b.id as booking_id, b.check_in_date, b.check_out_date,
                  COALESCE(g.last_name || ' ' || g.first_name, f.name) as booked_by
            FROM room r
            JOIN hotel h ON r.hotel_id = h.id
            JOIN booking_room br ON r.id = br.room_id
            JOIN booking b ON br.booking_id = b.id
            LEFT JOIN guest g ON b.guest_id = g.id
            LEFT JOIN firm f ON b.firm_id = f.id
            WHERE b.status = 'Забронировано'
            AND b.check_out_date <= %s
            AND b.check_out_date >= CURRENT_DATE
            ORDER BY b.check_out_date, h.name, r.floor_number, r.room_number
        """
        return execute_query(query, (target_date,))

    @staticmethod
    def calculate_total_cost(booking_id):
        """
        Расчет общей стоимости бронирования (номера + услуги)

        Args:
            booking_id (int): ID бронирования

        Returns:
            dict: Сводка по стоимости
        """
        # Получаем данные о бронировании
        booking = Booking.get_by_id(booking_id)

        if not booking:
            return None

        # Расчет стоимости номеров
        rooms_cost = 0
        if 'rooms' in booking and booking['rooms']:
            for room in booking['rooms']:
                # Количество дней пребывания
                days = (booking['check_out_date'] - booking['check_in_date']).days
                room_total = room['base_rate'] * days
                rooms_cost += room_total

        # Расчет стоимости услуг
        services_cost = 0
        services_paid = 0
        services_unpaid = 0

        if 'services' in booking and booking['services']:
            for service in booking['services']:
                services_cost += service['cost']
                if service['paid']:
                    services_paid += service['cost']
                else:
                    services_unpaid += service['cost']

        # Применение скидки если бронирование от фирмы
        discount_rate = 0
        if booking['firm_id']:
            discount_query = """
                SELECT discount_rate FROM contract
                WHERE firm_id = %s
                AND contract_start_date <= %s
                AND contract_end_date >= %s
                ORDER BY discount_rate DESC
                LIMIT 1
            """
            discount_result = execute_query(
                discount_query,
                (booking['firm_id'], booking['booking_date'], booking['booking_date']),
                fetchone=True
            )

            if discount_result and 'discount_rate' in discount_result:
                discount_rate = discount_result['discount_rate']

        # Расчет итоговой стоимости с учетом скидки
        discount_amount = rooms_cost * (discount_rate / 100) if discount_rate > 0 else 0
        total_cost = rooms_cost - discount_amount + services_cost

        return {
            'booking_id': booking_id,
            'check_in_date': booking['check_in_date'],
            'check_out_date': booking['check_out_date'],
            'days': (booking['check_out_date'] - booking['check_in_date']).days,
            'rooms_cost': rooms_cost,
            'discount_rate': discount_rate,
            'discount_amount': discount_amount,
            'services_cost': services_cost,
            'services_paid': services_paid,
            'services_unpaid': services_unpaid,
            'total_cost': total_cost,
            'balance_due': total_cost - services_paid
        }