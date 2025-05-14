from flask import Blueprint, render_template, redirect, url_for
from app.models.hotel import Hotel
from app.models.room import Room
from app.models.booking import Booking
from app.models.complaint import Complaint

bp = Blueprint('main', __name__)


@bp.route('/')
def index():
    """Главная страница"""
    # Получаем статистику для отображения на панели управления
    hotel_stats = Hotel.get_hotel_stats()
    active_bookings = Booking.get_active_bookings()
    unresolved_complaints = Complaint.get_unresolved()

    # Получаем количество свободных номеров
    available_rooms = Room.get_available_rooms()
    available_rooms_count = len(available_rooms) if available_rooms else 0

    return render_template('index.html',
                           hotel_stats=hotel_stats,
                           active_bookings=active_bookings,
                           unresolved_complaints=unresolved_complaints,
                           available_rooms_count=available_rooms_count)


@bp.route('/dashboard')
def dashboard():
    """Панель управления"""
    return redirect(url_for('main.index'))


@bp.route('/about')
def about():
    """О системе"""
    return render_template('about.html')