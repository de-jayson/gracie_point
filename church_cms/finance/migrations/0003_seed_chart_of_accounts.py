"""
Data migration: seed the chart of accounts for every existing church.

New churches get this automatically via _setup_church_defaults() on registration.
This migration handles churches that were created before that was in place.

Run with: python manage.py migrate
"""

from django.db import migrations

ACCOUNTS = [
    # (code, name, account_type)
    # ── Assets ──────────────────────────────────────────────────────────────
    ('1000', 'Cash',                                    'asset'),
    ('1010', 'Bank Account',                            'asset'),
    ('1020', 'Mobile Money (MoMo)',                     'asset'),
    # ── Income ──────────────────────────────────────────────────────────────
    ('4001', '1st Offering Income',                     'income'),
    ('4002', '2nd Offering Income',                     'income'),
    ('4003', 'Junior Youth Offering Income',            'income'),
    ('4004', "Children's Offering Income",              'income'),
    ('4010', 'Tithe Income',                            'income'),
    ('4020', 'Thanksgiving Income',                     'income'),
    ('4030', 'Other Income',                            'income'),
    # ── Expenses ─────────────────────────────────────────────────────────────
    ('5000', 'General Expenses',                        'expense'),
    ('5010', 'Contributions paid to District',          'expense'),
    ('5020', 'Eucharist/Communion',                     'expense'),
    ('5030', "Children's Service Expenses",             'expense'),
    ('5040', 'Junior Youth Expenses',                   'expense'),
    ('5050', 'Brigade Expenses',                        'expense'),
    ('5060', 'Evangelism Expenses',                     'expense'),
    ('5070', 'Salaries & Allowances',                   'expense'),
    ('5080', 'Other Staff Related Expenses',            'expense'),
    ('5090', 'Travelling & Transport',                  'expense'),
    ('5100', 'Printing & Stationery',                   'expense'),
    ('5110', 'Courier & Postage',                       'expense'),
    ('5120', 'Rents',                                   'expense'),
    ('5130', 'Property Rates',                          'expense'),
    ('5140', 'Utilities',                               'expense'),
    ('5150', 'Telephones & Internet',                   'expense'),
    ('5160', 'Maintenance & Repairs',                   'expense'),
    ('5170', 'Vehicle Running (Fuel and Lubricants)',    'expense'),
    ('5180', 'Vehicle Maintenance',                     'expense'),
    ('5190', 'Depreciation & Amortization Expenses',    'expense'),
    ('5200', 'Levies',                                  'expense'),
    ('5210', 'Donations',                               'expense'),
    ('5220', 'Hospitality',                             'expense'),
    ('5230', 'Welfare Expenses',                        'expense'),
]


def seed_accounts(apps, schema_editor):
    Church  = apps.get_model('organizations', 'Church')
    Account = apps.get_model('finance', 'Account')

    for church in Church.objects.all():
        for code, name, account_type in ACCOUNTS:
            Account.objects.get_or_create(
                code=code,
                church=church,
                defaults={
                    'name':         name,
                    'account_type': account_type,
                    'is_active':    True,
                },
            )


def remove_accounts(apps, schema_editor):
    Account = apps.get_model('finance', 'Account')
    Account.objects.filter(
        code__in=[a[0] for a in ACCOUNTS]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        # Last finance migration — check with: python manage.py showmigrations finance
        ('finance', '0002_seed_expense_categories'),
        ('organizations', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_accounts, reverse_code=remove_accounts),
    ]
