from urllib.parse import urlencode

# 通用的 Search 工具类
class Search:
    def __init__(self, key, current_val, data_list, query_params):
        """
        __init__ 的 Docstring
        
        :param self: 
        :param key: URL 参数名 (如 'order' 或 'word')
        :param current_val: 当前激活的值
        :param data_list: 选项元组列表 [(值, 显示文本), ...]
        :param query_params: request.GET.copy()
        """
        self.key = key
        self.current_val = current_val
        self.data_list = data_list
        self.query_params = query_params

    # 生成筛选部分html标签
    def order_html(self):
        data_list = []
        # 排序列表
        for li in self.data_list:
            # 【关键修改】：使用 self.key 而不是硬编码的 'order'
            self.query_params[self.key] = li[0]

            # 移除分页，防止带页码跳转导致找不到数据
            if 'page' in self.query_params:
                self.query_params.pop('page')

            if self.current_val == li[0]:
                li = f'<li class="active"><a href="?{self.query_encode}">{li[1]}</a></li>'
            else:
                li = f'<li><a href="?{self.query_encode}">{li[1]}</a></li>'
            data_list.append(li)

        # 处理默认选中（如果没有传参数，默认第一个高亮）
        if not self.current_val:
            str_li = data_list[0]
            new_li = str_li[0:3] + ' class="active"' + str_li[3:]
            data_list[0] = new_li

        return ''.join(data_list) 

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
