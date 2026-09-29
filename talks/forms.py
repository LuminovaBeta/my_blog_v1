from django import forms

from .models import Talk


class TalkForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk and not self.is_bound:
            self.fields["tags_input"].initial = "，".join(self.instance.tags)

    category = forms.ChoiceField(
        label="分类",
        choices=Talk.Category.choices,
        required=False,
        initial=Talk.Category.UNCLASSIFIED,
    )
    tags_input = forms.CharField(
        label="标签",
        required=False,
        max_length=500,
        widget=forms.TextInput(attrs={
            "placeholder": "例如：电影、人物、旅行（用逗号分隔）",
        }),
    )

    class Meta:
        model = Talk
        fields = (
            "topic", "observed", "interest_reason", "understanding",
            "open_questions", "source", "category",
        )
        widgets = {
            "topic": forms.TextInput(attrs={"placeholder": "用一句话记下这件事"}),
            "observed": forms.Textarea(attrs={
                "rows": 3, "placeholder": "发生了什么？先随手记几句就好",
            }),
            "interest_reason": forms.Textarea(attrs={"rows": 3}),
            "understanding": forms.Textarea(attrs={"rows": 3}),
            "open_questions": forms.Textarea(attrs={"rows": 3}),
            "source": forms.Textarea(attrs={
                "rows": 2, "placeholder": "例如：自己的经历、文章标题或网页链接",
            }),
        }

    def clean_tags_input(self):
        raw = self.cleaned_data["tags_input"].replace("，", ",")
        tags = list(dict.fromkeys(
            part.strip() for part in raw.split(",") if part.strip()
        ))
        if len(tags) > 20 or any(len(tag) > 30 for tag in tags):
            raise forms.ValidationError("最多填写 20 个标签，每个标签不超过 30 个字。")
        return tags

    def clean_category(self):
        return self.cleaned_data["category"] or Talk.Category.UNCLASSIFIED
