import grpc
import socketio
from elasticsearch import Elasticsearch
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor

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
    #搜索类注册
    from .resources.search import bp_search
    app.register_blueprint(bp_search)

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

    #在定时任务该执行时，以进程或线程方式执行任务
    executors = {#10个线程
        'default': ThreadPoolExecutor(10)
    }
    #负责管理定时任务
    #  BackgroundScheduler 在框架程序（如Django、Flask）中使用
    app.scheduler = BackgroundScheduler(executors=executors)

    # 添加"静态的"定时任务
    from .schedule.statistic import fix_statistics
    # app.scheduler.add_job(fix_statistics, 'date', args=[app])
    app.scheduler.add_job(fix_statistics, 'cron', hour=3, args=[app])

    # 启动定时任务调度器
    app.scheduler.start()

    #rpc远程调用
    app.rpc_reco_channel = grpc.insecure_channel(app.config['RPC'].RECOMMEND)
    app.rpc_reco = app.rpc_reco_channel
    
    #消息推送通知
    app.sio_manager = socketio.KombuManager(app.config['RABBITMQ'],write_only=True)

    #elasticsearch
    app.es = Elasticsearch(
        app.config['ES'],
        # sniff before doing anything
        sniff_on_start=True,
        # refresh nodes after a node fails to respond
        sniff_on_connection_fail=True,
        # and also every 60 seconds
        sniffer_timeout=60
    )

    return app