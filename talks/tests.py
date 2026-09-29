from datetime import timedelta

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase, TestCase
from django.urls import resolve, reverse
from django.utils import timezone

from app01.models import UserInfo
from .models import Talk


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
        cls.admin = UserInfo.objects.create_user(
            username='talks-admin', password='test-password',
            is_superuser=True, is_staff=True,
        )

    def test_regular_user_cannot_open_talks(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse('talks:index')).status_code, 403)
        self.assertEqual(
            self.client.post(reverse('talks:index'), {'topic': '越权记录'}).status_code,
            403,
        )
        self.assertFalse(Talk.objects.exists())

    def test_admin_sees_talks_in_shared_navigation(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse('talks:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '随手记一条')
        self.assertContains(response, '继续补充')
        self.assertContains(response, '还没有谈资')
        self.assertContains(response, 'href="/talks/" class="is-active" aria-current="page"')
        self.assertNotContains(response, 'href="/library/" class="is-active"')

    def test_quick_save_only_requires_topic(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse('talks:index'), {
            'topic': '  今天在路上看到的事  ',
        })
        self.assertRedirects(
            response, reverse('talks:index') + '#talk-list',
            fetch_redirect_response=False,
        )
        talk = Talk.objects.get()
        self.assertEqual(talk.owner, self.admin)
        self.assertEqual(talk.topic, '今天在路上看到的事')
        self.assertEqual(talk.observed, '')
        self.assertEqual(talk.category, Talk.Category.UNCLASSIFIED)
        self.assertEqual(talk.tags, [])
        self.assertContains(self.client.get(reverse('talks:index')), talk.topic)

    def test_optional_fields_and_tags_are_saved(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse('talks:index'), {
            'topic': '一部电影',
            'observed': '看到一段有趣的对话',
            'interest_reason': '很真实',
            'understanding': '人与人之间需要耐心',
            'open_questions': '别人会怎么想？',
            'source': '电影片段',
            'category': 'short',
            'tags_input': '电影，聊天, 电影',
        })
        self.assertEqual(response.status_code, 302)
        talk = Talk.objects.get()
        self.assertEqual(talk.tags, ['电影', '聊天'])
        self.assertEqual(talk.get_category_display(), '短谈资')
        page = self.client.get(reverse('talks:index'))
        self.assertContains(page, '看到一段有趣的对话')
        self.assertContains(page, '人与人之间需要耐心')
        self.assertContains(page, '#电影')

    def test_invalid_input_does_not_create_record(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse('talks:index'), {
            'topic': '   ',
            'tags_input': '标签',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '主题不能为空')
        self.assertFalse(Talk.objects.exists())
        response = self.client.post(reverse('talks:index'), {
            'topic': '有效主题',
            'tags_input': '过长标签' * 10,
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '每个标签不超过 30 个字')
        self.assertFalse(Talk.objects.exists())

    def test_list_is_private_and_newest_first(self):
        second_admin = UserInfo.objects.create_user(
            username='talks-second-admin', password='test-password',
            is_superuser=True, is_staff=True,
        )
        Talk.objects.create(owner=second_admin, topic='别人的谈资')
        Talk.objects.create(owner=self.admin, topic='较早的谈资')
        Talk.objects.create(owner=self.admin, topic='最新的谈资')
        self.client.force_login(self.admin)
        response = self.client.get(reverse('talks:index'))
        self.assertNotContains(response, '别人的谈资')
        self.assertContains(response, '共 2 条')
        content = response.content.decode()
        self.assertLess(content.index('最新的谈资'), content.index('较早的谈资'))

    def test_list_paginates(self):
        for number in range(11):
            Talk.objects.create(owner=self.admin, topic=f'谈资 {number}')
        self.client.force_login(self.admin)
        first = self.client.get(reverse('talks:index'))
        self.assertContains(first, '下一页')
        second = self.client.get(reverse('talks:index') + '?page=2')
        self.assertContains(second, '第 2 / 2 页')
        self.assertContains(second, 'class="talk-card"', count=1)


class TalkModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = UserInfo.objects.create_user(
            username='talk-model-owner', password='test-password',
            is_superuser=True, is_staff=True,
        )

    def test_minimal_talk_allows_optional_fields_to_be_empty(self):
        talk = Talk(owner=self.owner, topic='一件值得聊的事')
        talk.full_clean()
        talk.save()
        self.assertEqual(talk.category, Talk.Category.UNCLASSIFIED)
        self.assertEqual(talk.tags, [])
        for field in ('observed', 'interest_reason', 'understanding',
                      'open_questions', 'source'):
            self.assertEqual(getattr(talk, field), '')
        self.assertIsNotNone(talk.created_at)
        self.assertIsNotNone(talk.updated_at)
        self.assertGreaterEqual(talk.updated_at, talk.created_at)

    def test_topic_is_required_and_whitespace_is_rejected(self):
        for topic in ('', '   '):
            with self.subTest(topic=topic):
                with self.assertRaises(ValidationError):
                    Talk(owner=self.owner, topic=topic).full_clean()

    def test_categories_and_multiple_tags(self):
        self.assertEqual(
            {choice.value for choice in Talk.Category},
            {'unclassified', 'short', 'serious', 'daily', 'personal'},
        )
        talk = Talk(
            owner=self.owner, topic='电影里的话题',
            category=Talk.Category.SHORT, tags=['电影', '聊天'],
        )
        talk.full_clean()
        talk.save()
        talk.refresh_from_db()
        self.assertEqual(talk.tags, ['电影', '聊天'])
        self.assertEqual(talk.get_category_display(), '短谈资')
        for tags in ('电影', ['电影', '  ']):
            with self.subTest(tags=tags):
                talk.tags = tags
                with self.assertRaises(ValidationError):
                    talk.full_clean()

    def test_updated_at_changes_when_record_is_edited(self):
        talk = Talk.objects.create(owner=self.owner, topic='原主题')
        Talk.objects.filter(pk=talk.pk).update(
            updated_at=timezone.now() - timedelta(days=1),
        )
        talk.refresh_from_db()
        previous_updated_at = talk.updated_at
        talk.understanding = '补充理解'
        talk.save()
        talk.refresh_from_db()
        self.assertGreater(talk.updated_at, previous_updated_at)
