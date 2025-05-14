from flask import Blueprint, render_template, request, jsonify, abort
from flask_login import login_required, current_user
from app.utils.db import execute_query
from datetime import datetime, date

bp = Blueprint('admin_queries', __name__, url_prefix='/admin/queries')


@bp.before_request
def check_admin():
    """Проверяет, что пользователь является администратором"""
    if not current_user.is_authenticated or current_user.role != 'admin':
        abort(403)  # Forbidden - доступ запрещен


@bp.route('/')
@login_required
def index():
    """Страница с формами для выполнения административных запросов"""
    return render_template('admin/queries/index.html')


@bp.route('/firms-with-bookings', methods=['GET', 'POST'])
@login_required
def firms_with_bookings():
    """
    Запрос 1: Получить перечень и общее число фирм, забронировавших места
    в объеме, не менее указанного
    """
    if request.method == 'POST':
        min_rooms = request.form.get('min_rooms', type=int)
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')

        # Конвертация дат
        start_date_obj = None
        end_date_obj = None

        if start_date:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
        if end_date:
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()

        query = """
        WITH firm_bookings AS (
            SELECT 
                f.id AS firm_id,
                f.name AS firm_name,
                f.firm_type,
                f.address,
                f.phone,
                f.is_active,
                COUNT(DISTINCT br.room_id) AS total_rooms_booked
            FROM 
                firm f
            JOIN 
                booking b ON f.id = b.firm_id
            JOIN 
                booking_room br ON b.id = br.booking_id
            WHERE 
                b.status != 'Отменено'
                AND (
                    %s IS NULL OR %s IS NULL
                    OR (b.check_in_date >= %s AND b.check_out_date <= %s)
                )
            GROUP BY 
                f.id, f.name, f.firm_type, f.address, f.phone, f.is_active
            HAVING 
                COUNT(DISTINCT br.room_id) >= %s
        )
        SELECT 
            fb.firm_id,
            fb.firm_name,
            fb.firm_type,
            fb.address,
            fb.phone,
            fb.is_active,
            fb.total_rooms_booked,
            (SELECT COUNT(*) FROM firm_bookings) AS total_matching_firms
        FROM 
            firm_bookings fb
        ORDER BY 
            fb.total_rooms_booked DESC, fb.firm_name;
        """

        firms = execute_query(
            query,
            (start_date_obj, end_date_obj, start_date_obj, end_date_obj, min_rooms),
            fetch=True
        )

        return render_template(
            'admin/queries/firms_with_bookings.html',
            firms=firms,
            min_rooms=min_rooms,
            start_date=start_date,
            end_date=end_date
        )

    return render_template('admin/queries/firms_with_bookings_form.html')


@bp.route('/guests-by-room-type', methods=['GET', 'POST'])
@login_required
def guests_by_room_type():
    """
    Запрос 2: Получить перечень и общее число постояльцев, заселявшихся в номера
    с указанными характеристиками за некоторый период
    """
    if request.method == 'POST':
        room_capacity = request.form.get('room_capacity', type=int)
        hotel_rating = request.form.get('hotel_rating', type=int)
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')

        # Конвертация дат
        start_date_obj = None
        end_date_obj = None

        if start_date:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
        if end_date:
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()

        query = """
        SELECT 
            g.id AS guest_id,
            g.last_name,
            g.first_name,
            g.middle_name,
            g.phone,
            g.email,
            COUNT(DISTINCT b.id) AS booking_count,
            COUNT(DISTINCT (CASE WHEN r.room_capacity >= %s THEN r.id ELSE NULL END)) AS matching_rooms_count,
            MIN(b.check_in_date) as first_check_in,
            MAX(b.check_out_date) as last_check_out
        FROM 
            guest g
        JOIN 
            booking b ON g.id = b.guest_id
        JOIN 
            booking_room br ON b.id = br.booking_id
        JOIN 
            room r ON br.room_id = r.id
        JOIN 
            hotel h ON r.hotel_id = h.id
        WHERE 
            b.status != 'Отменено'
            AND (%s IS NULL OR r.room_capacity >= %s)
            AND (%s IS NULL OR h.rating >= %s)
            AND (%s IS NULL OR %s IS NULL OR 
                (b.check_in_date >= %s AND b.check_out_date <= %s))
        GROUP BY 
            g.id, g.last_name, g.first_name, g.middle_name, g.phone, g.email
        ORDER BY 
            booking_count DESC, g.last_name, g.first_name;
        """

        guests = execute_query(
            query,
            (
                room_capacity,
                room_capacity, room_capacity,
                hotel_rating, hotel_rating,
                start_date_obj, end_date_obj, start_date_obj, end_date_obj
            ),
            fetch=True
        )

        return render_template(
            'admin/queries/guests_by_room_type.html',
            guests=guests,
            room_capacity=room_capacity,
            hotel_rating=hotel_rating,
            start_date=start_date,
            end_date=end_date,
            total_guests=len(guests) if guests else 0
        )

    return render_template('admin/queries/guests_by_room_type_form.html')


@bp.route('/available-rooms-count')
@login_required
def available_rooms_count():
    """
    Запрос 3: Получить количество свободных номеров на данный момент
    """
    query = """
    SELECT 
        h.name AS hotel_name,
        COUNT(*) AS available_rooms_count
    FROM 
        room r
    JOIN 
        hotel h ON r.hotel_id = h.id
    WHERE 
        r.is_available = TRUE
        AND NOT EXISTS (
            SELECT 1
            FROM booking_room br
            JOIN booking b ON br.booking_id = b.id
            WHERE 
                br.room_id = r.id
                AND b.status = 'Забронировано'
                AND CURRENT_DATE BETWEEN b.check_in_date AND b.check_out_date
        )
    GROUP BY 
        h.name
    ORDER BY 
        h.name;
    """

    hotel_stats = execute_query(query, fetch=True)

    total_available = sum(hotel['available_rooms_count'] for hotel in hotel_stats) if hotel_stats else 0

    return render_template(
        'admin/queries/available_rooms_count.html',
        hotel_stats=hotel_stats,
        total_available=total_available
    )


