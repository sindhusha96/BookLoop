# BookLoop – Student Book Exchange Platform

[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Framework-Flask%203.1-black.svg)](https://flask.palletsprojects.com/)
[![Database](https://img.shields.io/badge/Database-PostgreSQL%20%2F%20SQLite-indigo.svg)](https://www.postgresql.org/)
[![Tests](https://img.shields.io/badge/Tests-48%20Passed-emerald.svg)](https://pytest.org/)
[![Deploy](https://img.shields.io/badge/Deploy-Render%20Ready-success.svg)](https://render.com/)

> **"Give Your Books a Second Life."**  
> BookLoop is a full-stack, production-minded web application engineered specifically for university and college student communities to buy, sell, exchange, and request academic course textbooks with zero commissions.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Problem Statement & Objectives](#problem-statement--objectives)
3. [Key Features](#key-features)
4. [Technology Stack](#technology-stack)
5. [Application Architecture](#application-architecture)
6. [Database Schema](#database-schema)
7. [Project Folder Structure](#project-folder-structure)
8. [UI/UX Walkthrough](#uiux-walkthrough)
9. [Local Installation Guide](#local-installation-guide)
10. [Environment Variables](#environment-variables)
11. [Database Migrations & Seeding](#database-migrations--seeding)
12. [Running Locally](#running-locally)
13. [Running Automated Tests](#running-automated-tests)
14. [GitHub Setup & Version Control](#github-setup--version-control)
15. [Render Deployment Guide (Step-by-Step)](#render-deployment-guide-step-by-step)
16. [Security Highlights](#security-highlights)
17. [Future Enhancements](#future-enhancements)

---

## Project Overview

College students face steep annual textbook costs while past-semester books sit idle on dorm shelves. Commercial bookstore buybacks pay negligible amounts and resell textbooks at inflated prices.

**BookLoop** establishes a direct, student-to-student circular economy where students can:
- List books for sale or 1-to-1 course book exchange.
- Discover affordable course materials filtered by department, semester, and condition.
- Propose book swaps by offering one of their own available listings.
- Coordinate safe, daylight on-campus meetups without intermediaries or platform cuts.

---

## Problem Statement & Objectives

### The Problem
- **Financial Strain**: Students spend hundreds of dollars each semester on required reading materials.
- **Bookstore Inefficiencies**: Commercial bookstore buybacks pay pennies on the dollar and markup used books by 300%.
- **Campus Disconnection**: Junior students often struggle to find senior peers who have already completed the course.
- **Environmental Waste**: Unrecycled textbooks contribute to paper waste when disposed of or abandoned.

### Core Objectives
1. **Zero-Commission Platform**: Allow students to retain 100% of the value of their books.
2. **True Academic Swaps**: Support direct book-for-book exchanges alongside sales.
3. **Safety & Privacy by Design**: Keep phone numbers and personal emails private until a request is mutually accepted.
4. **Production Readiness**: Build with clean architecture, robust ORM migrations, secure session handling, Cloudinary asset pipelines, and automated test coverage.

---

## Key Features

### 1. Student Authentication & Profiles
- **Registration**: Custom validators prevent duplicate emails and usernames, enforce password strength, and capture student college/university affiliations.
- **Secure Sessions**: Passwords hashed with `werkzeug.security` (scrypt). Persistent login via `Flask-Login` with secure cookie options (`HttpOnly`, `SameSite=Lax`).
- **Profile Management**: Students can update full names, college affiliation, phone numbers, and academic bios, and securely change passwords with current-password verification.
- **Role-Based Access Control**: Strict segregation between `student` and `admin` roles via decorators (`@admin_required`).

### 2. Comprehensive Book Listing Management
- **Detailed Metadata**: Title, author, ISBN (optional), subject/course, department/discipline, semester/level, edition, condition, price, listing type, and description.
- **Condition Grading**: *Like New*, *Good*, *Acceptable*, *Used*.
- **Flexible Listing Types**:
  - `Sell`: Set price; buyers send purchase requests.
  - `Exchange`: Set price to $0.00; peers propose trades using their own listed books.
  - `Both`: Open to either cash purchase or course book swap.
- **Asset Upload Pipeline**: Seamlessly uploads to Cloudinary in production; provides local `/static/uploads/` fallback in development. Includes client-side 5MB limit check and instant image preview before upload.
- **Listing Lifecycle**: Owners can edit, mark available/unavailable, or permanently delete listings.

### 3. Search, Discovery & Filtering
- **Keyword Search**: Full-text matching across `title`, `author`, and `isbn`.
- **Granular Filters**:
  - Department / Academic Discipline (12 standard fields)
  - Semester / Academic Level (1st to 8th Semester, Graduate, Reference)
  - Physical Condition
  - Availability Mode (Sell, Exchange, Both)
  - Price Range (`min_price` and `max_price`)
- **Sorting**: Newest First, Price: Low to High, Price: High to Low.
- **Pagination**: Configurable items-per-page with persistent query-string state across page numbers.

### 4. Interactive Book Request System
- **Purchase Requests**: Requesters submit a request with an optional note. The owner accepts or rejects. Upon acceptance, the listing status updates to `Reserved`, and student contact coordinates are securely revealed to coordinate campus handoff.
- **Exchange Requests**: Requesters select an available book from their own active listings to offer in trade. Upon acceptance, **both books** are marked `Reserved`.
- **Status Lifecycle**: `Pending` &rarr; `Accepted` / `Rejected` / `Cancelled` &rarr; `Completed`.
- **Integrity Guards**: Prevents requesting one's own books, duplicate active requests, or invalid status modifications.

### 5. Saved Wishlist
- Add or remove books from user wishlist.
- Async AJAX toggle support with client toast alerts.
- Dedicated wishlist dashboard view.
- Unique database constraint preventing duplicate entries.

### 6. Student Dashboard
- Metric counters: Active listings, pending incoming requests, sent requests, completed deals, and saved wishlist items.
- Urgent pending request alert banner with one-click Accept/Decline.
- Recent activity timeline tracking listings, requests, and completed swaps.

### 7. Administrator Control Panel
- Platform-wide statistics: total users, active listings, completed exchanges, pending reports.
- Analytics breakdowns: listings by department and condition distribution.
- User management: search users, toggle active/deactivated status (with protection against self-deactivation).
- Listing moderation: search, view, toggle status, or remove inappropriate listings.
- Report moderation: review student reports, resolve, dismiss, or deactivate violating books.

---

## Technology Stack

| Layer | Technologies |
|---|---|
| **Frontend** | HTML5, CSS3, Vanilla JavaScript (ES6+), Bootstrap 5.3, Bootstrap Icons |
| **Backend** | Python 3.13, Flask 3.1, Flask-WTF, WTForms, email-validator |
| **ORM & Database** | Flask-SQLAlchemy 3.1, SQLAlchemy 2.1, SQLite (local), PostgreSQL (production) |
| **Migrations** | Flask-Migrate 4.1, Alembic 1.20 |
| **Authentication** | Flask-Login 0.6.3, Werkzeug 3.1 (scrypt password hashing) |
| **Storage** | Cloudinary API (Production) / Local Static Storage (Development) |
| **Testing** | Pytest 9.2, Pytest-Mock 3.17 |
| **WSGI & Server** | Gunicorn 23.0 (Render/Production), Flask Development Server (Local) |
| **Deployment** | Render (Web Service + Render PostgreSQL Database) |

---

## Application Architecture

```
[ Browser / Mobile Client ]
         │
         ▼
[ Gunicorn / Flask Application Factory (create_app) ]
         │
    ┌────┴──────────────────────────┐
    ▼                               ▼
[ Blueprints ]               [ Extensions ]
  ├── main (Landing, Info)      ├── db (SQLAlchemy)
  ├── auth (Auth & Profiles)    ├── login_manager (Flask-Login)
  ├── books (CRUD, Search)      ├── migrate (Flask-Migrate)
  ├── requests (Exchange/Buy)   └── csrf (Flask-WTF)
  ├── dashboard (Student Hub)
  ├── admin (Moderation)
  └── errors (403, 404, 500)
         │
    ┌────┴──────────────────────────┐
    ▼                               ▼
[ Relational Database ]     [ Media Storage ]
  SQLite (Dev) /              Cloudinary (Prod) /
  PostgreSQL (Prod)           Local uploads (Dev)
```

---

## Database Schema

```
 ┌───────────────┐          ┌───────────────┐
 │     users     │1       * │     books     │
 ├───────────────┼──────────┼───────────────┤
 │ id (PK)       │          │ id (PK)       │
 │ username      │          │ title         │
 │ email         │          │ author        │
 │ password_hash │          │ isbn          │
 │ role          │          │ subject       │
 │ full_name     │          │ department    │
 │ college_name  │          │ semester      │
 │ phone         │          │ edition       │
 │ bio           │          │ condition     │
 │ is_active     │          │ price         │
 │ created_at    │          │ listing_type  │
 └───────┬───────┘          │ cover_image   │
         │1                 │ is_available  │
         │                  │ is_reserved   │
         │                  │ user_id (FK)  │
         │                  └───────┬───────┘
         │                          │1
         │*                         │*
 ┌───────┴───────┐          ┌───────┴───────┐
 │   wishlists   │          │ book_requests │
 ├───────────────┤          ├───────────────┤
 │ id (PK)       │          │ id (PK)       │
 │ user_id (FK)  │          │ book_id (FK)  │
 │ book_id (FK)  │          │ requester (FK)│
 └───────────────┘          │ type          │
                            │ offered_book  │
                            │ status        │
                            │ message       │
                            └───────────────┘
```

Additional models:
- **`reports`**: Moderation reports linking `book_id` and `reporter_id` with reason, details, status (`Pending`, `Resolved`, `Dismissed`), and admin notes.
- **`activity_logs`**: User activity events (`user_id`, `action`, `description`, `created_at`) powering the student timeline.

---

## Project Folder Structure

```
BookLoop/
│
├── app/
│   ├── __init__.py               # Application factory & context processors
│   ├── models.py                 # SQLAlchemy relational data models
│   ├── forms.py                  # WTForms form definitions & validation rules
│   ├── utils.py                  # Cloudinary image handler & @admin_required
│   │
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── main.py               # Landing page, about, contact, privacy
│   │   ├── auth.py               # Register, login, logout, profile, password
│   │   ├── books.py              # Browse, search, create, edit, delete, report
│   │   ├── requests.py           # Purchase/exchange requests & completion
│   │   ├── dashboard.py          # Student metrics, my listings, wishlist
│   │   ├── admin.py              # Admin metrics, users, books, reports
│   │   └── errors.py             # HTTP 403, 404, 500 error handlers
│   │
│   ├── static/
│   │   ├── css/
│   │   │   └── main.css          # Custom responsive marketplace styling
│   │   ├── js/
│   │   │   └── main.js           # AJAX wishlist, image preview, alerts
│   │   ├── images/
│   │   │   ├── book_placeholder.svg
│   │   │   └── book_placeholder.png
│   │   └── uploads/              # Local upload fallback (git-ignored)
│   │
│   └── templates/
│       ├── base.html             # Base layout, navbar, flash alerts, footer
│       ├── index.html            # Landing page with hero & featured books
│       ├── about.html            # Mission, principles & FAQ
│       ├── contact.html          # Campus support form & rep contacts
│       ├── privacy.html          # Privacy policy & exchange guidelines
│       ├── auth/
│       │   ├── login.html
│       │   ├── register.html
│       │   ├── profile.html
│       │   └── change_password.html
│       ├── books/
│       │   ├── browse.html       # Search, filter sidebar, sort & pagination
│       │   ├── detail.html       # Book details, request modals, report modal
│       │   ├── add.html          # New book listing form with image preview
│       │   └── edit.html         # Edit listing form
│       ├── dashboard/
│       │   ├── index.html        # Student hub & activity timeline
│       │   ├── my_listings.html  # Manage own books & toggle availability
│       │   ├── incoming_requests.html # Accept/reject incoming proposals
│       │   ├── sent_requests.html# Track sent proposals
│       │   └── wishlist.html     # Saved bookmarks
│       ├── admin/
│       │   ├── dashboard.html    # Analytics overview & platform metrics
│       │   ├── users.html        # User management & deactivation
│       │   ├── books.html        # Listing moderation
│       │   └── reports.html      # Review and resolve reported listings
│       └── errors/
│           ├── 403.html
│           ├── 404.html
│           └── 500.html
│
├── migrations/                   # Alembic database version migrations
├── tests/
│   ├── conftest.py               # Pytest fixtures & in-memory test DB
│   ├── test_auth.py              # Authentication, hashing, and profiles
│   ├── test_books.py             # Book listing CRUD & ownership checks
│   ├── test_requests.py          # Purchase/exchange workflows & completion
│   ├── test_search.py            # Search keywords, filters, sorting
│   ├── test_wishlist.py          # Wishlist operations & AJAX endpoint
│   ├── test_admin.py             # Admin authorization & moderation
│   └── test_forms.py             # WTForms validation & edge cases
│
├── config.py                     # Environment-aware configuration classes
├── run.py                        # Entry point with CLI init, seed, and admin
├── requirements.txt              # Production dependency specifications
├── render.yaml                   # Infrastructure-as-code for Render deployment
├── Procfile                      # Web process definition for Gunicorn
├── .env.example                  # Environment variable configuration template
├── .gitignore                    # Git exclusion rules
└── README.md                     # Comprehensive project documentation
```

---

## UI/UX Walkthrough

- **Color Palette**: Warm white canvas (`#fcfbf9`), surface white (`#ffffff`), deep navy (`#0f172a`, `#1e293b`), and vibrant blue accent (`#2563eb`).
- **Condition Badges**: Soft emerald for *Like New*, muted blue for *Good*, amber for *Acceptable*, and slate for *Used*.
- **Book Cover Cards**: 3:4 aspect-ratio responsive image containers with smooth zoom on hover.
- **Safety Prompts**: Prominently displayed notices emphasizing daylight public campus exchanges.
- **Toast Notifications**: Lightweight, accessible popups for asynchronous wishlist actions.

---

## Local Installation Guide

### Prerequisites
- Python 3.10+ (tested up to Python 3.13)
- Git

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/bookloop.git
cd bookloop
```

### 2. Create and Activate Virtual Environment
```bash
# Windows
python -m venv .venv
.\.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## Environment Variables

Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Configure your local `.env`:
```ini
FLASK_APP=run.py
FLASK_ENV=development
FLASK_DEBUG=1
SECRET_KEY=your-local-dev-secret-key-change-me

# SQLite for local development
DATABASE_URL=sqlite:///bookloop.db

# Cloudinary (Optional for local dev; leave blank to use local storage)
CLOUDINARY_CLOUD_NAME=
CLOUDINARY_API_KEY=
CLOUDINARY_API_SECRET=

# Default Administrator Seed Credentials
ADMIN_EMAIL=admin@bookloop.edu
ADMIN_USERNAME=admin
ADMIN_PASSWORD=AdminPassword123!
```

---

## Database Migrations & Seeding

### Initialize / Upgrade Database Tables
```bash
# Apply migrations to create the database schema
flask db upgrade
```

### Create Default Administrator
```bash
flask create-admin
```

### Populate Seed Data (Recommended for Initial Testing)
Populates realistic students, sample books across multiple departments, pending exchange requests, and wishlist items:
```bash
flask seed-data
```

**Pre-seeded Test Accounts:**
- **Admin**:
  - Email: `admin@bookloop.edu`
  - Password: `AdminPassword123!`
- **Students**:
  - `alex@campus.edu` / `Student123!`
  - `sophia@medschool.edu` / `Student123!`
  - `marcus@business.edu` / `Student123!`

---

## Running Locally

Start the local Flask development server:
```bash
python run.py
```

Open your browser at:
```
http://127.0.0.1:5000/
```

---

## Running Automated Tests

BookLoop includes an automated test suite with **48 pytest test cases** verifying authentication, authorization, CRUD operations, book requests, search/filter algorithms, and security boundaries.

Run all tests:
```bash
pytest -v
```

Run specific test modules:
```bash
pytest tests/test_auth.py -v
pytest tests/test_books.py -v
pytest tests/test_requests.py -v
pytest tests/test_search.py -v
pytest tests/test_admin.py -v
pytest tests/test_wishlist.py -v
pytest tests/test_forms.py -v
```

---

## GitHub Setup & Version Control

To initialize and push this project to a new GitHub repository:

```bash
# 1. Initialize Git repository
git init

# 2. Add all files (respecting .gitignore)
git add .

# 3. Create initial commit
git commit -m "Initial commit: Production-ready BookLoop student book exchange platform"

# 4. Link your GitHub remote
git remote add origin https://github.com/your-username/bookloop.git

# 5. Push to main branch
git branch -M main
git push -u origin main
```

> [!NOTE]
> `.env`, SQLite `.db` files, temporary local uploads, and cache directories are excluded via `.gitignore` to protect credentials.

---

## Render Deployment Guide (Step-by-Step)

BookLoop is deployment-configured for [Render](https://render.com/).

### Option A: Blueprint Deployment (Recommended)
Because this repository contains a configured `render.yaml`, you can deploy both the Web Service and Managed PostgreSQL Database simultaneously:

1. Push your repository to **GitHub**.
2. Log in to [Render Dashboard](https://dashboard.render.com/).
3. Click **New +** &rarr; **Blueprint**.
4. Select your `bookloop` repository.
5. Render reads `render.yaml` and provisions:
   - `bookloop-postgres` (PostgreSQL Database)
   - `bookloop-app` (Python Web Service running `gunicorn run:app`)
6. Under Environment Variables for `bookloop-app`, fill in your Cloudinary keys:
   - `CLOUDINARY_CLOUD_NAME`
   - `CLOUDINARY_API_KEY`
   - `CLOUDINARY_API_SECRET`
7. Click **Apply**.

---

### Option B: Manual Service Creation on Render

#### Step 1: Create PostgreSQL Database
1. In Render Dashboard, click **New +** &rarr; **PostgreSQL**.
2. Name: `bookloop-postgres`
3. Database: `bookloop`
4. User: `bookloop_admin`
5. Select the **Free** tier and click **Create Database**.
6. Once provisioned, copy the **Internal Database URL**.

#### Step 2: Create Web Service
1. Click **New +** &rarr; **Web Service**.
2. Connect your GitHub repository.
3. Configure settings:
   - **Name**: `bookloop`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt && flask db upgrade`
   - **Start Command**: `gunicorn run:app`
4. Under **Environment Variables**, add:
   - `FLASK_ENV`: `production`
   - `SECRET_KEY`: *(Generate a 32+ character random secret string)*
   - `DATABASE_URL`: *(Paste the Internal Database URL from Step 1)*
   - `CLOUDINARY_CLOUD_NAME`: *(From your Cloudinary Dashboard)*
   - `CLOUDINARY_API_KEY`: *(From your Cloudinary Dashboard)*
   - `CLOUDINARY_API_SECRET`: *(From your Cloudinary Dashboard)*
5. Click **Create Web Service**.

#### Step 3: Run Database Migrations & Create Admin on Render
Once the service builds successfully:
1. In your Render Web Service dashboard, navigate to the **Shell** tab.
2. Run:
   ```bash
   flask db upgrade
   flask create-admin --username admin --email admin@yourcollege.edu --password SecureAdminPass123!
   ```
3. Your BookLoop marketplace is live and ready for students!

---

## Security Highlights

- **No Plaintext Passwords**: Passwords encrypted using Werkzeug's `generate_password_hash` with scrypt algorithm.
- **CSRF Protection**: All POST/PUT/DELETE forms protected by Flask-WTF CSRF tokens; AJAX requests transmit CSRF header.
- **SQL Injection Prevention**: 100% parameter-bound queries via SQLAlchemy ORM; no raw string concatenation.
- **Safe Asset Storage**: Cloudinary integration ensures uploads are stored on external CDN with size and file extension validation (JPG, PNG, WEBP max 5MB).
- **Contact Privacy**: Student phone numbers and personal emails are concealed from all public pages and only revealed to mutual parties upon request acceptance.
- **Role Verification**: Admin endpoints enforce `@admin_required` decorators; non-admin attempts are blocked with HTTP 403 Forbidden.
- **Ownership Verification**: Route handlers ensure students can only edit or delete listings they personally own.

---

## Future Enhancements

- [ ] Campus Geo-Radius filtering for multi-campus university systems.
- [ ] In-app direct messaging for scheduled pickup coordination.
- [ ] Barcode scanning on mobile using HTML5 Barcode Detection API to autofill ISBN and edition.
- [ ] Email/SMS pickup reminders 2 hours before agreed meetup times.
- [ ] Campus reputation badges and verified peer review ratings upon completed transactions.

---

## License

Distributed under the **MIT License**. Created for academic book sustainability and college student communities.
