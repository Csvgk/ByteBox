from django.contrib import admin

from .models import Category, Comment, Post, Tag


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name']
    prepopulated_fields = {'slug': ['name']}


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name']
    prepopulated_fields = {'slug': ['name']}


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'author', 'is_published', 'created_at']
    list_filter = ['is_published', 'category', 'created_at']
    list_editable = ['is_published']
    search_fields = ['title', 'excerpt', 'content']
    prepopulated_fields = {'slug': ['title']}
    filter_horizontal = ['tags']
    inlines = [CommentInline]


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['author', 'post', 'created_at']
    search_fields = ['text', 'author__username']
