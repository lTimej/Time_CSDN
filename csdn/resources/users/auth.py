import random
from datetime import datetime,timedelta

from flask_limiter.util import get_remote_address
from flask_restful import Resource
from flask_restful.reqparse import RequestParser
from sqlalchemy import or_
from sqlalchemy.exc import DatabaseError

from flask import current_app, request, g

from celery_tasks.sms.tasks import send_sms_code
from models import db
from models.user import User, UserProfile
from utils.generate_username import get_username
from utils.getJwt import generate_jwt
from . import constants
from utils import parsers
from utils.limiter import limiter as lmt
from redis.exceptions import ConnectionError
from celery.result import AsyncResult

class GetSmsCode(Resource):
    error_message = 'Too many requests.'

    # decorators = [
    #     # 一个用户限制一分钟请求一次
    #     lmt.limit(constants.LIMIT_SMS_VERIFICATION_CODE_BY_MOBILE,
    #               key_func=lambda: request.view_args['mobile'],
    #               error_message=error_message),
    #     # 限制大量用户请求
    #     lmt.limit(constants.LIMIT_SMS_VERIFICATION_CODE_BY_IP,
    #               key_func=get_remote_address,
    #               error_message=error_message)
    # ]
    def get(self,mobile):
        '''
        发送验证码，并存入redis数据库
        :param mobile:
        :return:
        '''
        #随机生成6位验证码
        sms_code = '{:0>6d}'.format(random.randint(0, 999999))
        print(sms_code)
        #保存之redis
        try:
            current_app.redis_master.setex("app:code:{}".format(mobile),constants.SMS_VERIFICATION_CODE_EXPIRES, sms_code)
        except ConnectionError as e:
            return {"message":"invalid"},400

        #异步发送
        # res = send_sms_code.delay(mobile,sms_code)

        return {"message":"ok","code":sms_code},201

class Auth(Resource):
    def _get_token(self,user_id,refresh=True):
        '''
        获取token
        :param user_id: 用户id
        :param refresh: 默认生成一个刷新token
        :return: token,refresh_token
        '''
        now = datetime.utcnow()
        # json不能序列化datetime,所以转化为str
        expiry = str(now + timedelta(hours=current_app.config['JWT_EXPIRY_HOURS']))
        # 生成token
        token = generate_jwt({'user_id': user_id, 'is_refresh': False}, expiry)
        refresh_token = None
        if refresh:
            refresh_expiry = str(now + timedelta(days=current_app.config['JWT_REFRESH_DAYS']))
            refresh_token = generate_jwt({'user_id': user_id, 'is_refresh': True}, refresh_expiry)
        return token, refresh_token

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
        if not real_sms_code :#验证码过期
            return {"message":"sms_code is expired"},400
        if real_sms_code.decode() != sms_code:#验证码输入错误
            return {"message": "sms_code is error"}, 401
        #把数据库不存在的用户保存到数据库
        # 1、查询当前手机号用户对象
        user = User.query.filter_by(mobile=mobile).first()
        if not user:#不存在，保存至数据库
            #生成id
            user_id = current_app.id_worker.get_id()
            try:#与用户信息共存
                user = User(id=user_id,mobile=mobile,
                            last_login=datetime.now(),
                            name=get_username(mobile),
                            )
                db.session.add(user)
                db.session.flush()
                profile = UserProfile(id=user.id,company='无',career='无')
                db.session.add(profile)
                db.session.commit()
            except Exception as e:
                current_app.logger.error(e)
                db.session.rollback()
                return {"message":"data is abnormal"},405
        else:#存在，判断该用户是否可用
            if user.status == User.STATUS.DISABLE:
                return {"message":"this user is not exist"},403
        #响应之前构造token认证码
        print(888888,user.id)
        token,refresh_token = self._get_token(user.id)
        return {"token":token,"refresh_token":refresh_token},201

    def put(self):
        '''
        刷新token
        :return:
        '''
        if g.user_id is not None and g.is_refresh is True:
            token,refresh_token = self._get_token(g.user_id,refresh=False)
            return {'token':token,"refresh_token":refresh_token},201
        else:
            return {'message': 'Invalid refresh token'}, 403

class Login(Resource):
    def _get_token(self,user_id,refresh=True):
        '''
        获取token
        :param user_id: 用户id
        :param refresh: 默认生成一个刷新token
        :return: token,refresh_token
        '''
        now = datetime.utcnow()
        # json不能序列化datetime,所以转化为str
        expiry = str(now + timedelta(hours=current_app.config['JWT_EXPIRY_HOURS']))
        # 生成token
        token = generate_jwt({'user_id': user_id, 'is_refresh': False}, expiry)
        refresh_token = None
        if refresh:
            refresh_expiry = str(now + timedelta(days=current_app.config['JWT_REFRESH_DAYS']))
            refresh_token = generate_jwt({'user_id': user_id, 'is_refresh': True}, refresh_expiry)
        return token, refresh_token
    def post(self):
        '''
        账号密码登录
        :return:
        '''
        #获取参数
        data = RequestParser()
        #校验
        data.add_argument('username',type=parsers.checkout_username,required=True,location='json')
        #密码做了hashlib  md5加密处理
        data.add_argument('password',type=parsers.checkout_pwd,required=True,location='json')
        args = data.parse_args()
        username = args.username
        password = args.password
        try:#账号允许用户名/手机号/邮箱登录
            user = User.query.filter(or_(User.name==username,User.mobile==username,User.email==username),User.password==password).first()
            if user:
                token,refresh_token = self._get_token(user.id)
                return {"token":token,"refresh_token":refresh_token},201
            else:
                return {"message":"username or password is error"},402
        except DatabaseError as e:
            current_app.logger.error(e)
            return {"message": "data is abnormal"}, 405

