from django.urls import path
from .views import (
    # Rescuer APIs
    RescuerProfileView,
    RescuerStatusUpdateView,
    # Team APIs
    TeamListView,
    TeamCreateView,
    TeamDetailView,
    TeamMembersView,
    # Membership APIs
    JoinTeamView,
    ApproveMembershipView,
    LeaveTeamView,
    # Notification APIs
    NotificationListView,
    MarkNotificationReadView,
    MarkAllNotificationsReadView,
)

app_name = 'teams'

urlpatterns = [
    # Rescuer endpoints
    path('rescuers/profile/<int:user_id>/', RescuerProfileView.as_view(), name='rescuer-profile'),
    path('rescuers/status/', RescuerStatusUpdateView.as_view(), name='rescuer-status'),

    # Team endpoints
    path('teams/', TeamListView.as_view(), name='team-list'),
    path('teams/create/', TeamCreateView.as_view(), name='team-create'),
    path('teams/<int:pk>/', TeamDetailView.as_view(), name='team-detail'),
    path('teams/<int:pk>/members/', TeamMembersView.as_view(), name='team-members'),

    # Membership endpoints
    path('teams/<int:pk>/join/', JoinTeamView.as_view(), name='team-join'),
    path('teams/membership/<int:membership_id>/', ApproveMembershipView.as_view(), name='membership-approve'),
    path('teams/<int:pk>/leave/', LeaveTeamView.as_view(), name='team-leave'),

    # Notification endpoints
    path('notifications/', NotificationListView.as_view(), name='notification-list'),
    path('notifications/<int:pk>/read/', MarkNotificationReadView.as_view(), name='notification-read'),
    path('notifications/read-all/', MarkAllNotificationsReadView.as_view(), name='notification-read-all'),
]
