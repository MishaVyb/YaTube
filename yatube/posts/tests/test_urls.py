from typing import Dict, Optional, Tuple, Union
from http import HTTPStatus

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib import auth

from posts.models import Group, Post
from posts.urls import app_name
from core.functools.utils import reverse_next


User = auth.get_user_model()


class URLTests(TestCase):

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

    def setUp(self):

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
            title='Test group title',
            slug='test_group',
            description='Test group description',
        )
        self.post: Post = Post.objects.create(
            text='Test post text, which length is much more than 15 letters',
            author=self.user_author,
            group=self.group,
        )

        url_args = {
            'post_detail': [self.post.pk],
            'post_edit': [self.post.pk],
            'profile': [self.user.get_username()],
            'profile_follow': [self.user.get_username()],
            'profile_unfollow': [self.user.get_username()],
            'group_list': [self.group.slug],
        }
        self.url_reverse = {
            url: reverse(app_name + ':' + url, args=url_args.get(url, None))
            for url in self.URLS
        }

    def test_url_teplates(self):
        url_templates = {
            'index': '/index.html',
            'follow_index': '/follow.html',
            'post_create': '/create_post.html',
            'post_detail': '/post_detail.html',
            'post_edit': '/create_post.html',
            'profile': '/profile.html',
            'group_list': '/group_list.html',
        }

        for url_name, template in url_templates.items():
            url = self.url_reverse[url_name]
            with self.subTest(url=url, template=template):
                response = self.user_author_client.get(url)
                self.assertTemplateUsed(response, app_name + template)

    def test_urls_access_via_or_redirect(self):
        '''
        Test is trying access url by specific user and check a redirection.

        Input data defined inside method as dict, where:
            `key` - url name
            `value` - a sequence contained cases as tuples, where tuple's item:
                `[1]` - by which client make a request
                `[2]` - expected HTTPStatus
                `[3]` - redirect url if supposed to be
        '''

        data: Dict[
            str,
            Tuple[
                Tuple[
                    Client,
                    Union[HTTPStatus.OK, HTTPStatus.FOUND],
                    Optional[str],
                ],
                ...,
            ],
        ] = {
            # url ### via client ### status ### redirect if status is 302 #
            'index': (
                (self.guest_client, HTTPStatus.OK, None),
                (self.user_client, HTTPStatus.OK, None),
                (self.user_author_client, HTTPStatus.OK, None),
            ),
            'follow_index': (
                (
                    self.guest_client,
                    HTTPStatus.FOUND,
                    reverse_next(
                        'users:login', self.url_reverse['follow_index']
                    ),
                ),
                (self.user_client, HTTPStatus.OK, None),
                (self.user_author_client, HTTPStatus.OK, None),
            ),
            'post_create': (
                (
                    self.guest_client,
                    HTTPStatus.FOUND,
                    reverse_next(
                        'users:login', self.url_reverse['post_create']
                    ),
                ),
                (self.user_client, HTTPStatus.OK, None),
                (self.user_author_client, HTTPStatus.OK, None),
            ),
            'post_detail': (
                (self.guest_client, HTTPStatus.OK, None),
                (self.user_client, HTTPStatus.OK, None),
                (self.user_author_client, HTTPStatus.OK, None),
            ),
            'post_edit': (
                (
                    self.guest_client,
                    HTTPStatus.FOUND,
                    reverse_next('users:login', self.url_reverse['post_edit']),
                ),
                (
                    self.user_client,
                    HTTPStatus.FOUND,
                    self.url_reverse['post_detail'],
                ),
                (self.user_author_client, HTTPStatus.OK, None),
            ),
            'profile': (
                (self.guest_client, HTTPStatus.OK, None),
                (self.user_client, HTTPStatus.OK, None),
                (self.user_author_client, HTTPStatus.OK, None),
            ),
            'profile_follow': (
                (
                    self.guest_client,
                    HTTPStatus.FOUND,
                    reverse_next(
                        'users:login', self.url_reverse['profile_follow']
                    ),
                ),
                (
                    self.user_client,
                    HTTPStatus.FOUND,
                    self.url_reverse['profile'],
                ),
                (
                    self.user_author_client,
                    HTTPStatus.FOUND,
                    self.url_reverse['profile'],
                ),
            ),
            'profile_unfollow': (
                (
                    self.guest_client,
                    HTTPStatus.FOUND,
                    reverse_next(
                        'users:login', self.url_reverse['profile_unfollow']
                    ),
                ),
                (
                    self.user_client,
                    HTTPStatus.FOUND,
                    self.url_reverse['profile'],
                ),
                (
                    self.user_author_client,
                    HTTPStatus.FOUND,
                    self.url_reverse['profile'],
                ),
            ),
            'group_list': (
                (self.guest_client, HTTPStatus.OK, None),
                (self.user_client, HTTPStatus.OK, None),
                (self.user_author_client, HTTPStatus.OK, None),
            ),
        }

        for url_name, cases in data.items():
            url = self.url_reverse[url_name]
            for client, status, redirect in cases:
                with self.subTest(url=url, client=client, status=status):
                    response = client.get(url)
                    self.assertEqual(response.status_code, status)

                    if status == HTTPStatus.FOUND or redirect:
                        if status is not HTTPStatus.FOUND or redirect is None:
                            raise ValueError(
                                'HTTPStatus is not for redirection or '
                                'redirect url name is not define'
                            )
                        self.assertRedirects(response, redirect)

    def test_unexisting_url(self):
        responce = self.user_client.get('/some_unexisting_page/')
        self.assertEqual(responce.status_code, HTTPStatus.NOT_FOUND)
