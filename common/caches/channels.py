import json

from sqlalchemy.orm import load_only,contains_eager

from models.news import Channel,UserChannel
from flask import current_app
from . import constants

from redis.exceptions import RedisError
from sqlalchemy.exc import DatabaseError

class AllArticleChannel():
    '''
    redis:   string:   key:value
    '''
    keys = "all:channel"

    @classmethod
    def get(cls):
        '''

        :return: [{'channel_name':"",'id':1},{},{}]
        '''
        #从缓存中获取
        redis_conn = current_app.redis_cluster
        try:
            res = redis_conn.get(cls.keys)
        except RedisError as e:
            current_app.logger.error(e)
            res = None
        if res:
            channel_str = json.loads(res)
            return channel_str
        #缓存没有从数据库中获取，然后存入redis中
        channel_list = []
        try:#从数据库中获取
            channels = Channel.query.options(load_only(Channel.id,Channel.name)).filter(Channel.is_visible==True,Channel.is_default==False).order_by(Channel.sequence,Channel.id).all()
        except DatabaseError as e:
            current_app.logger.error(e)
            raise e
        if not channels:
            return channel_list
        for channel in channels:
            channel_list.append({
                'id': channel.id,
                'channel_name': channel.name
            })
        try:#存入redis
            redis_conn.setex(cls.keys,constants.ALL_CHANNELS_CACHE_TTL,json.dumps(channel_list))
        except RedisError as e:
            current_app.logger.error(e)
        #返回
        return channel_list
    @classmethod
    def clear(cls):
        '''
        清楚缓存
        :return:
        '''
        redis_conn = current_app.redis_cluster
        try:
            redis_conn.delete(cls.keys)
        except RedisError as e:
            current_app.logger.error(e)

    @classmethod
    def exit(cls,channel_id):
        '''
        判断频道是否存在
        :param channel_id:
        :return:
        '''
        # 此处不直接用redis判断是否存在键值
        # 先从redis中判断是否存在键，再从键判断值是否存在，redis集群中无法保证事务
        chs = cls.get()
        for ch in chs:
            if channel_id == ch['id']:
                return True
        return False

class UserArticleChannel():
    '''
    用户所选频道
    '''
    def __init__(self,user_id):
        self.key = "user:channel:{}".format(user_id)
        self.user_id = user_id
        self.redis_conn= current_app.redis_cluster

    def get(self):
        '''
        获取用户所属频道
        :return:
        '''
        #从缓存中获取
        try:
            res = self.redis_conn.get(self.key)
        except RedisError as e:
            current_app.logger.error(e)
            res = None
        #存在，返回
        if res :
            user_channels = json.loads(res)
            return user_channels
        else:#不存在从数据库获取
            try:
                ucs = UserChannel.query.join(UserChannel.channel).options(load_only(UserChannel.channel_id),contains_eager(UserChannel.channel).load_only(Channel.name)).filter(UserChannel.user_id==self.user_id,UserChannel.is_deleted==False,Channel.is_visible==True).all()
            except DatabaseError as e:
                current_app.logger.error(e)
                raise e
            if not ucs:#数据库不存在，返回None
                return None
            user_channels = []
            for uc in ucs:
                user_channels.append(({
                    "id":uc.channel_id,
                    "channel_name":uc.channel.name
                }))
            try:
                self.redis_conn.setex(self.key,constants.UserChannelsCacheTTL.get_val(),json.dumps(user_channels))
            except RedisError as e:
                current_app.logger.error(e)
            return user_channels

    def clear(self):
        try:
            self.redis_conn.delete(self.key)
        except RedisError as e:
            current_app.logger.error(e)
    def exist(self,channel_id):
        user_channels = self.get()
        for i in user_channels:
            if i.get('id') == channel_id:
                return True
        return False


class DefaultChannelCache():
    '''
    获取默认文章频道
    '''
    key = "default:channel"
    @classmethod
    def get(cls):
        #先从缓存中获取
        redis_conn = current_app.redis_master
        try:
            res = redis_conn.get(cls.key)
        except RedisError as e:
            current_app.logger.error(e)
            res = None
        #缓存存在，直接返回
        if res:
            return json.loads(res)
        #缓存不存在，先从数据库中获取
        try:
            dcs = Channel.query.options(load_only(Channel.id,Channel.name)).filter(Channel.is_visible==True,Channel.is_default==True).order_by(Channel.sequence,Channel.id).all()
        except DatabaseError as e:
            current_app.logger.error(e)
            raise e
        if not dcs:
            return None
        default_channel = []
        for dc in dcs:
            default_channel.append({
                'id':dc.id,
                'channel_name':dc.name
            })
        try:
            redis_conn.setex(cls.key,constants.DEFAULT_USER_CHANNELS_CACHE_TTL,json.dumps(default_channel))
        except RedisError as e:
            current_app.logger.error(e)

        return default_channel

class AnonyUserChannel():
    '''
    匿名用户频道缓存
    '''
    key = 'anony:channel'
    @classmethod
    def get(cls):
        redis_conn = current_app.redis_master
        try:
            res = redis_conn.get(cls.key)
            res = json.loads(res)
        except Exception as e:
            current_app.logger.error(e)
            res = []
        if res:
            return res

    @classmethod
    def save(cls,channels):
        redis_conn = current_app.redis_master
        try:
            redis_conn.setex(cls.key, constants.ANONY_USER_CHANNELS_CACHE_TTL, json.dumps(channels))
        except RedisError as e:
            current_app.logger.error(e)
            raise {"message": " saved failed"}

    @classmethod
    def clear(cls):
        redis_conn = current_app.redis_master
        try:
            redis_conn.delete(cls.key)
        except RedisError as e:
            current_app.logger.error(e)

    @classmethod
    def exist(cls,channel_id):
        res = cls.get()
        for ret in res:
            if ret.get('id') == channel_id:
                return True
        return False







