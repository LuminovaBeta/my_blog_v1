from django.views import View
from django.http import JsonResponse
from django import forms
from api.views.login import clean_form
from app01.models import Comment, Articles
from django.db.models import F# 查询
from api.utils.find_root_comment import find_root_comment
from app01.utils.sub_comment import find_root_sub_comment # 找所有的子评论

class CommentView(View):
    # 发布评论
    def post(self, request, nid):
        # /api/article/2/comment/
        # 文章id
        # 用户
        # 评论的内容
        res = {
            'msg': '文章评论成功',
            'code': 412,
            'self': None,
        }
        data = request.data
        if not request.user.username:
            res['msg'] = '请先登录'
            return JsonResponse(res)
        content = data.get('content')
        if not content:
            res['msg'] = '请输入内容！'
            return JsonResponse(res)
        
        # 文章评论校验成功, 添加一次用户评论
        # Parent ID（父级 ID 或 父评论 ID）
        # 没有 pid (None)：代表这是一条根评论（直接评论文章的）。
        pid = data.get('pid')
        # 文章评论数加1
        Articles.objects.filter(nid=nid).update(comment_count = F('comment_count')+1)
        if pid:
            comment_obj = Comment.objects.create(
                content=content,
                user=request.user,
                article_id=nid,
                parent_comment_id=pid,
            )
            # 根评论的子评论数加一
            # 找最终的根评论
            root_comment_obj = find_root_comment(comment_obj)
            root_comment_obj.comment_count += 1
            root_comment_obj.save()
            # Comment.objects.filter(nid=pid).update(comment_count=F('comment_count')+1)
        else:
            
            Comment.objects.create(
                content=content,
                user=request.user,
                article_id=nid,
            )
         
        res['code'] = 0
        return JsonResponse(res)

    # 删除评论, nid评论ID(Comment ID)
    def delete(self, request, nid):
        # 自己发布的评论、超级管理员才能删除
        res = {
            'msg': '评论删除成功',
            'code': 412,
        }
        # print(nid)
        # 登录人
        login_user = request.user
        comment_query = Comment.objects.filter(nid=nid)
        # 评论人
        comment_user = comment_query.first().user

        # aid文章ID(Article ID)
        aid = request.data.get('aid')
        
        # 根评论id
        pid = request.data.get('pid')

        # 用户验证失败
        if not (login_user == comment_user or login_user.is_superuser):
            res['msg'] = '用户验证失败'
            return JsonResponse(res)

        # 算子评论的数量
        lis = []
        find_root_sub_comment(comment_query.first(), lis)

        # 文章评论数量计算
        Articles.objects.filter(nid=aid).update(comment_count = F('comment_count') - len(lis) - 1)

        if not pid:
            # 如果删除的是根评论
            
            pass
        else:
            # 如果删除的是子评论
            # 找最终的根评论
            Comment.objects.filter(nid=pid).update(comment_count = F('comment_count') - len(lis) - 1)
        # 删除
        comment_query.delete()
        res['code'] = 0
        return JsonResponse(res) # 成功后返回
        
class Comment_DiggView(View):
    # nid 评论id
    def post(self, request, nid):
        res = {
            'msg': '点赞成功',
            'code': 412,
            'data': 0,
        }
        # 登录验证
        if not request.user.username:
            res['msg'] = '请先登录'
            return JsonResponse(res)
        
        
        comment_query = Comment.objects.filter(nid=nid)
        comment_query.update(digg_count=F('digg_count')+1)
        digg_count = comment_query.first().digg_count
        
        res['data'] = digg_count
        res['code'] = 0
        return JsonResponse(res)
