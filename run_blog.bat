@echo off
chcp 65001 >nul
title 博客本地开发服务器

echo 🚀 正在启动 Django 博客项目...
echo =======================================

:: 切换到脚本所在的当前目录
cd /d "%~dp0"

:: 检查虚拟环境是否存在
if not exist "venv\Scripts\activate.bat" (
    echo ❌ 找不到虚拟环境！请检查 venv 文件夹是否存在。
    pause
    exit /b
)

:: 激活虚拟环境并启动服务
call venv\Scripts\activate.bat
python manage.py runserver 127.0.0.1:8000

pause