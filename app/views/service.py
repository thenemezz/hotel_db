from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort
from flask_login import login_required, current_user
from app.models.service import ServiceType, ServiceUsage
from app.models.guest import Guest
from datetime import datetime, date

bp = Blueprint('service', __name__)


@bp.route('/')
@login_required
def index():
    """Список всех услуг"""
    # Проверка прав доступа
    if not current_user.has_access('serviceusage', 'read'):
        abort(403)  # Forbidden - доступ запрещен

    service_usages = ServiceUsage.get_all()
    return render_template('services/index.html', service_usages=service_usages)


@bp.route('/types')
@login_required
def types():
    """Список всех типов услуг"""
    # Проверка прав доступа
    if not current_user.has_access('servicetype', 'read'):
        abort(403)  # Forbidden - доступ запрещен

    service_types = ServiceType.get_all()
    return render_template('services/types.html', service_types=service_types)


@bp.route('/types/create', methods=['GET', 'POST'])
@login_required
def create_type():
    """Форма создания нового типа услуги"""
    # Проверка прав доступа
    if not current_user.has_access('servicetype', 'create'):
        abort(403)  # Forbidden - доступ запрещен

    if request.method == 'POST':
        # Получаем данные из формы
        name = request.form.get('name')
        base_price = float(request.form.get('base_price', 0))
        is_active = 'is_active' in request.form

        # Создаем тип услуги
        result = ServiceType.create(
            name=name,
            base_price=base_price,
            is_active=is_active
        )

        if result and 'id' in result:
            flash('Тип услуги успешно создан', 'success')
            return redirect(url_for('service.types'))
        else:
            flash('Ошибка при создании типа услуги', 'error')

    return render_template('services/create_type.html')


