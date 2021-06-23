from flask import current_app,g
from flask_restful import Resource,inputs
from flask_restful.reqparse import RequestParser
from . import constants
from caches import articles as cache_article
from caches import users as cache_user

class AllSearchView(Resource):
    '''
    搜索
    '''
    def get(self):
        '''

        :return:
        '''
        #获取参数
        data = RequestParser()
        #校验数据
        data.add_argument("keyword",type=inputs.regex(r'^.{1,50}$'),required=True,location='args')
        data.add_argument("page",type=inputs.positive,required=False,location="args")
        data.add_argument("page_num",type=inputs.int_range(constants.DEFAULT_SEARCH_PER_PAGE_MIN,constants.DEFAULT_SEARCH_PER_PAGE_MAX),required=False,location="args")
        args = data.parse_args()
        #关键词搜索
        keyword = args.keyword
        #内容列表分页初始化
        page = 1 if args.page is None else args.page
        page_num = constants.DEFAULT_SEARCH_PER_PAGE_MIN if args.page_num is None else args.page_num
        #es查询语句
        query = {
            "query":{
                "bool":{
                    "must":[
                        {
                            "match":{
                                "title":keyword
                            }
                        }
                    ],
                    "filter":[
                        {
                            "term":{
                                "status":0
                            }
                        }
                    ]
                }
            },
            "from":(page-1)*page_num,
            "size":page_num,
            "_source":False
        }
        ret = current_app.es.search(index="articles",doc_type="article",body=query)
        #查询结果总数
        total_num = ret.get("hits").get("total")
        #文章id列表
        articles = ret.get("hits").get("hits")
        articles_list = []
        #构造前端数据
        for article in articles:
            article_dict = cache_article.ArticlesDetailCache(article.get("_id")).get()
            if article_dict:
                articles_list.append(article_dict)
        #将搜索次存入缓存
        if g.user_id and page == 1:#如果已登录并且值存入一次，即page=1时第一次搜索
            try:
                cache_user.UserSearchCache(g.user_id).save(keyword)
            except Exception as e:
                current_app.logger.error(e)

        return {"message":"ok","articles":articles_list,"total_num":total_num},201




