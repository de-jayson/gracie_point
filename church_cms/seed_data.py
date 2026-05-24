import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'church_cms.settings')
django.setup()

from datetime import date, timedelta, time  # ✅ added time
from decimal import Decimal
from accounts.models import CustomUser
from members.models import Member
from attendance.models import ServiceAttendance
from finance.models import ServiceOffering
from events.models import Event

print("🌱 Seeding GracePoint CMS v2 demo data...")

# ── Users ──────────────────────────────────────────────────────────────────────
admin_user, _ = CustomUser.objects.get_or_create(
    username='admin',
    defaults=dict(
        first_name='Samuel', last_name='Owusu',
        email='admin@gracepoint.org', role='admin',
        is_staff=True, is_superuser=True,
    )
)
admin_user.set_password('admin123')
admin_user.save()

pastor, _ = CustomUser.objects.get_or_create(
    username='pastor',
    defaults=dict(first_name='Emmanuel', last_name='Asante',
                  email='pastor@gracepoint.org', role='pastor')
)
pastor.set_password('pastor123')
pastor.save()

finance_officer, _ = CustomUser.objects.get_or_create(
    username='finance',
    defaults=dict(first_name='Abena', last_name='Mensah',
                  email='finance@gracepoint.org', role='finance_officer')
)
finance_officer.set_password('finance123')
finance_officer.save()

print("  ✓ Users created  (admin/admin123 · pastor/pastor123 · finance/finance123)")

# ── Members ────────────────────────────────────────────────────────────────────
members_data = [
    ('Kwame',   'Asante',    'kwame@email.com',    '+233244111001', 'male',   date(2020, 1, 15), 'active'),
    ('Akosua',  'Boateng',   'akosua@email.com',   '+233244111002', 'female', date(2020, 3, 22), 'active'),
    ('Kofi',    'Mensah',    'kofi@email.com',     '+233244111003', 'male',   date(2021, 6,  5), 'active'),
    ('Ama',     'Darko',     'ama@email.com',      '+233244111004', 'female', date(2021, 8, 14), 'active'),
    ('Yaw',     'Ofori',     'yaw@email.com',      '+233244111005', 'male',   date(2022, 2, 28), 'active'),
    ('Abena',   'Appiah',    'abena2@email.com',   '+233244111006', 'female', date(2022, 5, 10), 'active'),
    ('Kweku',   'Tetteh',    'kweku@email.com',    '+233244111007', 'male',   date(2022, 9, 18), 'active'),
    ('Efua',    'Acheampong','efua@email.com',     '+233244111008', 'female', date(2023, 1,  7), 'active'),
    ('Nana',    'Adjei',     'nana@email.com',     '+233244111009', 'male',   date(2023, 4, 20), 'active'),
    ('Adwoa',   'Kyei',      'adwoa@email.com',    '+233244111010', 'female', date(2023, 7,  3), 'active'),
    ('Fiifi',   'Quaye',     'fiifi@email.com',    '+233244111011', 'male',   date(2024, 1, 12), 'active'),
    ('Maame',   'Sarpong',   'maame@email.com',    '+233244111012', 'female', date(2024, 3, 25), 'visitor'),
    ('Kwabena', 'Asare',     'kwabena@email.com',  '+233244111013', 'male',   date(2024, 6,  8), 'active'),
    ('Afia',    'Bonsu',     'afia@email.com',     '+233244111014', 'female', date(2024, 8, 19), 'inactive'),
    ('Kojo',    'Frimpong',  'kojo@email.com',     '+233244111015', 'male',   date(2025, 1,  5), 'active'),
]

for first, last, email, phone, gender, joined, status in members_data:
    Member.objects.get_or_create(
        email=email,
        defaults=dict(
            first_name=first, last_name=last,
            phone=phone, gender=gender,
            date_joined=joined, status=status,
            address='Accra, Greater Accra, Ghana',
        )
    )

print(f"  ✓ {len(members_data)} members created")

# ── Attendance (ServiceAttendance — headcounts, no member linkage) ─────────────
today = date.today()

