from flask import Blueprint
from flask import g
from flask import redirect
from flask import request
from flask import session
from flask import url_for
from info.utils.common import user_login_data

user_blue = Blueprint("user",__name__,url_prefix="/user")

from  . import views

@user_blue.before_request
@user_login_data
def before_request():
    user = g.user
    if not user:
        return redirect("/")