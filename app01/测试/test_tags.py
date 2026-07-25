import os
import sys
import django
from django.db.models import Count

# ==========================================
# 核心修改：动态获取项目根目录并加入系统路径
# ==========================================
# 当前文件在 app01/测试/ 下，往上退两级就是项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BASE_DIR)

# 挂载 Django 运行环境 (必须在导入具体模型前完成)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'my_blog.settings')
django.setup()

# ==========================================

# 导入你的标签模型 (这里引用你之前暴露的 app01.models)
from app01.models import Tags

def check_tag_data():
    print("========== 标签数据诊断测试 ==========")
    
    # 诊断 A：检查数据库中是否真的创建了标签
    all_tags = Tags.objects.all()
    print(f"[诊断 A] 数据库中当前总共有 {all_tags.count()} 个标签。")
    for tag in all_tags:
        print(f"   - 发现标签: {tag.title}")
        
    print("\n--------------------------------------\n")
    
    # 诊断 B：检查标签与文章的关联情况
    tags_with_count = Tags.objects.annotate(count=Count('articles'))
    print("[诊断 B] 各标签关联的文章数量：")
    for tag in tags_with_count:
        print(f"   - 标签 [{tag.title}] 关联了 {tag.count} 篇文章")

    print("\n--------------------------------------\n")
    
    # 诊断 C：模拟标签云最终的过滤结果
    cloud_tags = tags_with_count.filter(count__gt=0).order_by('-count')
    print(f"[诊断 C] 最终能进入标签云的标签数量 (count > 0): {cloud_tags.count()}")
    for tag in cloud_tags:
        print(f"   - 标签云将展示: {tag.title} ({tag.count})")
        
    print("======================================")

if __name__ == '__main__':
    check_tag_data()