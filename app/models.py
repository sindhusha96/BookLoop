from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db


class User(UserMixin, db.Model):
    """User account model for both Students and Admins."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='student')  # 'student', 'admin'
    full_name = db.Column(db.String(100), nullable=False)
    college_name = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(20), nullable=True)  # Private until transaction/exchange accepted
    bio = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    books = db.relationship('Book', back_populates='owner', cascade='all, delete-orphan', lazy='dynamic')
    requests_sent = db.relationship('BookRequest', foreign_keys='BookRequest.requester_id', back_populates='requester', cascade='all, delete-orphan', lazy='dynamic')
    wishlist_items = db.relationship('Wishlist', back_populates='user', cascade='all, delete-orphan', lazy='dynamic')
    activity_logs = db.relationship('ActivityLog', back_populates='user', cascade='all, delete-orphan', lazy='dynamic')
    reports_filed = db.relationship('Report', foreign_keys='Report.reporter_id', back_populates='reporter', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role == 'admin'

    def has_in_wishlist(self, book_id):
        return self.wishlist_items.filter_by(book_id=book_id).first() is not None

    def __repr__(self):
        return f'<User {self.username} ({self.role})>'


class Book(db.Model):
    """Academic book listing model."""
    __tablename__ = 'books'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    author = db.Column(db.String(150), nullable=False, index=True)
    isbn = db.Column(db.String(32), nullable=True, index=True)
    subject = db.Column(db.String(100), nullable=False, index=True)
    department = db.Column(db.String(100), nullable=False, index=True)  # Engineering, Computer Science, etc.
    semester = db.Column(db.String(50), nullable=False, index=True)    # 1st, 2nd, ..., 8th, General
    edition = db.Column(db.String(50), nullable=True)
    description = db.Column(db.Text, nullable=False)
    condition = db.Column(db.String(50), nullable=False, index=True)    # Like New, Good, Acceptable, Used
    price = db.Column(db.Numeric(10, 2), nullable=False, default=0.00, index=True)
    listing_type = db.Column(db.String(20), nullable=False, index=True) # 'Sell', 'Exchange', 'Both'
    cover_image_url = db.Column(db.String(500), nullable=True)
    is_available = db.Column(db.Boolean, default=True, nullable=False, index=True)
    is_reserved = db.Column(db.Boolean, default=False, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    owner = db.relationship('User', back_populates='books')
    requests = db.relationship('BookRequest', foreign_keys='BookRequest.book_id', back_populates='book', cascade='all, delete-orphan', lazy='dynamic')
    offered_in_requests = db.relationship('BookRequest', foreign_keys='BookRequest.offered_book_id', back_populates='offered_book', lazy='dynamic')
    wishlisted_by = db.relationship('Wishlist', back_populates='book', cascade='all, delete-orphan', lazy='dynamic')
    reports = db.relationship('Report', back_populates='book', cascade='all, delete-orphan', lazy='dynamic')

    @property
    def formatted_price(self):
        if self.listing_type == 'Exchange':
            return "Exchange Only"
        if self.price == 0:
            return "Free"
        return f"${self.price:,.2f}"

    @property
    def display_status(self):
        if not self.is_available:
            return "Unavailable"
        if self.is_reserved:
            return "Reserved"
        return "Available"

    def __repr__(self):
        return f'<Book {self.title} by {self.author}>'


class BookRequest(db.Model):
    """Purchase or Exchange requests between students."""
    __tablename__ = 'book_requests'

    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False, index=True)
    requester_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    request_type = db.Column(db.String(20), nullable=False)  # 'purchase', 'exchange'
    offered_book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=True, index=True)
    status = db.Column(db.String(20), default='Pending', nullable=False, index=True)  # Pending, Accepted, Rejected, Cancelled, Completed
    message = db.Column(db.Text, nullable=True)
    response_note = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    book = db.relationship('Book', foreign_keys=[book_id], back_populates='requests')
    requester = db.relationship('User', foreign_keys=[requester_id], back_populates='requests_sent')
    offered_book = db.relationship('Book', foreign_keys=[offered_book_id], back_populates='offered_in_requests')

    def __repr__(self):
        return f'<BookRequest #{self.id}: {self.request_type} - {self.status}>'


class Wishlist(db.Model):
    """User wishlist / saved books."""
    __tablename__ = 'wishlists'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Unique constraint prevents duplicate saves
    __table_args__ = (
        db.UniqueConstraint('user_id', 'book_id', name='uq_user_book_wishlist'),
    )

    user = db.relationship('User', back_populates='wishlist_items')
    book = db.relationship('Book', back_populates='wishlisted_by')

    def __repr__(self):
        return f'<Wishlist User:{self.user_id} Book:{self.book_id}>'


class Report(db.Model):
    """Reports for inappropriate or scam listings."""
    __tablename__ = 'reports'

    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False, index=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    reason = db.Column(db.String(100), nullable=False)  # Spam, Inappropriate, Duplicate, Fake, etc.
    details = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='Pending', nullable=False, index=True)  # Pending, Resolved, Dismissed
    admin_notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    book = db.relationship('Book', back_populates='reports')
    reporter = db.relationship('User', back_populates='reports_filed')

    def __repr__(self):
        return f'<Report #{self.id} on Book:{self.book_id} Status:{self.status}>'


class ActivityLog(db.Model):
    """User platform activity timeline."""
    __tablename__ = 'activity_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    action = db.Column(db.String(100), nullable=False)  # LIST_BOOK, EDIT_BOOK, DELETE_BOOK, REQUEST_BOOK, ACCEPT_REQUEST, etc.
    description = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    user = db.relationship('User', back_populates='activity_logs')

    @classmethod
    def log(cls, user_id, action, description):
        """Helper method to record an activity."""
        try:
            log_entry = cls(user_id=user_id, action=action, description=description)
            db.session.add(log_entry)
            db.session.commit()
            return log_entry
        except Exception:
            db.session.rollback()
            return None

    def __repr__(self):
        return f'<ActivityLog User:{self.user_id} {self.action}>'
