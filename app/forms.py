import re
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, SelectField, DecimalField, HiddenField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, ValidationError, NumberRange
from app.models import User

DEPARTMENT_CHOICES = [
    ('', 'All Departments'),
    ('Computer Science & IT', 'Computer Science & IT'),
    ('Electrical & Electronics', 'Electrical & Electronics'),
    ('Mechanical Engineering', 'Mechanical Engineering'),
    ('Civil Engineering', 'Civil Engineering'),
    ('Chemical Engineering', 'Chemical Engineering'),
    ('Business & Management', 'Business & Management'),
    ('Medical & Health Sciences', 'Medical & Health Sciences'),
    ('Law & Legal Studies', 'Law & Legal Studies'),
    ('Natural Sciences & Math', 'Natural Sciences & Math'),
    ('Arts & Humanities', 'Arts & Humanities'),
    ('Social Sciences', 'Social Sciences'),
    ('General / Reference', 'General / Reference')
]

SEMESTER_CHOICES = [
    ('', 'All Semesters'),
    ('1st Semester', '1st Semester'),
    ('2nd Semester', '2nd Semester'),
    ('3rd Semester', '3rd Semester'),
    ('4th Semester', '4th Semester'),
    ('5th Semester', '5th Semester'),
    ('6th Semester', '6th Semester'),
    ('7th Semester', '7th Semester'),
    ('8th Semester', '8th Semester'),
    ('Year 1', 'Year 1'),
    ('Year 2', 'Year 2'),
    ('Year 3', 'Year 3'),
    ('Year 4+', 'Year 4+'),
    ('Graduate / Masters', 'Graduate / Masters'),
    ('General Reference', 'General Reference')
]

CONDITION_CHOICES = [
    ('Like New', 'Like New – Excellent, no marks or highlights'),
    ('Good', 'Good – Clean pages, minor signs of wear'),
    ('Acceptable', 'Acceptable – Visible wear, some notes/highlighting'),
    ('Used', 'Used – Heavy wear, fully readable and intact')
]

LISTING_TYPE_CHOICES = [
    ('Sell', 'For Sale Only'),
    ('Exchange', 'For Exchange Only'),
    ('Both', 'Available for Sale or Exchange')
]


class RegistrationForm(FlaskForm):
    """User registration form."""
    username = StringField('Username', validators=[
        DataRequired(message="Username is required."),
        Length(min=3, max=30, message="Username must be between 3 and 30 characters.")
    ])
    email = StringField('College / Personal Email', validators=[
        DataRequired(message="Email address is required."),
        Email(message="Please enter a valid email address."),
        Length(max=120)
    ])
    full_name = StringField('Full Name', validators=[
        DataRequired(message="Full name is required."),
        Length(min=2, max=100)
    ])
    college_name = StringField('College / University Name', validators=[
        DataRequired(message="College name is required."),
        Length(min=2, max=150)
    ])
    phone = StringField('Contact Phone Number (Optional)', validators=[
        Optional(),
        Length(min=7, max=20, message="Please enter a valid contact number.")
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message="Password is required."),
        Length(min=8, message="Password must be at least 8 characters long.")
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(message="Please confirm your password."),
        EqualTo('password', message="Passwords must match.")
    ])
    submit = SubmitField('Create Account')

    def validate_username(self, username):
        if not re.match(r'^[A-Za-z0-9_]+$', username.data):
            raise ValidationError("Username can only contain letters, numbers, and underscores.")
        user = User.query.filter_by(username=username.data.strip()).first()
        if user:
            raise ValidationError("That username is already taken. Please pick a different one.")

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data.strip().lower()).first()
        if user:
            raise ValidationError("An account with that email already exists. Please log in.")


class LoginForm(FlaskForm):
    """User login form."""
    email = StringField('Email or Username', validators=[
        DataRequired(message="Please enter your email or username.")
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message="Please enter your password.")
    ])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class ProfileEditForm(FlaskForm):
    """Edit student profile details."""
    full_name = StringField('Full Name', validators=[
        DataRequired(message="Full name cannot be empty."),
        Length(min=2, max=100)
    ])
    college_name = StringField('College / University', validators=[
        DataRequired(message="College name cannot be empty."),
        Length(min=2, max=150)
    ])
    phone = StringField('Contact Phone Number', validators=[
        Optional(),
        Length(min=7, max=20)
    ])
    bio = TextAreaField('About Me / Bio', validators=[
        Optional(),
        Length(max=500, message="Bio must not exceed 500 characters.")
    ])
    submit = SubmitField('Update Profile')