@bp.route('/available-rooms-by-characteristics', methods=['GET', 'POST'])
@login_required
def available_rooms_by_characteristics():
    """
    Запрос 4: Получить сведения о количестве свободных номеров с указанными характеристиками
    """
    if request.method == 'POST':
        hotel_rating = request.form.get('hotel_rating', type=int)
        room_capacity = request.form.get('room_capacity', type=int)
        floor_number = request.form.get('floor_number', type=int)
        min_price = request.form.get('min_price', type=float)
        max_price = request.form.get('max_price', type=float)

        has_restaurant = 'has_restaurant' in request.form
        has_pool_sauna = 'has_pool_sauna' in request.form

        query = """
        SELECT 
            h.name AS hotel_name,
            h.rating AS hotel_rating,
            r.floor_number,
            r.room_capacity,
            CASE 
                WHEN r.base_rate < 3000 THEN 'Эконом'
                WHEN r.base_rate >= 3000 AND r.base_rate < 5000 THEN 'Стандарт'
                WHEN r.base_rate >= 5000 AND r.base_rate < 8000 THEN 'Комфорт'
                ELSE 'Люкс'
            END AS price_category,
            COUNT(*) AS available_rooms_count
        FROM 
            room r
        JOIN 
            hotel h ON r.hotel_id = h.id
        WHERE 
            r.is_available = TRUE
            AND NOT EXISTS (
                SELECT 1
                FROM booking_room br
                JOIN booking b ON br.booking_id = b.id
                WHERE 
                    br.room_id = r.id
                    AND b.status = 'Забронировано'
                    AND CURRENT_DATE BETWEEN b.check_in_date AND b.check_out_date
            )
            AND (%s IS NULL OR h.rating = %s)
            AND (%s IS NULL OR r.room_capacity >= %s)
            AND (%s IS NULL OR r.floor_number = %s)
            AND (%s IS NULL OR r.base_rate >= %s)
            AND (%s IS NULL OR r.base_rate <= %s)
            AND (%s = FALSE OR h.has_restaurant = %s)
            AND (%s = FALSE OR h.has_pool_sauna = %s)
        GROUP BY 
            h.name, h.rating, r.floor_number, r.room_capacity, price_category
        ORDER BY 
            h.name, h.rating, r.floor_number, r.room_capacity;
        """

        results = execute_query(
            query,
            (
                hotel_rating, hotel_rating,
                room_capacity, room_capacity,
                floor_number, floor_number,
                min_price, min_price,
                max_price, max_price,
                has_restaurant, has_restaurant,
                has_pool_sauna, has_pool_sauna
            ),
            fetch=True
        )

        total_available = sum(result['available_rooms_count'] for result in results) if results else 0

        return render_template(
            'admin/queries/available_rooms_by_characteristics.html',
            results=results,
            total_available=total_available,
            hotel_rating=hotel_rating,
            room_capacity=room_capacity,
            floor_number=floor_number,
            min_price=min_price,
            max_price=max_price,
            has_restaurant=has_restaurant,
            has_pool_sauna=has_pool_sauna
        )

    return render_template('admin/queries/available_rooms_by_characteristics_form.html')


@bp.route('/room-availability/<int:room_id>')
@login_required
def room_availability(room_id):
    """
    Запрос 5: Получить сведения о конкретном свободном номере:
    в течение какого времени он будет пустовать и о его характеристиках
    """
    query = """
    WITH next_booking AS (
        SELECT 
            br.room_id,
            MIN(b.check_in_date) AS next_check_in_date
        FROM 
            booking b
        JOIN 
            booking_room br ON b.id = br.booking_id
        WHERE 
            b.status = 'Забронировано'
            AND b.check_in_date > CURRENT_DATE
            AND br.room_id = %s
        GROUP BY 
            br.room_id
    )

    SELECT 
        r.id AS room_id,
        h.name AS hotel_name,
        h.rating AS hotel_stars,
        r.floor_number,
        r.room_number,
        r.room_capacity AS capacity,
        r.base_rate AS price_per_night,
        CURRENT_DATE AS available_from,
        COALESCE(nb.next_check_in_date, CURRENT_DATE + INTERVAL '365 days') AS available_until,
        COALESCE(
            nb.next_check_in_date - CURRENT_DATE, 
            365
        ) AS days_available,
        h.has_housekeeping,
        h.has_laundry,
        h.has_dry_cleaning,
        h.has_restaurant,
        h.has_bar,
        h.has_pool_sauna,
        h.has_billiards,
        CASE 
            WHEN r.base_rate < 3000 THEN 'Эконом'
            WHEN r.base_rate >= 3000 AND r.base_rate < 5000 THEN 'Стандарт'
            WHEN r.base_rate >= 5000 AND r.base_rate < 8000 THEN 'Комфорт'
            ELSE 'Люкс'
        END AS price_category
    FROM 
        room r
    JOIN 
        hotel h ON r.hotel_id = h.id
    LEFT JOIN 
        next_booking nb ON r.id = nb.room_id
    WHERE 
        r.is_available = TRUE
        AND NOT EXISTS (
            SELECT 1
            FROM booking_room br
            JOIN booking b ON br.booking_id = b.id
            WHERE 
                br.room_id = r.id
                AND b.status = 'Забронировано'
                AND CURRENT_DATE BETWEEN b.check_in_date AND b.check_out_date
        )
        AND r.id = %s;
    """

    room_info = execute_query(query, (room_id, room_id), fetch=True, fetchone=True)

    if not room_info:
        # Если номер не найден или занят, получим данные о номере
        basic_query = """
        SELECT 
            r.id AS room_id,
            h.name AS hotel_name,
            r.room_number,
            r.is_available,
            EXISTS (
                SELECT 1
                FROM booking_room br
                JOIN booking b ON br.booking_id = b.id
                WHERE 
                    br.room_id = r.id
                    AND b.status = 'Забронировано'
                    AND CURRENT_DATE BETWEEN b.check_in_date AND b.check_out_date
            ) AS currently_occupied
        FROM 
            room r
        JOIN 
            hotel h ON r.hotel_id = h.id
        WHERE 
            r.id = %s;
        """

        basic_info = execute_query(basic_query, (room_id,), fetch=True, fetchone=True)

        return render_template(
            'admin/queries/room_not_available.html',
            room_info=basic_info
        )

    return render_template(
        'admin/queries/room_availability.html',
        room_info=room_info
    )


from datetime import datetime, date, timedelta


