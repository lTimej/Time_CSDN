from flask import Blueprint
from flask_restful import Api, output_json
from . import auth

user_bp = Blueprint('user',__name__)

user_api = Api(user_bp,catch_all_404s=True)
user_api.representation('application/json')(output_json)

user_api.add_resource(auth.Auth,'/v1/login/auth',endpoint='auth')
user_api.add_resource(auth.GetSmsCode,'/v1/login/smscode/<mobile:mobile>',endpoint='smscode')
