"""
URL configuration for my_blog project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from app01 import views
from django.conf import settings
from django.views.static import serve

urlpatterns = [
    path('admin/', admin.site.urls),
    # 函数分发
    # path('admin_home/', views.admin_home), # 自定义admin页面（未开发）
    path('',views.index),
    path('news/', views.news), # 新闻页面（未开发）
    path('search/', views.search), 
    path('moods/', views.moods), # 心情页面（未开发）
    path('login/', views.login),
    path('login/random_code/', views.get_random_code),
    path('sign/', views.sign),
    path('logout/', views.logout),
    path('backend/', views.backend),
    path('backend/add_article', views.add_article), # 后台添加文章
    path('backend/edit_avatar', views.edit_avatar), # 后台修改头像
    path('backend/reset_passward', views.reset_passward), # 后台重置密码

    re_path(r'^backend/edit_article/(?P<nid>\d+)/', views.edit_article), # 编辑文章

    # 匹配文章页面
    re_path(r'^article/(?P<nid>\d+)/', views.article), # 正则表达式
    re_path(r'^api/', include('api.urls')),  # 将所有api开头的api，都分发到api的urls.py中
    re_path(r'media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}), # 用户上传文件路由配置
]
