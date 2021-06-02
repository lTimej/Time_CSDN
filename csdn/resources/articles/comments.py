from flask_restful import Resource
from flask_restful.inputs import positive, int_range
from flask_restful.reqparse import RequestParser
from flask import current_app,g
from sqlalchemy.exc import SQLAlchemyError

from models import db
from models.news import Comment
from utils import parsers
from utils.decorator import login_required
from utils.snowflake import id_worker
from . import constants
from caches import comments, articles,statistics


class CommentView(Resource):
    '''
    评论
    '''
    method_decorators = {
        'post': [login_required],
    }
    def _comment_type(self,value):
        '''
        评论类型验证
        :param value:
        :return:
        '''
        if value in ['a','c']:
            return value
        else:
            return ValueError("type is failed")
    def get(self):
        '''
        :return:
        '''
        data = RequestParser()
        data.add_argument('type', type=self._comment_type, required=True, location='args')
        data.add_argument('source', type=positive, required=True, location='args')
        data.add_argument('offset', type=positive, required=False, location='args')
        data.add_argument('limit', type=int_range(constants.DEFAULT_COMMENT_PER_PAGE_MIN,
                                                       constants.DEFAULT_COMMENT_PER_PAGE_MAX,
                                                       argument='limit'), required=False, location='args')
        args = data.parse_args()
        limit = args.limit if args.limit is not None else constants.DEFAULT_COMMENT_PER_PAGE_MIN

        if args.type == 'a':
            #一级评论
            article_id = args.source
            total_num , end_id , last_id , page_comments = comments.ArticleCommentCache(article_id).get_page(args.offset,limit)
            # print("dsjklfqwjeoiwejd",total_num , end_id , last_id , page_comments)
        else:
            #评论的评论
            comment_id = args.source
            total_num, end_id, last_id, page_comments = comments.ArticleCommentResponseCache(comment_id).get_page(args.offset,limit)
        #获取评论相关信息
        comment_dict = comments.CommentCache.get_list(page_comments)
        # print("lkajdio98329838",comment_dict)
        return {"total_num":total_num,"end_id":end_id,'last_id':last_id,'comments':comment_dict},201

    def post(self):
        '''
        评论
        :return:
        '''
        user_id = g.user_id
        data = RequestParser()
        data.add_argument('article_id',type=parsers.checkout_article_id,required=True,location='json')
        data.add_argument('content', required=True, location='json')
        data.add_argument('comment_id',type=positive,required=False,location='json')
        args = data.parse_args()

        article_id = args.article_id
        content = args.content
        comment_parent_id = args.comment_id
        if not content:
            return {'message': 'Empty content.'}, 400

        allow_comment = articles.ArticlesDetailCache(article_id).is_allow_comment()
        if not allow_comment:
            return {'message': 'Article denied comment.'}, 400
        if not comment_parent_id:
            #文章评论
            comment_id = current_app.id_worker.get_id()
            comment = Comment(id=comment_id,user_id=user_id,article_id=article_id,content=content,parent_id=None)
            db.session.add(comment)
            db.session.commit()
            statistics.ArticleCommentCount.incr(article_id, 1)
            try:
                comments.CommentCache(comment_id).save(comment)
            except SQLAlchemyError as e:
                current_app.logger.error(e)
            comments.ArticleCommentCache(article_id).add(comment)
        else:
            flag = comments.CommentCache(comment_parent_id).exist()
            if not flag:
                return {'message': 'Invalid target comment id.'}, 400
            comment_id = current_app.id_worker.get_id()
            comment = Comment(id=comment_id, user_id=user_id, article_id=article_id, content=content, parent_id=comment_parent_id)
            db.session.add(comment)
            db.session.commit()
            statistics.ArticleCommentCount.incr(article_id, 1)
            try:
                comments.CommentCache(comment_id).save(comment)
            except SQLAlchemyError as e:
                current_app.logger.error(e)
            comments.ArticleCommentResponseCache(article_id).add(comment)
        return {'comment_id': comment.id, 'art_id': article_id}, 201


