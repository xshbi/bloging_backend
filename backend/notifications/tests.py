"""
Comprehensive tests for the `notifications` app.

Covers:
  - List notifications (own only)
  - Filter unread-only
  - Unread count endpoint
  - Mark single notification as read
  - Mark all as read
  - Clear all notifications
  - Signal: like/dislike on post creates notification for post author
  - Signal: comment on post creates notification for post author
  - Signal: reply to comment creates notification for comment author
  - Self-reaction/comment does NOT create notification
"""

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from users.models import User
from blog.models import Post
from comments.models import Comment
from reactions.models import Reaction
from .models import Notification


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


def create_notification(recipient, sender, notif_type='like', post=None, is_read=False):
    return Notification.objects.create(
        recipient=recipient, sender=sender,
        notif_type=notif_type, post=post, is_read=is_read
    )


# ---------------------------------------------------------------------------
# List & Filter
# ---------------------------------------------------------------------------

class NotificationListTests(TestCase):
    def setUp(self):
        self.user1 = create_user('user1')
        self.user2 = create_user('user2')
        self.post = create_post(self.user1)
        self.notif = create_notification(self.user1, self.user2, post=self.post)

    def test_user_sees_own_notifications(self):
        client = auth_client(self.user1)
        resp = client.get(reverse('notifications'))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['count'], 1)

    def test_user_does_not_see_others_notifications(self):
        client = auth_client(self.user2)
        resp = client.get(reverse('notifications'))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['count'], 0)

    def test_filter_unread_only(self):
        create_notification(self.user1, self.user2, post=self.post, is_read=True)
        client = auth_client(self.user1)
        resp = client.get(reverse('notifications') + '?unread=true')
        for n in resp.data['results']:
            self.assertFalse(n['is_read'])

    def test_requires_authentication(self):
        resp = APIClient().get(reverse('notifications'))
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


# ---------------------------------------------------------------------------
# Unread Count
# ---------------------------------------------------------------------------

class UnreadCountTests(TestCase):
    def setUp(self):
        self.user = create_user('user1')
        self.sender = create_user('sender')
        self.post = create_post(self.user)

    def test_unread_count_is_correct(self):
        create_notification(self.user, self.sender, post=self.post, is_read=False)
        create_notification(self.user, self.sender, post=self.post, is_read=True)
        client = auth_client(self.user)
        resp = client.get(reverse('unread_count'))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['unread_count'], 1)

    def test_unread_count_zero_when_all_read(self):
        create_notification(self.user, self.sender, post=self.post, is_read=True)
        client = auth_client(self.user)
        resp = client.get(reverse('unread_count'))
        self.assertEqual(resp.data['unread_count'], 0)


# ---------------------------------------------------------------------------
# Mark Single as Read
# ---------------------------------------------------------------------------

class MarkReadTests(TestCase):
    def setUp(self):
        self.user = create_user('user1')
        self.sender = create_user('sender')
        self.post = create_post(self.user)
        self.notif = create_notification(self.user, self.sender, post=self.post)

    def test_mark_own_notification_as_read(self):
        client = auth_client(self.user)
        url = reverse('mark_read', kwargs={'pk': self.notif.id})
        resp = client.patch(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.notif.refresh_from_db()
        self.assertTrue(self.notif.is_read)

    def test_cannot_mark_other_users_notification(self):
        other = create_user('other')
        client = auth_client(other)
        url = reverse('mark_read', kwargs={'pk': self.notif.id})
        resp = client.patch(url)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)


# ---------------------------------------------------------------------------
# Mark All as Read
# ---------------------------------------------------------------------------

class MarkAllReadTests(TestCase):
    def setUp(self):
        self.user = create_user('user1')
        self.sender = create_user('sender')
        self.post = create_post(self.user)
        for _ in range(3):
            create_notification(self.user, self.sender, post=self.post, is_read=False)

    def test_mark_all_read(self):
        client = auth_client(self.user)
        resp = client.patch(reverse('mark_all_read'))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('3', resp.data['message'])
        self.assertEqual(Notification.objects.filter(recipient=self.user, is_read=False).count(), 0)


