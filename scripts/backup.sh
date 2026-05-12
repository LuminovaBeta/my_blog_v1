#!/bin/bash

# ================= 配置区 =================
# 1. 基础路径配置
PROJECT_DIR="/home/wshsm/my_blog_v1"         # 你的 Django 项目根目录
BACKUP_DIR="/home/wshsm/blog_backup"            # 备份文件存放的目录
MEDIA_DIR="$PROJECT_DIR/media/uploads"       # 图片所在目录

# 2. 数据库配置 (这里以最常用的 MySQL 为例。如果是 SQLite，直接打包那个 db.sqlite3 文件即可)
DB_USER="my_blog_user" # 用户名
DB_PASS="root" # 你的数据库密码
DB_NAME="my_blog"   # 你的数据库名

# 3. 生成精确到秒的时间戳 (格式: 20260512143005)
DATE=$(date +%Y%m%d%H%M%S)
BACKUP_FILENAME="backup-${DATE}.tar.gz"

# ================= 执行区 =================

echo "开始执行博客备份: $DATE"

# 1. 确保备份目录存在
mkdir -p $BACKUP_DIR

# 2. 导出数据库为 SQL 文件
echo "正在导出数据库..."
mysqldump -u$DB_USER -p$DB_PASS $DB_NAME > $BACKUP_DIR/db_backup_$DATE.sql

# 3. 将数据库 SQL 和 图片目录 一起压缩成一个大礼包 (.tar.gz)
echo "正在打包图片和数据库..."
tar -czf $BACKUP_DIR/$BACKUP_FILENAME -C $BACKUP_DIR db_backup_$DATE.sql -C $PROJECT_DIR media

# 4. 打包完成后，删除临时的 SQL 文件（因为它已经在压缩包里了）
rm -f $BACKUP_DIR/db_backup_$DATE.sql

# 5. 清理过期的旧备份 (只保留最近 7 天的备份，防止硬盘被撑爆)
# echo "清理 7 天前的旧备份..."
# find $BACKUP_DIR -name "blog_backup_*.tar.gz" -type f -mtime +7 -exec rm {} \;

echo "✅ 备份完成！备份文件已保存至: $BACKUP_DIR/$BACKUP_FILENAME"