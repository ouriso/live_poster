from django.contrib import admin

from .models import Comment, Group, Post


class GroupAdmin(admin.ModelAdmin):
    list_display = ("pk", "title", "slug", "description")
    prepopulated_fields = {'slug': ('title',)}
    empty_value_display = "-пусто-"


class PostAdmin(admin.ModelAdmin):
    list_display = ("pk", "text", "pub_date", "author", "group")
    search_fields = ("text",)
    list_filter = ("pub_date",)
    empty_value_display = "-пусто-"


class CommentAdmin(admin.ModelAdmin):
    list_display = ("pk", "author", "text", "created")
    list_filter = ("created",)
    empty_value_display = "-пусто-"


admin.site.register(Group, GroupAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(Comment, CommentAdmin)
