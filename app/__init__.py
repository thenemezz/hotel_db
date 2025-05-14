import os
from flask import Flask, redirect, url_for, render_template
from app.config import config
from markupsafe import Markup
from flask_login import LoginManager, current_user

# Создаем экземпляр LoginManager
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Пожалуйста, войдите для доступа к этой странице.'
login_manager.login_message_category = 'info'


def create_app(config_name=None):
    """Фабрика создания Flask-приложения"""

    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG', 'default')

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Инициализация Flask-Login
    login_manager.init_app(app)

    # Добавляем фильтр nl2br
    @app.template_filter('nl2br')
    def nl2br_filter(s):
        if s is None:
            return ""
        return Markup(s.replace('\n', '<br>'))

    # Функция загрузки пользователя для Flask-Login
    from app.models.user import User
    @login_manager.user_loader
    def load_user(user_id):
        user_data = User.get_by_id(int(user_id))
        if user_data:
            # Создаем анонимный класс, реализующий интерфейс UserMixin
            class UserWrapper:
                def __init__(self, user_data):
                    self.id = user_data['id']
                    self.username = user_data['username']
                    self.role = user_data['role']
                    self._user_data = user_data

                def get_id(self):
                    return str(self.id)

                @property
                def is_authenticated(self):
                    return True

                @property
                def is_active(self):
                    return True

                @property
                def is_anonymous(self):
                    return False

                def has_access(self, entity, action):
                    return User.has_access(self._user_data, entity, action)

            return UserWrapper(user_data)
        return None

    # Регистрация маршрутов
    from app.views import main as main_blueprint
    from app.views import hotel as hotel_blueprint
    from app.views import room as room_blueprint
    from app.views import booking as booking_blueprint
    from app.views import firm as firm_blueprint
    from app.views import guest as guest_blueprint
    from app.views import service as service_blueprint
    from app.views import complaint as complaint_blueprint
    from app.views import auth as auth_blueprint
    from app.views import admin_queries

    app.register_blueprint(main_blueprint.bp)
    app.register_blueprint(hotel_blueprint.bp, url_prefix='/hotels')
    app.register_blueprint(room_blueprint.bp, url_prefix='/rooms')
    app.register_blueprint(booking_blueprint.bp, url_prefix='/bookings')
    app.register_blueprint(firm_blueprint.bp, url_prefix='/firms')
    app.register_blueprint(guest_blueprint.bp, url_prefix='/guests')
    app.register_blueprint(service_blueprint.bp, url_prefix='/services')
    app.register_blueprint(complaint_blueprint.bp, url_prefix='/complaints')
    app.register_blueprint(auth_blueprint.bp, url_prefix='/auth')
    app.register_blueprint(admin_queries.bp)

    # Проверка прав доступа на каждый запрос
    @app.before_request
    def check_user_access():
        # Реализация проверки доступа
        pass

    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403

    return app