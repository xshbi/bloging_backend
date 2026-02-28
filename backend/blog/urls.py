from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PostViewSet, CategoryViewSet, TagViewSet

router = DefaultRouter()
router.register('posts',      PostViewSet,      basename='post')
router.register('categories', CategoryViewSet,  basename='category')
router.register('tags',       TagViewSet,        basename='tag')

urlpatterns = [
    path('', include(router.urls)),
]

# This auto generates:
# GET    /api/posts/                   → list all posts
# POST   /api/posts/                   → create post
# GET    /api/posts/:slug/             → post detail
# PUT    /api/posts/:slug/             → update post
# PATCH  /api/posts/:slug/             → partial update
# DELETE /api/posts/:slug/             → delete post
# GET    /api/posts/my_posts/          → my posts
# POST   /api/posts/:slug/publish/     → publish post
# POST   /api/posts/:slug/archive/     → archive post
# GET    /api/categories/              → list categories
# GET    /api/categories/:slug/        → category detail
# GET    /api/tags/                    → list tags
# GET    /api/tags/:slug/              → tag detail