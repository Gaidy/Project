import time
from datetime import timedelta,datetime
from flask import g, jsonify
from flask import redirect
from flask import request
from flask import session
from flask import url_for

from info import constants
from info.utils.common import user_login_data
from info.models import User, News, Category
from info.utils.image_storage import storage
from info.utils.response_code import RET
from . import admin_blue
from  flask import render_template
from info import db

@admin_blue.route("/index")
@user_login_data
def admin_index():
    user = g.user

    return render_template("admin/index.html",user = user.to_dict())


@admin_blue.route("/login",methods = ["GET","POST"])
def admin_login():

    if request.method == "GET":
        user_id = session.get("user_id",None)
        is_admin = session.get("is_admin",False)
        if user_id and is_admin:
            return redirect(url_for("admin.admin_index"))
        return render_template("/admin/login.html")
    username = request.form.get("username")
    password = request.form.get("password")
    if not all([username,password]):
        return render_template("admin/login.html",errmsg = "参数不足")
    try:
        user = User.query.filter(User.mobile == username).first()
    except Exception as e :
        return render_template("admin/login.html",errmsg = "数据查询失败")
    if not user:
        return render_template("admin/login.html",errmsg = "用户不存在")
    if not user.check_password(password):
        return render_template("admin/login.html",errmsg = "密码错误")
    if not user.is_admin:
        return render_template("admin/login.html",errmsg = "用户无权限")

    session["user_id"] = user.id
    session["nick_name"] = user.nick_name
    session["mobile"] = user.mobile
    session["is_admin"] = user.is_admin

    return redirect(url_for("admin.admin_index"))

@admin_blue.route("/user_count")
def user_count():
    total_count = 0
    try:
        total_count = User.query.filter(User.is_admin==False).count()
    except Exception as e:
        total_count = 0

    mon_count = 0


    now = time.localtime()
    mon_begin = "%d-%02d-01" %(now.tm_year,now.tm_mon)
    mon_begin_date = datetime.strptime(mon_begin,"%Y-%m-%d")
    mon_count = User.query.filter(User.is_admin == False, User.create_time >= mon_begin_date).count()


    day_count = 0
    day_begin = '%d-%02d-%02d' % (now.tm_year, now.tm_mon, now.tm_mday)
    day_begin_date = datetime.strptime(day_begin, '%Y-%m-%d')
    day_count = User.query.filter(User.is_admin == False, User.create_time > day_begin_date).count()

    now_date = datetime.strptime(datetime.now().strftime('%Y-%m-%d'),'%Y-%m-%d')

    active_count = []
    active_date = []

    for i in range(0,31):
        begin_date = now_date - timedelta(days = i)
        end_date = now_date - timedelta(days=(i-1))

        count = 0

        count = User.query.filter(User.is_admin == False,User.create_time>=begin_date,User.create_time <end_date).count()
        active_count.append(count)
        active_date .append(begin_date.strftime("%Y‐%m‐%d"))
    print(begin_date,end_date)

    active_count.reverse()
    active_date.reverse()

    data = {
        "total_count": total_count,
        "mon_count": mon_count,
        "day_count": day_count,
        "active_count": active_count,
        "active_date": active_date
    }
    return render_template("admin/user_count.html", data=data)

@admin_blue.route("/user_list")
def user_list():
    page = request.args.get("p",1)
    try:
        page = int(page)
    except Exception as e:
        page = 1
    paginate = User.query.filter(User.is_admin == False).order_by(User.last_login.desc()).paginate(page,10,False)
    items = paginate.items
    current_page = paginate.page
    total_page = paginate.pages
    users = []
    for user in items:
        users.append(user.to_admin_dict())

    data = {
        "users":users,
        "current_page":current_page,
        "total_page":total_page
    }
    return render_template("admin/user_list.html",data = data)

@admin_blue.route("/news_review")
def news_review():
    page = request.args.get("p",1)
    keywords = request.form.get("keywords")

    try:
        page = int(page)
    except Exception as e:
        page = 1

    news_list = []
    current_page = 1
    total_page = 1

    filters = [News.status != 0]
    if keywords:
        filters.append(News.title.contains(keywords))
    paginate = News.query.filter(*filters).order_by(News.create_time.desc()).paginate(page, 10, False)
    items = paginate.items
    current_page = paginate.pages
    total_page = paginate.page
    for item in items:
        news_list.append(item)

    data = {
        "news_list": news_list,
        "current_page": current_page,
        "total_page": total_page
    }
    return render_template("admin/news_review.html", data=data)



