"""
Data migration: seed global expense categories.
These are shared across all churches — no church FK.
Run automatically with: python manage.py migrate
"""
 
from django.db import migrations
 
CATEGORIES = [
    "Contributions paid to District",
    "Eucharist/Communion",
    "Children's Service Expenses",
    "Junior Youth Expenses",
    "Brigade Expenses",
    "Evangelism Expenses",
    "Salaries & Allowances",
    "Other Staff Related Expenses",
    "Travelling & Transport",
    "Printing & Stationery",
    "Courier & Postage",
    "Rents",
    "Property Rates",
    "Utilities",
    "Telephones & Internet",
    "Maintenance & Repairs",
    "Vehicle Running (Fuel and Lubricants)",
    "Vehicle Maintenance",
    "Depreciation & Amortization Expenses",
    "Levies",
    "Donations",
    "Hospitality",
    "Welfare Expenses",
]
 
 
def seed_categories(apps, schema_editor):
    ExpenseCategory = apps.get_model('finance', 'ExpenseCategory')
    for name in CATEGORIES:
        ExpenseCategory.objects.get_or_create(name=name)
 
 
def remove_categories(apps, schema_editor):
    ExpenseCategory = apps.get_model('finance', 'ExpenseCategory')
    ExpenseCategory.objects.filter(name__in=CATEGORIES).delete()
 
 
class Migration(migrations.Migration):
 
    dependencies = [
        # Replace with the actual last migration in your finance app
        # Run: python manage.py showmigrations finance
        # and use the last one listed
        ('finance', '0001_initial'),
    ]
 
    operations = [
        migrations.RunPython(seed_categories, reverse_code=remove_categories),
    ]
 