import os
import shutil
import tempfile

from http import HTTPStatus


from django.test import TestCase, Client, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from posts.models import Group, Post
from posts.urls import app_name
from core.functools.utils import reverse_next
from posts.models import Comment
from yatube.settings import BASE_DIR

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class FormTests(TestCase):

    URLS = {
        'index': '',
        'post_create': '/create/',
        'post_detail': 'posts/<int:post_id>/',
        'add_comment': 'posts/<int:post_id>/comment/',
        'post_edit': '/posts/<int:post_id>/edit/',
        'profile': '/profile/<str:username>/',
        'group_list': '/group/<slug:slug>/',
    }

    @classmethod
    def setUpClass(cls) -> None:
        return super().setUpClass()

    @classmethod
    def tearDownClass(cls) -> None:
        return super().setUpClass()

    def setUp(self) -> None:
        self.user: User = User.objects.create_user(username='test_user')
        self.user_client = Client()
        self.user_client.force_login(self.user)
        self.guest_client = Client()

        self.group: Group = Group.objects.create(
            title='Тестовая группа',
            slug='test_group',
            description='Тестовое описание группы',
        )

        self.post: Post = Post.objects.create(
            text=(
                f'Тестовый пост в группе {self.group}.'
                f'Автор поста {self.user}'
            ),
            author=self.user,
            group=self.group,
        )

        url_args = {
            'post_detail': [self.post.pk],
            'add_comment': [self.post.pk],
            'post_edit': [self.post.pk],
            'profile': [self.user.get_username()],
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

    def test_post_create_guest_client(self):
        test_text = 'I see you my friend'
        form_data = {'text': test_text}
        response = self.guest_client.post(
            self.url_reverse['post_create'], data=form_data, follow=True
        )

        self.assertRedirects(
            response,
            reverse_next('users:login', self.url_reverse['post_create']),
        )
        self.assertFalse(Post.objects.filter(text=test_text).exists())

    def test_post_create_no_group_auth_client(self):
        test_text = 'I see you my friend'
        form_data = {'text': test_text}
        response = self.user_client.post(
            self.url_reverse['post_create'], data=form_data, follow=True
        )

        self.assertRedirects(response, self.url_reverse['profile'])

        self.assertEqual(Post.objects.first().text, test_text)
        self.assertFalse(
            Post.objects.filter(group__isnull=False, text=test_text).exists()
        )

    def test_post_create_with_group_auth_client(self):
        test_text = 'I see you my friend'
        test_group_choise = self.group.pk
        form_data = {'text': test_text, 'group': test_group_choise}
        response = self.user_client.post(
            self.url_reverse['post_create'], data=form_data, follow=True
        )

        self.assertRedirects(response, self.url_reverse['profile'])

        self.assertEqual(Post.objects.first().text, test_text)
        self.assertEqual(Post.objects.first().group, self.group)
        self.assertFalse(
            Post.objects.filter(group__isnull=True, text=test_text).exists()
        )

    def test_post_create_guest_client(self):
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

    def test_post_edit_author_client(self):
        old_text = self.post.text
        new_text = 'This post just has edited by author'
        new_group = Group.objects.create(title='new group', slug='new')
        form_data = {'text': new_text, 'group': new_group.pk}
        response = self.user_client.post(
            self.url_reverse['post_edit'], data=form_data, follow=True
        )

        self.assertRedirects(response, self.url_reverse['post_detail'])

        self.assertTrue(new_group.posts.filter(text=new_text).exists())
        self.assertFalse(Post.objects.filter(text=old_text).exists())
        self.assertFalse(self.group.posts.filter(text=new_text).exists())

    def test_post_edit_another_user_client(self):
        another_user_client = Client()
        another_user_client.force_login(
            User.objects.create(username='not post author')
        )

        old_text = self.post.text
        old_group = self.post.group
        new_text = 'This post just has edited by another user'
        new_group = Group.objects.create(title='new group', slug='new')
        form_data = {'text': new_text, 'group': new_group.pk}
        response = another_user_client.post(
            self.url_reverse['post_edit'], data=form_data, follow=True
        )

        self.assertRedirects(response, self.url_reverse['post_detail'])
        self.assertEqual(
            Post.objects.filter(text=old_text).first().group, old_group
        )
        self.assertTrue(Post.objects.filter(text=old_text).exists())
        self.assertFalse(Post.objects.filter(text=new_text).exists())

    def test_post_create_and_edit_invalid_form_blank_text(self):
        def __test(blank_text, url_name):
            form_data = {'text': blank_text}
            response = self.user_client.post(
                self.url_reverse[url_name],
                data=form_data,
                follow=True,
            )

            self.assertFormError(
                response,
                form='form',
                field='text',
                errors=['....постой пост отправить нельзя...'],
            )
            self.assertFalse(Post.objects.filter(text=blank_text).exists())
            self.assertEqual(response.status_code, HTTPStatus.OK)

        for blank_text in ('', '   ', '\n', '  \n  \n '):
            for url_name in ('post_edit', 'post_create'):
                with self.subTest(text=blank_text, url=url_name):
                    __test(blank_text, url_name)

    def test_post_create_with_image_auth_client(self):
        test_text = 'some post with group and image'
        test_group_choise = self.group.pk
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        test_image = SimpleUploadedFile(
            name='small.gif', content=small_gif, content_type='image/gif'
        )
        form_data = {
            'text': test_text,
            'group': test_group_choise,
            'image': test_image,
        }
        response = self.user_client.post(
            self.url_reverse['post_create'], data=form_data, follow=True
        )

        self.assertRedirects(response, self.url_reverse['profile'])

        self.assertEqual(Post.objects.first().text, test_text)
        self.assertEqual(Post.objects.first().group, self.group)
        self.assertEqual(
            Post.objects.first().image.name,
            os.path.join(app_name, test_image.name),
        )
        self.assertFalse(
            Post.objects.filter(group__isnull=True, text=test_text).exists()
        )

    def test_post_comment_user_client(self):
        """Test is trying leave a comment by `user client` and expecting:

        `1` redirection to the same page
        `2` comment left under current post
        """
        comment_text = 'No, you can not see me, I am hiding'
        comment_form = {'text': comment_text}
        response = self.user_client.post(
            self.url_reverse['add_comment'], data=comment_form, follow=True
        )

        self.assertRedirects(response, self.url_reverse['post_detail'])
        self.assertEqual(
            Comment.objects.get(text=comment_text).post, self.post
        )

    def test_post_comment_guest_client(self):
        """Test is trying leave a comment by `guest client` and expecting:

        `1` redirection to login page
        `2` comment has not added to data base
        """
        comment_text = 'No, you can not see me, I am hiding'
        comment_form = {'text': comment_text}
        response = self.guest_client.post(
            self.url_reverse['add_comment'], data=comment_form, follow=True
        )

        self.assertRedirects(
            response,
            reverse_next('users:login', self.url_reverse['add_comment']),
        )
        self.assertFalse(Comment.objects.filter(text=comment_form).exists())