@admin_blue.route("/news_review_detail",methods = ["GET","post"])
def news_review_detail():
    if request.method =="GET":
        news_id = request.args.get("news_id")
        news = News.query.get(news_id)
        data = {
            "news":news.to_dict()
        }
        return render_template("admin/news_review_detail.html",data = data)
    action = request.json.get("action")
    news_id = request.json.get("news_id")
    news = News.query.get(news_id)

    if action == "accept":
        news.status = 0
    else:
        reason = request.json.get("reason")
        if not reason:
            return jsonify(errno = RET.PARAMERR,errmsg = "请输入拒绝的理由")

            news.status = -1
            news.reason = reason
    db.session.commit()
    return jsonify(errno=RET.OK, errmsg="OK")


@admin_blue.route("/news_edit")
def news_edit():
    page = request.args.get("p",1)
    keywords = request.args.get("keywords","")
    try:
        page = int(page)
    except Exception as e:
        page = 1

    news_list = []
    current_page = 1
    total_page = 1
    filters = []
    if keywords:
        filters.append(News.title.contains(keywords))

    paginate = News.query.filter(*filters).order_by(News.create_time.desc()).paginate(page,10,False)
    news = paginate.items
    current_page = paginate.page
    total_page = paginate.pages
    for new in news:
        news_list.append(new)
    data = {
        "news_list":news_list,
        "current_page":current_page,
        "total_page":total_page
    }
    return render_template('admin/news_edit.html', data=data)

@admin_blue.route("/news_edit_detail",methods = ["GET","POST"])
def news_edit_detail():
    if request.method == "GET":
        news_id = request.args.get("news_id")
        if not news_id:
            return render_template("admin/news_edit_detail.html",data = {"errmsg": "未查询到此新闻"})


        news = News.query.get(news_id)


        if not news:
            return render_template("admin/news_edit_detail.html",data = {"errmsg": "未查询到此新闻"})

        categories = Category.query.all()
        categories_li = []
        for category in categories:
            c_dict = category.to_dict()
            c_dict["is_selected"] = False
            if category.id == news.category_id:
                c_dict["is_selected"] = True
            categories_li.append(c_dict)
        categories_li.pop(0)
        data = {
            "news":news.to_dict(),
            "categories":categories_li
            }
        return render_template('admin/news_edit_detail.html', data = data)

    news_id = request.form.get("news_id")
    title = request.form.get("title")
    digest = request.form.get("digest")
    content = request.form.get("content")
    index_image = request.files.get("index_image")
    category_id = request.form.get("category_id")
    if not all([title,digest,content,category_id]):
        return jsonify(errno = RET.PARAMERR,errmsg = "参数有误")
    news = News.query.get(news_id)
    if not news:
        return jsonify(errno = RET.PARAMERR,errmsg ="未查询到新闻数据" )
    if index_image:
        try:
            index_image = index_image.read()
        except Exception as e:
            return jsonify(errno=RET.PARAMERR, errmsg="参数有误")

        try:
            key = storage(index_image)
        except Exception as e:
            return jsonify(errno = RET.THIRDERR,errmsg = "上传图片错误")
        news.index_image_url = constants.QINIU_DOMIN_PREFIX +key

    news.title = title
    news.digest = digest
    news.content = content
    news.category_id = category_id
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存数据失败")
    return jsonify(errno=RET.OK, errmsg="编辑成功")


@admin_blue.route("/news_category")
def get_news_category():
    categories = Category.query.all()
    categories_dicts = []
    for category in categories:
        categories_dicts.append(category.to_dict())
    categories_dicts.pop(0)
    data = {
        "categories":categories_dicts
    }
    return render_template("admin/news_type.html",data = data)


@admin_blue.route("/add_category",methods = ["POST"])
def add_category():
    category_id = request.json .get("id")
    category_name = request.json.get("name")
    if not category_name:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    if category_id:
        try:
            category = Category.query.get(category_id)
        except Exception as e:
            return jsonify(errno = RET.DBERR,errmsg = "查询数据失败")
        if not category:
            return jsonify(errno = RET.NODATA,errmsg = "未查询到分类信息")
        category.name = category_name
    else:
        category = Category()
        category.name = category_name
        db.session.add(category)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify(errno = RET.DBERR,errmsg =  "数据保存失败")
    return  jsonify(errno = RET.OK,errmsg = "保存数据成功")













