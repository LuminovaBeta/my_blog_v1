import time
from django.views import View
from django.http import JsonResponse
from api.views.login import clean_form
from django.db.models import F
from django import forms
from django.contrib import auth
from app01.models import Avatars

# 修改密码的字段验证
class EditPasswordForm(forms.Form):
    old_pwd = forms.CharField(error_messages={'required': '请输入原密码'})
    new_pwd = forms.CharField(min_length=4, error_messages={'required': '请输入新密码', 'min_length': '长度不小于4位'})
    re_new_pwd = forms.CharField(min_length=4, error_messages={'required': '请再次输入新密码', 'min_length': '长度不小于4位'})

    # 重写init方法
    def __init__(self, *args, **kwargs):
        # 做自己想做的事情
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

    def clean_old_pwd(self):
        old_pwd = self.cleaned_data['old_pwd']
        user = auth.authenticate(username=self.request.user.username, password=old_pwd)
        if not user:
            self.add_error('old_pwd', '原密码输入错误！')
        return old_pwd

    def clean(self):
        new_pwd = self.cleaned_data.get('new_pwd')
        re_new_pwd = self.cleaned_data.get('re_new_pwd')
        if new_pwd != re_new_pwd:
            self.add_error('re_new_pwd', '两次密码不一致')
        return self.cleaned_data

# 修改密码
class EditPasswordView(View):
    def post(self, request):
        res = {
            "msg": '密码修改成功！',
            'self': None,
            'code': 414,
        }
        data = request.data
        form = EditPasswordForm(data, request=request)

        # 验证不通过
        if not form.is_valid():
            res['self'], res['msg'] = clean_form(form)
            return JsonResponse(res)
        
        user = request.user
        user.set_password(data['new_pwd'])
        user.save()

        auth.logout(request)  # 退出登录

        res['msg'] = '密码修改成功, 请重新登录! '
        res['code'] = 0
        return JsonResponse(res)

# 修改头像
class EditAvatarView(View):
    def put(self, request):
        res = {
            'msg': '头像修改成功',
            'code': 414,
        }
        avatar_id = request.data.get('avatar_id')

        # 判断用户的登录状态
        user = request.user
        sign_status = user.sign_status
        avatar = Avatars.objects.get(nid=avatar_id)

        if sign_status == 0:
            # 用户名+密码 注册
            user.avatar_id = avatar_id
        else:
            # 其他方式注册
            avatar_url = avatar.url.url
            user.avatar_url = avatar_url
        user.save()

        res['data'] = avatar.url.url
        res['code'] = 0
        return JsonResponse(res)


# 信息绑定的字段验证
class EditUserInfoForm(forms.Form):
    email = forms.EmailField(error_messages={'required': '请输入邮箱', "invalid": '请输入正确的邮箱'})
    pwd = forms.CharField(error_messages={'required': '请输入密码'})
    code = forms.CharField(error_messages={'required': '请输入验证码'})

    # 重写init方法
    def __init__(self, *args, **kwargs):
        # 做自己想做的事情
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        # 判断是否和self里面的邮箱相同
        if email == self.request.session.get('valid_email_obj')['email']:
            return email
        self.add_error('email', '邮箱二次校验错误！')

    def clean_pwd(self):
        pwd = self.cleaned_data['pwd']
        user = auth.authenticate(username=self.request.user.username, password=pwd)
        if user:
            return pwd
        self.add_error('pwd', '密码错误！')

    def clean_code(self):
        code = self.cleaned_data['code']
        if code == self.request.session.get('valid_email_obj')['code']:
            return code
        self.add_error('code', '验证码错误')

# 信息绑定
class EditUserInfoView(View):
    def put(self, request):
        res = {
            'code': 332,
            'msg': '信息绑定成功！',
            "self": None,
        }

        # 先校验时间
        valid_email_obj = request.session.get('valid_email_obj')
        if not valid_email_obj:
            res['msg'] = '请先获取验证码！'
            return JsonResponse(res)

        time_stamp = valid_email_obj['time_stamp']
        now = time.time()
        if (now - time_stamp) > 300:  # 5分钟
            res['msg'] = "验证码超时，请重新获取！"
            return JsonResponse(res)

        form = EditUserInfoForm(request.data, request=request) # form 表单字段验证
        if not form.is_valid():
            res['self'], res['msg'] = clean_form(form)
            return JsonResponse(res)

        # 绑定信息
        user = request.user

        user.email = form.cleaned_data['email']
        user.save()

        res['code'] = 0
        return JsonResponse(res)