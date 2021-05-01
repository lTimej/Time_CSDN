import json
import time

from settings.default import CeleryConfig
from celery_tasks.sms.yuntongxun.ccp_sms import CCP
from celery_tasks.main import celery_app

from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)
# bind：保证task对象会作为第一个参数自动传入
# name：异步任务别名
# retry_backoff：异常自动重试的时间间隔 第n次(retry_backoff×2^(n-1))s
# max_retries：异常自动重试次数的上限
@celery_app.task(bind=True, name='sms.send_sms_code', retry_backoff=3)
def send_sms_code(self,mobile,sms_code):
    '''
    发送短信验证码
    :param mobile: 手机号
    :param sms_code: 验证码
    :return:
    '''
    try:#发送短信
        sms_response = CCP().send_template_sms(to=mobile, datas=[sms_code, CeleryConfig.SMS_CODE_REDIS_EXPIRES//60], tempId=CeleryConfig.SEND_SMS_TEMPLATE_ID)
    except  Exception as e:#失败重新请求3次
        logger.error('[send_sms_code] {}'.format(e))
        raise self.retry(exc=e, max_retries=3)
    #{'statusCode': '000000', 'templateSMS': {'smsMessageSid': 'cc634baa6bbb493d90fc2a8e0ebd93f1', 'dateCreated': '20210501160131'}
    # #获取响应
    # sms_response = json.loads(sms_response)
    # resp_code = sms_response.get('statusCode')
    # if sms_response != '000000':#失败
    #     message = sms_response.get('Message', '')
    #     logger.error('send sms failed')
    #     raise self.retry(exc=Exception(message), max_retries=3)
    # logger.info('[send_sms_code] {} {}'.format(mobile, sms_code))
    return sms_response

