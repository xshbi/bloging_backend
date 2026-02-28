"""
Comprehensive tests for the `reactions` app.

Covers:
  - React to a post (like/dislike)
  - React to a comment
  - Toggle-off: same reaction type removes reaction (200 toggled_off)
  - Toggle-switch: different reaction type updates it
  - Invalid reaction (neither post nor comment, or both)
  - Delete own reaction
  - Cannot delete other user's reaction
  - Filter reactions by post and type
  - Share track (POST)
  - Share count & breakdown (GET)
"""

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from users.models import User
from blog.models import Post
from comments.models import Comment
from .models import Reaction, Share


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


def create_comment(post, author, body='A comment'):
    return Comment.objects.create(post=post, author=author, body=body)


# ---------------------------------------------------------------------------
# Reaction Tests
# ---------------------------------------------------------------------------

class ReactionPostTests(TestCase):
    def setUp(self):
        self.author = create_user('author', role='author')
        self.user = create_user('user1')
        self.post = create_post(self.author)
        self.url = reverse('reaction-list')

    def test_like_post(self):
        client = auth_client(self.user)
        resp = client.post(self.url, {'post': self.post.id, 'reaction_type': 'like'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Reaction.objects.filter(user=self.user, post=self.post, reaction_type='like').exists())

    def test_dislike_post(self):
        client = auth_client(self.user)
        resp = client.post(self.url, {'post': self.post.id, 'reaction_type': 'dislike'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_toggle_off_same_reaction(self):
        """Posting the same reaction type twice removes it (toggle off)."""
        client = auth_client(self.user)
        client.post(self.url, {'post': self.post.id, 'reaction_type': 'like'}, format='json')
        resp = client.post(self.url, {'post': self.post.id, 'reaction_type': 'like'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data.get('toggled_off'))
        self.assertFalse(Reaction.objects.filter(user=self.user, post=self.post).exists())

    def test_toggle_switch_reaction_type(self):
        """Posting a different reaction type updates the existing one."""
        client = auth_client(self.user)
        client.post(self.url, {'post': self.post.id, 'reaction_type': 'like'}, format='json')
        resp = client.post(self.url, {'post': self.post.id, 'reaction_type': 'dislike'}, format='json')
        self.assertIn(resp.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])
        reaction = Reaction.objects.get(user=self.user, post=self.post)
        self.assertEqual(reaction.reaction_type, 'dislike')

    def test_unauthenticated_cannot_react(self):
        resp = APIClient().post(self.url, {'post': self.post.id, 'reaction_type': 'like'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_reaction_requires_post_or_comment(self):
        client = auth_client(self.user)
        resp = client.post(self.url, {'reaction_type': 'like'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reaction_cannot_target_both_post_and_comment(self):
        comment = create_comment(self.post, self.author)
        client = auth_client(self.user)
        resp = client.post(self.url, {
            'post': self.post.id,
            'comment': comment.id,
            'reaction_type': 'like',
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


class ReactionCommentTests(TestCase):
    def setUp(self):
        self.author = create_user('author', role='author')
        self.user = create_user('user1')
        self.post = create_post(self.author)
        self.comment = create_comment(self.post, self.author)
        self.url = reverse('reaction-list')

    def test_like_comment(self):
        client = auth_client(self.user)
        resp = client.post(self.url, {'comment': self.comment.id, 'reaction_type': 'like'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)


class ReactionDeleteTests(TestCase):
    def setUp(self):
        self.author = create_user('author', role='author')
        self.user = create_user('user1')
        self.other = create_user('user2')
        self.post = create_post(self.author)

    def test_user_can_delete_own_reaction(self):
        reaction = Reaction.objects.create(user=self.user, post=self.post, reaction_type='like')
        client = auth_client(self.user)
        url = reverse('reaction-detail', kwargs={'pk': reaction.id})
        resp = client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

    def test_other_user_cannot_delete_reaction(self):
        reaction = Reaction.objects.create(user=self.user, post=self.post, reaction_type='like')
        client = auth_client(self.other)
        url = reverse('reaction-detail', kwargs={'pk': reaction.id})
        resp = client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)


class ReactionFilterTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.author = create_user('author', role='author')
        self.user = create_user('user1')
        self.post = create_post(self.author)
        Reaction.objects.create(user=self.user, post=self.post, reaction_type='like')
        self.url = reverse('reaction-list')

    def test_filter_by_post(self):
        resp = self.client.get(f'{self.url}?post={self.post.id}')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        for r in resp.data['results']:
            self.assertEqual(r['post'], self.post.id)

    def test_filter_by_reaction_type(self):
        resp = self.client.get(f'{self.url}?type=like&post={self.post.id}')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        for r in resp.data['results']:
            self.assertEqual(r['reaction_type'], 'like')


# ---------------------------------------------------------------------------
# Post Reaction Counts (via Post model properties)
# ---------------------------------------------------------------------------

class PostReactionCountTests(TestCase):
    def setUp(self):
        self.author = create_user('author', role='author')
        self.user1 = create_user('user1')
        self.user2 = create_user('user2')
        self.post = create_post(self.author)

    def test_total_likes_count(self):
        Reaction.objects.create(user=self.user1, post=self.post, reaction_type='like')
        Reaction.objects.create(user=self.user2, post=self.post, reaction_type='dislike')
        self.post.refresh_from_db()
        self.assertEqual(self.post.total_likes, 1)
        self.assertEqual(self.post.total_dislikes, 1)


# ---------------------------------------------------------------------------
# Share Tests
# ---------------------------------------------------------------------------

class ShareTests(TestCase):
    def setUp(self):
        self.author = create_user('author', role='author')
        self.user = create_user('user1')
        self.post = create_post(self.author)
        self.share_url = reverse('shares')

    def test_track_share(self):
        client = auth_client(self.user)
        resp = client.post(self.share_url, {
            'post': self.post.id,
            'platform': 'twitter',
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Share.objects.filter(user=self.user, post=self.post, platform='twitter').exists())

    def test_get_share_count(self):
        Share.objects.create(user=self.user, post=self.post, platform='twitter')
        Share.objects.create(user=self.author, post=self.post, platform='facebook')
        client = auth_client(self.user)
        resp = client.get(f'{self.share_url}?post={self.post.id}')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['total'], 2)
        self.assertIn('twitter', resp.data['breakdown'])
        self.assertIn('facebook', resp.data['breakdown'])

    def test_share_requires_post_param(self):
        client = auth_client(self.user)
        resp = client.get(self.share_url)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthenticated_cannot_share(self):
        resp = APIClient().post(self.share_url, {
            'post': self.post.id,
            'platform': 'twitter',
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
