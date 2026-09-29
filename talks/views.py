from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from django.views.decorators.http import require_GET


@login_required(login_url='/login/')
@require_GET
def index(request):
    """管理员专用的谈资库入口；录入和数据模型尚未实现。"""
    if not request.user.is_superuser:
        raise PermissionDenied
    return render(request, 'talks/index.html')
