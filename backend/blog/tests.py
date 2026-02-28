"""
Comprehensive tests for the `blog` app.

Covers:
  - Category CRUD (admin-gated writes)
  - Tag CRUD (admin-gated writes)
  - Post list (published-only for unauthenticated, all for author/admin)
  - Post create / retrieve (view count increment) / update / delete
  - Post my_posts action
  - Post publish / archive actions
  - Filter & search
"""

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from users.models import User
from .models import Post, Category, Tag


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


def create_category(name='Tech'):
    return Category.objects.create(name=name)


def create_tag(name='django'):
    return Tag.objects.create(name=name)


def create_post(author, title='Hello World', status_val='published', category=None):
    return Post.objects.create(
        author=author,
        title=title,
        content='Some content here.',
        status=status_val,
        category=category,
    )


# ---------------------------------------------------------------------------
# Category Tests
# ---------------------------------------------------------------------------

class CategoryTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_superuser(username='admin', password='AdminPass1!')
        self.viewer = create_user('viewer')
        self.list_url = reverse('category-list')

    def test_anyone_can_list_categories(self):
        create_category('Python')
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_admin_can_create_category(self):
        admin_client = auth_client(self.admin, 'AdminPass1!')
        resp = admin_client.post(self.list_url, {'name': 'Django'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Category.objects.filter(name='Django').exists())

    def test_viewer_cannot_create_category(self):
        viewer_client = auth_client(self.viewer)
        resp = viewer_client.post(self.list_url, {'name': 'Blocked'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_slug_auto_generated(self):
        admin_client = auth_client(self.admin, 'AdminPass1!')
        admin_client.post(self.list_url, {'name': 'Web Dev'}, format='json')
        cat = Category.objects.get(name='Web Dev')
        self.assertEqual(cat.slug, 'web-dev')

    def test_admin_can_delete_category(self):
        cat = create_category('ToDelete')
        admin_client = auth_client(self.admin, 'AdminPass1!')
        url = reverse('category-detail', kwargs={'slug': cat.slug})
        resp = admin_client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Tag Tests
# ---------------------------------------------------------------------------

class TagTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_superuser(username='admin', password='AdminPass1!')
        self.list_url = reverse('tag-list')

    def test_list_tags_public(self):
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_admin_create_tag(self):
        admin_client = auth_client(self.admin, 'AdminPass1!')
        resp = admin_client.post(self.list_url, {'name': 'python'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_non_admin_cannot_create_tag(self):
        # Unauthenticated clients get 401; authenticated non-admins get 403.
        # Test the unauthenticated case (simplest):
        resp = self.client.post(self.list_url, {'name': 'blocked'}, format='json')
        self.assertIn(resp.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])


# ---------------------------------------------------------------------------
# Post Tests
# ---------------------------------------------------------------------------

class PostListTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.author = create_user('author', role='author')
        self.viewer = create_user('viewer')
        self.draft_post = create_post(self.author, title='Draft Post', status_val='draft')
        self.pub_post   = create_post(self.author, title='Published Post', status_val='published')
        self.url = reverse('post-list')

    def test_anonymous_sees_only_published(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        titles = [p['title'] for p in resp.data['results']]
        self.assertIn('Published Post', titles)
        self.assertNotIn('Draft Post', titles)

    def test_viewer_sees_only_published(self):
        viewer_client = auth_client(self.viewer)
        resp = viewer_client.get(self.url)
        titles = [p['title'] for p in resp.data['results']]
        self.assertNotIn('Draft Post', titles)

    def test_author_sees_all_posts(self):
        author_client = auth_client(self.author)
        resp = author_client.get(self.url)
        titles = [p['title'] for p in resp.data['results']]
        self.assertIn('Draft Post', titles)
        self.assertIn('Published Post', titles)


class PostCreateTests(TestCase):
    def setUp(self):
        self.author = create_user('author', role='author')
        self.viewer = create_user('viewer')

    def test_authenticated_user_can_create_post(self):
        client = auth_client(self.author)
        resp = client.post(reverse('post-list'), {
            'title': 'New Post',
            'content': 'Content here',
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data['author']['username'], 'author')
        self.assertEqual(resp.data['status'], 'draft')  # default

    def test_unauthenticated_cannot_create_post(self):
        resp = APIClient().post(reverse('post-list'), {
            'title': 'Anon Post',
            'content': 'Content',
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_slug_auto_generated_on_create(self):
        client = auth_client(self.author)
        resp = client.post(reverse('post-list'), {
            'title': 'My Unique Title',
            'content': 'Content',
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data['slug'], 'my-unique-title')


class PostDetailTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.author = create_user('author', role='author')
        self.other_user = create_user('other')
        self.post = create_post(self.author, title='Detail Post', status_val='published')

    def test_retrieve_post_increments_view_count(self):
        initial_views = self.post.views_count
        url = reverse('post-detail', kwargs={'slug': self.post.slug})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.post.refresh_from_db()
        self.assertEqual(self.post.views_count, initial_views + 1)

    def test_author_can_update_own_post(self):
        author_client = auth_client(self.author)
        url = reverse('post-detail', kwargs={'slug': self.post.slug})
        resp = author_client.patch(url, {'content': 'Updated content'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_other_user_cannot_update_post(self):
        other_client = auth_client(self.other_user)
        url = reverse('post-detail', kwargs={'slug': self.post.slug})
        resp = other_client.patch(url, {'content': 'Injected content'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_author_can_delete_own_post(self):
        author_client = auth_client(self.author)
        url = reverse('post-detail', kwargs={'slug': self.post.slug})
        resp = author_client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Post.objects.filter(id=self.post.id).exists())

    def test_other_user_cannot_delete_post(self):
        other_client = auth_client(self.other_user)
        url = reverse('post-detail', kwargs={'slug': self.post.slug})
        resp = other_client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)


class PostActionsTests(TestCase):
    def setUp(self):
        self.author = create_user('author', role='author')
        self.other = create_user('other')
        self.post = create_post(self.author, title='Action Post', status_val='draft')

    def test_author_can_publish(self):
        client = auth_client(self.author)
        url = reverse('post-publish', kwargs={'slug': self.post.slug})
        resp = client.post(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.post.refresh_from_db()
        self.assertEqual(self.post.status, 'published')

    def test_other_user_cannot_publish(self):
        # Use a published post so the non-author can find it via get_object().
        # A viewer gets 404 for drafts (filtered out), so publish it first.
        published_post = create_post(self.author, title='Published Action Post', status_val='published')
        client = auth_client(self.other)
        url = reverse('post-publish', kwargs={'slug': published_post.slug})
        resp = client.post(url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_author_can_archive(self):
        self.post.status = 'published'
        self.post.save()
        client = auth_client(self.author)
        url = reverse('post-archive', kwargs={'slug': self.post.slug})
        resp = client.post(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.post.refresh_from_db()
        self.assertEqual(self.post.status, 'archived')

    def test_my_posts_returns_only_own_posts(self):
        create_post(self.other, title='Other Post', status_val='published')
        client = auth_client(self.author)
        url = reverse('post-my-posts')
        resp = client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        for p in resp.data:
            self.assertEqual(p['author']['username'], 'author')

    def test_my_posts_requires_auth(self):
        url = reverse('post-my-posts')
        resp = APIClient().get(url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


class PostFilterSearchTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.author = create_user('author', role='author')
        self.cat = create_category('Tech')
        self.tag = create_tag('python')
        self.post = create_post(self.author, title='Python Guide', status_val='published', category=self.cat)
        self.post.tags.add(self.tag)

    def test_filter_by_category_slug(self):
        url = reverse('post-list') + f'?category__slug={self.cat.slug}'
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(len(resp.data['results']) >= 1)

    def test_filter_by_tag_slug(self):
        url = reverse('post-list') + f'?tags__slug={self.tag.slug}'
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(len(resp.data['results']) >= 1)

    def test_search_by_title(self):
        url = reverse('post-list') + '?search=Python'
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        titles = [p['title'] for p in resp.data['results']]
        self.assertIn('Python Guide', titles)
