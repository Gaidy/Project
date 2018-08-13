import functools

from flask import g
from flask import session

from info.models import User


def do_index_class(news_click_desc):
    if news_click_desc ==0:
        return "first"
    elif news_click_desc ==1:
        return "second"
    elif news_click_desc ==2:
        return "third"
    else:
        return ""


def user_login_data(f):
    @functools.wraps(f)
    def wrapper(*args,**kwargs):
        user_id = session.get("user_id")
        user = None
        if user_id:
            user= User.query.get(user_id)
        g.user = user
        return f(*args,**kwargs)
    return wrapper

