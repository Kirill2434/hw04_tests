from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.post = Post.objects.create(
            author=User.objects.create_user(username='Auth'),
            text='Тестовый пост увеличим кол-во символов',
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )

    def test_models_have_correct_str_(self):
        """Проверяем, что у моделей корректно работает __str__."""
        post = PostModelTest.post
        expected_object_name_post = self.post.text[:15]
        group = PostModelTest.group
        expected_object_name_group = group.title
        models = {
            expected_object_name_post: str(post),
            expected_object_name_group: str(group)
        }
        for expected_object_name, model in models.items():
            with self.subTest(expected_object_name=expected_object_name):
                self.assertEqual(expected_object_name, model)
