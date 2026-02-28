from rest_framework import serializers
from .models import Notification
from users.serializers import UserPublicSerializer

class NotificationSerializer(serializers.ModelSerializer):
    recipient  = UserPublicSerializer(read_only=True)
    sender     = UserPublicSerializer(read_only=True)
    post_title = serializers.SerializerMethodField()
    message    = serializers.SerializerMethodField()

    class Meta:
        model  = Notification
        fields = [
            'id', 'recipient', 'sender',
            'notif_type', 'post', 'post_title',
            'comment', 'is_read', 'message', 'created_at'
        ]
        read_only_fields = [
            'recipient', 'sender', 'notif_type',
            'post', 'comment', 'created_at'
        ]

    def get_post_title(self, obj):
        if obj.post:
            return obj.post.title
        return None

    def get_message(self, obj):
        """Human readable notification message"""
        sender = obj.sender.username
        post   = obj.post.title if obj.post else 'your post'

        messages = {
            'like':    f'{sender} liked your post "{post}"',
            'dislike': f'{sender} disliked your post "{post}"',
            'comment': f'{sender} commented on your post "{post}"',
            'reply':   f'{sender} replied to your comment on "{post}"',
            'share':   f'{sender} shared your post "{post}"',
            'follow':  f'{sender} started following you',
        }
        return messages.get(obj.notif_type, f'{sender} interacted with your content')