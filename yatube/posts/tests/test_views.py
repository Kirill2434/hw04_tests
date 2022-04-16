from django import forms
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()

NUM_POSTS = 10


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

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def post_response_context(self, response):
        """Проверяем Context в двух тестах"""
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_lists',
                kwargs={'slug': self.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': self.post.author.username}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}
            ): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': 1}
            ): 'posts/create_post.html'
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_group_list_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
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

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:profile',
                    kwargs={'username': self.user})
        )
        test_author = response.context.get('author')
        self.assertEqual(test_author, self.post.author)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.client.get(reverse(
            'posts:post_detail',
            kwargs={'post_id': self.post.id})
        )
        test_posts = response.context.get('posts')
        self.assertEqual(test_posts, self.post)

    def test_post_create_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        is_edit = response.context['is_edit']
        self.post_response_context(response)
        self.assertFalse(is_edit)
        self.assertIsInstance(is_edit, bool)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
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
        for post_text in range(13):
            cls.posts = Post.objects.create(
                author=cls.user,
                group=cls.group,
                text=f'{post_text} Тестовый текст'
            )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_paginator_correct(self):
        """ Проверка паджинатора. """
        templates = [
            reverse('posts:index'),
            reverse('posts:group_lists', kwargs={'slug': self.group.slug}),
            reverse('posts:profile',
                    kwargs={'username': self.user.username})
        ]
        for num in range(len(templates)):
            with self.subTest(templates=templates[num]):
                response = self.authorized_client.get(templates[num])
                self.assertEqual(len(response.context['page_obj']), NUM_POSTS)
