from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.models.complaint import Complaint
from app.models.guest import Guest
from datetime import datetime, date

bp = Blueprint('complaint', __name__)


@bp.route('/')
def index():
    """Список всех жалоб"""
    complaints = Complaint.get_all()
    return render_template('complaints/index.html', complaints=complaints)


@bp.route('/<int:complaint_id>')
def show(complaint_id):
    """Информация о жалобе"""
    complaint = Complaint.get_by_id(complaint_id)
    if not complaint:
        flash('Жалоба не найдена', 'error')
        return redirect(url_for('complaint.index'))

    return render_template('complaints/show.html', complaint=complaint)


@bp.route('/create', methods=['GET', 'POST'])
def create():
    """Форма создания новой жалобы"""
    # Получаем список гостей
    guests = Guest.get_all()

    if request.method == 'POST':
        # Получаем данные из формы
        guest_id = int(request.form.get('guest_id')) if request.form.get('guest_id') else None
        description = request.form.get('description')
        complaint_date_str = request.form.get('complaint_date')
        resolved = 'resolved' in request.form
        resolution_date_str = request.form.get('resolution_date') if resolved else None
        resolution_details = request.form.get('resolution_details') if resolved else None

        # Валидация
        if not guest_id:
            flash('Необходимо указать гостя', 'error')
            return render_template('complaints/create.html', guests=guests)

        if not description or len(description) < 10:
            flash('Описание жалобы должно содержать не менее 10 символов', 'error')
            return render_template('complaints/create.html', guests=guests)

        try:
            complaint_date = datetime.strptime(complaint_date_str,
                                               '%Y-%m-%d').date() if complaint_date_str else date.today()
            resolution_date = datetime.strptime(resolution_date_str, '%Y-%m-%d').date() if resolution_date_str else None

            # Создаем жалобу
            result = Complaint.create(
                guest_id=guest_id,
                description=description,
                complaint_date=complaint_date,
                resolved=resolved,
                resolution_date=resolution_date,
                resolution_details=resolution_details
            )

            if result and 'id' in result:
                flash('Жалоба успешно создана', 'success')
                return redirect(url_for('complaint.show', complaint_id=result['id']))
            else:
                flash('Ошибка при создании жалобы', 'error')

        except ValueError:
            flash('Некорректный формат даты', 'error')

    return render_template('complaints/create.html', guests=guests)


@bp.route('/<int:complaint_id>/edit', methods=['GET', 'POST'])
def edit(complaint_id):
    """Форма редактирования жалобы"""
    complaint = Complaint.get_by_id(complaint_id)
    if not complaint:
        flash('Жалоба не найдена', 'error')
        return redirect(url_for('complaint.index'))

    # Получаем список гостей
    guests = Guest.get_all()

    if request.method == 'POST':
        # Получаем данные из формы
        guest_id = int(request.form.get('guest_id')) if request.form.get('guest_id') else None
        description = request.form.get('description')
        complaint_date_str = request.form.get('complaint_date')
        resolved = 'resolved' in request.form
        resolution_date_str = request.form.get('resolution_date') if resolved else None
        resolution_details = request.form.get('resolution_details') if resolved else None

        # Валидация
        if not guest_id:
            flash('Необходимо указать гостя', 'error')
            return render_template('complaints/edit.html', complaint=complaint, guests=guests)

        if not description or len(description) < 10:
            flash('Описание жалобы должно содержать не менее 10 символов', 'error')
            return render_template('complaints/edit.html', complaint=complaint, guests=guests)

        try:
            complaint_date = datetime.strptime(complaint_date_str,
                                               '%Y-%m-%d').date() if complaint_date_str else date.today()
            resolution_date = datetime.strptime(resolution_date_str, '%Y-%m-%d').date() if resolution_date_str else None

            # Обновляем жалобу
            result = Complaint.update(
                complaint_id=complaint_id,
                guest_id=guest_id,
                description=description,
                complaint_date=complaint_date,
                resolved=resolved,
                resolution_date=resolution_date,
                resolution_details=resolution_details
            )

            if result and 'id' in result:
                flash('Жалоба успешно обновлена', 'success')
                return redirect(url_for('complaint.show', complaint_id=complaint_id))
            else:
                flash('Ошибка при обновлении жалобы', 'error')

        except ValueError:
            flash('Некорректный формат даты', 'error')

    return render_template('complaints/edit.html', complaint=complaint, guests=guests)


@bp.route('/<int:complaint_id>/delete', methods=['POST'])
def delete(complaint_id):
    """Удаление жалобы"""
    complaint = Complaint.get_by_id(complaint_id)
    if not complaint:
        flash('Жалоба не найдена', 'error')
    else:
        result = Complaint.delete(complaint_id)
        if result and 'id' in result:
            flash('Жалоба успешно удалена', 'success')
        else:
            flash('Ошибка при удалении жалобы', 'error')

    return redirect(url_for('complaint.index'))


@bp.route('/<int:complaint_id>/resolve', methods=['GET', 'POST'])
def resolve(complaint_id):
    """Форма разрешения жалобы"""
    complaint = Complaint.get_by_id(complaint_id)
    if not complaint:
        flash('Жалоба не найдена', 'error')
        return redirect(url_for('complaint.index'))

    if complaint['resolved']:
        flash('Эта жалоба уже разрешена', 'info')
        return redirect(url_for('complaint.show', complaint_id=complaint_id))

    if request.method == 'POST':
        resolution_details = request.form.get('resolution_details')

        if not resolution_details or len(resolution_details) < 10:
            flash('Описание разрешения должно содержать не менее 10 символов', 'error')
            return render_template('complaints/resolve.html', complaint=complaint)

        result = Complaint.resolve(complaint_id, resolution_details)
        if result and 'id' in result:
            flash('Жалоба успешно разрешена', 'success')
            return redirect(url_for('complaint.show', complaint_id=complaint_id))
        else:
            flash('Ошибка при разрешении жалобы', 'error')

    return render_template('complaints/resolve.html', complaint=complaint)


@bp.route('/unresolved')
def unresolved():
    """Список неразрешенных жалоб"""
    complaints = Complaint.get_unresolved()
    return render_template('complaints/unresolved.html', complaints=complaints)


@bp.route('/stats')
def stats():
    """Статистика по жалобам"""
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

    # Получаем статистику по жалобам
    stats = Complaint.get_complaint_stats(
        start_date=start_date_obj,
        end_date=end_date_obj
    )

    return render_template('complaints/stats.html',
                           stats=stats,
                           start_date=start_date,
                           end_date=end_date)