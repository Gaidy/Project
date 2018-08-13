from flask import g, jsonify
from flask import render_template
from flask import request
from flask import session

from info import constants
from info import db
from info.models import Category, News, User
from info.utils.common import user_login_data
from info.utils.image_storage import storage
from info.utils.response_code import RET
from flask import redirect
from  . import user_blue

@user_blue.route("/other_news_list")
@user_login_data
def other_news_list():
    page = request.args.get("p",1)
    user_id = request.args.get("user_id")
    try:
        page = int(page)
    except Exception as e:
        page=1
    if not all([page,user_id]):
        return jsonify(errno = RET.PARAMERR,errmsg = "参数错误")
    paginate = News.query.filter(News.user_id == user_id).paginate(page,10,False)
    news = paginate.items
    current_page = paginate.page
    total_page = paginate.pages

    news_dict_li = []
    for item in news:
        news_dict_li.append(item.to_review_dict())

    data = {
        "news_list":news_dict_li,
        "current_page":current_page,
        "total_page":total_page
    }
    return jsonify(errno=RET.OK, errmsg="OK", data=data)






@user_blue.route("/other_info")
@user_login_data
def other_info():
    user = g.user
    if not user:
        return jsonify(errno = RET.SESSIONERR,errmsg = "请登陆")
    other_user_id = request.args.get("id")
    if not other_user_id:
        return jsonify(errno = RET.PARAMERR,errmsg = "参数错误")
    other = User.query.get(other_user_id)
    is_followed = False
    if other.followers.filter(User.id == user.id):
        is_followed = True

    data = {
        "user_info":user.to_dict() ,
        "other_info":other,
        "is_followed":is_followed
    }

    return render_template("news/other.html",data = data)

@user_blue.route("/user_follow")
@user_login_data
def user_follow():
    user = g.user
    if not user:
        return jsonify(errno = RET.SESSIONERR,errmsg = "请登录")

    page = request.args.get("p",1)
    try:
        page = int(page)
    except Exception as e:
        page = 1
    follow_users =  []
    paginate = user.followed.paginate(page,10,False)
    follows = paginate.items
    current_page = paginate.page
    total_page = paginate.pages
    for follow in follows:
        follow_users.append(follow.to_dict())
    print("follow",follow_users)
    data = {
        "users":follow_users,
        "current_page":current_page,
        "total_page":total_page
    }

    return render_template("news/user_follow.html",data = data)



@user_blue.route("/info")
@user_login_data
def user_info():
    user = g.user
    data = {
        "user_info":user.to_dict() if user else None
    }
    return render_template("/news/user.html",data=data)


@user_blue.route("/base_info",methods = ["GET","POST"])
@user_login_data
def user_base_info():
    user = g.user
    data = {
        "user_info": user.to_dict() if user else None
    }
    if request.method == "GET":

        return render_template("/news/user_base_info.html",data=data)

    signature = request.json.get("signature")
    nick_name = request.json.get("nick_name")
    gender = request.json.get("gender")

    if not all([signature,nick_name,gender]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数有误")

    user.nick_name = nick_name
    user.signature = signature
    user.gender = gender
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存数据失败")

    session["nick_name"] = nick_name
    return jsonify(errno=RET.OK, errmsg="修改成功")


@user_blue.route("/pic_info",methods = ["GET","POST"])
@user_login_data
def user_pic_info():
    user = g.user
    if request.method == "GET":
        data = {
            "user_info":user.to_dict() if user else None
        }
        return render_template("news/user_pic_info.html",data = data)
    #获取要上传的文件
    try:
        avatar = request.files.get("avatar").read()
    except Exception as e:
        return jsonify(errno=RET.PARAMERR, errmsg="读取文件出错")

    #将文件上传到七牛云
    try:
        url = storage(avatar)
    except Exception as e:
        return jsonify(errno=RET.THIRDERR, errmsg="上传图片错误")
    #将头像更新到用户模型中
    user.avatar_url = url
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存用户数据错误")
    print(constants.QINIU_DOMIN_PREFIX + url)

    return jsonify(errno=RET.OK, errmsg="OK", data={"avatar_url": constants.QINIU_DOMIN_PREFIX + url})

@user_blue.route("/pass_info",methods = ["GET","POST"])
@user_login_data
def pass_info():
    user = g.user
    if request.method == "GET":
        return render_template("news/user_pass_info.html")
    old_password = request.json.get("old_password")
    new_password = request.json.get("new_password")
    if not all([old_password,new_password]):
        return jsonify(errno = RET.PARAMERR,errmsg = "请输入密码")
    if not user.check_password(old_password):
        return jsonify(errno = RET.PARAMERR,errmsg = "旧密码错误")

    user.password = new_password
    db.session.commit()
    session.pop("user_id")
    session.pop("nick_name")
    return jsonify(errno=RET.OK, errmsg="密码修改成功")


@user_blue.route("/collection")
@user_login_data
def user_collection():

    p = request.args.get("p",1)
    try:
        p = int(p)
    except Exception as e:
        p=1
    user = g.user
    collections = []
    current_page = 1
    total_page = 1
    print(user,"1111111111")
    paginate = user.collection_news.paginate(p, constants.USER_COLLECTION_MAX_NEWS, False)
    items = paginate.items
    current_page = paginate.page
    total_page = paginate.pages


    collections = []
    for item in items:
        collections.append(item.to_dict())
    data = {
        "collections" : collections,
        "current_page" :current_page,
        "total_page" : total_page

    }

    return render_template("news/user_collection.html",data = data)

@user_blue.route("/news_release",methods = ["GET","POST"])
@user_login_data
def news_release():
    if request.method == "GET":
        category_list = Category.query.all()
        categorys = []
        for category in category_list:
            categorys.append(category.to_dict())
        categorys.pop(0)
        data = {
                "categories" : categorys
            }
        return render_template("news/user_news_release.html",data=data)

    title = request.form.get("title")
    category_id = request.form.get("category_id")
    digest = request.form.get("digest")
    index_image = request.files.get("index_image")
    content = request.form.get("content")

    if not all([title,category_id,digest,content]):
        return jsonify(errno = RET.PARAMERR,errmsg = "参数错误")

    user = g.user
    index_image = index_image.read()
    key = storage(index_image)

    news = News()
    news.title = title
    news.source = "个人资源"
    news.digest = digest
    news.content = content
    news.index_image_url = constants.QINIU_DOMIN_PREFIX + key
    news.category_id = category_id
    news.user_id = user.id

    news.status = 1
    db.session.add(news)
    db.session.commit()
    return jsonify(errno=RET.OK, errmsg="发布成功")

@user_blue.route("/news_list")
@user_login_data
def news_list():
    user = g.user
    page = request.args.get("p",1)
    try:
        page = int(page)
    except Exception as e :
      page = 1
    paginate = News.query.filter(News.user_id==user.id).paginate(page,10,False)
    items = paginate.items
    current_page = paginate.page
    total_page = paginate.pages
    news_list =[]
    for item in items:
        news_list.append(item.to_dict())
    data = {
        "current_page": current_page,
        "total_page": total_page,
        "news_list": news_list
    }
    return render_template("news/user_news_list.html", data=data)
