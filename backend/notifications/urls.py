from django.urls import path
from .views import (
    NotificationListView,
    MarkNotificationReadView,
    MarkAllReadView,
    ClearAllNotificationsView,
    UnreadCountView
)

urlpatterns = [
    path('notifications/',                NotificationListView.as_view(),       name='notifications'),
    path('notifications/unread-count/',   UnreadCountView.as_view(),            name='unread_count'),
    path('notifications/mark-all-read/',  MarkAllReadView.as_view(),            name='mark_all_read'),
    path('notifications/clear/',          ClearAllNotificationsView.as_view(),  name='clear_notifications'),
    path('notifications/<int:pk>/read/',  MarkNotificationReadView.as_view(),   name='mark_read'),
]

# Routes:
# GET    /api/notifications/                  → list all notifications
# GET    /api/notifications/?unread=true      → unread only
# GET    /api/notifications/unread-count/     → just the count for bell icon
# PATCH  /api/notifications/mark-all-read/   → mark all as read
# DELETE /api/notifications/clear/           → clear all
# PATCH  /api/notifications/:id/read/        → mark one as read