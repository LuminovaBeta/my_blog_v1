## 一、说明

axios, editor.md, 

## 二、项目运行

1. 创建数据库

   [mysql 安装](https://dev.mysql.com/downloads/installer/)

   ```bash
   mysql -u root -p -e "CREATE DATABASE my_blog CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci; CREATE USER 'my_blog_user'@'%' IDENTIFIED BY 'root'; GRANT ALL PRIVILEGES ON my_blog.* TO 'my_blog_user'@'%'; FLUSH PRIVILEGES;"
   uv run manage.py migrate  // 生成所有数据表
   uv run manage.py createsuperuser   // 创建超级管理员
   ```

2. 运行博客

   ```bash
   uv sync
   uv run manage.py runserver
   ```

## 扫地机器人脚本

通过游标逐篇读取数据库文章，提取图片地址并存入集合，随后立即释放内存。最后遍历磁盘文件，删除所有不在该集合中的图片。

文件位置 `my_BLOG/app01/management/commands/clean_zombie_images.py`

```bash
python manage.py clean_zombie_images
```

## 文件备份

备份脚本存在 `my_blog_v1/scripts/backup.sh`, 需要先配置路径以及数据库

### 备份脚本

> 没有经过恢复测试的备份，就等于没有备份

### 备份恢复命令

"目标项目目录: $PROJECT_DIR"
"目标数据库名: $DB_NAME"
"待恢复备份包: $BACKUP_FILE"

1. 解压缩包

    ```bash
    mkdir blog_restore_temp
    tar -xzf backup-20260513145149.tar.gz -C ./blog_restore_temp
    ```

2. 恢复数据库

    ```bash
    cd blog_restore_temp
    mysql -u my_blog_user -p my_blog < db_backup_20260513145149.sql
    ```

3. 同步 media 文件夹

    ```bash
    rsync -av --delete 源路径 目标路径
    # 例: rsync -av --delete blog_backup/blog_restore_temp/media/ my_blog_v1/media/
    ```
