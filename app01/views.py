from django.shortcuts import render
from django.shortcuts import HttpResponse
from django.shortcuts import redirect # 重定向
from django.http import JsonResponse
from django import forms
import json
from datetime import timedelta
from app01.utils.random_code import random_code
from app01.utils.sub_comment import sub_comment_list # 评论列表
from app01.utils.pagination import Pagination # 分页
from app01.utils.search import Search # 文章搜索
from app01.utils.article_access import has_article_access

from django.contrib import auth
from app01.models import UserInfo # 导入用户表
from app01.models import Articles # 导入文章表
from app01.models import Tags # 导入标签
from app01.models import Cover # 导入文章封面
from app01.models import Avatars # 导入头像表
from app01.models import ArticleDraft # 导入文章草稿表
from app01.models import Comment # 导入评论表
from app01.models import ArticleView
from django.db.models import Count, F, Min, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone


# Create your views here.


def article_draft_data(draft):
    """生成编辑器初始化所需的草稿数据。"""
    if not draft:
        return None
    return {
        'nid': draft.nid,
        'article_id': draft.article_id,
        'title': draft.title,
        'abstract': draft.abstract,
        'content': draft.content,
        'category': str(draft.category) if draft.category is not None else '',
        'cover_id': str(draft.cover_id) if draft.cover_id else '',
        'cover_url': draft.cover.url.url if draft.cover_id else '',
        'tags': [str(tag.nid) for tag in draft.tags.all()],
        'has_password': bool(draft.pwd) or bool(draft.article and draft.article.pwd),
        'has_saved_draft_password': draft.password_action == 'set' and bool(draft.pwd),
        'password_action': draft.password_action,
        'recommend': draft.recommend,
        'version': draft.version,
        'updated_at': draft.updated_at.isoformat(),
    }

# 主页面
def index(request):
    article_list = Articles.objects.filter(status=1).order_by('-change_date') # 过滤出已发布的文章
    published_articles = Articles.objects.filter(status=1)

    site_article_count = published_articles.count()
    site_total_views = published_articles.aggregate(
        total=Coalesce(Sum('look_count'), 0),
    )['total']
    site_tag_count = Tags.objects.filter(articles__status=1).distinct().count()
    first_publish_date = published_articles.aggregate(
        first=Min('create_date'),
    )['first']
    if first_publish_date:
        site_days = max(
            (timezone.localdate() - timezone.localtime(first_publish_date).date()).days + 1,
            1,
        )
    else:
        site_days = 0

    forty_eight_hours_ago = timezone.now() - timedelta(hours=48)
    reading_rank = published_articles.filter(
        view_records__viewed_at__gte=forty_eight_hours_ago,
    ).annotate(
        recent_views=Count('view_records'),
    ).order_by('-recent_views', '-look_count', '-change_date')[:5]
    # 过滤分类
    tech_list = article_list.filter(category=1)[:6]  # 过滤出技术
    project_list = article_list.filter(category=2)[:6]  # 过滤出项目

    # 分页
    query_params = request.GET.copy()
    pager = Pagination(current_page=request.GET.get('page'),
        all_count=article_list.count(),
        base_url='',
        query_params=query_params,
        per_page=12,
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
    article_list = Articles.objects.filter(status=1, title__icontains=search_key)

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
        per_page=12,
        pager_page_count=7,
    )
    article_list = article_list[ pager.start:pager.end ]


    # 文章搜索条件
    return render(request,'search.html', locals())

# 文章页面
def article(request, nid):
    artitle_query = Articles.objects.filter(nid=nid)
    if not artitle_query:
        return redirect('/')     # 找不到对应文章就回首页
    article = artitle_query.first()    # 找到nid为nid的，第一篇文章，

    # 受保护文章在 Session 解锁前不渲染正文，也不记录阅读量。
    if not has_article_access(request, article):
        return render(request, 'article_locked.html', {'article': article})

    # 每刷新一次浏览量加一
    artitle_query.update(look_count=F('look_count')+1)
    article.refresh_from_db(fields=['look_count'])
    ArticleView.objects.create(article=article)

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

    published_articles = Articles.objects.filter(status=1)
    published_count = published_articles.count()
    draft_count = ArticleDraft.objects.filter(owner=request.user).count()
    received_comment_count = Comment.objects.filter(
        article__status=1,
    ).count()
    total_reads = published_articles.aggregate(
        total=Coalesce(Sum('look_count'), 0),
    )['total']

    collected_articles = request.user.collects.filter(status=1).select_related(
        'cover',
    ).order_by('-change_date')
    collected_count = collected_articles.count()

    recent_article_items = [
        {
            'title': article.title or '未命名文章',
            'status': '已发布',
            'status_type': 'success',
            'updated_at': article.change_date,
            'look_count': article.look_count,
            'edit_url': f'/backend/edit_article/{article.nid}/',
        }
        for article in published_articles.order_by('-change_date')[:5]
    ]
    recent_draft_items = [
        {
            'title': draft.title or '未命名草稿',
            'status': '修改草稿' if draft.article_id else '新文章草稿',
            'status_type': 'warning' if draft.article_id else 'info',
            'updated_at': draft.updated_at,
            'look_count': draft.article.look_count if draft.article_id else 0,
            'edit_url': (
                f'/backend/edit_article/{draft.article_id}/'
                if draft.article_id
                else f'/backend/add_article?draft={draft.nid}'
            ),
        }
        for draft in ArticleDraft.objects.filter(owner=request.user).select_related(
            'article',
        ).order_by('-updated_at')[:5]
    ]
    recent_edit_items = sorted(
        recent_article_items + recent_draft_items,
        key=lambda item: item['updated_at'].timestamp() if item['updated_at'] else 0,
        reverse=True,
    )[:5]

    recent_comments = Comment.objects.filter(
        article__status=1,
    ).select_related('article', 'user').order_by('-create_time')[:5]
    return render(request, 'backend/backend.html', locals())

