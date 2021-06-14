from flask_restful import Resource
from flask_restful.reqparse import RequestParser
from flask import current_app,g
from sqlalchemy.orm import load_only

from models import db
from models.news import Attitude

from utils import parsers
from utils.decorator import login_required

from caches import users,articles,statistics

class ArticleUserLikeCountView(Resource):
    '''
    文章点赞数
    '''
    method_decorators = {
        'post': [login_required],
        'delete':[login_required]
    }
    def post(self):
        '''
        点赞
        :return:
        '''
        user_id = g.user_id
        # 获取被收藏的文章id
        data = RequestParser()
        data.add_argument('aid', type=parsers.checkout_article_id, required=True, location='json')
        args = data.parse_args()
        aid = args.aid
        res = 1
        try:
            att = Attitude(user_id=user_id, article_id=aid,attitude=Attitude.ATTITUDE.LIKING)
            db.session.add(att)
            db.session.commit()
        except Exception as e:
            current_app.logger.error(e)
            db.session.rollback()
            res = Attitude.query.filter(Attitude.user_id==user_id,Attitude.article_id==aid,Attitude.attitude==Attitude.ATTITUDE.DISLIKE).update({"attitude":Attitude.ATTITUDE.LIKING})
            db.session.commit()
        if res > 0:
            users.UserArticleAttitudeCache(user_id).clear()
            articles.ArticleLikeCache(user_id,aid).clear()
            statistics.UserArticleLikeCount.incr(user_id)
            statistics.ArticleLikeCount.incr(aid)
        return {"aid":aid},201
    def delete(self):
        user_id = g.user_id
        # 获取被收藏的文章id
        data = RequestParser()
        data.add_argument('aid', type=parsers.checkout_article_id, required=True, location='json')
        args = data.parse_args()
        aid = args.aid
        res = 1
        try:
            res = Attitude.query.filter(Attitude.user_id==user_id,Attitude.article_id==aid,Attitude.attitude==Attitude.ATTITUDE.LIKING).update({"attitude":Attitude.ATTITUDE.DISLIKE})
            db.session.commit()
        except Exception as e:
            current_app.logger.error(e)
            return {"message":"this attitude is not exist"},401
        if res > 0:
            users.UserArticleAttitudeCache(user_id).clear()
            articles.ArticleLikeCache(user_id, aid).clear()
            statistics.UserArticleLikeCount.incr(user_id, -1)
            statistics.ArticleLikeCount.incr(aid, -1)
        return {"message": "success"}, 201
    def get(self):
        '''
        获取当前文章点赞人员信息
        :return:
        '''
        #获取文章id
        data = RequestParser()
        #文章id校验
        data.add_argument('aid',type=parsers.checkout_article_id,required=True,location='args')
        args = data.parse_args()
        #文章id
        aid = args.aid
        user_ids = articles.ArticleAttitudeCache(aid).get()
        users_info = []
        for user_id in user_ids:
            user_info = users.UserProfileCache(user_id).get()
            users_info.append({
                'head_photo':user_info.get('head_photo'),
                'aid':aid
            })
        return {'users_info':users_info},201

