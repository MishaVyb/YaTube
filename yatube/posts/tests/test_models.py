from typing import Dict

from django import test
from django.contrib import auth
from django.db import models

from posts.models import Group, Post

User = auth.get_user_model()


class ModelTestBaseTools(test.TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username='test_user')
        self.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_group',
            description='Тестовое описание группы',
        )
        self.post = Post.objects.create(
            text='Тестовый пост с группой, длинна которого больше 15 символов',
            author=self.user,
            group=self.group,
        )
        return super().setUp()

    def fields_meta_checker(
        self,
        test_model: models.Model,
        field_verboses: Dict[str, str],
        field_attribute: str,
    ) -> None:
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    getattr(
                        test_model._meta.get_field(field), field_attribute
                    ),
                    expected_value,
                )


class PostModelTest(ModelTestBaseTools):

    field_verboses = {
        'text': 'Текст поста',
        'group': 'Группа',
    }

    field_help_text = {
        'text': 'Текст нового поста',
        'group': 'Группа, к которой будет относиться пост',
    }
    field_error_messages = {'text': {'required': 'Напишите хоть что-нибудь!'}}

    def test_str_method(self):
        self.assertEqual(str(self.post), self.post.text[:15] + '...')

    def test_verbose_name(self) -> None:
        self.fields_meta_checker(
            self.post, self.field_verboses, 'verbose_name'
        )

    def test_help_text(self) -> None:
        self.fields_meta_checker(self.post, self.field_help_text, 'help_text')


class GroupModelTest(ModelTestBaseTools):

    field_verboses = {
        'title': 'Название',
        'slug': 'slug',
        'description': 'Описание',
    }

    field_help_text = {
        'title': '',
        'slug': '',
        'description': '',
    }

    def test_str_method(self):
        self.assertEqual(str(self.group), 'Тестовая группа')

    def test_verbose_name(self) -> None:
        self.fields_meta_checker(
            self.group, self.field_verboses, 'verbose_name'
        )

    def test_help_text(self) -> None:
        self.fields_meta_checker(self.group, self.field_help_text, 'help_text')
