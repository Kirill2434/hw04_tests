from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Kir')
        cls.post = Post.objects.create(
            author=User.objects.create_user(username='auth',
                                            email='example@yandex.ru',
                                            password='123456789'),
            text='Тестовый пост'
        )

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание'
        )
        cls.edit_post = Post.objects.create(
            text='Отредактированный текст',
            author=cls.user,
            group=cls.group
        )
        cls.dict_pages = {
            'home': ['/', 'posts/index.html'],
            'group': ['group', 'posts/group_list.html'],
            'create': ['create', 'posts/create_post.html'],
            'profile': ['profile', 'posts/profile.html'],
            'posts_detail': ['posts', 'posts/post_detail.html'],
            'post_edit': ['posts/1/edit/', 'posts/create_post.html']
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_unauthorized_user_access(self):
        """ Страницы доступны неавторизованному пользователю. """
        url_names = (
            self.dict_pages['home'][0],
            f"/{self.dict_pages['group'][0]}/{self.group.slug}/",
            f"/{self.dict_pages['profile'][0]}/{self.post.author}/",
            f"/{self.dict_pages['posts_detail'][0]}/{self.post.pk}/"
        )
        for adress in url_names:
            with self.subTest():
                response = self.guest_client.get(adress)
                self.assertEqual(response.status_code, 200)

    def test_create_url_exists_at_desired_location(self):
        """ Страница create доступна авторизованному пользователю. """
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, 200)

    def test_edit_url_authorized_user_unavailable(self):
        """ Авторизованный пользователь, но не автор поста
         не может получить доступ к странице редактирования. """

        response = self.authorized_client.get(
            f"/{self.dict_pages['post_edit']}/2/")
        self.assertEqual(response.status_code, 404)

    def test_create_and_edit_url_unauthorized_user_unavailable(self):
        """ Страница create и edit не доступна
        неавторизованному пользователю. """
        response_create = self.guest_client.post(self.dict_pages['create'][0])
        response_edit = self.guest_client.post(self.dict_pages['post_edit'][0])
        response_list = [
            response_create,
            response_edit
        ]
        for response in response_list:
            with self.subTest():
                self.assertEqual(response.status_code, 404)

    def test_posts_urls_uses_correct_template(self):
        """ URL-адрес использует соответствующий шаблон. """
        templates_url_names = {
            self.dict_pages['home'][0]: 
            self.dict_pages['home'][1],
            f"/{self.dict_pages['group'][0]}/{self.group.slug}/": 
            self.dict_pages['group'][1],
            f"/{self.dict_pages['create'][0]}/": 
            self.dict_pages['create'][1],
            f"/{self.dict_pages['profile'][0]}/{self.post.author}/": 
            self.dict_pages['profile'][1],
            f"/{self.dict_pages['posts_detail'][0]}/{self.post.pk}/":
            self.dict_pages['posts_detail'][1]

        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_404_url_exists_at_desired_location(self):
        """ запрос к несуществующей странице вернёт ошибку 404. """
        response = self.guest_client.get('/group/general/')
        self.assertEqual(response.status_code, 404)
