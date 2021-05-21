import time

from flask_restful import Resource, inputs
from flask_restful.reqparse import RequestParser
from flask import current_app,g
from sqlalchemy.exc import IntegrityError

from caches.users import UserFocusCache,UserFansCache,UserProfileCache
from caches.statistics import UserFocusCount,UserFansCount
from models import db
from utils import parsers
from . import constants
from utils.decorator import login_required

from models.user import Relation


class UserFocus(Resource):
    '''
    用户关注
    '''
    method_decorators = [login_required]
    def get(self):
        '''
        获取用户关注列表
        :return:
        '''
        user_id = g.user_id
        #分页处理
        data = RequestParser()
        # 校验参数
        data.add_argument("page", type=parsers.checkout_page, required=False, location='args')
        data.add_argument("page_num", type=inputs.int_range(constants.DEFAULT_USER_FOLLOWINGS_PER_PAGE_MIN,
                                                            constants.DEFAULT_USER_FOLLOWINGS_PER_PAGE_MAX,
                                                            'page_num'),
                          required=False, location='args')
        args = data.parse_args()
        #当前页
        page = args.page
        #每页的数量
        page_num = args.page_num if args.page_num else constants.DEFAULT_USER_FOLLOWINGS_PER_PAGE_MIN
        focus = UserFocusCache(user_id).get()
        fans = UserFansCache(user_id).get()
        focus_limit = focus[(page-1)*page_num:page*page_num]
        res = []
        total_num = len(focus)
        for f in focus_limit:
            user = UserProfileCache(f).get()
            res.append({
                'id':f,
                'user_name':user.get('user_name'),
                'head_photo':user.get('head_photo'),
                'introductiojn':user.get('introduction'),
                'mutual_focus':f in fans
            })
        print(22222222222, res)
        return {"focus":res,"total_num":total_num,"page":page,"page_num":page_num},201

    def post(self):
        '''
        关注用户
        :return:
        '''
        user_id = g.user_id
        #获取被关注用户id
        data = RequestParser()
        data.add_argument('target',type=parsers.checkout_user_id,required=True,location='json')
        args = data.parse_args()
        target_id = args.target
        #用户不能关注自己
        if target_id == user_id:
            return {"message":"user cannot focus self"},400
        #存入数据库
        #存入成功标志
        ret = 1
        try:
            follow = Relation(user_id=user_id, target_user_id=target_id, relation=Relation.RELATION.FOLLOW)
            db.session.add(follow)
            db.session.commit()
        except IntegrityError as e:
            current_app.logger.error(e)
            #更新成功返回1，失败返回0
            ret = Relation.query.filter(Relation.user_id == user_id,
                                        Relation.target_user_id == target_id,
                                        Relation.relation != Relation.RELATION.FOLLOW)\
                .update({'relation': Relation.RELATION.FOLLOW})

        if ret > 0:
            timestamp = time.time()
            #当前用户增加关注用户
            UserFocusCache(user_id).update(target_id,timestamp)
            #被关注用户增加粉丝
            UserFansCache(target_id).update(user_id,timestamp)
            UserFocusCount.incr(user_id)
            UserFansCount.incr(target_id)
        return {"target_id":str(target_id)},201

class UserFans(Resource):
    '''
    用户粉丝
    '''
    method_decorators = [login_required]
    def get(self):
        '''
        获取用户关注列表
        :return:
        '''
        user_id = g.user_id
        #分页处理
        data = RequestParser()
        # 校验参数
        data.add_argument("page", type=parsers.checkout_page, required=False, location='args')
        data.add_argument("page_num", type=inputs.int_range(constants.DEFAULT_USER_FOLLOWINGS_PER_PAGE_MIN,
                                                            constants.DEFAULT_USER_FOLLOWINGS_PER_PAGE_MAX,
                                                            'page_num'),
                          required=False, location='args')
        args = data.parse_args()
        #当前页
        page = args.page
        #每页的数量
        page_num = args.page_num if args.page_num else constants.DEFAULT_USER_FOLLOWINGS_PER_PAGE_MIN
        focus = UserFocusCache(user_id).get()
        fans = UserFansCache(user_id).get()
        fans_limit = fans[(page - 1) * page_num:page * page_num]
        res = []
        total_num = len(fans)
        for f in fans_limit:
            user = UserProfileCache(f).get()
            res.append({
                'id':f,
                'user_name':user.get('user_name'),
                'head_photo':user.get('head_photo'),
                'introductiojn':user.get('introduction'),
                "mutual_focus": f in focus#判断是否互相关注
            })
        print(1111111111, res)
        return {"fans":res,"total_num":total_num,"page":page,"page_num":page_num},201
