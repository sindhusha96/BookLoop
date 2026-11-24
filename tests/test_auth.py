import pytest
from app import db
from app.models import User, ActivityLog


def test_password_hashing(app):
    """Ensure passwords are never stored in plain text and are properly hashed."""
    u = User(username="test_hash", email="hash@college.edu", full_name="Hash User", college_name="Tech")
    u.set_password("MySecureSecret123!")
    
    assert u.password_hash != "MySecureSecret123!"
    assert u.check_password("MySecureSecret123!")
    assert not u.check_password("WrongPassword")


def test_student_registration_success(client, app):
    """Test successful student account registration."""
    response = client.post('/auth/register', data={
        'username': 'new_student',
        'email': 'new_student@university.edu',
        'full_name': 'New Student',
        'college_name': 'Engineering University',
        'phone': '+1 (555) 777-8888',
        'password': 'StrongPassword123!',
        'confirm_password': 'StrongPassword123!'
    }, follow_redirects=True)

    assert response.status_code == 200
    with app.app_context():
        user = User.query.filter_by(username='new_student').first()
        assert user is not None
        assert user.role == 'student'
        assert user.email == 'new_student@university.edu'
        assert user.is_active is True


def test_registration_duplicate_email(client, test_student):
    """Test that registering with an existing email is prevented."""
    response = client.post('/auth/register', data={
        'username': 'different_username',
        'email': test_student.email,  # duplicate
        'full_name': 'Another Person',
        'college_name': 'Some College',
        'password': 'StrongPassword123!',
        'confirm_password': 'StrongPassword123!'
    }, follow_redirects=True)

    assert b"An account with that email already exists" in response.data


def test_registration_duplicate_username(client, test_student):
    """Test that registering with an existing username is prevented."""
    response = client.post('/auth/register', data={
        'username': test_student.username,  # duplicate
        'email': 'unique_email@test.edu',
        'full_name': 'Another Person',
        'college_name': 'Some College',
        'password': 'StrongPassword123!',
        'confirm_password': 'StrongPassword123!'
    }, follow_redirects=True)

    assert b"That username is already taken" in response.data


def test_login_and_logout(client, test_student):
    """Test user login with both email and username, and logout."""
    # Login via email
    res_email = client.post('/auth/login', data={
        'email': test_student.email,
        'password': 'StudentPass123!'
    }, follow_redirects=True)
    assert res_email.status_code == 200
    assert b"Welcome back" in res_email.data

    # Logout
    res_logout = client.get('/auth/logout', follow_redirects=True)
    assert res_logout.status_code == 200
    assert b"successfully logged out" in res_logout.data

    # Login via username
    res_uname = client.post('/auth/login', data={
        'email': test_student.username,
        'password': 'StudentPass123!'
    }, follow_redirects=True)
    assert res_uname.status_code == 200
    assert b"Welcome back" in res_uname.data

    # Log out to leave client in clean state
    client.get('/auth/logout')


def test_login_invalid_credentials(client, test_student):
    """Test login failure with wrong password."""
    client.get('/auth/logout')
    response = client.post('/auth/login', data={
        'email': test_student.email,
        'password': 'IncorrectPassword'
    }, follow_redirects=True)

    assert b"Invalid email/username or password" in response.data


def test_login_deactivated_account(app):
    """Test that deactivated accounts cannot log in."""
    fresh_client = app.test_client()
    with app.app_context():
        user = User(
            username="deactivated_student",
            email="deactivated@college.edu",
            full_name="Deactivated Student",
            college_name="College",
            role="student",
            is_active=False
        )
        user.set_password("StudentPass123!")
        db.session.add(user)
        db.session.commit()

    response = fresh_client.post('/auth/login', data={
        'email': 'deactivated@college.edu',
        'password': 'StudentPass123!'
    }, follow_redirects=True)

    assert b"Your account has been deactivated" in response.data


def test_profile_update(auth_client, app, test_student):
    """Test student profile editing."""
    response = auth_client.post('/auth/profile', data={
        'full_name': 'John Updated Doe',
        'college_name': 'Updated Institute',
        'phone': '+1 (555) 999-0000',
        'bio': 'Updated bio content'
    }, follow_redirects=True)

    assert response.status_code == 200
    with app.app_context():
        user = User.query.get(test_student.id)
        assert user.full_name == 'John Updated Doe'
        assert user.college_name == 'Updated Institute'
        assert user.bio == 'Updated bio content'


def test_change_password_success(auth_client, app, test_student):
    """Test changing password with valid current password."""
    response = auth_client.post('/auth/change-password', data={
        'current_password': 'StudentPass123!',
        'new_password': 'NewPassword456!',
        'confirm_new_password': 'NewPassword456!'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"password has been changed successfully" in response.data

    with app.app_context():
        user = User.query.get(test_student.id)
        assert user.check_password('NewPassword456!')
        assert not user.check_password('StudentPass123!')


def test_change_password_wrong_current(auth_client, test_student):
    """Test changing password with incorrect current password."""
    response = auth_client.post('/auth/change-password', data={
        'current_password': 'WrongPassword123!',
        'new_password': 'NewPassword456!',
        'confirm_new_password': 'NewPassword456!'
    }, follow_redirects=True)

    assert b"Current password is incorrect" in response.data
