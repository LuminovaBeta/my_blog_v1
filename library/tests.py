from django.db.models import ProtectedError
from django.test import TestCase
from django.urls import reverse

from app01.models import UserInfo
from .models import Book, BookQuote, IndependentExcerpt


class LibraryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserInfo.objects.create_user(username="library-reader", password="test-password")
        cls.other = UserInfo.objects.create_user(username="library-other", password="test-password")

    def setUp(self):
        self.client.force_login(self.user)

    def test_login_required(self):
        self.client.logout()
        for name in ("bookshelf", "add_book", "excerpts", "add_excerpt"):
            response = self.client.get(reverse(f"library:{name}"))
            self.assertEqual(response.status_code, 302)
            self.assertIn("/login/", response["Location"])

    def test_dropdown_filters_submit_immediately_without_action_buttons(self):
        for name in ("bookshelf", "excerpts"):
            with self.subTest(name=name):
                response = self.client.get(reverse(f"library:{name}"))
                self.assertContains(response, 'onchange="this.form.requestSubmit()"')
                self.assertContains(response, 'data-library-filter-form')
                self.assertContains(response, 'data-library-results')
                self.assertContains(response, '/static/js/library/filter-results.js')
                self.assertNotContains(response, '>筛选</button>')
                self.assertNotContains(response, '>清空</a>')

    def test_talks_navigation_is_visible_only_to_admin(self):
        self.assertNotContains(self.client.get(reverse("library:bookshelf")), '>谈资库</a>')
        self.client.force_login(self.other)
        self.assertNotContains(self.client.get(reverse("library:excerpts")), '>谈资库</a>')
        admin = UserInfo.objects.create_user(
            username="library-admin", password="test-password",
            is_superuser=True, is_staff=True,
        )
        self.client.force_login(admin)
        for name in ("bookshelf", "excerpts"):
            self.assertContains(self.client.get(reverse(f"library:{name}")), '>谈资库</a>')

    def test_book_filter_returns_only_private_result_fragment(self):
        Book.objects.create(owner=self.user, title="在读书", read_status="reading")
        Book.objects.create(owner=self.user, title="想读书", read_status="want")
        Book.objects.create(owner=self.other, title="别人的在读书", read_status="reading")
        response = self.client.get(
            reverse("library:bookshelf") + "?status=reading",
            headers={"X-Library-Partial": "results"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["X-Library-Partial"], "results")
        self.assertIn("X-Library-Partial", response["Vary"])
        self.assertContains(response, "在读书")
        self.assertNotContains(response, "想读书")
        self.assertNotContains(response, "别人的在读书")
        self.assertNotContains(response, "MY LIBRARY")

    def test_excerpt_filter_returns_only_private_result_fragment(self):
        IndependentExcerpt.objects.create(
            owner=self.user, content="英文电影句子", category="english", source_type="movie",
        )
        IndependentExcerpt.objects.create(
            owner=self.user, content="文言文句子", category="classical", source_type="web",
        )
        IndependentExcerpt.objects.create(
            owner=self.other, content="别人的英文句子", category="english", source_type="movie",
        )
        response = self.client.get(
            reverse("library:excerpts") + "?category=english&source=movie",
            headers={"X-Library-Partial": "results"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["X-Library-Partial"], "results")
        self.assertIn("X-Library-Partial", response["Vary"])
        self.assertContains(response, "共 1 条摘录")
        self.assertContains(response, "英文电影句子")
        self.assertNotContains(response, "文言文句子")
        self.assertNotContains(response, "别人的英文句子")
        self.assertNotContains(response, "WORDS TO KEEP")

    def test_partial_pagination_keeps_filters(self):
        for number in range(13):
            Book.objects.create(
                owner=self.user, title=f"在读书 {number}", read_status="reading",
            )
        url = reverse("library:bookshelf")
        first = self.client.get(
            url + "?status=reading", headers={"X-Library-Partial": "results"},
        )
        self.assertContains(first, "page=2")
        second = self.client.get(
            url + "?status=reading&page=2",
            headers={"X-Library-Partial": "results"},
        )
        self.assertContains(second, 'class="library-book-card"', count=1)
        self.assertContains(second, "status=reading")

    def test_book_create_edit_filter_and_delete(self):
        response = self.client.post(reverse("library:add_book"), {
            "title": "我的书", "author": "某作者", "read_status": "reading",
            "progress_percent": 35,
        })
        self.assertEqual(response.status_code, 302)
        book = Book.objects.get(title="我的书")
        self.assertEqual(book.owner, self.user)
        self.assertContains(self.client.get(reverse("library:bookshelf")), "我的书")
        self.assertContains(self.client.get(reverse("library:bookshelf")), "正在阅读")
        self.assertNotContains(self.client.get(reverse("library:bookshelf") + "?q=不存在"), "某作者")
        response = self.client.post(reverse("library:edit_book", args=[book.pk]), {
            "title": "修改后", "read_status": "finished", "progress_percent": 100,
        })
        self.assertEqual(response.status_code, 302)
        book.refresh_from_db()
        self.assertEqual(book.title, "修改后")
        self.assertEqual(book.read_status, "finished")
        self.assertEqual(self.client.get(reverse("library:delete_book", args=[book.pk])).status_code, 405)
        self.assertEqual(self.client.post(reverse("library:delete_book", args=[book.pk])).status_code, 302)
        self.assertFalse(Book.objects.filter(pk=book.pk).exists())

    def test_book_validation_and_pdf_not_stored(self):
        response = self.client.post(reverse("library:add_book"), {
            "title": "页码不正确", "read_status": "reading", "progress_percent": 101,
            "current_page": 50, "total_pages": 20,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Book.objects.count(), 0)
        self.assertContains(response, "当前页码不能超过总页数")
        self.assertContains(response, "PDF / EPUB")
        self.assertNotIn("ebook", [field.name for field in Book._meta.fields])

    def test_book_quotes_belong_only_to_book_and_are_protected(self):
        book = Book.objects.create(owner=self.user, title="书A")
        response = self.client.post(reverse("library:add_quote", args=[book.pk]), {
            "content": "只在书里出现的句子", "chapter": "第一章", "page_number": 12,
        })
        self.assertEqual(response.status_code, 302)
        quote = BookQuote.objects.get(book=book)
        self.assertEqual(self.client.get(reverse("library:edit_quote", args=[quote.pk])).status_code, 200)
        self.assertEqual(self.client.post(reverse("library:edit_quote", args=[quote.pk]), {
            "content": "修改后的好句", "note": "私人记录",
        }).status_code, 302)
        quote.refresh_from_db()
        self.assertEqual(quote.content, "修改后的好句")
        self.assertContains(self.client.get(reverse("library:book_detail", args=[book.pk])), quote.content)
        self.assertNotContains(self.client.get(reverse("library:excerpts")), quote.content)
        self.assertEqual(self.client.post(reverse("library:delete_book", args=[book.pk])).status_code, 409)
        with self.assertRaises(ProtectedError):
            book.delete()
        self.assertEqual(self.client.post(reverse("library:delete_quote", args=[quote.pk])).status_code, 302)
        self.assertEqual(self.client.post(reverse("library:delete_book", args=[book.pk])).status_code, 302)

    def test_independent_excerpt_crud_and_filter(self):
        self.assertEqual(self.client.get(reverse("library:add_excerpt")).status_code, 200)
        invalid = self.client.post(reverse("library:add_excerpt"), {
            "content": "不能作为书中好句", "source_type": "book",
        })
        self.assertEqual(invalid.status_code, 200)
        self.assertFalse(IndependentExcerpt.objects.exists())
        response = self.client.post(reverse("library:add_excerpt"), {
            "content": "A good sentence", "category": "english", "source_type": "movie",
            "source_title": "A film", "translation": "好句",
        })
        self.assertEqual(response.status_code, 302)
        excerpt = IndependentExcerpt.objects.get(owner=self.user)
        self.assertContains(self.client.get(reverse("library:excerpts") + "?category=english&source=movie"), excerpt.content)
        self.assertNotContains(self.client.get(reverse("library:excerpts") + "?category=classical"), excerpt.content)
        self.assertNotIn("book", [field.name for field in IndependentExcerpt._meta.fields])
        self.assertNotIn("book", IndependentExcerpt.SourceType.values)
        response = self.client.post(reverse("library:edit_excerpt", args=[excerpt.pk]), {
            "content": "Changed sentence", "category": "chinese", "source_type": "web",
        })
        self.assertEqual(response.status_code, 302)
        excerpt.refresh_from_db()
        self.assertEqual(excerpt.content, "Changed sentence")
        self.assertEqual(self.client.get(reverse("library:delete_excerpt", args=[excerpt.pk])).status_code, 405)
        self.assertEqual(self.client.post(reverse("library:delete_excerpt", args=[excerpt.pk])).status_code, 302)
        self.assertFalse(IndependentExcerpt.objects.filter(pk=excerpt.pk).exists())

    def test_other_users_records_are_invisible_and_immutable(self):
        book = Book.objects.create(owner=self.other, title="别人的书")
        quote = BookQuote.objects.create(book=book, content="别人的书中好句")
        excerpt = IndependentExcerpt.objects.create(owner=self.other, content="别人的摘录")
        self.assertNotContains(self.client.get(reverse("library:bookshelf")), book.title)
        self.assertNotContains(self.client.get(reverse("library:excerpts")), excerpt.content)
        for name, pk in (
            ("book_detail", book.pk), ("edit_book", book.pk), ("edit_quote", quote.pk),
            ("edit_excerpt", excerpt.pk),
        ):
            self.assertEqual(self.client.get(reverse(f"library:{name}", args=[pk])).status_code, 404)
        for name, pk, data in (
            ("edit_book", book.pk, {"title": "越权修改"}),
            ("edit_quote", quote.pk, {"content": "越权修改"}),
            ("edit_excerpt", excerpt.pk, {"content": "越权修改"}),
        ):
            self.assertEqual(self.client.post(reverse(f"library:{name}", args=[pk]), data).status_code, 404)
        for name, pk in (
            ("delete_book", book.pk), ("delete_quote", quote.pk), ("delete_excerpt", excerpt.pk),
        ):
            self.assertEqual(self.client.post(reverse(f"library:{name}", args=[pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse("library:add_quote", args=[book.pk]), {"content": "越权"}).status_code, 404)
        self.assertTrue(BookQuote.objects.filter(pk=quote.pk).exists())
        self.assertTrue(IndependentExcerpt.objects.filter(pk=excerpt.pk).exists())
