from rest_framework import serializers
from .models import Comment
from users.serializers import UserPublicSerializer

class CommentSerializer(serializers.ModelSerializer):
    author  = UserPublicSerializer(read_only=True)
    replies = serializers.SerializerMethodField()

    class Meta:
        model  = Comment
        fields = [
            'id', 'post', 'author', 'parent',
            'body', 'is_edited', 'replies',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['author', 'is_edited']

    def get_replies(self, obj):
        """Return nested replies for top-level comments"""
        if obj.replies.exists():
            return CommentSerializer(
                obj.replies.all(),
                many    = True,
                context = self.context
            ).data
        return []


class CommentCreateSerializer(serializers.ModelSerializer):
    """Used only for creating/updating a comment"""
    class Meta:
        model  = Comment
        fields = ['id', 'post', 'parent', 'body']

    def validate_parent(self, value):
        """Make sure reply belongs to the same post"""
        if value:
            post_id = self.initial_data.get('post')
            try:
                if value.post_id != int(post_id):
                    raise serializers.ValidationError(
                        "Reply must belong to the same post."
                    )
            except (TypeError, ValueError):
                raise serializers.ValidationError(
                    "Invalid post ID provided."
                )
        return value