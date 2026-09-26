import io
import json
import tempfile
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile

from django.test import Client, TestCase, override_settings

from app01.models import ArticleDraft, Articles, Cover, Tags, UserInfo
from app01.utils.article_backup import build_article_backup, rewrite_images


class ArticleBackupTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = UserInfo.objects.create_user(username='backup-admin', password='test-password', is_superuser=True)
        cls.reader = UserInfo.objects.create_user(username='backup-reader', password='test-password')
        cls.cover = Cover.objects.create(url='article_img/封面.png')
        cls.article = Articles.objects.create(
            title='同名 / 文章', status=1, abstract='备份测试', category=1,
            content='![图片](/media/uploads/测试%20图.png)\n![重复](/media/uploads/测试%20图.png)',
            cover=cls.cover, pwd='private-password-hash', author='admin',
        )
        cls.tag = Tags.objects.create(title='Django')
        cls.article.tag.add(cls.tag)
        cls.unpublished = Articles.objects.create(title='同名 / 文章', status=0, content='尚未发布')
        ArticleDraft.objects.create(owner=cls.admin, title='独立草稿', content='不可导出的草稿正文')

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.media = Path(self.directory.name)
        self.settings_override = override_settings(MEDIA_ROOT=self.media, MEDIA_URL='/media/')
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)
        for filename in ('article_img/封面.png', 'uploads/测试 图.png', 'uploads/pic(1).png'):
            image = self.media / filename
            image.parent.mkdir(parents=True, exist_ok=True)
            image.write_bytes(b'example-image-bytes')

    def archive(self, response):
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/zip')
        data = b''.join(response.streaming_content)
        response.close()
        archive = ZipFile(io.BytesIO(data))
        self.addCleanup(archive.close)
        return archive

    def test_selected_export_contains_portable_images_and_metadata_without_password(self):
        self.client.force_login(self.admin)
        archive = self.archive(self.client.post('/api/article/export/', {'scope': 'selected', 'article_ids': str(self.article.pk)}))
        manifest = json.loads(archive.read('manifest.json'))
        self.assertEqual(len(manifest['articles']), 1)
        directory = manifest['articles'][0]['directory']
        metadata = json.loads(archive.read(f'{directory}/metadata.json'))
        markdown = archive.read(f'{directory}/article.md').decode('utf-8')
        self.assertEqual(metadata['tags'], [{'id': self.tag.pk, 'name': 'Django'}])
        self.assertTrue(metadata['password_protected'])
        self.assertNotIn('pwd', metadata)
        self.assertNotIn(self.article.pwd, archive.read(f'{directory}/metadata.json').decode('utf-8'))
        self.assertNotIn('/media/', markdown)
        self.assertIn('(images/', markdown)
        self.assertEqual(len([name for name in archive.namelist() if '/images/' in name]), 2)
        self.assertEqual(archive.read(f'{directory}/{metadata["cover"]["path"]}'), b'example-image-bytes')
        self.article.refresh_from_db()
        self.assertIn('/media/', self.article.content)
        self.assertEqual(self.article.pwd, 'private-password-hash')

    def test_all_export_includes_unpublished_and_keeps_same_titles_separate(self):
        self.client.force_login(self.admin)
        archive = self.archive(self.client.post('/api/article/export/', {'scope': 'all'}))
        entries = json.loads(archive.read('manifest.json'))['articles']
        self.assertEqual({item['id'] for item in entries}, {self.article.pk, self.unpublished.pk})
        self.assertEqual(len({item['directory'] for item in entries}), 2)
        self.assertNotIn('不可导出的草稿正文', ''.join(archive.read(name).decode('utf-8') for name in archive.namelist()))

    def test_missing_external_traversal_and_non_image_files_are_reported(self):
        (self.media / 'private.txt').write_text('private-file-content', encoding='utf-8')
        urls = [
            '/media/missing.png', 'https://external.invalid/media/pic.png',
            '/media/%2e%2e/private.png', '/media/private.txt',
            '/media/%5c..%5cprivate.png', '/media/C:/private.png',
        ]
        self.article.content = '\n'.join(f'![image]({url})' for url in urls)
        output = build_article_backup([self.article], 'http://testserver/')
        self.addCleanup(output.close)
        with ZipFile(output) as archive:
            manifest = json.loads(archive.read('manifest.json'))
            self.assertEqual(len(manifest['articles'][0]['warnings']), len(urls))
            readme = archive.read('README.txt').decode('utf-8')
            for url in urls:
                self.assertIn(url, readme)
            self.assertNotIn('private-file-content', ''.join(archive.read(name).decode('utf-8') for name in archive.namelist()))

    def test_same_site_absolute_image_reference_html_and_code_examples(self):
        original = (
            '![inline](http://testserver/media/uploads/pic(1).png "title")\n'
            '![reference][photo]\n[photo]: </media/uploads/测试 图.png> "title"\n'
            '<img src="/media/uploads/测试%20图.png" alt="image">\n'
            '`![code](/media/no.png)`\n'
            '```markdown\n![code](/media/no.png)\n```\n'
            '    ![code](/media/no.png)\n'
        )
        self.article.content = original
        output = build_article_backup([self.article], 'http://testserver/')
        self.addCleanup(output.close)
        with ZipFile(output) as archive:
            entry = json.loads(archive.read('manifest.json'))['articles'][0]
            content = archive.read(entry['directory'] + '/article.md').decode('utf-8')
            self.assertIn('![inline](images/', content)
            self.assertIn('[photo]: <images/', content)
            self.assertIn('<img src="images/', content)
            self.assertEqual(content.count('/media/no.png'), 3)
            self.assertFalse(entry['warnings'])

    def test_inline_reference_and_html_rewrite_leaves_normal_links_unchanged(self):
        content = '![one](/media/a.png)\n![ref][]\n[ref]: /media/b.png\n<a href="/media/c.png">link</a>\n[link](/media/d.png)'
        seen = []

        def replace(url):
            seen.append(url)
            return 'images/' + url.rsplit('/', 1)[-1]

        updated = rewrite_images(content, replace)
        self.assertEqual(seen, ['/media/a.png', '/media/b.png'])
        self.assertIn('[link](/media/d.png)', updated)
        self.assertIn('href="/media/c.png"', updated)

    def test_guest_and_regular_user_cannot_export_or_view_page(self):
        self.assertEqual(self.client.post('/api/article/export/', {'scope': 'all'}).status_code, 401)
        self.assertEqual(self.client.get('/backend/article_backup').status_code, 302)
        self.client.force_login(self.reader)
        self.assertEqual(self.client.post('/api/article/export/', {'scope': 'all'}).status_code, 403)
        self.assertEqual(self.client.get('/backend/article_backup').status_code, 302)

    def test_csrf_and_post_are_required(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.admin)
        self.assertEqual(client.get('/api/article/export/').status_code, 405)
        self.assertEqual(client.post('/api/article/export/', {'scope': 'all'}).status_code, 403)
        page = client.get('/backend/article_backup')
        self.assertEqual(page.status_code, 200)
        self.assertNotIn(self.article.pwd.encode(), page.content)
        self.assertNotIn(self.article.content.encode(), page.content)
        response = client.post('/api/article/export/', {'scope': 'selected', 'article_ids': [self.article.pk]}, HTTP_X_CSRFTOKEN=client.cookies['csrftoken'].value)
        self.archive(response)

    def test_bad_selection_and_export_limit(self):
        self.client.force_login(self.admin)
        for payload in (
            {}, {'scope': 'selected'}, {'scope': 'selected', 'article_ids': ['oops']},
            {'scope': 'selected', 'article_ids': ['-1']},
            {'scope': 'selected', 'article_ids': ['9' * 100]},
        ):
            with self.subTest(payload=payload):
                self.assertEqual(self.client.post('/api/article/export/', payload).status_code, 400)
        self.assertEqual(self.client.post('/api/article/export/', {'scope': 'selected', 'article_ids': [99999]}).status_code, 404)
        self.assertEqual(self.client.post('/api/article/export/', {'scope': 'selected', 'article_ids': ','.join(str(i) for i in range(1, 1001))}).status_code, 404)
        with patch('app01.utils.article_backup.MAX_EXPORT_BYTES', 1):
            self.assertEqual(self.client.post('/api/article/export/', {'scope': 'all'}).status_code, 413)

    def test_symlink_target_outside_media_is_not_exported(self):
        with tempfile.TemporaryDirectory() as outside:
            secret = Path(outside) / 'outside.png'
            secret.write_bytes(b'outside-secret')
            link = self.media / 'linked.png'
            try:
                link.symlink_to(secret)
            except OSError:
                self.skipTest('Creating symlinks requires privileges on this Windows host')
            self.article.content = '![link](/media/linked.png)'
            output = build_article_backup([self.article], 'http://testserver/')
            self.addCleanup(output.close)
            with ZipFile(output) as archive:
                warnings = json.loads(archive.read('manifest.json'))['articles'][0]['warnings']
                self.assertIn('超出上传目录', warnings[0]['reason'])
                self.assertNotIn(b'outside-secret', b''.join(archive.read(name) for name in archive.namelist()))
