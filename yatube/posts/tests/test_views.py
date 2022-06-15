import shutil
import tempfile


from http import HTTPStatus
from django import forms
from django.db.models.fields.files import ImageFieldFile
from django.http.response import HttpResponse
from django.test import TestCase, Client, override_settings
from django.contrib.auth import get_user_model
from django.core.paginator import Page
from django.urls import reverse
from django.test.utils import ContextList
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from django.db.models import QuerySet


from posts.models import Group, Post, Follow
from posts.urls import app_name
from core.functools.utils import lastloop
from core.functools.utils import reverse_next

from yatube.settings import POSTS_PER_PAGE, BASE_DIR


User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ViewTests(TestCase):

    URLS = {
        'index': '',
        'follow_index': '/follow/',
        'post_create': '/create/',
        'post_detail': 'posts/<int:post_id>/',
        'post_edit': '/posts/<int:post_id>/edit/',
        'profile': '/profile/<str:username>/',
        'profile_follow': '/profile/<str:username>/follow/',
        'profile_unfollow': '/profile/<str:username>/unfollow/',
        'group_list': '/group/<slug:slug>/',
    }

    @classmethod
    def setUpClass(cls) -> None:
        return super().setUpClass()

    @classmethod
    def tearDownClass(cls) -> None:
        return super().setUpClass()

    def setUp(self) -> None:
        cache.clear()

        self.user: User = User.objects.create_user(username='test_user')
        self.user_author: User = User.objects.create_user(
            username='post_author'
        )

        self.guest_client = Client()
        self.user_client = Client()
        self.user_client.force_login(self.user)
        self.user_author_client = Client()
        self.user_author_client.force_login(self.user_author)

        self.group: Group = Group.objects.create(
            title='Тестовая группа',
            slug='test_group',
            description='Тестовое описание группы',
        )

        self.posts_amount = {
            'by author': {'no group': 27, 'with group': 33, 'total': 27 + 33},
            'by user': {'no group': 14, 'with group': 0, 'total': 14 + 0},
            'total': 27 + 33 + 14 + 0,
        }
        amount = self.posts_amount['by user']['no group']
        Post.objects.bulk_create(
            [
                Post(
                    text=(
                        f'Пост {i}/{amount} без группы.'
                        f'Автор поста {self.user}'
                    ),
                    author=self.user,
                )
                for i in range(amount)
            ]
        )
        amount = self.posts_amount['by author']['no group']
        Post.objects.bulk_create(
            [
                Post(
                    text=(
                        f'Пост {i}/{amount} без группы.'
                        f'Автор поста {self.user_author}'
                    ),
                    author=self.user_author,
                )
                for i in range(amount)
            ]
        )
        amount = self.posts_amount['by author']['with group']
        Post.objects.bulk_create(
            [
                Post(
                    text=(
                        f'Пост {i}/{amount} в группе {self.group}.'
                        f'Автор поста {self.user_author}'
                    ),
                    author=self.user_author,
                    group=self.group,
                )
                for i in range(amount)
            ]
        )

        test_post: Post = (
            Post.objects.select_related('author', 'group')
            .filter(author=self.user_author, group=self.group)
            .first()
        )

        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif', content=small_gif, content_type='image/gif'
        )
        test_post.image = uploaded
        test_post.save()

        url_args = {
            'post_detail': [test_post.pk],
            'post_edit': [test_post.pk],
            'profile': [self.user_author.get_username()],
            'profile_follow': [self.user_author.get_username()],
            'profile_unfollow': [self.user_author.get_username()],
            'group_list': [self.group.slug],
        }
        self.url_reverse = {
            url: reverse(app_name + ':' + url, args=url_args.get(url, None))
            for url in self.URLS
        }

        return super().setUp()

    def tearDown(self) -> None:
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        return super().tearDown()

    def test_context(self) -> None:
        expected_context = {
            'index': ('page_obj',),
            'post_create': ('is_edit', 'form'),
            'post_detail': ('post',),
            'post_edit': ('is_edit', 'form'),
            'profile': ('profile', 'page_obj'),
            'group_list': ('group', 'page_obj'),
        }
        form_field_types = {
            'text': forms.CharField,
            'group': forms.ChoiceField,
        }
        for url_name, attrs in expected_context.items():
            response: HttpResponse = self.user_author_client.get(
                self.url_reverse[url_name]
            )
            context: ContextList = response.context
            for attr in attrs:
                with self.subTest(url=url_name, attr=attr):
                    self.assertIn(attr, context.keys())

                    if attr == 'form':
                        for field_name, expected in form_field_types.items():
                            result = context[attr].fields[field_name]
                            self.assertIsInstance(result, expected)

    def test_context_for_post_with_image(self):
        urls_contained_post_with_image = (
            'index',
            'post_detail',
            'profile',
            'group_list',
        )
        post_attr_types = (
            ('author', User),
            ('group', Group),
            ('text', str),
            ('image', ImageFieldFile),
        )

        for url in urls_contained_post_with_image:
            url = self.url_reverse[url]
            context: ContextList = self.user_author_client.get(url).context
            try:
                post: Post = context['page_obj'][0]
            except KeyError:
                post: Post = context['post']
            for attr, expected_type in post_attr_types:
                self.assertTrue(hasattr(post, attr))
                self.assertIsInstance(getattr(post, attr), expected_type)

    def test_posts_amount_after_filter_and_paginator(self) -> None:
        '''Test is filtering posts and checks expected posts amount with
        resulting.

        Input data defined inside method as dict, where:
            `key` - url name
            `value` - a tuple, where:
                `[1]` - a QuerySet filtered in supposed way
                `[2]` - amounts defiend at setUp
        '''
        data = {
            'index': (
                Post.objects.all().count(),  # result
                self.posts_amount['total'],  # expected
            ),
            'group_list': (
                Post.objects.filter(group__isnull=False).count(),
                self.posts_amount['by author']['with group']
                + self.posts_amount['by user']['with group'],
            ),
            'profile': (
                Post.objects.filter(author=self.user_author).count(),
                self.posts_amount['by author']['total'],
            ),
        }
        for url_name, (result, expected) in data.items():
            self.assertEqual(result, expected)
            posts_amount = result

            pages_amount = posts_amount // POSTS_PER_PAGE
            last_page_posts_amount = posts_amount % POSTS_PER_PAGE

            if last_page_posts_amount:
                pages_amount += 1
            else:
                last_page_posts_amount = POSTS_PER_PAGE

            for i, last in lastloop(range(1, pages_amount + 1)):
                with self.subTest(page=i):

                    url = self.url_reverse[url_name] + f'?page={i}'
                    context: ContextList = self.guest_client.get(url).context

                    page: Page = context['page_obj']

                    if not last:
                        self.assertEqual(len(page), POSTS_PER_PAGE)
                    else:
                        self.assertEqual(len(page), last_page_posts_amount)

    def test_new_post_created(self) -> None:
        new_group: Group = Group.objects.create(
            title='Тестовая группа',
            slug='new_test_group',
            description='Тестовое описание группы',
        )

        new_post: Post = Post.objects.create(
            text=(
                f'Дополнительный тестовый пост.'
                f'Автор поста {self.user_author}'
            ),
            author=self.user_author,
            group=new_group,
        )

        context: ContextList = self.user_author_client.get(
            self.url_reverse['index']
        ).context
        self.assertEqual(context['page_obj'][0], new_post)

        context = self.user_author_client.get(
            reverse('posts:group_list', args=['new_test_group'])
        ).context
        self.assertEqual(context['page_obj'][0], new_post)

        context = self.user_author_client.get(
            self.url_reverse['group_list']
        ).context
        self.assertNotIn(new_post, context['page_obj'])

        context = self.user_author_client.get(
            self.url_reverse['profile']
        ).context
        self.assertEqual(context['page_obj'][0], new_post)

        context = self.user_author_client.get(
            reverse('posts:profile', args=['test_user'])
        ).context
        self.assertNotIn(new_post, context['page_obj'])

    def test_post_create_guest_client(self):
        """Проверим поведение вьюхи с неавторизированным пользоваетелм.
        Пост реально не должен создаваться в базе.
        """
        test_text = 'I am not a user, but trying to create a post'
        test_group_choise = self.group.pk
        form_data = {'text': test_text, 'group': test_group_choise}
        response = self.guest_client.post(
            self.url_reverse['post_create'], data=form_data, follow=True
        )

        self.assertRedirects(
            response,
            reverse_next('users:login', self.url_reverse['post_create']),
        )
        self.assertFalse(Post.objects.filter(text=test_text).exists())

    def test_post_edit_another_user_client(self):
        """Проверим поведение вьюхи с неавторизированным пользоваетелм.
        Пост не должен редактироваться, текст и группа останутся оригинальными.
        """
        another_user_client = Client()
        another_user_client.force_login(
            User.objects.create(username='not post author')
        )

        old_text = Post.objects.first().text
        old_group = Post.objects.first().group
        new_text = 'This post just has edited by another user'
        new_group = Group.objects.create(title='new group', slug='new')
        form_data = {'text': new_text, 'group': new_group.pk}
        response = another_user_client.post(
            self.url_reverse['post_edit'], data=form_data, follow=True
        )

        self.assertRedirects(response, self.url_reverse['post_detail'])
        self.assertTrue(Post.objects.filter(text=old_text).exists())
        self.assertEqual(
            Post.objects.filter(text=old_text).first().group, old_group
        )
        self.assertFalse(Post.objects.filter(text=new_text).exists())

    def test_cache_applyes(self):
        """Test is requesting url for making a cache and expecting:

        `1` - post is steal appear at the page even after deleting it.\n
        `2` - post disappears from page after clearing a cache.
        """
        urls = ('index',)
        for url in urls:
            url = self.url_reverse[url]
            with self.subTest(url=url):
                self.user_client.get(url)
                deleted: Post = Post.objects.first()
                Post.delete(deleted)

                response: HttpResponse = self.user_client.get(url)
                http_content: str = response.content.decode("utf-8")
                self.assertIn(deleted.text, http_content)

                cache.clear()
                response = self.user_client.get(url)
                http_content = response.content.decode("utf-8")
                self.assertNotIn(deleted.text, http_content)

    def test_follow_and_unfollow_other_authors_by_user_client(self):
        """Test is trying follow/unfollow other authors by user client and
        expecting:

        `1` - `profile_follow` creates only one Follow instance (even if there
        are many such requests).\n
        `2` - `user` as a follower has `author` object.\n
        `3` - `user` as a following has no objects (because nobody is following
        him).\n
        `4` - `author` as following has `user` object.\n
        `5` - `author` as follower has no objects (because he is not a
        follower).\n
        `6` - `profile_unfollow` deletes Follow objects for `user` and
        `author`.\n
        `7` - by many requests to `profile_unfollow` nothing breaks down.\n
        """
        repeats_amount = 7

        for _ in range(repeats_amount):
            self.user_client.get(self.url_reverse['profile_follow'])

        self.user_client.get(self.url_reverse['profile_follow'])
        query: QuerySet = Follow.objects.filter(user=self.user)

        self.assertEqual(query.count(), 1)

        self.assertEqual(self.user.follower.last().author, self.user_author)
        self.assertFalse(self.user.following.all())

        self.assertEqual(self.user_author.following.last().user, self.user)
        self.assertFalse(self.user_author.follower.all())

        self.user_client.get(self.url_reverse['profile_unfollow'])
        self.assertFalse(Follow.objects.filter(user=self.user))
        self.assertFalse(Follow.objects.filter(author=self.user_author))

        for _ in range(repeats_amount):
            self.assertEqual(
                self.user_client.get(
                    self.url_reverse['profile_unfollow']
                ).status_code,
                HTTPStatus.FOUND,
            )

    def test_follow_index_contains_only_following_posts(self):
        """Test is creating a new `author` post and expecting:

        `1` - on follow page for follower new post appears.
        `2` - on follow page for not follower new post does not appear.
        """

        follower_user: User = User.objects.create(username='follower_user')
        follower_client = Client()
        follower_client.force_login(follower_user)
        follower_client.get(self.url_reverse['profile_follow'])

        new_post: Post = Post.objects.create(
            text='Haters gonna hate!', author=self.user_author
        )

        context: ContextList
        context = follower_client.get(self.url_reverse['follow_index']).context
        self.assertEqual(context['page_obj'][0], new_post)

        context = self.user_client.get(
            self.url_reverse['follow_index']
        ).context
        self.assertEqual(len(context['page_obj']), 0)
