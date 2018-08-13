import redis
from flask import g
from flask import render_template

from config import config_map
from flask_wtf.csrf import CSRFProtect, generate_csrf
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, app

db = SQLAlchemy()
redis_store = None # type:redis.StrictRedis

def create_app(config_name):

    app = Flask(__name__)
    class_name = config_map.get(config_name)
    app.config.from_object(class_name)
    # 配置数据库
    # global db
    # db = SQLAlchemy(app)
    db.init_app(app)   #将db初始化，并将db设置为全局变量
    global redis_store
    redis_store = redis.StrictRedis(host=class_name.REDIS_HOST, port=class_name.REDIS_PORT,decode_responses=True)
    Session(app)
    CSRFProtect(app)

    from info.utils.common import user_login_data

    @app.errorhandler(404)
    @user_login_data
    def not_found(e):
        user = g.user
        data = {
            "user_info": user.to_dict() if user else None
        }
        return render_template("news/404.html", data=data)


    @app.after_request
    def after_request(response):
        # 调用函数生成 csrf_token
        csrf_token = generate_csrf()
        # 通过 cookie 将值传给前端
        response.set_cookie("csrf_token", csrf_token)
        return response

    from .index import index_blue
    app.register_blueprint(index_blue)
    from .passport import passport_bule
    app.register_blueprint(passport_bule)
    from .news import news_blue
    app.register_blueprint(news_blue)
    from .user import user_blue
    app.register_blueprint(user_blue)

    from .admin import admin_blue
    app.register_blueprint(admin_blue)


    #添加过滤器
    from info.utils.common import do_index_class
    app.add_template_filter(do_index_class,"index_class")
    return app

