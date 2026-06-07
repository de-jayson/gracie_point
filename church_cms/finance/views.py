"""
Finance Views — Zova CMS

URL structure (finance/ prefix):
  /                  → FinanceDashboardView   (landing page)
  /services/         → OfferingListView
  /add/              → OfferingCreateView
  /<pk>/             → OfferingDetailView
  /<pk>/edit/        → OfferingEditView
  /<pk>/delete/      → OfferingDeleteView
  /records/          → RecordsPageView
  /records/download/ → DownloadPDFView
  /expenses/         → ExpenseListView
  /expenses/add/     → ExpenseCreateView
  /expenses/<pk>/edit/    → ExpenseEditView
  /expenses/<pk>/delete/  → ExpenseDeleteView
  /expenses/<pk>/approve/ → ExpenseApproveView
  /expenses/<pk>/reject/  → ExpenseRejectView
  /funds/            → FundListView
  /funds/add/        → FundCreateView
  /funds/<pk>/       → FundDetailView
  /audit/            → AuditLogView
  /google/...        → OAuth views
"""

import io
import json
import os
from datetime import date
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views import View
from django.conf import settings

from accounts.decorators import finance_required
from .forms import ServiceOfferingForm, ExpenseForm, ExpenseApprovalForm, FundForm
from .models import (
    ServiceOffering, ExpenseRecord, ExpenseCategory,
    Fund, AuditLog,
)
from .posting_service import PostingService, ExpenseService, AuditService

from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google.oauth2.credentials import Credentials
from .drive import get_credentials, save_credentials, delete_credentials, is_connected
from .models import DriveSettings

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

GOOGLE_CLIENT_SECRETS_FILE = os.path.join(settings.BASE_DIR, 'client_secret.json')
SCOPES       = ['https://www.googleapis.com/auth/drive.file']
REDIRECT_URI = 'http://127.0.0.1:8000/finance/google/callback/'


# ─────────────────────────────────────────────────────────────────────────────
# PDF BUILDER
# ─────────────────────────────────────────────────────────────────────────────

