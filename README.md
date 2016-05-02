# weibo_search_spider
新浪微博搜索爬虫

**功能**：爬取新浪微博的搜索结果,支持高级搜索中对搜索时间的限定

**网址**：http://s.weibo.com/

**实现**：采取selenium测试工具，模拟微博登录，结合PhantomJS/Firefox，分析DOM节点后，采用Xpath对节点信息进行获取，实现重要信息的抓取，并存储至Excel中。

**环境**：

1、python 2.7

2、安装selenium库

3、安装Firefox浏览器

获取的微博信息包括：博主昵称, 博主主页, 微博认证, 微博达人, 微博内容, 发布时间, 微博地址, 微博来源, 转发, 评论, 赞
![这里写图片描述](http://img.blog.csdn.net/20160502170809267)

详见博客：http://blog.csdn.net/destinyuan/article/details/51297528