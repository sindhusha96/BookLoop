import pytest
from app import db
from app.models import Book


@pytest.fixture
def multiple_books(app, test_student):
    """Seed multiple books with varying subjects, departments, and prices."""
    b1 = Book(
        title="Microeconomics Principles",
        author="N. Gregory Mankiw",
        subject="Economics",
        department="Business & Management",
        semester="1st Semester",
        condition="Good",
        price=20.00,
        listing_type="Sell",
        is_available=True,
        description="Standard freshman economics textbook.",
        user_id=test_student.id
    )
    b2 = Book(
        title="Organic Chemistry",
        author="David Klein",
        subject="Chemistry",
        department="Natural Sciences & Math",
        semester="3rd Semester",
        condition="Like New",
        price=50.00,
        listing_type="Exchange",
        is_available=True,
        description="Comprehensive organic chemistry guide.",
        user_id=test_student.id
    )
    b3 = Book(
        title="Data Structures and Algorithms in Python",
        author="Michael T. Goodrich",
        subject="Computer Science",
        department="Computer Science & IT",
        semester="2nd Semester",
        condition="Acceptable",
        price=15.00,
        listing_type="Both",
        is_available=True,
        description="Clean copy with minor highlighting.",
        user_id=test_student.id
    )
    b4 = Book(
        title="Sold Old Book",
        author="Unknown Author",
        subject="General",
        department="General / Reference",
        semester="1st Semester",
        condition="Used",
        price=10.00,
        listing_type="Sell",
        is_available=False,  # Unavailable!
        description="This book has been sold.",
        user_id=test_student.id
    )
    db.session.add_all([b1, b2, b3, b4])
    db.session.commit()
    return [b1, b2, b3, b4]


def test_search_by_keyword(client, multiple_books):
    """Test searching books by title or author keyword."""
    # Search title
    res_title = client.get('/books/browse?q=Microeconomics')
    assert b"Microeconomics Principles" in res_title.data
    assert b"Organic Chemistry" not in res_title.data

    # Search author
    res_author = client.get('/books/browse?q=Klein')
    assert b"Organic Chemistry" in res_author.data
    assert b"Microeconomics Principles" not in res_author.data


def test_filter_by_department(client, multiple_books):
    """Test filtering books by department."""
    response = client.get('/books/browse?department=Business+%26+Management')
    assert b"Microeconomics Principles" in response.data
    assert b"Organic Chemistry" not in response.data
    assert b"Data Structures" not in response.data


def test_filter_by_condition(client, multiple_books):
    """Test filtering by physical condition."""
    response = client.get('/books/browse?condition=Like+New')
    assert b"Organic Chemistry" in response.data
    assert b"Microeconomics Principles" not in response.data


def test_filter_by_listing_type(client, multiple_books):
    """Test filtering by Sell or Exchange mode."""
    # Exchange filter should match 'Exchange' and 'Both'
    res_exchange = client.get('/books/browse?listing_type=Exchange')
    assert b"Organic Chemistry" in res_exchange.data
    assert b"Data Structures and Algorithms in Python" in res_exchange.data
    assert b"Microeconomics Principles" not in res_exchange.data


def test_filter_by_price_range(client, multiple_books):
    """Test filtering by min and max price."""
    # Price between $18 and $30 (should only match Mankiw at $20)
    response = client.get('/books/browse?min_price=18&max_price=30')
    assert b"Microeconomics Principles" in response.data
    assert b"Data Structures and Algorithms in Python" not in response.data
    assert b"Organic Chemistry" not in response.data


def test_sort_by_price(client, multiple_books):
    """Test price sorting order."""
    # Low to High
    res_asc = client.get('/books/browse?sort_by=price_asc')
    assert res_asc.status_code == 200
    content = res_asc.data.decode('utf-8')
    pos_cheap = content.find("Data Structures and Algorithms in Python")  # $15
    pos_expensive = content.find("Organic Chemistry")  # $50
    assert pos_cheap < pos_expensive


def test_unavailable_books_excluded(client, multiple_books):
    """Test that unavailable books do not appear in catalog."""
    response = client.get('/books/browse')
    assert b"Sold Old Book" not in response.data
