from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.test import Client, TestCase
from django.urls import reverse

from .models import Group, Post

User = get_user_model()


class TestPosts(TestCase):
    def setUp(self):
        self.client = Client()
        self.client2 = Client()
        user = User.objects.create_user(
            first_name='Jerry',
            last_name='Mouse',
            username='jerry',
            email='jerry@disney.com',
            password='A12345a!'
        )
        self.client.force_login(user)
        self.group = Group.objects.create(
            title='Cats',
            slug='cats',
            description='Only for cats'
        )
        self.group2 = Group.objects.create(
            title='Antirats',
            slug='antirats',
            description='For rats haters'
        )
        self.context = {
            'group': self.group.pk,
            'text': 'Lets go!',
        }
        self.context2 = {
            'group': self.group2.pk,
            'text': 'Ohhhh, nooooo!',
        }

    def test_profile_exist(self):
        response = self.client.get(reverse('profile', args=('jerry',)))
        self.assertEqual(response.status_code, 200)

    def test_auth(self):
        response = self.create_post(self.client)
        post = Post.objects.get(
            pk=1,
            text=self.context['text'],
            group=self.context['group']
        )
        self.assertTrue(post)

    def test_not_auth(self):
        posts_before = Post.objects.all().count()
        response = self.create_post(self.client2)
        posts_after = Post.objects.all().count()
        self.assertEqual(posts_after, posts_before)

    def test_group(self):
        response = self.client.get(reverse('group', args=('cats',)))
        self.assertEqual(response.status_code, 200)

    def test_post_exist(self):
        post = Post.objects.create(
            text=self.context['text'],
            author=User.objects.get(username='jerry'),
            group=self.group
        )
        self.response_asserts('cats', self.context)

    def test_wrong_user(self):
        post = self.create_post(self.client)
        user2 = User.objects.create(
            first_name='Tom',
            last_name='Cat',
            username='tom',
            email='tom@disney.com',
            password='A12345a!'
        )
        self.client2.force_login(user2)
        url = reverse('post_edit', args=('jerry', 1,))
        post_upd = self.client2.post(url, self.context2)
        post = Post.objects.get(pk=1)
        self.assertEqual(post.text, self.context['text'])
        self.assertEqual(post.group.pk, self.context['group'])

    def test_post_edit(self):
        post = self.create_post(self.client)
        url = reverse('post_edit', args=('jerry', 1,))
        post_upd = self.client.post(url, self.context2)
        self.response_asserts('antirats', self.context2)

    def create_post(self, client):
        return client.post(reverse('new_post'), self.context, follow=True)

    def response_asserts(self, group, context):
        responses = (
            self.client.get(reverse('index')),
            self.client.get(reverse('group', args=(group,))),
            self.client.get(reverse('profile', args=('jerry',))),
        )
        for response in responses:
            post_template = response.context['page'][0]
            self.assertEqual(post_template.text, context['text'])
            self.assertEqual(post_template.group.pk, context['group'])


class TestErrors(TestCase):
    def test_404(self):
        client = Client()
        response = client.get('/news/')
        self.assertEqual(response.status_code, 404)
