import os
import click
from app import db
from app.models import User, Book, BookRequest, Wishlist, ActivityLog


def register_cli_commands(app):
    """Register custom Flask CLI management commands."""

    @app.cli.command("init-db")
    def init_db():
        """Create all database tables."""
        db.create_all()
        click.echo("[OK] Database tables created successfully.")

    @app.cli.command("create-admin")
    @click.option('--username', default=None, help='Admin username')
    @click.option('--email', default=None, help='Admin email address')
    @click.option('--password', default=None, help='Admin password')
    def create_admin(username, email, password):
        """Create an administrator account."""
        is_production = os.environ.get('FLASK_ENV') == 'production' or not app.config.get('DEBUG', False)

        admin_email = email or os.environ.get('ADMIN_EMAIL', 'admin@bookloop.edu')
        admin_username = username or os.environ.get('ADMIN_USERNAME', 'admin')
        admin_password = password or os.environ.get('ADMIN_PASSWORD')

        if is_production:
            if not admin_password:
                click.echo("[ERROR] In production, an explicit admin password must be supplied via --password or the ADMIN_PASSWORD environment variable.")
                return
            if admin_password in ('AdminPassword123!', 'password', 'admin123', 'admin', '12345678'):
                click.echo("[ERROR] In production, default or trivial admin passwords ('AdminPassword123!') are strictly prohibited.")
                return
            if len(admin_password) < 12:
                click.echo("[ERROR] In production, the admin password must be at least 12 characters.")
                return
        else:
            # Development fallback
            admin_password = admin_password or 'AdminPassword123!'

        user = User.query.filter((User.email == admin_email) | (User.username == admin_username)).first()
        if user:
            user.role = 'admin'
            user.set_password(admin_password)
            db.session.commit()
            click.echo(f"[OK] Existing user '{user.username}' upgraded to administrator.")
        else:
            admin_user = User(
                username=admin_username,
                email=admin_email,
                full_name="Platform Administrator",
                college_name="BookLoop University Headquarters",
                role='admin'
            )
            admin_user.set_password(admin_password)
            db.session.add(admin_user)
            db.session.commit()
            click.echo(f"[OK] Administrator account '{admin_username}' ({admin_email}) created.")

    @app.cli.command("seed-data")
    def seed_data():
        """Populate database with sample students and academic books for testing."""
        is_production = os.environ.get('FLASK_ENV') == 'production' or not app.config.get('DEBUG', False)
        if is_production:
            click.echo("[ERROR] The seed-data command is disabled in production environments for security.")
            return

        db.create_all()

        # Check if sample users already exist
        if User.query.filter_by(username='alex_cs').first():
            click.echo("Sample data already present.")
            return

        # Create Admin
        admin = User(
            username="admin",
            email="admin@bookloop.edu",
            full_name="Admin Director",
            college_name="Central Institute of Technology",
            role="admin"
        )
        admin.set_password("AdminPassword123!")
        db.session.add(admin)

        # Create Students
        student1 = User(
            username="alex_cs",
            email="alex@campus.edu",
            full_name="Alex Rivera",
            college_name="Engineering College of Technology",
            phone="+1 (555) 234-5678",
            bio="Junior Computer Science major passionate about open-source algorithms and distributed systems.",
            role="student"
        )
        student1.set_password("Student123!")
        db.session.add(student1)

        student2 = User(
            username="sophia_med",
            email="sophia@medschool.edu",
            full_name="Sophia Chen",
            college_name="University School of Medicine",
            phone="+1 (555) 987-6543",
            bio="2nd year Medical student. Happy to swap preclinical textbooks for anatomy atlases.",
            role="student"
        )
        student2.set_password("Student123!")
        db.session.add(student2)

        student3 = User(
            username="marcus_biz",
            email="marcus@business.edu",
            full_name="Marcus Vance",
            college_name="School of Global Management",
            phone="+1 (555) 432-1098",
            bio="Finance and Economics senior. Graduating this semester, selling all core textbooks.",
            role="student"
        )
        student3.set_password("Student123!")
        db.session.add(student3)

        db.session.commit()

        # Create Books
        books = [
            Book(
                title="Introduction to Algorithms",
                author="Thomas H. Cormen, Charles E. Leiserson, Ronald L. Rivest, Clifford Stein",
                isbn="978-0262046305",
                subject="Data Structures & Algorithms",
                department="Computer Science & IT",
                semester="3rd Semester",
                edition="4th Edition (CLRS)",
                description="The definitive guide to algorithms. Essential reference for CS majors. In excellent condition, no pencil markings or highlighter marks.",
                condition="Like New",
                price=45.00,
                listing_type="Both",
                cover_image_url="https://images.unsplash.com/photo-1532012164546-f432f2e3edd9?auto=format&fit=crop&w=600&q=80",
                is_available=True,
                user_id=student1.id
            ),
            Book(
                title="Computer Systems: A Programmer's Perspective",
                author="Randal E. Bryant, David R. O'Hallaron",
                isbn="978-0134092669",
                subject="Computer Architecture & OS",
                department="Computer Science & IT",
                semester="4th Semester",
                edition="3rd Edition",
                description="Deep dive into computer architecture, memory hierarchies, and machine-level representation. Lightly read with clean pages.",
                condition="Good",
                price=38.50,
                listing_type="Sell",
                cover_image_url="https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?auto=format&fit=crop&w=600&q=80",
                is_available=True,
                user_id=student1.id
            ),
            Book(
                title="Gray's Anatomy for Students",
                author="Richard Drake, A. Wayne Vogl, Adam W. M. Mitchell",
                isbn="978-0323393041",
                subject="Human Gross Anatomy",
                department="Medical & Health Sciences",
                semester="1st Semester",
                edition="4th Edition",
                description="Clinically oriented, clearly written and colorfully illustrated. Includes surface anatomy and clinical cases. Very light shelf wear on corners.",
                condition="Like New",
                price=55.00,
                listing_type="Both",
                cover_image_url="https://images.unsplash.com/photo-1584820927498-cfe5211fd8bf?auto=format&fit=crop&w=600&q=80",
                is_available=True,
                user_id=student2.id
            ),
            Book(
                title="Principles of Corporate Finance",
                author="Richard A. Brealey, Stewart C. Myers, Franklin Allen",
                isbn="978-1260013900",
                subject="Corporate Financial Management",
                department="Business & Management",
                semester="5th Semester",
                edition="13th Edition",
                description="Comprehensive guide to how financial managers solve practical problems. Minor highlighter on chapters 4-6.",
                condition="Good",
                price=32.00,
                listing_type="Sell",
                cover_image_url="https://images.unsplash.com/photo-1554224155-8d04cb21cd6c?auto=format&fit=crop&w=600&q=80",
                is_available=True,
                user_id=student3.id
            ),
            Book(
                title="Calculus: Early Transcendentals",
                author="James Stewart",
                isbn="978-1285741550",
                subject="Engineering Mathematics",
                department="Natural Sciences & Math",
                semester="1st Semester",
                edition="8th Edition",
                description="Required for all freshman calculus series (Math 1A/1B). Well preserved binding, all exercises clear and legible.",
                condition="Good",
                price=28.00,
                listing_type="Exchange",
                cover_image_url="https://images.unsplash.com/photo-1509228468518-180dd4864904?auto=format&fit=crop&w=600&q=80",
                is_available=True,
                user_id=student3.id
            ),
            Book(
                title="Machine Learning: A Probabilistic Perspective",
                author="Kevin P. Murphy",
                isbn="978-0262018029",
                subject="Artificial Intelligence",
                department="Computer Science & IT",
                semester="6th Semester",
                edition="Adaptive Computation Series",
                description="Rigorous and self-contained introduction to statistical machine learning. Excellent condition.",
                condition="Like New",
                price=60.00,
                listing_type="Both",
                cover_image_url="https://images.unsplash.com/photo-1516321318423-f06f85e504b3?auto=format&fit=crop&w=600&q=80",
                is_available=True,
                user_id=student1.id
            )
        ]

        for b in books:
            db.session.add(b)
        db.session.commit()

        # Create sample exchange request from Sophia to Alex for CLRS
        req1 = BookRequest(
            book_id=books[0].id,
            requester_id=student2.id,
            request_type="exchange",
            offered_book_id=books[2].id,
            status="Pending",
            message="Hi Alex! I'm taking the bioinformatics elective this term and would love to exchange my Gray's Anatomy for your Algorithms book if that works for you!"
        )
        db.session.add(req1)

        # Create sample wishlist
        wish1 = Wishlist(user_id=student2.id, book_id=books[1].id)
        wish2 = Wishlist(user_id=student3.id, book_id=books[0].id)
        db.session.add(wish1)
        db.session.add(wish2)

        # Activity logs
        ActivityLog.log(student1.id, "LISTED_BOOK", 'Listed "Introduction to Algorithms".')
        ActivityLog.log(student2.id, "LISTED_BOOK", 'Listed "Gray\'s Anatomy for Students".')
        ActivityLog.log(student2.id, "EXCHANGE_REQUEST_SENT", 'Proposed exchange for "Introduction to Algorithms".')

        db.session.commit()
        click.echo("[OK] Sample students, books, requests, and activity seeded successfully!")
