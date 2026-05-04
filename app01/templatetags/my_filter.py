from django import template
import pendulum
import datetime

# 导入需要使用到的类
from app01.models import Avatars, Cover, UserInfo

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

# 判断是否有文章内容
@register.filter
def is_article_list(article_list):
    if len(article_list):
        return 'search_content'
    return 'no_content'

# 时间格式化
@register.filter
def date_humaniz(date: datetime.datetime):
    """
    date_humaniz 的 Docstring
    将时间转换为人性化描述 (如: 3分钟前)

    :param date: 时间对象，需要与现在(now)计算差值的时间
    :type date: datetime.datetime
    """
    # 将传入的 时间对象 转换成 pendulum 对象
    p_date = pendulum.instance(date).in_timezone('Asia/Shanghai')
    # print(p_date)

    now = pendulum.now('Asia/Shanghai')
    # print(now)

    # 计算相差天数
    diff_days = p_date.diff(now).in_days()

    # 超过7天
    if diff_days >= 7:
        if p_date.year == now.year:
            return p_date.format('MM-DD')
        else:
            return p_date.format('YYYY-MM-DD')
        
    # 7天以内显示相对时间
    time_difference = p_date.diff_for_humans(locale='zh')

    return time_difference

# 计算使用头像的总和
@register.filter
def to_calculate_avatar(avatar: Avatars):
    # moodcomment_set: 心情评论头像使用(暂时不用)
    # moods_set: 心情头像使用(暂时不用)
    # userinfo_set: 用户头像使用
    count = avatar.moodcomment_set.count() + avatar.moods_set.count() + avatar.userinfo_set.count()
    if count:
        return ''
    return 'no_avatar'

# 计算使用文章封面的总和
@register.filter
def to_calculate_cover(cover: Cover):
    count = cover.articles_set.count()
    # print(count)
    if count:
        return ''
    return 'no_cover'

# 获取用户头像
@register.filter
def get_avatar(user: UserInfo):
    if user.sign_status in [1, 2]:
        return user.avatar_url
    if user.avatar:
        return user.avatar.url.url
    return ''