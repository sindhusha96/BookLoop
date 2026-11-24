import pytest
from app import db
from app.models import Book, Report, ActivityLog


def test_create_book_listing(auth_client, app, test_student):
    """Test listing a new academic book."""
    response = auth_client.post('/books/create', data={
        'title': 'Artificial Intelligence: A Modern Approach',
        'author': 'Stuart Russell, Peter Norvig',
        'isbn': '978-0136042594',
        'subject': 'Artificial Intelligence',
        'department': 'Computer Science & IT',
        'semester': '5th Semester',
        'edition': '4th Edition',
        'condition': 'Like New',
        'listing_type': 'Both',
        'price': '42.00',
        'description': 'The standard textbook in artificial intelligence. Pristine condition with no markings.'
    }, follow_redirects=True)

    assert response.status_code == 200
    with app.app_context():
        book = Book.query.filter_by(title='Artificial Intelligence: A Modern Approach').first()
        assert book is not None
        assert book.author == 'Stuart Russell, Peter Norvig'
        assert book.price == 42.00
        assert book.user_id == test_student.id
        assert book.is_available is True
        assert book.is_reserved is False


def test_edit_book_by_owner(auth_client, app, sample_book):
    """Test book listing update by the owner."""
    response = auth_client.post(f'/books/{sample_book.id}/edit', data={
        'title': 'Database Systems Design - Updated Title',
        'author': sample_book.author,
        'isbn': sample_book.isbn,
        'subject': sample_book.subject,
        'department': sample_book.department,
        'semester': sample_book.semester,
        'edition': '7th Edition Revised',
        'condition': 'Like New',
        'listing_type': 'Sell',
        'price': '29.99',
        'description': 'Updated detailed book description notes.'
    }, follow_redirects=True)

    assert response.status_code == 200
    with app.app_context():
        b = db.session.get(Book, sample_book.id)
        assert b.title == 'Database Systems Design - Updated Title'
        assert float(b.price) == 29.99
        assert b.condition == 'Like New'


def test_edit_book_by_unauthorized_user(second_client, sample_book):
    """Test that a non-owner cannot edit another student's listing."""
    response = second_client.post(f'/books/{sample_book.id}/edit', data={
        'title': 'Hacked Title',
        'author': 'Hacker',
        'subject': sample_book.subject,
        'department': sample_book.department,
        'semester': sample_book.semester,
        'condition': 'Used',
        'listing_type': 'Sell',
        'price': '5.00',
        'description': 'Attempted unauthorized change.'
    }, follow_redirects=True)

    assert b"You are not authorized to edit this listing" in response.data
    assert sample_book.title == "Database Systems Design"


def test_delete_book_by_owner(auth_client, app, sample_book):
    """Test deleting book listing by owner."""
    response = auth_client.post(f'/books/{sample_book.id}/delete', follow_redirects=True)
    assert response.status_code == 200

    with app.app_context():
        b = Book.query.get(sample_book.id)
        assert b is None


def test_delete_book_by_unauthorized_user(second_client, app, sample_book):
    """Test that non-owner cannot delete another student's listing."""
    response = second_client.post(f'/books/{sample_book.id}/delete', follow_redirects=True)
    assert b"You are not authorized to delete this listing" in response.data

    with app.app_context():
        b = Book.query.get(sample_book.id)
        assert b is not None


def test_delete_book_by_admin(admin_client, app, sample_book):
    """Test that an administrator can delete any inappropriate listing."""
    response = admin_client.post(f'/books/{sample_book.id}/delete', follow_redirects=True)
    assert response.status_code == 200

    with app.app_context():
        b = Book.query.get(sample_book.id)
        assert b is None


def test_toggle_book_availability(auth_client, app, sample_book):
    """Test toggling listing availability between available and unavailable."""
    assert sample_book.is_available is True

    # Toggle to unavailable
    res1 = auth_client.post(f'/books/{sample_book.id}/toggle-status', follow_redirects=True)
    assert res1.status_code == 200
    with app.app_context():
        b = Book.query.get(sample_book.id)
        assert b.is_available is False

    # Toggle back to available
    res2 = auth_client.post(f'/books/{sample_book.id}/toggle-status', follow_redirects=True)
    assert res2.status_code == 200
    with app.app_context():
        b = Book.query.get(sample_book.id)
        assert b.is_available is True


def test_report_book_listing(second_client, app, sample_book, second_student):
    """Test reporting a book listing for moderation."""
    response = second_client.post(f'/books/{sample_book.id}/report', data={
        'reason': 'Spam or Scam',
        'details': 'This listing appears to have invalid contact or misleading details.'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"report has been submitted to the moderation team" in response.data

    with app.app_context():
        rep = Report.query.filter_by(book_id=sample_book.id, reporter_id=second_student.id).first()
        assert rep is not None
        assert rep.reason == 'Spam or Scam'
        assert rep.status == 'Pending'


def test_report_own_book_prevented(auth_client, sample_book):
    """Test that a user cannot report their own listing."""
    response = auth_client.post(f'/books/{sample_book.id}/report', data={
        'reason': 'Other',
        'details': 'Self report test'
    }, follow_redirects=True)

    assert b"You cannot report your own listing" in response.data
