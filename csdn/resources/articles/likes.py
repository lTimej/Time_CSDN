from flask_restful import Resource
from flask_restful.reqparse import RequestParser
from flask import current_app,g

from models import db
from models.news import Attitude

from utils import parsers
from utils.decorator import login_required

from caches import users,articles,statistics


class ArticleUserLikeCountView(Resource):
    '''
    文章点赞数
    '''
    method_decorators = [login_required]
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
        if res > 0:
            pass

