"""
Finance Models

Accounting-powered church finance engine.

Layers:
  1. Chart of Accounts   — Account
  2. Double-entry ledger — JournalEntry / JournalLine
  3. Service collections — ServiceOffering
  4. Expense management  — ExpenseCategory, ExpenseRecord
  5. Fund tracking       — Fund, FundTransaction
  6. Audit trail         — AuditLog

Rule: balances are ALWAYS derived from journal lines — never stored directly.
"""

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError


# ── 1. Chart of Accounts ──────────────────────────────────────────────────────

class Account(models.Model):
    """
    A single account in the chart of accounts.

    Assets   1000–1999
    Income   4000–4999
    Expenses 5000–5999
    """

    ACCOUNT_TYPES = [
        ('asset',     'Asset'),
        ('liability', 'Liability'),
        ('equity',    'Equity'),
        ('income',    'Income'),
        ('expense',   'Expense'),
    ]

    church = models.ForeignKey(
        'organizations.Church',
        on_delete=models.CASCADE,
        related_name='accounts',
    )

    name         = models.CharField(max_length=100)
    code         = models.CharField(max_length=20)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES)

    parent = models.ForeignKey(
        'self',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='children',
    )

    is_active  = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['code']
        verbose_name = 'Account'
        verbose_name_plural = 'Chart of Accounts'
        # code is unique per church, not globally
        unique_together = [('church', 'code')]

    def __str__(self):
        return f'{self.code} — {self.name}'

    @property
    def balance(self):
        """Derived balance from posted journal lines only."""
        from django.db.models import Sum
        lines        = JournalLine.objects.filter(account=self, journal_entry__posted=True)
        total_debit  = lines.aggregate(s=Sum('debit'))['s']  or 0
        total_credit = lines.aggregate(s=Sum('credit'))['s'] or 0
        if self.account_type in ('asset', 'expense'):
            return total_debit - total_credit
        return total_credit - total_debit


# ── 2. Double-Entry Journal ───────────────────────────────────────────────────

class JournalEntry(models.Model):
    """
    A balanced accounting transaction.
    Total debits must always equal total credits.
    Posted entries are immutable.
    """

    church = models.ForeignKey(
        'organizations.Church',
        on_delete=models.CASCADE,
        related_name='journal_entries',
    )

    description      = models.TextField()
    transaction_date = models.DateField()

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='journal_entries',
    )

    # Source links — only one will be set per entry
    service_offering = models.OneToOneField(
        'ServiceOffering',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='journal_entry',
    )
    expense_record = models.OneToOneField(
        'ExpenseRecord',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='journal_entry',
    )

    posted     = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-transaction_date', '-created_at']
        verbose_name = 'Journal Entry'
        verbose_name_plural = 'Journal Entries'

    def __str__(self):
        status = 'Posted' if self.posted else 'Draft'
        return f'[{status}] {self.transaction_date} — {self.description}'

    def _validate_balance(self):
        from django.db.models import Sum
        lines = self.lines.all()
        if not lines.exists():
            return
        total_debit  = lines.aggregate(s=Sum('debit'))['s']  or 0
        total_credit = lines.aggregate(s=Sum('credit'))['s'] or 0
        if total_debit != total_credit:
            raise ValidationError(
                f'Journal entry is unbalanced: debits={total_debit}, credits={total_credit}.'
            )

    def clean(self):
        self._validate_balance()

    @property
    def total_debits(self):
        from django.db.models import Sum
        return self.lines.aggregate(s=Sum('debit'))['s'] or 0

    @property
    def total_credits(self):
        from django.db.models import Sum
        return self.lines.aggregate(s=Sum('credit'))['s'] or 0

    @property
    def is_balanced(self):
        return self.total_debits == self.total_credits


class JournalLine(models.Model):
    """One debit or credit leg of a journal entry."""

    journal_entry = models.ForeignKey(
        JournalEntry,
        related_name='lines',
        on_delete=models.CASCADE,
    )
    account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name='journal_lines',
    )
    debit  = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    memo   = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name = 'Journal Line'

    def __str__(self):
        if self.debit > 0:
            return f'DR {self.account.code} {self.debit}'
        return f'CR {self.account.code} {self.credit}'

    def clean(self):
        if self.debit < 0 or self.credit < 0:
            raise ValidationError('Amounts cannot be negative.')
        if self.debit > 0 and self.credit > 0:
            raise ValidationError('A line cannot have both debit and credit.')


# ── 3. Service Offering ───────────────────────────────────────────────────────

