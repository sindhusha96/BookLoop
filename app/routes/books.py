from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, current_app
from flask_login import login_required, current_user
from app import db
from app.models import Book, User, Wishlist, Report, ActivityLog
from app.forms import (
    BookListingForm, PurchaseRequestForm, ExchangeRequestForm, ReportBookForm,
    DEPARTMENT_CHOICES, SEMESTER_CHOICES, CONDITION_CHOICES, LISTING_TYPE_CHOICES
)
from app.utils import save_book_image

books_bp = Blueprint('books', __name__)


@books_bp.route('/browse')
def browse():
    """Search, filter, sort, and paginate book listings."""
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config.get('ITEMS_PER_PAGE', 9)

    # Filter arguments
    q = request.args.get('q', '').strip()
    subject = request.args.get('subject', '').strip()
    department = request.args.get('department', '').strip()
    semester = request.args.get('semester', '').strip()
    condition = request.args.get('condition', '').strip()
    listing_type = request.args.get('listing_type', '').strip()
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    sort_by = request.args.get('sort_by', 'newest').strip()

    # Base query: only show available books
    query = Book.query.filter_by(is_available=True)

    # Keyword search across title, author, and description
    if q:
        search_pattern = f"%{q}%"
        query = query.filter(
            (Book.title.ilike(search_pattern)) |
            (Book.author.ilike(search_pattern)) |
            (Book.isbn.ilike(search_pattern))
        )

    if subject:
        query = query.filter(Book.subject.ilike(f"%{subject}%"))

    if department:
        query = query.filter(Book.department == department)

    if semester:
        query = query.filter(Book.semester == semester)

    if condition:
        query = query.filter(Book.condition == condition)

    if listing_type:
        if listing_type == 'Sell':
            query = query.filter(Book.listing_type.in_(['Sell', 'Both']))
        elif listing_type == 'Exchange':
            query = query.filter(Book.listing_type.in_(['Exchange', 'Both']))
        else:
            query = query.filter(Book.listing_type == listing_type)

    if min_price is not None:
        query = query.filter(Book.price >= min_price)

    if max_price is not None:
        query = query.filter(Book.price <= max_price)

    # Sorting
    if sort_by == 'price_asc':
        query = query.order_by(Book.price.asc(), Book.created_at.desc())
    elif sort_by == 'price_desc':
        query = query.order_by(Book.price.desc(), Book.created_at.desc())
    else:  # 'newest' default
        query = query.order_by(Book.created_at.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    books = pagination.items

    return render_template(
        'books/browse.html',
        books=books,
        pagination=pagination,
        q=q,
        subject=subject,
        department=department,
        semester=semester,
        condition=condition,
        listing_type=listing_type,
        min_price=min_price,
        max_price=max_price,
        sort_by=sort_by,
        departments=DEPARTMENT_CHOICES,
        semesters=SEMESTER_CHOICES,
        conditions=CONDITION_CHOICES,
        listing_types=LISTING_TYPE_CHOICES
    )


@books_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create a new book listing."""
    form = BookListingForm()
    if form.validate_on_submit():
        image_url = None
        if form.cover_image.data:
            image_url = save_book_image(form.cover_image.data)

        # Price defaults to 0 for Exchange-only listings
        price_val = form.price.data if form.listing_type.data in ['Sell', 'Both'] and form.price.data else 0.00

        book = Book(
            title=form.title.data.strip(),
            author=form.author.data.strip(),
            isbn=form.isbn.data.strip() if form.isbn.data else None,
            subject=form.subject.data.strip(),
            department=form.department.data,
            semester=form.semester.data,
            edition=form.edition.data.strip() if form.edition.data else None,
            description=form.description.data.strip(),
            condition=form.condition.data,
            price=price_val,
            listing_type=form.listing_type.data,
            cover_image_url=image_url,
            is_available=True,
            is_reserved=False,
            user_id=current_user.id
        )
        db.session.add(book)
        db.session.commit()

        ActivityLog.log(current_user.id, 'LISTED_BOOK', f'Listed "{book.title}" for {book.listing_type}.')
        flash(f'"{book.title}" was listed successfully!', 'success')
        return redirect(url_for('books.detail', book_id=book.id))

    return render_template('books/add.html', form=form)


@books_bp.route('/<int:book_id>')
def detail(book_id):
    """View details of a specific book."""
    book = Book.query.get_or_404(book_id)

    # Wishlist status for current user
    is_in_wishlist = False
    if current_user.is_authenticated:
        is_in_wishlist = current_user.has_in_wishlist(book.id)

    # Forms for purchase and exchange
    purchase_form = PurchaseRequestForm()
    exchange_form = ExchangeRequestForm()
    report_form = ReportBookForm()

    # Populate exchange book choices with current user's available books
    user_available_books = []
    if current_user.is_authenticated and current_user.id != book.user_id:
        user_books = Book.query.filter_by(
            user_id=current_user.id,
            is_available=True,
            is_reserved=False
        ).all()
        user_available_books = user_books
        exchange_form.offered_book_id.choices = [(b.id, f"{b.title} ({b.condition})") for b in user_books]
        if not user_books:
            exchange_form.offered_book_id.choices = [(0, 'No available books in your listings')]

    # Related books from the same department
    related_books = Book.query.filter(
        Book.department == book.department,
        Book.id != book.id,
        Book.is_available == True
    ).limit(3).all()

    return render_template(
        'books/detail.html',
        book=book,
        is_in_wishlist=is_in_wishlist,
        purchase_form=purchase_form,
        exchange_form=exchange_form,
        report_form=report_form,
        user_available_books=user_available_books,
        related_books=related_books
    )


@books_bp.route('/<int:book_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(book_id):
    """Edit an existing book listing."""
    book = Book.query.get_or_404(book_id)

    # Ownership check
    if book.user_id != current_user.id and not current_user.is_admin:
        flash("You are not authorized to edit this listing.", "danger")
        return redirect(url_for('books.detail', book_id=book.id))

    form = BookListingForm(obj=book)

    if form.validate_on_submit():
        book.title = form.title.data.strip()
        book.author = form.author.data.strip()
        book.isbn = form.isbn.data.strip() if form.isbn.data else None
        book.subject = form.subject.data.strip()
        book.department = form.department.data
        book.semester = form.semester.data
        book.edition = form.edition.data.strip() if form.edition.data else None
        book.condition = form.condition.data
        book.listing_type = form.listing_type.data
        book.price = form.price.data if form.listing_type.data in ['Sell', 'Both'] and form.price.data else 0.00
        book.description = form.description.data.strip()

        # Update cover image if new one uploaded
        if form.cover_image.data:
            new_image_url = save_book_image(form.cover_image.data)
            if new_image_url:
                book.cover_image_url = new_image_url

        db.session.commit()
        ActivityLog.log(current_user.id, 'EDITED_BOOK', f'Updated listing for "{book.title}".')
        flash(f'Listing "{book.title}" updated successfully.', 'success')
        return redirect(url_for('books.detail', book_id=book.id))

    return render_template('books/edit.html', form=form, book=book)


@books_bp.route('/<int:book_id>/delete', methods=['POST'])
@login_required
def delete(book_id):
    """Delete a book listing."""
    book = Book.query.get_or_404(book_id)

    # Ownership check
    if book.user_id != current_user.id and not current_user.is_admin:
        flash("You are not authorized to delete this listing.", "danger")
        return redirect(url_for('books.detail', book_id=book.id))

    book_title = book.title
    db.session.delete(book)
    db.session.commit()

    ActivityLog.log(current_user.id, 'DELETED_BOOK', f'Deleted book listing "{book_title}".')
    flash(f'Listing "{book_title}" has been deleted.', 'info')

    if current_user.is_admin and request.referrer and '/admin' in request.referrer:
        return redirect(url_for('admin.books'))
    return redirect(url_for('dashboard.my_listings'))


@books_bp.route('/<int:book_id>/toggle-status', methods=['POST'])
@login_required
def toggle_status(book_id):
    """Toggle book availability (available / unavailable)."""
    book = Book.query.get_or_404(book_id)

    if book.user_id != current_user.id and not current_user.is_admin:
        flash("You are not authorized to modify this listing.", "danger")
        return redirect(url_for('books.detail', book_id=book.id))

    book.is_available = not book.is_available
    if not book.is_available:
        book.is_reserved = False

    db.session.commit()
    new_status = "Available" if book.is_available else "Unavailable"
    ActivityLog.log(current_user.id, 'STATUS_CHANGED', f'Marked "{book.title}" as {new_status}.')
    flash(f'"{book.title}" is now marked as {new_status}.', 'success')

    return redirect(request.referrer or url_for('dashboard.my_listings'))


@books_bp.route('/<int:book_id>/report', methods=['POST'])
@login_required
def report(book_id):
    """Submit a report against a book listing."""
    book = Book.query.get_or_404(book_id)

    if book.user_id == current_user.id:
        flash("You cannot report your own listing.", "warning")
        return redirect(url_for('books.detail', book_id=book.id))

    form = ReportBookForm()
    if form.validate_on_submit():
        rep = Report(
            book_id=book.id,
            reporter_id=current_user.id,
            reason=form.reason.data,
            details=form.details.data.strip(),
            status='Pending'
        )
        db.session.add(rep)
        db.session.commit()

        flash("Your report has been submitted to the moderation team for review. Thank you for keeping BookLoop safe.", "info")
    else:
        flash("Failed to submit report. Please check the details provided.", "danger")

    return redirect(url_for('books.detail', book_id=book.id))