def _build_pdf(records, title="Financial Records", church_name="Church"):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm, topMargin=20*mm, bottomMargin=20*mm)

    styles = getSampleStyleSheet()
    DARK  = colors.HexColor('#0e1015')
    GREEN = colors.HexColor('#22c55e')
    MID   = colors.HexColor('#3f4a5a')
    WHITE = colors.white

    title_style = ParagraphStyle('T', parent=styles['Title'], textColor=DARK, fontSize=18, spaceAfter=4)
    sub_style   = ParagraphStyle('S', parent=styles['Normal'], textColor=colors.HexColor('#6b7280'), fontSize=9, spaceAfter=12)

    grand_total = sum(r.total for r in records)
    story = [
        Paragraph(church_name, title_style),
        Paragraph(f"{title}  •  Generated {date.today().strftime('%d %B %Y')}", sub_style),
    ]

    summary = Table([['Total Records', 'Grand Total'], [str(len(records)), f"GHS {grand_total:,.2f}"]], colWidths=[84*mm, 84*mm])
    summary.setStyle(TableStyle([
        ('BACKGROUND', (0,0),(-1,0), GREEN), ('TEXTCOLOR', (0,0),(-1,0), WHITE),
        ('FONTNAME',   (0,0),(-1,0), 'Helvetica-Bold'), ('FONTSIZE', (0,0),(-1,0), 9),
        ('BACKGROUND', (0,1),(-1,1), colors.HexColor('#f0fdf4')),
        ('FONTNAME',   (0,1),(-1,1), 'Helvetica-Bold'), ('FONTSIZE', (0,1),(-1,1), 13),
        ('ALIGN',      (0,0),(-1,-1), 'CENTER'), ('VALIGN', (0,0),(-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0),(-1,-1), 8), ('BOTTOMPADDING', (0,0),(-1,-1), 8),
        ('GRID',       (0,0),(-1,-1), 0.5, colors.HexColor('#d1fae5')),
    ]))
    story += [summary, Spacer(1, 8*mm)]

    for rec in records:
        story += [
            Paragraph(rec.event_name, ParagraphStyle('RH', parent=styles['Heading2'], textColor=DARK, fontSize=11, spaceBefore=6, spaceAfter=2)),
            Paragraph(rec.date.strftime('%A, %d %B %Y'), sub_style),
        ]
        rows = [['Category', 'Amount (GHS)']]
        for label, val in [
            ('1st Offering', rec.first_offering), ('2nd Offering', rec.second_offering),
            ('JY Offering', rec.jy_offering), ("Children's Service Offering", rec.children_offering),
            ('Tithe', rec.tithe), ('Thanksgiving', rec.thanksgiving),
        ]:
            if val > 0: rows.append([label, f"{val:,.2f}"])
        if rec.other_amount > 0:
            rows.append([f"Other ({rec.other_description})" if rec.other_description else "Other", f"{rec.other_amount:,.2f}"])
        rows.append(['TOTAL', f"{rec.total:,.2f}"])

        t = Table(rows, colWidths=[120*mm, 48*mm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0),(-1,0), MID), ('TEXTCOLOR', (0,0),(-1,0), WHITE),
            ('FONTNAME',   (0,0),(-1,0), 'Helvetica-Bold'), ('FONTSIZE', (0,0),(-1,-1), 9),
            ('ALIGN',      (1,0),(1,-1), 'RIGHT'),
            ('ROWBACKGROUNDS', (0,1),(-1,-2), [WHITE, colors.HexColor('#f8fafc')]),
            ('BACKGROUND', (0,-1),(-1,-1), colors.HexColor('#ecfdf5')),
            ('FONTNAME',   (0,-1),(-1,-1), 'Helvetica-Bold'),
            ('TEXTCOLOR',  (0,-1),(-1,-1), colors.HexColor('#166534')),
            ('TOPPADDING', (0,0),(-1,-1), 5), ('BOTTOMPADDING', (0,0),(-1,-1), 5),
            ('LEFTPADDING',(0,0),(-1,-1), 8), ('RIGHTPADDING',  (0,0),(-1,-1), 8),
            ('LINEBELOW',  (0,0),(-1,-2), 0.3, colors.HexColor('#e2e8f0')),
            ('BOX',        (0,0),(-1,-1), 0.5, colors.HexColor('#d1d5db')),
        ]))
        story.append(t)
        if rec.notes:
            story += [Spacer(1,2*mm), Paragraph(f"<i>Note: {rec.notes}</i>",
                ParagraphStyle('N', parent=styles['Normal'], textColor=colors.HexColor('#6b7280'), fontSize=8))]
        story.append(Spacer(1, 6*mm))

    doc.build(story)
    buf.seek(0)
    return buf


# ─────────────────────────────────────────────────────────────────────────────
# GOOGLE DRIVE HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _credentials_from_session(session):
    # DEPRECATED — kept for safety, no longer used.
    # Credentials are now stored in DriveCredential (DB), not the session.
    return None

def _get_or_create_drive_folder(service, folder_name):
    results = service.files().list(
        q=f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false",
        fields='files(id)',
    ).execute()
    files = results.get('files', [])
    if files:
        return files[0]['id']
    return service.files().create(
        body={'name': folder_name, 'mimeType': 'application/vnd.google-apps.folder'},
        fields='id',
    ).execute()['id']


# ─────────────────────────────────────────────────────────────────────────────
# FINANCE DASHBOARD  (landing page at /finance/)
# ─────────────────────────────────────────────────────────────────────────────

