from flask_restful import Resource, inputs
from flask import current_app,g
from flask_restful.reqparse import RequestParser

from utils import parsers
from utils.decorator import login_required
from . import constants

from caches import users,articles

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
        return {"aid":aid},201

