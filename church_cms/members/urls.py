"""Members URL Configuration"""

from django.urls import path
from . import views

app_name = 'members'

urlpatterns = [
    path('', views.MemberListView.as_view(), name='list'),
    path('<int:pk>/', views.MemberDetailView.as_view(), name='detail'),
    path('add/', views.MemberCreateView.as_view(), name='create'),
    path('<int:pk>/edit/', views.MemberEditView.as_view(), name='edit'),
    path('<int:pk>/delete/', views.MemberDeleteView.as_view(), name='delete'),
]
