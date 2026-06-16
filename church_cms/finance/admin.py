"""Finance Admin Configuration"""
from django.contrib import admin
from .models import (
    Account, JournalEntry, JournalLine, ServiceOffering,
    ExpenseCategory, ExpenseRecord, Fund, FundTransaction, AuditLog,
    DriveCredential, DriveSettings,
)


# ── Chart of Accounts ──────────────────────────────────────────────────────────

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display  = ('code', 'name', 'church', 'account_type', 'parent', 'is_active', 'derived_balance')
    list_filter   = ('church', 'account_type', 'is_active')
    search_fields = ('code', 'name')
    ordering      = ('church', 'code')

    def derived_balance(self, obj):
        return f"GHS {obj.balance:,.2f}"
    derived_balance.short_description = 'Balance (from ledger)'


# ── Journal Entries ────────────────────────────────────────────────────────────

class JournalLineInline(admin.TabularInline):
    model  = JournalLine
    extra  = 0
    fields = ('account', 'debit', 'credit', 'memo')

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.posted:
            return ('account', 'debit', 'credit', 'memo')
        return ()


@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display    = ('transaction_date', 'church', 'description', 'total_debits_display', 'is_balanced', 'posted', 'created_by')
    list_filter     = ('church', 'posted', 'transaction_date')
    search_fields   = ('description',)
    readonly_fields = ('created_at', 'updated_at')
    inlines         = [JournalLineInline]
    date_hierarchy  = 'transaction_date'

    def total_debits_display(self, obj):
        return f"GHS {obj.total_debits:,.2f}"
    total_debits_display.short_description = 'Total'

    def is_balanced(self, obj):
        return obj.is_balanced
    is_balanced.boolean = True
    is_balanced.short_description = 'Balanced?'

    def has_delete_permission(self, request, obj=None):
        if obj and obj.posted:
            return False
        return super().has_delete_permission(request, obj)


# ── Service Offerings ──────────────────────────────────────────────────────────

@admin.register(ServiceOffering)
class ServiceOfferingAdmin(admin.ModelAdmin):
    list_display    = ('event_name', 'church', 'date', 'first_offering', 'tithe', 'thanksgiving', 'total', 'ledger_posted')
    list_filter     = ('church', 'date')
    search_fields   = ('event_name',)
    date_hierarchy  = 'date'
    readonly_fields = ('recorded_at', 'updated_at', 'ledger_posted', 'total')

    def ledger_posted(self, obj):
        return obj.has_journal_entry
    ledger_posted.boolean = True
    ledger_posted.short_description = 'Posted to Ledger?'


# ── Expense Categories ─────────────────────────────────────────────────────────

@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display  = ('name', 'account', 'color')
    search_fields = ('name',)
    ordering      = ('name',)


# ── Expense Records ────────────────────────────────────────────────────────────

@admin.register(ExpenseRecord)
class ExpenseRecordAdmin(admin.ModelAdmin):
    list_display    = ('title', 'church', 'amount', 'expense_date', 'category', 'fund', 'status', 'created_by', 'approved_by', 'ledger_posted')
    list_filter     = ('church', 'status', 'category', 'fund', 'payment_method')
    search_fields   = ('title', 'description')
    date_hierarchy  = 'expense_date'
    readonly_fields = ('created_at', 'updated_at', 'approved_at', 'ledger_posted')

    def ledger_posted(self, obj):
        return obj.has_journal_entry
    ledger_posted.boolean = True
    ledger_posted.short_description = 'Posted to Ledger?'

    def has_delete_permission(self, request, obj=None):
        if obj and obj.is_approved:
            return False
        return super().has_delete_permission(request, obj)


# ── Funds ──────────────────────────────────────────────────────────────────────

class FundTransactionInline(admin.TabularInline):
    model           = FundTransaction
    extra           = 0
    readonly_fields = ('transaction_type', 'amount', 'description', 'reference_date', 'created_by', 'created_at')
    can_delete      = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Fund)
class FundAdmin(admin.ModelAdmin):
    list_display    = ('code', 'name', 'church', 'status', 'is_restricted', 'assigned_ministry',
                       'opening_balance', 'balance_display', 'total_income_display', 'total_expenses_display')
    list_filter     = ('church', 'status', 'is_restricted', 'funding_source')
    search_fields   = ('name', 'code', 'assigned_ministry')
    readonly_fields = ('created_at', 'updated_at', 'balance_display', 'total_income_display', 'total_expenses_display')
    inlines         = [FundTransactionInline]
    fieldsets = (
        ('Church',          {'fields': ('church',)}),
        ('Fund Configuration', {'fields': ('name', 'code', 'description')}),
        ('Financial Setup', {'fields': ('opening_balance', 'funding_source')}),
        ('Governance',      {'fields': ('is_restricted', 'approval_threshold', 'assigned_ministry', 'status')}),
        ('Audit',           {'fields': ('created_by', 'created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

    def balance_display(self, obj):
        return f"GHS {obj.balance:,.2f}"
    balance_display.short_description = 'Balance'

    def total_income_display(self, obj):
        return f"GHS {obj.total_income:,.2f}"
    total_income_display.short_description = 'Total Inflow'

    def total_expenses_display(self, obj):
        return f"GHS {obj.total_expenses:,.2f}"
    total_expenses_display.short_description = 'Total Outflow'


# ── Audit Log ──────────────────────────────────────────────────────────────────

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display    = ('created_at', 'church', 'user', 'action', 'entity_type', 'entity_id', 'description')
    list_filter     = ('church', 'action', 'entity_type')
    search_fields   = ('description', 'user__username')
    readonly_fields = ('user', 'action', 'entity_type', 'entity_id', 'description', 'old_values', 'new_values', 'created_at')
    date_hierarchy  = 'created_at'

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


# ── Drive Integration ──────────────────────────────────────────────────────────

@admin.register(DriveCredential)
class DriveCredentialAdmin(admin.ModelAdmin):
    list_display    = ('church', 'updated_at', 'created_at')
    readonly_fields = ('token', 'refresh_token', 'token_uri', 'client_id',
                       'client_secret', 'scopes', 'created_at', 'updated_at')
    # Credentials are read-only in admin — managed through the app's OAuth flow
    def has_add_permission(self, request):
        return False


@admin.register(DriveSettings)
class DriveSettingsAdmin(admin.ModelAdmin):
    list_display = ('church', 'folder_name', 'frequency', 'override', 'updated_at')
    list_filter  = ('frequency', 'override')
