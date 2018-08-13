import redis

class Config(object):

    SECRET_KEY = "AKJSKCNKJDkzxmkdksld"

    # 连接mysql数据库
    SQLALCHEMY_DATABASE_URI = "mysql://root:mysql@127.0.0.1:3306/information"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # redis配置
    REDIS_HOST = "127.0.0.1"
    REDIS_PORT = 6379

    # #flask_session的配置信息
    # 指定 session 保存到 redis 中
    SESSION_TYPE = "redis"
    # 让 cookie 中的 session_id 被加密签名处理
    SESSION_USE_SIGNER = True
    # 使用 redis 的实例
    SESSION_REDIS = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT)
    # session 的有效期，单位是秒
    PERMANENT_SESSION_LIFETIME = 86400

class DevelopementConfig(Config):

    DEBUG = True

class ProductionConfig(Config):

    pass

config_map = {
    "development": DevelopementConfig,
    "production": ProductionConfig
}