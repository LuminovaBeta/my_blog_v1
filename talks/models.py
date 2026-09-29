from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


def validate_tags(value):
    if not isinstance(value, list) or any(
        not isinstance(tag, str) or not tag.strip() for tag in value
    ):
        raise ValidationError("标签必须是非空字符串组成的列表。")


class Talk(models.Model):
    class Category(models.TextChoices):
        UNCLASSIFIED = "unclassified", "未分类"
        SHORT = "short", "短谈资"
        SERIOUS = "serious", "严肃谈资"
        DAILY = "daily", "日常谈资"
        PERSONAL = "personal", "个性谈资"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="talks",
        verbose_name="记录者",
    )
    topic = models.CharField("主题", max_length=200)
    observed = models.TextField("我看到了什么", blank=True)
    interest_reason = models.TextField("为什么吸引我", blank=True)
    understanding = models.TextField("我的理解", blank=True)
    open_questions = models.TextField("还想知道什么", blank=True)
    source = models.TextField("来源", blank=True)
    category = models.CharField(
        "分类",
        max_length=20,
        choices=Category.choices,
        default=Category.UNCLASSIFIED,
    )
    tags = models.JSONField("标签", default=list, blank=True, validators=[validate_tags])
    created_at = models.DateTimeField("记录时间", auto_now_add=True)
    updated_at = models.DateTimeField("修改时间", auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [models.Index(fields=["owner", "-created_at"])]
        verbose_name = "谈资"
        verbose_name_plural = "谈资"

    def clean(self):
        super().clean()
        if not self.topic or not self.topic.strip():
            raise ValidationError({"topic": "主题不能为空。"})
        self.topic = self.topic.strip()

    def __str__(self):
        return self.topic
