from flask_restful import Resource,request,inputs
from flask_restful.reqparse import RequestParser
from flask import g,current_app
from sqlalchemy.exc import DatabaseError
from werkzeug.datastructures import FileStorage

from models import db
from utils import parsers
from utils.decorator import login_required

from caches.users import UserProfileCache,UserOtherProfileCache
from models.user import User,UserProfile
#获取当前用户所有信息
class CurrUserProfile(Resource):
    '''
    获取当前登录用户基本信息
    '''
    method_decorators = {
        'get': [login_required],
        'patch': [login_required],
    }

    def get(self):
        '''
        获取用户信息
        :return:
        '''
        user_id = g.user_id
        #获取基本信息
        user_dict = UserProfileCache(user_id).get()
        #获取其他信息
        user_other_dict = UserOtherProfileCache(user_id).get()
        if user_dict is None and user_other_dict is None:
            return {"message":"user is not exist"},403
        user_dict.update(user_other_dict)
        return user_dict,201
    def patch(self):
        '''
        修改用户信息
        :return:
        '''
        #获取数据
        data = RequestParser()
        #校验数据
        data.add_argument('head_photo',type=parsers.checkout_img,required=False,location='files')
        data.add_argument('oldPwd', type=parsers.checkout_pwd, required=False, location='json')
        data.add_argument('newPwd',type=parsers.checkout_pwd,required=False,location='json')
        data.add_argument('user_name',type=inputs.regex(r'^.{1,20}$'),required=False,location='json')
        data.add_argument('gender',type=parsers.checkout_gender,required=False,location='json')
        data.add_argument('introduce',type=inputs.regex(r'^.{99}$'),required=False,location='json')
        data.add_argument('tag',type=inputs.regex(r'^.{16}$'),required=False,location='json')
        data.add_argument('authName',type=inputs.regex(r'^.{2,4}$'),required=False,location='json')
        data.add_argument('birthday',type=parsers.checkout_date,required=False,location='json')
        data.add_argument('areas',type=inputs.regex(r'^.{99}$'),required=False,location='json')
        #修改数据至数据库和缓存
        args = data.parse_args()
        #用户基本信息修改
        userProfile = {}
        #用户其他信息修改
        userOtherProfile = {}
        #返回信息----整体
        user_dict = {}
        #是否更新用户基本信息缓存
        is_update_userProfileCache = False
        #是否更新用户其他信息缓存
        is_update_userOtherProfileCache = False
        if args.head_photo:#上传照片fdfs
            #{'Group name': 'group1', 'Remote file_id': 'group1/M00/00/00/wKiZgmCWCCCAZZpOAAEwN58xN6E131.png',
            # 'Status': 'Upload successed.', 'Local file name': './t3.png', 'Uploaded size': '76.00KB',
            # 'Storage IP': '192.168.153.130'}
            res = current_app.fdfs_client.upload_by_buffer(args.head_photo.read(),file_ext_name='png')
            if res.get('Status') == 'Upload successed.':
                img_url = res.get('Remote file_id')
                userProfile['profile_photo'] = img_url
                user_dict['head_photo'] = current_app.config['FDFS_DOMAIN'] + img_url
                is_update_userProfileCache = True
            else:
                return {'message': 'Uploading profile photo image failed.'}, 507
        # 存在修改
        if args.user_name:
            userProfile['name'] = args.user_name
            user_dict['user_name'] = args.user_name
            is_update_userProfileCache = True
        if args.newPwd:
            if args.oldPwd:
                user = User.query.filter_by(password=args.oldPwd).first()
                if user:
                   userProfile['password'] = args.newPwd
                   user_dict['pwd'] = 1
                   is_update_userProfileCache = True
                else:
                    return {'message': 'password is error.'}, 400
            else:
                userProfile['password'] = args.newPwd
                user_dict['pwd'] = 1
                is_update_userProfileCache = True


        if args.gender:
            userOtherProfile['gender'] = args.gender
            user_dict['gender'] = args.gender
            is_update_userOtherProfileCache = True

        if args.introduce:
            userProfile['introduction'] = args.introduce
            user_dict['introduce'] = args.introduce
            is_update_userProfileCache = True

        if args.tag:
            userOtherProfile['tag'] = args.tag
            user_dict['tag'] = args.tag
            is_update_userOtherProfileCache = True

        if args.authName:
            userOtherProfile['real_name'] = args.authName
            user_dict['authName'] = args.authName
            is_update_userOtherProfileCache = True

        if args.birthday:
            userOtherProfile['birthday'] = args.birthday
            user_dict['birthday'] = args.birthday
            is_update_userOtherProfileCache = True

        if args.areas:
            userOtherProfile['area'] = args.areas
            user_dict['areas'] = args.areas
            is_update_userOtherProfileCache = True
        try:
            if userProfile:
                User.query.filter_by(id=g.user_id).update(userProfile)
            if userOtherProfile:
                UserProfile.query.filter_by(id=g.user_id).update(userOtherProfile)
            db.session.commit()
        except DatabaseError as e:
            db.session.rollback()
            return {'message': 'User name has existed.'}, 409
        if is_update_userProfileCache:
            UserProfileCache(g.user_id).clear()
        if is_update_userOtherProfileCache:
            UserOtherProfileCache(g.user_id).clear()
        return user_dict,201



