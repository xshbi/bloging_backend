from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLES = [('admin', 'Admin'), ('author', 'Author'), ('viewer', 'Viewer')]
    role   = models.CharField(max_length=10, choices=ROLES, default='viewer')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio    = models.TextField(blank=True)

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_set',   
        blank=True
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_set',    
        blank=True
    )

    def __str__(self):
        return self.username