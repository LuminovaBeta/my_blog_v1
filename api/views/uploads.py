import os
import uuid
import datetime
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.clickjacking import xframe_options_exempt

@csrf_exempt
@xframe_options_exempt
def upload_image(request):
    if request.method == 'POST':
        res={
             'success': 0, # 0表示失败，1表示成功
             'message': "上传失败",
             'url': ""
        }
        # 获取上传的文件 (注意这个 key 是 editor.md 固定的)
        img_file = request.FILES.get('editormd-image-file')
        if not img_file:
            res['message'] = "未获取到图片"
            return JsonResponse(res)
        
        # root: 文件名, ext: 文件后缀
        root, ext = os.path.splitext(img_file.name)
        # 【安全清洗】把文件名里的空格替换成下划线，防止 Linux 路径报错
        safe_root = root.replace(' ', '_')
        now = datetime.datetime.now()
        image_name = f"{now.strftime('%Y%m%d_%H%M%S')}_{safe_root}{ext}"

        relative_path = os.path.join('uploads', 'articles_image', now.strftime('%Y%m'))
        abs_image_path = os.path.join(settings.MEDIA_ROOT, relative_path)

        if not os.path.exists(abs_image_path):
            os.makedirs(abs_image_path)

        file_path = os.path.join(abs_image_path, image_name)
        with open(file_path, 'wb+') as f:
            for chunk in img_file.chunks():
                f.write(chunk)

        url_path = os.path.join(settings.MEDIA_URL, relative_path, image_name)
        # 强制替换反斜杠为正斜杠 (兼容 Windows 开发环境)
        url_path = url_path.replace('\\', '/')


        # 测试
        # print(img_file, root, ext, safe_root, image_name)
        # print('上传文件名字:' + root + ext)
        # print('文件保存名称:' + image_name)
        # print('相对路径:' + relative_path)
        # print('绝对路径:' + abs_image_path)
        # print('返回路径:' + url_path)

        res['success'] = 1
        res['message'] = "上传成功"
        res['url'] = url_path
        return JsonResponse(res)
