from flask_restful import Resource
from flask import g

from utils.decorator import login_required

from caches.users import UserProfileCache


class CurrUserProfile(Resource):

    method_decorators = [login_required]

    def get(self):
        user_id = g.user_id
        user_dict = UserProfileCache(user_id).get()
        print(user_dict)
        if user_dict is None:
            return {"message":"user is not exist"},403
        return user_dict,201