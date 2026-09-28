from django.test import SimpleTestCase, TestCase
from django.urls import resolve, reverse

from app01.models import UserInfo


class TalksRouteTests(SimpleTestCase):
    def test_namespaced_route(self):
        self.assertEqual(resolve('/talks/').namespace, 'talks')
        self.assertEqual(reverse('talks:index'), '/talks/')

    def test_anonymous_user_is_redirected(self):
        response = self.client.get(reverse('talks:index'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response['Location'])


class TalksPageTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserInfo.objects.create_user(username='talks-reader', password='test-password')

    def test_authenticated_user_sees_placeholder(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('talks:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '谈资库已建立')
        self.assertEqual(self.client.post(reverse('talks:index')).status_code, 405)
