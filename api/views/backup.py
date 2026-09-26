from django.http import FileResponse, JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST

from app01.models import Articles
from app01.utils.article_backup import ExportTooLarge, build_article_backup


@require_POST
def export_articles(request):
    if not request.user.is_authenticated:
        return JsonResponse({'msg': '请先登录'}, status=401)
    if not request.user.is_superuser:
        return JsonResponse({'msg': '没有文章管理权限'}, status=403)

    articles = Articles.objects.select_related('cover').prefetch_related('tag').order_by('nid')
    scope = request.POST.get('scope')
    if scope == 'selected':
        raw_ids = [value for field in request.POST.getlist('article_ids') for value in field.split(',')]
        if not raw_ids or len(raw_ids) > 1000:
            return JsonResponse({'msg': '请选择 1 至 1000 篇文章'}, status=400)
        try:
            ids = {int(value) for value in raw_ids}
            if any(value < 1 or value > 2147483647 for value in ids):
                raise ValueError
        except ValueError:
            return JsonResponse({'msg': '文章编号不合法'}, status=400)
        articles = articles.filter(nid__in=ids)
        if articles.count() != len(ids):
            return JsonResponse({'msg': '部分文章已不存在，请刷新后重新选择'}, status=404)
    elif scope != 'all':
        return JsonResponse({'msg': '请选择导出范围'}, status=400)

    count = articles.count()
    if count == 0:
        return JsonResponse({'msg': '暂无可导出的文章'}, status=400)
    if count > 1000:
        return JsonResponse({'msg': '每次最多导出 1000 篇文章，请分批选择'}, status=400)
    try:
        package = build_article_backup(articles, request.build_absolute_uri('/'))
    except ExportTooLarge as exc:
        return JsonResponse({'msg': str(exc)}, status=413)

    filename = f'article_backup_{timezone.localtime():%Y%m%d_%H%M%S}.zip'
    response = FileResponse(package, as_attachment=True, filename=filename, content_type='application/zip')
    response['Cache-Control'] = 'no-store, private'
    return response