@bp.route('/rooms-to-be-freed', methods=['GET', 'POST'])
@login_required
def rooms_to_be_freed():
    target_date_obj = None
    rooms = None

    if request.method == 'POST':
        target_date_str = request.form.get('target_date')
        try:
            target_date_obj = datetime.strptime(target_date_str, '%Y-%m-%d').date()
        except (TypeError, ValueError):
            flash('Некорректный формат даты', 'error')
            return redirect(url_for('admin_queries.rooms_to_be_freed'))

        query = """
        SELECT r.id AS room_id,
               h.name AS hotel_name,
               r.room_number,
               r.floor_number,
               r.room_capacity,
               r.base_rate,
               b.check_out_date,
               g.last_name || ' ' || g.first_name AS guest_name,
               (b.check_out_date - CURRENT_DATE) AS days_until_free
        FROM   room r
        JOIN   hotel h        ON r.hotel_id  = h.id
        JOIN   booking_room br ON r.id       = br.room_id
        JOIN   booking b      ON br.booking_id = b.id
        LEFT JOIN guest g     ON b.guest_id = g.id
        WHERE  b.status = 'Забронировано'
          AND  CURRENT_DATE BETWEEN b.check_in_date AND b.check_out_date
          AND  b.check_out_date <= %s
        ORDER BY b.check_out_date, h.name, r.room_number;
        """
        rooms = execute_query(query, (target_date_obj,), fetch=True)

    # Для GET-запроса или при первой загрузке страницы — дата по умолчанию
    if target_date_obj is None:
        target_date_obj = date.today() + timedelta(days=7)

    return render_template(
        'admin/queries/rooms_to_be_freed.html',
        rooms=rooms,
        target_date=target_date_obj.strftime('%Y-%m-%d'),
        total_rooms=len(rooms) if rooms else 0
    )


@bp.route('/firm-booking-preferences', methods=['GET', 'POST'])
@login_required
def firm_booking_preferences():
    """
    Запрос 7: Получить данные об объеме бронирования номеров данной фирмой за указанный период,
    и каким номерам отдавались предпочтения
    """
    # Сначала получим список всех фирм для выбора
    firms_query = "SELECT id, name FROM firm ORDER BY name;"
    firms = execute_query(firms_query, fetch=True)

    if request.method == 'POST':
        firm_id = request.form.get('firm_id', type=int)
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')

        # Конвертация дат
        start_date_obj = None
        end_date_obj = None

        if start_date:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
        if end_date:
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()

        # Запрос для получения общей статистики бронирований
        stats_query = """
        SELECT 
            f.name AS firm_name,
            COUNT(DISTINCT b.id) AS total_bookings,
            SUM(b.total_rooms) AS total_rooms_booked,
            SUM(b.total_persons) AS total_guests,
            MIN(b.check_in_date) AS first_booking_date,
            MAX(b.check_out_date) AS last_checkout_date,
            CAST(AVG(b.check_out_date - b.check_in_date) AS INTEGER) AS avg_stay_days
        FROM 
            firm f
        JOIN 
            booking b ON f.id = b.firm_id
        WHERE 
            f.id = %s
            AND b.status != 'Отменено'
            AND (%s IS NULL OR %s IS NULL OR 
                (b.check_in_date >= %s AND b.check_out_date <= %s))
        GROUP BY 
            f.name;
        """

        # Запрос для получения предпочтений по номерам
        preferences_query = """
        SELECT 
            h.name AS hotel_name,
            r.floor_number,
            r.room_capacity,
            CASE 
                WHEN r.base_rate < 3000 THEN 'Эконом'
                WHEN r.base_rate >= 3000 AND r.base_rate < 5000 THEN 'Стандарт'
                WHEN r.base_rate >= 5000 AND r.base_rate < 8000 THEN 'Комфорт'
                ELSE 'Люкс'
            END AS price_category,
            COUNT(*) AS booking_count,
            ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS percentage
        FROM 
            booking b
        JOIN 
            booking_room br ON b.id = br.booking_id
        JOIN 
            room r ON br.room_id = r.id
        JOIN 
            hotel h ON r.hotel_id = h.id
        WHERE 
            b.firm_id = %s
            AND b.status != 'Отменено'
            AND (%s IS NULL OR %s IS NULL OR 
                (b.check_in_date >= %s AND b.check_out_date <= %s))
        GROUP BY 
            h.name, r.floor_number, r.room_capacity, price_category
        ORDER BY 
            booking_count DESC, h.name;
        """

        stats = execute_query(
            stats_query,
            (firm_id, start_date_obj, end_date_obj, start_date_obj, end_date_obj),
            fetch=True,
            fetchone=True
        )

        preferences = execute_query(
            preferences_query,
            (firm_id, start_date_obj, end_date_obj, start_date_obj, end_date_obj),
            fetch=True
        )

        # Получим название фирмы, если статистика пуста
        if not stats:
            firm_name_query = "SELECT name FROM firm WHERE id = %s;"
            firm_name_result = execute_query(firm_name_query, (firm_id,), fetch=True, fetchone=True)
            firm_name = firm_name_result['name'] if firm_name_result else 'Неизвестная фирма'
        else:
            firm_name = stats['firm_name']

        return render_template(
            'admin/queries/firm_booking_preferences.html',
            stats=stats,
            preferences=preferences,
            firm_name=firm_name,
            firm_id=firm_id,
            start_date=start_date,
            end_date=end_date
        )

    return render_template('admin/queries/firm_booking_preferences_form.html', firms=firms)


@bp.route('/unhappy-clients')
@login_required
def unhappy_clients():
    """
    Запрос 8: Получить список недовольных клиентов и их жалобы
    """
    query = """
    SELECT 
        c.id AS complaint_id,
        g.id AS guest_id,
        g.last_name || ' ' || g.first_name AS guest_name,
        g.phone,
        g.email,
        c.complaint_date,
        c.description,
        c.resolved,
        c.resolution_date,
        c.resolution_details,
        (SELECT COUNT(*) FROM complaint WHERE guest_id = g.id) AS total_complaints_by_guest
    FROM 
        complaint c
    JOIN 
        guest g ON c.guest_id = g.id
    ORDER BY 
        c.resolved, c.complaint_date DESC, total_complaints_by_guest DESC;
    """

    complaints = execute_query(query, fetch=True)

    unresolved_count = sum(1 for complaint in complaints if not complaint['resolved'])

    return render_template(
        'admin/queries/unhappy_clients.html',
        complaints=complaints,
        unresolved_count=unresolved_count,
        total_count=len(complaints) if complaints else 0
    )


