from flask_restful import Resource
from flask_restful.reqparse import RequestParser

from flask import current_app,g
from models import news, user, db
from models.news import Read
from utils import parsers
from caches import users,articles,statistics
from utils.decorator import login_required


class ArticleReadingView(Resource):
    '''
    文章阅读信息
    '''

    def post(self):
        user_id = g.user_id
        # 获取被收藏的文章id
        data = RequestParser()
        data.add_argument('aid', type=parsers.checkout_article_id, required=True, location='json')
        args = data.parse_args()
        aid = args.aid
        if user_id:
            flag = users.UserArticleReadCache(user_id).exist(aid)
            if flag:
                try:
                    read = Read(user_id=user_id, article_id=aid)
                    db.session.add(read)
                    db.session.commit()
                except Exception as e:
                    current_app.logger.error(e)
                    db.session.rollback()
                    return {"message": "data is exist"}, 401
                users.UserArticleReadCache(user_id).clear()
                statistics.ArticleReadCount.incr(aid, 1)
        print("(((======12====)))",aid)
        return {"message":"OK","aid":aid},201