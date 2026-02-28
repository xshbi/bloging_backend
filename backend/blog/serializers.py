from rest_framework import serializers
from .models import Post, Category, Tag
from users.serializers import UserPublicSerializer

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model  = Category
        fields = ['id', 'name', 'slug', 'description']
        read_only_fields = ['slug']


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Tag
        fields = ['id', 'name', 'slug']
        read_only_fields = ['slug']


class PostListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing posts (no full content)"""
    author   = UserPublicSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    tags     = TagSerializer(many=True, read_only=True)

    class Meta:
        model  = Post
        fields = [
            'id', 'title', 'slug', 'cover_image',
            'author', 'category', 'tags', 'status',
            'views_count', 'total_likes', 'total_dislikes',
            'total_comments', 'total_shares', 'created_at'
        ]
        read_only_fields = ['slug', 'views_count']


class PostDetailSerializer(serializers.ModelSerializer):
    """Full serializer for single post detail (includes content)"""
    author   = UserPublicSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    tags     = TagSerializer(many=True, read_only=True)

    # writable IDs for create/update
    category_id = serializers.PrimaryKeyRelatedField(
        queryset   = Category.objects.all(),
        source     = 'category',
        write_only = True,
        required   = False
    )
    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset   = Tag.objects.all(),
        source     = 'tags',
        write_only = True,
        many       = True,
        required   = False
    )

    class Meta:
        model  = Post
        fields = [
            'id', 'title', 'slug', 'content', 'cover_image',
            'author', 'category', 'category_id',
            'tags', 'tag_ids', 'status',
            'views_count', 'total_likes', 'total_dislikes',
            'total_comments', 'total_shares',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['slug', 'views_count', 'author']

    def create(self, validated_data):
        tags = validated_data.pop('tags', [])
        post = Post.objects.create(**validated_data)
        post.tags.set(tags)
        return post

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if tags is not None:
            instance.tags.set(tags)
        return instance