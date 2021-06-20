
class DefaultConfig():
    '''
    基础配置
    '''

    # JWT
    JWT_SECRET = 'akldj2378/\edws09qeikl90\/'
    JWT_EXPIRY_HOURS = 2
    JWT_REFRESH_DAYS = 14

    #默认头像
    DEFAULT_TX = 'group1/M00/00/00/wKiZgmCOpa6AbvCXAAEwN58xN6E181.png'
    FDFS_DOMAIN = 'http://192.168.153.132:8888/'

    #错误页面
    ERROR_404_HELP = False

    # 日志
    LOGGING_LEVEL = 'DEBUG'
    LOGGING_FILE_DIR = '/home/time/logs'
    LOGGING_FILE_MAX_BYTES = 300 * 1024 * 1024
    LOGGING_FILE_BACKUP = 10

    #flask_sqlalchemy
    SQLALCHEMY_BINDS = {
        'm': 'mysql://root:liujun@127.0.0.1:3306/csdn',
        's': 'mysql://root:liujun@127.0.0.1:8306/csdn',
        'masters': ['m'],
        'slaves': ['s'],
        'default': 'm'
    }
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # 追踪数据的修改信号
    SQLALCHEMY_ECHO = True #是否打印sql语句执行过程

    # 设置三个redis 哨兵
    REDIS_SENTINELS = [
        ('127.0.0.1', '26380'),
        ('127.0.0.1', '26381'),
        ('127.0.0.1', '26382'),
    ]
    REDIS_SENTINEL_SERVICE_NAME = 'mymaster'

    # redis 集群
    REDIS_CLUSTER = [
        {'host': '127.0.0.1', 'port': '7000'},
        {'host': '127.0.0.1', 'port': '7001'},
        {'host': '127.0.0.1', 'port': '7002'},
    ]
    # 限流服务redis
    RATELIMIT_STORAGE_URL = 'redis+sentinel://127.0.0.1:26380,127.0.0.1:26381,127.0.0.1:26382/mymaster'
    RATELIMIT_STRATEGY = 'moving-window'

    #消息队列
    RABBITMQ = 'amqp://time:liujun@localhost:5672/csdn'

    # Snowflake ID Worker 参数
    DATACENTER_ID = 0
    WORKER_ID = 0
    SEQUENCE = 0
    class RPC:
        RECOMMEND = '127.0.0.1:8889'
        # CHATBOT = '172.17.0.59:9999'
    #rpc远程调用





class CeleryConfig(object):
    """
    Celery默认配置
    """
    broker_url = 'amqp://time:liujun@localhost:5672/csdn'

    # 容联云通讯短信验证码有效期，单位：秒
    SMS_CODE_REDIS_EXPIRES = 300
    # 短信模板
    SEND_SMS_TEMPLATE_ID = 1



