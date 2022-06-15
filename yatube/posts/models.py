from django.db import models
from django.contrib.auth import get_user_model

from core.models import CreatedModel


User = get_user_model()


class Group(models.Model):
    """
    Group is a model contains data about YaTube group (society).

    Parameters
    ----------
    title: `char` `max_length=200`
        Group name.
    slug: `slug` `unique=True`
        Uniq URL adress. ASCII (unicode is not supported).
    description: `text` `blank=True`
        A text describing the community.
        This text will be displayed on the community page.
    """

    title = models.CharField('Название', max_length=200)
    slug = models.SlugField('slug', unique=True)
    description = models.TextField('Описание', blank=True)

    class Meta:
        verbose_name = 'группа'
        verbose_name_plural = 'группы'

    def __str__(self) -> str:
        return self.title


class Post(CreatedModel):
    """
    Post is a model contains data about user publication.

    Parameters
    ----------
    text: `text` `blank=True`
        Main content of the publication.
    author: `User`
        Foreign key to certain user who made a publication.
        Also User model contains related keys to all its publications.
            (related_name `posts`)
    group: `Group` `blank=True`
        Foreign key to a group which this post is belongs to.
        Also Group model contains related keys to all its publications.
            (related_name `posts`)
    """

    text = models.TextField(
        verbose_name='Текст поста',
        help_text='Текст нового поста',
        error_messages={'required': 'Напишите хоть что-нибудь!'},
    )
    image = models.ImageField('Картинка', upload_to='posts/', blank=True)
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='posts'
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        related_name='posts',
        blank=True,
        null=True,
        verbose_name='Группа',
        help_text='Группа, к которой будет относиться пост',
    )

    class Meta(CreatedModel.Meta):
        verbose_name = 'пост'
        verbose_name_plural = 'посты'

    def __str__(self) -> str:
        return self.text[:15] + '...'


class Comment(CreatedModel):

    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        blank=False,
        verbose_name='Пост',
        help_text='Пост, к которому будет относится комментарий',
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='comments'
    )
    text = models.TextField(
        verbose_name='Комментарий',
        help_text='Текст комментария к посту',
        error_messages={'required': 'Пустой комментарий оставить нельзя.'},
    )

    class Meta(CreatedModel.Meta):
        verbose_name = 'комментарий'
        verbose_name_plural = 'комментарии'

    def __str__(self) -> str:
        return self.text[:15] + '...'


class Follow(models.Model):
    """
    `user` — ссылка на объект пользователя, который подписывается.
    `author` — ссылка на объект пользователя, на которого подписываются.
    """

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='follower'
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='following'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=('user', 'author'), name='unique')
        ]
