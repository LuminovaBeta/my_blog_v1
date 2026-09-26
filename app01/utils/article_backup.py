"""Portable article exports. Only read uploaded images beneath MEDIA_ROOT."""

import hashlib
import html
import json
import re
from pathlib import Path
from tempfile import SpooledTemporaryFile
from urllib.parse import unquote, urlsplit
from zipfile import ZIP_DEFLATED, ZipFile

from django.conf import settings
from django.utils import timezone


MAX_EXPORT_BYTES = 512 * 1024 * 1024
MAX_IMAGE_BYTES = 25 * 1024 * 1024
IMAGE_SUFFIXES = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp', '.ico', '.avif'}
# Preserve fenced/indented code and inline code examples verbatim.
CODE = re.compile(
    r'^ {0,3}(?P<fence>`{3,}|~{3,})[^\n]*\n.*?^ {0,3}(?P=fence)[ \t]*(?:\n|$)'
    r'|^(?:(?: {4}|\t)[^\n]*(?:\n|$))+'
    r'|(?P<ticks>`+)(?!`).*?(?<!`)(?P=ticks)(?!`)',
    re.MULTILINE | re.DOTALL,
)
INLINE_IMAGE = re.compile(
    r'!\[(?:\\.|[^\]\\])*\]\(\s*'
    r'(?P<url><[^>\n]+>|(?:\\.|[^\s()\\]|\([^()\n]*\))+)'
    r'(?:\s+(?:"[^"\n]*"|\x27[^\x27\n]*\x27|\([^()\n]*\)))?\s*\)'
)
IMAGE_REF = re.compile(r'!\[([^\]\n]+)\](?:[ \t]*\[([^\]\n]*)\])?')
REF_DEF = re.compile(r'^ {0,3}\[([^\]\n]+)\]:[ \t]*(?P<url><[^>\n]+>|\S+)', re.MULTILINE)
HTML_IMAGE = re.compile(r'<img\b[^>]*>', re.IGNORECASE)
HTML_SRC = re.compile(r'(?<![\w-])src\s*=\s*(?:"(?P<double>[^"]*)"|\x27(?P<single>[^\x27]*)\x27|(?P<bare>[^\s>]+))', re.IGNORECASE)


class ExportTooLarge(ValueError):
    pass


def safe_title(title):
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', title or '未命名文章')
    return name.strip(' .')[:60] or '未命名文章'


def rewrite_images(content, replace):
    """Rewrite inline/reference Markdown images and HTML img src, not code."""
    protected = list(CODE.finditer(content))

    def outside_code(start, end):
        return not any(start < block.end() and end > block.start() for block in protected)

    references = {
        ' '.join((match.group(2) or match.group(1)).split()).casefold()
        for match in IMAGE_REF.finditer(content)
        if outside_code(match.start(), match.end())
    }
    edits = []

    def add_url(match, group='url', offset=0):
        start, end = match.span(group)
        original = match.group(group)
        wrapped = original.startswith('<') and original.endswith('>')
        url = original[1:-1] if wrapped else original
        changed = replace(html.unescape(re.sub(r'\\([() ])', r'\1', url)))
        if changed != html.unescape(re.sub(r'\\([() ])', r'\1', url)):
            edits.append((offset + start, offset + end, f'<{changed}>' if wrapped else changed))

    for match in INLINE_IMAGE.finditer(content):
        if outside_code(match.start(), match.end()):
            add_url(match)
    for match in REF_DEF.finditer(content):
        if ' '.join(match.group(1).split()).casefold() in references and outside_code(match.start(), match.end()):
            add_url(match)
    for tag in HTML_IMAGE.finditer(content):
        if outside_code(tag.start(), tag.end()):
            src = HTML_SRC.search(tag.group())
            if src:
                group = next(key for key in ('double', 'single', 'bare') if src.group(key) is not None)
                add_url(src, group, tag.start())
    for start, end, replacement in sorted(edits, reverse=True):
        content = content[:start] + replacement + content[end:]
    return content