@bp.route('/types/<int:service_type_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_type(service_type_id):
    """Форма редактирования типа услуги"""
    # Проверка прав доступа
    if not current_user.has_access('servicetype', 'update'):
        abort(403)  # Forbidden - доступ запрещен

    service_type = ServiceType.get_by_id(service_type_id)
    if not service_type:
        flash('Тип услуги не найден', 'error')
        return redirect(url_for('service.types'))

    if request.method == 'POST':
        # Получаем данные из формы
        name = request.form.get('name')
        base_price = float(request.form.get('base_price', 0))
        is_active = 'is_active' in request.form

        # Обновляем тип услуги
        result = ServiceType.update(
            service_type_id=service_type_id,
            name=name,
            base_price=base_price,
            is_active=is_active
        )

        if result and 'id' in result:
            flash('Тип услуги успешно обновлен', 'success')
            return redirect(url_for('service.types'))
        else:
            flash('Ошибка при обновлении типа услуги', 'error')

    return render_template('services/edit_type.html', service_type=service_type)


@bp.route('/types/<int:service_type_id>/delete', methods=['POST'])
@login_required
def delete_type(service_type_id):
    """Удаление типа услуги"""
    # Проверка прав доступа
    if not current_user.has_access('servicetype', 'delete'):
        abort(403)  # Forbidden - доступ запрещен

    service_type = ServiceType.get_by_id(service_type_id)
    if not service_type:
        flash('Тип услуги не найден', 'error')
    else:
        result = ServiceType.delete(service_type_id)
        if result and 'id' in result:
            flash('Тип услуги успешно удален', 'success')
        else:
            flash('Ошибка при удалении типа услуги', 'error')

    return redirect(url_for('service.types'))


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Форма создания новой услуги"""
    # Проверка прав доступа
    if not current_user.has_access('serviceusage', 'create'):
        abort(403)  # Forbidden - доступ запрещен

    # Получаем список гостей и типов услуг
    # Для получения списка гостей нужны права доступа на чтение гостей
    # Но сервисная служба должна иметь возможность создавать услуги
    guests = Guest.get_all()
    service_types = ServiceType.get_active()

    if request.method == 'POST':
        # Получаем данные из формы
        guest_id = int(request.form.get('guest_id')) if request.form.get('guest_id') else None
        service_type_id = int(request.form.get('service_type_id')) if request.form.get('service_type_id') else None
        cost = float(request.form.get('cost', 0))
        usage_date_str = request.form.get('usage_date')
        booking_id = int(request.form.get('booking_id')) if request.form.get('booking_id') else None
        room_id = int(request.form.get('room_id')) if request.form.get('room_id') else None
        paid = 'paid' in request.form

        try:
            usage_date = datetime.strptime(usage_date_str, '%Y-%m-%d').date() if usage_date_str else date.today()

            if guest_id and service_type_id:
                # Создаем услугу
                result = ServiceUsage.create(
                    guest_id=guest_id,
                    service_type_id=service_type_id,
                    cost=cost,
                    usage_date=usage_date,
                    booking_id=booking_id,
                    room_id=room_id,
                    paid=paid
                )

                if result and 'id' in result:
                    flash('Услуга успешно создана', 'success')
                    return redirect(url_for('service.index'))
                else:
                    flash('Ошибка при создании услуги', 'error')
            else:
                flash('Необходимо указать гостя и тип услуги', 'error')

        except ValueError:
            flash('Некорректный формат даты', 'error')

    return render_template('services/create.html', guests=guests, service_types=service_types)


@bp.route('/<int:service_usage_id>')
@login_required
def show(service_usage_id):
    """Информация об использованной услуге"""
    # Проверка прав доступа
    if not current_user.has_access('serviceusage', 'read'):
        abort(403)  # Forbidden - доступ запрещен

    service_usage = ServiceUsage.get_by_id(service_usage_id)
    if not service_usage:
        flash('Услуга не найдена', 'error')
        return redirect(url_for('service.index'))

    return render_template('services/show.html', service_usage=service_usage)


@bp.route('/<int:service_usage_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(service_usage_id):
    """Форма редактирования услуги"""
    # Проверка прав доступа
    if not current_user.has_access('serviceusage', 'update'):
        abort(403)  # Forbidden - доступ запрещен

    service_usage = ServiceUsage.get_by_id(service_usage_id)
    if not service_usage:
        flash('Услуга не найдена', 'error')
        return redirect(url_for('service.index'))

    # Получаем список гостей и типов услуг
    guests = Guest.get_all()
    service_types = ServiceType.get_all()

    if request.method == 'POST':
        # Получаем данные из формы
        guest_id = int(request.form.get('guest_id')) if request.form.get('guest_id') else None
        service_type_id = int(request.form.get('service_type_id')) if request.form.get('service_type_id') else None
        cost = float(request.form.get('cost', 0))
        usage_date_str = request.form.get('usage_date')
        booking_id = int(request.form.get('booking_id')) if request.form.get('booking_id') else None
        room_id = int(request.form.get('room_id')) if request.form.get('room_id') else None
        paid = 'paid' in request.form

        try:
            usage_date = datetime.strptime(usage_date_str, '%Y-%m-%d').date() if usage_date_str else date.today()

            if guest_id and service_type_id:
                # Обновляем услугу
                result = ServiceUsage.update(
                    service_usage_id=service_usage_id,
                    guest_id=guest_id,
                    service_type_id=service_type_id,
                    cost=cost,
                    usage_date=usage_date,
                    booking_id=booking_id,
                    room_id=room_id,
                    paid=paid
                )

                if result and 'id' in result:
                    flash('Услуга успешно обновлена', 'success')
                    return redirect(url_for('service.show', service_usage_id=service_usage_id))
                else:
                    flash('Ошибка при обновлении услуги', 'error')
            else:
                flash('Необходимо указать гостя и тип услуги', 'error')

        except ValueError:
            flash('Некорректный формат даты', 'error')

    return render_template('services/edit.html',
                           service_usage=service_usage,
                           guests=guests,
                           service_types=service_types)


@bp.route('/<int:service_usage_id>/delete', methods=['POST'])
@login_required
def delete(service_usage_id):
    """Удаление услуги"""
    # Проверка прав доступа
    if not current_user.has_access('serviceusage', 'delete'):
        abort(403)  # Forbidden - доступ запрещен

    service_usage = ServiceUsage.get_by_id(service_usage_id)
    if not service_usage:
        flash('Услуга не найдена', 'error')
    else:
        result = ServiceUsage.delete(service_usage_id)
        if result and 'id' in result:
            flash('Услуга успешно удалена', 'success')
        else:
            flash('Ошибка при удалении услуги', 'error')

    return redirect(url_for('service.index'))


@bp.route('/<int:service_usage_id>/mark-as-paid', methods=['POST'])
@login_required
def mark_as_paid(service_usage_id):
    """Отметить услугу как оплаченную"""
    # Проверка прав доступа
    if not current_user.has_access('serviceusage', 'update'):
        abort(403)  # Forbidden - доступ запрещен

    service_usage = ServiceUsage.get_by_id(service_usage_id)
    if not service_usage:
        flash('Услуга не найдена', 'error')
    else:
        result = ServiceUsage.mark_as_paid(service_usage_id)
        if result and 'id' in result:
            flash('Услуга отмечена как оплаченная', 'success')
        else:
            flash('Ошибка при обновлении статуса оплаты услуги', 'error')

    return redirect(url_for('service.show', service_usage_id=service_usage_id))


@bp.route('/stats')
@login_required
def stats():
    """Статистика по услугам"""
    # Проверка прав доступа
    if not current_user.has_access('serviceusage', 'read'):
        abort(403)  # Forbidden - доступ запрещен

    # Фильтры из параметров запроса
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    # Преобразование дат
    start_date_obj = None
    end_date_obj = None

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

    # Получаем статистику по услугам
    stats = ServiceUsage.get_service_stats(
        start_date=start_date_obj,
        end_date=end_date_obj
    )

    return render_template('services/stats.html',
                           stats=stats,
                           start_date=start_date,
                           end_date=end_date)