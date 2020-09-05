from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .models import Follow
from posts.models import Post
from posts.views import paginator_render


User = get_user_model()

@login_required
def follow_index(request):
    # user = get_object_or_404(get_user_model(), username=request.user.username)
    # posts = user.follower.posts.all()
    # posts = get_object_or_404(Post, author=request.user__follower)
    user_follower = request.user
    subscriptions = Follow.objects.get(user=user_follower)
    posts = subscriptions.select_related('user__posts')
    # posts = get_object_or_404(Post, author=subscriptions)
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
