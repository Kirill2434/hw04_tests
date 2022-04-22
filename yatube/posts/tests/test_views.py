from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.core.cache import cache

from ..forms import PostForm
from ..models import Group, Post, Comment, Follow

User = get_user_model()

SUM_OF_PAGINATOR_POSTS = 13
SECOND_PAGE_PAGINATOR_POSTS = SUM_OF_PAGINATOR_POSTS - settings.POSTS_PER_PAGE


class PostViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Тестовый заголовок',
            author=cls.user,
            group=cls.group
        )
        cls.new_group = Group.objects.create(
            title='Новая группа',
            slug='test-slug_new',
            description='Новое описание',
        )
        cls.templates_and_url = {
            'home': ['posts:index', 'posts/index.html'],
            'group': ['posts:group_lists', 'posts/group_list.html'],
            'profile': ['posts:profile', 'posts/profile.html'],
            'post_detail': ['posts:post_detail', 'posts/post_detail.html'],
            'create': ['posts:post_create', 'posts/create_post.html'],
            'post_edit': ['posts:post_edit', 'posts/create_post.html']
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def check_post(self, post):
        self.assertEqual(post.author.username, self.user.username)
        self.assertEqual(post.pub_date, self.post.pub_date)
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.group, self.group)

    def post_response_context(self, response):
        """ Проверяем Context в двух тестах. """
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
                self.assertIsInstance(response.context.get('form'), PostForm)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse(self.templates_and_url['home'][0]):
                self.templates_and_url['home'][1],
            reverse(
                self.templates_and_url['group'][0],
                kwargs={'slug': self.group.slug}
            ): self.templates_and_url['group'][1],
            reverse(
                self.templates_and_url['profile'][0],
                kwargs={'username': self.post.author.username}
            ): self.templates_and_url['profile'][1],
            reverse(
                self.templates_and_url['post_detail'][0],
                kwargs={'post_id': self.post.id}
            ): self.templates_and_url['post_detail'][1],
            reverse(self.templates_and_url['create'][0]):
                self.templates_and_url['create'][1],
            reverse(
                self.templates_and_url['post_edit'][0],
                kwargs={'post_id': self.post.pk}
            ): self.templates_and_url['post_edit'][1]
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """ Шаблон index сформирован с правильным контекстом. """
        response = self.authorized_client.get(reverse('posts:index'))
        test_object = response.context['page_obj'][0]
        self.check_post(test_object)

    def test_group_list_show_correct_context(self):
        """ Шаблон group_list сформирован с правильным контекстом. """
        response = self.authorized_client.get(
            reverse(
                'posts:group_lists',
                kwargs={'slug': self.group.slug}
            )
        )
        test_group_title = response.context.get('group').title
        test_group = response.context.get('group').description
        self.assertEqual(test_group_title, 'Тестовая группа')
        self.assertEqual(test_group, self.group.description)
        test_object = response.context['page_obj'][0]
        self.check_post(test_object)

    def test_profile_show_correct_context(self):
        """ Шаблон profile сформирован с правильным контекстом. """
        response = self.authorized_client.get(
            reverse('posts:profile',
                    kwargs={'username': self.user})
        )
        test_author = response.context.get('author')
        self.assertEqual(test_author, self.post.author)
        test_object = response.context['page_obj'][0]
        self.check_post(test_object)

    def test_post_detail_show_correct_context(self):
        """ Шаблон post_detail сформирован с правильным контекстом. """
        response = self.guest_client.get(reverse(
            'posts:post_detail',
            kwargs={'post_id': self.post.id})
        )
        test_posts = response.context.get('posts')
        self.assertEqual(test_posts, self.post)
        test_object = response.context['posts']
        self.check_post(test_object)

    def test_post_create_show_correct_context(self):
        """ Шаблон post_create сформирован с правильным контекстом. """
        response = self.authorized_client.get(reverse('posts:post_create'))
        is_edit = response.context['is_edit']
        self.post_response_context(response)
        self.assertFalse(is_edit)
        self.assertIsInstance(is_edit, bool)

    def test_post_edit_page_show_correct_context(self):
        """ Шаблон post_edit сформирован с правильным контекстом. """
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}))
        is_edit = response.context['is_edit']
        self.post_response_context(response)
        self.assertTrue(is_edit)

    def test_post_right_3_pages(self):
        """ Проверяем, что при создании поста с группой
        этот пост появляется на главной странице,
        на странице группы, на старнице профайла. """
        pages = [
            reverse('posts:index'),
            reverse('posts:group_lists', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user.username})
        ]
        for reverse_page in pages:
            with self.subTest(reverse_page=reverse_page):
                response = self.authorized_client.get(reverse_page)
                test_page = response.context['page_obj'][0]
                self.assertEqual(test_page, self.post)

    def test_add_comment_on_pages(self):
        """ Проверяем, что при создании поста с комментарием
        этот пост появляется на странице поста. """
        self.post_comment = Post.objects.create(
            text='Текст для теста',
            author=self.user,
            group=self.group
        )
        self.comments = Comment.objects.create(
            post=self.post_comment,
            author=self.user,
            text='Текст комментария'
        )
        form = {
            'post': self.comments.post,
            'author': self.comments.author,
            'text': self.comments.text
        }
        response_post = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form,
            follow=True
        )
        self.assertRedirects(response_post, reverse('posts:post_detail', kwargs={'post_id': self.post.id}))
        response_get = self.authorized_client.get(reverse('posts:post_detail', kwargs={'post_id': self.post.id}))
        test_page = response_get.context['comments'][0].text
        self.assertEqual(test_page, self.comments.text)

    def test_wrong_group_post(self):
        """ Проверка на ошибочное попадание поста не в ту группу. """
        response = self.authorized_client.get(
            reverse(
                'posts:group_lists',
                kwargs={'slug': self.new_group.slug}
            )
        )
        context = response.context['page_obj'].object_list
        self.assertNotIn(self.post, context)

    def test_caching_correct_work(self):
        """ Корректность раболты cache на главной странице. """
        primary_response = self.guest_client.get(reverse('posts:index')).content
        Post.objects.filter(text=self.post.text).delete()
        response_action = self.guest_client.get(reverse('posts:index')).content
        self.assertEqual(primary_response, response_action)
        cache.clear()
        response_clear_action = self.guest_client.get(reverse('posts:index')).content
        self.assertNotEqual(response_clear_action, primary_response)


class PiginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Auto_2')
        cls.group = Group.objects.create(
            title='Тестовая группа_2',
            slug='test_slug',
            description='Тестовое_описание_2'
        )
        for post_text in range(SUM_OF_PAGINATOR_POSTS):
            cls.posts = Post.objects.create(
                author=cls.user,
                group=cls.group,
                text=f'{post_text} Тестовый текст'
            )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_paginator_correct_first_page(self):
        """ Проверка первой страницы паджинатора. """
        templates = [
            reverse('posts:index'),
            reverse('posts:group_lists', kwargs={'slug': self.group.slug}),
            reverse('posts:profile',
                    kwargs={'username': self.user.username})
        ]
        for num in range(len(templates)):
            with self.subTest(templates=templates[num]):
                response = self.authorized_client.get(templates[num])
                self.assertEqual(len(
                    response.context['page_obj']
                ), settings.POSTS_PER_PAGE)

    def test_paginator_correct_second_page(self):
        """ Проверка второй страницы паджинатора. """
        templates_2 = [
            reverse('posts:index') + '?page=2',
            reverse('posts:group_lists',
                    kwargs={'slug': self.group.slug}) + '?page=2',
            reverse('posts:profile',
                    kwargs={'username': self.user.username}) + '?page=2'
        ]
        for num_2 in range(len(templates_2)):
            with self.subTest(templates=templates_2[num_2]):
                response = self.authorized_client.get(templates_2[num_2])
                self.assertEqual(len(
                    response.context['page_obj']
                ), SECOND_PAGE_PAGINATOR_POSTS)


class FollowTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Auth')
        cls.follower = User.objects.create_user(username='follower_Kir')
        cls.post = Post.objects.create(
            text='Тестовый заголовок',
            author=cls.user
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.follower_client = Client()
        self.follower_client.force_login(self.follower)

    def test_follow_true(self):
        """ Авторизованный пользователь может
        подписываться на других пользователей. """
        self.follower_client.get(reverse('posts:profile_follow', kwargs={'username': self.user}))
        follow = Follow.objects.filter(user=self.follower, author=self.post.author).exists()
        self.assertTrue(follow)

    def test_unfollow_true(self):
        """ Авторизованный пользователь может
        отписываться от других пользователей. """
        self.follower_client.get(reverse('posts:profile_unfollow',
                                         kwargs={'username': self.follower}))
        self.assertFalse(Follow.objects.filter(user=self.follower,
                                               author=self.post.author).exists())

    def test_follow_post_on_page(self):
        """ Новая запись пользователя появляется в ленте тех,
        кто на него подписан и не появляется в ленте тех,
        кто не подписан. """
        Follow.objects.create(user=self.follower,
                              author=self.post.author)
        response = self.follower_client.get(reverse('posts:follow_index'))
        test_page = response.context['page_obj'][0].text
        self.assertEqual(test_page, self.post.text)
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertNotContains(response, self.post.text)
