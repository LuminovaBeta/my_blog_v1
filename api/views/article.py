from django.views import View
from django.http import JsonResponse
from markdown import markdown
from pyquery import PyQuery
from django import forms
from api.views.login import clean_form

from app01.models import Tags, Articles, Cover
import random
from django.db.models import F

class AddArticleForm(forms.Form):
    title = forms.CharField(error_messages={'required': '请输入文章标题'})
    content = forms.CharField(error_messages={'required': '请输入文章内容'})
    abstract = forms.CharField(required=False) # 不进行为空验证
    cover_id = forms.IntegerField(required=False) # 不进行为空验证

    category = forms.IntegerField(required=False) # 不进行为空验证
    pwd = forms.CharField(required=False) # 不进行为空验证
    recommend = forms.BooleanField(required=False)
    status = forms.IntegerField(required=False)
    word = forms.IntegerField(required=False)


    # 全局钩子校验分类和密码
    def clean(self):
        category = self.cleaned_data['category']
        if not category:
            self.cleaned_data.pop('category')        

        pwd = self.cleaned_data['pwd']
        if not pwd:
            self.cleaned_data.pop('pwd')

    # 局部钩子-文章简介
    def clean_abstract(self):
        abstract = self.cleaned_data['abstract']
        # 1. 数据库配置的能存的最大长度
        db_max_length = 150
        if abstract:
            # 如果超过长度，直接截取前150个字符
            if len(abstract) > db_max_length:
                return abstract[:db_max_length]
            return abstract
        # 截取正文的前80字符
        content = self.cleaned_data.get('content')
        if content:
            abstract = PyQuery(markdown(content)).text()[:80]
            return abstract
        
    # 获取文章字数
    def clean_word(self):
        word = self.cleaned_data['word']
        content = self.cleaned_data.get('content')
        if content:
            word = len(PyQuery(markdown(content)).text())
        return word
    
    # 文章封面
    def clean_cover_id(self):
        cover_id = self.cleaned_data['cover_id']
        if cover_id:
            return cover_id
        cover_set = Cover.objects.all().values('nid')
        cover_id = random.choice(cover_set)['nid']
        return cover_id
    
class ArticleView(View):
    # 发布文章
    def post(self, request):
        res = {
            'msg': '文章发布成功',
            'code': 412,
            "data": None,
        }

        data = request.data

        # 状态改为已发布
        data['status'] = 1
        
        form = AddArticleForm(data)
        if not form.is_valid():
            res['self'], res['msg'] = clean_form(form)
            return JsonResponse(res)

        # 校验通过
        form.cleaned_data['author'] = 'wshsm'
        form.cleaned_data['source'] = 'yt'
        article_obj = Articles.objects.create(**form.cleaned_data)
        tags = data.get('tags')
        # print(tags)
        # 校验是否存在
        for tag in tags:
            if tag.isdigit():
                # 是数字
                article_obj.tag.add(tag)
            else:
                # 先创建，再多对多关联
                tag_obj = Tags.objects.create(title=tag)
                article_obj.tag.add(tag_obj.nid)
        res['code'] = 0
        res['data'] = article_obj.nid
        return JsonResponse(res)
    
    # 编辑文章
    def put(self, request, nid):
        res = {
            'msg': '文章编辑成功',
            'code': 412,
            "data": None,
        }
        article_query = Articles.objects.filter(nid=nid) # 检查有没有文章,如果有则取这篇文章
        if not article_query:
            res['msg'] = '请求错误'
            return JsonResponse(res)# 没有文章直接 return 
        data = request.data
        data['status'] = 1
        
        form = AddArticleForm(data)
        if not form.is_valid():
            res['self'], res['msg'] = clean_form(form)
            return JsonResponse(res)

        # 校验通过
        form.cleaned_data['author'] = 'wshsm'
        form.cleaned_data['source'] = 'yt'
        article_query.update(**form.cleaned_data)# 更新

        # 标签修改
        tags = data.get('tags')
        # 先清空所有的文章标签
        article_query.first().tag.clear() # first 查询结果集中取出第一个数据对象
        for tag in tags:
            if tag.isdigit():
                # 是数字
                article_query.first().tag.add(tag)
            else:
                # 先创建，再多对多关联
                tag_obj = Tags.objects.create(title=tag)
                article_query.first().tag.add(tag_obj.nid)

        res['code'] = 0
        res['data'] = article_query.first().nid
        return JsonResponse(res)

