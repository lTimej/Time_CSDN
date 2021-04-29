from flask_restful import Resource
from flask_restful.reqparse import RequestParser

from utils import parsers


class Auth(Resource):

    def post(self):
        '''
        登录认证
        :return:
        '''
        #获取数据
        parser = RequestParser()
        parser.add_argument('mobile',type=parsers.mobile,required=True,location='json')
        parser.add_argument('sms_code',type=parsers.regex(r'^\d{6}$'),required=True,location='json')
        args = parser.parse_args()
        mobile = args.mobile
        sms_code = args.sms_code
        #验证数据
        # 上传数据库