def build_article_backup(articles, origin):
    """Return a seeked temporary ZIP; the FileResponse owns/cleans it up."""
    output = SpooledTemporaryFile(max_size=8 * 1024 * 1024, mode='w+b')
    now = timezone.now().isoformat()
    total_bytes = 0
    media_root = Path(settings.MEDIA_ROOT).resolve()
    media_url = urlsplit(settings.MEDIA_URL)
    media_prefix = '/' + media_url.path.strip('/') + '/'
    allowed_hosts = {urlsplit(origin).netloc.casefold()}
    if media_url.netloc:
        allowed_hosts.add(media_url.netloc.casefold())
    manifest = {'schema_version': 1, 'exported_at': now, 'articles': []}

    def reserve(size):
        nonlocal total_bytes
        total_bytes += size
        if total_bytes > MAX_EXPORT_BYTES:
            raise ExportTooLarge('所选内容超过 512 MB，请分批导出。')

    try:
        with ZipFile(output, 'w', compression=ZIP_DEFLATED, allowZip64=True) as archive:
            def write_text(name, value):
                data = value.encode('utf-8')
                reserve(len(data))
                archive.writestr(name, data)

            for article in articles:
                folder = f'articles/{article.pk}_{safe_title(article.title)}'
                warnings = []
                assets = []
                copied = {}

                def warn(url, reason):
                    item = {'url': url, 'reason': reason}
                    if item not in warnings:
                        warnings.append(item)
                    return url

                def copy_image(url):
                    try:
                        parsed = urlsplit(url)
                        if parsed.scheme == 'data':
                            return url  # Embedded images are already self-contained.
                        if parsed.scheme not in ('', 'http', 'https'):
                            return warn(url, '不支持的图片地址，已保留原链接')
                        if parsed.netloc and parsed.netloc.casefold() not in allowed_hosts:
                            return warn(url, '外链图片未下载，需要联网查看')
                        path = unquote(parsed.path)
                        if not path.startswith('/'):
                            path = '/' + path
                        if not path.startswith(media_prefix):
                            return warn(url, '不在上传目录中，未打包')
                        relative = path[len(media_prefix):]
                        if '\\' in relative or '\x00' in relative or '..' in relative.split('/') or ':' in relative:
                            return warn(url, '图片路径不合法，未打包')
                        source = (media_root / relative).resolve()
                        if not source.is_relative_to(media_root):
                            return warn(url, '图片路径超出上传目录，未打包')
                        if source.suffix.lower() not in IMAGE_SUFFIXES:
                            return warn(url, '不是支持的图片文件，未打包')
                        if source in copied:
                            target = copied[source]
                            assets.append({'original_url': url, 'path': target})
                            return target
                        with source.open('rb') as image:
                            data = image.read(MAX_IMAGE_BYTES + 1)
                        if len(data) > MAX_IMAGE_BYTES:
                            return warn(url, '单张图片超过 25 MB，未打包')
                        reserve(len(data))
                        digest = hashlib.sha256(relative.encode('utf-8')).hexdigest()[:20]
                        target = f'images/{digest}{source.suffix.lower()}'
                        archive.writestr(f'{folder}/{target}', data)
                        copied[source] = target
                        assets.append({'original_url': url, 'path': target})
                        return target
                    except (OSError, ValueError) as exc:
                        if isinstance(exc, ExportTooLarge):
                            raise
                        return warn(url, '图片不存在或无法读取，已保留原链接')

                content = rewrite_images(article.content or '', copy_image)
                cover_url = article.cover.url.url if article.cover_id and article.cover.url else ''
                cover_path = copy_image(cover_url) if cover_url else ''
                metadata = {
                    'schema_version': 1,
                    'id': article.pk,
                    'title': article.title or '',
                    'abstract': article.abstract or '',
                    'category': article.category,
                    'category_name': article.get_category_display(),
                    'tags': [{'id': tag.pk, 'name': tag.title} for tag in article.tag.all()],
                    'author': article.author or '',
                    'source': article.source or '',
                    'link': article.link or '',
                    'status': article.status,
                    'recommend': article.recommend,
                    'word': article.word,
                    'created_at': article.create_date.isoformat() if article.create_date else None,
                    'updated_at': article.change_date.isoformat() if article.change_date else None,
                    'password_protected': bool(article.pwd),
                    'cover': {'original_url': cover_url, 'path': cover_path},
                    'assets': assets,
                    'warnings': warnings,
                }
                write_text(f'{folder}/article.md', content)
                write_text(f'{folder}/metadata.json', json.dumps(metadata, ensure_ascii=False, indent=2))
                manifest['articles'].append({
                    'id': article.pk, 'title': article.title or '', 'directory': folder,
                    'warnings': warnings,
                })

            write_text('manifest.json', json.dumps(manifest, ensure_ascii=False, indent=2))
            readme = [
                '文章本地备份（格式版本 1）', f'导出时间：{now}',
                f'文章数量：{len(manifest["articles"])}', '',
                '解压后使用 Markdown 编辑器打开各文章目录中的 article.md。',
                'metadata.json 保存文章信息和图片地址映射；manifest.json 为文章清单。',
                '请保留 images 文件夹与 article.md 的相对位置。',
                '仅导出已保存的正式文章（含未发布文章），不包含草稿、评论和账号数据。',
                '密码文章的正文以明文保存；不包含密码或密码哈希，请妥善保管压缩包。',
                '此文件用于本地保存与迁移参考，当前尚未提供导入恢复功能。', '',
                '图片处理说明：外链保持原地址；缺失、超限或不支持的图片列于下方。',
            ]
            for entry in manifest['articles']:
                for warning in entry['warnings']:
                    readme.append(f'[{entry["id"]} {entry["title"]}] {warning["reason"]}：{warning["url"]}')
            if not any(entry['warnings'] for entry in manifest['articles']):
                readme.append('无图片警告。')
            write_text('README.txt', '\n'.join(readme) + '\n')
        output.seek(0)
        return output
    except Exception:
        output.close()
        raise
