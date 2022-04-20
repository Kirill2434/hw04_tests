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
        cls.edit_post_2 = Post.objects.create(
            text='Новый текст',
            author=cls.user,
            group=cls.group
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_post_create(self):
        """Валидная форма post_create создает запись в Post."""
        self.post = Post.objects.create(
            text='Старый текст',
            author=self.user,
            group=self.group
        )
        posts_count = Post.objects.count()
        create_text = 'Новый текст'
        form_data = {
            'text': create_text,
            'group': self.group.pk
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        first_post = Post.objects.last()
        self.assertRedirects(response, reverse('posts:profile', kwargs={
            'username': self.user.username}))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(first_post.text, create_text)
        self.assertEqual(first_post.author, self.post.author)
        self.assertEqual(first_post.group, self.post.group)

    def test_post_edit(self):
        """Валидная форма post_edit редактирует запись в Post."""
        self.post = Post.objects.create(
            text='Старый текст',
            author=self.user,
            group=self.group
        )
        posts_count = Post.objects.count()
        new_text = 'Отредактированный текст'
        form_data = {
            'text': new_text,
            'group': self.post.group.id
        }
        response = self.authorized_client.post(
            reverse(
                'posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        first_post = Post.objects.first()
        self.assertRedirects(response, reverse('posts:post_detail', kwargs={
            'post_id': self.post.id}))
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(first_post.text, new_text)
        self.assertEqual(first_post.author, self.post.author)
        self.assertEqual(first_post.group, self.post.group)

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
        self.assertEqual(Post.objects.count(), posts_count)
