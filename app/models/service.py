from app.utils.db import execute_query
from datetime import date


class ServiceType:
    @staticmethod
    def get_all():
        """Получение всех типов услуг"""
        query = """
            SELECT * FROM service_type
            ORDER BY name
        """
        return execute_query(query)

    @staticmethod
    def get_by_id(service_type_id):
        """Получение типа услуги по ID"""
        query = "SELECT * FROM service_type WHERE id = %s"
        return execute_query(query, (service_type_id,), fetchone=True)

    @staticmethod
    def create(name, base_price, is_active=True):
        """Создание нового типа услуги"""
        query = """
            INSERT INTO service_type 
            (name, base_price, is_active)
            VALUES (%s, %s, %s)
            RETURNING id
        """
        params = (name, base_price, is_active)
        return execute_query(query, params, commit=True, fetchone=True)

    @staticmethod
    def update(service_type_id, name, base_price, is_active=True):
        """Обновление данных типа услуги"""
        query = """
            UPDATE service_type 
            SET name = %s, base_price = %s, is_active = %s
            WHERE id = %s
            RETURNING id
        """
        params = (name, base_price, is_active, service_type_id)
        return execute_query(query, params, commit=True, fetchone=True)

    @staticmethod
    def delete(service_type_id):
        """Удаление типа услуги"""
        query = "DELETE FROM service_type WHERE id = %s RETURNING id"
        return execute_query(query, (service_type_id,), commit=True, fetchone=True)

    @staticmethod
    def get_active():
        """Получение всех активных типов услуг"""
        query = """
            SELECT * FROM service_type
            WHERE is_active = TRUE
            ORDER BY name
        """
        return execute_query(query)


