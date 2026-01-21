from django.utils.deprecation import MiddlewareMixin
import json
#
# 解析POST请求的数据
class Md1(MiddlewareMixin):
    # 请求中间件
    def process_request(self, request):
        # 只处理json数据，不对admin登录时发送的form格式的内容进行处理
        if request.method != 'GET' and request.META.get('CONTENT_TYPE') == 'application/json':
            # print(request.META.get('CONTENT_TYPE')) # 可以尝试输出表头信息
            data = json.loads(request.body)
            request.data = data

    # 响应中间件
    def process_response(self, request, response):
        return response