# ---------------------------------------------------------------------------
# Clear All
# ---------------------------------------------------------------------------

class ClearNotificationsTests(TestCase):
    def setUp(self):
        self.user = create_user('user1')
        self.sender = create_user('sender')
        self.post = create_post(self.user)
        for _ in range(2):
            create_notification(self.user, self.sender, post=self.post)

    def test_clear_all_notifications(self):
        client = auth_client(self.user)
        resp = client.delete(reverse('clear_notifications'))
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Notification.objects.filter(recipient=self.user).count(), 0)

    def test_unauthenticated_cannot_clear(self):
        resp = APIClient().delete(reverse('clear_notifications'))
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


# ---------------------------------------------------------------------------
# Signal Tests
# ---------------------------------------------------------------------------

class SignalNotificationTests(TestCase):
    def setUp(self):
        self.post_author = create_user('post_author', role='author')
        self.commenter   = create_user('commenter')
        self.post        = create_post(self.post_author)

    def test_like_creates_notification_for_post_author(self):
        initial_count = Notification.objects.filter(recipient=self.post_author).count()
        Reaction.objects.create(user=self.commenter, post=self.post, reaction_type='like')
        self.assertEqual(
            Notification.objects.filter(recipient=self.post_author, notif_type='like').count(),
            initial_count + 1
        )

    def test_dislike_creates_notification_for_post_author(self):
        Reaction.objects.create(user=self.commenter, post=self.post, reaction_type='dislike')
        self.assertTrue(
            Notification.objects.filter(recipient=self.post_author, notif_type='dislike').exists()
        )

    def test_comment_creates_notification_for_post_author(self):
        Comment.objects.create(post=self.post, author=self.commenter, body='Hello!')
        self.assertTrue(
            Notification.objects.filter(recipient=self.post_author, notif_type='comment').exists()
        )

    def test_reply_creates_notification_for_comment_author(self):
        top_comment = Comment.objects.create(post=self.post, author=self.post_author, body='Top')
        replier = create_user('replier')
        Comment.objects.create(post=self.post, author=replier, body='Reply', parent=top_comment)
        self.assertTrue(
            Notification.objects.filter(recipient=self.post_author, notif_type='reply').exists()
        )

    def test_self_reaction_does_not_create_notification(self):
        """Author reacting to their own post should NOT create a notification."""
        Reaction.objects.create(user=self.post_author, post=self.post, reaction_type='like')
        self.assertFalse(
            Notification.objects.filter(recipient=self.post_author, notif_type='like').exists()
        )

    def test_self_comment_does_not_create_notification(self):
        """Author commenting on their own post should NOT create a notification."""
        Comment.objects.create(post=self.post, author=self.post_author, body='My own comment')
        self.assertFalse(
            Notification.objects.filter(recipient=self.post_author, notif_type='comment').exists()
        )


# ---------------------------------------------------------------------------
# Notification Serializer (message field)
# ---------------------------------------------------------------------------

class NotificationMessageTests(TestCase):
    def setUp(self):
        self.user = create_user('recipient')
        self.sender = create_user('sender')
        self.post = create_post(self.user, 'My Great Post')

    def test_notification_message_for_like(self):
        notif = create_notification(self.user, self.sender, notif_type='like', post=self.post)
        client = auth_client(self.user)
        resp = client.get(reverse('notifications'))
        messages = [n['message'] for n in resp.data['results']]
        self.assertTrue(any('liked' in m and 'My Great Post' in m for m in messages))

    def test_notification_post_title_field(self):
        notif = create_notification(self.user, self.sender, notif_type='comment', post=self.post)
        client = auth_client(self.user)
        resp = client.get(reverse('notifications'))
        post_titles = [n.get('post_title') for n in resp.data['results']]
        self.assertIn('My Great Post', post_titles)
