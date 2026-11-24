import pytest
from app import create_app, db
from app.models import User, Book, BookRequest, Wishlist, Report, ActivityLog


@pytest.fixture
def app():
    """Create and configure a clean Flask application instance for each test."""
    app = create_app('testing')

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """A test CLI runner for the app."""
    return app.test_cli_runner()


@pytest.fixture
def test_student(app):
    """Create a sample student user."""
    user = User(
        username="student_john",
        email="john@college.edu",
        full_name="John Doe",
        college_name="State University",
        phone="+1 (555) 111-2222",
        role="student"
    )
    user.set_password("StudentPass123!")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def second_student(app):
    """Create a second student user for peer interactions."""
    user = User(
        username="student_sarah",
        email="sarah@college.edu",
        full_name="Sarah Smith",
        college_name="Engineering Tech",
        phone="+1 (555) 333-4444",
        role="student"
    )
    user.set_password("StudentPass123!")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def admin_user(app):
    """Create a sample administrator user."""
    admin = User(
        username="admin_boss",
        email="boss@bookloop.edu",
        full_name="System Admin",
        college_name="Campus HQ",
        role="admin"
    )
    admin.set_password("AdminPass123!")
    db.session.add(admin)
    db.session.commit()
    return admin


@pytest.fixture
def sample_book(app, test_student):
    """Create a sample book listed by test_student."""
    book = Book(
        title="Database Systems Design",
        author="Abraham Silberschatz",
        isbn="978-0078022159",
        subject="Database Management Systems",
        department="Computer Science & IT",
        semester="4th Semester",
        edition="6th Edition",
        description="Comprehensive database concepts textbook. Very good condition with minimal notes.",
        condition="Good",
        price=35.00,
        listing_type="Both",
        is_available=True,
        is_reserved=False,
        user_id=test_student.id
    )
    db.session.add(book)
    db.session.commit()
    return book


@pytest.fixture
def auth_client(client, test_student):
    """Test client logged in as test_student."""
    with client.session_transaction() as sess:
        sess['_user_id'] = str(test_student.id)
        sess['_fresh'] = True
    return client


@pytest.fixture
def second_client(client, second_student):
    """Test client logged in as second_student."""
    with client.session_transaction() as sess:
        sess['_user_id'] = str(second_student.id)
        sess['_fresh'] = True
    return client


@pytest.fixture
def admin_client(client, admin_user):
    """Test client logged in as admin_user."""
    with client.session_transaction() as sess:
        sess['_user_id'] = str(admin_user.id)
        sess['_fresh'] = True
    return client
