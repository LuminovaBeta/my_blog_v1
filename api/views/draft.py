from django.db import transaction
from django.contrib.auth.hashers import make_password
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views import View

from app01.models import ArticleDraft, Articles, Cover, Tags


def draft_data(draft):
    """返回编辑器恢复草稿所需的数据。"""
    return {
        'nid': draft.nid,
        'article_id': draft.article_id,
        'title': draft.title,
        'abstract': draft.abstract,
        'content': draft.content,
        'category': str(draft.category) if draft.category is not None else '',
        'cover_id': str(draft.cover_id) if draft.cover_id else '',
        'cover_url': draft.cover.url.url if draft.cover_id else '',
        'tags': [str(tag.nid) for tag in draft.tags.all()],
        'has_password': bool(draft.pwd) or bool(draft.article and draft.article.pwd),
        'has_saved_draft_password': draft.password_action == 'set' and bool(draft.pwd),
        'password_action': draft.password_action,
        'recommend': draft.recommend,
        'version': draft.version,
        'updated_at': draft.updated_at.isoformat(),
    }


class ArticleDraftView(View):
    """创建、读取和更新当前管理员自己的文章草稿。"""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse(
                {'code': 401, 'msg': '请先登录', 'data': None},
                status=401,
            )
        if not request.user.is_superuser:
            return JsonResponse(
                {'code': 403, 'msg': '没有文章管理权限', 'data': None},
                status=403,
            )
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, nid):
        draft = get_object_or_404(
            ArticleDraft.objects.prefetch_related('tags'),
            nid=nid,
            owner=request.user,
        )
        return JsonResponse({'code': 0, 'msg': '草稿读取成功', 'data': draft_data(draft)})

    def delete(self, request, nid):
        draft = get_object_or_404(ArticleDraft, nid=nid, owner=request.user)
        draft.delete()
        return JsonResponse({'code': 0, 'msg': '草稿已删除', 'data': None})

    @transaction.atomic
    def post(self, request, nid=None):
        data = getattr(request, 'data', None)
        if not isinstance(data, dict):
            return JsonResponse(
                {'code': 400, 'msg': '请求数据格式错误', 'data': None},
                status=400,
            )

        article = None
        article_id = data.get('article_id')
        if article_id not in (None, ''):
            article = get_object_or_404(Articles, nid=article_id)

        if nid is not None:
            draft = get_object_or_404(ArticleDraft, nid=nid, owner=request.user)
            if article and draft.article_id not in (None, article.nid):
                return JsonResponse(
                    {'code': 400, 'msg': '草稿与文章不匹配', 'data': None},
                    status=400,
                )
        elif article:
            draft, _ = ArticleDraft.objects.get_or_create(
                article=article,
                defaults={'owner': request.user},
            )
            if draft.owner_id != request.user.pk:
                return JsonResponse(
                    {'code': 403, 'msg': '该文章已有其他用户的草稿', 'data': None},
                    status=403,
                )
        else:
            draft = ArticleDraft(owner=request.user)

        client_version = data.get('version')
        if draft.pk and client_version not in (None, ''):
            try:
                client_version = int(client_version)
            except (TypeError, ValueError):
                return JsonResponse(
                    {'code': 400, 'msg': '草稿版本格式错误', 'data': None},
                    status=400,
                )
            if client_version != draft.version:
                return JsonResponse(
                    {
                        'code': 409,
                        'msg': '草稿已在其他页面更新，请刷新后重试',
                        'data': draft_data(draft),
                    },
                    status=409,
                )

        title = str(data.get('title') or '')
        abstract = str(data.get('abstract') or '')
        content = str(data.get('content') or '')
        password_action = str(data.get('password_action') or 'keep')
        new_password = str(data.get('new_password') or '')
        if len(title) > 32:
            return JsonResponse({'code': 400, 'msg': '文章标题不能超过32字', 'data': None}, status=400)
        if len(abstract) > 150:
            return JsonResponse({'code': 400, 'msg': '文章简介不能超过150字', 'data': None}, status=400)
        if password_action not in dict(ArticleDraft.password_action_choice):
            return JsonResponse({'code': 400, 'msg': '密码操作类型错误', 'data': None}, status=400)
        if new_password and not 4 <= len(new_password) <= 32:
            return JsonResponse({'code': 400, 'msg': '文章密码长度应为4至32位', 'data': None}, status=400)
        if password_action == 'set' and not new_password:
            has_saved_password = bool(draft.pk and draft.password_action == 'set' and draft.pwd)
            if not has_saved_password:
                return JsonResponse({'code': 400, 'msg': '请输入新的文章密码', 'data': None}, status=400)

        category = data.get('category')
        if category in (None, ''):
            category = None
        else:
            try:
                category = int(category)
            except (TypeError, ValueError):
                return JsonResponse({'code': 400, 'msg': '文章分类格式错误', 'data': None}, status=400)
            if category not in dict(Articles.category_choice):
                return JsonResponse({'code': 400, 'msg': '文章分类不存在', 'data': None}, status=400)

        cover = None
        cover_id = data.get('cover_id')
        if cover_id not in (None, ''):
            cover = get_object_or_404(Cover, nid=cover_id)

        raw_tags = data.get('tags') or []
        if not isinstance(raw_tags, (list, tuple)):
            return JsonResponse({'code': 400, 'msg': '文章标签格式错误', 'data': None}, status=400)
        normalized_tags = []
        seen_tags = set()
        for raw_tag in raw_tags:
            tag_value = str(raw_tag).strip()
            if not tag_value or tag_value in seen_tags:
                continue
            if not tag_value.isdigit() and len(tag_value) > 16:
                return JsonResponse(
                    {'code': 400, 'msg': f'标签“{tag_value}”不能超过16字', 'data': None},
                    status=400,
                )
            seen_tags.add(tag_value)
            normalized_tags.append(tag_value)

        draft.article = article or draft.article
        draft.title = title
        draft.abstract = abstract
        draft.content = content
        draft.category = category
        draft.cover = cover
        if password_action == 'set' and new_password:
            draft.pwd = make_password(new_password)
        elif password_action != 'set':
            draft.pwd = ''
        draft.password_action = password_action
        draft.recommend = bool(data.get('recommend', False))
        if draft.pk:
            draft.version += 1
        draft.save()

        tag_objects = []
        for tag_value in normalized_tags:
            if tag_value.isdigit():
                tag = Tags.objects.filter(nid=int(tag_value)).first()
                if tag:
                    tag_objects.append(tag)
                continue
            tag = Tags.objects.filter(title=tag_value).first()
            if not tag:
                tag = Tags.objects.create(title=tag_value)
            tag_objects.append(tag)
        draft.tags.set(tag_objects)

        return JsonResponse(
            {'code': 0, 'msg': '草稿已暂存', 'data': draft_data(draft)},
            status=201 if client_version in (None, '') and draft.version == 1 else 200,
        )
