from flask_restful import Resource, inputs
from flask import current_app,g
from flask_restful.reqparse import RequestParser

from models import db
from utils import parsers
from utils.decorator import login_required
from . import constants
from models.news import Collection

from caches import users,articles,statistics

class CollectionsList(Resource):
    '''
    文章收藏的增删改查
    '''
    method_decorators = [login_required]

    def get(self):
        '''
        获取收藏列表
        :return:
        '''
        user_id = g.user_id
        # 分页处理
        data = RequestParser()
        # 校验参数
        data.add_argument("page", type=parsers.checkout_page, required=False, location='args')
        data.add_argument("page_num", type=inputs.int_range(constants.DEFAULT_ARTICLE_PER_PAGE_MIN,
                                                            constants.DEFAULT_ARTICLE_PER_PAGE_MAX,
                                                            'page_num'),
                          required=False, location='args')
        args = data.parse_args()
        # 当前页
        page = args.page
        # 每页的数量
        page_num = args.page_num if args.page_num else constants.DEFAULT_ARTICLE_PER_PAGE_MIN

        #获取文章收藏id
        total_num,collections = users.UserCollectionCache(user_id).get_page(page,page_num)
        print(collections)
        res = []
        for aid in collections:
            article = articles.ArticlesDetailCache(aid).get()
            res.append(article)

        return {"page":page,"page_num":page_num,"total_num":total_num,"collections":res},201
    def post(self):
        '''
        收藏文章
        :return:
        '''
        user_id = g.user_id
        # 获取被收藏的文章id
        data = RequestParser()
        data.add_argument('aid', type=parsers.checkout_article_id, required=True, location='json')
        args = data.parse_args()
        aid = args.aid
        ret = 1
        try:
            collection = Collection(user_id=user_id, article_id=aid)
            db.session.add(collection)
            db.session.commit()
        except Exception as e:
            current_app.logger.error(e)
            db.session.rollback()
            ret = Collection.query.filter_by(user_id=user_id, article_id=aid, is_deleted=True).update({'is_deleted': False})
            db.session.commit()
        if ret > 0:
            users.UserCollectionCache(user_id).clear()
            statistics.ArticleCollectionCount.incr(aid)
            statistics.UserCollectionCount.incr(user_id)
        return {"aid":aid},201
    def delete(self):
        '''
        取消收藏
        :return:
        '''
        user_id = g.user_id
        # 获取被收藏的文章id
        data = RequestParser()
        data.add_argument('aid', type=parsers.checkout_article_id, required=True, location='json')
        args = data.parse_args()
        aid = args.aid
        try:
            ret = Collection.query.filter(Collection.user_id==user_id,Collection.article_id==aid,Collection.is_deleted==False).update({'is_deleted': True})
            db.session.commit()
        except Exception as e:
            current_app.logger.error(e)
            return {"message": "collection user is not exist"}, 401
        if ret > 0:
            users.UserCollectionCache(user_id).clear()
            statistics.ArticleCollectionCount.incr(aid,-1)
            statistics.UserCollectionCount.incr(user_id,-1)
        return {"message":"ok"},201

class UserArticleStatusJudge(Resource):
    '''
    判断当前用户对文章的浏览状态，比如是否关注，是否收藏，是否点赞
    '''
    def get(self):
        '''
        获取判断是否存在信息
        :return:
        '''
        user_id = g.user_id
        data = RequestParser()
        data.add_argument('aid', type=parsers.checkout_article_id, required=True, location='args')
        data.add_argument('uid', type=parsers.checkout_user_id, required=True, location='args')
        args = data.parse_args()
        aid = args.aid
        uid = args.uid
        if user_id:#已登录
            isfocus = users.UserFocusCache(user_id).isFocus(uid)
            iscollection = users.UserCollectionCache(user_id).article_exist(aid)
            islike = users.UserArticleAttitudeCache(user_id).exist(aid)
        else:#未登录
            isfocus = False
            iscollection = False
            islike = False
        #这篇文章被收藏多少次
        collection_num = statistics.ArticleCollectionCount.get(aid)
        like_num = statistics.ArticleLikeCount.get(aid)
        context= {
            "isfocus":isfocus,
            "iscollection":iscollection,
            "islike":islike,
            "collection_num":collection_num,
            "like_num":like_num,
            "aid":aid
        }
        return context,201


