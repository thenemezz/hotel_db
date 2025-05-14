from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.models.booking import Booking
from app.models.room import Room
from app.models.guest import Guest
from app.models.firm import Firm
from app.models.service import ServiceType, ServiceUsage
from datetime import datetime, date

bp = Blueprint('booking', __name__)


@bp.route('/')
def index():
    """Список всех бронирований"""
    bookings = Booking.get_all()
    return render_template('bookings/index.html', bookings=bookings)


@bp.route('/<int:booking_id>')
def show(booking_id):
    """Информация о бронировании"""
    booking = Booking.get_by_id(booking_id)
    if not booking:
        flash('Бронирование не найдено', 'error')
        return redirect(url_for('booking.index'))

    # Получаем расчет стоимости бронирования
    cost_summary = Booking.calculate_total_cost(booking_id)

    return render_template('bookings/show.html', booking=booking, cost_summary=cost_summary)


@bp.route('/create', methods=['GET', 'POST'])
def create():
    """Форма создания нового бронирования"""
    # Получаем списки гостей и фирм для выбора
    guests = Guest.get_all()
    firms = Firm.get_all()

    if request.method == 'POST':
        # Определяем тип бронирования (от гостя или от фирмы)
        booking_type = request.form.get('booking_type')

        # Получаем ID гостя или фирмы в зависимости от типа бронирования
        guest_id = None
        firm_id = None

        if booking_type == 'guest':
            guest_id = int(request.form.get('guest_id')) if request.form.get('guest_id') else None
        elif booking_type == 'firm':
            firm_id = int(request.form.get('firm_id')) if request.form.get('firm_id') else None

        # Получаем остальные данные из формы
        total_rooms = int(request.form.get('total_rooms', 1))
        total_persons = int(request.form.get('total_persons', 1))
        check_in_str = request.form.get('check_in_date')
        check_out_str = request.form.get('check_out_date')

        try:
            check_in_date = datetime.strptime(check_in_str, '%Y-%m-%d').date()
            check_out_date = datetime.strptime(check_out_str, '%Y-%m-%d').date()

            # Проверка на корректность дат
            if check_in_date >= check_out_date:
                flash('Дата заезда должна быть раньше даты выезда', 'error')
                return render_template('bookings/create.html', guests=guests, firms=firms)

            # Создаем бронирование
            result = Booking.create(
                firm_id=firm_id,
                guest_id=guest_id,
                total_rooms=total_rooms,
                total_persons=total_persons,
                check_in_date=check_in_date,
                check_out_date=check_out_date,
                booking_date=date.today(),
                status='Забронировано'
            )

            if result and 'id' in result:
                booking_id = result['id']
                flash('Бронирование успешно создано', 'success')
                return redirect(url_for('booking.rooms', booking_id=booking_id))
            else:
                flash('Ошибка при создании бронирования', 'error')

        except ValueError:
            flash('Некорректный формат даты', 'error')

    return render_template('bookings/create.html', guests=guests, firms=firms)


@bp.route('/<int:booking_id>/edit', methods=['GET', 'POST'])
def edit(booking_id):
    """Форма редактирования бронирования"""
    booking = Booking.get_by_id(booking_id)
    if not booking:
        flash('Бронирование не найдено', 'error')
        return redirect(url_for('booking.index'))

    # Получаем списки гостей и фирм для выбора
    guests = Guest.get_all()
    firms = Firm.get_all()

    if request.method == 'POST':
        # Определяем тип бронирования (от гостя или от фирмы)
        booking_type = request.form.get('booking_type')

        # Получаем ID гостя или фирмы в зависимости от типа бронирования
        guest_id = None
        firm_id = None

        if booking_type == 'guest':
            guest_id = int(request.form.get('guest_id')) if request.form.get('guest_id') else None
        elif booking_type == 'firm':
            firm_id = int(request.form.get('firm_id')) if request.form.get('firm_id') else None

        # Получаем остальные данные из формы
        total_rooms = int(request.form.get('total_rooms', 1))
        total_persons = int(request.form.get('total_persons', 1))
        check_in_str = request.form.get('check_in_date')
        check_out_str = request.form.get('check_out_date')
        status = request.form.get('status', 'Забронировано')

        try:
            check_in_date = datetime.strptime(check_in_str, '%Y-%m-%d').date()
            check_out_date = datetime.strptime(check_out_str, '%Y-%m-%d').date()

            # Проверка на корректность дат
            if check_in_date >= check_out_date:
                flash('Дата заезда должна быть раньше даты выезда', 'error')
                return render_template('bookings/edit.html', booking=booking, guests=guests, firms=firms)

            # Обновляем бронирование
            result = Booking.update(
                booking_id=booking_id,
                firm_id=firm_id,
                guest_id=guest_id,
                total_rooms=total_rooms,
                total_persons=total_persons,
                check_in_date=check_in_date,
                check_out_date=check_out_date,
                booking_date=booking['booking_date'],
                status=status
            )

            if result and 'id' in result:
                flash('Бронирование успешно обновлено', 'success')
                return redirect(url_for('booking.show', booking_id=booking_id))
            else:
                flash('Ошибка при обновлении бронирования', 'error')

        except ValueError:
            flash('Некорректный формат даты', 'error')

    return render_template('bookings/edit.html', booking=booking, guests=guests, firms=firms)