@bp.route('/room-profitability', methods=['GET', 'POST'])
@login_required
def room_profitability():
    """
    Запрос 9: Получить данные о рентабельности номеров с определенными характеристиками
    """
    if request.method == 'POST':
        hotel_rating = request.form.get('hotel_rating', type=int)
        room_capacity = request.form.get('room_capacity', type=int)
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')

        # Конвертация дат
        start_date_obj = None
        end_date_obj = None

        if start_date:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
        else:
            # Если не указана начальная дата, берем начало текущего года
            start_date_obj = date(date.today().year, 1, 1)
            start_date = start_date_obj.strftime('%Y-%m-%d')

        if end_date:
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
        else:
            # Если не указана конечная дата, берем текущую дату
            end_date_obj = date.today()
            end_date = end_date_obj.strftime('%Y-%m-%d')

        # Расчет доходов от номеров (бронирования)
        query = """
        WITH room_bookings AS (
            SELECT 
                r.id AS room_id,
                h.id AS hotel_id,
                h.name AS hotel_name,
                h.rating AS hotel_rating,
                r.room_capacity,
                r.base_rate,
                CASE 
                    WHEN r.base_rate < 3000 THEN 'Эконом'
                    WHEN r.base_rate >= 3000 AND r.base_rate < 5000 THEN 'Стандарт'
                    WHEN r.base_rate >= 5000 AND r.base_rate < 8000 THEN 'Комфорт'
                    ELSE 'Люкс'
                END AS price_category,
                -- Доходы от номера
                COUNT(DISTINCT b.id) AS booking_count,
                SUM(
                    CASE 
                        WHEN b.check_in_date < %s THEN %s
                        ELSE b.check_in_date
                    END - 
                    CASE 
                        WHEN b.check_out_date > %s THEN %s
                        ELSE b.check_out_date
                    END
                ) AS days_booked,
                SUM(
                    (CASE 
                        WHEN b.check_out_date > %s THEN %s
                        ELSE b.check_out_date
                    END - 
                    CASE 
                        WHEN b.check_in_date < %s THEN %s
                        ELSE b.check_in_date
                    END) * r.base_rate
                ) AS booking_revenue
            FROM 
                room r
            JOIN 
                hotel h ON r.hotel_id = h.id
            LEFT JOIN 
                booking_room br ON r.id = br.room_id
            LEFT JOIN 
                booking b ON br.booking_id = b.id AND b.status != 'Отменено'
                AND (
                    (b.check_in_date BETWEEN %s AND %s) OR
                    (b.check_out_date BETWEEN %s AND %s) OR
                    (b.check_in_date <= %s AND b.check_out_date >= %s)
                )
            WHERE 
                (%s IS NULL OR h.rating = %s)
                AND (%s IS NULL OR r.room_capacity = %s)
            GROUP BY 
                r.id, h.id, h.name, h.rating, r.room_capacity, r.base_rate, price_category
        ),
        service_revenue AS (
            SELECT 
                rb.room_id,
                COALESCE(SUM(su.cost), 0) AS service_revenue
            FROM 
                room_bookings rb
            LEFT JOIN 
                service_usage su ON rb.room_id = su.room_id
                AND su.usage_date BETWEEN %s AND %s
            GROUP BY 
                rb.room_id
        )
        SELECT 
            rb.hotel_name,
            rb.hotel_rating,
            rb.room_capacity,
            rb.price_category,
            COUNT(*) AS room_count,

            -- Период в днях
            (%s - %s + 1) AS period_days,

            -- Средний показатель заполняемости
            ROUND(SUM(rb.days_booked) * 100.0 / (COUNT(*) * (%s - %s + 1)), 2) AS occupancy_rate,

            -- Доходы
            SUM(rb.booking_revenue) AS total_booking_revenue,
            SUM(sr.service_revenue) AS total_service_revenue,
            SUM(rb.booking_revenue + sr.service_revenue) AS total_revenue,

            -- Средний доход на номер
            ROUND(SUM(rb.booking_revenue + sr.service_revenue) / COUNT(*), 2) AS avg_revenue_per_room,

            -- Рентабельность (предполагаем фиксированные расходы в зависимости от категории)
            ROUND(SUM(rb.booking_revenue + sr.service_revenue) * 100.0 / 
                SUM(
                    CASE 
                        WHEN rb.price_category = 'Эконом' THEN 1000
                        WHEN rb.price_category = 'Стандарт' THEN 2000
                        WHEN rb.price_category = 'Комфорт' THEN 3000
                        ELSE 5000
                    END * (%s - %s + 1)
                ), 2) AS profitability_ratio
        FROM 
            room_bookings rb
        JOIN 
            service_revenue sr ON rb.room_id = sr.room_id
        GROUP BY 
            rb.hotel_name, rb.hotel_rating, rb.room_capacity, rb.price_category
        ORDER BY 
            profitability_ratio DESC, rb.hotel_name;
        """

        params = (
            start_date_obj, start_date_obj, end_date_obj, end_date_obj,
            end_date_obj, end_date_obj, start_date_obj, start_date_obj,
            start_date_obj, end_date_obj, start_date_obj, end_date_obj,
            start_date_obj, end_date_obj,
            hotel_rating, hotel_rating, room_capacity, room_capacity,
            start_date_obj, end_date_obj,
            end_date_obj, start_date_obj, end_date_obj, start_date_obj,
            end_date_obj, start_date_obj
        )

        results = execute_query(query, params, fetch=True)

        return render_template(
            'admin/queries/room_profitability.html',
            results=results,
            hotel_rating=hotel_rating,
            room_capacity=room_capacity,
            start_date=start_date,
            end_date=end_date
        )

    return render_template('admin/queries/room_profitability_form.html')


