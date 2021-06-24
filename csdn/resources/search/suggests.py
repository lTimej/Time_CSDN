from flask_restful import Resource
from flask_restful.reqparse import RequestParser
from flask import current_app,g
from flask_restful import Resource,inputs


class UserSearchSuggest(Resource):
    '''
    搜索建议
    '''
    def get(self):
        data = RequestParser()
        data.add_argument("keyword", type=inputs.regex(r'^.{1,50}$'), required=True, location='args')