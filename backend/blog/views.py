from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Post, Category, Tag
from .serializers import (
    PostListSerializer,
    PostDetailSerializer,
    CategorySerializer,
    TagSerializer
)


class IsAuthorOrAdminOrReadOnly(permissions.BasePermission):
    """Allow read to anyone, write only to author or admin"""
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user or request.user.role == 'admin'


class PostViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrAdminOrReadOnly]
    lookup_field       = 'slug'
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields   = ['category__slug', 'tags__slug', 'status', 'author__username']
    search_fields      = ['title', 'content']
    ordering_fields    = ['created_at', 'views_count']
    ordering           = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        # admins and authors can see drafts; anonymous users and viewers only see published
        if user.is_authenticated and getattr(user, 'role', 'viewer') in ['admin', 'author']:
            return Post.objects.all().select_related('author', 'category').prefetch_related('tags')
        return Post.objects.filter(status='published').select_related('author', 'category').prefetch_related('tags')

    def get_serializer_class(self):
        if self.action == 'list':
            return PostListSerializer
        return PostDetailSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # increment view count on every detail fetch
        instance.views_count += 1
        instance.save(update_fields=['views_count'])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def my_posts(self, request):
        """GET /api/posts/my_posts/ — returns logged in author's posts"""
        posts = Post.objects.filter(author=request.user).order_by('-created_at')
        serializer = PostListSerializer(posts, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def publish(self, request, slug=None):
        """POST /api/posts/:slug/publish/ — publish a draft"""
        post = self.get_object()
        if post.author != request.user and request.user.role != 'admin':
            return Response(
                {'error': 'Not allowed.'},
                status=status.HTTP_403_FORBIDDEN
            )
        post.status = 'published'
        post.save(update_fields=['status'])
        return Response({'message': 'Post published successfully.'})

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def archive(self, request, slug=None):
        """POST /api/posts/:slug/archive/ — archive a post"""
        post = self.get_object()
        if post.author != request.user and request.user.role != 'admin':
            return Response(
                {'error': 'Not allowed.'},
                status=status.HTTP_403_FORBIDDEN
            )
        post.status = 'archived'
        post.save(update_fields=['status'])
        return Response({'message': 'Post archived.'})


class CategoryViewSet(viewsets.ModelViewSet):
    queryset           = Category.objects.all()
    serializer_class   = CategorySerializer
    lookup_field       = 'slug'
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_permissions(self):
        # only admin can create/edit/delete categories
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]


class TagViewSet(viewsets.ModelViewSet):
    queryset           = Tag.objects.all()
    serializer_class   = TagSerializer
    lookup_field       = 'slug'

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]