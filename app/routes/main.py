from flask import Blueprint, render_template, request, redirect, url_for
from app.models import Book, User, BookRequest
from app import db

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """BookLoop landing page."""
    # Fetch recently listed available books
    recent_books = Book.query.filter_by(is_available=True).order_by(Book.created_at.desc()).limit(6).all()
    
    # Platform statistics
    total_books = Book.query.count()
    total_students = User.query.filter_by(role='student').count()
    completed_exchanges = BookRequest.query.filter_by(status='Completed').count()
    
    # Popular category counts
    popular_categories = [
        {'name': 'Computer Science & IT', 'icon': 'bi-laptop', 'count': Book.query.filter(Book.department.ilike('%Computer%'), Book.is_available==True).count()},
        {'name': 'Business & Management', 'icon': 'bi-briefcase', 'count': Book.query.filter(Book.department.ilike('%Business%'), Book.is_available==True).count()},
        {'name': 'Mechanical Engineering', 'icon': 'bi-gear-wide-connected', 'count': Book.query.filter(Book.department.ilike('%Mechanical%'), Book.is_available==True).count()},
        {'name': 'Medical & Health Sciences', 'icon': 'bi-heart-pulse', 'count': Book.query.filter(Book.department.ilike('%Medical%'), Book.is_available==True).count()},
        {'name': 'Natural Sciences & Math', 'icon': 'bi-calculator', 'count': Book.query.filter(Book.department.ilike('%Science%'), Book.is_available==True).count()},
        {'name': 'Law & Legal Studies', 'icon': 'bi-bank', 'count': Book.query.filter(Book.department.ilike('%Law%'), Book.is_available==True).count()}
    ]

    return render_template(
        'index.html',
        recent_books=recent_books,
        total_books=total_books,
        total_students=total_students,
        completed_exchanges=completed_exchanges,
        popular_categories=popular_categories
    )


@main_bp.route('/about')
def about():
    """About BookLoop mission and story."""
    return render_template('about.html')


@main_bp.route('/contact')
def contact():
    """Contact page and campus representative guidelines."""
    return render_template('contact.html')


@main_bp.route('/privacy')
def privacy():
    """Privacy policy and terms of student exchange."""
    return render_template('privacy.html')
