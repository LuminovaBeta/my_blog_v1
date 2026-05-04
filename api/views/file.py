from django.http import JsonResponse
from django.views import View

from app01.models import Avatars, Cover, UserInfo
from app01.models import avatar_delete, cover_delete

from django.db.models import Q # 引入Q对象，专门用来处理复杂的数据库查询条件的
from django.core.files.uploadedfile import InMemoryUploadedFile # 完全保存在服务器内存（RAM）中的上传文件
from django.core.handlers.wsgi import WSGIRequest

# 头像
class AvatarView(View):
    # @is_super_method
    def post(self, request: WSGIRequest):
        res = {
            "code": 345,
            'msg': '文件上传不合法！'
        }
        if not request.user.is_superuser:
            res['msg'] = '用户验证失败'
            return JsonResponse(res)
        file: InMemoryUploadedFile = request.FILES.get('file')
        name: str = file.name
        # 使用白名单的方式，如果不在白名单就是不合法的文件
        white_file_type = [
            'jpg', 'jpeg', 'png', 'webp'
        ]
        if name.split('.')[-1] not in white_file_type:
            res['msg'] = '文件上传类型不合法！'
            return JsonResponse(res)

        kb = file.size / 1024
        mb = kb / 1024
        if mb > 2:
            res['msg'] = '图片大小超过2MB'
            return JsonResponse(res)
        
        
        Avatars.objects.create(url=file) # 保存文件和数据库路径记录

        res['code'] = 0
        res['msg'] = 'success'
        return JsonResponse(res)
    
    def delete(self, request, nid):
        res = {
            'code': 322,
            'msg': '图片删除成功！'
        }

        # 用户超级管理员权限验证
        if not request.user.is_superuser:
            res['msg'] = '用户验证失败'
            return JsonResponse(res)
        
        avatar_query = Avatars.objects.filter(nid=nid)
        if not avatar_query:
            res['msg'] = '图片已被删除！'
            return JsonResponse(res)
        
        # 判断图片是不是有人在使用
        obj: Avatars = avatar_query.first()

        user_query = UserInfo.objects.filter(Q(sign_status=1) | Q(sign_status=2))
        for user in user_query:
            if obj.url.url == user.avatar_url:
                res['msg'] = '该图片有人使用！'
                return JsonResponse(res)

        # 删除操作
        avatar_delete(obj) # 删除硬盘上的物理文件
        avatar_query.delete() # 删除数据库里的记录

        res['code'] = 0
        return JsonResponse(res)
    
# 文章封面
# 封面
class CoverView(View):
    # @is_super_method
    def post(self, request: WSGIRequest):
        res = {
            "code": 345,
            'msg': '文件上传不合法！'
        }
        if not request.user.is_superuser:
            res['msg'] = '用户验证失败'
            return JsonResponse(res)
        file: InMemoryUploadedFile = request.FILES.get('file')
        name: str = file.name
        white_file_type = [
            'jpg', 'jpeg', 'png', 'webp',
        ]
        if name.split('.')[-1] not in white_file_type:
            return JsonResponse(res)

        kb = file.size / 1024 / 1024
        if kb > 2:
            res['msg'] = '图片大小超过2MB'
            return JsonResponse(res)
        Cover.objects.create(url=file)
        res['code'] = 0
        res['msg'] = 'success'
        return JsonResponse(res)

    # @is_super_method
    def delete(self, request, nid):

        res = {
            'code': 322,
            'msg': '图片删除成功！'
        }
        if not request.user.is_superuser:
            res['msg'] = '用户验证失败'
            return JsonResponse(res)
        cover_query = Cover.objects.filter(nid=nid)
        if not cover_query:
            res['msg'] = '图片已被删除！'
            return JsonResponse(res)
        cover_delete(cover_query.first())
        cover_query.delete()

        res['code'] = 0
        return JsonResponse(res)

