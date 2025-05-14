from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort
from flask_login import login_required, current_user
from app.models.room import Room
from app.models.hotel import Hotel
from datetime import datetime, date

bp = Blueprint('room', __name__)


@bp.route('/')
@login_required
def index():
    """Список всех номеров"""
    # Проверка прав доступа
    if not current_user.has_access('room', 'read'):
        abort(403)  # Forbidden - доступ запрещен

    rooms = Room.get_all()
    return render_template('rooms/index.html', rooms=rooms)


@bp.route('/<int:room_id>')
@login_required
def show(room_id):
    """Информация о номере"""
    # Проверка прав доступа
    if not current_user.has_access('room', 'read'):
        abort(403)  # Forbidden - доступ запрещен

    room = Room.get_room_availability_details(room_id)
    if not room:
        flash('Номер не найден', 'error')
        return redirect(url_for('room.index'))

    return render_template('rooms/show.html', room=room)


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Форма создания нового номера"""
    # Проверка прав доступа
    if not current_user.has_access('room', 'create'):
        abort(403)  # Forbidden - доступ запрещен

    hotels = Hotel.get_all()

    if request.method == 'POST':
        # Получаем данные из формы
        hotel_id = int(request.form.get('hotel_id'))
        floor_number = int(request.form.get('floor_number', 1))
        room_number = request.form.get('room_number')
        room_capacity = int(request.form.get('room_capacity', 1))
        base_rate = float(request.form.get('base_rate', 0))
        is_available = 'is_available' in request.form

        # Создаем номер
        result = Room.create(
            hotel_id=hotel_id,
            floor_number=floor_number,
            room_number=room_number,
            room_capacity=room_capacity,
            base_rate=base_rate,
            is_available=is_available
        )

        if result and 'id' in result:
            flash('Номер успешно создан', 'success')
            return redirect(url_for('room.show', room_id=result['id']))
        else:
            flash('Ошибка при создании номера', 'error')

    return render_template('rooms/create.html', hotels=hotels)


@bp.route('/<int:room_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(room_id):
    """Форма редактирования номера"""
    # Проверка прав доступа
    if not current_user.has_access('room', 'update'):
        abort(403)  # Forbidden - доступ запрещен

    room = Room.get_by_id(room_id)
    if not room:
        flash('Номер не найден', 'error')
        return redirect(url_for('room.index'))

    hotels = Hotel.get_all()

    if request.method == 'POST':
        # Получаем данные из формы
        hotel_id = int(request.form.get('hotel_id'))
        floor_number = int(request.form.get('floor_number', 1))
        room_number = request.form.get('room_number')
        room_capacity = int(request.form.get('room_capacity', 1))
        base_rate = float(request.form.get('base_rate', 0))
        is_available = 'is_available' in request.form

        # Обновляем номер
        result = Room.update(
            room_id=room_id,
            hotel_id=hotel_id,
            floor_number=floor_number,
            room_number=room_number,
            room_capacity=room_capacity,
            base_rate=base_rate,
            is_available=is_available
        )

        if result and 'id' in result:
            flash('Номер успешно обновлен', 'success')
            return redirect(url_for('room.show', room_id=room_id))
        else:
            flash('Ошибка при обновлении номера', 'error')

    return render_template('rooms/edit.html', room=room, hotels=hotels)


@bp.route('/<int:room_id>/delete', methods=['POST'])
@login_required
def delete(room_id):
    """Удаление номера"""
    # Проверка прав доступа
    if not current_user.has_access('room', 'delete'):
        abort(403)  # Forbidden - доступ запрещен

    room = Room.get_by_id(room_id)
    if not room:
        flash('Номер не найден', 'error')
    else:
        result = Room.delete(room_id)
        if result and 'id' in result:
            flash('Номер успешно удален', 'success')
        else:
            flash('Ошибка при удалении номера', 'error')

    return redirect(url_for('room.index'))


@bp.route('/available')
@login_required
def available():
    """Список свободных номеров"""
    # Проверка прав доступа
    if not current_user.has_access('room', 'read'):
        abort(403)  # Forbidden - доступ запрещен

    # Фильтры из параметров запроса
    check_in = request.args.get('check_in')
    check_out = request.args.get('check_out')
    capacity = request.args.get('capacity')
    hotel_id = request.args.get('hotel_id')

    # Преобразование дат и чисел
    check_in_date = None
    check_out_date = None
    room_capacity = None
    hotel_id_int = None

    if check_in:
        try:
            check_in_date = datetime.strptime(check_in, '%Y-%m-%d').date()
        except ValueError:
            flash('Некорректный формат даты заезда', 'error')

    if check_out:
        try:
            check_out_date = datetime.strptime(check_out, '%Y-%m-%d').date()
        except ValueError:
            flash('Некорректный формат даты выезда', 'error')

    if capacity:
        try:
            room_capacity = int(capacity)
        except ValueError:
            flash('Некорректное значение вместимости', 'error')

    if hotel_id:
        try:
            hotel_id_int = int(hotel_id)
        except ValueError:
            flash('Некорректный ID отеля', 'error')

    # Получаем свободные номера с учетом фильтров
    rooms = Room.get_available_rooms(
        check_in_date=check_in_date,
        check_out_date=check_out_date,
        capacity=room_capacity,
        hotel_id=hotel_id_int
    )

    # Получаем список отелей для фильтра
    hotels = Hotel.get_all()

    return render_template('rooms/available.html',
                           rooms=rooms,
                           hotels=hotels,
                           check_in=check_in,
                           check_out=check_out,
                           capacity=capacity,
                           hotel_id=hotel_id)


@bp.route('/available-by-date')
@login_required
def available_by_date():
    """Список номеров, которые будут доступны к указанной дате"""
    # Проверка прав доступа
    if not current_user.has_access('room', 'read'):
        abort(403)  # Forbidden - доступ запрещен

    target_date_str = request.args.get('target_date')
    target_date = None

    if target_date_str:
        try:
            target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Некорректный формат даты', 'error')
            target_date = date.today()
    else:
        target_date = date.today()

    rooms = Room.get_rooms_available_by_date(target_date)

    return render_template('rooms/available_by_date.html',
                           rooms=rooms,
                           target_date=target_date.strftime('%Y-%m-%d'))