@method_decorator(login_required, name='dispatch')
class FinanceDashboardView(View):
    template_name = 'finance/dashboard.html'

    def get(self, request):
        offerings  = ServiceOffering.objects.filter(church=request.user.church)
        expenses   = ExpenseRecord.objects.filter(church=request.user.church)
        funds      = Fund.objects.filter(church=request.user.church, status=Fund.STATUS_ACTIVE)

        total_income   = sum(r.total for r in offerings)
        total_expenses = expenses.filter(status='approved').aggregate(s=Sum('amount'))['s'] or 0
        cash_available = total_income - total_expenses
        pending_count  = expenses.filter(status='pending').count()

        # Recent activity (last 8 items combined, sorted by date)
        recent_offerings = list(offerings.order_by('-date')[:5])
        recent_expenses  = list(expenses.filter(status='approved').order_by('-expense_date')[:5])

        # Monthly income — last 6 months
        from django.db.models.functions import TruncMonth
        monthly_income = (
            ServiceOffering.objects
            .filter(church=request.user.church)
            .annotate(month=TruncMonth('date'))
            .values('month')
            .annotate(total=Sum('first_offering') + Sum('second_offering') +
                            Sum('jy_offering') + Sum('children_offering') +
                            Sum('tithe') + Sum('thanksgiving') + Sum('other_amount'))
            .order_by('month')
        )

        return render(request, self.template_name, {
            'total_income':    total_income,
            'total_expenses':  total_expenses,
            'cash_available':  cash_available,
            'pending_count':   pending_count,
            'funds':           funds,
            'recent_offerings': recent_offerings,
            'recent_expenses':  recent_expenses,
            'monthly_income':   list(monthly_income),
            'active_tab':       'overview',
        })


# ─────────────────────────────────────────────────────────────────────────────
# SERVICE OFFERINGS
# ─────────────────────────────────────────────────────────────────────────────

@method_decorator(login_required, name='dispatch')
class OfferingListView(View):
    template_name = 'finance/offering_list.html'

    def get(self, request):
        records     = ServiceOffering.objects.filter(church=request.user.church)
        grand_total = sum(r.total for r in records)
        return render(request, self.template_name, {
            'records':    records,
            'grand_total': grand_total,
            'active_tab': 'services',
        })


@method_decorator([login_required, finance_required], name='dispatch')
class OfferingCreateView(View):
    template_name = 'finance/offering_form.html'

    def get(self, request):
        return render(request, self.template_name, {
            'form': ServiceOfferingForm(), 'title': 'Record Service Finances', 'active_tab': 'services',
        })

    def post(self, request):
        form = ServiceOfferingForm(request.POST)
        if form.is_valid():
            record             = form.save(commit=False)
            record.recorded_by = request.user
            record.church      = request.user.church    # auto-assign church
            record.save()
            try:
                PostingService.post_service_income(record, request.user)
            except ValueError as e:
                messages.warning(request, f'Record saved but accounting entry failed: {e}')
            messages.success(request, f'Finances for "{record.event_name}" saved. Total: GHS {record.total:,.2f}')
            return redirect('finance:list')
        messages.error(request, 'Please correct the errors below.')
        return render(request, self.template_name, {
            'form': form, 'title': 'Record Service Finances', 'active_tab': 'services',
        })


@method_decorator([login_required, finance_required], name='dispatch')
class OfferingEditView(View):
    template_name = 'finance/offering_form.html'

    def get(self, request, pk):
        record = get_object_or_404(ServiceOffering, pk=pk, church=request.user.church)
        return render(request, self.template_name, {
            'form': ServiceOfferingForm(instance=record), 'title': 'Edit Record',
            'record': record, 'active_tab': 'services',
        })

    def post(self, request, pk):
        record = get_object_or_404(ServiceOffering, pk=pk, church=request.user.church)
        form   = ServiceOfferingForm(request.POST, instance=record)
        if form.is_valid():
            record = form.save(commit=False)
            record.save()
            try:
                PostingService.post_service_income(record, request.user)
            except ValueError as e:
                messages.warning(request, f'Record updated but accounting re-post failed: {e}')
            messages.success(request, 'Record updated.')
            return redirect('finance:list')
        return render(request, self.template_name, {
            'form': form, 'title': 'Edit Record', 'record': record, 'active_tab': 'services',
        })


@method_decorator([login_required, finance_required], name='dispatch')
class OfferingDeleteView(View):
    def post(self, request, pk):
        record = get_object_or_404(ServiceOffering, pk=pk, church=request.user.church)
        try:
            PostingService.reverse_service_income(record, request.user)
        except Exception:
            pass
        record.delete()
        messages.success(request, 'Record deleted.')
        return redirect('finance:list')


@method_decorator(login_required, name='dispatch')
class OfferingDetailView(View):
    template_name = 'finance/offering_detail.html'

    def get(self, request, pk):
        record = get_object_or_404(ServiceOffering, pk=pk, church=request.user.church)
        return render(request, self.template_name, {
            'record':        record,
            'journal_entry': getattr(record, 'journal_entry', None),
            'active_tab':    'services',
        })


