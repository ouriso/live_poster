from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
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
            'group_pk': self.group.pk,
            'text': 'Lets go!',
        }
        self.context2 = {
            'group_pk': self.group2.pk,
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
            group=self.context['group_pk']
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
        self.assertEqual(post.group.pk, self.context['group_pk'])

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
            self.assertEqual(post_template.group.pk, context['group_pk'])

    def test_comments_auth(self):
        post = self.create_post(self.client)
        arg = (self.user.username, 1)
        url = reverse('add_comment', args=arg)
        text = 'You shall not pass!!!'
        response = self.client.post(url, {'text': text})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Comment.objects.exists())

    def test_comments_not_auth(self):
        post = self.create_post(self.client)
        arg = (self.user.username, 1)
        url = reverse('add_comment', args=arg)
        comment = self.client2.post(url, {'text': self.context2['text']})
        self.assertFalse(Comment.objects.all().exists())

    def test_comments_on_page(self):
        post = Post.objects.create(
            text=self.context['text'],
            author=self.user,
            group=self.group
        )
        text = 'You shall not pass!!!'
        Comment.objects.create(
            text=text,
            author=self.user,
            post=post
        )
        arg = (self.user.username, 1)
        response = self.client.get(reverse('post', args=arg))
        self.assertEqual(response.status_code, 200)
        post_template = response.context['page'][0]
        self.assertEqual(post_template.text, text)

    def test_cache_index(self):
        response_1 = self.client.get(reverse('index'))
        post = Post.objects.create(
            text='First', group=self.group, author=self.user
        )
        response_2 = self.client.get(reverse('index'))
        self.assertEqual(response_1.content, response_2.content)
        cache.clear()
        response_3 = self.client.get(reverse('index'))
        self.assertNotEqual(response_1.content, response_3.content)
        self.assertEqual(response_3.context['page'][0].text, 'First')

    def create_post(self, client):
        return client.post(reverse('new_post'), self.context, follow=True)


class TestImages(TestCase):
    def setUp(self):
        self.client = Client()
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
        self.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        self.uploaded = SimpleUploadedFile(
            'small.gif', self.small_gif, content_type='image/gif'
        )

    def test_img_post(self):
        post = self.client.post(
            reverse('new_post'),
            {'text': 'post with image', 'image': self.uploaded}
        )
        arg = (self.user.username, 1)
        response = self.client.get(reverse('post', args=arg))
        self.assertContains(response, '<img class="card-img"')

    def test_img_pages(self):
        post = Post.objects.create(
            author=self.user,
            text='post with image',
            group=self.group,
            image=self.uploaded
        )
        links = (
            reverse('index'),
            reverse('group', args=(post.group.slug,)),
            reverse('profile', args=(post.author.username,)),
        )
        for link in links:
            response = self.client.get(link)
            self.assertContains(response, '<img class="card-img"')

    def test_img_wrong(self):
        uploaded = SimpleUploadedFile(
            'small.txt', self.small_gif, content_type='text/txt'
        )
        post = self.client.post(
            reverse('new_post'), {
                'text': 'post with image',
                'image': uploaded,
            }
        )
        form = post.context['form']
        self.assertFormError( post, 'form', 'image', form.errors['image'])
        self.assertFalse(Post.objects.all().exists())

    def tearDown(self):
        Post.objects.all().delete()


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

    def test_follow(self):
        self.client2.get(
            reverse('profile_follow', args=(self.user.username,))
        )
        is_follow = Follow.objects.get(user=self.user2, author=self.user)
        self.assertTrue(is_follow)

    def test_unfollow(self):
        self.client2.get(
            reverse('profile_follow', args=(self.user.username,))
        )
        self.client2.get(
            reverse('profile_unfollow', args=(self.user.username,))
        )
        followers = Follow.objects.all().values_list('user', flat=True)
        self.assertNotIn(self.user2, followers)

    def test_follow_index(self):
        self.client2.get(
            reverse('profile_follow', args=(self.user.username,))
        )
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
        posts_count = len(response.context['page'])
        self.assertEqual(posts_count, 0)


class TestErrors(TestCase):
    def test_404(self):
        client = Client()
        response = client.get('/news/')
        self.assertEqual(response.status_code, 404)
