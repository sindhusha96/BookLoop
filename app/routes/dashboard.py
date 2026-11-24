from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Book, BookRequest, Wishlist, ActivityLog

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@login_required
def index():
    """Student dashboard overview with summary metrics and activity."""
    # Summary counts
    my_books = Book.query.filter_by(user_id=current_user.id)
    my_books_count = my_books.count()
    active_listings_count = my_books.filter_by(is_available=True).count()

    # Incoming requests
    incoming_query = BookRequest.query.join(BookRequest.book).filter(BookRequest.book.has(user_id=current_user.id))
    pending_incoming_count = incoming_query.filter(BookRequest.status == 'Pending').count()
    accepted_incoming_count = incoming_query.filter(BookRequest.status == 'Accepted').count()

    # Sent requests
    sent_query = BookRequest.query.filter_by(requester_id=current_user.id)
    sent_requests_count = sent_query.count()
    pending_sent_count = sent_query.filter_by(status='Pending').count()
    accepted_sent_count = sent_query.filter_by(status='Accepted').count()

    # Completed transactions (both incoming and sent)
    completed_incoming = incoming_query.filter(BookRequest.status == 'Completed').count()
    completed_sent = sent_query.filter_by(status='Completed').count()
    total_completed = completed_incoming + completed_sent

    # Wishlist count
    wishlist_count = Wishlist.query.filter_by(user_id=current_user.id).count()

    # Recent activity logs
    recent_activities = ActivityLog.query.filter_by(user_id=current_user.id).order_by(ActivityLog.created_at.desc()).limit(8).all()

    # Urgent pending incoming requests preview
    urgent_incoming = incoming_query.filter(BookRequest.status == 'Pending').order_by(BookRequest.created_at.desc()).limit(3).all()

    return render_template(
        'dashboard/index.html',
        my_books_count=my_books_count,
        active_listings_count=active_listings_count,
        pending_incoming_count=pending_incoming_count,
        accepted_incoming_count=accepted_incoming_count,
        sent_requests_count=sent_requests_count,
        pending_sent_count=pending_sent_count,
        accepted_sent_count=accepted_sent_count,
        total_completed=total_completed,
        wishlist_count=wishlist_count,
        recent_activities=recent_activities,
        urgent_incoming=urgent_incoming
    )


@dashboard_bp.route('/my-listings')
@login_required
def my_listings():
    """Manage user's own listed books."""
    books = Book.query.filter_by(user_id=current_user.id).order_by(Book.created_at.desc()).all()
    return render_template('dashboard/my_listings.html', books=books)


@dashboard_bp.route('/incoming-requests')
@login_required
def incoming_requests():
    """View and manage incoming requests received for user's books."""
    status_filter = request.args.get('status', 'all')

    query = BookRequest.query.join(BookRequest.book).filter(BookRequest.book.has(user_id=current_user.id))

    if status_filter != 'all':
        query = query.filter(BookRequest.status == status_filter.capitalize())

    requests_list = query.order_by(BookRequest.created_at.desc()).all()

    return render_template('dashboard/incoming_requests.html', requests=requests_list, current_filter=status_filter)


@dashboard_bp.route('/sent-requests')
@login_required
def sent_requests():
    """View and manage requests sent to other students."""
    status_filter = request.args.get('status', 'all')

    query = BookRequest.query.filter_by(requester_id=current_user.id)

    if status_filter != 'all':
        query = query.filter(BookRequest.status == status_filter.capitalize())

    requests_list = query.order_by(BookRequest.created_at.desc()).all()

    return render_template('dashboard/sent_requests.html', requests=requests_list, current_filter=status_filter)


@dashboard_bp.route('/wishlist')
@login_required
def wishlist():
    """View saved / bookmarked books."""
    items = Wishlist.query.filter_by(user_id=current_user.id).order_by(Wishlist.created_at.desc()).all()
    return render_template('dashboard/wishlist.html', items=items)


@dashboard_bp.route('/wishlist/toggle/<int:book_id>', methods=['POST'])
@login_required
def toggle_wishlist(book_id):
    """Add or remove a book from the user's wishlist."""
    book = Book.query.get_or_404(book_id)

    existing = Wishlist.query.filter_by(user_id=current_user.id, book_id=book.id).first()

    if existing:
        db.session.delete(existing)
        db.session.commit()
        in_wishlist = False
        message = f'"{book.title}" was removed from your wishlist.'
    else:
        wishlist_item = Wishlist(user_id=current_user.id, book_id=book.id)
        db.session.add(wishlist_item)
        db.session.commit()
        in_wishlist = True
        message = f'"{book.title}" was added to your wishlist!'

    # Support AJAX responses
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
        return jsonify({
            'success': True,
            'in_wishlist': in_wishlist,
            'message': message
        })

    flash(message, 'info')
    return redirect(request.referrer or url_for('books.detail', book_id=book.id))
