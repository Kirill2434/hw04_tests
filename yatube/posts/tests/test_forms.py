from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class TaskCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Auth')
        cls.group = Group.objects.create(
            title='Ожидаемая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.group_2 = Group.objects.create(
            title='Тестовая группа_2',
            slug='test-slug_2',
            description='Тестовое описание_2',
        )
        cls.post = Post.objects.create(
            text='Ожидаемый текст',
            author=cls.user,
            group=cls.group
        )
        cls.edit_post_2 = Post.objects.create(
            text='Отредактированный текст',
            author=cls.user,
            group=cls.group_2
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_post_create(self):
        """Валидная форма post_create создает запись в Post."""
        posts_count = Post.objects.count()
        create_text = 'Ожидаемый текст'
        form_data = {
            'text': create_text,
            'group': self.group.pk
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        last_post = Post.objects.last()
        self.post.refresh_from_db()
        self.assertRedirects(response, reverse('posts:profile', kwargs={
            'username': self.user.username}))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(last_post, self.post)

    def test_post_edit(self):
        """Валидная форма post_edit редактирует запись в Post."""
        posts_count = Post.objects.count()
        last_post = self.edit_post_2
        new_text = 'Новый текст'
        form_data = {
            'text': new_text,
            'group': self.edit_post_2.group.id
        }
        response = self.authorized_client.post(
            reverse(
                'posts:post_edit', kwargs={'post_id': self.edit_post_2.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('posts:post_detail', kwargs={
            'post_id': self.edit_post_2.id}))
        # Проверка на то, что в БД не создается новая запись
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(last_post, self.edit_post_2)

    def test_post_edit_guest_client(self):
        """ Неавторизованный пользователь
        не может редактировать записи на сайте. """
        posts_count = Post.objects.count()
        new_text_2 = 'new_text_from_guest_client'
        form_data = {
            'text': new_text_2,
            'group': self.edit_post_2.group.pk
        }
        post_ed = 'posts:post_edit'
        response = self.guest_client.post(
            reverse(post_ed, kwargs={'post_id': self.edit_post_2.pk}),
            data=form_data,
            follow=True
        )
        post_name = 'posts:post_edit'
        name = reverse(post_name, kwargs={'post_id': self.edit_post_2.pk})
        self.edit_post_2.refresh_from_db()
        self.assertRedirects(response,
                             f"{reverse('users:login')}?next="
                             f"{name}")
        # Проверка на то, что в БД не создается новая запись
        self.assertEqual(Post.objects.count(), posts_count)
