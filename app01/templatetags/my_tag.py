from django import template

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
