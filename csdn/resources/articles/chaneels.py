from flask_restful import Resource
from caches import channels as cache_channel
from caches import users as cache_users

class GetAllChannel(Resource):
    def get(self):
        '''
        获取所有频道
        :return:
        '''
        channels = cache_channel.AllArticleChannel().get()
        return {"channels":channels},201

class GetDefaultChannel(Resource):
    '''
    默认频道
    '''
    def get(self):
        '''
        获取默认频道
        :return:
        '''
        default_channel = cache_channel.DefaultChannelCache.get()
        return {"default_channel":default_channel},201