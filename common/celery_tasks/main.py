from celery import Celery
from settings.default import CeleryConfig

#实例化一个celery对象
celery_app = Celery("csdn")
#环境配置
celery_app.config_from_object(CeleryConfig)
# Set the default Django settings module for the 'celery' program.
celery_app.config_from_envvar('CSDN_CELERY_SETTINGS', silent=True)
#添加任务
celery_app.autodiscover_tasks(['celery_tasks.sms'])


''''
#启动
celery -A celery_tasks.main worker -l INFO  

 celery -A celery_tasks.main worker -Q sms
调用

'''