from django.db import models
from django.utils.text import slugify
from users.models import User

class Category(models.Model):
    name        = models.CharField(max_length=100, unique=True)
    slug        = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Post(models.Model):
    STATUS_CHOICES = [
        ('draft',     'Draft'),
        ('published', 'Published'),
        ('archived',  'Archived'),
    ]

    author      = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    title       = models.CharField(max_length=255)
    slug        = models.SlugField(unique=True, blank=True)
    content     = models.TextField()
    cover_image = models.ImageField(upload_to='covers/%Y/%m/', blank=True, null=True)
    category    = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    tags        = models.ManyToManyField(Tag, blank=True)
    status      = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    views_count = models.PositiveIntegerField(default=0)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    # helper properties
    @property
    def total_likes(self):
        return self.reactions.filter(reaction_type='like').count()

    @property
    def total_dislikes(self):
        return self.reactions.filter(reaction_type='dislike').count()

    @property
    def total_comments(self):
        return self.comments.count()

    @property
    def total_shares(self):
        return self.shares.count()