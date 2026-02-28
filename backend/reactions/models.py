from django.db import models
from users.models import User
from blog.models import Post
from comments.models import Comment

class Reaction(models.Model):
    LIKE    = 'like'
    DISLIKE = 'dislike'
    REACTION_TYPES = [
        (LIKE,    'Like'),
        (DISLIKE, 'Dislike'),
    ]

    user          = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reactions')
    post          = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='reactions', null=True, blank=True)
    comment       = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='reactions', null=True, blank=True)
    reaction_type = models.CharField(max_length=10, choices=REACTION_TYPES)
    created_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        # one reaction per user per post
        unique_together = [
            ('user', 'post'),
            ('user', 'comment'),
        ]

    def __str__(self):
        return f'{self.user} - {self.reaction_type} on {self.post or self.comment}'


class Share(models.Model):
    PLATFORMS = [
        ('facebook',  'Facebook'),
        ('twitter',   'Twitter'),
        ('whatsapp',  'WhatsApp'),
        ('linkedin',  'LinkedIn'),
        ('copy_link', 'Copy Link'),
        ('other',     'Other'),
    ]

    user      = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shares')
    post      = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='shares')
    platform  = models.CharField(max_length=20, choices=PLATFORMS, default='other')
    shared_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user} shared {self.post} on {self.platform}'