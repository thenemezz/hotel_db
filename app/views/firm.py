from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort
from flask_login import login_required, current_user
from app.models.firm import Firm
from datetime import datetime

bp = Blueprint('firm', __name__)


@bp.route('/')
@login_required
def index():
    """Список всех фирм"""
    # Проверка прав доступа
    if not current_user.has_access('firm', 'read'):
        abort(403)  # Запрещено

    firms = Firm.get_all()
    return render_template('firms/index.html', firms=firms)


@bp.route('/<int:firm_id>')
@login_required
def show(firm_id):
    """Информация о фирме"""
    # Проверка прав доступа
    if not current_user.has_access('firm', 'read'):
        abort(403)  # Запрещено

    firm = Firm.get_by_id(firm_id)
    if not firm:
        flash('Фирма не найдена', 'error')
        return redirect(url_for('firm.index'))

    # Получаем контракты фирмы
    contracts = Firm.get_contracts(firm_id)

    # Получаем статистику по бронированиям фирмы
    booking_preferences = Firm.get_booking_preferences(firm_id)

    return render_template('firms/show.html',
                           firm=firm,
                           contracts=contracts,
                           booking_preferences=booking_preferences)


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Форма создания новой фирмы"""
    # Проверка прав доступа
    if not current_user.has_access('firm', 'create'):
        abort(403)  # Запрещено

    if request.method == 'POST':
        # Получаем данные из формы
        name = request.form.get('name')
        firm_type = request.form.get('firm_type', None) or None
        address = request.form.get('address', None) or None
        phone = request.form.get('phone', None) or None
        is_active = 'is_active' in request.form

        # Создаем фирму
        result = Firm.create(
            name=name,
            firm_type=firm_type,
            address=address,
            phone=phone,
            is_active=is_active
        )

        if result and 'id' in result:
            flash('Фирма успешно создана', 'success')
            return redirect(url_for('firm.show', firm_id=result['id']))
        else:
            flash('Ошибка при создании фирмы', 'error')

    return render_template('firms/create.html')


@bp.route('/<int:firm_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(firm_id):
    """Форма редактирования фирмы"""
    # Проверка прав доступа
    if not current_user.has_access('firm', 'update'):
        abort(403)  # Запрещено

    firm = Firm.get_by_id(firm_id)
    if not firm:
        flash('Фирма не найдена', 'error')
        return redirect(url_for('firm.index'))

    if request.method == 'POST':
        # Получаем данные из формы
        name = request.form.get('name')
        firm_type = request.form.get('firm_type', None) or None
        address = request.form.get('address', None) or None
        phone = request.form.get('phone', None) or None
        is_active = 'is_active' in request.form

        # Обновляем фирму
        result = Firm.update(
            firm_id=firm_id,
            name=name,
            firm_type=firm_type,
            address=address,
            phone=phone,
            is_active=is_active
        )

        if result and 'id' in result:
            flash('Данные фирмы успешно обновлены', 'success')
            return redirect(url_for('firm.show', firm_id=firm_id))
        else:
            flash('Ошибка при обновлении данных фирмы', 'error')

    return render_template('firms/edit.html', firm=firm)


@bp.route('/<int:firm_id>/delete', methods=['POST'])
@login_required
def delete(firm_id):
    """Удаление фирмы"""
    # Проверка прав доступа
    if not current_user.has_access('firm', 'delete'):
        abort(403)  # Запрещено

    firm = Firm.get_by_id(firm_id)
    if not firm:
        flash('Фирма не найдена', 'error')
    else:
        result = Firm.delete(firm_id)
        if result and 'id' in result:
            flash('Фирма успешно удалена', 'success')
        else:
            flash('Ошибка при удалении фирмы', 'error')

    return redirect(url_for('firm.index'))


@bp.route('/<int:firm_id>/contracts', methods=['GET', 'POST'])
@login_required
def contracts(firm_id):
    """Управление контрактами фирмы"""
    # Проверка прав доступа
    if not current_user.has_access('firm', 'read'):
        abort(403)  # Запрещено для просмотра

    # Дополнительная проверка для POST запросов (создание контракта)
    if request.method == 'POST' and not current_user.has_access('firm', 'create'):
        abort(403)  # Запрещено для создания

    firm = Firm.get_by_id(firm_id)
    if not firm:
        flash('Фирма не найдена', 'error')
        return redirect(url_for('firm.index'))

    if request.method == 'POST':
        # Получаем данные из формы для нового контракта
        start_date_str = request.form.get('contract_start_date')
        end_date_str = request.form.get('contract_end_date')
        discount_rate = float(request.form.get('discount_rate', 0))

        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

            # Добавляем новый контракт
            result = Firm.add_contract(
                firm_id=firm_id,
                contract_start_date=start_date,
                contract_end_date=end_date,
                discount_rate=discount_rate
            )

            if result and 'id' in result:
                flash('Контракт успешно добавлен', 'success')
            else:
                flash('Ошибка при добавлении контракта', 'error')

        except ValueError:
            flash('Некорректный формат даты', 'error')

    # Получаем все контракты фирмы
    contracts = Firm.get_contracts(firm_id)

    return render_template('firms/contracts.html', firm=firm, contracts=contracts)


@bp.route('/with-bookings')
@login_required
def with_bookings():
    """Список фирм, забронировавших места в объеме не менее указанного"""
    # Проверка прав доступа
    if not current_user.has_access('firm', 'read'):
        abort(403)  # Запрещено

    # Фильтры из параметров запроса
    min_rooms = request.args.get('min_rooms')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    # Преобразование параметров
    min_rooms_int = None
    start_date_obj = None
    end_date_obj = None

    if min_rooms:
        try:
            min_rooms_int = int(min_rooms)
        except ValueError:
            flash('Некорректное значение минимального количества комнат', 'error')

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

    # Получаем фирмы с учетом фильтров
    firms = Firm.get_firms_with_bookings(
        min_rooms=min_rooms_int,
        start_date=start_date_obj,
        end_date=end_date_obj
    )

    return render_template('firms/with_bookings.html',
                           firms=firms,
                           min_rooms=min_rooms,
                           start_date=start_date,
                           end_date=end_date)