def add_article(request):
    if not request.user.is_superuser:
        return redirect('/')

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

    draft_obj = None
    draft_id = request.GET.get('draft')
    if draft_id and draft_id.isdigit():
        draft_obj = ArticleDraft.objects.filter(
            nid=draft_id,
            owner=request.user,
            article__isnull=True,
        ).prefetch_related('tags').first()
    draft_data = article_draft_data(draft_obj)

    return render(request, 'backend/add_article.html', locals())


# 文章草稿列表
def draft_list(request):
    if not request.user.is_superuser:
        return redirect('/')

    draft_query = ArticleDraft.objects.filter(owner=request.user).select_related(
        'article',
        'cover',
    ).prefetch_related('tags')
    draft_count = draft_query.count()
    return render(request, 'backend/draft_list.html', locals())


# 文章管理列表
def article_list(request):
    if not request.user.is_superuser:
        return redirect('/')

    article_query = Articles.objects.select_related('cover').prefetch_related(
        'tag',
    ).order_by('-change_date')
    article_count = article_query.count()
    return render(request, 'backend/article_list.html', locals())

# 编辑修改头像
def edit_avatar(request):
    # 拿到所有的头像
    avatar_list = Avatars.objects.all()

    # 如果是用户名注册
    # avatar_id = request.user.avatar.nid
    # 检查用户是否有头像
    if request.user.avatar:
        avatar_id = request.user.avatar.nid
    else:
        # 如果没有头像，给它指定一个默认头像的 nid，或者直接设为 None
        # 具体取决于你前端逻辑的需要，通常设为 None 即可
        avatar_id = None

    # 如果是其他方式注册则查询
    avatar_url = request.user.avatar_url
    # 找到当前用户头像，用于初始化
    for i in avatar_list:

        # --- 调试代码开始 ---
        print(f"系统头像: {i.url.url} (类型: {type(i.url.url)})")
        print(f"用户头像: {avatar_url} (类型: {type(avatar_url)})")
        print("-" * 20)
        # --- 调试代码结束 ---

        if i.url.url == avatar_url:
            avatar_id = i.nid
            break

    return render(request, 'backend/edit_avatar.html', locals())

# 重置密码
def reset_passward(request):
    return render(request, 'backend/reset_passward.html', locals())

# 编辑文章
def edit_article(request, nid):
    if not request.user.is_superuser:
        return redirect('/')

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
    draft_obj = ArticleDraft.objects.filter(
        article=article_obj,
        owner=request.user,
    ).prefetch_related('tags').first()
    draft_data = article_draft_data(draft_obj)
    return render(request, 'backend/edit_article.html', locals())

# 头像列表 / 编辑头像
def avatar_list(request):
    user = request.user
    sign_status = user.sign_status
    # 查询所有的头像
    avatar_list = Avatars.objects.all()

    if sign_status == 0:
        # 如果是用户名注册
        # avatar_id = request.user.avatar.nid
        # 增加容错判断
        if request.user.avatar:
            avatar_id = request.user.avatar.nid
        else:
            avatar_id = None  # 或者设置成你数据库里默认头像的真实 ID
    else:
        avatar_url = request.user.avatar_url
        for i in avatar_list:
            if i.url.url == avatar_url:
                avatar_id = i.nid
    return render(request, 'backend/avatar_list.html', locals())

# 文章封面
def cover_list(request):
    cover_query = Cover.objects.all()
    return render(request, 'backend/cover_list.html', locals())

# simpleui显示自己想显示的页面
# def admin_home(request):
#     return render(request, 'admin_home.html', locals())

def moods(request):
    return render(request, 'moods.html', locals())