@bp.route('/guest-details-by-room', methods=['GET', 'POST'])
@login_required
def guest_details_by_room():
    """
    Запрос 10: Получить сведения о постояльце из заданного номера
    """
    # Получим список всех номеров для выбора
    rooms_query = """
    SELECT 
        r.id, 
        h.name || ' - Номер ' || r.room_number || ' (Этаж ' || r.floor_number || ')' AS room_description
    FROM 
        room r
    JOIN 
        hotel h ON r.hotel_id = h.id
    ORDER BY 
        h.name, r.floor_number, r.room_number;
    """
    rooms = execute_query(rooms_query, fetch=True)

    if request.method == 'POST':
        room_id = request.form.get('room_id', type=int)

        # Получим информацию о текущем госте в номере
        current_guest_query = """
        SELECT 
            g.id AS guest_id,
            g.last_name || ' ' || g.first_name AS guest_name,
            g.phone,
            g.email,
            r.room_number,
            h.name AS hotel_name,
            b.check_in_date,
            b.check_out_date,
            b.id AS booking_id
        FROM 
            guest g
        JOIN 
            booking b ON g.id = b.guest_id
        JOIN 
            booking_room br ON b.id = br.booking_id
        JOIN 
            room r ON br.room_id = r.id
        JOIN 
            hotel h ON r.hotel_id = h.id
        WHERE 
            r.id = %s
            AND b.status = 'Забронировано'
            AND CURRENT_DATE BETWEEN b.check_in_date AND b.check_out_date
        LIMIT 1;
        """

        current_guest = execute_query(current_guest_query, (room_id,), fetch=True, fetchone=True)

        if current_guest:
            guest_id = current_guest['guest_id']
            booking_id = current_guest['booking_id']

            # Получим информацию об услугах
            services_query = """
            SELECT 
                st.name AS service_name,
                su.usage_date,
                su.cost,
                su.paid
            FROM 
                service_usage su
            JOIN 
                service_type st ON su.service_type_id = st.id
            WHERE 
                su.guest_id = %s
                AND (su.booking_id = %s OR su.room_id = %s)
            ORDER BY 
                su.usage_date DESC;
            """

            services = execute_query(services_query, (guest_id, booking_id, room_id), fetch=True)

            # Получим информацию о жалобах
            complaints_query = """
            SELECT 
                c.complaint_date,
                c.description,
                c.resolved,
                c.resolution_date,
                c.resolution_details
            FROM 
                complaint c
            WHERE 
                c.guest_id = %s
            ORDER BY 
                c.complaint_date DESC;
            """

            complaints = execute_query(complaints_query, (guest_id,), fetch=True)

            # Рассчитаем общую сумму за услуги и сколько неоплачено
            total_services_amount = sum(service['cost'] for service in services) if services else 0
            unpaid_amount = sum(service['cost'] for service in services if not service['paid']) if services else 0

            return render_template(
                'admin/queries/guest_details_by_room.html',
                current_guest=current_guest,
                services=services,
                complaints=complaints,
                total_services_amount=total_services_amount,
                unpaid_amount=unpaid_amount,
                room_id=room_id
            )
        else:
            # Если в номере нет текущего гостя, получим информацию о номере
            room_info_query = """
            SELECT 
                r.room_number,
                h.name AS hotel_name,
                r.floor_number,
                r.room_capacity,
                r.base_rate,
                r.is_available
            FROM 
                room r
            JOIN 
                hotel h ON r.hotel_id = h.id
            WHERE 
                r.id = %s;
            """

            room_info = execute_query(room_info_query, (room_id,), fetch=True, fetchone=True)

            # Получим последнего гостя в этом номере
            last_guest_query = """
            SELECT 
                g.id AS guest_id,
                g.last_name || ' ' || g.first_name AS guest_name,
                b.check_in_date,
                b.check_out_date,
                b.status
            FROM 
                guest g
            JOIN 
                booking b ON g.id = b.guest_id
            JOIN 
                booking_room br ON b.id = br.booking_id
            WHERE 
                br.room_id = %s
            ORDER BY 
                b.check_out_date DESC
            LIMIT 1;
            """

            last_guest = execute_query(last_guest_query, (room_id,), fetch=True, fetchone=True)

            return render_template(
                'admin/queries/room_without_guest.html',
                room_info=room_info,
                last_guest=last_guest,
                room_id=room_id
            )

    return render_template('admin/queries/guest_details_by_room_form.html', rooms=rooms)


@bp.route('/firms-with-contracts', methods=['GET', 'POST'])
@login_required
def firms_with_contracts():
    """
    Запрос 11: Получить сведения о фирмах, с которыми заключены договора на указанный период
    """
    if request.method == 'POST':
        target_date = request.form.get('target_date')

        if target_date:
            target_date_obj = datetime.strptime(target_date, '%Y-%m-%d').date()
        else:
            target_date_obj = date.today()

        query = """
        SELECT 
            f.id AS firm_id,
            f.name AS firm_name,
            f.firm_type,
            f.address,
            f.phone,
            f.is_active,
            c.contract_start_date,
            c.contract_end_date,
            c.discount_rate,
            -- Рассчитываем сколько дней осталось до истечения договора
            (c.contract_end_date - %s) AS days_remaining,
            -- Количество бронирований по договору
            (
                SELECT COUNT(*)
                FROM booking b
                WHERE b.firm_id = f.id
                AND b.status != 'Отменено'
                AND (
                    (b.check_in_date BETWEEN c.contract_start_date AND c.contract_end_date) OR
                    (b.check_out_date BETWEEN c.contract_start_date AND c.contract_end_date) OR
                    (b.check_in_date <= c.contract_start_date AND b.check_out_date >= c.contract_end_date)
                )
            ) AS bookings_count
        FROM 
            firm f
        JOIN 
            contract c ON f.id = c.firm_id
        WHERE 
            %s BETWEEN c.contract_start_date AND c.contract_end_date
            AND f.is_active = TRUE
        ORDER BY 
            days_remaining, f.name;
        """

        firms = execute_query(query, (target_date_obj, target_date_obj), fetch=True)

        return render_template(
            'admin/queries/firms_with_contracts.html',
            firms=firms,
            target_date=target_date,
            total_firms=len(firms) if firms else 0
        )

    return render_template('admin/queries/firms_with_contracts_form.html')


