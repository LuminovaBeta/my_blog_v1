from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_http_methods, require_POST
from django.views.decorators.vary import vary_on_headers

from .forms import TalkForm
from .models import Talk


@login_required(login_url="/login/")
@require_http_methods(["GET", "POST"])
@vary_on_headers("X-Library-Partial")
def index(request):
    _require_admin(request)

    if request.method == "POST":
        form = TalkForm(request.POST)
        if form.is_valid():
            talk = form.save(commit=False)
            talk.owner = request.user
            talk.tags = form.cleaned_data["tags_input"]
            talk.save()
            return redirect(f"{reverse('talks:index')}#talk-list")
    else:
        form = TalkForm()

    owned = Talk.objects.filter(owner=request.user)
    query = request.GET.get("q", "").strip()
    category = request.GET.get("category", "")
    tag = request.GET.get("tag", "")
    tags = sorted({item for values in owned.values_list("tags", flat=True) for item in values})
    records = owned
    if query:
        records = records.filter(
            Q(topic__icontains=query) | Q(observed__icontains=query)
            | Q(interest_reason__icontains=query) | Q(understanding__icontains=query)
            | Q(open_questions__icontains=query) | Q(source__icontains=query)
        )
    if category in Talk.Category.values:
        records = records.filter(category=category)
    if tag and tag in tags:
        # JSON containment is not supported by every database used for this project.
        matching_ids = [pk for pk, values in records.values_list("pk", "tags") if tag in values]
        records = records.filter(pk__in=matching_ids)
    elif tag:
        records = records.none()
    page = Paginator(records, 10).get_page(request.GET.get("page"))
    context = {
        "form": form, "talks": page, "query": query, "category": category,
        "tag": tag, "tags": tags, "categories": Talk.Category.choices,
    }
    if request.method == "GET" and request.headers.get("X-Library-Partial") == "results":
        response = render(request, "talks/results.html", context)
        response["X-Library-Partial"] = "results"
        return response
    return render(request, "talks/index.html", context)


@login_required(login_url="/login/")
@require_GET
def detail(request, pk):
    _require_admin(request)
    talk = get_object_or_404(Talk, pk=pk, owner=request.user)
    return render(request, "talks/detail.html", {"talk": talk})


@login_required(login_url="/login/")
@require_http_methods(["GET", "POST"])
def edit(request, pk):
    _require_admin(request)
    talk = get_object_or_404(Talk, pk=pk, owner=request.user)
    form = TalkForm(request.POST or None, instance=talk)
    if request.method == "POST" and form.is_valid():
        edited = form.save(commit=False)
        edited.tags = form.cleaned_data["tags_input"]
        edited.save()
        return redirect("talks:detail", pk=pk)
    return render(request, "talks/edit.html", {"form": form, "talk": talk})


@login_required(login_url="/login/")
@require_POST
def delete(request, pk):
    _require_admin(request)
    talk = get_object_or_404(Talk, pk=pk, owner=request.user)
    talk.delete()
    return redirect(f"{reverse('talks:index')}#talk-list")


def _require_admin(request):
    if not request.user.is_superuser:
        raise PermissionDenied
