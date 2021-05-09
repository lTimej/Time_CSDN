from flask import Blueprint
from flask_restful import Api, output_json
from . import auth,profile

user_bp = Blueprint('user',__name__)

user_api = Api(user_bp,catch_all_404s=True)
user_api.representation('application/json')(output_json)

#用户认证
user_api.add_resource(auth.Auth,'/v1/login/auth',endpoint='auth')
#用户登录
user_api.add_resource(auth.Login,'/v1/login',endpoint='login')
#获取短信验证码
user_api.add_resource(auth.GetSmsCode,'/v1/login/smscode/<mobile:mobile>',endpoint='smscode')
#当前用户信息
user_api.add_resource(profile.CurrUserProfile,'/v1/curr/user',endpoint='curruser')
