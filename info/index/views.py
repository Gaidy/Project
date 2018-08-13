from flask import g
from flask import render_template,current_app, jsonify
from flask import request
from flask import session
from info.utils.common import user_login_data
from info import constants, db
from info.models import User, News, Category
from info.utils.response_code import RET
from . import index_blue
"""
index.views:只放置首页的业务逻辑
"""
@index_blue.route("/favicon.ico")
def xxxx():
    return current_app.send_static_file('news/favicon.ico')

# self.send_static_file



@index_blue.route("/")
def index():
    # 1.判断用户是否登陆
    user_id = session.get("user_id")
    user = None
    if user_id:
        user = User.query.get(user_id)
        print(user)
    # 2.获取点击排行的数据
    try:
        news_list = News.query.order_by(News.clicks.desc()).limit(10)
    except Exception as e:
        current_app.logger.error(e)
    click_news_list = []
    for news in news_list if news_list else []:
        click_news_list.append(news.to_basic_dict())


    # 3.获取新闻分类
    categories = Category.query.all()
    print(categories[0].name)
    categories_list = []
    for category in categories:
        categories_list.append(category.to_dict())


    data = {
        "user_info":user.to_dict() if user else None,
        "click_news_list":click_news_list,
        "categories_list":categories_list
    }

    return render_template("news/index.html",data=data)

@index_blue.route("/newslist")
def get_news_list():
    cid = request.args.get("cid","1")
    page = request.args.get("page","1")
    per_page = request.args.get("per_page","10")
    try:
        cid = int(cid)
        page = int(page)
        per_page = int(per_page)
    except Exception as e:
        return jsonify(errno = RET.PARAMERR,errmsg = "参数错误")
    filters = [News.status == 0]
    if cid != 1:
        filters.append(News.category_id == cid)
    paginate = News.query.filter(*filters).order_by(News.create_time.desc()).paginate(page, per_page, False)
    print(paginate)
    # 获取查询出来的数据
    items = paginate.items
    print(items)
    # 获取到总页数
    total_page = paginate.pages
    current_page = paginate.page
    news_list = []
    for news in items:
        news_list.append(news.to_dict())
    data = {
        "newsList":news_list,
        "current_page":current_page,
        "total_page":total_page,
        "cid":cid
    }
    return jsonify(errno=RET.OK, errmsg="ok", data=data)

@index_blue.route("/logout")
def logout():
    session.pop("mobile")
    session.pop("user_id")
    session.pop("nick_name")
    return jsonify(errno = RET.OK,errmsg = "退出成功" )







