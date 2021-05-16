from flask import Blueprint
from flask_restful import Api
from utils.output import output_json
from . import article,chaneels
from ..users import channels as user_channel

article_bp = Blueprint('article',__name__)

article_api = Api(article_bp,catch_all_404s=True)
article_api.representation('application/json')(output_json)

#每个频道的文章
article_api.add_resource(article.ArticleList,'/v1/articles/<int(min=1):channel_id>',endpoint='article')
#每个用户的文章
article_api.add_resource(article.UserArticleList,'/v1/user/articles',endpoint='userArticle')

#所有频道
article_api.add_resource(chaneels.GetAllChannel,'/v1/articles/channel',endpoint='channels')

#默认频道
article_api.add_resource(chaneels.GetDefaultChannel,'/v1/default/channel',endpoint='dchannels')

#默认频道
article_api.add_resource(user_channel.UserChannelView,'/v1/user/channel',endpoint='anonychannels')


