from django import forms
from .models import Book, BookQuote, IndependentExcerpt


class StyledModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.DateInput):
                field.widget.input_type = "date"
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs.setdefault("rows", 4)

    def clean(self):
        cleaned = super().clean()
        for name, value in cleaned.items():
            if isinstance(value, str):
                cleaned[name] = value.strip()
        return cleaned


class BookForm(StyledModelForm):
    class Meta:
        model = Book
        fields = ("title", "author", "translator", "category", "publisher", "isbn",
                  "published_date", "description", "read_status", "progress_percent",
                  "current_page", "total_pages", "rating", "started_at", "finished_at")

    def clean(self):
        cleaned = super().clean()
        current, total = cleaned.get("current_page"), cleaned.get("total_pages")
        if current is not None and total is not None and current > total:
            self.add_error("current_page", "当前页码不能超过总页数。")
        return cleaned


class BookQuoteForm(StyledModelForm):
    class Meta:
        model = BookQuote
        fields = ("content", "chapter", "page_number", "translation", "note")


class IndependentExcerptForm(StyledModelForm):
    class Meta:
        model = IndependentExcerpt
        fields = ("content", "category", "source_type", "source_title",
                  "attribution", "translation", "note")
