from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.vary import vary_on_headers
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .forms import BookForm, BookQuoteForm, IndependentExcerptForm
from .models import Book, BookQuote, IndependentExcerpt


@login_required(login_url="/login/")
@require_GET
@vary_on_headers("X-Library-Partial")
def bookshelf(request):
    owned = Book.objects.filter(owner=request.user)
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "")
    books = owned
    if query:
        books = books.filter(Q(title__icontains=query) | Q(author__icontains=query))
    if status in Book.ReadStatus.values:
        books = books.filter(read_status=status)
    page = Paginator(books, 12).get_page(request.GET.get("page"))
    context = {"books": page, "query": query, "status": status}
    if request.headers.get("X-Library-Partial") == "results":
        response = render(request, "library/bookshelf_results.html", context)
        response["X-Library-Partial"] = "results"
        return response
    context.update({
        "total_count": owned.count(),
        "reading_count": owned.filter(read_status=Book.ReadStatus.READING).count(),
        "finished_count": owned.filter(read_status=Book.ReadStatus.FINISHED).count(),
    })
    return render(request, "library/bookshelf.html", context)


@login_required(login_url="/login/")
@require_http_methods(["GET", "POST"])
def add_book(request):
    form = BookForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        book = form.save(commit=False)
        book.owner = request.user
        book.save()
        return redirect("library:book_detail", pk=book.pk)
    return render(request, "library/add_book.html", {"form": form, "is_edit": False})


@login_required(login_url="/login/")
@require_GET
def book_detail(request, pk):
    book = get_object_or_404(Book.objects.prefetch_related("quotes"), pk=pk, owner=request.user)
    return render(request, "library/book_preview.html", {"book": book})


@login_required(login_url="/login/")
@require_http_methods(["GET", "POST"])
def edit_book(request, pk):
    book = get_object_or_404(Book, pk=pk, owner=request.user)
    form = BookForm(request.POST or None, instance=book)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("library:book_detail", pk=book.pk)
    return render(request, "library/add_book.html", {"form": form, "book": book, "is_edit": True})


@login_required(login_url="/login/")
@require_POST
def delete_book(request, pk):
    book = get_object_or_404(Book, pk=pk, owner=request.user)
    if book.quotes.exists():
        return HttpResponse("请先删除这本书的好句，再删除书籍。", status=409)
    book.delete()
    return redirect("library:bookshelf")


@login_required(login_url="/login/")
@require_http_methods(["GET", "POST"])
def add_quote(request, book_id):
    book = get_object_or_404(Book, pk=book_id, owner=request.user)
    form = BookQuoteForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        quote = form.save(commit=False)
        quote.book = book
        quote.save()
        return redirect("library:book_detail", pk=book.pk)
    return render(request, "library/quote_form.html", {"form": form, "book": book, "is_edit": False})


@login_required(login_url="/login/")
@require_http_methods(["GET", "POST"])
def edit_quote(request, pk):
    quote = get_object_or_404(BookQuote.objects.select_related("book"), pk=pk, book__owner=request.user)
    form = BookQuoteForm(request.POST or None, instance=quote)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("library:book_detail", pk=quote.book_id)
    return render(request, "library/quote_form.html", {"form": form, "book": quote.book, "is_edit": True})


@login_required(login_url="/login/")
@require_POST
def delete_quote(request, pk):
    quote = get_object_or_404(BookQuote, pk=pk, book__owner=request.user)
    book_id = quote.book_id
    quote.delete()
    return redirect("library:book_detail", pk=book_id)


@login_required(login_url="/login/")
@require_GET
@vary_on_headers("X-Library-Partial")
def excerpts(request):
    records = IndependentExcerpt.objects.filter(owner=request.user)
    query = request.GET.get("q", "").strip()
    category = request.GET.get("category", "")
    source = request.GET.get("source", "")
    if query:
        records = records.filter(Q(content__icontains=query) | Q(source_title__icontains=query) | Q(attribution__icontains=query))
    if category in IndependentExcerpt.Category.values:
        records = records.filter(category=category)
    if source in IndependentExcerpt.SourceType.values:
        records = records.filter(source_type=source)
    count = records.count()
    page = Paginator(records, 10).get_page(request.GET.get("page"))
    context = {
        "excerpts": page, "query": query, "category": category, "source": source,
        "count": count,
    }
    if request.headers.get("X-Library-Partial") == "results":
        response = render(request, "library/excerpt_results.html", context)
        response["X-Library-Partial"] = "results"
        return response
    context.update({
        "categories": IndependentExcerpt.Category.choices,
        "sources": IndependentExcerpt.SourceType.choices,
    })
    return render(request, "library/excerpts.html", context)


@login_required(login_url="/login/")
@require_http_methods(["GET", "POST"])
def add_excerpt(request):
    form = IndependentExcerptForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        excerpt = form.save(commit=False)
        excerpt.owner = request.user
        excerpt.save()
        return redirect("library:excerpts")
    return render(request, "library/excerpt_form.html", {"form": form, "is_edit": False})


@login_required(login_url="/login/")
@require_http_methods(["GET", "POST"])
def edit_excerpt(request, pk):
    excerpt = get_object_or_404(IndependentExcerpt, pk=pk, owner=request.user)
    form = IndependentExcerptForm(request.POST or None, instance=excerpt)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("library:excerpts")
    return render(request, "library/excerpt_form.html", {"form": form, "is_edit": True})


@login_required(login_url="/login/")
@require_POST
def delete_excerpt(request, pk):
    excerpt = get_object_or_404(IndependentExcerpt, pk=pk, owner=request.user)
    excerpt.delete()
    return redirect("library:excerpts")


@login_required(login_url="/login/")
@require_GET
def book_preview(request):
    return redirect("library:bookshelf")
