from django import template
from app01.utils.search import Search # 通用的 Search 工具类
from django.utils.safestring import mark_safe
from app01.models import Tags

# 注册
register = template.Library()

# 自定义过滤器
# @register.filter
# def add1(item):
#     return int(item) + 1

@register.inclusion_tag('my_tag/headers.html')
def banner(menu_name, article=None):
    img_list = [
        "/static/my/img/header/index_小汽车.png",
        "/static/my/img/header/index_1.jpg",
        "/static/my/img/header/index_2.jpg"        
    ]

    if article:
        # 有值: 说明是文章详情页面

        # 拿到文章的封面地址
        cover = article.cover.url.url
        img_list = [cover]
        pass

    return {"img_list": img_list}

# 搜索界面的排序标签
@register.simple_tag
def generate_order_html(request):
    order = request.GET.get('order', '')
    query_params = request.GET.copy()
    # 生成排序标签
    order = Search(
        key='order',
        current_val=order,
        # 发布 浏览 点赞 收藏 评论
        data_list=[
            ('-change_date', '综合排序'), 
            ('-create_date', '最新发布'), 
            ('-look_count', '最多浏览'), 
            ('-digg_count', '最多点赞'), 
            ('-collects_count', '最多收藏'), 
            ('-comment_count', '最多评论'), 
        ],
        query_params=query_params
    )
    return mark_safe(order.order_html())

# 搜索界面的字数筛选标签
@register.simple_tag
def generate_word_html(request):
    word = request.GET.get('word', '')
    query_params = request.GET.copy()
    # 生成排序标签
    word = Search(
        key='word',
        current_val=word,
        # 发布 浏览 点赞 收藏 评论
        data_list=[
            ('0', '全部字数'), 
            ('1', '1000字以下'), 
            ('2', '1K-3K字'), 
            ('3', '3K-5K字'), 
            ('4', '5K字以上'), 
        ],
        query_params=query_params
    )
    return mark_safe(word.order_html())

# 搜索界面的标签筛选标签
@register.simple_tag
def generate_tag_html(request):
    tag = request.GET.get('tag', '')
    tag_list = Tags.objects.exclude(articles__isnull=True) # 过滤掉没有文章的标签

    data_list = []
    data_list.append(('', '全部标签'))
    for tag_obj in tag_list:
        data_list.append((tag_obj.title, tag_obj.title))

    query_params = request.GET.copy()

    # 生成排序标签
    tag = Search(
        key='tag',
        current_val=tag,
        # 发布 浏览 点赞 收藏 评论
        data_list=data_list,
        query_params=query_params
    )
    return mark_safe(tag.order_html())
