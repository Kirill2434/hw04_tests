from django.test import Client, TestCase


class ViewTestClass(TestCase):

    def setUp(self):
        self.guest_client = Client()

    def test_404_url_exists_at_desired_location(self):
        """ Запрос к несуществующей странице вернёт ошибку 404. """
        response = self.guest_client.get('/group/general/')
        self.assertEqual(response.status_code, 404)

    def test_404_use_coorect_tamplate(self):
        """ Cтраница 404 отдает кастомный шаблон. """
        response = self.guest_client.get('/group/general/')
        self.assertTemplateUsed(response, 'core/404.html')
