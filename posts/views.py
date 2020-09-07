from datetime import datetime

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import CommentForm, PostForm
from .models import Group, Post


def index(request):
    post_list = Post.objects.all()
    return paginator_render(request, 'index.html', {}, post_list)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    return paginator_render(request, 'group.html', {'group': group}, post_list)


@login_required
def new_post(request):
    context = {'new_or_edit': ('Добавить запись', 'Добавить'), }
    if not request.method == 'POST':
        context['form'] = PostForm()
        return render(request, 'new.html', context)

    form = PostForm(request.POST)
    context['form'] = form
    if form.is_valid():
        form_commit = form.save(commit=False)
        form_commit.author = request.user
        form_commit.save()
        return redirect('index')
    return render(request, 'new.html', context)


def profile(request, username):
    author = get_object_or_404(get_user_model(), username=username)
    posts = author.posts.all()
    following = True if request.user.follower.filter(author=author) else False
    template = 'profile.html'
    context = {
        'following': following,
        'author': author,
    }
    return paginator_render(request, template, context, posts)


def post_view(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, pk=post_id)
    comments = post.comments.all()
    posts_count = post.author.posts.count()
    url = reverse(
        'post', kwargs={'username': username, 'post_id': post_id}
    )
    form = CommentForm(request.POST)
    context = {
        'post': post,
        'form': form,
    }
    return paginator_render(request, 'post.html', context, comments)


def post_edit(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, pk=post_id)
    url = reverse(
        'post', kwargs={'username': username, 'post_id': post_id}
    )
    if not request.user == post.author:
        return redirect(url)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    context = {
        'new_or_edit': ('Редактировать запись', 'Сохранить'),
        'post': post,
        'form': form,
    }

    if form.is_valid():
        form.save()
        return redirect(url)
    return render(request, 'new.html', context)


def add_comment(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, pk=post_id)
    url = reverse(
        'post', kwargs={'username': username, 'post_id': post_id}
    )
    form = CommentForm(request.POST)
    context = {'form': form}
    if form.is_valid():
        form_commit = form.save(commit=False)
        form_commit.post = post
        form_commit.author = request.user
        form_commit.save()
        return redirect(url)
    return render(request, 'comments.html', context)


def paginator_render(request, template, context, queryset, num_items=10):
    paginator = Paginator(queryset, num_items)
    page = paginator.get_page(request.GET.get('page'))
    context = context
    context['paginator'] = paginator
    context['page'] = page
    return render(request, template, context)


def page_not_found(request, exception):
    return render(
        request,
        'misc/404.html',
        {'path': request.path},
        status=404
    )


def server_error(request):
    return render(request, 'misc/500.html', status=500)