from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

class Book(models.Model):
    class ReadStatus(models.TextChoices):
        WANT = "want", "想读"
        READING = "reading", "在读"
        FINISHED = "finished", "已读"
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="library_books")
    title = models.CharField("书名", max_length=200)
    author = models.CharField("作者", max_length=200, blank=True)
    translator = models.CharField("译者", max_length=200, blank=True)
    category = models.CharField("分类", max_length=100, blank=True)
    publisher = models.CharField("出版社", max_length=200, blank=True)
    isbn = models.CharField("ISBN", max_length=20, blank=True)
    published_date = models.DateField("出版日期", null=True, blank=True)
    description = models.TextField("书籍简介", blank=True)
    read_status = models.CharField("阅读状态", max_length=20, choices=ReadStatus.choices, default=ReadStatus.WANT)
    progress_percent = models.PositiveSmallIntegerField("阅读进度", default=0, validators=[MaxValueValidator(100)])
    current_page = models.PositiveIntegerField("当前页码", null=True, blank=True)
    total_pages = models.PositiveIntegerField("总页数", null=True, blank=True)
    rating = models.PositiveSmallIntegerField("评分", null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)])
    started_at = models.DateField("开始阅读日期", null=True, blank=True)
    finished_at = models.DateField("读完日期", null=True, blank=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("修改时间", auto_now=True)
    class Meta:
        ordering = ["-updated_at", "-id"]
        indexes = [models.Index(fields=["owner", "-updated_at"])]
    def __str__(self):
        return self.title

class BookQuote(models.Model):
    book = models.ForeignKey(Book, on_delete=models.PROTECT, related_name="quotes")
    content = models.TextField("好句内容")
    chapter = models.CharField("章节", max_length=200, blank=True)
    page_number = models.PositiveIntegerField("页码", null=True, blank=True)
    translation = models.TextField("译文", blank=True)
    note = models.TextField("我的想法", blank=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("修改时间", auto_now=True)
    class Meta:
        ordering = ["-updated_at", "-id"]
    def __str__(self):
        return self.content[:40]

class IndependentExcerpt(models.Model):
    class Category(models.TextChoices):
        ENGLISH = "english", "英文"
        CHINESE = "chinese", "现代中文"
        CLASSICAL = "classical", "文言文"
        OTHER = "other", "其他"
    class SourceType(models.TextChoices):
        MOVIE = "movie", "电影"
        WEB = "web", "网页"
        OTHER = "other", "其他"
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="independent_excerpts")
    content = models.TextField("摘录内容")
    category = models.CharField("内容类别", max_length=20, choices=Category.choices, default=Category.OTHER)
    source_type = models.CharField("来源类型", max_length=20, choices=SourceType.choices, default=SourceType.OTHER)
    source_title = models.CharField("来源作品", max_length=200, blank=True)
    attribution = models.CharField("人物或作者", max_length=200, blank=True)
    translation = models.TextField("译文", blank=True)
    note = models.TextField("我的想法", blank=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("修改时间", auto_now=True)
    class Meta:
        ordering = ["-updated_at", "-id"]
        indexes = [models.Index(fields=["owner", "-updated_at"])]
    def __str__(self):
        return self.content[:40]
