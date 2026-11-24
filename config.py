import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
# Load environment variables from .env if present
load_dotenv(os.path.join(basedir, '.env'))


class Config:
    """Base application configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-insecure-secret-key-bookloop-change-me')
    
    # Handle PostgreSQL URL scheme discrepancy (postgres:// -> postgresql://)
    database_url = os.environ.get('DATABASE_URL', f'sqlite:///{os.path.join(basedir, "bookloop.db")}')
    if database_url and database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
        
    SQLALCHEMY_DATABASE_URI = database_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload settings
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 Megabytes
    UPLOAD_FOLDER = os.path.join(basedir, 'app', 'static', 'uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
    
    # Cloudinary credentials
    CLOUDINARY_CLOUD_NAME = os.environ.get('CLOUDINARY_CLOUD_NAME')
    CLOUDINARY_API_KEY = os.environ.get('CLOUDINARY_API_KEY')
    CLOUDINARY_API_SECRET = os.environ.get('CLOUDINARY_API_SECRET')
    
    # Security cookie defaults
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = 'Lax'
    
    # Pagination
    ITEMS_PER_PAGE = 9


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    SESSION_COOKIE_SECURE = False


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    SECRET_KEY = os.environ.get('SECRET_KEY')

    @classmethod
    def init_app(cls, app):
        """Enforce production security constraints on startup."""
        secret_key = os.environ.get('SECRET_KEY')
        insecure_keys = (
            None,
            '',
            'dev-insecure-secret-key-bookloop-change-me',
            'change-this-to-a-secure-random-secret-key-in-production',
            'test-secret-key-never-use-in-production'
        )
        if not secret_key or secret_key in insecure_keys:
            raise RuntimeError(
                "PRODUCTION CRITICAL ERROR: The SECRET_KEY environment variable is missing, "
                "empty, or set to an insecure default. A cryptographically random secret key "
                "(e.g. generated via `python -c 'import secrets; print(secrets.token_hex(32))'`) "
                "must be configured before starting BookLoop in production."
            )
        if len(secret_key) < 16:
            raise RuntimeError(
                "PRODUCTION CRITICAL ERROR: The SECRET_KEY environment variable must be at least 16 characters."
            )
        
        # Enforce PostgreSQL in production
        db_url = os.environ.get('DATABASE_URL')
        if not db_url:
            raise RuntimeError(
                "PRODUCTION CRITICAL ERROR: DATABASE_URL environment variable is mandatory in production."
            )


from sqlalchemy.pool import StaticPool


class TestingConfig(Config):
    """Testing configuration with in-memory database."""
    TESTING = True
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = 'sqlite://'
    SQLALCHEMY_ENGINE_OPTIONS = {
        'poolclass': StaticPool,
        'connect_args': {'check_same_thread': False}
    }
    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False
    SECRET_KEY = 'test-secret-key-never-use-in-production'


config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
