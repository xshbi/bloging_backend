from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from .models import Comment
from .serializers import CommentSerializer, CommentCreateSerializer


class IsOwnerOrAdminOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user or request.user.role == 'admin'


class CommentViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrAdminOrReadOnly]

    def get_queryset(self):
        queryset = Comment.objects.filter(
            parent=None
        ).select_related('author', 'post').prefetch_related('replies__author')

        post_slug = self.request.query_params.get('post')
        if post_slug:
            queryset = queryset.filter(post__slug=post_slug)

        return queryset.order_by('-created_at')

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return CommentCreateSerializer
        return CommentSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        serializer.save(is_edited=True)

    def destroy(self, request, *args, **kwargs):
        comment = self.get_object()
        if comment.author != request.user and request.user.role != 'admin':
            return Response(
                {'error': 'Not allowed.'},
                status=status.HTTP_403_FORBIDDEN
            )
        comment.delete()
        return Response(
            {'message': 'Comment deleted.'},
            status=status.HTTP_204_NO_CONTENT
        )