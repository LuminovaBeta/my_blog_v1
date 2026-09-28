from django.test import SimpleTestCase, TestCase
from django.urls import resolve, reverse

from app01.models import UserInfo


class LibraryPageSketchTests(SimpleTestCase):
    def test_routes_belong_to_library_app(self):
        for name in ('bookshelf', 'book_preview', 'add_book'):
            with self.subTest(name=name):
                self.assertEqual(resolve(reverse(f'library:{name}')).namespace, 'library')

    def test_sketch_pages_require_login(self):
        for name in ('bookshelf', 'book_preview', 'add_book'):
            with self.subTest(name=name):
                response = self.client.get(reverse(f'library:{name}'))
                self.assertEqual(response.status_code, 302)
                self.assertIn('/login/', response['Location'])

    def test_add_page_has_no_submit_endpoint(self):
        response = self.client.post('/library/add/')
        self.assertEqual(response.status_code, 302)


class LibraryAuthenticatedPageTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserInfo.objects.create_user(username='library-reader', password='test-password')

    def setUp(self):
        self.client.force_login(self.user)

    def test_all_sketch_pages_render_without_book_models(self):
        for name in ('bookshelf', 'book_preview', 'add_book'):
            with self.subTest(name=name):
                response = self.client.get(reverse(f'library:{name}'))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, '我的书库')
                self.assertContains(response, '/static/css/library/library.css')

    def test_preview_does_not_offer_a_working_save_action(self):
        response = self.client.get(reverse('library:add_book'))
        self.assertContains(response, '保存书籍（待开发）')
        self.assertContains(response, 'disabled title="保存功能尚未接入"')
        self.assertEqual(self.client.post(reverse('library:add_book')).status_code, 405)
