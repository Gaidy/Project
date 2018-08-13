from flask import current_app
from flask import g, jsonify
from flask import json
from flask import redirect
from flask import request
from flask import url_for
from info.utils.common import user_login_data

from info import db
from info.models import News, User, Comment,CommentLike
from info.utils.response_code import RET
from . import news_blue
from flask import render_template
from info.utils.common import user_login_data



@news_blue.route("/<int:news_id>")
@user_login_data
def news_detail(news_id):
    user = g.user
    # 获取点击的新闻的详情
    news_model = News.query.get(news_id)
    if not user:
        data={
            "news": news_model.to_dict(),
            "user_info":user.to_dict() if user else []
        }
        return render_template("news/detail.html",data = data)
    #获取新闻点击排行前十条
    news_dict_model = News.query.order_by(News.clicks.desc()).limit(10)
    #
    news_dict = []
    #将这十条新闻进行迭代
    for news_wec in news_dict_model:
        news_dict.append(news_wec.to_dict())

    print(news_model)
    #判断新闻是否存在，不存在侧报错
    if not news_model:
        return render_template("/news/404.html")
    #点击新闻，对点击两+1
    news_model.clicks += 1
    #判断是否收藏过该新闻，默认False
    is_collected  = False
    # 当前登录用户是否关注当前新闻作者
    is_followed = False
    if news_model:
        if news_model in user.collection_news:
            is_collected = True
        if  news_model.user and news_model.user.followers.filter(User.id == g.user.id).count()>0:
            is_followed = True
    try:
        comment_list = Comment.query.filter(Comment.news_id ==news_id).order_by(Comment.create_time.desc()).all()
    except Exception as e :
        pass
    comments = []
    for comment in comment_list :
        comment = comment.to_dict() if comment_list else None
        comments.append(comment)

        """获取所以评论点赞的数据"""
        comment_likes = []
        comment_like_ids = []
        if user:
            comment_likes = Comment.query.filter(Comment.user_id==user.id).all()
            comment_like_ids = [comment_like.id for comment_like in
comment_likes]
            comment_dict_list = []
            print("comment_list",comment_list)
            for item in comment_list:
                comment_dict= item.to_dict()
                comment_dict["is_like"] = False
                if item.id in comment_like_ids:
                    comment_dict["is_like"] = True

                comment_dict_list.append(comment_dict)

    data={
        "user_info":user.to_dict() if user else [],
        "click_news_list":news_dict,
        "news": news_model.to_dict(),
        "is_collected":is_collected,
        "comments":comments,
        "is_followed":is_followed
    }
    return render_template("news/detail.html",data = data)



@news_blue.route("/news_collect",methods = ["POST"])
@user_login_data
def news_collect():
    print("news_collect的url",request.url)
    user = g.user
    if not user:
        return jsonify(errno = RET.SERVERERR,errmsg = "请登陆")
    news_id = request.json.get("news_id")
    action = request.json.get("action")

    news = News.query.get(news_id)
    if action == "collect":
        user.collection_news.append(news)
    else:
        user.collection_news.remove(news)
    db.session.commit()
    return jsonify(errno=RET.OK, errmsg="收藏成功")


@news_blue.route("/news_comment",methods = ["POST"])
@user_login_data
def news_comment():
    user = g.user
    if not user:
        return redirect(url_for("/login"))
    news_id = request.json.get("news_id")
    comment_str = request.json.get("comment")
    parent_id = request.json.get("parent_id")
    #获取要评论的新闻
    if not all([news_id, comment_str,comment_str]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不足")
    news = News.query.get(news_id)
    if not news:
        return jsonify(errno=RET.NODATA, errmsg="该新闻不存在")

    comment = Comment()
    comment.user_id= user.id
    comment.news_id = news_id
    comment.content = comment_str
    if parent_id :
        comment.parent_id = parent_id

    try:
        db.session.add(comment)
        db.session.commit()
    except Exception as e:
        return jsonify(errno=RET.DBERR, errmsg="保存评论数据失败")

    return jsonify(errno = RET.OK,errmsg = "评论成功",data =comment.to_dict())


@news_blue.route("/comment_like",methods = ["POST"])
@user_login_data
def set_comment_like():
    """评论点赞"""
    # print("点赞",request.url)
    user = g.user
    if not user :
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")
    #获取参数
    comment_id = request.json.get("comment_id")
    news_id = request.json.get("news_id")
    action = request.json.get("action")

    if not all([comment_id,news_id,action]):

        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

        # 查询评论数据
    try:
        comment = Comment.query.get(comment_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询数据失败")

    if not comment:
        return jsonify(errno=RET.NODATA, errmsg="评论数据不存在")

    if action == "add":
        comment_like = CommentLike.query.filter(CommentLike.comment_id==comment_id,CommentLike.user_id == user.id).first()
        if not comment_like:
            comment_like = CommentLike()
            comment_like.comment_id = comment_id
            comment_like.user_id = user.id
            comment.like_count+=1
        else:
            comment_like = Comment.query.filter(CommentLike.comment_id == comment_id,CommentLike.user_id==user.id).first()
            if comment_like:
                db.session.delete(comment_like)
                comment.like_count -= 1
    db.session.commit()
    return jsonify(errno=RET.OK, errmsg="点赞成功")

@news_blue.route("/followed_user",methods = ["POST"])
@user_login_data
def followed_user():
    if not g.user:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")
    user_id = request.json.get("user_id")
    action = request.json.get("action")
    if not all([user_id,action]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
    if action not in ("follow","unfollow"):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")
    try:
        target_user = User.query.get(user_id)
    except Exception as e:
        return jsonify(errno=RET.DBERR, errmsg="查询数据库失败")
    if not target_user:
        return jsonify(errno=RET.NODATA, errmsg="未查询到用户数据")
    if action == "follow":
        if target_user.followers.filter(User.id == g.user.id).count()>0:
            return jsonify(errno=RET.DATAEXIST, errmsg="当前已关注")
        target_user.followers.append(g.user)
    else:
        if target_user.followers.filter(User.id == g.user.id).count()>0:
            target_user.followers.remove(g.user)
    try:
        db.session.commit()
    except Exception as e :
        return jsonify(errno = RET.DBERR,errmsg = "数据保存错误")
    return jsonify(errno=RET.OK, errmsg="操作成功")



