from flask_restful import Resource
from flask_restful.reqparse import RequestParser
from flask import current_app,g
from flask_restful import Resource,inputs


class UserSearchSuggest(Resource):
    '''
    搜索建议
    '''
    def select(self,keyword):
        '''
        从elasticsearch查询
        :param keyword:
        :return:
        '''
        query = {
            'from': 0,
            'size': 20,
            '_source': False,
            'suggest': {
                'word-completion': {
                    'prefix': keyword,
                    'completion': {
                        'field': 'suggest'
                    }
                }
            }
        }
        #建议
        res = current_app.es.search(index='completions', body=query)
        options = res['suggest']['word-completion'][0]['options']
        return options
    def get(self):
        '''
        获取建议词条
        :return:
        '''
        #获取关键字
        data = RequestParser()
        #校验关键字
        data.add_argument("keyword", type=inputs.regex(r'^.{0,50}$'), required=True, location='args')
        args = data.parse_args()
        keyword = args.keyword
        #获取建议文章
        options = self.select(keyword)
        #为空，进行词条纠错
        if not options:
            query = {
                'from': 0,
                'size': 20,
                '_source': False,
                'suggest': {
                    'text': keyword,
                    'word-phrase': {
                        'phrase': {
                            'field': 'title',
                            'size': 1
                        }
                    }
                }
            }
            ret = current_app.es.search(index='articles', doc_type='article', body=query)
            options = ret['suggest']['word-phrase'][0]['options']
            ky = options[0].get("text")
            #纠错后在查询
            options = self.select(ky)
        searchs = []
        for option in options:
            if option.get("text") not in searchs:
                searchs.append(option.get("text"))
        return {"message":"ok","searchs":searchs},201
