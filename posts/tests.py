from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.shortcuts import get_object_or_404
from django.test import Client, TestCase
from django.urls import reverse

from .models import Comment, Follow, Group, Post

User = get_user_model()


class HelperTest():
    def setInit(self):
        self.client = Client()
        self.client2 = Client()
        self.user_jerry = User.objects.create_user(
            first_name='Jerry',
            last_name='Mouse',
            username='jerry',
            email='jerry@disney.com',
            password='A12345a!'
        )
        self.user_tom = User.objects.create_user(
            first_name='Tom',
            last_name='Cat',
            username='tom',
            email='tom@disney.com',
            password='A12345a!'
        )
        self.client.force_login(self.user_jerry)
        self.group_cats = Group.objects.create(
            title='Cats',
            slug='cats',
            description='Only for cats'
        )
        self.group_dogs = Group.objects.create(
            title='Dogs',
            slug='dogs',
        )
        self.text_post = 'Lets go!'
        self.text_post_upd = 'Atack! I say, atack!'

    def create_post(self, image=None):
        return Post.objects.create(
            text=self.text_post,
            author=self.user_jerry,
            group=self.group_cats,
            image=image
        )

    def get_responses(self, username, group):
        return (
            self.client.get(reverse('index')),
            self.client.get(reverse('group', args=(group.slug,))),
            self.client.get(reverse('profile', args=(username,))),
        )

    def assert_responses(self, responses, text, group):
        for response in responses:
            post_template = response.context['page'][0]
            self.assertEqual(post_template.text, text)
            self.assertEqual(post_template.group.pk, group.pk)


class TestPosts(TestCase, HelperTest):
    def setUp(self):
        self.setInit()

    def test_profile_exist(self):
        response = self.client.get(
            reverse('profile', args=(self.user_jerry,))
        )
        self.assertEqual(response.status_code, 200)

    def test_post_auth(self):
        self.client.post(
            reverse('new_post'),
            {'text': self.text_post, 'group': self.group_cats.pk},
            follow=True
        )
        post = Post.objects.get(
            pk=1,
            text=self.text_post,
            group=self.group_cats.pk
        )
        self.assertTrue(post)

    def test_post_not_auth(self):
        posts_before = Post.objects.all().count()
        context = {
            'text': self.text_post,
            'group': self.group_cats.pk,
        }
        response = self.client2.post(
            reverse('new_post'), context
        )
        posts_after = Post.objects.all().count()
        self.assertEqual(posts_after, posts_before)

    def test_group(self):
        response = self.client.get(
            reverse('group', args=(self.group_cats.slug,))
        )
        self.assertEqual(response.status_code, 200)

    def test_post_exist(self):
        post = self.create_post()
        responses = self.get_responses(self.user_jerry, self.group_cats)
        self.assert_responses(responses, self.text_post, self.group_cats)

    def test_post_edit(self):
        post = self.create_post()
        post_edit_url = reverse('post_edit', args=(self.user_jerry, post.pk))
        self.client.post(
            post_edit_url,
            {'text': self.text_post_upd, 'group': self.group_dogs.pk}
        )
        responses = self.get_responses(self.user_jerry, self.group_dogs)
        self.assert_responses(
            responses, self.text_post_upd, self.group_dogs
        )

    def test_wrong_user(self):
        post = self.create_post()
        self.client2.force_login(self.user_tom)
        post_edit_url = reverse('post_edit', args=(self.user_jerry, post.pk,))
        self.client2.post(
            post_edit_url,
            {'text': self.text_post_upd, 'group': self.group_dogs.pk}
        )
        responses = self.get_responses(self.user_jerry, self.group_cats)
        self.assert_responses(responses, self.text_post, self.group_cats)

    def test_cache_index(self):
        response_1 = self.client.get(reverse('index'))
        post = self.create_post()
        response_2 = self.client.get(reverse('index'))
        self.assertEqual(response_1.content, response_2.content)
        cache.clear()
        response_3 = self.client.get(reverse('index'))
        self.assertNotEqual(response_1.content, response_3.content)
        self.assertEqual(response_3.context['page'][0].text, self.text_post)


