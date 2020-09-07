from django.urls import path

from . import views

urlpatterns = [
    # path('<str:username>/', views.profile, name='profile'),
    path('follow/', views.follow_index, name='follow_index'),
    path(
        '<str:username>/follow/',
        views.profile_follow,
        name='profile_follow'
    ),
    path(
        '<str:username>/unfollow/',
        views.profile_unfollow,
        name='profile_unfollow'
    ),
]
