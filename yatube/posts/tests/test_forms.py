import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings

from ..models import Group, Post, Comment

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


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

    def test_add_comment_authorized_client(self):
        """ Авторизованный пользователь может комментировать посты. """
        self.post = Post.objects.create(
            text='Текст для теста',
            author=self.user,
            group=self.group
        )
        self.comments = Comment.objects.create(
            post=self.post,
            author=self.user,
            text='Текст комментария'
        )
        comments_count = Comment.objects.count()
        form = {
            'post': self.comments.post,
            'author': self.comments.author,
            'text': self.comments.text
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}))
        first_comment = Comment.objects.first()
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertEqual(first_comment.post, self.comments.post)
        self.assertEqual(first_comment.author, self.comments.author)
        self.assertEqual(first_comment.text, self.comments.text)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ImagionFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Auth_2')
        cls.group = Group.objects.create(
            title='Новая группа',
            slug='test_slug_2',
            description='Новое описание',
        )
        cls.post = Post.objects.create(
            text='Текст',
            author=cls.user,
            group=cls.group
        )
        cls.picture = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def check_post(self, post):
        self.assertEqual(post.author.username, self.user.username)
        self.assertEqual(post.pub_date, self.post.pub_date)
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.group, self.group)

    def test_image_post_create_record(self):
        """Тест отправки поста с картинкой через форму
         создает запись в БД."""
        posts_count = Post.objects.count()
        uploaded = SimpleUploadedFile(
            name='picture.gif',
            content=self.picture,
            content_type='image/gif')
        form_edit = {
            'text': 'Какой то текст',
            'group': self.group.pk,
            'image': uploaded
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_edit,
            follow=True)
        self.assertRedirects(response, reverse('posts:profile', kwargs={
            'username': self.user.username}))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        first_post = Post.objects.first()
        self.assertEqual(first_post.image, 'posts/picture.gif')
        self.assertEqual(first_post.author, self.post.author)
        self.assertEqual(first_post.group, self.post.group)

    def test_post_image_correct_context(self):
        """ Проверяем, что при создании поста с картинкой
        этот пост появляется на главной странице,
        на странице группы, на старнице профайла. """
        self.post = Post.objects.create(
            text='Здесь я добавил картинку',
            author=self.user,
            group=self.group,
            image='posts/picture.gif'
        )
        pages = [
            reverse('posts:index'),
            reverse('posts:group_lists', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user.username})
        ]
        for reverse_page in pages:
            with self.subTest(reverse_page=reverse_page):
                response = self.authorized_client.get(reverse_page)
                test_page = response.context['page_obj'][0]
                self.assertEqual(test_page.image, self.post.image)
                self.check_post(test_page)

    def test_post_detail_image_correct_context(self):
        """Проверяем, что при создании поста с картинкой
        этот пост появляется на отдельной странице поста."""
        self.post = Post.objects.create(
            text='Моя картинка',
            author=self.user,
            group=self.group,
            image='posts/picture.gif'
        )
        response = self.client.get(reverse(
            'posts:post_detail',
            kwargs={'post_id': self.post.id})
        )
        test_posts = response.context.get('posts')
        self.assertEqual(test_posts.image, self.post.image)
        test_object = response.context['posts']
        self.check_post(test_object)
