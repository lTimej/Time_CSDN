from flask import Flask

def _create_app(config,enable_config_file=False):
    '''
    创建app对象
    :param config: 配置类
    :param enable_config_file:
    :return: 一个app对象
    '''
    app = Flask(__name__)
    app.config.from_object(config)
    if enable_config_file:
        from utils import constants
        app.config.from_envvar(constants.GLOBAL_SETTING_ENV_NAME, silent=True)

    return app

def create_app(config,enable_config_file=False):
    '''
    配置信息
    :param config: 配置类
    :param enable_config_file: app对象
    :return:
    '''
    app = _create_app(config,enable_config_file)

    # 配置日志
    from utils.logging import create_logger
    create_logger(app)

    # MySQL数据库连接初始化
    from models import db
    db.init_app(app)

    #redis哨兵
    from redis.sentinel import Sentinel
    _sentinel = Sentinel(app.config['REDIS_SENTINELS'])
    app.redis_master = _sentinel.master_for(app.config['REDIS_SENTINEL_SERVICE_NAME'])
    app.redis_slave = _sentinel.slave_for(app.config['REDIS_SENTINEL_SERVICE_NAME'])

    #redis集群
    from rediscluster import StrictRedisCluster
    app.redis_cluster = StrictRedisCluster(startup_nodes=app.config['REDIS_CLUSTER'])

    # 注册url转换器
    from utils.converters import register_converters
    register_converters(app)

    #用户类注册
    from .resources.users import user_bp
    app.register_blueprint(user_bp)
    #文章类注册
    from .resources.articles import  article_bp
    app.register_blueprint(article_bp)

    #雪花算法生成user_id
    from utils.snowflake.id_worker import IdWorker
    app.id_worker = IdWorker(app.config['DATACENTER_ID'],
                             app.config['WORKER_ID'],
                             app.config['SEQUENCE'])
    #请求钩子
    from utils.middleware import user_authenticate
    app.before_request(user_authenticate)

    #fdfs
    from fdfs_client.client import Fdfs_client
    app.fdfs_client = Fdfs_client('/home/time/Time_CSDN/Time_CSDN/common/utils/fdfs/client.conf')

    return app