@bp.route('/<int:booking_id>/status', methods=['POST'])
def update_status(booking_id):
    """Обновление статуса бронирования"""
    booking = Booking.get_by_id(booking_id)
    if not booking:
        flash('Бронирование не найдено', 'error')
        return redirect(url_for('booking.index'))

    status = request.form.get('status')
    if status in ['Забронировано', 'Отменено', 'Завершено']:
        result = Booking.update_status(booking_id, status)
        if result and 'id' in result:
            flash(f'Статус бронирования изменен на "{status}"', 'success')
        else:
            flash('Ошибка при обновлении статуса бронирования', 'error')
    else:
        flash('Некорректный статус бронирования', 'error')

    return redirect(url_for('booking.show', booking_id=booking_id))


@bp.route('/<int:booking_id>/delete', methods=['POST'])
def delete(booking_id):
    """Удаление бронирования"""
    booking = Booking.get_by_id(booking_id)
    if not booking:
        flash('Бронирование не найдено', 'error')
    else:
        result = Booking.delete(booking_id)
        if result and 'id' in result:
            flash('Бронирование успешно удалено', 'success')
        else:
            flash('Ошибка при удалении бронирования', 'error')

    return redirect(url_for('booking.index'))


@bp.route('/<int:booking_id>/rooms', methods=['GET', 'POST'])
def rooms(booking_id):
    """Управление номерами для бронирования"""
    booking = Booking.get_by_id(booking_id)
    if not booking:
        flash('Бронирование не найдено', 'error')
        return redirect(url_for('booking.index'))

    if request.method == 'POST':
        # Добавление номера к бронированию
        room_id = int(request.form.get('room_id')) if request.form.get('room_id') else None
        if room_id:
            result = Booking.add_room(booking_id, room_id)
            if result and 'booking_id' in result:
                flash('Номер успешно добавлен к бронированию', 'success')
            else:
                flash('Ошибка при добавлении номера к бронированию', 'error')

    # Получаем текущие номера бронирования
    booking_rooms = Booking.get_rooms(booking_id)

    # Получаем доступные номера для добавления
    check_in_date = booking['check_in_date']
    check_out_date = booking['check_out_date']

    available_rooms = Room.get_available_rooms(
        check_in_date=check_in_date,
        check_out_date=check_out_date
    )

    return render_template('bookings/rooms.html',
                           booking=booking,
                           booking_rooms=booking_rooms,
                           available_rooms=available_rooms)


@bp.route('/<int:booking_id>/rooms/<int:room_id>/remove', methods=['POST'])
def remove_room(booking_id, room_id):
    """Удаление номера из бронирования"""
    booking = Booking.get_by_id(booking_id)
    if not booking:
        flash('Бронирование не найдено', 'error')
        return redirect(url_for('booking.index'))

    result = Booking.remove_room(booking_id, room_id)
    if result and 'booking_id' in result:
        flash('Номер успешно удален из бронирования', 'success')
    else:
        flash('Ошибка при удалении номера из бронирования', 'error')

    return redirect(url_for('booking.rooms', booking_id=booking_id))


@bp.route('/<int:booking_id>/services', methods=['GET', 'POST'])
def services(booking_id):
    """Управление услугами для бронирования"""
    booking = Booking.get_by_id(booking_id)
    if not booking:
        flash('Бронирование не найдено', 'error')
        return redirect(url_for('booking.index'))

    if request.method == 'POST':
        # Добавление услуги к бронированию
        service_type_id = int(request.form.get('service_type_id')) if request.form.get('service_type_id') else None
        room_id = int(request.form.get('room_id')) if request.form.get('room_id') else None
        cost = float(request.form.get('cost', 0))
        usage_date_str = request.form.get('usage_date')
        paid = 'paid' in request.form

        try:
            usage_date = datetime.strptime(usage_date_str, '%Y-%m-%d').date() if usage_date_str else date.today()

            if service_type_id and (booking['guest_id'] or booking['firm_id']):
                # Если бронирование от фирмы, нужно указать гостя для услуги
                guest_id = booking['guest_id']
                if not guest_id and request.form.get('guest_id'):
                    guest_id = int(request.form.get('guest_id'))

                if guest_id or booking['guest_id']:
                    result = ServiceUsage.create(
                        guest_id=guest_id or booking['guest_id'],
                        service_type_id=service_type_id,
                        cost=cost,
                        usage_date=usage_date,
                        booking_id=booking_id,
                        room_id=room_id,
                        paid=paid
                    )

                    if result and 'id' in result:
                        flash('Услуга успешно добавлена', 'success')
                    else:
                        flash('Ошибка при добавлении услуги', 'error')
                else:
                    flash('Необходимо указать гостя для услуги', 'error')
            else:
                flash('Необходимо указать тип услуги и гостя или фирму', 'error')

        except ValueError:
            flash('Некорректный формат даты', 'error')

    # Получаем услуги бронирования
    services = ServiceUsage.get_by_booking(booking_id)

    # Получаем типы услуг для выбора
    service_types = ServiceType.get_active()

    # Получаем номера бронирования
    rooms = Booking.get_rooms(booking_id)

    # Если бронирование от фирмы, получаем список гостей для выбора
    guests = None
    if booking['firm_id'] and not booking['guest_id']:
        guests = Guest.get_all()

    return render_template('bookings/services.html',
                           booking=booking,
                           services=services,
                           service_types=service_types,
                           rooms=rooms,
                           guests=guests)


@bp.route('/active')
def active():
    """Список активных бронирований"""
    bookings = Booking.get_active_bookings()
    return render_template('bookings/active.html', bookings=bookings)


@bp.route('/to-be-freed')
def to_be_freed():
    """Список номеров, которые освободятся к указанному сроку"""
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

    rooms = Booking.get_rooms_to_be_freed_by_date(target_date)

    return render_template('bookings/to_be_freed.html',
                           rooms=rooms,
                           target_date=target_date.strftime('%Y-%m-%d'))