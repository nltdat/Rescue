from django.urls import path
from .views import (
    IncidentListView,
    IncidentCreateView,
    IncidentDetailView,
    IncidentUpdateView,
    IncidentDeleteView,
    ImageUploadView,
)

app_name = 'incidents'

urlpatterns = [
    path('', IncidentListView.as_view(), name='incident-list'),
    path('create/', IncidentCreateView.as_view(), name='incident-create'),
    path('<int:pk>/', IncidentDetailView.as_view(), name='incident-detail'),
    path('<int:pk>/update/', IncidentUpdateView.as_view(), name='incident-update'),
    path('<int:pk>/delete/', IncidentDeleteView.as_view(), name='incident-delete'),
    path('upload-images/', ImageUploadView.as_view(), name='upload-images'),
]
