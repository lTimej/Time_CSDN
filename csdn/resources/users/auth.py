import random
from datetime import datetime

from flask_limiter.util import get_remote_address
from flask_restful import Resource
from flask_restful.reqparse import RequestParser

from flask import current_app,request

from celery_tasks.sms.tasks import send_sms_code
from models import db
from models.user import User, UserProfile
from . import constants
from utils import parsers
from utils.limiter import limiter as lmt
from redis.exceptions import RedisError


class GetSmsCode(Resource):
    error_message = 'Too many requests.'

    decorators = [
        #一个用户限制一分钟请求一次
        # lmt.limit(constants.LIMIT_SMS_VERIFICATION_CODE_BY_MOBILE,
        #           key_func=lambda: request.view_args['mobile'],
        #           error_message=error_message),
        #限制大量用户请求
        # lmt.limit(constants.LIMIT_SMS_VERIFICATION_CODE_BY_IP,
        #           key_func=get_remote_address,
        #           error_message=error_message)
    ]
    def get(self,mobile):
        '''
        发送验证码，并存入redis数据库
        :param mobile:
        :return:
        '''
        #随机生成6位验证码
        sms_code = '{:0>6d}'.format(random.randint(0, 999999))
        #保存之redis
        current_app.redis_master.setex("app:code:{}".format(mobile),constants.SMS_VERIFICATION_CODE_EXPIRES, sms_code)
        #异步发送
        res = send_sms_code.delay(mobile,sms_code)
        return {"res":res}

class Auth(Resource):
    def _get_token(self,):
        secret = current_app.config['JWT_SECRET']


    def post(self):
        '''
        登录认证
        :return:
        '''
        #获取数据
        parser = RequestParser()
        parser.add_argument('mobile',type=parsers.mobile,required=True,location='json')
        parser.add_argument('sms_code',type=parsers.regex(r'^\d{6}$'),required=True,location='json')
        args = parser.parse_args()
        mobile = args.mobile
        sms_code = args.sms_code
        #获取redis中验证码
        key = "app:code:{}".format(mobile)
        try:#先从主中获取
            real_sms_code = current_app.redis_master.get(key)
        except ConnectionError as e:#获取不到在从副上取
            current_app.logger.error(e)
            real_sms_code = current_app.redis_slave.get(key)
        #删除redis中验证码，用户点击登录后旧要重新获取验证码
        try:
            current_app.redis_master.delete(key)
        except ConnectionError as e:
            current_app.logger.error(e)
        #验证
        if not real_sms_code or real_sms_code != sms_code:
            return {"message":"sms_code is invalid"},400
        #把数据库不存在的用户保存到数据库
        # 1、查询当前手机号用户对象
        user = User.query.filter_by(mobile=mobile).first()
        if not user:#不存在，保存至数据库
            #生成id
            user_id = current_app.id_worker.get_id()
            try:#与用户信息共存
                user = User(id=user_id,mobile=mobile,last_login=datetime.now())
                db.session.add(user)
                db.session.flush()
                profile = UserProfile(id=user.id)
                db.session.add(profile)
                db.session.commit()
            except Exception as e:
                current_app.logger.error(e)
                db.session.rollback()
        else:#存在，判断该用户是否可用
            if user.status == User.STATUS.DISABLE:
                return {"message":"this user is not used"},403
        #响应之前构造token认证码




        print(mobile,sms_code)

        return {"code":'ok'},200
        #验证数据
        # 上传数据库