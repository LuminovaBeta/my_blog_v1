from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.http import require_GET


@login_required(login_url='/login/')
@require_GET
def index(request):
    """私人谈资库的入口；录入和数据模型尚未实现。"""
    return render(request, 'talks/index.html')
