from app.utils.db import execute_query
from datetime import date


class Complaint:
    @staticmethod
    def get_all():
        """Получение всех жалоб"""
        query = """
            SELECT c.*, 
                  g.last_name || ' ' || g.first_name as guest_name,
                  g.phone as guest_phone
            FROM complaint c
            JOIN guest g ON c.guest_id = g.id
            ORDER BY c.complaint_date DESC
        """
        return execute_query(query)

    @staticmethod
    def get_by_id(complaint_id):
        """Получение жалобы по ID"""
        query = """
            SELECT c.*, 
                  g.last_name, g.first_name, g.middle_name,
                  g.phone as guest_phone, g.email as guest_email
            FROM complaint c
            JOIN guest g ON c.guest_id = g.id
            WHERE c.id = %s
        """
        return execute_query(query, (complaint_id,), fetchone=True)

    @staticmethod
    def create(guest_id, description, complaint_date=None, resolved=False, resolution_date=None,
               resolution_details=None):
        """Создание новой жалобы"""
        if not complaint_date:
            complaint_date = date.today()

        query = """
            INSERT INTO complaint 
            (guest_id, description, complaint_date, resolved, resolution_date, resolution_details)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        params = (guest_id, description, complaint_date, resolved, resolution_date, resolution_details)
        return execute_query(query, params, commit=True, fetchone=True)

    @staticmethod
    def update(complaint_id, guest_id, description, complaint_date, resolved=False, resolution_date=None,
               resolution_details=None):
        """Обновление данных жалобы"""
        query = """
            UPDATE complaint 
            SET guest_id = %s, description = %s, complaint_date = %s,
                resolved = %s, resolution_date = %s, resolution_details = %s
            WHERE id = %s
            RETURNING id
        """
        params = (guest_id, description, complaint_date, resolved, resolution_date, resolution_details, complaint_id)
        return execute_query(query, params, commit=True, fetchone=True)

    @staticmethod
    def delete(complaint_id):
        """Удаление жалобы"""
        query = "DELETE FROM complaint WHERE id = %s RETURNING id"
        return execute_query(query, (complaint_id,), commit=True, fetchone=True)

    @staticmethod
    def resolve(complaint_id, resolution_details):
        """Отметить жалобу как разрешенную"""
        resolution_date = date.today()

        query = """
            UPDATE complaint 
            SET resolved = TRUE,
                resolution_date = %s,
                resolution_details = %s
            WHERE id = %s
            RETURNING id
        """
        return execute_query(query, (resolution_date, resolution_details, complaint_id), commit=True, fetchone=True)

    @staticmethod
    def get_unresolved():
        """Получение всех неразрешенных жалоб"""
        query = """
            SELECT c.*, 
                  g.last_name || ' ' || g.first_name as guest_name,
                  g.phone as guest_phone
            FROM complaint c
            JOIN guest g ON c.guest_id = g.id
            WHERE c.resolved = FALSE
            ORDER BY c.complaint_date ASC
        """
        return execute_query(query)

    @staticmethod
    def get_by_guest(guest_id):
        """Получение жалоб по гостю"""
        query = """
            SELECT c.* 
            FROM complaint c
            WHERE c.guest_id = %s
            ORDER BY c.complaint_date DESC
        """
        return execute_query(query, (guest_id,))

    @staticmethod
    def get_complaint_stats(start_date=None, end_date=None):
        """
        Получение статистики по жалобам

        Args:
            start_date (date, optional): Начальная дата
            end_date (date, optional): Конечная дата

        Returns:
            dict: Статистика по жалобам
        """
        params = []
        conditions = []

        # Запрос для общей статистики
        stats_query = """
            SELECT 
                COUNT(*) as total_complaints,
                COUNT(CASE WHEN resolved = TRUE THEN 1 END) as resolved_complaints,
                COUNT(CASE WHEN resolved = FALSE THEN 1 END) as unresolved_complaints,
                AVG(CASE WHEN resolved = TRUE THEN EXTRACT(DAY FROM (resolution_date - complaint_date)) END) as avg_resolution_days,
                COUNT(DISTINCT guest_id) as unique_complainants
            FROM complaint
        """

        if start_date:
            conditions.append("complaint_date >= %s")
            params.append(start_date)

        if end_date:
            conditions.append("complaint_date <= %s")
            params.append(end_date)

        if conditions:
            stats_query += " WHERE " + " AND ".join(conditions)

        stats = execute_query(stats_query, tuple(params), fetchone=True)

        # Запрос для частоты жалоб по месяцам
        monthly_query = """
            SELECT 
                EXTRACT(YEAR FROM complaint_date) as year,
                EXTRACT(MONTH FROM complaint_date) as month,
                COUNT(*) as complaints_count,
                COUNT(CASE WHEN resolved = TRUE THEN 1 END) as resolved_count
            FROM complaint
        """

        if conditions:
            monthly_query += " WHERE " + " AND ".join(conditions)

        monthly_query += """
            GROUP BY EXTRACT(YEAR FROM complaint_date), EXTRACT(MONTH FROM complaint_date)
            ORDER BY year DESC, month DESC
        """

        monthly_stats = execute_query(monthly_query, tuple(params))

        # Объединяем все данные
        result = {
            'general_stats': stats,
            'monthly_stats': monthly_stats
        }

        return result
    