class TestComments(TestCase, HelperTest):
    def setUp(self):
        self.setInit()
        self.post = self.create_post()
        self.text = 'You shall not pass!!!'

    def test_comments_auth(self):
        arg = (self.user_jerry, self.post.pk)
        add_comment_url = reverse('add_comment', args=arg)

        response = self.client.post(add_comment_url, {'text': self.text})
        comment = Comment.objects.first()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(comment.text, self.text)
        self.assertEqual(comment.author, self.user_jerry)

    def test_comments_not_auth(self):
        arg = (self.user_jerry, self.post.pk)
        add_comment_url = reverse('add_comment', args=arg)
        comment = self.client2.post(add_comment_url, {'text': self.text})
        self.assertFalse(Comment.objects.all().exists())

    def test_comments_on_page(self):
        arg = (self.user_jerry, self.post.pk)
        Comment.objects.create(
            text=self.text,
            author=self.user_jerry,
            post=self.post
        )
        response = self.client.get(reverse('post', args=arg))
        self.assertEqual(response.status_code, 200)
        post_template = response.context['page'][0]
        self.assertEqual(post_template.text, self.text)


class TestImages(TestCase, HelperTest):
    def setUp(self):
        self.setInit()
        self.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        self.uploaded = SimpleUploadedFile(
            'small.gif', self.small_gif, content_type='image/gif'
        )

    def test_img_post(self):
        post = self.create_post(self.uploaded)
        arg = (self.user_jerry, post.pk)
        response = self.client.get(reverse('post', args=arg))
        self.assertContains(response, '<img class="card-img"')

    def test_img_pages(self):
        post = self.create_post(self.uploaded)
        responses = self.get_responses(self.user_jerry, self.group_cats)
        for response in responses:
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
        error_text = ("Формат файлов 'txt' не поддерживается. "
            "Поддерживаемые форматы файлов: 'bmp, dib, gif, tif, tiff, "
            "jfif, jpe, jpg, jpeg, pbm, pgm, ppm, pnm, png, apng, blp, bufr, "
            "cur, pcx, dcx, dds, ps, eps, fit, fits, fli, flc, ftc, ftu, gbr, "
            "grib, h5, hdf, jp2, j2k, jpc, jpf, jpx, j2c, icns, ico, im, iim, "
            "mpg, mpeg, mpo, msp, palm, pcd, pdf, pxr, psd, bw, rgb, rgba, sgi, "
            "ras, tga, icb, vda, vst, webp, wmf, emf, xbm, xpm'."
        )
        self.assertFalse(form.is_valid())
        self.assertFormError(post, 'form', 'image', error_text)
        self.assertFalse(Post.objects.all().exists())

    def tearDown(self):
        Post.objects.all().delete()


class TestFollows(TestCase, HelperTest):
    def setUp(self):
        self.setInit()

        self.client2.force_login(self.user_tom)
        self.post = self.create_post()

    def test_follow(self):
        self.client2.get(
            reverse('profile_follow', args=(self.user_jerry,))
        )
        is_follow = Follow.objects.get(pk=1)
        self.assertEqual(is_follow.user, self.user_tom)
        self.assertEqual(is_follow.author, self.user_jerry)

    def test_unfollow(self):
        self.client2.get(
            reverse('profile_follow', args=(self.user_jerry,))
        )
        self.client2.get(
            reverse('profile_unfollow', args=(self.user_jerry,))
        )
        followers = Follow.objects.all().values_list('user', flat=True)
        self.assertNotIn(self.user_tom, followers)

    def test_follow_index(self):
        self.client2.get(
            reverse('profile_follow', args=(self.user_jerry,))
        )
        response = self.client2.get(reverse('follow_index'))
        post_template = response.context['page'][0]
        self.assertEqual(post_template.text, self.post.text)
        self.assertEqual(post_template.group.pk, self.post.group.pk)

    def test_not_follow_index(self):
        response = self.client2.get(reverse('follow_index'))
        posts_count = len(response.context['page'])
        self.assertEqual(posts_count, 0)


class TestErrors(TestCase):
    def test_404(self):
        client = Client()
        response = client.get('/news/')
        self.assertEqual(response.status_code, 404)
