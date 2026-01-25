from django.utils.http import urlencode # 记得在文件顶部导入
import math

class Pagination:
    def __init__(self, current_page, all_count, base_url, query_params, per_page=20, pager_page_count=11, position='position'):
        """
        :param self: 
        :param current_page: 当前页码
        :param all_count: 数据库中的总条数
        :param base_url: 原始的url
        :param query_params: 保留原始搜索条件
        :param per_page: 每页显示多少条
        :param pager_page_count: 分页条上最多显示多少个 (动态计算)
        :param position: 锚点id
        """
        
        self.all_count = all_count
        self.per_page = per_page
        self.position = position

        # 计算页码总数
        self.current_count = math.ceil(all_count/per_page)

        # 只能是，满足条件的数字
        self.current_page = current_page
        try:
            self.current_page = int(current_page)
            if not (0 < self.current_page <= self.current_count):
                self.current_page = 1
        except Exception:
            self.current_page = 1# 如果传入的非int，会来到这里
            
        self.base_url = base_url
        self.query_params = query_params
        

        self.pager_page_count = pager_page_count
        # print(self.current_page, self.current_count)

        # 分页的中值
        self.half_pager_count = int(self.pager_page_count / 2)
        if self.current_count < self.pager_page_count:
            # 如果可分页页码小于最大显示页码，就让最大显示页码变成可分页页码
            self.pager_page_count = self.current_count


    def page_html(self):
        # 计算页码的起始和结束
        # 分类讨论 1.正常情况(中间) 2.在左边 3.在右边
        # 1.正常情况(中间)
        # 20 9       4 5 6 7 8 9 10 11 12 13 14
        start = self.current_page - self.half_pager_count -1
        end = self.current_page + self.half_pager_count
        # 2.在左边
        if self.current_page <= self.half_pager_count:
            start = 1
            end = self.pager_page_count

        # 3.在右边
        if self.current_page + self.half_pager_count >= self.current_count:
            start = self.current_count - self.pager_page_count + 1
            end = self.current_count

        # 生成分页
        page_list = []
        # 上一页
        if self.current_page != 1:
            self.query_params['page'] = self.current_page - 1
            page_list.append(f'<li><a href="{self.base_url}?{self.query_encode}#{self.position}">上一页</a></li>')
        # 数字部分
        for i in range(start, end+1):
            self.query_params['page'] = i
            if self.current_page == i:
                li = f'<li class="active"><a href="{self.base_url}?{self.query_encode}#{self.position}">{i}</a></li>'
            else:
                li = f'<li><a href="{self.base_url}?{self.query_encode}#{self.position}">{i}</a></li>'
            page_list.append(li)
        # 下一页
        if self.current_page != self.current_count:
            self.query_params['page'] = self.current_page + 1
            page_list.append(f'<li><a href="{self.base_url}?{self.query_encode}#{self.position}">下一页</a></li>')        
        
        return ''.join(page_list)

    # property: 可以不用传参(把括号去掉)
    @property
    def query_encode(self):
        return self.query_params.urlencode()


    # 列表切片
    # 每页展示的文章索引值，从0开始，左闭右开
    # [  (页码-1)*每页展示条数 : 页码*每页展示条数  ]
    @property
    def start(self):
        return (self.current_page-1)*self.per_page
    @property
    def end(self):
        return self.current_page*self.per_page
