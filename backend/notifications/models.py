from django.db import models
from users.models import User
from blog.models import Post
from comments.models import Comment

class Notification(models.Model):
    NOTIF_TYPES = [
        ('like',    'Like'),
        ('dislike', 'Dislike'),
        ('comment', 'Comment'),
        ('reply',   'Reply'),
        ('share',   'Share'),
        ('follow',  'Follow'),
    ]

    recipient  = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender     = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_notifications')
    notif_type = models.CharField(max_length=20, choices=NOTIF_TYPES)
    post       = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True)
    comment    = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, blank=True)
    is_read    = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.sender} → {self.recipient} ({self.notif_type})'