class ServiceOffering(models.Model):
    """
    Financial collections for a single service/event.
    A balanced journal entry is auto-generated by PostingService on save.
    """

    church = models.ForeignKey(
        'organizations.Church',
        on_delete=models.CASCADE,
        related_name='service_offerings',
    )

    event_name = models.CharField(max_length=300)
    date       = models.DateField()
    notes      = models.TextField(blank=True, null=True)

    first_offering    = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='1st Offering')
    second_offering   = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='2nd Offering')
    jy_offering       = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='JY Offering')
    children_offering = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Children's Service Offering")
    tithe             = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Tithe')
    thanksgiving      = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Thanksgiving')
    other_amount      = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Other Amount')
    other_description = models.CharField(max_length=200, blank=True, null=True, verbose_name='Other Description')

    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='service_offerings',
    )
    recorded_at = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-recorded_at']
        verbose_name = 'Service Offering Record'
        verbose_name_plural = 'Service Offering Records'

    def __str__(self):
        return f'{self.event_name} ({self.date})'

    @property
    def total(self):
        return (
            self.first_offering + self.second_offering +
            self.jy_offering    + self.children_offering +
            self.tithe          + self.thanksgiving +
            self.other_amount
        )

    @property
    def has_journal_entry(self):
        return hasattr(self, 'journal_entry') and self.journal_entry is not None


# ── 4. Expense Management ─────────────────────────────────────────────────────

class ExpenseCategory(models.Model):
    """
    A category for grouping expenses (e.g. Transport, Welfare, Media).
    Each category maps to a ledger account for automatic posting.
    """

    church = models.ForeignKey(
        'organizations.Church',
        on_delete=models.CASCADE,
        related_name='expense_categories',
    )

    name    = models.CharField(max_length=100)
    color   = models.CharField(max_length=20, default='zinc', help_text='Tailwind color name for UI badges')
    account = models.ForeignKey(
        Account,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='expense_categories',
        help_text='Expense account this category posts to',
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Expense Category'
        verbose_name_plural = 'Expense Categories'
        # name is unique per church, not globally
        unique_together = [('church', 'name')]

    def __str__(self):
        return self.name


class ExpenseRecord(models.Model):
    """
    A single church expense.

    Approval flow:  pending → approved / rejected
    On approval:    journal entry posted + fund balance reduced
    """

    STATUS_PENDING  = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'

    STATUS_CHOICES = [
        (STATUS_PENDING,  'Pending'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    PAYMENT_METHODS = [
        ('cash',     'Cash'),
        ('bank',     'Bank Transfer'),
        ('momo',     'Mobile Money'),
        ('cheque',   'Cheque'),
        ('other',    'Other'),
    ]

    church = models.ForeignKey(
        'organizations.Church',
        on_delete=models.CASCADE,
        related_name='expenses',
    )

    title        = models.CharField(max_length=255)
    description  = models.TextField(blank=True, null=True)
    amount       = models.DecimalField(max_digits=12, decimal_places=2)
    expense_date = models.DateField()

    category = models.ForeignKey(
        ExpenseCategory,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='expenses',
    )
    fund = models.ForeignKey(
        'Fund',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='expenses',
    )

    # Link to the service/event this expense belongs to (optional)
    related_service = models.ForeignKey(
        ServiceOffering,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='expenses',
    )

    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='cash')
    receipt_url    = models.FileField(upload_to='finance/receipts/', null=True, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)

    created_by  = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='expenses_created',
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='expenses_approved',
    )
    approved_at   = models.DateTimeField(null=True, blank=True)
    approval_note = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-expense_date', '-created_at']
        verbose_name = 'Expense Record'
        verbose_name_plural = 'Expense Records'

    def __str__(self):
        return f'{self.title} — GHS {self.amount} ({self.get_status_display()})'

    @property
    def has_journal_entry(self):
        return hasattr(self, 'journal_entry') and self.journal_entry is not None

    @property
    def is_pending(self):
        return self.status == self.STATUS_PENDING

    @property
    def is_approved(self):
        return self.status == self.STATUS_APPROVED


# ── 5. Fund Tracking ──────────────────────────────────────────────────────────

class Fund(models.Model):
    """
    A named pool of money (e.g. Main Operations, Building Fund, Welfare).

    Balance = opening_balance + total_income - total_expenses
    All figures are derived — never stored — except opening_balance which
    seeds the fund on creation.
    """

    STATUS_ACTIVE   = 'active'
    STATUS_INACTIVE = 'inactive'
    STATUS_ARCHIVED = 'archived'

    STATUS_CHOICES = [
        (STATUS_ACTIVE,   'Active'),
        (STATUS_INACTIVE, 'Inactive'),
        (STATUS_ARCHIVED, 'Archived'),
    ]

    FUNDING_SOURCES = [
        ('cash',     'Cash'),
        ('bank',     'Bank Transfer'),
        ('momo',     'Mobile Money'),
        ('donation', 'Donation'),
        ('other',    'Other'),
    ]

    church = models.ForeignKey(
        'organizations.Church',
        on_delete=models.CASCADE,
        related_name='funds',
    )

    # ── Identity ──────────────────────────────────────────────────────────────
    name        = models.CharField(max_length=100)
    code        = models.CharField(
        max_length=20,
        help_text='Short reference code e.g. BLD001, WLF001',
    )
    description = models.TextField(blank=True, null=True)

    # ── Financial setup ───────────────────────────────────────────────────────
    opening_balance = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        help_text='Starting balance when this fund was created',
    )
    funding_source = models.CharField(
        max_length=20, choices=FUNDING_SOURCES, default='cash',
        help_text='Where the initial deposit came from',
    )

    # ── Governance ────────────────────────────────────────────────────────────
    is_restricted       = models.BooleanField(
        default=False,
        help_text='Money can only be used for this fund\'s designated purpose',
    )
    approval_threshold  = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        help_text='Expenses above this amount require senior approval (leave blank to disable)',
    )
    assigned_ministry   = models.CharField(
        max_length=100, blank=True, null=True,
        help_text='e.g. Youth Ministry, Media Team, Welfare Team',
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE,
    )

    # ── Timestamps ────────────────────────────────────────────────────────────
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='funds_created',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Fund'
        verbose_name_plural = 'Funds'
        # name and code are unique per church, not globally
        unique_together = [('church', 'name'), ('church', 'code')]

    def __str__(self):
        return f'{self.code} — {self.name}'

    @property
    def is_active(self):
        return self.status == self.STATUS_ACTIVE

    @property
    def total_income(self):
        from django.db.models import Sum
        return self.transactions.filter(
            transaction_type='credit'
        ).aggregate(s=Sum('amount'))['s'] or 0

    @property
    def total_expenses(self):
        from django.db.models import Sum
        return self.expenses.filter(
            status=ExpenseRecord.STATUS_APPROVED
        ).aggregate(s=Sum('amount'))['s'] or 0

    @property
    def balance(self):
        return self.opening_balance + self.total_income - self.total_expenses

    @property
    def pending_expenses_total(self):
        from django.db.models import Sum
        return self.expenses.filter(
            status=ExpenseRecord.STATUS_PENDING
        ).aggregate(s=Sum('amount'))['s'] or 0

    @property
    def requires_approval_for(self, amount):
        """Return True if the given amount requires senior approval."""
        if self.approval_threshold is None:
            return False
        return amount > self.approval_threshold


