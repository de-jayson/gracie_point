"""Attendance URL Configuration"""
from django.urls import path
from . import views

app_name = 'attendance'

urlpatterns = [
    path('', views.AttendanceListView.as_view(), name='list'),
    path('add/', views.AttendanceCreateView.as_view(), name='create'),
    path('<int:pk>/', views.AttendanceDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.AttendanceEditView.as_view(), name='edit'),
    path('<int:pk>/delete/', views.AttendanceDeleteView.as_view(), name='delete'),
]
