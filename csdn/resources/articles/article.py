from flask import g
from flask_restful import Resource,inputs
from flask_restful.reqparse import RequestParser

from caches.users import UserArticleCache
from utils import parsers
from utils.decorator import login_required
from . import  constants
from caches.articles import ChannelArticleCache,ArticlesDetailCache

class ArticleList(Resource):

    def get(self,channel_id):
        '''
        获取所选频道的文章数据
        :param channel_id: 频道id
        :return:
        '''
        #获取参数
        data = RequestParser()
        #校验参数
        data.add_argument("page",type=parsers.checkout_page,required=False,location='args')
        data.add_argument("page_num",type=inputs.int_range(constants.DEFAULT_ARTICLE_PER_PAGE_MIN,
                                                                 constants.DEFAULT_ARTICLE_PER_PAGE_MAX,
                                                                 'page_num'),
                               required=False, location='args')
        args = data.parse_args()
        page = args.page
        page_num = args.page_num if args.page_num else constants.DEFAULT_ARTICLE_PER_PAGE_MIN
        #获取文章id
        total_num,page_articles = ChannelArticleCache(channel_id).get_page_content(page,page_num)
        results = []
        for article_id in page_articles:
            #获取文章详情信息
            articles = ArticlesDetailCache(article_id).get()
            if articles:
                results.append(articles)
        return {"total_num":total_num,"page":page,"page_num":page_num,"articles":results},201

class UserArticleList(Resource):
    method_decorators = [login_required]
    def get(self):
        '''
        获取当前用户的所有文章
        :return:
        '''
        user_id = g.user_id
        # 获取参数
        data = RequestParser()
        # 校验参数
        data.add_argument("page", type=parsers.checkout_page, required=False, location='args')
        data.add_argument("page_num", type=inputs.int_range(constants.DEFAULT_ARTICLE_PER_PAGE_MIN,
                                                            constants.DEFAULT_ARTICLE_PER_PAGE_MAX,
                                                            'page_num'),
                          required=False, location='args')
        args = data.parse_args()
        page = args.page
        page_num = args.page_num if args.page_num else constants.DEFAULT_ARTICLE_PER_PAGE_MIN
        #获取文章id
        total_num,articleIds = UserArticleCache(user_id).get_page(page,page_num)
        results = []
        for article_id in articleIds:
            # 获取文章详情信息
            articles = ArticlesDetailCache(article_id).get()
            if articles:
                results.append(articles)
        # print(results)
        return {"total_num": total_num, "page": page, "page_num": page_num, "articles": results}, 201




