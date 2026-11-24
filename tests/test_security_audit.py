import os
import io
import pytest
from app import create_app, db
from app.models import User, Book
from app.utils import save_book_image
from werkzeug.datastructures import FileStorage


def test_production_config_requires_secret_key(monkeypatch):
    """Ensure ProductionConfig refuses to boot without a secure, non-default SECRET_KEY."""
    monkeypatch.delenv('SECRET_KEY', raising=False)
    monkeypatch.setenv('DATABASE_URL', 'postgresql://user:pass@localhost:5432/bookloop')

    with pytest.raises(RuntimeError, match="SECRET_KEY environment variable is missing"):
        create_app('production')

    # Also reject development default key
    monkeypatch.setenv('SECRET_KEY', 'dev-insecure-secret-key-bookloop-change-me')
    with pytest.raises(RuntimeError, match="insecure default"):
        create_app('production')

    # Also reject keys shorter than 16 characters
    monkeypatch.setenv('SECRET_KEY', 'short-key')
    with pytest.raises(RuntimeError, match="at least 16 characters"):
        create_app('production')


def test_production_config_requires_database_url(monkeypatch):
    """Ensure ProductionConfig refuses to boot without DATABASE_URL."""
    monkeypatch.setenv('SECRET_KEY', 'a' * 32)
    monkeypatch.delenv('DATABASE_URL', raising=False)

    with pytest.raises(RuntimeError, match="DATABASE_URL environment variable is mandatory"):
        create_app('production')


def test_production_config_valid(monkeypatch):
    """Ensure ProductionConfig succeeds when valid configuration is supplied."""
    monkeypatch.setenv('SECRET_KEY', 'c' * 32)
    monkeypatch.setenv('DATABASE_URL', 'postgresql://user:pass@localhost:5432/bookloop')

    prod_app = create_app('production')
    assert prod_app.config['DEBUG'] is False
    assert prod_app.config['SESSION_COOKIE_SECURE'] is True
    assert prod_app.config['REMEMBER_COOKIE_SECURE'] is True


def test_image_upload_extension_validation(app):
    """Verify that disallowed file types are rejected by save_book_image."""
    with app.app_context():
        # Disallowed exe file
        bad_file = FileStorage(
            stream=io.BytesIO(b"executable payload"),
            filename="malware.exe",
            content_type="application/octet-stream"
        )
        assert save_book_image(bad_file) is None

        # Disallowed script file
        bad_script = FileStorage(
            stream=io.BytesIO(b"echo 'pwned'"),
            filename="exploit.sh",
            content_type="text/x-sh"
        )
        assert save_book_image(bad_script) is None

        # Allowed image file in testing / dev
        good_img = FileStorage(
            stream=io.BytesIO(b"fake image data"),
            filename="clean_cover.jpg",
            content_type="image/jpeg"
        )
        url = save_book_image(good_img)
        assert url is not None
        assert url.startswith('/static/uploads/')


def test_production_image_no_local_fallback(app, monkeypatch):
    """In production, save_book_image must NOT fall back to ephemeral local disk if Cloudinary is not configured."""
    with app.app_context():
        # Simulate production environment
        app.debug = False
        app.testing = False
        app.config['CLOUDINARY_CLOUD_NAME'] = None

        img = FileStorage(
            stream=io.BytesIO(b"image data"),
            filename="book_cover.jpg",
            content_type="image/jpeg"
        )
        url = save_book_image(img)
        # Must return None instead of writing to ephemeral local disk
        assert url is None


def test_seed_data_disabled_in_production(runner, monkeypatch):
    """Ensure seed-data command refuses to run in production."""
    monkeypatch.setenv('FLASK_ENV', 'production')
    result = runner.invoke(args=['seed-data'])
    assert "disabled in production" in result.output


def test_create_admin_enforces_strong_password_in_production(runner, monkeypatch):
    """Ensure create-admin rejects default or weak passwords in production."""
    monkeypatch.setenv('FLASK_ENV', 'production')

    # Rejects default password
    result1 = runner.invoke(args=[
        'create-admin',
        '--username', 'prod_admin',
        '--email', 'admin_prod@bookloop.edu',
        '--password', 'AdminPassword123!'
    ])
    assert "default or trivial admin passwords ('AdminPassword123!') are strictly prohibited" in result1.output

    # Rejects short password
    result2 = runner.invoke(args=[
        'create-admin',
        '--username', 'prod_admin',
        '--email', 'admin_prod@bookloop.edu',
        '--password', 'shortpass'
    ])
    assert "admin password must be at least 12 characters" in result2.output


def test_contact_info_hidden_on_book_detail(client, sample_book, test_student):
    """Verify that private phone numbers and emails are NEVER exposed on the public book detail page."""
    response = client.get(f'/books/{sample_book.id}')
    assert response.status_code == 200

    # Ensure seller's phone is NOT in the HTML response
    assert test_student.phone.encode('utf-8') not in response.data

    # Ensure seller's private email is NOT in the HTML response
    assert test_student.email.encode('utf-8') not in response.data

    # Ensure college name and display name are safely shown
    assert test_student.full_name.encode('utf-8') in response.data
    assert test_student.college_name.encode('utf-8') in response.data