@bp.route('/frequent-guests', methods=['GET', 'POST'])
@login_required
def frequent_guests():
    """
    Запрос 12: Получить сведения о наиболее часто посещающих гостиницу постояльцах
    """
    # Получим список всех отелей для выбора
    hotels_query = "SELECT id, name FROM hotel ORDER BY name;"
    hotels = execute_query(hotels_query, fetch=True)

    if request.method == 'POST':
        hotel_id = request.form.get('hotel_id', type=int)
        min_visits = request.form.get('min_visits', type=int) or 2

        query = """
        SELECT 
            g.id AS guest_id,
            g.last_name || ' ' || g.first_name AS guest_name,
            g.phone,
            g.email,
            COUNT(DISTINCT b.id) AS visit_count,
            SUM((b.check_out_date - b.check_in_date)) AS total_days_stayed,
            MIN(b.check_in_date) AS first_visit,
            MAX(b.check_out_date) AS last_visit,
            ROUND(AVG((b.check_out_date - b.check_in_date)), 1) AS avg_stay_length,
            STRING_AGG(DISTINCT h.name, ', ') AS visited_hotels
        FROM 
            guest g
        JOIN 
            booking b ON g.id = b.guest_id
        JOIN 
            booking_room br ON b.id = br.booking_id
        JOIN 
            room r ON br.room_id = r.id
        JOIN 
            hotel h ON r.hotel_id = h.id
        WHERE 
            b.status != 'Отменено'
            AND (%s IS NULL OR r.hotel_id = %s)
        GROUP BY 
            g.id, g.last_name, g.first_name, g.phone, g.email
        HAVING 
            COUNT(DISTINCT b.id) >= %s
        ORDER BY 
            visit_count DESC, total_days_stayed DESC;
        """

        guests = execute_query(query, (hotel_id, hotel_id, min_visits), fetch=True)

        # Определим название отеля для заголовка
        hotel_name = "всех отелях"
        if hotel_id:
            for hotel in hotels:
                if hotel['id'] == hotel_id:
                    hotel_name = f"отеле \"{hotel['name']}\""
                    break

        return render_template(
            'admin/queries/frequent_guests.html',
            guests=guests,
            hotel_id=hotel_id,
            min_visits=min_visits,
            hotel_name=hotel_name,
            total_guests=len(guests) if guests else 0
        )

    return render_template('admin/queries/frequent_guests_form.html', hotels=hotels)


@bp.route('/new-clients', methods=['GET', 'POST'])
@login_required
def new_clients():
    """
    Запрос 13: Получить сведения о новых клиентах за указанный период
    """
    if request.method == 'POST':
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')

        # Конвертация дат
        start_date_obj = None
        end_date_obj = None

        if start_date:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
        else:
            # Если не указана начальная дата, берем начало текущего месяца
            today = date.today()
            start_date_obj = date(today.year, today.month, 1)
            start_date = start_date_obj.strftime('%Y-%m-%d')

        if end_date:
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
        else:
            # Если не указана конечная дата, берем текущую дату
            end_date_obj = date.today()
            end_date = end_date_obj.strftime('%Y-%m-%d')

        query = """
        WITH first_bookings AS (
            SELECT 
                guest_id,
                MIN(booking_date) AS first_booking_date
            FROM 
                booking
            GROUP BY 
                guest_id
        )
        SELECT 
            g.id AS guest_id,
            g.last_name || ' ' || g.first_name AS guest_name,
            g.phone,
            g.email,
            fb.first_booking_date,
            -- Информация о первом бронировании
            b.check_in_date,
            b.check_out_date,
            h.name AS hotel_name,
            r.room_number,
            (b.check_out_date - b.check_in_date) AS stay_length,
            b.total_persons
        FROM 
            guest g
        JOIN 
            first_bookings fb ON g.id = fb.guest_id
        JOIN 
            booking b ON g.id = b.guest_id AND fb.first_booking_date = b.booking_date
        JOIN 
            booking_room br ON b.id = br.booking_id
        JOIN 
            room r ON br.room_id = r.id
        JOIN 
            hotel h ON r.hotel_id = h.id
        WHERE 
            fb.first_booking_date BETWEEN %s AND %s
        ORDER BY 
            fb.first_booking_date DESC;
        """

        new_clients = execute_query(query, (start_date_obj, end_date_obj), fetch=True)

        return render_template(
            'admin/queries/new_clients.html',
            new_clients=new_clients,
            start_date=start_date,
            end_date=end_date,
            total_clients=len(new_clients) if new_clients else 0
        )

    return render_template('admin/queries/new_clients_form.html')


@bp.route('/guest-history/<int:guest_id>')
@login_required
def guest_history(guest_id):
    """
    Запрос 14: Получить сведения о конкретном человеке, сколько раз он посещал гостиницу
    """
    # Получим основную информацию о госте
    guest_query = """
    SELECT 
        g.id,
        g.last_name || ' ' || g.first_name AS guest_name,
        g.phone,
        g.email,
        g.passport_series,
        g.passport_number,
        COUNT(DISTINCT b.id) AS visit_count,
        MIN(b.check_in_date) AS first_visit,
        MAX(b.check_out_date) AS last_visit
    FROM 
        guest g
    LEFT JOIN 
        booking b ON g.id = b.guest_id AND b.status != 'Отменено'
    WHERE 
        g.id = %s
    GROUP BY 
        g.id, g.last_name, g.first_name, g.phone, g.email, g.passport_series, g.passport_number;
    """

    guest = execute_query(guest_query, (guest_id,), fetch=True, fetchone=True)

    if not guest:
        return render_template('admin/queries/guest_not_found.html', guest_id=guest_id)

    # Получим историю посещений
    bookings_query = """
    SELECT 
        b.id AS booking_id,
        b.booking_date,
        b.check_in_date,
        b.check_out_date,
        b.status,
        b.total_rooms,
        b.total_persons,
        STRING_AGG(h.name || ' - Номер ' || r.room_number, ', ') AS rooms,
        SUM((b.check_out_date - b.check_in_date) * r.base_rate) AS room_cost
    FROM 
        booking b
    JOIN 
        booking_room br ON b.id = br.booking_id
    JOIN 
        room r ON br.room_id = r.id
    JOIN 
        hotel h ON r.hotel_id = h.id
    WHERE 
        b.guest_id = %s
    GROUP BY 
        b.id, b.booking_date, b.check_in_date, b.check_out_date, b.status, b.total_rooms, b.total_persons
    ORDER BY 
        b.check_in_date DESC;
    """

    bookings = execute_query(bookings_query, (guest_id,), fetch=True)

    # Получим данные об услугах и оплатах
    services_query = """
    SELECT 
        b.id AS booking_id,
        st.name AS service_name,
        su.usage_date,
        su.cost,
        su.paid
    FROM 
        service_usage su
    JOIN 
        service_type st ON su.service_type_id = st.id
    LEFT JOIN 
        booking b ON su.booking_id = b.id
    WHERE 
        su.guest_id = %s
    ORDER BY 
        su.usage_date DESC;
    """

    services = execute_query(services_query, (guest_id,), fetch=True)

    # Группируем услуги по бронированиям
    services_by_booking = {}
    total_services_cost = 0
    total_unpaid = 0

    for service in services:
        booking_id = service['booking_id']
        if booking_id not in services_by_booking:
            services_by_booking[booking_id] = []

        services_by_booking[booking_id].append(service)
        total_services_cost += service['cost']
        if not service['paid']:
            total_unpaid += service['cost']

    # Получим данные о жалобах
    complaints_query = """
    SELECT 
        c.id AS complaint_id,
        c.complaint_date,
        c.description,
        c.resolved,
        c.resolution_date,
        c.resolution_details
    FROM 
        complaint c
    WHERE 
        c.guest_id = %s
    ORDER BY 
        c.complaint_date DESC;
    """

    complaints = execute_query(complaints_query, (guest_id,), fetch=True)

    return render_template(
        'admin/queries/guest_history.html',
        guest=guest,
        bookings=bookings,
        services=services,
        services_by_booking=services_by_booking,
        complaints=complaints,
        total_services_cost=total_services_cost,
        total_unpaid=total_unpaid
    )


