from django.contrib import admin
from app01.models import Articles # 文章表
from app01.models import Tags # 标签表
from app01.models import Cover # 文章封面表
from app01.models import Comment # 文章评论
from app01.models import Avatars # 头像
from app01.models import UserInfo # 用户

# Register your models here.

admin.site.register(Articles)
admin.site.register(Tags)
admin.site.register(Cover)
admin.site.register(Comment)
admin.site.register(Avatars)
admin.site.register(UserInfo)