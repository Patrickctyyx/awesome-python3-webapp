### 到这里为止web框架已经基本成型了，比较一下和flask的差别

#### 连接数据库
- flask:使用MySQLdb模块
- awesome:创建了全局的连接池

#### 初始化app
- flask:使用flask.Flask类
- awesome:使用aiohttl.web.Application类

#### 渲染模板
- flask:内置jinja2，直接用render_template()来渲染
- awesome:要激活jinja2环境(jinja2.Environment类)

#### url处理函数
- flask:直接把想要的路径用@app.route()和函数绑定就可以了
- awesome:

1. 编写函数来绑定路径
2. 编写RequestHandler来封装url函数
3. 注册url处理函数

#### 跑起应用
- flask:直接app.run()
- awesome:
 
1. loop.create_server(app.make_handler(), '127.0.0.1', 9000)
2. 让loop一直运行

#### 根据以上的这些步骤，awesome基本已经集成了flask的基本功能了，真的是从零开始搭建一个网站
#### 尽管不懂得还有很多，不过还是由衷的佩服那些造轮子的人，大大减小了我们的开发的学习成本
