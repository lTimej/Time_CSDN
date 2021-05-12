from flask_restful import Resource
from caches import channels as cache_channel

class GetAllChannel(Resource):

    def get(self):
        '''
        获取所分频道
        :return:
        '''
        channels = cache_channel.AllArticleChannel().get()
        channels.insert(0,{
            'id': 0,
            'channel_name': "热榜"
        })
        channels.insert(0,{
            'id': -1,
            'channel_name': "推荐"
        })
        channels.insert(0,{
            'id':-2,
            'channel_name':"关注"
        })


        return {"channels":channels},201


