# GracePoint Church Management System

A complete, production-structured Church Management System built with Django, Tailwind CSS, and SQLite.

---

## 🏗️ Project Structure

```
church_cms/
├── church_cms/          # Project config (settings, urls, wsgi)
├── accounts/            # Custom User model + auth (login/logout/RBAC)
├── members/             # Member CRUD + profiles
├── attendance/          # Service sessions + attendance marking
├── finance/             # Contributions (tithe/offering/donation) + reports
├── events/              # Church events management
├── dashboard/           # Overview stats home screen
├── templates/           # All HTML templates
│   ├── base.html        # Sidebar + navbar layout
│   ├── accounts/
│   ├── members/
│   ├── attendance/
│   ├── finance/
│   ├── events/
│   └── dashboard/
├── static/              # Static assets (CSS, JS, images)
├── manage.py
├── requirements.txt
└── seed_data.py         # Demo data loader
```

---

## ⚡ Quick Setup

### 1. Create & activate a virtual environment
```bash
python -m venv venv
source venv/bin/activate        # Linux / macOS
venv\Scripts\activate           # Windows
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Apply database migrations
```bash
python manage.py makemigrations accounts members attendance finance events
python manage.py migrate
```

### 4. Load demo data (recommended)
```bash
python seed_data.py
```
This creates sample members, services, contributions, events, and three user accounts:

| Username | Password   | Role            |
|----------|------------|-----------------|
| admin    | admin123   | Admin           |
| pastor   | pastor123  | Pastor          |
| finance  | finance123 | Finance Officer |

### 5. (Optional) Create your own superuser
```bash
python manage.py createsuperuser
```

### 6. Run the development server
```bash
python manage.py runserver
```

Visit: **http://127.0.0.1:8000**

---

## 🔐 Role-Based Access

| Feature                  | Admin | Pastor | Finance Officer |
|--------------------------|:-----:|:------:|:---------------:|
| Dashboard                |  ✅   |   ✅   |       ✅        |
| View Members             |  ✅   |   ✅   |       ✅        |
| Add/Edit/Delete Members  |  ✅   |   ✅   |       ✅        |
| View Attendance          |  ✅   |   ✅   |       ✅        |
| Mark Attendance          |  ✅   |   ✅   |       ✅        |
| View Contributions       |  ✅   |   ✅   |       ✅        |
| Record Contributions     |  ✅   |   ❌   |       ✅        |
| Edit/Delete Contributions|  ✅   |   ❌   |       ✅        |
| Finance Reports          |  ✅   |   ✅   |       ✅        |
| Events                   |  ✅   |   ✅   |       ✅        |
| Manage System Users      |  ✅   |   ❌   |       ❌        |

---

## 🧩 Module Summary

### Accounts
- Custom `CustomUser` model extending `AbstractUser`
- Role field: `admin`, `pastor`, `finance_officer`
- Login/logout with redirect
- Admin-only user management (CRUD)
- Role decorators: `@admin_required`, `@finance_required`, `@pastor_or_admin_required`

### Members
- Full CRUD with search (name, email, phone) and status filter
- Fields: name, phone, email, address, gender, DOB, date joined, status, notes
- Member detail page shows linked attendance history and contributions

### Attendance
- Service sessions: Sunday, Midweek, Prayer, Special, Youth
- Checkbox-based bulk attendance marking
- Select All / Deselect All buttons
- Attendance detail shows present vs. absent members

### Finance
- Record tithes, offerings, donations, special seeds
- Optional member linkage (supports anonymous contributions)
- Filter by type, date range
- Report page: breakdown by type with visual bars + monthly trend

### Events
- Create, edit, delete events
- Separate upcoming / past sections
- Fields: title, type, date, start/end time, location, description

### Dashboard
- Total active members (+ new this month)
- Latest service attendance count
- This month's contributions total
- Upcoming events count
- Recent members list
- Recent contributions table

---

## 🎨 UI Design

- **Theme**: Dark blue-black (`#0e1015` background)
- **Accents**: Dimmed emerald green (`#22c55e` family)
- **Fonts**: DM Serif Display (logo) + Inter (body)
- **Sidebar**: Collapsible with grouped navigation sections
- **Cards**: Glassmorphism-style with subtle borders
- **Tables**: Clean rows with hover states
- **Messages**: Color-coded feedback (success/error/info/warning)
- **Responsive**: Works on desktop and tablet

---

## 🗄️ Switching to PostgreSQL

In `church_cms/settings.py`, replace the SQLite config with:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'church_cms'),
        'USER': os.environ.get('DB_USER', 'postgres'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}
```

Install `psycopg2-binary`:
```bash
pip install psycopg2-binary
```

---

## 🔧 Django Admin

Access the Django admin at `/admin/` using the superuser credentials.

All models are registered:
- `CustomUser` (accounts)
- `Member` (members)
- `Service`, `Attendance` (attendance)
- `Contribution` (finance)
- `Event` (events)

---

## 📝 Notes

- `SECRET_KEY` in settings must be changed for production
- Set `DEBUG = False` in production
- Run `python manage.py collectstatic` before deploying
- All forms use CSRF protection
- Passwords are hashed with Django's default PBKDF2 algorithm
