from flask import Blueprint
from flask_restful import Api
from utils.output import output_json
from . import article,chaneels

article_bp = Blueprint('article',__name__)

article_api = Api(article_bp,catch_all_404s=True)
article_api.representation('application/json')(output_json)

#每个频道的文章
article_api.add_resource(article.ArticleList,'/v1/articles/<int(min=1):channel_id>',endpoint='article')

#所有频道
article_api.add_resource(chaneels.GetAllChannel,'/v1/articles/channel',endpoint='channels')


