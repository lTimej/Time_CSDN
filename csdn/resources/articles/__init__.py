from flask import Blueprint
from flask_restful import Api
from utils.output import output_json
from . import article,chaneels,collections,likes,reads,comments
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
#用户频道频道
article_api.add_resource(user_channel.UserChannelView,'/v1/user/channel',endpoint='anonychannels')
#用户文章收藏
article_api.add_resource(collections.CollectionsList,'/v1/article/collection',endpoint='collection')
#获取文章浏览状态
article_api.add_resource(collections.UserArticleStatusJudge,'/v1/article/status',endpoint='status')
#文章点赞
article_api.add_resource(likes.ArticleUserLikeCountView,'/v1/article/likes',endpoint='likes')
#文章阅读
article_api.add_resource(reads.ArticleReadingView,'/v1/article/reads',endpoint='reads')
#文章评论
article_api.add_resource(comments.CommentView,'/v1/article/comment',endpoint='comment')


