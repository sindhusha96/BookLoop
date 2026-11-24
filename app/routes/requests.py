from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app import db
from app.models import Book, BookRequest, ActivityLog
from app.forms import PurchaseRequestForm, ExchangeRequestForm

requests_bp = Blueprint('requests', __name__)


@requests_bp.route('/purchase/<int:book_id>', methods=['POST'])
@login_required
def create_purchase_request(book_id):
    """Create a purchase request for a listed book."""
    book = Book.query.get_or_404(book_id)

    # Cannot request own book
    if book.user_id == current_user.id:
        flash("You cannot send a purchase request for your own book listing.", "warning")
        return redirect(url_for('books.detail', book_id=book.id))

    # Listing must be available and allow selling
    if not book.is_available or book.is_reserved or book.listing_type not in ['Sell', 'Both']:
        flash("This book is not currently available for purchase.", "danger")
        return redirect(url_for('books.detail', book_id=book.id))

    # Check for duplicate active request
    existing_request = BookRequest.query.filter(
        BookRequest.book_id == book.id,
        BookRequest.requester_id == current_user.id,
        BookRequest.status.in_(['Pending', 'Accepted'])
    ).first()

    if existing_request:
        flash(f"You already have an active request ({existing_request.status}) for this book.", "info")
        return redirect(url_for('dashboard.sent_requests'))

    form = PurchaseRequestForm()
    if form.validate_on_submit():
        req = BookRequest(
            book_id=book.id,
            requester_id=current_user.id,
            request_type='purchase',
            status='Pending',
            message=form.message.data.strip() if form.message.data else None
        )
        db.session.add(req)
        db.session.commit()

        ActivityLog.log(current_user.id, 'PURCHASE_REQUEST_SENT', f'Sent purchase request for "{book.title}".')
        flash(f'Purchase request sent to {book.owner.full_name}! You will be notified when they accept.', 'success')
        return redirect(url_for('dashboard.sent_requests'))

    flash("Failed to submit request. Please try again.", "danger")
    return redirect(url_for('books.detail', book_id=book.id))


@requests_bp.route('/exchange/<int:book_id>', methods=['POST'])
@login_required
def create_exchange_request(book_id):
    """Create an exchange request offering one of user's listed books."""
    book = Book.query.get_or_404(book_id)

    # Cannot request own book
    if book.user_id == current_user.id:
        flash("You cannot exchange with your own book listing.", "warning")
        return redirect(url_for('books.detail', book_id=book.id))

    # Listing must allow exchange
    if not book.is_available or book.is_reserved or book.listing_type not in ['Exchange', 'Both']:
        flash("This book is not currently available for exchange.", "danger")
        return redirect(url_for('books.detail', book_id=book.id))

    # Check for duplicate active request
    existing_request = BookRequest.query.filter(
        BookRequest.book_id == book.id,
        BookRequest.requester_id == current_user.id,
        BookRequest.status.in_(['Pending', 'Accepted'])
    ).first()

    if existing_request:
        flash(f"You already have an active request ({existing_request.status}) for this book.", "info")
        return redirect(url_for('dashboard.sent_requests'))

    form = ExchangeRequestForm()
    # Populate user's available books for validation
    user_books = Book.query.filter_by(
        user_id=current_user.id,
        is_available=True,
        is_reserved=False
    ).all()
    form.offered_book_id.choices = [(b.id, b.title) for b in user_books]

    if not user_books:
        flash("You must have at least one available book listed on BookLoop to offer an exchange.", "warning")
        return redirect(url_for('books.create'))

    if form.validate_on_submit():
        offered_book = Book.query.get(form.offered_book_id.data)
        if not offered_book or offered_book.user_id != current_user.id or not offered_book.is_available or offered_book.is_reserved:
            flash("The selected offered book is no longer available.", "danger")
            return redirect(url_for('books.detail', book_id=book.id))

        req = BookRequest(
            book_id=book.id,
            requester_id=current_user.id,
            request_type='exchange',
            offered_book_id=offered_book.id,
            status='Pending',
            message=form.message.data.strip() if form.message.data else None
        )
        db.session.add(req)
        db.session.commit()

        ActivityLog.log(current_user.id, 'EXCHANGE_REQUEST_SENT', f'Proposed exchange: "{offered_book.title}" for "{book.title}".')
        flash(f'Exchange request sent to {book.owner.full_name}! Check Sent Requests for updates.', 'success')
        return redirect(url_for('dashboard.sent_requests'))

    flash("Failed to process exchange request. Please check the offered book choice.", "danger")
    return redirect(url_for('books.detail', book_id=book.id))