attendance_data = [
    (
        f'Sunday Service – {(today - timedelta(days=6)).strftime("%d %B %Y")}',
        'sunday', today - timedelta(days=6),
        48, 65, 20, 26, 14, 17,
        'Good turnout. Guest speaker Pastor Boateng ministered.'
    ),
    (
        f'Midweek Service – {(today - timedelta(days=10)).strftime("%d %B %Y")}',
        'midweek', today - timedelta(days=10),
        25, 34, 10, 15, 6, 8,
        'Bible study on the book of Romans.'
    ),
    (
        f'Sunday Service – {(today - timedelta(days=13)).strftime("%d %B %Y")}',
        'sunday', today - timedelta(days=13),
        52, 70, 22, 29, 15, 19,
        None
    ),
    (
        f'Prayer Meeting – {(today - timedelta(days=17)).strftime("%d %B %Y")}',
        'prayer', today - timedelta(days=17),
        18, 27, 8, 11, 0, 0,
        'Dawn prayer. No children\'s service held.'
    ),
    (
        f'Sunday Service – {(today - timedelta(days=20)).strftime("%d %B %Y")}',
        'sunday', today - timedelta(days=20),
        44, 61, 18, 23, 13, 16,
        None
    ),
    (
        f'Youth Service – {(today - timedelta(days=27)).strftime("%d %B %Y")}',
        'youth', today - timedelta(days=27),
        10, 12, 35, 42, 8, 10,
        'Youth Sunday. Young people led worship and ministered.'
    ),
]

for event_name, stype, sdate, am, af, jm, jf, cm, cf, notes in attendance_data:
    obj, created = ServiceAttendance.objects.get_or_create(
        event_name=event_name,
        date=sdate,
    )
    if not created:  # ✅ update if exists
        obj.service_type = stype
        obj.adults_male = am
        obj.adults_female = af
        obj.junior_youth_male = jm
        obj.junior_youth_female = jf
        obj.children_male = cm
        obj.children_female = cf
        obj.notes = notes
        obj.save()
    else:
        obj.service_type = stype
        obj.adults_male = am
        obj.adults_female = af
        obj.junior_youth_male = jm
        obj.junior_youth_female = jf
        obj.children_male = cm
        obj.children_female = cf
        obj.notes = notes
        obj.save()

print(f"  ✓ {len(attendance_data)} attendance records created")

# ── Service Offerings ─────────────────────────────────────────────────────────
offering_data = [
    (
        f'Sunday Service – {(today - timedelta(days=6)).strftime("%d %B %Y")}',
        today - timedelta(days=6),
        Decimal('850.00'), Decimal('320.00'), Decimal('150.00'), Decimal('85.00'),
        Decimal('1200.00'), Decimal('430.00'), Decimal('0.00'), '',
        'Smooth collection. Recorded by Finance Officer Mensah.'
    ),
    # (rest unchanged)
]

for event_name, edate, f1, f2, jy, ch, ti, th, ot, od, notes in offering_data:
    obj, created = ServiceOffering.objects.get_or_create(
        event_name=event_name,
        date=edate,
    )
    if not created:  # ✅ update if exists
        obj.first_offering = f1
        obj.second_offering = f2
        obj.jy_offering = jy
        obj.children_offering = ch
        obj.tithe = ti
        obj.thanksgiving = th
        obj.other_amount = ot
        obj.other_description = od
        obj.notes = notes
        obj.save()
    else:
        obj.first_offering = f1
        obj.second_offering = f2
        obj.jy_offering = jy
        obj.children_offering = ch
        obj.tithe = ti
        obj.thanksgiving = th
        obj.other_amount = ot
        obj.other_description = od
        obj.notes = notes
        obj.save()

print(f"  ✓ {len(offering_data)} service offering records created")

# ── Events ─────────────────────────────────────────────────────────────────────
events_data = [
    ('Annual Church Conference 2025',
     'Our flagship annual gathering. All departments are expected to participate.',
     'conference', today + timedelta(days=14), time(9, 0), time(17, 0), 'GracePoint Auditorium'),
    # rest unchanged...
]

for title, desc, etype, edate, stime, etime, loc in events_data:
    obj, created = Event.objects.get_or_create(
    title=title,
    defaults=dict(
        description=desc,
        event_type=etype,
        date=edate,
        start_time=stime,
        end_time=etime,
        location=loc,
        created_by=admin_user,
    )
)

if not created:
    obj.description = desc
    obj.event_type = etype
    obj.date = edate
    obj.start_time = stime
    obj.end_time = etime
    obj.location = loc
    obj.created_by = admin_user
    obj.save()

print(f"  ✓ {len(events_data)} events created")

print("✅ Seeding complete! GracePoint CMS v2 demo data is ready.")