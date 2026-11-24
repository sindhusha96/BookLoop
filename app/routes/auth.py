from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlparse
from app import db
from app.models import User, ActivityLog
from app.forms import RegistrationForm, LoginForm, ProfileEditForm, ChangePasswordForm

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Register a new student account."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data.strip(),
            email=form.email.data.strip().lower(),
            full_name=form.full_name.data.strip(),
            college_name=form.college_name.data.strip(),
            phone=form.phone.data.strip() if form.phone.data else None,
            role='student'
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        # Log registration activity
        ActivityLog.log(user.id, 'ACCOUNT_CREATED', 'Created BookLoop student account.')

        # Automatically log the student in
        login_user(user)
        flash(f"Welcome to BookLoop, {user.full_name}! Your account has been created.", "success")
        return redirect(url_for('dashboard.index'))

    return render_template('auth/register.html', form=form)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Authenticate student or administrator."""
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('dashboard.index'))

    form = LoginForm()
    if form.validate_on_submit():
        identifier = form.email.data.strip()
        # Allow sign in with either email or username
        user = User.query.filter(
            (User.email == identifier.lower()) | (User.username == identifier)
        ).first()

        if user and user.check_password(form.password.data):
            if not user.is_active:
                flash("Your account has been deactivated. Please contact support.", "danger")
                return render_template('auth/login.html', form=form)

            login_user(user, remember=form.remember_me.data)
            flash(f"Welcome back, {user.full_name}!", "success")

            next_page = request.args.get('next')
            # Protect against open redirect attacks
            if not next_page or urlparse(next_page).netloc != '':
                if user.is_admin:
                    next_page = url_for('admin.dashboard')
                else:
                    next_page = url_for('dashboard.index')

            return redirect(next_page)
        else:
            flash("Invalid email/username or password. Please check your credentials.", "danger")

    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    """Log out current user."""
    logout_user()
    flash("You have been successfully logged out.", "info")
    return redirect(url_for('main.index'))


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """View and edit user profile."""
    form = ProfileEditForm(obj=current_user)
    if form.validate_on_submit():
        current_user.full_name = form.full_name.data.strip()
        current_user.college_name = form.college_name.data.strip()
        current_user.phone = form.phone.data.strip() if form.phone.data else None
        current_user.bio = form.bio.data.strip() if form.bio.data else None
        db.session.commit()

        ActivityLog.log(current_user.id, 'PROFILE_UPDATED', 'Updated profile information.')
        flash("Your profile has been updated successfully.", "success")
        return redirect(url_for('auth.profile'))

    return render_template('auth/profile.html', form=form)


@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Update user password."""
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash("Current password is incorrect.", "danger")
            return render_template('auth/change_password.html', form=form)

        current_user.set_password(form.new_password.data)
        db.session.commit()

        ActivityLog.log(current_user.id, 'PASSWORD_CHANGED', 'Changed account password.')
        flash("Your password has been changed successfully.", "success")
        return redirect(url_for('auth.profile'))

    return render_template('auth/change_password.html', form=form)
