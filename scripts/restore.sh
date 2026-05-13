#!/bin/bash

# ================= 1. 基础检查与加载配置 =================
# 检查是否传入了备份文件参数
if [ -z "$1" ]; then
    echo "❌ 错误: 请指定要恢复的备份文件！"
    echo "用法: ./restore.sh /你的备份路径/20260512143005-backup-ulb3a3ot.tar.gz"
    exit 1
fi

BACKUP_FILE="$1"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

if [ -f "$SCRIPT_DIR/.env.backup" ]; then
    source "$SCRIPT_DIR/.env.backup"
else
    echo "❌ 错误: 找不到配置文件 $SCRIPT_DIR/.env.backup"
    exit 1
fi

# ================= 2. 🚨 危险操作确认 🚨 =================
echo "==================================================="
echo "⚠️ 警告：你正在执行博客数据恢复/同步操作！"
echo "目标项目目录: $PROJECT_DIR"
echo "目标数据库名: $DB_NAME"
echo "待恢复备份包: $BACKUP_FILE"
echo "⚠️ 此操作将【覆盖】当前数据库和 media 文件夹的现有内容！"
echo "==================================================="
read -p "你确定要继续吗？输入 'yes' 确认: " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "🚫 操作已取消。"
    exit 0
fi

# ================= 3. 执行核心解压与恢复 =================
echo "⏳ 开始执行恢复流程..."

# 创建一个临时文件夹用来解压
TEMP_DIR="/tmp/blog_restore_temp"
rm -rf $TEMP_DIR
mkdir -p $TEMP_DIR

# 1. 解压缩包
echo "📦 正在解压备份文件..."
tar -xzf "$BACKUP_FILE" -C "$TEMP_DIR"

# 2. 恢复数据库
echo "🗄️ 正在覆盖同步数据库..."
# 你的备份脚本里导出的 sql 名字叫 db_backup_temp.sql
mysql -u$DB_USER -p$DB_PASS $DB_NAME < "$TEMP_DIR/db_backup_temp.sql"

# 3. 同步 media 文件夹
echo "🖼️ 正在同步用户 media 文件..."
# 使用 rsync 替代 cp，它是最强大的同步工具，只会覆盖修改过的文件，效率极高
# 注意：确保你的服务器上安装了 rsync (sudo apt install rsync)
rsync -av --delete "$TEMP_DIR/media/" "$PROJECT_DIR/media/"

# 4. 清理临时文件
echo "🧹 清理临时解压文件..."
rm -rf "$TEMP_DIR"

echo "🎉 恢复/同步全部完成！你的博客已满血复活！"