"""Finance Forms"""

from django import forms
from .models import ServiceOffering, ExpenseRecord, ExpenseCategory, Fund

INPUT_CLASS  = 'w-full bg-zinc-800 border border-zinc-700 rounded-lg px-4 py-3 text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500'
MONEY_CLASS  = 'w-full bg-zinc-800 border border-zinc-700 rounded-lg px-4 py-3 text-zinc-100 text-right font-semibold placeholder-zinc-600 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500'
SELECT_CLASS = 'w-full bg-zinc-800 border border-zinc-700 rounded-lg px-4 py-3 text-zinc-100 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500'


# ── Service Offering ──────────────────────────────────────────────────────────

class ServiceOfferingForm(forms.ModelForm):
    class Meta:
        model  = ServiceOffering
        fields = [
            'event_name', 'date',
            'first_offering', 'second_offering',
            'jy_offering', 'children_offering',
            'tithe', 'thanksgiving',
            'other_amount', 'other_description',
            'notes',
        ]
        widgets = {
            'event_name':        forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'e.g. Sunday Service – 4th May 2025'}),
            'date':              forms.DateInput(attrs={'class': INPUT_CLASS, 'type': 'date'}),
            'first_offering':    forms.NumberInput(attrs={'class': MONEY_CLASS, 'min': 0, 'step': '0.01', 'placeholder': '0.00'}),
            'second_offering':   forms.NumberInput(attrs={'class': MONEY_CLASS, 'min': 0, 'step': '0.01', 'placeholder': '0.00'}),
            'jy_offering':       forms.NumberInput(attrs={'class': MONEY_CLASS, 'min': 0, 'step': '0.01', 'placeholder': '0.00'}),
            'children_offering': forms.NumberInput(attrs={'class': MONEY_CLASS, 'min': 0, 'step': '0.01', 'placeholder': '0.00'}),
            'tithe':             forms.NumberInput(attrs={'class': MONEY_CLASS, 'min': 0, 'step': '0.01', 'placeholder': '0.00'}),
            'thanksgiving':      forms.NumberInput(attrs={'class': MONEY_CLASS, 'min': 0, 'step': '0.01', 'placeholder': '0.00'}),
            'other_amount':      forms.NumberInput(attrs={'class': MONEY_CLASS, 'min': 0, 'step': '0.01', 'placeholder': '0.00'}),
            'other_description': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Specify (e.g. Building Fund, Welfare...)'}),
            'notes':             forms.Textarea(attrs={'class': INPUT_CLASS, 'rows': 3, 'placeholder': "Any extra notes about this service's finances..."}),
        }


# ── Expense Forms ─────────────────────────────────────────────────────────────

class ExpenseForm(forms.ModelForm):
    class Meta:
        model  = ExpenseRecord
        fields = [
            'title', 'amount', 'expense_date',
            'category', 'fund', 'related_service',
            'payment_method', 'description',
            'receipt_url',
        ]
        widgets = {
            'title':           forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'e.g. Sound system repair'}),
            'amount':          forms.NumberInput(attrs={'class': MONEY_CLASS, 'min': 0, 'step': '0.01', 'placeholder': '0.00'}),
            'expense_date':    forms.DateInput(attrs={'class': INPUT_CLASS, 'type': 'date'}),
            'category':        forms.Select(attrs={'class': SELECT_CLASS}),
            'fund':            forms.Select(attrs={'class': SELECT_CLASS}),
            'related_service': forms.Select(attrs={'class': SELECT_CLASS}),
            'payment_method':  forms.Select(attrs={'class': SELECT_CLASS}),
            'description':     forms.Textarea(attrs={'class': INPUT_CLASS, 'rows': 3, 'placeholder': 'Details about this expense...'}),
            'receipt_url':     forms.ClearableFileInput(attrs={'class': INPUT_CLASS}),
        }

    def __init__(self, *args, **kwargs):
        # church kwarg scopes funds and services — categories are global
        church = kwargs.pop('church', None)
        super().__init__(*args, **kwargs)

        # Categories are global — same list for every church
        self.fields['category'].queryset = ExpenseCategory.objects.all().order_by('name')

        if church:
            self.fields['fund'].queryset            = Fund.objects.filter(church=church, status=Fund.STATUS_ACTIVE).order_by('name')
            self.fields['related_service'].queryset = ServiceOffering.objects.filter(church=church).order_by('-date')[:50]
        else:
            self.fields['fund'].queryset            = Fund.objects.none()
            self.fields['related_service'].queryset = ServiceOffering.objects.none()

        self.fields['category'].empty_label        = '— Select Category —'
        self.fields['fund'].empty_label            = '— Select Fund (optional) —'
        self.fields['fund'].required               = False
        self.fields['related_service'].empty_label = '— Link to Service (optional) —'
        self.fields['related_service'].required    = False


class ExpenseApprovalForm(forms.Form):
    """Used by the approve/reject views."""
    note = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': INPUT_CLASS,
            'rows': 3,
            'placeholder': 'Add a note (optional)...',
        }),
        label='Note',
    )


# ── Fund Form ─────────────────────────────────────────────────────────────────

class FundForm(forms.ModelForm):
    class Meta:
        model  = Fund
        fields = [
            'name', 'description',
            'opening_balance', 'funding_source',
            'is_restricted', 'approval_threshold', 'assigned_ministry', 'status',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': INPUT_CLASS, 'placeholder': 'e.g. Building Fund',
            }),
            'description': forms.Textarea(attrs={
                'class': INPUT_CLASS, 'rows': 3, 'placeholder': 'What is this fund for?',
            }),
            'opening_balance': forms.NumberInput(attrs={
                'class': MONEY_CLASS, 'min': 0, 'step': '0.01', 'placeholder': '0.00',
            }),
            'funding_source': forms.Select(attrs={'class': SELECT_CLASS}),
            'is_restricted':  forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 rounded border-zinc-600 bg-zinc-800 text-emerald-500 focus:ring-emerald-500',
            }),
            'approval_threshold': forms.NumberInput(attrs={
                'class': MONEY_CLASS, 'min': 0, 'step': '0.01',
                'placeholder': 'e.g. 5000.00 (leave blank to disable)',
            }),
            'assigned_ministry': forms.TextInput(attrs={
                'class': INPUT_CLASS, 'placeholder': 'e.g. Youth Ministry, Media Team',
            }),
            'status': forms.Select(attrs={'class': SELECT_CLASS}),
        }
