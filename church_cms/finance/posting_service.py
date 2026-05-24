"""
Finance Services Layer

All business logic lives here — never in views.

PostingService   — income journal entries (existing)
ExpenseService   — expense creation, approval, rejection
FundService      — fund credits and debits
AuditService     — audit log creation
ChartOfAccountsSeeder — initial account setup

Approval flow:
    ExpenseRecord created (pending)
        ↓
    ExpenseService.approve_expense()
        ↓  (atomic transaction)
        ├── post expense journal entry
        ├── debit fund balance
        └── create audit log
"""

from decimal import Decimal
from django.db import transaction as db_transaction
from django.utils import timezone

from .models import (
    Account, JournalEntry, JournalLine,
    ExpenseRecord, Fund, FundTransaction, AuditLog,
)


# ── Shared helper ─────────────────────────────────────────────────────────────

def _get_account(code):
    try:
        return Account.objects.get(code=code, is_active=True)
    except Account.DoesNotExist:
        raise ValueError(
            f'Account "{code}" not found. Run the chart-of-accounts seed first.'
        )


# ── 1. Posting Service (income) ───────────────────────────────────────────────

class PostingService:
    """Converts service offering records into balanced journal entries."""

    CASH_ACCOUNT              = '1000'
    FIRST_OFFERING_ACCOUNT    = '4001'
    SECOND_OFFERING_ACCOUNT   = '4002'
    JY_OFFERING_ACCOUNT       = '4003'
    CHILDREN_OFFERING_ACCOUNT = '4004'
    TITHE_ACCOUNT             = '4010'
    THANKSGIVING_ACCOUNT      = '4020'
    OTHER_INCOME_ACCOUNT      = '4030'

    @staticmethod
    def _add_credit_line(entry, account, amount, memo=''):
        if amount and amount > 0:
            JournalLine.objects.create(
                journal_entry=entry,
                account=account,
                debit=Decimal('0'),
                credit=amount,
                memo=memo,
            )

    @classmethod
    @db_transaction.atomic
    def post_service_income(cls, service_record, user):
        """
        DR  Cash 1000                (total)
            CR  4001 1st Offering
            CR  4002 2nd Offering
            CR  4003 JY Offering
            CR  4004 Children Offering
            CR  4010 Tithe
            CR  4020 Thanksgiving
            CR  4030 Other
        """
        total = service_record.total
        if total <= 0:
            return None

        if service_record.has_journal_entry:
            cls._void_existing_entry(service_record, user)

        cash_account = _get_account(cls.CASH_ACCOUNT)

        entry = JournalEntry.objects.create(
            description=f'Service Income — {service_record.event_name}',
            transaction_date=service_record.date,
            created_by=user,
            service_offering=service_record,
            posted=True,
        )

        JournalLine.objects.create(
            journal_entry=entry,
            account=cash_account,
            debit=total,
            credit=Decimal('0'),
            memo='Total service collections',
        )

        income_lines = [
            (cls.FIRST_OFFERING_ACCOUNT,      service_record.first_offering,    '1st Offering'),
            (cls.SECOND_OFFERING_ACCOUNT,     service_record.second_offering,   '2nd Offering'),
            (cls.JY_OFFERING_ACCOUNT,         service_record.jy_offering,       'JY Offering'),
            (cls.CHILDREN_OFFERING_ACCOUNT,   service_record.children_offering, "Children's Offering"),
            (cls.TITHE_ACCOUNT,               service_record.tithe,             'Tithe'),
            (cls.THANKSGIVING_ACCOUNT,        service_record.thanksgiving,      'Thanksgiving'),
            (cls.OTHER_INCOME_ACCOUNT,        service_record.other_amount,
             service_record.other_description or 'Other Income'),
        ]

        for code, amount, memo in income_lines:
            account = _get_account(code)
            cls._add_credit_line(entry, account, amount, memo)

        entry._validate_balance()

        AuditService.log(
            user=user,
            action='service_posted',
            entity_type='ServiceOffering',
            entity_id=service_record.pk,
            description=f'Journal entry #{entry.pk} posted for {service_record.event_name}. Total: GHS {total}',
        )

        return entry

    @classmethod
    @db_transaction.atomic
    def reverse_service_income(cls, service_record, user):
        if not service_record.has_journal_entry:
            return None

        original = service_record.journal_entry
        if not original.posted:
            original.delete()
            return None

        reversal = JournalEntry.objects.create(
            description=f'REVERSAL — {original.description}',
            transaction_date=original.transaction_date,
            created_by=user,
            posted=True,
        )

        for line in original.lines.all():
            JournalLine.objects.create(
                journal_entry=reversal,
                account=line.account,
                debit=line.credit,
                credit=line.debit,
                memo=f'Reversal of: {line.memo}',
            )

        original.description = f'[VOIDED] {original.description}'
        original.posted = False
        original.save(update_fields=['description', 'posted'])

        AuditService.log(
            user=user,
            action='service_reversed',
            entity_type='ServiceOffering',
            entity_id=service_record.pk,
            description=f'Journal entry #{original.pk} reversed for {service_record.event_name}.',
        )

        return reversal

    @classmethod
    def _void_existing_entry(cls, service_record, user):
        cls.reverse_service_income(service_record, user)
        je = service_record.journal_entry
        if je:
            je.service_offering = None
            je.save(update_fields=['service_offering'])


