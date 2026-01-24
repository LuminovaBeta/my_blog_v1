import os
import sys
import django

# 父路径
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(base_dir)

# sub_comment 代表的是 “挂载在当前根评论下的所有子评论列表”。

if __name__ == '__main__':
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "my_blog.settings")
    import django
    django.setup()

    from app01.models import Articles, Comment
    # print(Articles.objects.get(nid=1))

    # 方案二：根据根评论递归查找他下面的所有子评论，并放到一个空间中
    # 找到某个文章的所有评论
    comment_query = Comment.objects.filter(article_id=15)

    def find_root_sub_comment(root_comment, sub_comment_list):
        for sub_comment in root_comment.comment_set.all():
            # 找子评论
            sub_comment_list.append(sub_comment) # 追加
            return find_root_sub_comment(sub_comment, sub_comment_list)
        return 
    
    # 把评论存储到列表
    comment_list = []

    for comment in comment_query:
        # print(comment, comment.parent_comment)
        # 如果父亲为None, 就说明是根评论
        if not comment.parent_comment:

            # 递归查找所有子评论
            lis = []

            find_root_sub_comment(comment, lis)
            comment.sub_comment = lis
            comment_list.append(comment)
            continue
    for comment in comment_list:
        print(comment)
        for sub_comment in comment.sub_comment:
            print(sub_comment)
    
