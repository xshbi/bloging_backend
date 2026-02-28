from rest_framework import viewsets, permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Reaction, Share
from .serializers import ReactionSerializer, ShareSerializer


class ReactionViewSet(viewsets.ModelViewSet):
    serializer_class   = ReactionSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    http_method_names  = ['get', 'post', 'delete']  # no PUT/PATCH on reactions

    def get_queryset(self):
        queryset = Reaction.objects.select_related('user', 'post', 'comment')

        # filter by post
        post_id = self.request.query_params.get('post')
        if post_id:
            queryset = queryset.filter(post_id=post_id)

        # filter by reaction type
        reaction_type = self.request.query_params.get('type')
        if reaction_type:
            queryset = queryset.filter(reaction_type=reaction_type)

        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        """Override to handle toggle-off (reaction removed) gracefully."""
        try:
            return super().create(request, *args, **kwargs)
        except ValidationError as exc:
            detail = exc.detail
            if isinstance(detail, dict) and detail.get('toggled_off'):
                return Response({'toggled_off': True, 'detail': 'Reaction removed.'}, status=status.HTTP_200_OK)
            raise

    def destroy(self, request, *args, **kwargs):
        reaction = self.get_object()
        if reaction.user != request.user and request.user.role != 'admin':
            return Response(
                {'error': 'Not allowed.'},
                status=status.HTTP_403_FORBIDDEN
            )
        reaction.delete()
        return Response(
            {'message': 'Reaction removed.'},
            status=status.HTTP_204_NO_CONTENT
        )


class ShareView(APIView):
    """Track when a user shares a post"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ShareSerializer(
            data    = request.data,
            context = {'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(
            {'message': 'Share tracked successfully.'},
            status=status.HTTP_201_CREATED
        )

    def get(self, request):
        """Get share count for a post"""
        post_id = request.query_params.get('post')
        if not post_id:
            return Response({'error': 'post param required.'}, status=400)

        shares = Share.objects.filter(post_id=post_id)
        total  = shares.count()

        # breakdown by platform
        breakdown = {}
        for share in shares:
            breakdown[share.platform] = breakdown.get(share.platform, 0) + 1

        return Response({
            'total'    : total,
            'breakdown': breakdown
        })