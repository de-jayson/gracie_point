"""Finance URL Configuration"""
from django.urls import path
from . import views

app_name = 'finance'

urlpatterns = [
    # ── Dashboard (landing page) ──────────────────────────────────────────────
    path('',                          views.FinanceDashboardView.as_view(),   name='dashboard'),

    # ── Service Offerings ─────────────────────────────────────────────────────
    path('services/',                 views.OfferingListView.as_view(),       name='list'),
    path('add/',                      views.OfferingCreateView.as_view(),     name='create'),
    path('<int:pk>/',                 views.OfferingDetailView.as_view(),     name='detail'),
    path('<int:pk>/edit/',            views.OfferingEditView.as_view(),       name='edit'),
    path('<int:pk>/delete/',          views.OfferingDeleteView.as_view(),     name='delete'),
    path('records/',                  views.RecordsPageView.as_view(),        name='records'),
    path('records/download/',         views.DownloadPDFView.as_view(),        name='download_pdf'),
    path('records/drive-settings/',   views.SaveDriveSettingsView.as_view(), name='drive_settings'),
    path('google/connect/',           views.google_connect,                   name='google_connect'),
    path('google/callback/',          views.google_callback,                  name='google_callback'),
    path('google/disconnect/',        views.google_disconnect,                name='google_disconnect'),
    path('google/status/',            views.google_status,                    name='google_status'),
    path('google/save-now/',          views.drive_save_now,                   name='drive_save_now'),

    # ── Expenses ──────────────────────────────────────────────────────────────
    path('expenses/',                 views.ExpenseListView.as_view(),        name='expense_list'),
    path('expenses/add/',             views.ExpenseCreateView.as_view(),      name='expense_create'),
    path('expenses/<int:pk>/edit/',   views.ExpenseEditView.as_view(),        name='expense_edit'),
    path('expenses/<int:pk>/delete/', views.ExpenseDeleteView.as_view(),      name='expense_delete'),
    path('expenses/<int:pk>/approve/',views.ExpenseApproveView.as_view(),     name='expense_approve'),
    path('expenses/<int:pk>/reject/', views.ExpenseRejectView.as_view(),      name='expense_reject'),

    # ── Funds ─────────────────────────────────────────────────────────────────
    path('funds/',                    views.FundListView.as_view(),           name='fund_list'),
    path('funds/add/',                views.FundCreateView.as_view(),         name='fund_create'),
    path('funds/<int:pk>/',           views.FundDetailView.as_view(),         name='fund_detail'),

    # ── Audit Log ─────────────────────────────────────────────────────────────
    path('audit/',                    views.AuditLogView.as_view(),           name='audit_log'),
]
