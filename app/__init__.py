import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from config import config_by_name

# Initialize Flask extensions
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
csrf = CSRFProtect()


def create_app(config_name=None):
    """Application factory for BookLoop."""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
        if config_name not in config_by_name:
            config_name = 'default'

    app = Flask(__name__)
    config_class = config_by_name[config_name]
    app.config.from_object(config_class)

    # Execute configuration initialization and security checks if defined
    if hasattr(config_class, 'init_app'):
        config_class.init_app(app)

    # Ensure instance and upload folders exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.instance_path, exist_ok=True)

    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'

    # Register blueprints
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.books import books_bp
    from app.routes.requests import requests_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.admin import admin_bp
    from app.routes.errors import errors_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(books_bp, url_prefix='/books')
    app.register_blueprint(requests_bp, url_prefix='/requests')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(errors_bp)

    # Register custom CLI commands
    from app.cli import register_cli_commands
    register_cli_commands(app)

    # User loader callback for Flask-Login
    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Context processor to inject global variables (e.g. categories, pending requests count)
    @app.context_processor
    def inject_global_data():
        from flask_login import current_user
        from app.models import BookRequest
        unread_requests_count = 0
        if current_user.is_authenticated:
            unread_requests_count = BookRequest.query.join(
                BookRequest.book
            ).filter(
                BookRequest.book.has(user_id=current_user.id),
                BookRequest.status == 'Pending'
            ).count()
        return {
            'pending_incoming_count': unread_requests_count
        }

    return app