class ServiceUsage:
    @staticmethod
    def get_all():
        """Получение всех использованных услуг"""
        query = """
            SELECT su.*, 
                  st.name as service_name, 
                  g.last_name || ' ' || g.first_name as guest_name,
                  r.room_number,
                  h.name as hotel_name
            FROM service_usage su
            JOIN service_type st ON su.service_type_id = st.id
            JOIN guest g ON su.guest_id = g.id
            LEFT JOIN room r ON su.room_id = r.id
            LEFT JOIN hotel h ON r.hotel_id = h.id
            ORDER BY su.usage_date DESC
        """
        return execute_query(query)

    @staticmethod
    def get_by_id(service_usage_id):
        """Получение использованной услуги по ID"""
        query = """
            SELECT su.*, 
                  st.name as service_name, 
                  g.last_name || ' ' || g.first_name as guest_name,
                  r.room_number,
                  h.name as hotel_name
            FROM service_usage su
            JOIN service_type st ON su.service_type_id = st.id
            JOIN guest g ON su.guest_id = g.id
            LEFT JOIN room r ON su.room_id = r.id
            LEFT JOIN hotel h ON r.hotel_id = h.id
            WHERE su.id = %s
        """
        return execute_query(query, (service_usage_id,), fetchone=True)

    @staticmethod
    def create(guest_id, service_type_id, cost, usage_date=None, booking_id=None, room_id=None, paid=False):
        """Создание новой использованной услуги"""
        if not usage_date:
            usage_date = date.today()

        query = """
            INSERT INTO service_usage 
            (guest_id, service_type_id, cost, usage_date, booking_id, room_id, paid)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        params = (guest_id, service_type_id, cost, usage_date, booking_id, room_id, paid)
        return execute_query(query, params, commit=True, fetchone=True)

    @staticmethod
    def update(service_usage_id, guest_id, service_type_id, cost, usage_date, booking_id=None, room_id=None,
               paid=False):
        """Обновление данных использованной услуги"""
        query = """
            UPDATE service_usage 
            SET guest_id = %s, service_type_id = %s, cost = %s, usage_date = %s,
                booking_id = %s, room_id = %s, paid = %s
            WHERE id = %s
            RETURNING id
        """
        params = (guest_id, service_type_id, cost, usage_date, booking_id, room_id, paid, service_usage_id)
        return execute_query(query, params, commit=True, fetchone=True)

    @staticmethod
    def delete(service_usage_id):
        """Удаление использованной услуги"""
        query = "DELETE FROM service_usage WHERE id = %s RETURNING id"
        return execute_query(query, (service_usage_id,), commit=True, fetchone=True)

    @staticmethod
    def mark_as_paid(service_usage_id):
        """Отметить услугу как оплаченную"""
        query = """
            UPDATE service_usage 
            SET paid = TRUE
            WHERE id = %s
            RETURNING id
        """
        return execute_query(query, (service_usage_id,), commit=True, fetchone=True)

    @staticmethod
    def get_by_guest(guest_id, paid=None):
        """
        Получение услуг по гостю

        Args:
            guest_id (int): ID гостя
            paid (bool, optional): Статус оплаты (None - все услуги)

        Returns:
            list: Список услуг
        """
        params = [guest_id]

        query = """
            SELECT su.*, 
                  st.name as service_name, 
                  r.room_number,
                  h.name as hotel_name,
                  b.check_in_date, b.check_out_date
            FROM service_usage su
            JOIN service_type st ON su.service_type_id = st.id
            LEFT JOIN room r ON su.room_id = r.id
            LEFT JOIN hotel h ON r.hotel_id = h.id
            LEFT JOIN booking b ON su.booking_id = b.id
            WHERE su.guest_id = %s
        """

        if paid is not None:
            query += " AND su.paid = %s"
            params.append(paid)

        query += " ORDER BY su.usage_date DESC"

        return execute_query(query, tuple(params))

    @staticmethod
    def get_by_booking(booking_id):
        """Получение услуг по бронированию"""
        query = """
            SELECT su.*, 
                  st.name as service_name, 
                  g.last_name || ' ' || g.first_name as guest_name,
                  r.room_number,
                  h.name as hotel_name
            FROM service_usage su
            JOIN service_type st ON su.service_type_id = st.id
            JOIN guest g ON su.guest_id = g.id
            LEFT JOIN room r ON su.room_id = r.id
            LEFT JOIN hotel h ON r.hotel_id = h.id
            WHERE su.booking_id = %s
            ORDER BY su.usage_date
        """
        return execute_query(query, (booking_id,))

    @staticmethod
    def get_service_stats(start_date=None, end_date=None):
        """
        Получение статистики по использованным услугам

        Args:
            start_date (date, optional): Начальная дата
            end_date (date, optional): Конечная дата

        Returns:
            dict: Статистика по услугам
        """
        params = []
        conditions = []

        # Запрос для общей статистики
        stats_query = """
            SELECT 
                COUNT(*) as total_services,
                SUM(cost) as total_revenue,
                SUM(CASE WHEN paid = TRUE THEN cost ELSE 0 END) as paid_amount,
                SUM(CASE WHEN paid = FALSE THEN cost ELSE 0 END) as unpaid_amount,
                COUNT(DISTINCT guest_id) as unique_guests
            FROM service_usage
        """

        if start_date:
            conditions.append("usage_date >= %s")
            params.append(start_date)

        if end_date:
            conditions.append("usage_date <= %s")
            params.append(end_date)

        if conditions:
            stats_query += " WHERE " + " AND ".join(conditions)

        stats = execute_query(stats_query, tuple(params), fetchone=True)

        # Запрос для популярности услуг
        popular_query = """
            SELECT st.id, st.name, 
                  COUNT(*) as usage_count,
                  SUM(su.cost) as total_revenue
            FROM service_usage su
            JOIN service_type st ON su.service_type_id = st.id
        """

        if conditions:
            popular_query += " WHERE " + " AND ".join(conditions)

        popular_query += """
            GROUP BY st.id, st.name
            ORDER BY usage_count DESC
        """

        popular_services = execute_query(popular_query, tuple(params))

        # Объединяем все данные
        result = {
            'general_stats': stats,
            'popular_services': popular_services
        }

        return result