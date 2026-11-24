import os
import uuid
from functools import wraps
from flask import current_app, flash, redirect, url_for, abort
from flask_login import current_user
from werkzeug.utils import secure_filename
import cloudinary
import cloudinary.uploader


def admin_required(f):
    """Decorator to restrict route access to administrators only."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Please sign in as an administrator to access this area.", "warning")
            return redirect(url_for('auth.login'))
        if not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def save_book_image(file_storage):
    """
    Save book cover image either to Cloudinary (production)
    or local static/uploads/ (local development).
    Returns the public image URL, or None if invalid or failed.
    """
    if not file_storage or not file_storage.filename:
        return None

    # Defensive filename and extension validation
    filename = secure_filename(file_storage.filename)
    if not filename or '.' not in filename:
        current_app.logger.warning(f"Upload rejected: invalid or empty filename '{file_storage.filename}'.")
        return None

    ext = filename.rsplit('.', 1)[1].lower()
    allowed_extensions = current_app.config.get('ALLOWED_EXTENSIONS', {'png', 'jpg', 'jpeg', 'webp'})
    if ext not in allowed_extensions:
        current_app.logger.warning(f"Upload rejected: extension '{ext}' not permitted.")
        return None

    # Check Cloudinary configuration
    cloud_name = current_app.config.get('CLOUDINARY_CLOUD_NAME')
    api_key = current_app.config.get('CLOUDINARY_API_KEY')
    api_secret = current_app.config.get('CLOUDINARY_API_SECRET')
    is_production = not current_app.debug and not current_app.testing

    if cloud_name and api_key and api_secret:
        # Configure and upload to Cloudinary
        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret,
            secure=True
        )
        try:
            upload_result = cloudinary.uploader.upload(
                file_storage,
                folder="bookloop/covers",
                transformation=[
                    {'width': 800, 'height': 1100, 'crop': 'limit'},
                    {'quality': 'auto'}
                ]
            )
            return upload_result.get('secure_url')
        except Exception as e:
            current_app.logger.error(f"Cloudinary upload failed: {e}")
            if is_production:
                current_app.logger.error("Production image persistence failed on Cloudinary. Refusing ephemeral local fallback.")
                return None
    elif is_production:
        current_app.logger.error("Production environment requires Cloudinary credentials (CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET). Refusing ephemeral local storage fallback.")
        return None

    # Local development storage fallback (disabled in production)
    unique_filename = f"{uuid.uuid4().hex}_{filename}"
    upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)

    os.makedirs(os.path.dirname(upload_path), exist_ok=True)
    file_storage.seek(0)
    file_storage.save(upload_path)

    # Return URL path accessible by browser
    return f"/static/uploads/{unique_filename}"
