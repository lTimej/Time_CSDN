import json

from flask import current_app

from sqlalchemy.orm import load_only
from sqlalchemy.exc import DatabaseError

from models.user import User

from . import constants

from redis.exceptions import RedisError

class UserCache():
    '''
    用户类缓存  redis集群
    redis:    key:value ------>string类型
              user:user_id:profile:  "{user_id:user_id,}"
    '''
    def __init__(self,user_id):
        '''
        初始化key和用户id
        '''
        self.key = "user:{}:profile".format(user_id)
        self.user_id = user_id
        self.redis_conn = current_app.redis_cluster
    def _save(self):
        '''
        保存缓存
        user_name
        head_photo
        introduce
        career
        year_code
        :return:
        '''
        #1、从数据库中获取
        try:
            user = User.query.options(load_only(User.name,User.profile_photo,User.introduction,User.code_year,User.profile.career)).filter_by(id=self.user_id).first()
        except DatabaseError as e:
            #获取失败，抛出异常
            current_app.logger.erroe(e)
            raise e

        if not user:#不存在，返回None，并在redis存入-1
            try:
                self.redis_conn.setex(self.key,constants.UserNotExistsCacheTTL.get_val(),-1)
            except RedisError as e:
                current_app.logger.error(e)
            return None
        else:  #存在，获取，并存入redis
            #构造字典
            user_dict = {
                'user_name':user.name,
                'head_photo':user.profile_photo,
                'introduction':user.introduction,
                'code_year':user.code_year,
                'career':user.profile.career
            }
            #转化位字符串存入redis
            user_str = json.dumps(user_dict)
            try:
                self.redis_conn.setex(self.key,constants.UserProfileCacheTTL.get_val(),user_str)
            except RedisError as e:
                current_app.logger.error(e)
            #返回用户数据
            return user_dict


    def get(self):
        '''
        获取用户缓存
        :return:
        '''
        #1、从缓存中获取
        res = self.redis_conn.get(self.key)
        if res:  # 存在直接拿
            '''
            redis缓存：数据库不存在时，默认存个-1,并且数据都是byte字节类型
            '''
            if res == b'-1':#数据库不存在
                return None
            else:
                user_dict = json.loads(res)
                return user_dict

        else:  #不存在，先从数据库取，然后存入redis
            return self._save()

    def clearCache(self):
        '''
        清楚缓存
        :return:
        '''
        try:
            self.redis_conn.delete(self.key)
        except RedisError as e:
            current_app.logger.error(e)

    def user_is_exist(self):
        '''
        通过缓存判断用户是否存在
        :return:
        '''
        try:#取出缓存
            res = self.redis_conn.get(self.key)
        except RedisError as e:
            current_app.logger.error(e)
            res = None
        #缓存位None，先存入缓存
        if res is None:
            ret = self._save()
            if ret is not None:
                return True
            else:#数据库不在返回None
                return False
        else:#缓存位-1返回False
            if res == b'-1':
                return False
            else:
                return True
