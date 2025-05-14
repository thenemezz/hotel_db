from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.models.user import User

bp = Blueprint('auth', __name__)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = 'remember' in request.form

        if User.verify_password(username, password):
            user_data = User.get_by_username(username)

            # Создаем того же UserWrapper, что и в user_loader
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

            user = UserWrapper(user_data)
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for('main.index'))
        else:
            flash('Неверное имя пользователя или пароль.', 'danger')

    return render_template('auth/login.html')


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы.', 'info')
    return redirect(url_for('auth.login'))