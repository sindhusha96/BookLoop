from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from app import db
from app.models import User, Book, BookRequest, Report, ActivityLog
from app.utils import admin_required

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    """Admin dashboard overview and analytics."""
    # Key platform metrics
    total_users = User.query.count()
    total_students = User.query.filter_by(role='student').count()
    total_books = Book.query.count()
    active_listings = Book.query.filter_by(is_available=True).count()
    pending_requests = BookRequest.query.filter_by(status='Pending').count()
    completed_exchanges = BookRequest.query.filter_by(status='Completed').count()
    total_reports = Report.query.count()
    pending_reports = Report.query.filter_by(status='Pending').count()

    # Registrations in past 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    new_users_month = User.query.filter(User.created_at >= thirty_days_ago).count()
    new_books_month = Book.query.filter(Book.created_at >= thirty_days_ago).count()

    # Department distribution
    departments = db.session.query(Book.department, db.func.count(Book.id)).group_by(Book.department).order_by(db.func.count(Book.id).desc()).limit(5).all()

    # Condition distribution
    conditions = db.session.query(Book.condition, db.func.count(Book.id)).group_by(Book.condition).all()

    # Recent pending reports
    recent_reports = Report.query.filter_by(status='Pending').order_by(Report.created_at.desc()).limit(5).all()

    # Recent user registrations
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()

    return render_template(
        'admin/dashboard.html',
        total_users=total_users,
        total_students=total_students,
        total_books=total_books,
        active_listings=active_listings,
        pending_requests=pending_requests,
        completed_exchanges=completed_exchanges,
        total_reports=total_reports,
        pending_reports=pending_reports,
        new_users_month=new_users_month,
        new_books_month=new_books_month,
        departments=departments,
        conditions=conditions,
        recent_reports=recent_reports,
        recent_users=recent_users
    )


@admin_bp.route('/users')
@login_required
@admin_required
def users():
    """Manage registered users."""
    search_q = request.args.get('q', '').strip()
    role_filter = request.args.get('role', '').strip()
    status_filter = request.args.get('status', '').strip()

    query = User.query

    if search_q:
        search_pattern = f"%{search_q}%"
        query = query.filter(
            (User.username.ilike(search_pattern)) |
            (User.email.ilike(search_pattern)) |
            (User.full_name.ilike(search_pattern)) |
            (User.college_name.ilike(search_pattern))
        )

    if role_filter:
        query = query.filter_by(role=role_filter)

    if status_filter == 'active':
        query = query.filter_by(is_active=True)
    elif status_filter == 'inactive':
        query = query.filter_by(is_active=False)

    users_list = query.order_by(User.created_at.desc()).all()

    return render_template(
        'admin/users.html',
        users=users_list,
        search_q=search_q,
        role_filter=role_filter,
        status_filter=status_filter
    )


@admin_bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def toggle_user_status(user_id):
    """Activate or deactivate a user account."""
    user = User.query.get_or_404(user_id)

    # Protect self from deactivation
    if user.id == current_user.id:
        flash("You cannot deactivate your own administrative account.", "danger")
        return redirect(url_for('admin.users'))

    user.is_active = not user.is_active
    db.session.commit()

    action_label = "activated" if user.is_active else "deactivated"
    flash(f"Account for {user.username} has been {action_label}.", "info")
    return redirect(url_for('admin.users'))


@admin_bp.route('/books')
@login_required
@admin_required
def books():
    """Manage all book listings."""
    search_q = request.args.get('q', '').strip()
    status_filter = request.args.get('status', '').strip()

    query = Book.query

    if search_q:
        search_pattern = f"%{search_q}%"
        query = query.filter(
            (Book.title.ilike(search_pattern)) |
            (Book.author.ilike(search_pattern)) |
            (Book.isbn.ilike(search_pattern))
        )

    if status_filter == 'available':
        query = query.filter_by(is_available=True)
    elif status_filter == 'unavailable':
        query = query.filter_by(is_available=False)
    elif status_filter == 'reserved':
        query = query.filter_by(is_reserved=True)

    books_list = query.order_by(Book.created_at.desc()).all()

    return render_template(
        'admin/books.html',
        books=books_list,
        search_q=search_q,
        status_filter=status_filter
    )


@admin_bp.route('/reports')
@login_required
@admin_required
def reports():
    """View and resolve listing reports."""
    status_filter = request.args.get('status', 'Pending').strip()

    query = Report.query
    if status_filter and status_filter != 'all':
        query = query.filter_by(status=status_filter)

    reports_list = query.order_by(Report.created_at.desc()).all()

    return render_template(
        'admin/reports.html',
        reports=reports_list,
        status_filter=status_filter
    )


@admin_bp.route('/reports/<int:report_id>/<action>', methods=['POST'])
@login_required
@admin_required
def handle_report(report_id, action):
    """Resolve or dismiss a reported listing."""
    rep = Report.query.get_or_404(report_id)

    if action == 'resolve':
        rep.status = 'Resolved'
        rep.admin_notes = request.form.get('admin_notes', 'Resolved by administrator.')
        flash(f"Report #{rep.id} marked as Resolved.", "success")
    elif action == 'dismiss':
        rep.status = 'Dismissed'
        rep.admin_notes = request.form.get('admin_notes', 'Dismissed as false report.')
        flash(f"Report #{rep.id} dismissed.", "info")
    elif action == 'deactivate_book':
        rep.book.is_available = False
        rep.book.is_reserved = False
        rep.status = 'Resolved'
        rep.admin_notes = 'Listing deactivated due to policy violation.'
        flash(f'Listing "{rep.book.title}" was deactivated and report was resolved.', "warning")
    else:
        abort(400)

    db.session.commit()
    return redirect(url_for('admin.reports'))
