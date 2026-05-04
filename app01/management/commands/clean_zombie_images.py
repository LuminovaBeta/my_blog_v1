# 通过游标逐篇读取数据库文章，提取图片地址并存入集合，随后立即释放内存。最后遍历磁盘文件，删除所有不在该集合中的图片。

import os
import time
import re
from django.core.management.base import BaseCommand
from django.conf import settings
from app01.models import Articles

class Command(BaseCommand):
    help = '高性能清理 Markdown 编辑器产生的无用僵尸图片'

    def handle(self, *args, **options):
        self.stdout.write("开始扫描数据库中正在使用的图片...")
        
        # 1. 创建一个“已使用名单”（使用 Python 的 Set 集合，查找速度是 O(1) 闪电级）
        used_image_urls = set()
        
        # 匹配 Markdown 图片语法的正则表达式：![...](url) 或者 <img src="url">
        # 这里提取的是 /media/uploads/... 这样的路径
        # 可以遍历 任意层级 的子路径
        img_pattern = re.compile(r'!\[.*?\]\((/media/uploads/articles_image/.*?)\)|src="(/media/uploads/articles_image/.*?)"')

        # 2. 🌟 核心优化：使用 iterator() 游标！
        # 它可以让 Django 每次只从数据库拉取一小批数据，而不是全部塞进内存
        # only('content') 表示只查询内容字段，不查标题、作者等，进一步提升速度
        for article in Articles.objects.only('content').iterator(chunk_size=1000):
            if Articles.content:
                # 找出这篇文章里所有的图片链接
                matches = img_pattern.findall(article.content)
                for match in matches:
                    # 正则可能会匹配到两个分组中的一个，取有值的那一个
                    url = match[0] if match[0] else match[1]
                    used_image_urls.add(url)

        self.stdout.write(f"数据库扫描完毕，共有 {len(used_image_urls)} 张图片正在被使用。")

        # 👇 测试：打印所有找到的图片 URL 👇
        self.stdout.write(self.style.WARNING("--- 以下是数据库中正在使用的图片列表 ---"))
        for url in used_image_urls:
            self.stdout.write(url)
        self.stdout.write(self.style.WARNING("--------------------------------------"))
        # 👆 测试部分结束 👆

        # 3. 定位到你的图片上传根目录
        upload_dir = os.path.join(settings.MEDIA_ROOT, 'uploads', 'articles_image')
        if not os.path.exists(upload_dir):
            self.stdout.write(self.style.WARNING("图片目录不存在，无需清理。"))
            return

        deleted_count = 0
        current_time = time.time()

        self.stdout.write("开始比对硬盘文件并清理僵尸图片...")

        # 4. 遍历硬盘里的所有图片文件
        for root, dirs, files in os.walk(upload_dir):
            for file in files:
                file_path = os.path.join(root, file)
                file_mod_time = os.path.getmtime(file_path)
                
                # 如果是 24 小时内上传的新图片，跳过（保护正在编辑的文章）
                if current_time - file_mod_time < 86400: # 缓冲期：24小时
                    continue
                
                # 计算出硬盘文件对应的 URL 格式
                relative_path = file_path.replace(settings.MEDIA_ROOT, '').replace('\\', '/')
                url_path = f"{settings.MEDIA_URL}{relative_path}".replace('//', '/')

                # 5. 🌟 核心优化：在 Set 中查找
                # 因为 used_image_urls 是 Set 集合，这里的查找不消耗 CPU，无论数据多大都是瞬间判断
                if url_path not in used_image_urls:
                    try:
                        os.remove(file_path)
                        deleted_count += 1
                        self.stdout.write(f"已删除: {file}") # 如果图片太多，建议把这行打印注释掉，不然刷屏会减慢速度
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"删除失败 {file}: {e}"))

        self.stdout.write(self.style.SUCCESS(f"清理完毕！共清除了 {deleted_count} 个僵尸文件。"))