@bp.route('/room-occupancy-history/<int:room_id>', methods=['GET', 'POST'])
@login_required
def room_occupancy_history(room_id):
    """
    Запрос 15: Получить сведения о конкретном номере: кем он был занят в определенный период
    """
    # Получим информацию о номере
    room_query = """
    SELECT 
        r.id AS room_id,
        r.room_number,
        r.floor_number,
        r.room_capacity,
        r.base_rate,
        r.is_available,
        h.name AS hotel_name,
        h.rating AS hotel_stars
    FROM 
        room r
    JOIN 
        hotel h ON r.hotel_id = h.id
    WHERE 
        r.id = %s;
    """

    room = execute_query(room_query, (room_id,), fetch=True, fetchone=True)

    if not room:
        return render_template('admin/queries/room_not_found.html', room_id=room_id)

    if request.method == 'POST':
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')

        # Конвертация дат
        start_date_obj = None
        end_date_obj = None

        if start_date:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
        else:
            # Если не указана начальная дата, берем дату 3 месяца назад
            start_date_obj = date.today().replace(day=1)
            start_date_obj = start_date_obj.replace(month=((start_date_obj.month - 3) % 12) or 12)
            if start_date_obj.month > 9:
                start_date_obj = start_date_obj.replace(year=start_date_obj.year - 1)
            start_date = start_date_obj.strftime('%Y-%m-%d')

        if end_date:
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
        else:
            # Если не указана конечная дата, берем текущую дату + 1 месяц
            end_date_obj = date.today()
            next_month = end_date_obj.month + 1
            year_offset = 0
            if next_month > 12:
                next_month = 1
                year_offset = 1

            end_date_obj = date(end_date_obj.year + year_offset, next_month, 1) - timedelta(days=1)
            end_date = end_date_obj.strftime('%Y-%m-%d')

        # Получим историю бронирований номера
        bookings_query = """
        SELECT 
            b.id AS booking_id,
            g.id AS guest_id,
            g.last_name || ' ' || g.first_name AS guest_name,
            b.booking_date,
            b.check_in_date,
            b.check_out_date,
            b.status,
            (b.check_out_date - b.check_in_date) AS stay_length,
            CASE
                WHEN b.firm_id IS NOT NULL THEN f.name
                ELSE 'Индивидуальное'
            END AS booking_type,
            b.total_persons
        FROM 
            booking_room br
        JOIN 
            booking b ON br.booking_id = b.id
        LEFT JOIN 
            guest g ON b.guest_id = g.id
        LEFT JOIN 
            firm f ON b.firm_id = f.id
        WHERE 
            br.room_id = %s
            AND (
                (b.check_in_date BETWEEN %s AND %s) OR
                (b.check_out_date BETWEEN %s AND %s) OR
                (b.check_in_date <= %s AND b.check_out_date >= %s)
            )
        ORDER BY 
            b.check_in_date;
        """

        bookings = execute_query(
            bookings_query,
            (room_id, start_date_obj, end_date_obj, start_date_obj, end_date_obj, start_date_obj, end_date_obj),
            fetch=True
        )

        # Посчитаем статистику использования номера
        total_days = (end_date_obj - start_date_obj).days + 1
        occupied_days = 0
        revenue = 0

        for booking in bookings:
            # Вычислим пересечение периода бронирования с запрошенным периодом
            check_in = max(booking['check_in_date'], start_date_obj)
            check_out = min(booking['check_out_date'], end_date_obj)

            days = (check_out - check_in).days
            if days > 0:
                occupied_days += days
                revenue += days * room['base_rate']

        # Рассчитаем процент загрузки
        occupancy_rate = (occupied_days / total_days) * 100 if total_days > 0 else 0

        # Получим услуги, связанные с этим номером
        services_query = """
        SELECT 
            st.name AS service_name,
            su.usage_date,
            g.last_name || ' ' || g.first_name AS guest_name,
            su.cost,
            su.paid
        FROM 
            service_usage su
        JOIN 
            service_type st ON su.service_type_id = st.id
        JOIN 
            guest g ON su.guest_id = g.id
        WHERE 
            su.room_id = %s
            AND su.usage_date BETWEEN %s AND %s
        ORDER BY 
            su.usage_date DESC;
        """

        services = execute_query(services_query, (room_id, start_date_obj, end_date_obj), fetch=True)
        service_revenue = sum(service['cost'] for service in services) if services else 0

        return render_template(
            'admin/queries/room_occupancy_history.html',
            room=room,
            bookings=bookings,
            services=services,
            start_date=start_date,
            end_date=end_date,
            total_days=total_days,
            occupied_days=occupied_days,
            occupancy_rate=occupancy_rate,
            room_revenue=revenue,
            service_revenue=service_revenue,
            total_revenue=revenue + service_revenue
        )

    return render_template('admin/queries/room_occupancy_history_form.html', room=room)


