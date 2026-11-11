from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import CommentForm, PostForm
from .models import Category, Comment, Post, Tag


def sidebar():
    return {
        'blog_categories': Category.objects.annotate(
            num_posts=Count('posts', filter=Q(posts__is_published=True))).filter(num_posts__gt=0),
        'blog_tags': Tag.objects.filter(posts__is_published=True).distinct(),
    }


def post_list(request):
    posts = Post.published.select_related('category', 'author').prefetch_related('tags')

    category = tag = None
    if request.GET.get('category'):
        category = get_object_or_404(Category, slug=request.GET['category'])
        posts = posts.filter(category=category)
    if request.GET.get('tag'):
        tag = get_object_or_404(Tag, slug=request.GET['tag'])
        posts = posts.filter(tags=tag)

    query = request.GET.get('q', '').strip()
    if query:
        posts = posts.filter(Q(title__icontains=query) | Q(excerpt__icontains=query) | Q(content__icontains=query))

    page_obj = Paginator(posts, 6).get_page(request.GET.get('page'))
    context = {'page_obj': page_obj, 'category': category, 'tag': tag, 'query': query, **sidebar()}
    return render(request, 'blog/post_list.html', context)


def post_detail(request, slug):
    post = get_object_or_404(Post.published.select_related('category', 'author'), slug=slug)

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            messages.success(request, 'Коментар додано!')
            return redirect(post.get_absolute_url() + '#comments')
    else:
        form = CommentForm()

    context = {
        'post': post,
        'comments': post.comments.select_related('author'),
        'form': form,
        'more_posts': Post.published.exclude(id=post.id)[:3],
        **sidebar(),
    }
    return render(request, 'blog/post_detail.html', context)


@login_required
@permission_required('blog.add_post', raise_exception=True)
def post_create(request):
    form = PostForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        form.save_m2m()
        messages.success(request, 'Статтю опубліковано.')
        return redirect(post.get_absolute_url())
    return render(request, 'blog/post_form.html', {'form': form, 'title': 'Нова стаття'})


@login_required
@permission_required('blog.change_post', raise_exception=True)
def post_update(request, slug):
    post = get_object_or_404(Post, slug=slug)
    form = PostForm(request.POST or None, request.FILES or None, instance=post)
    if form.is_valid():
        form.save()
        messages.success(request, 'Статтю оновлено.')
        return redirect(post.get_absolute_url())
    return render(request, 'blog/post_form.html', {'form': form, 'title': 'Редагування статті', 'post': post})


@login_required
@permission_required('blog.delete_post', raise_exception=True)
def post_delete(request, slug):
    post = get_object_or_404(Post, slug=slug)
    if request.method == 'POST':
        post.delete()
        messages.info(request, f'Статтю «{post.title}» видалено.')
        return redirect('blog:post_list')
    return render(request, 'blog/post_confirm_delete.html', {'post': post})


@login_required
def comment_update(request, pk):
    comment = get_object_or_404(Comment, pk=pk, author=request.user)
    form = CommentForm(request.POST or None, instance=comment)
    if form.is_valid():
        form.save()
        messages.success(request, 'Коментар оновлено.')
        return redirect(comment.post.get_absolute_url() + '#comments')
    return render(request, 'blog/comment_form.html', {'form': form, 'comment': comment})


@login_required
@require_POST
def comment_delete(request, pk):
    comment = get_object_or_404(Comment, pk=pk, author=request.user)
    post_url = comment.post.get_absolute_url()
    comment.delete()
    messages.info(request, 'Коментар видалено.')
    return redirect(post_url + '#comments')