# 文章点赞
class ArticleDiggView(View):
    def post(self, request, nid):
        res = {
            'msg': '点赞成功',
            'code': 412,
            'data': 0,
        }


        comment_query = Articles.objects.filter(nid=nid)
        comment_query.update(digg_count=F('digg_count')+1)
        digg_count = comment_query.first().digg_count
        
        res['data'] = digg_count
        res['code'] = 0
        return JsonResponse(res)
    
# 文章收藏
class ArticleCollectsView(View):
    def post(self, request, nid):
        res = {
            'msg': '收藏成功',
            'code': 412,
            'data': 0,
            'isCollects': True, # 是否是收藏
        }
        # 一个用户只能收藏一次
        # 同样的请求 取反

        # 登录验证
        if not request.user.username:
            res['msg'] = '请先登录'
            return JsonResponse(res)
        
        
        
        # 判断是否已经收藏
        flag = request.user.collects.filter(nid=nid)
        num = 0
        if flag:
            # 用户已经收藏文章
            # 取消收藏
            res['msg'] = '取消收藏'
            res['isCollects'] = False
            request.user.collects.remove(nid)
            num = -1
            Articles.objects.filter(nid=nid).update(collects_count = F('collects_count') + num)
        else:
            res['msg'] = '收藏成功' # 默认
            res['isCollects'] = True # 默认
            request.user.collects.add(nid)
            num = 1
            Articles.objects.filter(nid=nid).update(collects_count = F('collects_count') + num)
        
        Article_query = Articles.objects.filter(nid=nid)
        Article_query.update(digg_count=F('collects_count') + num)
        digg_count = Article_query.first().collects_count
        res['data'] = digg_count
        
        res['code'] = 0
        return JsonResponse(res)



# # 文章
# class ArticleView(View):
#     # 发布文章
#     def post(self, request):
#         res = {
#             'msg': '文章发布成功',
#             'code': 412,
#             "data": None,
#         }

#         data: dict = request.data
        
#         title = data.get('title')
#         if not title:
#             res['msg']= '请输入文章标题'
#             return JsonResponse(res)
        
#         content = data.get('content')
#         if not content:
#             res['msg']= '请输入文章内容'
#             return JsonResponse(res)
        
#         recommend = data.get('recommend')
#         # 构造必须传参的字典
#         extra = {
#             'title': title,
#             'content': content,
#             'recommend': recommend,
#             'status': 1, # 保存状态
#         } 
#         # 解析文本内容        
#         abstract = data.get('abstract')
#         if not abstract:
#             abstract = PyQuery(markdown(content)).text()[:30]
#         extra['abstract'] = abstract

#         catgory = data.get('catgory_id')
#         if catgory:
#             extra['catgory'] = catgory

#         # 封面
#         cover_id = data.get('cover_id')
#         if cover_id:
#             extra['cover_id'] = cover_id
#         else:
#             extra['cover_id'] = 1

#         pwd = data.get('pwd')
#         if pwd:
#             extra['pwd'] = pwd

#         # 添加文章
#         article_obj = Articles.objects.create(**extra)
#         # 添加标签
#         tags = data.get('tags')
#         if tags:
#             for tag in tags:
#                 if not tag.isdigit():
#                     tag_obj = Tags.objects.create(title=tag)
#                     article_obj.tag.add(tag_obj)
#                 else:
#                     article_obj.tag.add(tag)

#         res['code'] = 0
#         res['data'] = article_obj.nid
#         return JsonResponse(res)