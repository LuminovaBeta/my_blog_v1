from django import template

# 注册
register = template.Library()


# 自定义过滤器, 用户是否收藏文章
# 如果有登录返回 show
# 没有返回 空字符串
@register.filter
def is_user_coll(article, request):
    if str(request.user) == 'AnonymousUser':
        # 没有登录
        return ''
    if article in request.user.collects.all():
        return 'show'
    return ''