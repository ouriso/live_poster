from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from .models import Follow
from posts.models import Group, Post

User = get_user_model()


class TestFollows(TestCase):
    def setUp(self):
        self.client = Client()
        self.client2 = Client()
        self.client3 = Client()
        self.user = User.objects.create_user(
            first_name='Jerry',
            last_name='Mouse',
            username='jerry',
            email='jerry@disney.com',
            password='A12345a!'
        )
        self.user2 = User.objects.create_user(
            first_name='Tom',
            last_name='Cat',
            username='tom',
            email='tom@disney.com',
            password='A12345a!'
        )
        self.client.force_login(self.user)
        self.client2.force_login(self.user2)
        self.group = Group.objects.create(
            title='Cats',
            slug='cats',
            description='Only for cats'
        )
        self.post = Post.objects.create(
            text='First', group=self.group, author=self.user
        )
        self.client2.get(
            reverse('profile_follow', args=(self.user.username,))
        )

    def test_follow_unfollow(self):
        is_follow = Follow.objects.get(user=self.user2, author=self.user)
        self.assertTrue(is_follow)
        self.client2.get(
            reverse('profile_unfollow', args=(self.user.username,))
        )
        followers = Follow.objects.all().values_list('user', flat=True)
        self.assertNotIn(self.user2, followers)

    def test_follow_index(self):
        response = self.client2.get(reverse('follow_index'))
        post_template = response.context['page'][0]
        self.assertEqual(post_template.text, self.post.text)
        self.assertEqual(post_template.group.pk, self.post.group.pk)

    def test_not_follow_index(self):
        user3 = User.objects.create_user(
            first_name='Rex',
            last_name='Dog',
            username='rex',
            email='rex@disney.com',
            password='A12345a!'
        )
        self.client3.force_login(user3)
        response = self.client3.get(reverse('follow_index'))
        with self.assertRaises(IndexError):
            response.context['page'][0]
