from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort
from flask_login import login_required, current_user
from app.models.guest import Guest
from app.models.complaint import Complaint
from app.models.service import ServiceUsage
from datetime import datetime

bp = Blueprint('guest', __name__)


@bp.route('/')
@login_required
def index():
    """Список всех гостей"""
    # Проверка прав доступа
    if not current_user.has_access('guest', 'read'):
        abort(403)  # Forbidden - доступ запрещен

    # Проверяем, есть ли параметр поиска
    search = request.args.get('search', '')

    if search:
        guests = Guest.search(search)
    else:
        guests = Guest.get_all()

    return render_template('guests/index.html', guests=guests, search=search)


@bp.route('/<int:guest_id>')
@login_required
def show(guest_id):
    """Информация о госте"""
    # Проверка прав доступа
    if not current_user.has_access('guest', 'read'):
        abort(403)  # Forbidden - доступ запрещен

    guest = Guest.get_by_id(guest_id)
    if not guest:
        flash('Гость не найден', 'error')
        return redirect(url_for('guest.index'))

    # Получаем историю бронирований гостя
    bookings = Guest.get_guest_history(guest_id)

    # Получаем жалобы гостя
    complaints = Complaint.get_by_guest(guest_id)

    # Получаем услуги гостя
    services = ServiceUsage.get_by_guest(guest_id)

    return render_template('guests/show.html',
                           guest=guest,
                           bookings=bookings,
                           complaints=complaints,
                           services=services)


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Форма создания нового гостя"""
    # Проверка прав доступа
    if not current_user.has_access('guest', 'create'):
        abort(403)  # Forbidden - доступ запрещен

    if request.method == 'POST':
        # Получаем данные из формы
        last_name = request.form.get('last_name')
        first_name = request.form.get('first_name')
        middle_name = request.form.get('middle_name', None) or None
        passport_series = request.form.get('passport_series', None) or None
        passport_number = request.form.get('passport_number', None) or None
        phone = request.form.get('phone', None) or None
        email = request.form.get('email', None) or None

        # Создаем гостя
        result = Guest.create(
            last_name=last_name,
            first_name=first_name,
            middle_name=middle_name,
            passport_series=passport_series,
            passport_number=passport_number,
            phone=phone,
            email=email
        )

        if result and 'id' in result:
            flash('Гость успешно создан', 'success')
            return redirect(url_for('guest.show', guest_id=result['id']))
        else:
            flash('Ошибка при создании гостя', 'error')

    return render_template('guests/create.html')


@bp.route('/<int:guest_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(guest_id):
    """Форма редактирования гостя"""
    # Проверка прав доступа
    if not current_user.has_access('guest', 'update'):
        abort(403)  # Forbidden - доступ запрещен

    guest = Guest.get_by_id(guest_id)
    if not guest:
        flash('Гость не найден', 'error')
        return redirect(url_for('guest.index'))

    if request.method == 'POST':
        # Получаем данные из формы
        last_name = request.form.get('last_name')
        first_name = request.form.get('first_name')
        middle_name = request.form.get('middle_name', None) or None
        passport_series = request.form.get('passport_series', None) or None
        passport_number = request.form.get('passport_number', None) or None
        phone = request.form.get('phone', None) or None
        email = request.form.get('email', None) or None

        # Обновляем гостя
        result = Guest.update(
            guest_id=guest_id,
            last_name=last_name,
            first_name=first_name,
            middle_name=middle_name,
            passport_series=passport_series,
            passport_number=passport_number,
            phone=phone,
            email=email
        )

        if result and 'id' in result:
            flash('Данные гостя успешно обновлены', 'success')
            return redirect(url_for('guest.show', guest_id=guest_id))
        else:
            flash('Ошибка при обновлении данных гостя', 'error')

    return render_template('guests/edit.html', guest=guest)


@bp.route('/<int:guest_id>/delete', methods=['POST'])
@login_required
def delete(guest_id):
    """Удаление гостя"""
    # Проверка прав доступа
    if not current_user.has_access('guest', 'delete'):
        abort(403)  # Forbidden - доступ запрещен

    guest = Guest.get_by_id(guest_id)
    if not guest:
        flash('Гость не найден', 'error')
    else:
        result = Guest.delete(guest_id)
        if result and 'id' in result:
            flash('Гость успешно удален', 'success')
        else:
            flash('Ошибка при удалении гостя', 'error')

    return redirect(url_for('guest.index'))


@bp.route('/by-room-types')
@login_required
def by_room_types():
    """Список гостей, заселявшихся в номера с указанными характеристиками"""
    # Проверка прав доступа
    if not current_user.has_access('guest', 'read'):
        abort(403)  # Forbidden - доступ запрещен

    # Фильтры из параметров запроса
    room_capacity = request.args.get('room_capacity')
    hotel_rating = request.args.get('hotel_rating')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    # Преобразование параметров
    room_capacity_int = None
    hotel_rating_int = None
    start_date_obj = None
    end_date_obj = None

    if room_capacity:
        try:
            room_capacity_int = int(room_capacity)
        except ValueError:
            flash('Некорректное значение вместимости номера', 'error')

    if hotel_rating:
        try:
            hotel_rating_int = int(hotel_rating)
        except ValueError:
            flash('Некорректное значение рейтинга отеля', 'error')

    if start_date:
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
        except ValueError:
            flash('Некорректный формат начальной даты', 'error')

    if end_date:
        try:
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            flash('Некорректный формат конечной даты', 'error')

    # Получаем гостей с учетом фильтров
    guests = Guest.get_guests_by_room_types(
        room_capacity=room_capacity_int,
        hotel_rating=hotel_rating_int,
        start_date=start_date_obj,
        end_date=end_date_obj
    )

    return render_template('guests/by_room_types.html',
                           guests=guests,
                           room_capacity=room_capacity,
                           hotel_rating=hotel_rating,
                           start_date=start_date,
                           end_date=end_date)