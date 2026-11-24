import pytest
from app import db
from app.models import User, Book, Report


def test_student_forbidden_from_admin_dashboard(auth_client):
    """Test that regular students receive 403 Forbidden when accessing admin pages."""
    response = auth_client.get('/admin/')
    assert response.status_code == 403


def test_guest_redirected_to_login_from_admin(client):
    """Test that unauthenticated guests are redirected to login."""
    response = client.get('/admin/')
    assert response.status_code == 302
    assert '/auth/login' in response.headers['Location']


def test_admin_access_dashboard_success(admin_client):
    """Test that users with admin role can access the admin dashboard."""
    response = admin_client.get('/admin/')
    assert response.status_code == 200
    assert b"Administrator Control Panel" in response.data


def test_admin_toggle_user_status(admin_client, app, test_student):
    """Test admin deactivating and activating a student account."""
    assert test_student.is_active is True

    # Deactivate
    res1 = admin_client.post(f'/admin/users/{test_student.id}/toggle-status', follow_redirects=True)
    assert res1.status_code == 200
    with app.app_context():
        u = User.query.get(test_student.id)
        assert u.is_active is False

    # Reactivate
    res2 = admin_client.post(f'/admin/users/{test_student.id}/toggle-status', follow_redirects=True)
    assert res2.status_code == 200
    with app.app_context():
        u = User.query.get(test_student.id)
        assert u.is_active is True


def test_admin_self_deactivation_prevented(admin_client, admin_user):
    """Test that an admin cannot accidentally deactivate their own account."""
    response = admin_client.post(f'/admin/users/{admin_user.id}/toggle-status', follow_redirects=True)
    assert b"You cannot deactivate your own administrative account" in response.data
    assert admin_user.is_active is True


def test_admin_handle_report_deactivate_book(admin_client, app, sample_book, test_student):
    """Test admin resolving a report and deactivating the violating book."""
    with app.app_context():
        rep = Report(
            book_id=sample_book.id,
            reporter_id=test_student.id,
            reason='Inappropriate Content',
            details='Test inappropriate listing',
            status='Pending'
        )
        db.session.add(rep)
        db.session.commit()
        rep_id = rep.id

    response = admin_client.post(f'/admin/reports/{rep_id}/deactivate_book', follow_redirects=True)
    assert response.status_code == 200

    with app.app_context():
        updated_rep = Report.query.get(rep_id)
        assert updated_rep.status == 'Resolved'
        book = Book.query.get(sample_book.id)
        assert book.is_available is False
