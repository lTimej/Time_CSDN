from flask_restful import Resource
from caches import channels as cache_channel

class GetAllChannel(Resource):

    def get(self):
        '''
        获取所分频道
        :return:
        '''
        channels = cache_channel.AllArticleChannel().get()
        return {"channels":channels},201


