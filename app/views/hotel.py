from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort
from flask_login import login_required, current_user
from app.models.hotel import Hotel
from app.models.room import Room

bp = Blueprint('hotel', __name__)


@bp.route('/')
@login_required
def index():
    """Список всех отелей"""
    # Проверка прав доступа
    if not current_user.has_access('hotel', 'read'):
        abort(403)  # Forbidden - доступ запрещен

    hotels = Hotel.get_all()
    return render_template('hotels/index.html', hotels=hotels)


@bp.route('/<int:hotel_id>')
@login_required
def show(hotel_id):
    """Информация об отеле"""
    # Проверка прав доступа
    if not current_user.has_access('hotel', 'read'):
        abort(403)  # Forbidden - доступ запрещен

    hotel = Hotel.get_by_id(hotel_id)
    if not hotel:
        flash('Отель не найден', 'error')
        return redirect(url_for('hotel.index'))

    # Получаем все номера этого отеля
    rooms = Room.get_available_rooms(hotel_id=hotel_id)

    return render_template('hotels/show.html', hotel=hotel, rooms=rooms)


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Форма создания нового отеля"""
    # Проверка прав доступа
    if not current_user.has_access('hotel', 'create'):
        abort(403)  # Forbidden - доступ запрещен

    if request.method == 'POST':
        # Получаем данные из формы
        name = request.form.get('name')
        rating = int(request.form.get('rating', 3))
        floors = int(request.form.get('floors', 1))
        room_count = int(request.form.get('room_count', 0))

        # Получаем значения чекбоксов
        has_housekeeping = 'has_housekeeping' in request.form
        has_laundry = 'has_laundry' in request.form
        has_dry_cleaning = 'has_dry_cleaning' in request.form
        has_restaurant = 'has_restaurant' in request.form
        has_bar = 'has_bar' in request.form
        has_pool_sauna = 'has_pool_sauna' in request.form
        has_billiards = 'has_billiards' in request.form

        # Создаем отель
        result = Hotel.create(
            name=name,
            rating=rating,
            floors=floors,
            room_count=room_count,
            has_housekeeping=has_housekeeping,
            has_laundry=has_laundry,
            has_dry_cleaning=has_dry_cleaning,
            has_restaurant=has_restaurant,
            has_bar=has_bar,
            has_pool_sauna=has_pool_sauna,
            has_billiards=has_billiards
        )

        if result and 'id' in result:
            flash('Отель успешно создан', 'success')
            return redirect(url_for('hotel.show', hotel_id=result['id']))
        else:
            flash('Ошибка при создании отеля', 'error')

    return render_template('hotels/create.html')


@bp.route('/<int:hotel_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(hotel_id):
    """Форма редактирования отеля"""
    # Проверка прав доступа
    if not current_user.has_access('hotel', 'update'):
        abort(403)  # Forbidden - доступ запрещен

    hotel = Hotel.get_by_id(hotel_id)
    if not hotel:
        flash('Отель не найден', 'error')
        return redirect(url_for('hotel.index'))

    if request.method == 'POST':
        # Получаем данные из формы
        name = request.form.get('name')
        rating = int(request.form.get('rating', 3))
        floors = int(request.form.get('floors', 1))
        room_count = int(request.form.get('room_count', 0))

        # Получаем значения чекбоксов
        has_housekeeping = 'has_housekeeping' in request.form
        has_laundry = 'has_laundry' in request.form
        has_dry_cleaning = 'has_dry_cleaning' in request.form
        has_restaurant = 'has_restaurant' in request.form
        has_bar = 'has_bar' in request.form
        has_pool_sauna = 'has_pool_sauna' in request.form
        has_billiards = 'has_billiards' in request.form

        # Обновляем отель
        result = Hotel.update(
            hotel_id=hotel_id,
            name=name,
            rating=rating,
            floors=floors,
            room_count=room_count,
            has_housekeeping=has_housekeeping,
            has_laundry=has_laundry,
            has_dry_cleaning=has_dry_cleaning,
            has_restaurant=has_restaurant,
            has_bar=has_bar,
            has_pool_sauna=has_pool_sauna,
            has_billiards=has_billiards
        )

        if result and 'id' in result:
            flash('Отель успешно обновлен', 'success')
            return redirect(url_for('hotel.show', hotel_id=hotel_id))
        else:
            flash('Ошибка при обновлении отеля', 'error')

    return render_template('hotels/edit.html', hotel=hotel)


@bp.route('/<int:hotel_id>/delete', methods=['POST'])
@login_required
def delete(hotel_id):
    """Удаление отеля"""
    # Проверка прав доступа
    if not current_user.has_access('hotel', 'delete'):
        abort(403)  # Forbidden - доступ запрещен

    hotel = Hotel.get_by_id(hotel_id)
    if not hotel:
        flash('Отель не найден', 'error')
    else:
        result = Hotel.delete(hotel_id)
        if result and 'id' in result:
            flash('Отель успешно удален', 'success')
        else:
            flash('Ошибка при удалении отеля', 'error')

    return redirect(url_for('hotel.index'))


@bp.route('/api/hotels', methods=['GET'])
@login_required
def api_hotels():
    """API для получения списка отелей"""
    # Проверка прав доступа
    if not current_user.has_access('hotel', 'read'):
        return jsonify({'error': 'Доступ запрещен'}), 403

    hotels = Hotel.get_all()
    return jsonify(hotels)