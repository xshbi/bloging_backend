"""
Comprehensive tests for the `comments` app.

Covers:
  - List comments (filtered by post slug)
  - Create top-level comment
  - Create reply (valid and invalid parent post)
  - Update own comment (marks is_edited=True)
  - Delete own comment / admin delete / other user blocked
  - Nested replies serialization
"""

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from users.models import User
from blog.models import Post
from .models import Comment


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def create_user(username, role='viewer', password='StrongPass1!'):
    return User.objects.create_user(username=username, password=password, role=role)


def auth_client(user, password='StrongPass1!'):
    client = APIClient()
    resp = client.post(reverse('login'), {'username': user.username, 'password': password}, format='json')
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {resp.data["access"]}')
    return client


def create_post(author, title='Test Post'):
    return Post.objects.create(author=author, title=title, content='Content', status='published')


def create_comment(post, author, body='Great post!', parent=None):
    return Comment.objects.create(post=post, author=author, body=body, parent=parent)


# ---------------------------------------------------------------------------
# List Comments
# ---------------------------------------------------------------------------

class CommentListTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.author = create_user('author', role='author')
        self.post = create_post(self.author)
        create_comment(self.post, self.author, 'Top comment')
        self.url = reverse('comment-list')

    def test_anyone_can_list_comments(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_filter_by_post_slug(self):
        other_post = create_post(self.author, title='Other Post')
        create_comment(other_post, self.author, 'Different comment')
        url = f'{self.url}?post={self.post.slug}'
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        for c in resp.data['results']:
            self.assertEqual(c['post'], self.post.id)

    def test_list_shows_only_top_level_comments(self):
        top = create_comment(self.post, self.author, 'Top')
        create_comment(self.post, self.author, 'Reply', parent=top)
        resp = self.client.get(f'{self.url}?post={self.post.slug}')
        for c in resp.data['results']:
            self.assertIsNone(c['parent'])


# ---------------------------------------------------------------------------
# Create Comment
# ---------------------------------------------------------------------------

class CommentCreateTests(TestCase):
    def setUp(self):
        self.author = create_user('author', role='author')
        self.commenter = create_user('commenter')
        self.post = create_post(self.author)
        self.url = reverse('comment-list')

    def test_authenticated_user_can_comment(self):
        client = auth_client(self.commenter)
        resp = client.post(self.url, {
            'post': self.post.id,
            'body': 'Nice post!',
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_unauthenticated_cannot_comment(self):
        resp = APIClient().post(self.url, {
            'post': self.post.id,
            'body': 'Anonymous comment',
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_reply_to_comment_same_post(self):
        parent = create_comment(self.post, self.author, 'Parent')
        client = auth_client(self.commenter)
        resp = client.post(self.url, {
            'post': self.post.id,
            'parent': parent.id,
            'body': 'This is a reply',
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_reply_to_comment_different_post_blocked(self):
        other_post = create_post(self.author, title='Other Post')
        parent = create_comment(other_post, self.author, 'Parent on other post')
        client = auth_client(self.commenter)
        resp = client.post(self.url, {
            'post': self.post.id,   # different from parent's post
            'parent': parent.id,
            'body': 'Should fail',
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


# ---------------------------------------------------------------------------
# Update Comment
# ---------------------------------------------------------------------------

class CommentUpdateTests(TestCase):
    def setUp(self):
        self.author = create_user('author', role='author')
        self.other = create_user('other')
        self.post = create_post(self.author)
        self.comment = create_comment(self.post, self.author, 'Original body')

    def test_owner_can_update_comment(self):
        client = auth_client(self.author)
        url = reverse('comment-detail', kwargs={'pk': self.comment.id})
        resp = client.patch(url, {'body': 'Updated body'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.comment.refresh_from_db()
        self.assertTrue(self.comment.is_edited)

    def test_other_user_cannot_update_comment(self):
        client = auth_client(self.other)
        url = reverse('comment-detail', kwargs={'pk': self.comment.id})
        resp = client.patch(url, {'body': 'Hacked'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)


# ---------------------------------------------------------------------------
# Delete Comment
# ---------------------------------------------------------------------------

class CommentDeleteTests(TestCase):
    def setUp(self):
        self.author = create_user('author', role='author')
        self.other = create_user('other')
        self.admin = create_user('admin_user', role='admin')
        self.post = create_post(self.author)

    def test_owner_can_delete_own_comment(self):
        comment = create_comment(self.post, self.author, 'To delete')
        client = auth_client(self.author)
        url = reverse('comment-detail', kwargs={'pk': comment.id})
        resp = client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Comment.objects.filter(id=comment.id).exists())

    def test_other_user_cannot_delete_comment(self):
        comment = create_comment(self.post, self.author, 'Protected')
        client = auth_client(self.other)
        url = reverse('comment-detail', kwargs={'pk': comment.id})
        resp = client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_delete_any_comment(self):
        comment = create_comment(self.post, self.author, 'Admin remove')
        client = auth_client(self.admin)
        url = reverse('comment-detail', kwargs={'pk': comment.id})
        resp = client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Nested Replies Serialization
# ---------------------------------------------------------------------------

class CommentReplySerializationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.author = create_user('author', role='author')
        self.post = create_post(self.author)
        self.top = create_comment(self.post, self.author, 'Top-level')
        self.reply = create_comment(self.post, self.author, 'Reply', parent=self.top)

    def test_top_level_comment_has_replies(self):
        url = f'{reverse("comment-list")}?post={self.post.slug}'
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        top_comments = [c for c in resp.data['results'] if c['id'] == self.top.id]
        self.assertEqual(len(top_comments), 1)
        self.assertEqual(len(top_comments[0]['replies']), 1)
        self.assertEqual(top_comments[0]['replies'][0]['body'], 'Reply')
