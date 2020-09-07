from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
# from django.core.paginator import Paginator

from .models import Follow
from posts.models import Post
from posts.views import paginator_render


User = get_user_model()

@login_required
def follow_index(request):
    subscriptions = request.user.follower.all()
    subs = [entry.author for entry in subscriptions]
    # это ведь можно было одним запросом сделать?
    posts = Post.objects.filter(author__in=subs).distinct()
    return paginator_render(request, 'follow.html', {}, posts)

@login_required
def profile_follow(request, username):
    follower = request.user
    following = get_object_or_404(User, username=username)
    object_exists = Follow.objects.filter(user=follower, author=following)
    if not username == follower.username and not object_exists:        
        Follow.objects.create(user=follower, author=following)
    return redirect('profile', username)

@login_required
def profile_unfollow(request, username):
    follower = request.user
    following = get_object_or_404(User, username=username)
    object_exists = Follow.objects.filter(user=follower, author=following)
    object_exists.delete()
    return redirect('profile', username)

def profile(request, username):
    author = get_object_or_404(get_user_model(), username=username)
    posts = author.posts.all()
    # following = True if request.user.follower.filter(author=author) else False
    template = 'profile.html'
    context = {
        'following': following,
        'author': author,
    }
    return paginator_render(request, template, context, posts)
