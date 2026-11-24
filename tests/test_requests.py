import pytest
from app import db
from app.models import Book, BookRequest


@pytest.fixture
def offered_book(app, second_student):
    """Book listed by second_student to offer in exchanges."""
    book = Book(
        title="Calculus Vol 1",
        author="OpenStax",
        subject="Calculus",
        department="Natural Sciences & Math",
        semester="1st Semester",
        condition="Good",
        price=15.00,
        listing_type="Both",
        is_available=True,
        is_reserved=False,
        description="Freshman calculus math textbook.",
        user_id=second_student.id
    )
    db.session.add(book)
    db.session.commit()
    return book


def test_create_purchase_request(second_client, app, sample_book, second_student):
    """Test sending a purchase request for an available book."""
    response = second_client.post(f'/requests/purchase/{sample_book.id}', data={
        'message': 'I would like to purchase this book for class next week.'
    }, follow_redirects=True)

    assert response.status_code == 200
    with app.app_context():
        req = BookRequest.query.filter_by(book_id=sample_book.id, requester_id=second_student.id).first()
        assert req is not None
        assert req.request_type == 'purchase'
        assert req.status == 'Pending'
        assert req.message == 'I would like to purchase this book for class next week.'


def test_request_own_book_prevented(auth_client, sample_book):
    """Test that a student cannot send a request for their own book."""
    response = auth_client.post(f'/requests/purchase/{sample_book.id}', data={
        'message': 'Buying my own book'
    }, follow_redirects=True)

    assert b"You cannot send a purchase request for your own book listing" in response.data


def test_prevent_duplicate_active_requests(second_client, app, sample_book, second_student):
    """Test that multiple active requests for the same book by the same student are prevented."""
    # First request
    second_client.post(f'/requests/purchase/{sample_book.id}', data={'message': 'First request'})

    # Second request
    response = second_client.post(f'/requests/purchase/{sample_book.id}', data={'message': 'Second request'}, follow_redirects=True)
    assert b"You already have an active request" in response.data

    with app.app_context():
        count = BookRequest.query.filter_by(book_id=sample_book.id, requester_id=second_student.id).count()
        assert count == 1


def test_create_exchange_request(second_client, app, sample_book, offered_book, second_student):
    """Test sending an exchange request with an offered book."""
    response = second_client.post(f'/requests/exchange/{sample_book.id}', data={
        'offered_book_id': offered_book.id,
        'message': 'Would you be open to swapping for my Calculus textbook?'
    }, follow_redirects=True)

    assert response.status_code == 200
    with app.app_context():
        req = BookRequest.query.filter_by(book_id=sample_book.id, requester_id=second_student.id).first()
        assert req is not None
        assert req.request_type == 'exchange'
        assert req.offered_book_id == offered_book.id
        assert req.status == 'Pending'


def test_owner_accept_purchase_request(auth_client, app, sample_book, second_student):
    """Test that owner accepting a purchase request marks the listing as reserved."""
    with app.app_context():
        req = BookRequest(
            book_id=sample_book.id,
            requester_id=second_student.id,
            request_type='purchase',
            status='Pending'
        )
        db.session.add(req)
        db.session.commit()
        req_id = req.id

    response = auth_client.post(f'/requests/{req_id}/accept', follow_redirects=True)
    assert response.status_code == 200
    assert b"You accepted the request" in response.data

    with app.app_context():
        updated_req = BookRequest.query.get(req_id)
        assert updated_req.status == 'Accepted'
        book = Book.query.get(sample_book.id)
        assert book.is_reserved is True


def test_owner_accept_exchange_request_reserves_both_books(auth_client, app, sample_book, offered_book, second_student):
    """Test that accepting an exchange request reserves both the primary and offered book."""
    with app.app_context():
        req = BookRequest(
            book_id=sample_book.id,
            requester_id=second_student.id,
            request_type='exchange',
            offered_book_id=offered_book.id,
            status='Pending'
        )
        db.session.add(req)
        db.session.commit()
        req_id = req.id

    response = auth_client.post(f'/requests/{req_id}/accept', follow_redirects=True)
    assert response.status_code == 200

    with app.app_context():
        b1 = Book.query.get(sample_book.id)
        b2 = Book.query.get(offered_book.id)
        assert b1.is_reserved is True
        assert b2.is_reserved is True


def test_owner_reject_request(auth_client, app, sample_book, second_student):
    """Test book owner rejecting an incoming request."""
    with app.app_context():
        req = BookRequest(book_id=sample_book.id, requester_id=second_student.id, request_type='purchase', status='Pending')
        db.session.add(req)
        db.session.commit()
        req_id = req.id

    response = auth_client.post(f'/requests/{req_id}/reject', follow_redirects=True)
    assert response.status_code == 200
    assert b"request has been rejected" in response.data

    with app.app_context():
        updated_req = BookRequest.query.get(req_id)
        assert updated_req.status == 'Rejected'
        book = Book.query.get(sample_book.id)
        assert book.is_reserved is False


def test_requester_cancel_pending_request(second_client, app, sample_book, second_student):
    """Test requester cancelling their own pending request."""
    with app.app_context():
        req = BookRequest(book_id=sample_book.id, requester_id=second_student.id, request_type='purchase', status='Pending')
        db.session.add(req)
        db.session.commit()
        req_id = req.id

    response = second_client.post(f'/requests/{req_id}/cancel', follow_redirects=True)
    assert response.status_code == 200
    assert b"request has been cancelled" in response.data

    with app.app_context():
        updated_req = BookRequest.query.get(req_id)
        assert updated_req.status == 'Cancelled'


def test_complete_accepted_transaction(auth_client, app, test_student, second_student):
    """Test marking an accepted transaction as completed (marks book as unavailable)."""
    with app.app_context():
        book = Book(
            title="Database Systems Design Unique",
            author="Abraham Silberschatz",
            isbn="978-0078022159",
            subject="Database Management Systems",
            department="Computer Science & IT",
            semester="4th Semester",
            condition="Good",
            price=35.00,
            listing_type="Both",
            is_available=True,
            is_reserved=True,
            description="Comprehensive database concepts textbook.",
            user_id=test_student.id
        )
        db.session.add(book)
        db.session.commit()
        book_id = book.id

        req = BookRequest(
            book_id=book_id,
            requester_id=second_student.id,
            request_type='purchase',
            status='Accepted'
        )
        db.session.add(req)
        db.session.commit()
        req_id = req.id

    response = auth_client.post(f'/requests/{req_id}/complete', follow_redirects=True)
    assert response.status_code == 200
    assert b"marked as completed" in response.data

    with app.app_context():
        updated_req = db.session.get(BookRequest, req_id)
        assert updated_req.status == 'Completed'
        b = db.session.get(Book, book_id)
        assert b.is_available is False
        assert b.is_reserved is False
