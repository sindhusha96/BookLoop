import pytest
from werkzeug.datastructures import MultiDict
from app.forms import RegistrationForm, BookListingForm


def test_registration_form_invalid_username_characters(app):
    """Test that usernames with special characters or spaces are rejected."""
    with app.test_request_context():
        form = RegistrationForm(MultiDict({
            'username': 'john doe!@#',
            'email': 'valid@college.edu',
            'full_name': 'John Doe',
            'college_name': 'College',
            'password': 'Password123!',
            'confirm_password': 'Password123!'
        }))
        assert not form.validate()
        assert 'username' in form.errors


def test_registration_form_short_password(app):
    """Test that passwords under 8 characters are rejected."""
    with app.test_request_context():
        form = RegistrationForm(MultiDict({
            'username': 'valid_user',
            'email': 'valid@college.edu',
            'full_name': 'Valid User',
            'college_name': 'College',
            'password': 'short',
            'confirm_password': 'short'
        }))
        assert not form.validate()
        assert 'password' in form.errors


def test_registration_form_password_mismatch(app):
    """Test that mismatched confirmation password is rejected."""
    with app.test_request_context():
        form = RegistrationForm(MultiDict({
            'username': 'valid_user',
            'email': 'valid@college.edu',
            'full_name': 'Valid User',
            'college_name': 'College',
            'password': 'Password123!',
            'confirm_password': 'DifferentPassword456!'
        }))
        assert not form.validate()
        assert 'confirm_password' in form.errors


def test_book_form_negative_price(app):
    """Test that negative prices are rejected for for-sale books."""
    with app.test_request_context():
        form = BookListingForm(MultiDict({
            'title': 'Test Book',
            'author': 'Test Author',
            'subject': 'Test Subject',
            'department': 'Computer Science & IT',
            'semester': '1st Semester',
            'condition': 'Good',
            'listing_type': 'Sell',
            'price': '-15.00',
            'description': 'Valid long description for testing purposes.'
        }))
        assert not form.validate()
        assert 'price' in form.errors
