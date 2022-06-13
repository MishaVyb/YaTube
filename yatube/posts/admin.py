from django.contrib import admin
from .models import Group, Post


class PostAdmin(admin.ModelAdmin):
    """Class describing a configuration of `Post` model at admin's site.
    Which field would be seen. Which fields would be editable or filtered by.
    """

    list_display = ('pk', 'text', 'created', 'author', 'group')
    list_editable = ('group',)
    search_fields = ('text',)
    list_filter = ('created',)
    empty_value_display = '-пусто-'


class GroupAdmin(admin.ModelAdmin):
    """Class describing a configuration of `Group` model at admin's site.
    Which field would be seen. Which fields would be editable or filtered by.
    """

    list_display = ('pk', 'title', 'description', 'slug')
    list_editable = ('title', 'description', 'slug')
    search_fields = ('title', 'description', 'slug')
    list_filter = ('title',)
    empty_value_display = '-пусто-'


admin.site.register(Post, PostAdmin)
admin.site.register(Group, GroupAdmin)
