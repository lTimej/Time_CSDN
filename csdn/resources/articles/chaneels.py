from flask_restful import Resource
from flask import g
from caches import channels as cache_channel
from caches import users as cache_users
from utils.decorator import is_login


class GetAllChannel(Resource):
    method_decorators = [is_login]

    def get(self):
        '''
        获取所有频道
        :return:
        '''
        #获取所有频道
        all_channels = cache_channel.AllArticleChannel().get()
        user_id = g.user_id
        if user_id:#登录用户所属频道
            channels = cache_channel.UserArticleChannel(user_id).get()
        else:#匿名用户所属频道
            channels = cache_channel.AnonyUserChannel.get()

        unChannels = []
        if not channels:#如果用户无关乎频道，返回所有频道
            return {"channels": all_channels}, 201
        for i in all_channels:#去掉用户所关注的那些频道
            if i not in channels:
                unChannels.append(i)
        return {"channels":unChannels},201

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