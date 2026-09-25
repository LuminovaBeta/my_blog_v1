整体判断：项目结构完整、可以通过 Django 基础检查和 Python 编译，但目前更接近“功能原
  型”，继续增加功能前，建议先处理权限、安全和数据一致性。

  ## 第一优先级：立即修复

  1. 配置中存在明文密钥

  my_blog/settings.py:24 中直接保存了：

  - Django SECRET_KEY
  - MySQL 密码
  - 邮箱授权码
  - DEBUG=True
  - ALLOWED_HOSTS=['*']

  建议立即更换已经暴露的邮箱授权码和生产密钥，然后改为环境变量。仅从代码中删除不够，因为它们可能还存在于 Git 历史中。

  2. 文章接口缺少权限验证

  api/views/article.py:71 的文章发布、编辑接口没有登录或管理员判断；edit_article_content (api/views/article.py:214) 同时
  关闭了 CSRF 且没有鉴权。

  这意味着匿名请求理论上可以发布文章、修改任意文章正文。建议统一使用：

  - LoginRequiredMixin
  - UserPassesTestMixin
  - 或明确的编辑者权限装饰器

  后台页面也应保护，my_blog/urls.py:35 中只有 /backend/ 自己判断了登录，直接访问新增、编辑、封面页面仍可能绕过。

  3. 匿名文件上传风险

  api/views/uploads.py:9 的文章图片上传：

  - 使用了 csrf_exempt
  - 没有登录验证
  - 没有限制文件大小
  - 没有验证真实图片格式
  - 文件名没有完全由服务器生成

  建议用 Pillow 验证内容、限制尺寸和容量、生成 UUID 文件名，并只允许编辑者上传。

  4. 收藏逻辑会破坏点赞数据

  api/views/article.py:206 在收藏后更新了 digg_count，而不是只读取或更新 collects_count。收藏操作会导致文章点赞数被错误
  覆盖。

  5. 未发布及加密文章可能被绕过

  app01/views.py:50 的搜索没有过滤 status=1，文章详情 (app01/views.py:90) 也没有校验发布状态和文章密码。目前 pwd 只是存
  储字段，并没有真正形成访问控制。

  ## 第二优先级：稳定性与数据一致性

  - 评论删除使用前端传来的文章 ID 和父评论 ID 来修改计数，容易修改错误记录；评论不存在时调用 .first().user 也会直接报
    错。位置：api/views/comment.py:61。

  - 评论、收藏、标签和计数更新应放进 transaction.atomic()，并以数据库中的关系为准，不信任前端传来的关联 ID。
  - 点赞接口允许无限重复点赞，应增加用户点赞关系或限流。
  - JSON 中间件只识别完全等于 application/json 的请求头；遇到 application/json; charset=utf-8 或非法 JSON 时，
    request.data 可能不存在或直接返回 500。位置：app01/middleware_decode.py:6。

  - 邮箱验证码只按 Session 限制，容易通过新建 Session 批量发送；建议增加 IP、邮箱维度限流，并使用任务队列代替临时线程。
  - 注册与修改密码没有调用 Django 的密码验证器，表单只要求 4 位密码。

  ## 第三优先级：性能与可维护性

  - 评论树通过递归查询子评论，会产生明显的 N+1 查询。建议一次查出文章全部评论后，在内存中按 parent_comment_id 构建树。
  - 首页、搜索页使用 select_related('cover') 和必要的 prefetch_related('tag')，减少模板渲染查询。
  - app01/views.py 与 app01/views/ 目录职责重复，建议正式拆成 public.py、account.py、backend.py，删除未被加载的重复代
    码。

  - static/editor.md-master 包含 520 个文件、约 7.14 MiB，包括源码、测试、示例和文档。生产静态目录只保留运行必需的构建产
    物即可。

  - pyproject.toml、requirements.txt 和 uv.lock 三套依赖定义存在漂移风险，建议以 pyproject.toml + uv.lock 为唯一来源。
  - API 返回几乎始终是 HTTP 200，只通过自定义 code 表示错误。建议逐步使用 400、401、403、404、409 等标准状态码。

  ## 测试建议

  目前 Django 显示 Ran 0 tests。建议首先补这几组回归测试：

  - 匿名用户不能发布、编辑文章或上传图片
  - 普通用户不能编辑其他人的内容
  - 收藏不会改变点赞数
  - 删除评论后父评论和文章计数正确
  - 未发布、加密文章不能通过搜索或直接 URL 绕过
  - 非法 JSON、空文件、伪装图片不会产生 500

  ## 当前暂存修改的反馈

  当前有 5 个已暂存文件，主要是首页移动端适配。这里有两个明显问题：

  - templates/index.html:8 设置了 user-scalable=no，会阻止用户缩放页面，不利于无障碍体验，建议移除。
  - static/scss/index.scss:461 在移动端全局隐藏 .right，可能同时隐藏文章卡片正文等所有名为 right 的区域；应改为精确选择
    器。另外样式引用了 .menu_toggle_btn 和 .mobile_drawer，但模板里没有对应菜单按钮和抽屉逻辑，因此移动端导航目前并不完
    整。

  检查结果：基础 manage.py check 通过、代码编译通过、迁移无遗漏；生产检查有 7 项安全警告，自动化测试为 0。最合适的后续顺
  序是：先做“密钥迁移 + API 权限 + 上传安全 + 收藏逻辑修复”，然后补测试，最后再继续移动端和新功能。