from django.test import TestCase, Client
from django.contrib import auth


User = auth.get_user_model()
app_name = 'core'


class URLTests(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        self.url_reverse = {'unexisting_page': '/unexisting_page/'}
        return super().setUp()

    def tearDown(self) -> None:
        return super().tearDown()

    def test_url_teplates(self):
        url_templates = {
            'unexisting_page': '/404.html',
        }

        for url_name, template in url_templates.items():
            url = self.url_reverse[url_name]
            with self.subTest(url=url, template=template):
                response = self.client.get(url)
                self.assertTemplateUsed(response, app_name + template)
