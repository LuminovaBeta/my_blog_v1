from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from .forms import TalkForm
from .models import Talk


@login_required(login_url="/login/")
@require_http_methods(["GET", "POST"])
def index(request):
    """管理员可以快速记录谈资，并查看自己的记录。"""
    if not request.user.is_superuser:
        raise PermissionDenied

    form = TalkForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        talk = form.save(commit=False)
        talk.owner = request.user
        talk.tags = form.cleaned_data["tags_input"]
        talk.save()
        return redirect(f"{reverse('talks:index')}#talk-list")

    talks = Paginator(
        Talk.objects.filter(owner=request.user), 10,
    ).get_page(request.GET.get("page"))
    return render(request, "talks/index.html", {
        "form": form,
        "talks": talks,
    })
