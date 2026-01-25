from django import template
from app01.utils.search import Search
from django.utils.safestring import mark_safe

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

    print(menu_name, article)
    if article:
        # 有值: 说明是文章详情页面
        # print(article)

        # 拿到文章的封面地址
        cover = article.cover.url.url
        print(cover)
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
        order=order,
        # 发布 浏览 点赞 收藏 评论
        order_list=[
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
