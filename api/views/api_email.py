# 发送邮箱部分

import random
import time
from threading import Thread

from django import forms
# from django.conf import settings
from my_blog import settings
from django.core.handlers.wsgi import WSGIRequest
from django.core.mail import send_mail
from django.http import JsonResponse
from django.views import View

# from api.models import Email
from api.views.login import clean_form
from app01.models import UserInfo

# 钩子，
class EmailForm(forms.Form):
    # 自动进行为空校验，包括校验错误信息
    email = forms.EmailField(error_messages={'required': '请输入邮箱', "invalid": '请输入正确的邮箱'})

    # 邮箱校验，防止重复绑定
    def clean_email(self):
        email = self.cleaned_data['email']
        user = UserInfo.objects.filter(email=email)
        if user:
            self.add_error('email', '该邮箱已被人注册！')
        return email


class ApiEmail(View):
    def post(self, request: WSGIRequest):
        # TODO: 状态码肯定是要重新设计的，让开发人员一看码就知道对应的错误信息
        res = {
            'code': 333,
            "msg": '验证码获取成功！',
            "self": None
        }
        form = EmailForm(request.data) # 校验email，钩子
        if not form.is_valid():
            res['self'], res['msg'] = clean_form(form)
            return JsonResponse(res)

        # 发送邮箱  设置超时时间 60s
        # 去 session 里面读取
        valid_email_obj = request.session.get('valid_email_obj')
        if valid_email_obj:
            time_stamp = valid_email_obj['time_stamp']
            now_stamp = time.time()
            # 时间戳
            if (now_stamp - time_stamp) < 60:
                res['msg'] = '请求过于频繁'
                return JsonResponse(res)

        valid_email_code = ''.join(random.sample('0123456789', 6)) # 随机选择6位，并进行拼接
        # 在服务器的缓存中暂存 code: 验证码, time_stamp: 时间戳
        request.session["valid_email_obj"] = {
            'code': valid_email_code,
            'email': form.cleaned_data['email'],
            'time_stamp': time.time(),
        }

        # 多线程异步发送邮件
        Thread(target=send_mail,
               args=('【Yt博客网站】请完善你的信息!',
                     f'【Yt博客网站】你现在正在绑定邮箱, 邮箱验证码为 {valid_email_code}, 验证码有效期为5分钟。',
                     settings.EMAIL_HOST_USER,
                     [form.cleaned_data.get('email')],
                     False)).start()
        # Email.objects.create(
        #     email=form.cleaned_data.get('email'),
        #     content='完善信息'
        # )
        res['code'] = 0
        return JsonResponse(res)
