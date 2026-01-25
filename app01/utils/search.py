from urllib.parse import urlencode

class Search:
    def __init__(self, order, order_list, query_params):
        self.order_list = order_list
        self.order = order
        self.query_params = query_params

    def order_html(self):
        order_list = []
        # 综合排序
        # self.query_params['order'] = '-change_date'
        # order_list.append(f'<li><a href="?{self.query_encode}">综合排序</a></li>')
        # 排序列表
        for li in self.order_list:
            self.query_params['order'] = li[0]
            if self.order == li[0]:
                li = f'<li class="active"><a href="?{self.query_encode}">{li[1]}</a></li>'
            else:
                li = f'<li><a href="?{self.query_encode}">{li[1]}</a></li>'
            order_list.append(li)

        if not self.order:
            str_li = order_list[0]
            new_li = str_li[0:3] + ' class="active"' + str_li[3:]
            order_list[0] = new_li

        return ''.join(order_list) 

    # property: 可以不用传参(把括号去掉)
    @property
    def query_encode(self):
        return self.query_params.urlencode()


# if __name__ == '__main__':
#     order = Search(
#         order='look_count',
#         # 发布 浏览 点赞 收藏 评论
#         order_list=[
#             ('-create_date', '最新发布'), 
#             ('look_count', '最多浏览'), 
#             ('digg_count', '最多点赞'), 
#             ('collects_count', '最多收藏'), 
#             ('comment_count', '最多评论'), 
#         ],
#         query_params={"key" : '测试'}
#     )
#     print(order.order_html())
