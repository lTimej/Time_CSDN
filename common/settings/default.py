

class DefaultConfig():
    '''
    基础配置
    '''

    # JWT
    JWT_SECRET = 'akldj2378/\edws09qeikl90\/'
    JWT_EXPIRY_HOURS = 2
    JWT_REFRESH_DAYS = 14

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

