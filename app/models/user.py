from app.utils.db import execute_query


class User:
    @staticmethod
    def get_by_id(user_id):
        """Получение пользователя по ID"""
        query = "SELECT * FROM users WHERE id = %s"
        return execute_query(query, (user_id,), fetchone=True)

    @staticmethod
    def get_by_username(username):
        """Получение пользователя по имени пользователя"""
        query = "SELECT * FROM users WHERE username = %s"
        return execute_query(query, (username,), fetchone=True)

    @staticmethod
    def create(username, password, role):
        """Создание нового пользователя"""
        query = """
            INSERT INTO users 
            (username, password, role)
            VALUES (%s, %s, %s)
            RETURNING id
        """
        params = (username, password, role)
        return execute_query(query, params, commit=True, fetchone=True)

    @staticmethod
    def update(user_id, username=None, password=None, role=None):
        """Обновление данных пользователя"""
        user = User.get_by_id(user_id)
        if not user:
            return None

        # Строим запрос на обновление только указанных полей
        fields = []
        params = []

        if username is not None:
            fields.append("username = %s")
            params.append(username)

        if password is not None:
            fields.append("password = %s")
            params.append(password)

        if role is not None:
            fields.append("role = %s")
            params.append(role)

        if not fields:
            return user  # Нечего обновлять

        query = f"""
            UPDATE users 
            SET {", ".join(fields)}
            WHERE id = %s
            RETURNING id
        """
        params.append(user_id)
        return execute_query(query, tuple(params), commit=True, fetchone=True)

    @staticmethod
    def verify_password(username, password):
        """Проверка пароля пользователя (без хеширования)"""
        user = User.get_by_username(username)
        if not user:
            return False
        return user['password'] == password

    @staticmethod
    def has_access(user, entity, action):
        """
        Проверка прав доступа пользователя

        Args:
            user (dict): Пользователь
            entity (str): Сущность (hotel, room, firm, и т.д.)
            action (str): Действие (create, read, update, delete)

        Returns:
            bool: True если доступ разрешен, иначе False
        """
        if not user:
            return False

        role = user['role']

        # Администратор имеет полный доступ (CRUD) ко всем сущностям
        if role == 'admin':
            return True

        # Сервисная служба имеет ограниченный доступ
        if role == 'service':
            # Полный доступ (CRUD) к ServiceType, ServiceUsage, Complaint
            if entity.lower() in ['servicetype', 'service_type', 'serviceusage', 'service_usage', 'complaint']:
                return True

            # Только чтение (R) для Hotel и Room
            if entity.lower() in ['hotel', 'room'] and action.lower() == 'read':
                return True

            # Для всех остальных сущностей доступ закрыт
            return False

        # По умолчанию доступ запрещен
        return False