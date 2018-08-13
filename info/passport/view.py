import random
from datetime import datetime

from flask import make_response
from flask import request, jsonify
from flask import session

from info import constants, db
from info import redis_store
from info.models import User
from info.utils.captcha.captcha import captcha
from info.utils.response_code import RET
from . import passport_bule

@passport_bule.route("/login",methods = ["POST"])
def login():
    print("请求sms_code 的url:" + request.url)

    mobile = request.json.get("mobile")
    password = request.json.get("password")
    user = User.query.filter(mobile ==User.mobile).first()
    if not user:
        return jsonify(errno = RET.PARAMERR,errmsg = "请先注册")
    # 4. 保存用户登录状态
    if not user.check_password(password):
        return jsonify(errno = RET.PARAMERR,errmsg = "密码错误")
    session["user_id"] = user.id
    session["nick_name"] = user.nick_name
    session["mobile"] = user.mobile
    # 记录用户最后一次登录时间
    user.last_login = datetime.now()
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
    return jsonify(errno = RET.OK,errmsg = "登陆成功")


@passport_bule.route("/register",methods = ["POST"])
def register():
    mobile = request.json.get("mobile")
    smscode = request.json.get("smscode")
    password= request.json.get("password")

    redis_snscode = redis_store.get("sms_code" + mobile)
    print(redis_snscode)
    if smscode != redis_snscode:
        return jsonify(errno = RET.PARAMERR,errmsg = "验证码输入错误")
    user= User()
    user.mobile = mobile
    user.nick_name = mobile
    user.password = password

    user.last_login = datetime.now()
    print(db)

    db.session.add(user)
    db.session.commit()

    session["mobile"] = user.mobile
    session["user_id"] = user.id
    print(user.id)
    session["nick_name"] = user.mobile

    return jsonify(errno = RET.OK,errmsg = "注册成功")




@passport_bule.route("/sms_code",methods = ["POST"])
def sms_code():
    print("请求sms_code 的url:" + request.url)

    # mobile = request.json.get("mobile")
    # image_code = request.json.get("image_code")
    # image_code_id = request.json.get("image_code_id")
    # print(image_code_id)
    # redis_image_code = redis_store.get("sms_code" +image_code_id)
    # print(redis_image_code)
    # print(image_code)
    # if not redis_image_code:
    #     return jsonify(errno = RET.NODATA,errmsg = "图片验证码过期")
    # # 随机生成验证码
    # result = random.randint(0, 999999)
    # # 保持验证码是6位
    # sms_code = "%06d" % result
    # print("短信验证码 = " + sms_code)
    # # 发送短信
    # # 第一个参数发送给哪个手机号,最多一次只能发送200个手机号,通过,分割
    # # 第二个参数是数组形式进行发送[sms_code,100],数组里面的第一个参数表示机验证码, 第二个参数表示多久过期, 单位是分钟
    # # 第三个参数表示模板id 默认值表示1
    # # statusCode = CCP().send_template_sms(mobile,[sms_code, 5],1)
    # #
    # # if statusCode != 0:
    # # return jsonify(errno = RET.THIRDERR,errmsg = "发送短信失败")
    # return jsonify(errno=RET.OK, errmsg="发送短信成功")
    mobile = request.json.get("mobile")
    image_code = request.json.get("image_code")
    image_code_id = request.json.get("image_code_id")
    print(mobile,image_code,image_code_id)

    redis_image_code_id = redis_store.get("sms_code" + image_code_id)
    print(redis_image_code_id)

    if not redis_image_code_id:
        return jsonify(errno = RET.NODATA,errmsg = "验证码过期")

    if image_code.lower() != redis_image_code_id.lower():
        return jsonify(errno = RET.PARAMERR,errmsg = "验证码输入错误")
    result = random.randint(0,999999)
    sms_code = "%06d"%result
    redis_store.set("sms_code" + mobile,sms_code)
    print("短信验证码："+sms_code)

    return jsonify(errno=RET.OK, errmsg="发送短信成功")


@passport_bule.route("/image_code")
def passport():
    #获取当前提交过来的uuid
    #从浏览器请求时发送的响应行获取code_id
    code_id = request.args.get("code_id")
    #判断是否获取参数
    if not code_id:
        return jsonify(errno = RET.PARAMERR,errmsg = "参数错误")
    ##生成验证码内容
    # 第一个参数表示name
    # 第二个参数表示验证码里面具体的内容
    # 第三个参数是redis的过期时间,单位是秒,调用constants中的SMS_CODE_REDIS_EXPIRES
    name,text,image = captcha.generate_captcha()

    print("图片验证码内容 = " + text+" " +name )
    # 保存当前的验证码到redis中
    redis_store.set("sms_code" + code_id,text,constants.SMS_CODE_REDIS_EXPIRES)
    #初始化一个响应体
    resp = make_response(image)
    return resp

@passport_bule.route("/logout",methods = ["POST"] )
def admin_logout():
    session.pop("user_id",None)
    session.pop("nick_name",None)
    session.pop("mobile",None)
    session.pop("is_admin",False)

    return jsonify(errno = RET.OK,errmsg = "ok")
