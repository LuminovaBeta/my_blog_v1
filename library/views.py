from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.http import require_GET


@login_required(login_url='/login/')
@require_GET
def bookshelf(request):
    """展示书架草图；目前不查询书籍数据。"""
    return render(request, 'library/bookshelf.html')


@login_required(login_url='/login/')
@require_GET
def book_preview(request):
    """固定示例详情页，与真实书籍主键无关。"""
    return render(request, 'library/book_preview.html')


@login_required(login_url='/login/')
@require_GET
def add_book_preview(request):
    """仅展示新增表单的样式，不接收或保存输入。"""
    return render(request, 'library/add_book.html')
