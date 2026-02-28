from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ReactionViewSet, ShareView

router = DefaultRouter()
router.register('reactions', ReactionViewSet, basename='reaction')

urlpatterns = [
    path('', include(router.urls)),

    # shares
    path('shares/',  ShareView.as_view(), name='shares'),

]

# This auto generates:
# GET    /api/reactions/              → list reactions (filter by ?post=id&type=like)
# POST   /api/reactions/              → like or dislike
# DELETE /api/reactions/:id/          → remove reaction
# POST   /api/shares/                 → track a share
# GET    /api/shares/?post=id         → get share count + breakdown