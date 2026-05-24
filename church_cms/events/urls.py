"""Events URL Configuration"""

from django.urls import path
from . import views

app_name = 'events'

urlpatterns = [
    path('', views.EventListView.as_view(), name='list'),
    path('<int:pk>/', views.EventDetailView.as_view(), name='detail'),
    path('add/', views.EventCreateView.as_view(), name='create'),
    path('<int:pk>/edit/', views.EventEditView.as_view(), name='edit'),
    path('<int:pk>/delete/', views.EventDeleteView.as_view(), name='delete'),
]