class FundTransaction(models.Model):
    """
    Records money moving into or out of a fund.
    Credits = income allocated. Debits = approved expenses.
    """

    TYPES = [
        ('credit', 'Credit (Income)'),
        ('debit',  'Debit (Expense)'),
    ]

    church = models.ForeignKey(
        'organizations.Church',
        on_delete=models.CASCADE,
        related_name='fund_transactions',
    )

    fund             = models.ForeignKey(Fund, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=10, choices=TYPES)
    amount           = models.DecimalField(max_digits=12, decimal_places=2)
    description      = models.CharField(max_length=255)
    reference_date   = models.DateField()
    created_by       = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-reference_date', '-created_at']

    def __str__(self):
        return f'{self.fund.name} {self.transaction_type} GHS {self.amount}'


# ── 6. Audit Log ──────────────────────────────────────────────────────────────

class AuditLog(models.Model):
    """
    Immutable record of every financial action in the system.
    Never edited, never deleted.
    """

    ACTION_CHOICES = [
        ('expense_created',  'Expense Created'),
        ('expense_updated',  'Expense Updated'),
        ('expense_approved', 'Expense Approved'),
        ('expense_rejected', 'Expense Rejected'),
        ('expense_deleted',  'Expense Deleted'),
        ('fund_credited',    'Fund Credited'),
        ('fund_debited',     'Fund Debited'),
        ('service_posted',   'Service Income Posted'),
        ('service_reversed', 'Service Income Reversed'),
        ('entry_voided',     'Journal Entry Voided'),
    ]

    church = models.ForeignKey(
        'organizations.Church',
        on_delete=models.CASCADE,
        related_name='audit_logs',
    )

    user        = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='audit_logs',
    )
    action      = models.CharField(max_length=50, choices=ACTION_CHOICES)
    entity_type = models.CharField(max_length=100)   # e.g. 'ExpenseRecord'
    entity_id   = models.PositiveIntegerField(null=True, blank=True)
    description = models.TextField()
    old_values  = models.JSONField(null=True, blank=True)
    new_values  = models.JSONField(null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'

    def __str__(self):
        who = self.user.get_full_name() if self.user else 'System'
        return f'[{self.created_at:%d %b %Y %H:%M}] {who} — {self.get_action_display()}'
