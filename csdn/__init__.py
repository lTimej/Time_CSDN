from flask import Flask

def _create_app(config,enable_config_file=False):
    '''
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

    app = _create_app((config,enable_config_file))

    return app