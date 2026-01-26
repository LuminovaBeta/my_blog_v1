from django.shortcuts import render
from django.shortcuts import HttpResponse
from django.shortcuts import redirect # 重定向
from django.http import JsonResponse
from django import forms
import json
from app01.utils.random_code import random_code
from app01.utils.sub_comment import sub_comment_list # 评论列表
from app01.utils.pagination import Pagination # 分页
from app01.utils.search import Search # 文章搜索

from django.contrib import auth
from app01.models import UserInfo # 导入用户表
from app01.models import Articles # 导入文章表
from app01.models import Tags # 导入标签
from app01.models import Cover # 导入文章封面
from django.db.models import F




# Create your views here.

# 主页面
def index(request):
    article_list = Articles.objects.filter(status=1).order_by('-change_date') # 过滤出已发布的文章
    # 过滤分类
    tech_list = article_list.filter(category=1)[:6]  # 过滤出技术
    project_list = article_list.filter(category=2)[:6]  # 过滤出项目

    # 分页
    query_params = request.GET.copy()
    pager = Pagination(current_page=request.GET.get('page'),
        all_count=article_list.count(),
        base_url='',
        query_params=query_params,
        per_page=1,
        pager_page_count=7,
    )
    article_list = article_list[ pager.start:pager.end ]
    
    return render(request,'index.html', locals())

# 搜索页面
def search(request):
    search_key = request.GET.get('key', '')
    order = request.GET.get('order', '')
    word = request.GET.get('word', '')
    tag = request.GET.get('tag', '')
    query_params = request.GET.copy()
    article_list = Articles.objects.filter(title__icontains=search_key)

    # 排序
    if order:
        # 用户随意输入搜索条件，跳过
        try:
            article_list = article_list.order_by(order)
        except Exception:
            pass

    # 字数筛选
    if word:
        if word == '1':
            article_list = article_list.filter(word__range=(0, 1000))
        elif word == '2':
            article_list = article_list.filter(word__range=(1000, 3000))
        elif word == '3':
            article_list = article_list.filter(word__range=(3000, 5000))
        elif word == '4':
            article_list = article_list.filter(word__range=(5000, 9999999))

    # 标签筛选
    if tag:
        article_list = article_list.filter(tag__title=tag)

    # 分页器
    pager = Pagination(current_page=request.GET.get('page'),
        all_count=article_list.count(),
        base_url='',
        query_params=query_params,
        per_page=4,
        pager_page_count=7,
    )
    article_list = article_list[ pager.start:pager.end ]


    # 文章搜索条件
    return render(request,'search.html', locals())

# 文章页面
def article(request, nid):
    # print(nid)
    artitle_query = Articles.objects.filter(nid=nid)
    # 每刷新一次浏览量加一
    artitle_query.update(look_count=F('look_count')+1)
    if not artitle_query:
        return redirect('/')     # 找不到对应文章就回首页
    article = artitle_query.first()    # 找到nid为nid的，第一篇文章，

    comment_list = sub_comment_list(nid) # 拿到文章评论列表
    print(comment_list) 

    return render(request, 'article.html', locals())  # locals()把所有数据传给前端

# 新闻页面
def news(request):
    return render(request, 'news.html')


def login(request):
    return render(request, 'login.html')

# 获取随机验证码
def get_random_code(request):
    data, valid_code = random_code()
    request.session['valid_code'] = valid_code
    return HttpResponse(data)

def sign(request):
    return render(request, 'sign.html')

def logout(request):
    auth.logout(request)
    return redirect('/')

def backend(request):
    if not request.user.username:
        return redirect('/')
    return render(request, 'backend/backend.html', locals())

def add_article(request):
    # 拿到所有的分类、标签
    tag_list = Tags.objects.all()
    # 拿到所有的文章封面
    cover_list = Cover.objects.all()
    c_l = []
    for cover in cover_list:
        c_l.append({
            'url': cover.url.url,
            'nid': cover.nid,
        })

    # 拿到分类的字段
    categroy_list = Articles.category_choice

    return render(request, 'backend/add_article.html', locals())

def edit_avatar(request):
    return render(request, 'backend/edit_avatar.html', locals())

def reset_passward(request):
    return render(request, 'backend/reset_passward.html', locals())

def edit_article(request, nid):
    # 拿到所有的分类、标签
    tag_list = Tags.objects.all()
    # 拿到所有的文章封面
    cover_list = Cover.objects.all()
    c_l = []
    for cover in cover_list:
        c_l.append({
            'url': cover.url.url,
            'nid': cover.nid,
        })
    
    # print(nid)
    article_obj = Articles.objects.get(nid=nid)
    # tag的QuerySet数组反序列化
    tags = [str(tag.nid) for tag in article_obj.tag.all()]
    # print(tags)
    # 拿到分类的字段
    categroy_list = Articles.category_choice
    return render(request, 'backend/edit_article.html', locals())