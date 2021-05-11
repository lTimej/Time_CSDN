import json

from sqlalchemy.orm import load_only

from models.news import Channel
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
            channels = Channel.query.options(load_only(Channel.id,Channel.name)).filter(Channel.is_visible==True).order_by(Channel.sequence,Channel.id).all()
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