# ─────────────────────────────────────────────────────────────────────────────
# RECORDS & PDF / DRIVE
# ─────────────────────────────────────────────────────────────────────────────

@method_decorator(login_required, name='dispatch')
class RecordsPageView(View):
    template_name = 'finance/records.html'

    def get(self, request):
        records   = ServiceOffering.objects.filter(church=request.user.church)
        date_from = request.GET.get('date_from', '')
        date_to   = request.GET.get('date_to', '')
        if date_from: records = records.filter(date__gte=date_from)
        if date_to:   records = records.filter(date__lte=date_to)
        return render(request, self.template_name, {
            'records':     records,
            'grand_total': sum(r.total for r in records),
            'date_from':   date_from,
            'date_to':     date_to,
            'active_tab':  'records',
        })


@method_decorator(login_required, name='dispatch')
class DownloadPDFView(View):
    def get(self, request):
        records   = ServiceOffering.objects.filter(church=request.user.church)
        date_from = request.GET.get('date_from')
        date_to   = request.GET.get('date_to')
        if date_from: records = records.filter(date__gte=date_from)
        if date_to:   records = records.filter(date__lte=date_to)
        title = "Financial Records"
        if date_from or date_to:
            title = f"Financial Records ({date_from or '...'} to {date_to or '...'})"
        buf = _build_pdf(list(records), title=title, church_name=request.user.church.name)
        response = HttpResponse(buf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{request.user.church.name.lower().replace(" ", "_")}_finance_{date.today().isoformat()}.pdf"'
        return response


@method_decorator(login_required, name='dispatch')
class SaveDriveSettingsView(View):
    def post(self, request):
        data = json.loads(request.body)
        # Save Drive settings to DB — survives logout and session clears
        DriveSettings.objects.update_or_create(
            church=request.user.church,
            defaults={
                'folder_name': data.get('folder_name', request.user.church.name + ' Records'),
                'frequency':   data.get('frequency', 'monthly'),
                'override':    data.get('override', True),
            },
        )
        return JsonResponse({'status': 'ok'})


# ─────────────────────────────────────────────────────────────────────────────
# GOOGLE DRIVE OAUTH
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def google_connect(request):
    # Guard: user must belong to a church to connect Drive
    if not request.user.church:
        messages.error(request, 'Your account is not linked to a church. Contact your administrator.')
        return redirect('finance:records')

    flow = Flow.from_client_secrets_file(GOOGLE_CLIENT_SECRETS_FILE, scopes=SCOPES,
        redirect_uri=REDIRECT_URI, autogenerate_code_verifier=False)
    auth_url, state = flow.authorization_url(prompt='consent', access_type='offline', include_granted_scopes='true')
    # Store state in session temporarily — only needed during the OAuth handshake
    request.session['oauth_state']    = state
    request.session['oauth_church_id'] = str(request.user.church.id)
    return redirect(auth_url)


@login_required
def google_callback(request):
    # Guard: user must belong to a church
    if not request.user.church:
        messages.error(request, 'Your account is not linked to a church.')
        return redirect('finance:records')

    flow = Flow.from_client_secrets_file(GOOGLE_CLIENT_SECRETS_FILE, scopes=SCOPES,
        state=request.session.get('oauth_state'), redirect_uri=REDIRECT_URI, autogenerate_code_verifier=False)
    flow.fetch_token(authorization_response=request.build_absolute_uri())
    creds = flow.credentials
    # Save tokens to DB tied to this church — survives logout and session clears
    save_credentials(request.user.church, creds)
    # Clean up the temporary OAuth state from session
    request.session.pop('oauth_state', None)
    request.session.pop('oauth_church_id', None)
    messages.success(request, 'Google Drive connected successfully.')
    return redirect('finance:records')


@login_required
def google_disconnect(request):
    if request.user.church:
        delete_credentials(request.user.church)
    # Also clean session just in case
    request.session.pop('google_credentials', None)
    request.session.pop('oauth_state', None)
    messages.info(request, 'Google Drive disconnected.')
    return redirect('finance:records')


@login_required
def google_status(request):
    if not request.user.church:
        return JsonResponse({'connected': False})
    return JsonResponse({'connected': is_connected(request.user.church)})


@login_required
def drive_save_now(request):
    if not request.user.church:
        return JsonResponse({'status': 'error', 'error': 'Account not linked to a church.'}, status=400)
    creds = get_credentials(request.user.church)
    if not creds:
        return JsonResponse({'status': 'error', 'error': 'Google Drive not connected.'}, status=400)
    records   = ServiceOffering.objects.filter(church=request.user.church)
    date_from = request.GET.get('date_from')
    date_to   = request.GET.get('date_to')
    if date_from: records = records.filter(date__gte=date_from)
    if date_to:   records = records.filter(date__lte=date_to)
    church_name = request.user.church.name.lower().replace(' ', '_')
    filename    = f'{church_name}_finance_records.pdf' if override else f'{church_name}_finance_{date.today().isoformat()}.pdf'
    drive_cfg   = DriveSettings.objects.filter(church=request.user.church).first()
    folder_name = drive_cfg.folder_name if drive_cfg else request.user.church.name + ' Records'
    override    = drive_cfg.override if drive_cfg else True
    try:
        service   = build('drive', 'v3', credentials=creds)
        folder_id = _get_or_create_drive_folder(service, folder_name)
        pdf_buf   = _build_pdf(list(records), church_name=request.user.church.name)
        existing  = service.files().list(
            q=f"name='{filename}' and '{folder_id}' in parents and trashed=false", fields='files(id)',
        ).execute().get('files', []) if override else []
        media = MediaIoBaseUpload(pdf_buf, mimetype='application/pdf', resumable=True)
        if override and existing:
            service.files().update(fileId=existing[0]['id'], media_body=media).execute()
        else:
            service.files().create(body={'name': filename, 'parents': [folder_id]}, media_body=media, fields='id').execute()
        save_credentials(request.user.church, creds)  # persist refreshed token
        return JsonResponse({'status': 'ok', 'filename': filename, 'folder': folder_name})
    except Exception as e:
        return JsonResponse({'status': 'error', 'error': str(e)}, status=500)


# ─────────────────────────────────────────────────────────────────────────────
# EXPENSES
# ─────────────────────────────────────────────────────────────────────────────

@method_decorator(login_required, name='dispatch')
class ExpenseListView(View):
    template_name = 'finance/expense_list.html'

    def get(self, request):
        expenses = ExpenseRecord.objects.filter(church=request.user.church).select_related('category', 'fund', 'created_by', 'related_service')

        status_filter   = request.GET.get('status', '')
        category_filter = request.GET.get('category', '')
        date_from       = request.GET.get('date_from', '')
        date_to         = request.GET.get('date_to', '')

        if status_filter:   expenses = expenses.filter(status=status_filter)
        if category_filter: expenses = expenses.filter(category_id=category_filter)
        if date_from:       expenses = expenses.filter(expense_date__gte=date_from)
        if date_to:         expenses = expenses.filter(expense_date__lte=date_to)

        all_expenses   = ExpenseRecord.objects.filter(church=request.user.church)
        total_all      = all_expenses.aggregate(s=Sum('amount'))['s'] or 0
        total_approved = all_expenses.filter(status='approved').aggregate(s=Sum('amount'))['s'] or 0
        total_pending  = all_expenses.filter(status='pending').aggregate(s=Sum('amount'))['s'] or 0
        pending_count  = all_expenses.filter(status='pending').count()

        return render(request, self.template_name, {
            'expenses':        expenses,
            'categories':      ExpenseCategory.objects.all().order_by('name'),
            'status_choices':  ExpenseRecord.STATUS_CHOICES,
            'status_filter':   status_filter,
            'category_filter': category_filter,
            'date_from':       date_from,
            'date_to':         date_to,
            'total_all':       total_all,
            'total_approved':  total_approved,
            'total_pending':   total_pending,
            'pending_count':   pending_count,
            'active_tab':      'expenses',
        })


@method_decorator([login_required, finance_required], name='dispatch')
class ExpenseCreateView(View):
    template_name = 'finance/expense_form.html'

    def get(self, request):
        return render(request, self.template_name, {
            'form': ExpenseForm(church=request.user.church), 'title': 'Record Expense', 'active_tab': 'expenses',
        })

    def post(self, request):
        form = ExpenseForm(request.POST, request.FILES, church=request.user.church)
        if form.is_valid():
            expense            = form.save(commit=False)
            expense.created_by = request.user
            expense.church     = request.user.church    # auto-assign church
            expense.status     = ExpenseRecord.STATUS_PENDING
            expense.save()
            AuditService.log(
                user=request.user, action='expense_created',
                entity_type='ExpenseRecord', entity_id=expense.pk,
                description=f'Expense "{expense.title}" created for GHS {expense.amount}.',
                new_values={'title': expense.title, 'amount': str(expense.amount), 'status': 'pending'},
            )
            messages.success(request, f'Expense "{expense.title}" submitted for approval.')
            return redirect('finance:expense_list')
        messages.error(request, 'Please correct the errors below.')
        return render(request, self.template_name, {
            'form': form, 'title': 'Record Expense', 'active_tab': 'expenses',
        })


@method_decorator([login_required, finance_required], name='dispatch')
class ExpenseEditView(View):
    template_name = 'finance/expense_form.html'

    def get(self, request, pk):
        expense = get_object_or_404(ExpenseRecord, pk=pk, church=request.user.church)
        if not expense.is_pending:
            messages.warning(request, 'Only pending expenses can be edited.')
            return redirect('finance:expense_list')
        return render(request, self.template_name, {
            'form': ExpenseForm(instance=expense, church=request.user.church), 'title': 'Edit Expense',
            'expense': expense, 'active_tab': 'expenses',
        })

    def post(self, request, pk):
        expense = get_object_or_404(ExpenseRecord, pk=pk, church=request.user.church)
        if not expense.is_pending:
            messages.warning(request, 'Only pending expenses can be edited.')
            return redirect('finance:expense_list')
        form = ExpenseForm(request.POST, request.FILES, instance=expense, church=request.user.church)
        if form.is_valid():
            form.save()
            messages.success(request, 'Expense updated.')
            return redirect('finance:expense_list')
        return render(request, self.template_name, {
            'form': form, 'title': 'Edit Expense', 'expense': expense, 'active_tab': 'expenses',
        })


@method_decorator([login_required, finance_required], name='dispatch')
class ExpenseDeleteView(View):
    def post(self, request, pk):
        expense = get_object_or_404(ExpenseRecord, pk=pk, church=request.user.church)
        if expense.is_approved:
            messages.error(request, 'Approved expenses cannot be deleted.')
            return redirect('finance:expense_list')
        AuditService.log(
            user=request.user, action='expense_deleted',
            entity_type='ExpenseRecord', entity_id=expense.pk,
            description=f'Expense "{expense.title}" (GHS {expense.amount}) deleted.',
        )
        expense.delete()
        messages.success(request, 'Expense deleted.')
        return redirect('finance:expense_list')


@method_decorator([login_required, finance_required], name='dispatch')
class ExpenseApproveView(View):
    template_name = 'finance/expense_approve.html'

    def get(self, request, pk):
        expense = get_object_or_404(ExpenseRecord, pk=pk, church=request.user.church, status=ExpenseRecord.STATUS_PENDING)
        return render(request, self.template_name, {
            'expense': expense, 'form': ExpenseApprovalForm(),
            'action': 'approve', 'active_tab': 'expenses',
        })

    def post(self, request, pk):
        expense = get_object_or_404(ExpenseRecord, pk=pk, church=request.user.church, status=ExpenseRecord.STATUS_PENDING)
        form    = ExpenseApprovalForm(request.POST)
        if form.is_valid():
            try:
                ExpenseService.approve_expense(expense, request.user, note=form.cleaned_data.get('note', ''))
                messages.success(request, f'"{expense.title}" approved and posted to ledger.')
            except ValueError as e:
                messages.error(request, str(e))
        return redirect('finance:expense_list')


@method_decorator([login_required, finance_required], name='dispatch')
class ExpenseRejectView(View):
    template_name = 'finance/expense_approve.html'

    def get(self, request, pk):
        expense = get_object_or_404(ExpenseRecord, pk=pk, church=request.user.church, status=ExpenseRecord.STATUS_PENDING)
        return render(request, self.template_name, {
            'expense': expense, 'form': ExpenseApprovalForm(),
            'action': 'reject', 'active_tab': 'expenses',
        })

    def post(self, request, pk):
        expense = get_object_or_404(ExpenseRecord, pk=pk, church=request.user.church, status=ExpenseRecord.STATUS_PENDING)
        form    = ExpenseApprovalForm(request.POST)
        if form.is_valid():
            ExpenseService.reject_expense(expense, request.user, note=form.cleaned_data.get('note', ''))
            messages.success(request, f'"{expense.title}" rejected.')
        return redirect('finance:expense_list')


# ─────────────────────────────────────────────────────────────────────────────
# FUNDS
# ─────────────────────────────────────────────────────────────────────────────

@method_decorator(login_required, name='dispatch')
class FundListView(View):
    template_name = 'finance/fund_list.html'

    def get(self, request):
        status_filter = request.GET.get('status', '')
        funds = Fund.objects.filter(church=request.user.church)
        if status_filter:
            funds = funds.filter(status=status_filter)
        else:
            funds = funds.exclude(status='archived')  # hide archived by default
        return render(request, self.template_name, {
            'funds': funds,
            'active_tab': 'funds',
            'status_filter': status_filter,
            'status_choices': Fund.STATUS_CHOICES,
        })


@method_decorator([login_required, finance_required], name='dispatch')
class FundCreateView(View):
    template_name = 'finance/fund_form.html'

    def get(self, request):
        return render(request, self.template_name, {
            'form': FundForm(), 'title': 'Create Fund', 'active_tab': 'funds',
        })

    def post(self, request):
        form = FundForm(request.POST)
        if form.is_valid():
            fund            = form.save(commit=False)
            fund.created_by = request.user
            fund.church     = request.user.church    # auto-assign church
            fund.save()

    # Seed opening balance as a credit transaction so it shows in history
            
        from .posting_service import AuditService
        AuditService.log(
            user=request.user, action='fund_credited',
            entity_type='Fund', entity_id=fund.pk,
            description=f'Fund "{fund.name}" ({fund.code}) created with opening balance GHS {fund.opening_balance}.',
        )

        messages.success(request, f'Fund "{fund.name}" created.')
        return redirect('finance:fund_detail', pk=fund.pk)  # → detail, not list
        return render(request, self.template_name, {
            'form': form, 'title': 'Create Fund', 'active_tab': 'funds',
        })


@method_decorator(login_required, name='dispatch')
class FundDetailView(View):
    template_name = 'finance/fund_detail.html'

    def get(self, request, pk):
        fund         = get_object_or_404(Fund, pk=pk, church=request.user.church)
        active_inner = request.GET.get('tab', 'transactions')  # inner tabs
        transactions = fund.transactions.order_by('-reference_date')
        expenses_all = fund.expenses.select_related('category', 'created_by').order_by('-expense_date')
        expenses_approved = expenses_all.filter(status='approved')
        expenses_pending  = expenses_all.filter(status='pending')
        audit_logs   = AuditLog.objects.filter(entity_type='Fund', entity_id=fund.pk).order_by('-created_at')[:30]

        return render(request, self.template_name, {
            'fund':               fund,
            'transactions':       transactions[:20],
            'expenses':           expenses_approved[:20],
            'expenses_pending':   expenses_pending,
            'audit_logs':         audit_logs,
            'active_tab':         'funds',
            'active_inner':       active_inner,
            'pending_exp_count':  expenses_pending.count(),
        })


# ─────────────────────────────────────────────────────────────────────────────
# AUDIT LOG
# ─────────────────────────────────────────────────────────────────────────────

@method_decorator([login_required, finance_required], name='dispatch')
class AuditLogView(View):
    template_name = 'finance/audit_log.html'

    def get(self, request):
        logs = AuditLog.objects.filter(church=request.user.church).select_related('user').order_by('-created_at')[:100]
        return render(request, self.template_name, {'logs': logs, 'active_tab': 'records'})
