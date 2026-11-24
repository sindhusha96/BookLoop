import pytest
from app import db
from app.models import Wishlist


def test_add_to_wishlist(second_client, app, sample_book, second_student):
    """Test adding a book to the student's wishlist."""
    response = second_client.post(f'/dashboard/wishlist/toggle/{sample_book.id}', follow_redirects=True)
    assert response.status_code == 200
    assert b"added to your wishlist" in response.data

    with app.app_context():
        item = Wishlist.query.filter_by(user_id=second_student.id, book_id=sample_book.id).first()
        assert item is not None


def test_remove_from_wishlist_via_toggle(second_client, app, sample_book, second_student):
    """Test that toggling an already wishlisted book removes it."""
    with app.app_context():
        db.session.add(Wishlist(user_id=second_student.id, book_id=sample_book.id))
        db.session.commit()

    response = second_client.post(f'/dashboard/wishlist/toggle/{sample_book.id}', follow_redirects=True)
    assert response.status_code == 200
    assert b"removed from your wishlist" in response.data

    with app.app_context():
        item = Wishlist.query.filter_by(user_id=second_student.id, book_id=sample_book.id).first()
        assert item is None


def test_wishlist_ajax_toggle(second_client, app, sample_book):
    """Test AJAX toggle endpoint returning JSON."""
    response = second_client.post(
        f'/dashboard/wishlist/toggle/{sample_book.id}',
        headers={'X-Requested-With': 'XMLHttpRequest'}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert data['in_wishlist'] is True