# ── 2. Expense Service ────────────────────────────────────────────────────────

class ExpenseService:
    """
    Handles expense lifecycle: create, approve, reject.

    Approve flow (atomic):
        1. Set status = approved, approved_by, approved_at
        2. Post expense journal entry (DR expense account, CR cash)
        3. Debit fund balance via FundService
        4. Write audit log
    """

    CASH_ACCOUNT = '1000'

    @classmethod
    @db_transaction.atomic
    def create_expense(cls, *, title, amount, expense_date, category=None,
                       fund=None, related_service=None, description='',
                       payment_method='cash', created_by=None):
        """Create a new expense in pending status."""
        expense = ExpenseRecord.objects.create(
            title=title,
            amount=amount,
            expense_date=expense_date,
            category=category,
            fund=fund,
            related_service=related_service,
            description=description,
            payment_method=payment_method,
            created_by=created_by,
            status=ExpenseRecord.STATUS_PENDING,
        )

        AuditService.log(
            user=created_by,
            action='expense_created',
            entity_type='ExpenseRecord',
            entity_id=expense.pk,
            description=f'Expense "{title}" created for GHS {amount}.',
            new_values={'title': title, 'amount': str(amount), 'status': 'pending'},
        )

        return expense

    @classmethod
    @db_transaction.atomic
    def approve_expense(cls, expense, approved_by, note=''):
        """
        Approve an expense.

        DR  Expense Account (from category)  amount
            CR  Cash 1000                    amount

        Then debit the linked fund.
        """
        if expense.status != ExpenseRecord.STATUS_PENDING:
            raise ValueError(f'Cannot approve an expense with status "{expense.status}".')

        old_status = expense.status

        expense.status      = ExpenseRecord.STATUS_APPROVED
        expense.approved_by = approved_by
        expense.approved_at = timezone.now()
        expense.approval_note = note
        expense.save(update_fields=['status', 'approved_by', 'approved_at', 'approval_note', 'updated_at'])

        # Post journal entry
        cls._post_expense_entry(expense, approved_by)

        # Debit the fund
        if expense.fund:
            FundService.debit_fund(
                fund=expense.fund,
                amount=expense.amount,
                description=f'Expense: {expense.title}',
                reference_date=expense.expense_date,
                user=approved_by,
            )

        AuditService.log(
            user=approved_by,
            action='expense_approved',
            entity_type='ExpenseRecord',
            entity_id=expense.pk,
            description=f'Expense "{expense.title}" approved. GHS {expense.amount}.',
            old_values={'status': old_status},
            new_values={'status': 'approved', 'approved_by': str(approved_by)},
        )

        return expense

    @classmethod
    @db_transaction.atomic
    def reject_expense(cls, expense, rejected_by, note=''):
        """Reject a pending expense — no journal entry, no fund impact."""
        if expense.status != ExpenseRecord.STATUS_PENDING:
            raise ValueError(f'Cannot reject an expense with status "{expense.status}".')

        old_status = expense.status
        expense.status        = ExpenseRecord.STATUS_REJECTED
        expense.approved_by   = rejected_by
        expense.approved_at   = timezone.now()
        expense.approval_note = note
        expense.save(update_fields=['status', 'approved_by', 'approved_at', 'approval_note', 'updated_at'])

        AuditService.log(
            user=rejected_by,
            action='expense_rejected',
            entity_type='ExpenseRecord',
            entity_id=expense.pk,
            description=f'Expense "{expense.title}" rejected.',
            old_values={'status': old_status},
            new_values={'status': 'rejected'},
        )

        return expense

    @classmethod
    def _post_expense_entry(cls, expense, user):
        """
        DR  Expense Account (category.account or generic 5000)
            CR  Cash 1000
        """
        if expense.category and expense.category.account:
            expense_account = expense.category.account
        else:
            expense_account = _get_account('5000')  # fallback: Utilities Expense

        cash_account = _get_account(cls.CASH_ACCOUNT)

        entry = JournalEntry.objects.create(
            description=f'Expense — {expense.title}',
            transaction_date=expense.expense_date,
            created_by=user,
            expense_record=expense,
            posted=True,
        )

        JournalLine.objects.create(
            journal_entry=entry,
            account=expense_account,
            debit=expense.amount,
            credit=Decimal('0'),
            memo=expense.title,
        )
        JournalLine.objects.create(
            journal_entry=entry,
            account=cash_account,
            debit=Decimal('0'),
            credit=expense.amount,
            memo=f'Payment: {expense.get_payment_method_display()}',
        )

        entry._validate_balance()
        return entry


