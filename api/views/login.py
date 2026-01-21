from django import forms
from django.contrib import auth
from app01.models import UserInfo # 导入用户表
from app01.models import Avatars # 导入头像
from django.views import View
from django.http import JsonResponse
import random

# CBV class
# FBV function
# 父类，让后代继承
class loginBaseForm(forms.Form):
    # 重写init方法
    def __init__(self, *args, **kwargs):
        # 做自己想做的事情
        self.request = kwargs.pop('request', None)# 弹出：拿出request，并且删掉
        super().__init__(*args, **kwargs)

    # 局部钩子 - 验证码判断
    def clean_code(self):
        code = self.cleaned_data.get('code')
        valid_code = self.request.session.get('valid_code')
        print(code, valid_code)

        if code.upper() != valid_code.upper():
            self.add_error('code', "验证码输入错误")
        
        return self.cleaned_data


# 登录的字段验证
class LoginForm(loginBaseForm):
    name = forms.CharField(error_messages={'required': '请输入用户名'})
    pwd = forms.CharField(error_messages={'required': '请输入密码'})
    code = forms.CharField(error_messages={'required': '请输入验证码'})

    # 全局钩子
    def clean(self):
        name = self.cleaned_data.get('name')
        pwd = self.cleaned_data.get('pwd')
        # print(name, pwd)

        # 如果校验通过，就能拿到用户对象
        user = auth.authenticate(username=name, password=pwd)
        print(user)
        # 校验不通过
        if not user:
            self.add_error('pwd', "用户名或密码错误")       # 知识点  self.add_error 为字段添加信息
            return self.cleaned_data

        # 把用户对象放到cleaned_data中
        self.cleaned_data['user'] = user
        return self.cleaned_data
    
# 注册的字段验证
class SignForm(loginBaseForm):
    name = forms.CharField(error_messages={'required': '请输入用户名'})
    pwd = forms.CharField(error_messages={'required': '请输入密码'})
    re_pwd = forms.CharField(error_messages={'required': '请输入确认密码'})
    code = forms.CharField(error_messages={'required': '请输入验证码'})

    # 局部钩子，name不能重复
    def clean_name(self):
        name = self.cleaned_data.get('name')
        user_query = UserInfo.objects.filter(username=name)
        if user_query:
            self.add_error('name', "该用户已注册")
        
        return self.cleaned_data

    # 全局钩子，校验两次密码是否一致
    def clean(self):
        pwd = self.cleaned_data.get('pwd')
        re_pwd = self.cleaned_data.get('re_pwd')
        if pwd != re_pwd:
            self.add_error('re_pwd', "两次密码不一致")
        return self.cleaned_data

# 登录失败的可复用代码
def clean_form(form):
    err_dict:dict = form.errors
    # 拿到所有错误的字段名字
    err_valid = list(err_dict.keys())[0]
    # 拿到第一个字段的第一个错误信息
    err_msg = err_dict[err_valid][0]
    return err_valid,err_msg


# CBV 模式定义

class LoginView(View):
    def post(self, request):
        res = {
            'code': 1,# 状态吗
            'msg': "登录成功",
            'self': None
        }

        data = request.data

        form = LoginForm(data, request=request)

        # 验证不通过
        if not form.is_valid():
            res['self'], res['msg'] = clean_form(form)
            return JsonResponse(res)
            

        # 已经被优化的代码
        # valid_code = request.session.get('valid_code')
        # if valid_code.upper() != data.get('code').upper():
        #     print('验证码输入错误')
        #     res['msg'] = "验证码输入错误"
        #     res['self'] = 'code'
        #     return JsonResponse(res)
            
        # if name != 'wshsm' or pwd != '123789':
        #     res['msg'] = "用户名或密码输入错误"
        #     res['self'] = 'pwd'
        #     return JsonResponse(res)

        # 执行登录操作
        user = form.cleaned_data.get('user')
        auth.login(request, user)
        res['msg'] = "登录成功"
        res['code'] = 0

        return JsonResponse(res)

class SignView(View):
    def post(self, request):
        if request.method == 'POST':
            res = {
                'code': 1,# 状态吗
                'msg': "注册成功，三秒后返回登录页",
                'self': None
            }
            data = request.data
            form = SignForm(data, request=request)

            # 验证不通过
            if not form.is_valid():
                res['self'], res['msg'] = clean_form(form)
                return JsonResponse(res)
            
            # --- 注册成功代码 --- #
            user = UserInfo.objects.create_user(
                username=form.request.data.get('name'), 
                password=form.request.data.get('pwd')
            )

            # 随机头像
            avatar_list = [i.nid for i in Avatars.objects.all()]
            user.avatar_id = random.choice(avatar_list)
            user.save() # 保存

            # auth.login(request, user) # 注册成功后直接登录
            res['code'] = 0

            return JsonResponse(res)
