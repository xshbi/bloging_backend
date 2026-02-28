from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CommentViewSet

router = DefaultRouter()
router.register('comments', CommentViewSet, basename='comment')

urlpatterns = [
    path('', include(router.urls)),
]

# This auto generates:
# GET    /api/comments/              → list comments (filter by ?post=slug)
# POST   /api/comments/              → create comment
# GET    /api/comments/:id/          → comment detail
# PATCH  /api/comments/:id/          → edit comment
# DELETE /api/comments/:id/          → delete comment