# ── 3. Fund Service ───────────────────────────────────────────────────────────

class FundService:
    """Manages fund credits (income in) and debits (expense out)."""

    @staticmethod
    @db_transaction.atomic
    def credit_fund(*, fund, amount, description, reference_date, user=None):
        """Add money to a fund (income allocation)."""
        FundTransaction.objects.create(
            fund=fund,
            transaction_type='credit',
            amount=amount,
            description=description,
            reference_date=reference_date,
            created_by=user,
        )
        AuditService.log(
            user=user,
            action='fund_credited',
            entity_type='Fund',
            entity_id=fund.pk,
            description=f'Fund "{fund.name}" credited GHS {amount}. {description}',
        )

    @staticmethod
    @db_transaction.atomic
    def debit_fund(*, fund, amount, description, reference_date, user=None):
        """Remove money from a fund (expense approved)."""
        if fund.balance < amount:
            raise ValueError(
                f'Insufficient fund balance. '
                f'"{fund.name}" has GHS {fund.balance:,.2f}, need GHS {amount:,.2f}.'
            )
        FundTransaction.objects.create(
            fund=fund,
            transaction_type='debit',
            amount=amount,
            description=description,
            reference_date=reference_date,
            created_by=user,
        )
        AuditService.log(
            user=user,
            action='fund_debited',
            entity_type='Fund',
            entity_id=fund.pk,
            description=f'Fund "{fund.name}" debited GHS {amount}. {description}',
        )


# ── 4. Audit Service ──────────────────────────────────────────────────────────

class AuditService:
    """Write-only audit trail. Never call update/delete on AuditLog."""

    @staticmethod
    def log(*, user=None, action, entity_type, entity_id=None,
            description, old_values=None, new_values=None):
        AuditLog.objects.create(
            user=user,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            description=description,
            old_values=old_values,
            new_values=new_values,
        )


# ── 5. Chart of Accounts Seeder ───────────────────────────────────────────────

class ChartOfAccountsSeeder:
    """
    Seed the initial chart of accounts once.

        from finance.posting_service import ChartOfAccountsSeeder
        ChartOfAccountsSeeder.seed()
    """

    ACCOUNTS = [
        # Assets
        ('1000', 'Cash',                       'asset'),
        ('1010', 'Bank',                       'asset'),
        ('1020', 'MoMo Wallet',                'asset'),
        # Income
        ('4001', '1st Offering Income',        'income'),
        ('4002', '2nd Offering Income',        'income'),
        ('4003', 'JY Offering Income',         'income'),
        ('4004', "Children's Offering Income", 'income'),
        ('4010', 'Tithe Income',               'income'),
        ('4020', 'Thanksgiving Income',        'income'),
        ('4030', 'Other Income',               'income'),
        # Expenses
        ('5000', 'Utilities Expense',          'expense'),
        ('5010', 'Welfare Expense',            'expense'),
        ('5020', 'Media Expense',              'expense'),
        ('5030', 'Transport Expense',          'expense'),
        ('5040', 'Feeding Expense',            'expense'),
        ('5050', 'Accommodation Expense',      'expense'),
        ('5060', 'Equipment Expense',          'expense'),
        ('5070', 'Fuel Expense',               'expense'),
        ('5080', 'Decorations Expense',        'expense'),
    ]

    @classmethod
    def seed(cls):
        created = 0
        for code, name, account_type in cls.ACCOUNTS:
            _, was_created = Account.objects.get_or_create(
                code=code,
                defaults={'name': name, 'account_type': account_type},
            )
            if was_created:
                created += 1
        return created
