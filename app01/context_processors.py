from django.conf import settings

# 自定义配置cdn或者本地静态文件

def js_libs(request):
    if getattr(settings, 'USE_CDN', False):
        return {'libs': settings.CDN_LINKS}
    return {'libs': settings.LOCAL_LINKS}