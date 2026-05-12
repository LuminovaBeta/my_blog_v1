## 扫地机器人脚本

通过游标逐篇读取数据库文章，提取图片地址并存入集合，随后立即释放内存。最后遍历磁盘文件，删除所有不在该集合中的图片。

文件位置 `my_BLOG/app01/management/commands/clean_zombie_images.py`

```bash
python manage.py clean_zombie_images
```

## 文件备份

当前还没有进行开发此功能