@requests_bp.route('/<int:request_id>/accept', methods=['POST'])
@login_required
def accept_request(request_id):
    """Book owner accepts incoming request."""
    req = BookRequest.query.get_or_404(request_id)

    # Authorization check: only the book's owner can accept
    if req.book.user_id != current_user.id:
        flash("You are not authorized to accept this request.", "danger")
        return redirect(url_for('dashboard.incoming_requests'))

    if req.status != 'Pending':
        flash(f"This request has already been {req.status.lower()}.", "warning")
        return redirect(url_for('dashboard.incoming_requests'))

    # Mark request as accepted
    req.status = 'Accepted'

    # Reserve the listing
    req.book.is_reserved = True

    # If it's an exchange, also reserve the offered book
    if req.request_type == 'exchange' and req.offered_book:
        req.offered_book.is_reserved = True

    db.session.commit()

    # Log activities for both parties
    ActivityLog.log(current_user.id, 'REQUEST_ACCEPTED', f'Accepted {req.request_type} request for "{req.book.title}".')
    ActivityLog.log(req.requester_id, 'REQUEST_ACCEPTED_BY_OWNER', f'Your {req.request_type} request for "{req.book.title}" was accepted!')

    flash(f"You accepted the request! Contact details for {req.requester.full_name} are now available below to coordinate pickup.", "success")
    return redirect(url_for('dashboard.incoming_requests'))


@requests_bp.route('/<int:request_id>/reject', methods=['POST'])
@login_required
def reject_request(request_id):
    """Book owner rejects incoming request."""
    req = BookRequest.query.get_or_404(request_id)

    # Authorization check
    if req.book.user_id != current_user.id:
        flash("You are not authorized to reject this request.", "danger")
        return redirect(url_for('dashboard.incoming_requests'))

    if req.status != 'Pending':
        flash(f"This request has already been {req.status.lower()}.", "warning")
        return redirect(url_for('dashboard.incoming_requests'))

    req.status = 'Rejected'
    db.session.commit()

    ActivityLog.log(current_user.id, 'REQUEST_REJECTED', f'Declined {req.request_type} request for "{req.book.title}".')
    flash("The request has been rejected.", "info")
    return redirect(url_for('dashboard.incoming_requests'))


@requests_bp.route('/<int:request_id>/cancel', methods=['POST'])
@login_required
def cancel_request(request_id):
    """Requester cancels a pending request."""
    req = BookRequest.query.get_or_404(request_id)

    # Authorization check: only requester can cancel
    if req.requester_id != current_user.id:
        flash("You are not authorized to cancel this request.", "danger")
        return redirect(url_for('dashboard.sent_requests'))

    if req.status != 'Pending':
        flash(f"Cannot cancel a request that is already {req.status.lower()}.", "warning")
        return redirect(url_for('dashboard.sent_requests'))

    req.status = 'Cancelled'
    db.session.commit()

    ActivityLog.log(current_user.id, 'REQUEST_CANCELLED', f'Cancelled {req.request_type} request for "{req.book.title}".')
    flash("Your request has been cancelled.", "info")
    return redirect(url_for('dashboard.sent_requests'))


@requests_bp.route('/<int:request_id>/complete', methods=['POST'])
@login_required
def complete_request(request_id):
    """Mark an accepted transaction / exchange as completed."""
    req = BookRequest.query.get_or_404(request_id)

    # Either party can mark as complete once accepted
    if req.book.user_id != current_user.id and req.requester_id != current_user.id:
        flash("You are not authorized to complete this request.", "danger")
        return redirect(url_for('dashboard.index'))

    if req.status != 'Accepted':
        flash("Only accepted requests can be marked as completed.", "warning")
        return redirect(url_for('dashboard.index'))

    req.status = 'Completed'

    # Once completed, mark the primary book as unavailable (sold or exchanged)
    req.book.is_available = False
    req.book.is_reserved = False

    # If exchange, also mark offered book as unavailable
    if req.request_type == 'exchange' and req.offered_book:
        req.offered_book.is_available = False
        req.offered_book.is_reserved = False

    db.session.commit()

    ActivityLog.log(current_user.id, 'REQUEST_COMPLETED', f'Completed {req.request_type} for "{req.book.title}".')
    flash("Congratulations! The transaction has been marked as completed.", "success")
    return redirect(request.referrer or url_for('dashboard.index'))
