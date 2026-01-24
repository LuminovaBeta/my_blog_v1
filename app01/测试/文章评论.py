import os
import sys
import django

# sub_comment 代表的是 “挂载在当前根评论下的所有子评论列表”。

# 父路径
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(base_dir)

if __name__ == '__main__':
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "my_blog.settings")
    import django
    django.setup()

    from app01.models import Articles, Comment
    # print(Articles.objects.get(nid=1))

    # 方案一：根据子评论递归查找根评论，要把它放进根评论的一个空间中
    def find_root_comment(comment:Comment):
        # 找最终跟评论
        if comment.parent_comment:
            # 不是跟评论
            # 递归查找根评论
            return find_root_comment(comment.parent_comment)
        # 是根评论
        return comment
        
    comment_dict = {

    }

    # 找到某个文章的所有评论
    comment_query = Comment.objects.filter(article_id=15)

    for comment in comment_query:
        # print(comment, comment.parent_comment)
        # 如果父亲为None, 就说明是根评论
        if not comment.parent_comment:
            # 把根评论放到字典
            comment_dict[comment.nid] = comment
            # 给根评论添加自定义属性，将所有子评论放进去
            comment.sub_comment = []
            continue

    for comment in comment_query:
        # 一定是某个父评论的子评论
        for sub_comment in comment.comment_set.all():
            #遍历下面所有的子评论
            # 找这个子评论的最终根评论
            # find_root_comment 找这个子评论的最终根评论
            root_comment = find_root_comment(sub_comment)
            # 把子评论添加进属于自己的根评论
            print(sub_comment, root_comment, comment_dict)
            comment_dict[root_comment.nid].sub_comment.append(sub_comment)

    
    for k, v in comment_dict.items():
        print(v, '根评论')
        for comment in v.sub_comment:
            print('  ', comment, '子评论')
