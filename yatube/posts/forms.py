from django import forms
from .models import Comment, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = (
            'text',
            'group',
            'image',
        )
        widgets = {'text': forms.Textarea()}
        error_messages = {
            'text': {'required': "....постой пост отправить нельзя..."},
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        error_messages = {
            'text': {'required': "....постой комментарий оставить нельзя..."},
        }