@bp.route('/partner-booking-ratio')
@login_required
def partner_booking_ratio():
    """
    Запрос 16: Получить процентное отношение всех номеров к номерам, бронируемым партнерами
    """
    query = """
    WITH booking_stats AS (
        SELECT 
            h.id AS hotel_id,
            h.name AS hotel_name,
            COUNT(DISTINCT r.id) AS total_rooms,
            -- Количество номеров, которые когда-либо бронировались партнерами
            COUNT(DISTINCT CASE 
                WHEN EXISTS (
                    SELECT 1 
                    FROM booking_room br 
                    JOIN booking b ON br.booking_id = b.id 
                    WHERE br.room_id = r.id AND b.firm_id IS NOT NULL AND b.status != 'Отменено'
                ) THEN r.id 
                ELSE NULL 
            END) AS partner_booked_rooms,

            -- Количество бронирований партнеров
            (
                SELECT COUNT(DISTINCT b.id)
                FROM booking b
                JOIN booking_room br ON b.id = br.booking_id
                JOIN room r2 ON br.room_id = r2.id
                WHERE r2.hotel_id = h.id
                AND b.firm_id IS NOT NULL
                AND b.status != 'Отменено'
            ) AS partner_bookings,

            -- Общее количество бронирований
            (
                SELECT COUNT(DISTINCT b.id)
                FROM booking b
                JOIN booking_room br ON b.id = br.booking_id
                JOIN room r2 ON br.room_id = r2.id
                WHERE r2.hotel_id = h.id
                AND b.status != 'Отменено'
            ) AS total_bookings
        FROM 
            hotel h
        JOIN 
            room r ON h.id = r.hotel_id
        GROUP BY 
            h.id, h.name
    ),
    results AS (
        SELECT 
            bs.hotel_name,
            bs.total_rooms,
            bs.partner_booked_rooms,
            bs.total_rooms - bs.partner_booked_rooms AS never_partner_booked,
            ROUND(bs.partner_booked_rooms * 100.0 / bs.total_rooms, 2) AS partner_room_percentage,
            ROUND((bs.total_rooms - bs.partner_booked_rooms) * 100.0 / bs.total_rooms, 2) AS non_partner_room_percentage,
            bs.partner_bookings,
            bs.total_bookings,
            ROUND(bs.partner_bookings * 100.0 / NULLIF(bs.total_bookings, 0), 2) AS partner_booking_percentage,
            0 AS is_summary -- Это обычная строка отеля
        FROM 
            booking_stats bs
        UNION ALL
        SELECT 
            'Все отели' AS hotel_name,
            SUM(bs.total_rooms) AS total_rooms,
            SUM(bs.partner_booked_rooms) AS partner_booked_rooms,
            SUM(bs.total_rooms - bs.partner_booked_rooms) AS never_partner_booked,
            ROUND(SUM(bs.partner_booked_rooms) * 100.0 / SUM(bs.total_rooms), 2) AS partner_room_percentage,
            ROUND(SUM(bs.total_rooms - bs.partner_booked_rooms) * 100.0 / SUM(bs.total_rooms), 2) AS non_partner_room_percentage,
            SUM(bs.partner_bookings) AS partner_bookings,
            SUM(bs.total_bookings) AS total_bookings,
            ROUND(SUM(bs.partner_bookings) * 100.0 / NULLIF(SUM(bs.total_bookings), 0), 2) AS partner_booking_percentage,
            1 AS is_summary -- Это строка с итогами
        FROM 
            booking_stats bs
    )
    SELECT * FROM results
    ORDER BY 
        is_summary, hotel_name;
    """

    results = execute_query(query, fetch=True)

    # Получим список партнеров с количеством бронирований
    partners_query = """
    SELECT 
        f.name AS firm_name,
        COUNT(DISTINCT b.id) AS booking_count,
        COUNT(DISTINCT br.room_id) AS rooms_booked,
        ROUND(COUNT(DISTINCT b.id) * 100.0 / (
            SELECT COUNT(*) FROM booking WHERE firm_id IS NOT NULL AND status != 'Отменено'
        ), 2) AS percentage_of_partner_bookings
    FROM 
        firm f
    JOIN 
        booking b ON f.id = b.firm_id
    JOIN 
        booking_room br ON b.id = br.booking_id
    WHERE 
        b.status != 'Отменено'
    GROUP BY 
        f.name
    ORDER BY 
        booking_count DESC;
    """

    partners = execute_query(partners_query, fetch=True)

    return render_template(
        'admin/queries/partner_booking_ratio.html',
        results=results,
        partners=partners
    )

# Добавляем все маршруты к одному Blueprint
@bp.route('/all-guests')
@login_required
def all_guests():
    """
    Получить список всех гостей для выбора в других запросах
    """
    query = """
    SELECT 
        g.id,
        g.last_name || ' ' || g.first_name AS guest_name,
        COUNT(DISTINCT b.id) AS visit_count
    FROM 
        guest g
    LEFT JOIN 
        booking b ON g.id = b.guest_id AND b.status != 'Отменено'
    GROUP BY 
        g.id, g.last_name, g.first_name
    ORDER BY 
        g.last_name, g.first_name;
    """

    guests = execute_query(query, fetch=True)

    return render_template(
        'admin/queries/all_guests.html',
        guests=guests
    )


@bp.route('/all-rooms')
@login_required
def all_rooms():
    """
    Получить список всех номеров для выбора в других запросах
    """
    query = """
    SELECT 
        r.id,
        h.name || ' - Номер ' || r.room_number || ' (Этаж ' || r.floor_number || ')' AS room_description,
        r.is_available,
        EXISTS (
            SELECT 1
            FROM booking_room br
            JOIN booking b ON br.booking_id = b.id
            WHERE 
                br.room_id = r.id
                AND b.status = 'Забронировано'
                AND CURRENT_DATE BETWEEN b.check_in_date AND b.check_out_date
        ) AS currently_occupied
    FROM 
        room r
    JOIN 
        hotel h ON r.hotel_id = h.id
    ORDER BY 
        h.name, r.floor_number, r.room_number;
    """

    rooms = execute_query(query, fetch=True)

    return render_template(
        'admin/queries/all_rooms.html',
        rooms=rooms
    )