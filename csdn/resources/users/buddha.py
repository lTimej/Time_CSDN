from flask_restful import Resource

from utils.decorator import login_required


class HeadPhoto(Resource):
    method_decorators = [login_required]

    def get(self):
        '''
        获取头像
        :return:
        '''
    def post(self):
        '''
        上传头像
        :return:
        '''