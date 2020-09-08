import time

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.test import Client, TestCase
from django.urls import reverse

from .models import Comment, Follow, Group, Post

User = get_user_model()


class TestPosts(TestCase):
    def setUp(self):
        self.client = Client()
        self.client2 = Client()
        self.user = User.objects.create_user(
            first_name='Jerry',
            last_name='Mouse',
            username='jerry',
            email='jerry@disney.com',
            password='A12345a!'
        )
        self.client.force_login(self.user)
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

    def test_post_auth(self):
        response = self.create_post(self.client)
        post = Post.objects.get(
            pk=1,
            text=self.context['text'],
            group=self.context['group']
        )
        self.assertTrue(post)

    def test_post_not_auth(self):
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

    def test_img_post(self):
        with open('media/posts/file.jpg','rb') as img: 
            post = self.client.post(
                reverse('new_post'),
                {'author': self.user, 'text': 'post with image', 'image': img}
            )
        arg=(self.user.username, 1)
        response = self.client.get(reverse('post', args=arg)).context[0]
        self.assertTrue(response['post'].image)

    def test_comments_auth(self):
        post = self.create_post(self.client)
        arg=(self.user.username, 1)
        url = reverse('add_comment', args=arg)
        self.client.post(url, {'text': self.context2['text']})
        response = self.client.get(reverse('post', args=arg))
        post_template = response.context['page'][0]
        self.assertEqual(post_template.text, self.context2['text'])

    def test_comments_not_auth(self):
        post = self.create_post(self.client)
        arg=(self.user.username, 1)
        url = reverse('add_comment', args=arg)
        comment = self.client2.post(url, {'text': self.context2['text']})
        self.assertFalse(Comment.objects.all().exists())

    def test_cache_index(self):
        self.create_post(self.client)
        response_1 = self.client.get(reverse('index')).context['page'][0]
        self.create_posts()
        time.sleep(11)
        response_2 = self.client.get(reverse('index')).context['page'][0]
        self.assertEqual(response_1.text, response_2.text)
        self.assertEqual(response_1.group, response_2.group)
        self.assertEqual(response_1.pub_date, response_2.pub_date)
        time.sleep(11) 
        response_2 = self.client.get(reverse('index')).context[0] 
        self.assertNotEqual(response_1.text, response_2.text) 
        self.assertNotEqual(response_1.group, response_2.group) 
        self.assertNotEqual(response_1.pub_date, response_2.pub_date)

    def create_posts(self): 
        user2 = User.objects.create(
            first_name='Rex',
            last_name='Dog',
            username='rex',
            email='rex@disney.com',
            password='A12345a!'
        )
        post = Post.objects.create(text='First', group=self.group, author=user2) 
        post = Post.objects.create(text='Second', author=user2)

    def create_post(self, client):
        return client.post(reverse('new_post'), self.context, follow=True)


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


class TestErrors(TestCase):
    def test_404(self):
        client = Client()
        response = client.get('/news/')
        self.assertEqual(response.status_code, 404)