class ChangePasswordForm(FlaskForm):
    """Password modification form."""
    current_password = PasswordField('Current Password', validators=[
        DataRequired(message="Please enter your current password.")
    ])
    new_password = PasswordField('New Password', validators=[
        DataRequired(message="Please enter a new password."),
        Length(min=8, message="Password must be at least 8 characters long.")
    ])
    confirm_new_password = PasswordField('Confirm New Password', validators=[
        DataRequired(message="Please confirm your new password."),
        EqualTo('new_password', message="New passwords must match.")
    ])
    submit = SubmitField('Change Password')


class BookListingForm(FlaskForm):
    """Create or update a book listing."""
    title = StringField('Book Title', validators=[
        DataRequired(message="Book title is required."),
        Length(max=200)
    ])
    author = StringField('Author(s)', validators=[
        DataRequired(message="Author name is required."),
        Length(max=150)
    ])
    isbn = StringField('ISBN (Optional)', validators=[
        Optional(),
        Length(max=32)
    ])
    subject = StringField('Subject / Course', validators=[
        DataRequired(message="Subject is required."),
        Length(max=100)
    ])
    department = SelectField('Department / Branch', choices=[c for c in DEPARTMENT_CHOICES if c[0] != ''], validators=[
        DataRequired(message="Please select a department.")
    ])
    semester = SelectField('Semester / Academic Level', choices=[c for c in SEMESTER_CHOICES if c[0] != ''], validators=[
        DataRequired(message="Please select a semester or academic level.")
    ])
    edition = StringField('Edition (e.g., 3rd Edition, 2023)', validators=[
        Optional(),
        Length(max=50)
    ])
    condition = SelectField('Condition', choices=CONDITION_CHOICES, validators=[
        DataRequired(message="Please specify the condition of the book.")
    ])
    listing_type = SelectField('Listing Type', choices=LISTING_TYPE_CHOICES, validators=[
        DataRequired(message="Please select how you want to list this book.")
    ])
    price = DecimalField('Price ($)', places=2, validators=[
        Optional(),
        NumberRange(min=0.00, max=10000.00, message="Price must be a positive number.")
    ], default=0.00)
    description = TextAreaField('Description', validators=[
        DataRequired(message="Please provide a brief description of the book and its state."),
        Length(min=10, max=2500, message="Description must be between 10 and 2500 characters.")
    ])
    cover_image = FileField('Book Cover Image (PNG, JPG, WEBP - Max 5MB)', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png', 'webp'], 'Only image files (jpg, jpeg, png, webp) are permitted.')
    ])
    submit = SubmitField('Publish Listing')

    def validate_price(self, field):
        if self.listing_type.data in ['Sell', 'Both'] and (field.data is None or field.data < 0):
            raise ValidationError("Please specify a valid price for books available for sale.")


class PurchaseRequestForm(FlaskForm):
    """Purchase request form."""
    message = TextAreaField('Message to Book Owner (Optional)', validators=[
        Optional(),
        Length(max=500, message="Message cannot exceed 500 characters.")
    ])
    submit = SubmitField('Send Purchase Request')


class ExchangeRequestForm(FlaskForm):
    """Exchange request form offering an existing book."""
    offered_book_id = SelectField('Select Book to Offer in Exchange', coerce=int, validators=[
        DataRequired(message="Please select one of your listed books to offer in exchange.")
    ])
    message = TextAreaField('Message to Book Owner (Optional)', validators=[
        Optional(),
        Length(max=500, message="Message cannot exceed 500 characters.")
    ])
    submit = SubmitField('Send Exchange Request')


class ReportBookForm(FlaskForm):
    """Report inappropriate or scam listing."""
    reason = SelectField('Reason for Report', choices=[
        ('Inappropriate Content', 'Inappropriate or offensive content'),
        ('Spam or Scam', 'Suspected scam or spam listing'),
        ('Incorrect Information', 'Misleading / inaccurate information'),
        ('Duplicate Listing', 'Duplicate listing'),
        ('Other', 'Other violation')
    ], validators=[DataRequired()])
    details = TextAreaField('Details / Explanation', validators=[
        DataRequired(message="Please provide details regarding this report."),
        Length(min=10, max=1000, message="Details must be between 10 and 1000 characters.")
    ])
    submit = SubmitField('Submit Report')
