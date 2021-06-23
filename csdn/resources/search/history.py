from flask import current_app,g
from flask_restful import Resource
from redis import RedisError

from caches import users as cache_user
from utils.decorator import login_required

class UserHistorySearchRecord(Resource):
    '''
    用户历史搜索记录
    '''
    method_decorators = [login_required]
    def get(self):
        try:
            keywords = cache_user.UserSearchCache(g.user_id).get()
        except RedisError as e:
            current_app.logger.error(e)
            keywords = None
        return {"keywords":keywords},201
    def delete(self):
        try:
            cache_user.UserSearchCache(g.user_id).clear()
        except RedisError as e:
            current_app.logger.error(e)
        return {"message":"ok"},201
